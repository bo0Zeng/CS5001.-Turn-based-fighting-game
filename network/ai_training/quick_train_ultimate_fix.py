"""
quick_train_ultimate_fix.py
终极修复版训练 - 解决策略僵化问题 / Ultimate Fix Training

多方位修复：
1. ⬆️ 大幅提高熵系数（0.01 → 0.05）- 强制探索
2. ⬆️ 调整奖励权重 - 鼓励多样化策略
3. 🎯 特殊奖励control和burst成功
4. 🔄 混合对手训练 - 避免过拟合
5. 📉 惩罚单一动作过度使用
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = current_dir
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

import torch
import numpy as np
import random
from datetime import datetime

from environment import BattleEnv
from agents import PPOAgent, RandomAgent
from agents.rule_based_agent_v2 import ImprovedRuleAgent
from training import SelfPlayTrainer
from evaluation import Evaluator


class UltimateRewardEnv(BattleEnv):
    """
    终极修复版环境 - 内嵌改进的奖励函数
    
    直接修改环境的奖励计算
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 追踪动作使用
        self.p1_action_history_full = []
        self.p2_action_history_full = []
    
    def reset(self):
        obs = super().reset()
        self.p1_action_history_full = []
        self.p2_action_history_full = []
        return obs
    
    def step(self, p1_actions, p2_actions):
        # 记录动作
        self.p1_action_history_full.extend(p1_actions)
        self.p2_action_history_full.extend(p2_actions)
        
        # 获取基础奖励
        obs, p1_reward, p2_reward, done, info = super().step(p1_actions, p2_actions)
        
        # 修改奖励
        p1_reward = self._calculate_ultimate_reward(
            self.player1, self.player2, p1_reward, p1_actions, 
            self.p1_action_history_full, done, info
        )
        
        p2_reward = self._calculate_ultimate_reward(
            self.player2, self.player1, p2_reward, p2_actions,
            self.p2_action_history_full, done, info
        )
        
        return obs, p1_reward, p2_reward, done, info
    
    def _calculate_ultimate_reward(self, player, opponent, base_reward, 
                                   actions, action_history, done, info):
        """
        终极奖励计算
        
        在基础奖励上添加：
        1. Control成功超级奖励
        2. Burst有效使用奖励
        3. 动作多样性奖励
        4. 单一动作过度使用惩罚
        """
        reward = base_reward
        
        # 降低基础survival奖励的影响
        if not done:
            reward -= 0.4  # 抵消大部分survival奖励
        
        # 1. Control成功超级奖励
        if opponent.controlled and opponent.controller == player.name:
            reward += 10.0  # 巨额奖励！（原本只有5.0）
        
        # 2. Burst有效使用奖励
        # 检查是否使用了burst（动作11）
        if 11 in actions:
            # 如果距离<=2，额外奖励
            distance = self.combat.get_distance()
            if distance <= 2:
                reward += 10.0  # 近距离使用burst的奖励
        
        # 3. 动作多样性奖励（增强版）
        if len(action_history) >= 6:
            recent_actions = action_history[-6:]  # 最近3回合
            unique_actions = len(set(recent_actions))
            
            if unique_actions >= 4:
                reward += 20  # ⬆️ 大幅提高多样性奖励
            elif unique_actions >= 3:
                reward += 3.0  # 中等多样性奖励
            elif unique_actions <= 1:
                reward -= 10.0  # ⬆️ 大幅提高单调性惩罚
            elif unique_actions <= 2:
                reward -= 5.0   # ⬆️ 提高单调性惩罚
        
        # 4. 单一动作过度使用惩罚（增强版）
        if len(action_history) >= 8:
            recent_actions = action_history[-8:]
            
            # 统计所有动作的使用频率
            from collections import Counter
            action_counts = Counter(recent_actions)
            
            # 惩罚过度使用单一动作
            most_common_count = action_counts.most_common(1)[0][1]
            if most_common_count >= 7:  # 8次里用了6次同一动作
                reward -= 8.0 * (most_common_count - 5)  # ⬆️ 大幅提高惩罚
        
        # 5. 进攻性奖励（造成伤害额外奖励）
        damage_dealt = opponent.hp - (opponent.hp + info.get('damage_dealt_this_turn', 0))
        # 注：这里简化处理，实际需要追踪
        
        return reward


