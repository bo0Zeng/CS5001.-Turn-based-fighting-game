"""
diagnose_behavior.py
诊断智能体行为 / Diagnose Agent Behavior

分析智能体在不同场景下的行为模式
"""

import sys
import os
from collections import defaultdict

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

import numpy as np
import torch
from environment import BattleEnv, ActionSpace
from agents import PPOAgent, RuleBasedAgent


def analyze_action_distribution(agent, env, num_samples=100, scenario_name="默认"):
    """
    分析智能体的动作分布
    
    Args:
        agent: 智能体
        env: 环境
        num_samples: 采样次数
        scenario_name: 场景名称
    """
    action_space = ActionSpace()
    action_counts = defaultdict(int)
    
    for _ in range(num_samples):
        obs = env.reset()
        
        # 选择动作
        valid_actions = env.get_valid_actions(player_id=1)
        mask = np.zeros(12, dtype=bool)
        mask[valid_actions] = True
        
        action1, action2 = agent.select_action(obs, mask, deterministic=True)
        
        action_counts[action1] += 1
        action_counts[action2] += 1
    
    print(f"\n场景: {scenario_name}")
    print(f"动作分布（采样{num_samples}次，共{num_samples*2}个动作）:")
    print("-" * 60)
    
    # 排序显示
    sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
    
    for action_id, count in sorted_actions:
        action_name = action_space.get_action_name(action_id)
        percentage = count / (num_samples * 2) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {action_name:12s} ({action_id:2d}): {count:4d} 次 ({percentage:5.1f}%) {bar}")


def watch_single_game(agent1, agent2, env, verbose=True):
    """
    观看一场完整对局，记录详细信息
    
    Args:
        agent1: 玩家1智能体
        agent2: 玩家2智能体
        env: 环境
        verbose: 是否打印详细信息
    """
    action_space = ActionSpace()
    
    obs = env.reset()
    done = False
    turn = 0
    
    action_log = []
    
    if verbose:
        print("\n" + "="*60)
        print("📺 观看对局")
        print("="*60)
    
    while not done:
        turn += 1
        
        # 双方选择动作
        valid_p1 = env.get_valid_actions(player_id=1)
        mask_p1 = np.zeros(12, dtype=bool)
        mask_p1[valid_p1] = True
        p1_actions = agent1.select_action(obs, mask_p1, deterministic=True)
        
        valid_p2 = env.get_valid_actions(player_id=2)
        mask_p2 = np.zeros(12, dtype=bool)
        mask_p2[valid_p2] = True
        p2_actions = agent2.select_action(obs, mask_p2, deterministic=True)
        
        # 记录
        p1_names = [action_space.get_action_name(a) for a in p1_actions]
        p2_names = [action_space.get_action_name(a) for a in p2_actions]
        
        action_log.append({
            'turn': turn,
            'p1_actions': p1_actions,
            'p2_actions': p2_actions,
            'p1_names': p1_names,
            'p2_names': p2_names,
            'distance': env.combat.get_distance(),
        })
        
        if verbose:
            print(f"\n回合 {turn} | 距离: {env.combat.get_distance()}")
            print(f"  P1: {p1_names}")
            print(f"  P2: {p2_names}")
        
        # 执行
        obs, p1_reward, p2_reward, done, info = env.step(p1_actions, p2_actions)
        
        if verbose:
            print(f"  奖励: P1={p1_reward:.1f}, P2={p2_reward:.1f}")
            print(f"  HP: P1={env.player1.hp}, P2={env.player2.hp}")
    
    if verbose:
        print(f"\n游戏结束！胜者: {info.get('winner')}")
        print(f"总回合: {turn}")
    
    return action_log, info


