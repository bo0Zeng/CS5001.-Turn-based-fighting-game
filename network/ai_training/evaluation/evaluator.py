"""
evaluator.py
评估器 - 评估智能体性能 / Evaluator - Evaluate Agent Performance

提供：
- 对战评估
- 性能指标统计
- 对比多个智能体
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
import numpy as np
from tqdm import tqdm

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from environment import BattleEnv
from agents import BaseAgent, RandomAgent, RuleBasedAgent


class Evaluator:
    """
    智能体评估器
    
    用于评估智能体的性能
    """
    
    def __init__(self, env: BattleEnv, verbose: bool = True):
        """
        初始化评估器
        
        Args:
            env: 游戏环境
            verbose: 是否打印详细信息
        """
        self.env = env
        self.verbose = verbose
    
    def evaluate_agent(self,
                      agent: BaseAgent,
                      opponent: BaseAgent,
                      num_episodes: int = 100,
                      deterministic: bool = True) -> Dict[str, float]:
        """
        评估智能体对阵对手的表现
        
        Args:
            agent: 被评估的智能体
            opponent: 对手
            num_episodes: 评估episode数
            deterministic: 是否确定性选择动作
        
        Returns:
            评估结果字典
        """
        # 设置为评估模式
        if hasattr(agent, 'set_training_mode'):
            agent.set_training_mode(False)
        if hasattr(opponent, 'set_training_mode'):
            opponent.set_training_mode(False)
        
        wins = 0
        losses = 0
        draws = 0
        
        total_rewards = []
        episode_lengths = []
        damages_dealt = []
        damages_taken = []
        
        iterator = tqdm(range(num_episodes), desc="评估中") if self.verbose else range(num_episodes)
        
        for _ in iterator:
            obs = self.env.reset()
            done = False
            episode_reward = 0
            episode_length = 0
            
            p1_hp_initial = self.env.player1.hp
            p2_hp_initial = self.env.player2.hp
            
            while not done:
                # 智能体动作
                valid_p1 = self.env.get_valid_actions(player_id=1)
                mask_p1 = np.zeros(12, dtype=bool)
                mask_p1[valid_p1] = True
                p1_actions = agent.select_action(obs, mask_p1, deterministic)
                
                # 对手动作
                valid_p2 = self.env.get_valid_actions(player_id=2)
                mask_p2 = np.zeros(12, dtype=bool)
                mask_p2[valid_p2] = True
                p2_actions = opponent.select_action(obs, mask_p2, deterministic)
                
                # 执行
                obs, p1_reward, p2_reward, done, info = self.env.step(p1_actions, p2_actions)
                
                episode_reward += p1_reward
                episode_length += 1
            
            # 统计结果
            winner = info.get('winner')
            if winner == self.env.player1.name:
                wins += 1
            elif winner == self.env.player2.name:
                losses += 1
            else:
                draws += 1
            
            total_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            
            # 伤害统计
            damage_dealt = p2_hp_initial - self.env.player2.hp
            damage_taken = p1_hp_initial - self.env.player1.hp
            damages_dealt.append(damage_dealt)
            damages_taken.append(damage_taken)
        
        # 恢复训练模式
        if hasattr(agent, 'set_training_mode'):
            agent.set_training_mode(True)
        if hasattr(opponent, 'set_training_mode'):
            opponent.set_training_mode(True)
        
        # 计算指标
        results = {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'total_games': num_episodes,
            'win_rate': wins / num_episodes * 100,
            'loss_rate': losses / num_episodes * 100,
            'draw_rate': draws / num_episodes * 100,
            'avg_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'avg_episode_length': np.mean(episode_lengths),
            'avg_damage_dealt': np.mean(damages_dealt),
            'avg_damage_taken': np.mean(damages_taken),
            'damage_ratio': np.mean(damages_dealt) / (np.mean(damages_taken) + 1e-6),
        }
        
        return results
    
    def print_results(self, results: Dict[str, float], agent_name: str = "Agent"):
        """
        打印评估结果
        
        Args:
            results: 评估结果字典
            agent_name: 智能体名称
        """
        print("\n" + "="*60)
        print(f"📊 {agent_name} 评估结果 / Evaluation Results")
        print("="*60)
        
        print(f"\n🎮 对战结果:")
        print(f"  总场数: {results['total_games']}")
        print(f"  胜/负/平: {results['wins']}/{results['losses']}/{results['draws']}")
        print(f"  胜率: {results['win_rate']:.1f}%")
        print(f"  负率: {results['loss_rate']:.1f}%")
        print(f"  平局率: {results['draw_rate']:.1f}%")
        
        print(f"\n💰 奖励统计:")
        print(f"  平均奖励: {results['avg_reward']:.2f} ± {results['std_reward']:.2f}")
        
        print(f"\n⚔️ 战斗统计:")
        print(f"  平均回合长度: {results['avg_episode_length']:.1f}")
        print(f"  平均造成伤害: {results['avg_damage_dealt']:.1f}")
        print(f"  平均受到伤害: {results['avg_damage_taken']:.1f}")
        print(f"  伤害比率: {results['damage_ratio']:.2f}")
        
        print("="*60)
    
    def compare_agents(self,
                      agents: List[BaseAgent],
                      agent_names: List[str],
                      opponent: BaseAgent,
                      num_episodes: int = 100) -> Dict[str, Dict]:
        """
        比较多个智能体的性能
        
        Args:
            agents: 智能体列表
            agent_names: 智能体名称列表
            opponent: 共同对手
            num_episodes: 每个智能体的评估episodes
        
        Returns:
            所有智能体的评估结果
        """
        all_results = {}
        
        for agent, name in zip(agents, agent_names):
            print(f"\n评估 {name}...")
            results = self.evaluate_agent(agent, opponent, num_episodes)
            all_results[name] = results
            
            if self.verbose:
                self.print_results(results, name)
        
        return all_results
    
    def benchmark_against_baselines(self,
                                    agent: BaseAgent,
                                    agent_name: str = "Agent",
                                    num_episodes: int = 100) -> Dict[str, Dict]:
        """
        对比基线智能体的性能
        
        Args:
            agent: 被评估的智能体
            agent_name: 智能体名称
            num_episodes: 评估episodes
        
        Returns:
            对比结果字典
        """
        print("\n" + "="*60)
        print(f"🏆 {agent_name} 基线对比测试")
        print("="*60)
        
        results = {}
        
        # 对抗随机智能体
        print(f"\n📌 测试1: vs 随机智能体")
        random_agent = RandomAgent(action_dim=12)
        results['vs_random'] = self.evaluate_agent(agent, random_agent, num_episodes)
        self.print_results(results['vs_random'], f"{agent_name} vs Random")
        
        # 对抗规则智能体
        print(f"\n📌 测试2: vs 规则智能体")
        rule_agent = RuleBasedAgent(action_dim=12, aggression=0.7)
        results['vs_rule'] = self.evaluate_agent(agent, rule_agent, num_episodes)
        self.print_results(results['vs_rule'], f"{agent_name} vs Rule")
        
        # 汇总对比
        print("\n" + "="*60)
        print("📊 性能对比汇总")
        print("="*60)
        print(f"{'对手':<15} {'胜率':<10} {'平均奖励':<12} {'伤害比率'}")
        print("-"*60)
        for opponent_name, result in results.items():
            print(f"{opponent_name:<15} {result['win_rate']:>6.1f}%   {result['avg_reward']:>8.2f}    {result['damage_ratio']:>6.2f}")
        print("="*60)
        
        return results


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 Evaluator...")
    
    from environment import BattleEnv
    from agents import PPOAgent, RandomAgent, RuleBasedAgent
    import torch
    
    # 创建环境
    env = BattleEnv(reward_type='dense', verbose=False)
    
    # 创建评估器
    evaluator = Evaluator(env, verbose=True)
    
    # 测试1: 评估随机智能体 vs 随机智能体
    print("\n测试1: Random vs Random")
    random1 = RandomAgent(action_dim=12, seed=42)
    random2 = RandomAgent(action_dim=12, seed=123)
    
    results = evaluator.evaluate_agent(random1, random2, num_episodes=20)
    evaluator.print_results(results, "RandomAgent1")
    
    # 测试2: 评估规则智能体 vs 随机智能体
    print("\n测试2: Rule vs Random")
    rule_agent = RuleBasedAgent(action_dim=12, aggression=0.7)
    random_agent = RandomAgent(action_dim=12)
    
    results = evaluator.evaluate_agent(rule_agent, random_agent, num_episodes=20)
    evaluator.print_results(results, "RuleBasedAgent")
    
    # 测试3: 比较多个智能体
    print("\n测试3: 比较多个智能体")
    
    aggressive_rule = RuleBasedAgent(action_dim=12, aggression=0.9)
    defensive_rule = RuleBasedAgent(action_dim=12, aggression=0.3)
    balanced_rule = RuleBasedAgent(action_dim=12, aggression=0.5)
    
    agents = [aggressive_rule, defensive_rule, balanced_rule]
    names = ["Aggressive", "Defensive", "Balanced"]
    
    all_results = evaluator.compare_agents(
        agents, names, 
        opponent=random_agent,
        num_episodes=10
    )
    
    # 测试4: PPO智能体基线对比
    print("\n测试4: PPO基线对比（未训练模型）")
    
    device = torch.device('cpu')
    ppo_agent = PPOAgent(state_dim=66, action_dim=12, device=device)
    
    baseline_results = evaluator.benchmark_against_baselines(
        agent=ppo_agent,
        agent_name="Untrained PPO",
        num_episodes=10
    )
    
    print("\n✅ Evaluator 测试完成！")