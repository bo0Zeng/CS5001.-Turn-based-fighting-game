"""
selfplay_trainer.py
自对弈训练器 - 训练系统核心 / Self-Play Trainer - Core Training System

负责：
1. 管理自对弈循环
2. 收集训练数据
3. 更新智能体
4. 记录训练指标
5. 模型保存
"""

import sys
import os
from typing import Optional, Dict, List, Tuple
import numpy as np
import time
from tqdm import tqdm

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from environment import BattleEnv, ActionSpace
from agents import BaseAgent
from training.replay_buffer import EpisodeBuffer


class SelfPlayTrainer:
    """
    自对弈训练器
    
    用于训练两个智能体互相对抗
    """
    
    def __init__(self,
                 env: BattleEnv,
                 agent: BaseAgent,
                 opponent: Optional[BaseAgent] = None,
                 save_dir: str = "saved_models",
                 log_interval: int = 10,
                 save_interval: int = 50,
                 eval_interval: int = 20,
                 eval_episodes: int = 10):
        """
        初始化训练器
        
        Args:
            env: 游戏环境
            agent: 主训练智能体
            opponent: 对手智能体（None则自我对弈）
            save_dir: 模型保存目录
            log_interval: 日志记录间隔
            save_interval: 模型保存间隔
            eval_interval: 评估间隔
            eval_episodes: 评估episode数量
        """
        self.env = env
        self.agent = agent
        self.opponent = opponent if opponent is not None else agent
        self.save_dir = save_dir
        self.log_interval = log_interval
        self.save_interval = save_interval
        self.eval_interval = eval_interval
        self.eval_episodes = eval_episodes
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 动作空间
        self.action_space = ActionSpace()
        
        # 训练统计
        self.total_iterations = 0
        self.training_history = {
            'iteration': [],
            'agent_wins': [],
            'opponent_wins': [],
            'draws': [],
            'avg_reward': [],
            'avg_episode_length': [],
            'policy_loss': [],
            'value_loss': [],
            'entropy': [],
        }
    
    def train(self,
             num_iterations: int,
             episodes_per_iteration: int = 100,
             update_epochs: int = 4,
             batch_size: int = 64) -> Dict[str, List]:
        """
        执行训练
        
        Args:
            num_iterations: 训练迭代次数
            episodes_per_iteration: 每次迭代的episode数
            update_epochs: 每次迭代的更新轮数
            batch_size: 批大小
        
        Returns:
            训练历史字典
        """
        print("="*60)
        print("开始自对弈训练 / Start Self-Play Training")
        print("="*60)
        print(f"智能体: {self.agent.get_name()}")
        print(f"对手: {self.opponent.get_name()}")
        print(f"迭代次数: {num_iterations}")
        print(f"每次迭代episode数: {episodes_per_iteration}")
        print("="*60)
        
        for iteration in range(num_iterations):
            iteration_start_time = time.time()
            
            print(f"\n迭代 {iteration + 1}/{num_iterations}")
            
            # 收集数据
            episode_data = self._collect_episodes(episodes_per_iteration)
            
            # 更新智能体
            update_metrics = self._update_agent(
                episode_data,
                epochs=update_epochs,
                batch_size=batch_size
            )
            
            # 记录统计
            self._log_iteration(iteration + 1, episode_data, update_metrics)
            
            # 评估
            if (iteration + 1) % self.eval_interval == 0:
                eval_results = self.evaluate()
                print(f"\n📊 评估结果:")
                print(f"  胜率 vs 对手: {eval_results['win_rate']:.1f}%")
                print(f"  平均奖励: {eval_results['avg_reward']:.2f}")
            
            # 保存模型
            if (iteration + 1) % self.save_interval == 0:
                self._save_checkpoint(iteration + 1)
            
            iteration_time = time.time() - iteration_start_time
            print(f"⏱️  迭代耗时: {iteration_time:.2f}秒")
            
            self.total_iterations += 1
        
        print("\n" + "="*60)
        print("✅ 训练完成！")
        print("="*60)
        
        # 保存最终模型
        self._save_checkpoint(num_iterations, name="final")
        
        return self.training_history
    
    def _collect_episodes(self, num_episodes: int) -> Dict[str, List]:
        """
        收集episode数据
        
        Args:
            num_episodes: episode数量
        
        Returns:
            收集的数据字典
        """
        episode_buffer = EpisodeBuffer()
        
        agent_wins = 0
        opponent_wins = 0
        draws = 0
        total_rewards = 0
        total_lengths = 0
        
        print(f"收集 {num_episodes} 个episodes...")
        
        for episode in tqdm(range(num_episodes), desc="Episodes"):
            obs = self.env.reset()
            done = False
            episode_reward = 0
            episode_length = 0
            
            while not done:
                # 智能体选择动作
                valid_actions_p1 = self.env.get_valid_actions(player_id=1)
                action_mask_p1 = np.zeros(12, dtype=bool)
                action_mask_p1[valid_actions_p1] = True
                
                p1_actions = self.agent.select_action(
                    obs, valid_actions=action_mask_p1, deterministic=False
                )
                
                # 对手选择动作
                valid_actions_p2 = self.env.get_valid_actions(player_id=2)
                action_mask_p2 = np.zeros(12, dtype=bool)
                action_mask_p2[valid_actions_p2] = True
                
                p2_actions = self.opponent.select_action(
                    obs, valid_actions=action_mask_p2, deterministic=False
                )
                
                # 执行动作
                next_obs, p1_reward, p2_reward, done, info = self.env.step(
                    p1_actions, p2_actions
                )
                
                # 存储经验（只存储智能体的）
                episode_buffer.push(
                    state=obs,
                    action=p1_actions,
                    reward=p1_reward,
                    next_state=next_obs,
                    done=done,
                    action_mask=action_mask_p1
                )
                
                obs = next_obs
                episode_reward += p1_reward
                episode_length += 1
            
            # 统计结果
            winner = info.get('winner')
            if winner == self.env.player1.name:
                agent_wins += 1
            elif winner == self.env.player2.name:
                opponent_wins += 1
            else:
                draws += 1
            
            total_rewards += episode_reward
            total_lengths += episode_length
        
        # 获取所有数据
        all_data = episode_buffer.get_all()
        
        # 添加统计信息
        all_data['agent_wins'] = agent_wins
        all_data['opponent_wins'] = opponent_wins
        all_data['draws'] = draws
        all_data['avg_reward'] = total_rewards / num_episodes
        all_data['avg_length'] = total_lengths / num_episodes
        
        return all_data
    
    def _update_agent(self,
                     episode_data: Dict,
                     epochs: int,
                     batch_size: int) -> Dict[str, float]:
        """
        更新智能体
        
        Args:
            episode_data: episode数据
            epochs: 训练轮数
            batch_size: 批大小
        
        Returns:
            更新指标
        """
        # 检查智能体是否有update方法
        if not hasattr(self.agent, 'update'):
            return {}
        
        # 准备数据
        states = episode_data['states']
        actions = episode_data['actions']
        rewards = episode_data['rewards']
        next_states = episode_data['next_states']
        dones = episode_data['dones']
        action_masks = episode_data.get('action_masks')
        
        # 调用智能体的update方法
        metrics = self.agent.update(
            states, actions, rewards, next_states, dones,
            action_masks=action_masks,
            epochs=epochs,
            batch_size=batch_size
        )
        
        return metrics
    
    def _log_iteration(self,
                      iteration: int,
                      episode_data: Dict,
                      update_metrics: Dict):
        """
        记录迭代统计
        
        Args:
            iteration: 迭代次数
            episode_data: episode数据
            update_metrics: 更新指标
        """
        # 提取统计
        agent_wins = episode_data['agent_wins']
        opponent_wins = episode_data['opponent_wins']
        draws = episode_data['draws']
        total_episodes = agent_wins + opponent_wins + draws
        
        # 记录
        self.training_history['iteration'].append(iteration)
        self.training_history['agent_wins'].append(agent_wins / total_episodes * 100)
        self.training_history['opponent_wins'].append(opponent_wins / total_episodes * 100)
        self.training_history['draws'].append(draws / total_episodes * 100)
        self.training_history['avg_reward'].append(episode_data['avg_reward'])
        self.training_history['avg_episode_length'].append(episode_data['avg_length'])
        
        if update_metrics:
            self.training_history['policy_loss'].append(update_metrics.get('policy_loss', 0))
            self.training_history['value_loss'].append(update_metrics.get('value_loss', 0))
            self.training_history['entropy'].append(update_metrics.get('entropy', 0))
        
        # 打印
        if iteration % self.log_interval == 0:
            print(f"\n📈 迭代 {iteration} 统计:")
            print(f"  胜/负/平: {agent_wins}/{opponent_wins}/{draws}")
            print(f"  胜率: {agent_wins/total_episodes*100:.1f}%")
            print(f"  平均奖励: {episode_data['avg_reward']:.2f}")
            print(f"  平均长度: {episode_data['avg_length']:.1f}")
            
            if update_metrics:
                print(f"  策略损失: {update_metrics.get('policy_loss', 0):.4f}")
                print(f"  价值损失: {update_metrics.get('value_loss', 0):.4f}")
                print(f"  熵: {update_metrics.get('entropy', 0):.4f}")
    
    def evaluate(self, num_episodes: Optional[int] = None) -> Dict[str, float]:
        """
        评估智能体
        
        Args:
            num_episodes: 评估episode数（None使用默认值）
        
        Returns:
            评估结果字典
        """
        if num_episodes is None:
            num_episodes = self.eval_episodes
        
        # 设置为评估模式
        self.agent.set_training_mode(False)
        
        wins = 0
        total_reward = 0
        
        for _ in range(num_episodes):
            obs = self.env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                # 确定性选择动作
                valid_actions_p1 = self.env.get_valid_actions(player_id=1)
                action_mask_p1 = np.zeros(12, dtype=bool)
                action_mask_p1[valid_actions_p1] = True
                
                p1_actions = self.agent.select_action(
                    obs, valid_actions=action_mask_p1, deterministic=True
                )
                
                valid_actions_p2 = self.env.get_valid_actions(player_id=2)
                action_mask_p2 = np.zeros(12, dtype=bool)
                action_mask_p2[valid_actions_p2] = True
                
                p2_actions = self.opponent.select_action(
                    obs, valid_actions=action_mask_p2, deterministic=True
                )
                
                obs, p1_reward, p2_reward, done, info = self.env.step(
                    p1_actions, p2_actions
                )
                
                episode_reward += p1_reward
            
            if info.get('winner') == self.env.player1.name:
                wins += 1
            
            total_reward += episode_reward
        
        # 恢复训练模式
        self.agent.set_training_mode(True)
        
        results = {
            'win_rate': wins / num_episodes * 100,
            'avg_reward': total_reward / num_episodes,
            'num_episodes': num_episodes
        }
        
        return results
    
    def _save_checkpoint(self, iteration: int, name: Optional[str] = None):
        """
        保存检查点
        
        Args:
            iteration: 迭代次数
            name: 检查点名称（可选）
        """
        if name is None:
            filename = f"checkpoint_iter_{iteration}.pth"
        else:
            filename = f"{name}_model.pth"
        
        save_path = os.path.join(self.save_dir, filename)
        
        if hasattr(self.agent, 'save'):
            self.agent.save(save_path)
            print(f"💾 模型已保存: {save_path}")


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 SelfPlayTrainer...")
    
    # 导入必要的模块
    from environment import BattleEnv
    from agents import RandomAgent
    
    # 测试1: 创建训练器
    print("\n测试1: 创建训练器")
    
    env = BattleEnv(reward_type='dense', verbose=False)
    agent = RandomAgent(action_dim=12, seed=42)
    opponent = RandomAgent(action_dim=12, seed=123)
    
    trainer = SelfPlayTrainer(
        env=env,
        agent=agent,
        opponent=opponent,
        save_dir="test_models",
        log_interval=2,
        save_interval=5
    )
    
    print("✅ 训练器创建成功")
    
    # 测试2: 收集episodes
    print("\n测试2: 收集episodes")
    
    episode_data = trainer._collect_episodes(num_episodes=10)
    
    print(f"收集到的数据:")
    print(f"  状态数量: {len(episode_data['states'])}")
    print(f"  动作数量: {len(episode_data['actions'])}")
    print(f"  智能体胜: {episode_data['agent_wins']}")
    print(f"  对手胜: {episode_data['opponent_wins']}")
    print(f"  平局: {episode_data['draws']}")
    print(f"  平均奖励: {episode_data['avg_reward']:.2f}")
    
    # 测试3: 评估
    print("\n测试3: 评估智能体")
    
    eval_results = trainer.evaluate(num_episodes=5)
    print(f"评估结果:")
    for key, value in eval_results.items():
        print(f"  {key}: {value}")
    
    # 测试4: 短训练（使用随机智能体）
    print("\n测试4: 短期训练")
    
    history = trainer.train(
        num_iterations=3,
        episodes_per_iteration=5,
        update_epochs=1,
        batch_size=32
    )
    
    print(f"\n训练历史:")
    for key in ['iteration', 'agent_wins', 'avg_reward']:
        if key in history and history[key]:
            print(f"  {key}: {history[key]}")
    
    # 清理测试文件
    import shutil
    if os.path.exists("test_models"):
        shutil.rmtree("test_models")
        print("\n🗑️  已清理测试文件")
    
    print("\n✅ SelfPlayTrainer 测试完成！")