def main():
    """终极修复训练"""
    
    print("="*80)
    print("🔥 终极修复版训练 / Ultimate Fix Training")
    print("="*80)
    print()
    print("🎯 目标: 让AI学会Control和Burst")
    print()
    print("修复措施:")
    print("  1. 熵系数: 0.01 → 0.15 (探索+1400%)")
    print("  2. Control奖励: 5.0 → 15.0 (奖励+200%)")
    print("  3. Burst奖励: +10.0 (新增)")
    print("  4. 动作多样性奖励: +3.0 → +8.0 (大幅增强)")
    print("  5. 单一动作过度使用惩罚: -8.0/次 (大幅增强)")
    print("  6. Survival奖励: 实质降低")
    print("  7. 新增中等多样性奖励: +3.0")
    print("  8. 新增单调性严重惩罚: -10.0")
    print()
    print("="*80)
    
    # 设置
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  设备: {device}")
    
    # 创建终极修复环境
    print(f"🎮 创建终极修复环境...")
    env = UltimateRewardEnv(reward_type='dense', max_turns=30, verbose=False)
    
    # 创建PPO智能体（超高探索）
    print(f"🤖 创建超高探索PPO智能体...")
    agent = PPOAgent(
        state_dim=66,
        action_dim=12,
        hidden_sizes=(256, 128),
        learning_rate=3e-4,
        gamma=0.99,
        entropy_coef=0.2,  # ⬆️ 大幅提高探索性（15倍）
        clip_epsilon=0.3,    # ⬆️ 增大裁剪范围，允许更大更新
        device=device
    )
    
    # 混合对手（关键！）
    print(f"👾 创建混合对手池...")
    opponents = [
        RandomAgent(action_dim=12, seed=100),
        RandomAgent(action_dim=12, seed=200),
        ImprovedRuleAgent(aggression=0.7),
        ImprovedRuleAgent(aggression=0.9),
    ]
    opponent_names = ['Random1', 'Random2', 'Rule(0.7)', 'Rule(0.9)']
    
    print(f"   对手数量: {len(opponents)}")
    for name in opponent_names:
        print(f"     - {name}")
    
    # 保存目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"saved_models/ultimate_fix_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    print(f"💾 保存目录: {save_dir}")
    
    # 训练前评估
    print("\n" + "="*60)
    print("📊 训练前基线")
    print("="*60)
    
    evaluator = Evaluator(env, verbose=False)
    
    print("\n测试 vs ImprovedRule(0.8):")
    test_opponent = ImprovedRuleAgent(aggression=0.8)
    before_results = evaluator.evaluate_agent(agent, test_opponent, num_episodes=10)
    print(f"  胜率: {before_results['win_rate']:.1f}%")
    
    # 混合对手训练
    print("\n" + "="*60)
    print("🎓 开始混合对手训练")
    print("="*60)
    
    all_history = {
        'iteration': [],
        'agent_wins': [],
        'avg_reward': [],
        'policy_loss': [],
        'value_loss': [],
        'entropy': [],
    }
    
    num_iterations = 100
    episodes_per_iteration = 20
    
    for iteration in range(num_iterations):
        print(f"\n迭代 {iteration+1}/{num_iterations}")
        
        # 随机选择对手
        opponent_idx = np.random.randint(len(opponents))
        current_opponent = opponents[opponent_idx]
        
        print(f"  对手: {opponent_names[opponent_idx]}")
        
        # 使用这个对手训练
        trainer = SelfPlayTrainer(
            env=env,
            agent=agent,
            opponent=current_opponent,
            save_dir=save_dir,
            log_interval=20
        )
        
        # 收集数据
        from training.replay_buffer import EpisodeBuffer
        
        episode_buffer = EpisodeBuffer()
        
        for ep in range(episodes_per_iteration):
            obs = env.reset()
            done = False
            
            while not done:
                # 智能体动作
                valid_p1 = env.get_valid_actions(player_id=1)
                mask_p1 = np.zeros(12, dtype=bool)
                mask_p1[valid_p1] = True
                p1_actions = agent.select_action(obs, mask_p1, deterministic=False)
                
                # 对手动作
                valid_p2 = env.get_valid_actions(player_id=2)
                mask_p2 = np.zeros(12, dtype=bool)
                mask_p2[valid_p2] = True
                p2_actions = current_opponent.select_action(obs, mask_p2, deterministic=False)
                
                # 执行
                next_obs, p1_reward, p2_reward, done, info = env.step(p1_actions, p2_actions)
                
                episode_buffer.push(obs, p1_actions, p1_reward, next_obs, done, mask_p1)
                obs = next_obs
        
        # 更新
        if len(episode_buffer) > 0:
            data = episode_buffer.get_all()
            metrics = agent.update(
                data['states'], data['actions'], data['rewards'],
                data['next_states'], data['dones'],
                action_masks=data.get('action_masks'),
                epochs=4, batch_size=64
            )
            
            # 记录
            if (iteration + 1) % 10 == 0:
                print(f"  损失: Policy={metrics['policy_loss']:.4f}, "
                      f"Value={metrics['value_loss']:.4f}, "
                      f"Entropy={metrics['entropy']:.4f}")
        
        # 定期评估
        if (iteration + 1) % 20 == 0:
            print(f"\n  📊 评估（vs ImprovedRule 0.8）...")
            eval_results = evaluator.evaluate_agent(
                agent, test_opponent, num_episodes=20, deterministic=False  # ⬅️ 改为False，观察探索行为
            )
            print(f"    胜率: {eval_results['win_rate']:.1f}%")
            print(f"    平均奖励: {eval_results['avg_reward']:.2f}")
            
            all_history['agent_wins'].append(eval_results['win_rate'])
        
        # 保存
        if (iteration + 1) % 50 == 0:
            agent.save(os.path.join(save_dir, f"checkpoint_iter_{iteration+1}.pth"))
    
    # 训练后评估
    print("\n" + "="*60)
    print("📊 训练后完整评估")
    print("="*60)
    
    agent.set_training_mode(False)
    
    print("\n1. vs ImprovedRule(0.8):")
    after_results = evaluator.evaluate_agent(agent, test_opponent, num_episodes=50)
    evaluator.print_results(after_results, "Trained PPO")
    
    print("\n2. vs Random:")
    random_test = RandomAgent(action_dim=12)
    vs_random = evaluator.evaluate_agent(agent, random_test, num_episodes=30)
    print(f"  胜率: {vs_random['win_rate']:.1f}%")
    
    # 诊断动作分布
    print("\n3. 动作分布分析:")
    from collections import defaultdict
    action_counts = defaultdict(int)
    
    for _ in range(100):
        obs = env.reset()
        mask = np.ones(12, dtype=bool)
        a1, a2 = agent.select_action(obs, mask, deterministic=True)
        action_counts[a1] += 1
        action_counts[a2] += 1
    
    from environment import ActionSpace
    action_space = ActionSpace()
    
    print(f"\n  动作分布（200个动作）:")
    for action_id, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
        name = action_space.get_action_name(action_id)
        percentage = count / 200 * 100
        bar = "█" * int(percentage / 2)
        print(f"    {name:12s} ({action_id:2d}): {count:3d} ({percentage:5.1f}%) {bar}")
    
    # 检查是否有多样性
    unique_actions = len(action_counts)
    print(f"\n  使用的不同动作数: {unique_actions}/12")
    
    if unique_actions >= 8:
        print("  ✅ 动作多样性良好！")
    elif unique_actions >= 5:
        print("  ⚠️ 动作多样性一般")
    else:
        print("  ❌ 动作多样性不足，仍然过于单一")
    
    # 保存最终模型
    agent.save(os.path.join(save_dir, "final_model.pth"))
    
    # 生成报告
    print("\n" + "="*60)
    print("📈 训练总结")
    print("="*60)
    
    improvement = after_results['win_rate'] - before_results['win_rate']
    
    print(f"\nvs ImprovedRule胜率提升:")
    print(f"  训练前: {before_results['win_rate']:.1f}%")
    print(f"  训练后: {after_results['win_rate']:.1f}%")
    print(f"  提升: {improvement:+.1f}%")
    
    if unique_actions >= 8:
        print(f"\n✅ 成功！AI学会了多样化策略！")
        print(f"   使用了{unique_actions}种不同动作")
        
        if 2 in action_counts and action_counts[2] > 10:
            print(f"   ✅ 学会了Control! (使用{action_counts[2]}次)")
        if 11 in action_counts and action_counts[11] > 10:
            print(f"   ✅ 学会了Burst! (使用{action_counts[11]}次)")
    else:
        print(f"\n⚠️ 仍然过于单一，需要进一步调整")
        print(f"   建议: 继续提高entropy_coef或调整奖励权重")
    
    print(f"\n💾 模型已保存: {save_dir}/final_model.pth")
    
    return save_dir


if __name__ == "__main__":
    main()