def diagnose_model(model_path: str):
    """
    诊断模型行为
    
    Args:
        model_path: 模型路径
    """
    print("="*80)
    print("🔍 模型行为诊断 / Model Behavior Diagnosis")
    print("="*80)
    
    # 加载模型
    device = torch.device('cpu')
    agent = PPOAgent(state_dim=66, action_dim=12, device=device)
    
    if os.path.exists(model_path):
        agent.load(model_path)
        print(f"✅ 模型已加载: {model_path}")
    else:
        print(f"⚠️  使用未训练模型")
    
    agent.set_training_mode(False)
    
    # 创建环境和对手
    env = BattleEnv(reward_type='dense', verbose=False)
    rule_agent = RuleBasedAgent(action_dim=12, aggression=0.7)
    
    # 测试1: 动作分布分析
    print("\n" + "="*60)
    print("测试1: 动作分布分析")
    print("="*60)
    
    analyze_action_distribution(agent, env, num_samples=100, scenario_name="PPO Agent")
    analyze_action_distribution(rule_agent, env, num_samples=100, scenario_name="Rule Agent")
    
    # 测试2: 观看对局
    print("\n" + "="*60)
    print("测试2: 观看PPO vs Rule对局")
    print("="*60)
    
    action_log, info = watch_single_game(agent, rule_agent, env, verbose=True)
    
    # 测试3: 分析僵持原因
    print("\n" + "="*60)
    print("测试3: 僵持分析")
    print("="*60)
    
    # 统计动作模式
    p1_action_freq = defaultdict(int)
    p2_action_freq = defaultdict(int)
    
    for log in action_log:
        for action in log['p1_actions']:
            p1_action_freq[action] += 1
        for action in log['p2_actions']:
            p2_action_freq[action] += 1
    
    action_space = ActionSpace()
    
    print("\nPPO动作频率:")
    for action_id, count in sorted(p1_action_freq.items(), key=lambda x: x[1], reverse=True):
        name = action_space.get_action_name(action_id)
        print(f"  {name:12s}: {count} 次")
    
    print("\nRule动作频率:")
    for action_id, count in sorted(p2_action_freq.items(), key=lambda x: x[1], reverse=True):
        name = action_space.get_action_name(action_id)
        print(f"  {name:12s}: {count} 次")
    
    # 测试4: 不同距离下的行为
    print("\n" + "="*60)
    print("测试4: 不同距离下的偏好动作")
    print("="*60)
    
    # 手动构造不同距离的状态
    for distance in [0, 1, 2, 3, 5]:
        # 创建一个简化的状态（正常初始化，但修改距离）
        obs = env.reset()
        # 直接修改距离特征（第36维）
        obs_modified = obs.copy()
        obs_modified[36] = distance / 6.0  # 归一化距离
        
        # 采样多次看偏好
        action_dist = defaultdict(int)
        for _ in range(20):
            mask = np.ones(12, dtype=bool)
            action1, action2 = agent.select_action(obs_modified, mask, deterministic=True)
            action_dist[action1] += 1
            action_dist[action2] += 1
        
        top_action = max(action_dist.items(), key=lambda x: x[1])
        top_name = action_space.get_action_name(top_action[0])
        
        print(f"  距离{distance}: 最常用动作 = {top_name} ({top_action[1]}/40 次)")
    
    # 总结
    print("\n" + "="*80)
    print("🔍 诊断总结")
    print("="*80)
    
    if info['winner'] == 'Draw':
        print("⚠️  检测到僵持问题：")
        print("  - PPO vs Rule 所有对局都是平局")
        print("  - 双方都没有造成伤害")
        print("\n可能原因:")
        print("  1. 规则智能体过于保守（只防御）")
        print("  2. PPO只对Random训练，没见过攻击性策略")
        print("  3. 奖励函数鼓励了过度防御")
        print("\n建议:")
        print("  1. 使用 vs Rule 进行训练：")
        print("     python training/train_ppo.py --opponent rule --iterations 200")
        print("  2. 调整规则智能体的攻击性：")
        print("     RuleBasedAgent(aggression=0.9) 更激进")
        print("  3. 修改奖励函数，惩罚过度防御")
    else:
        print("✅ 对局正常，有胜负")
    
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, 
                       default='saved_models/complete_run_20251130_025018/final_model.pth',
                       help='模型路径')
    
    args = parser.parse_args()
    
    diagnose_model(args.model)