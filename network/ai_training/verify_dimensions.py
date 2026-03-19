"""
verify_dimensions.py
验证状态维度是否正确 / Verify State Dimensions

快速检查环境和模型的维度是否匹配
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

import numpy as np
import torch

print("="*60)
print("🔍 维度验证 / Dimension Verification")
print("="*60)

# 测试1: 环境观察维度
print("\n测试1: 环境观察维度")
from environment import BattleEnv

env = BattleEnv(verbose=False)
obs = env.reset()

print(f"✅ 环境创建成功")
print(f"  观察维度: {obs.shape}")
print(f"  期望维度: (66,)")
print(f"  匹配: {'✅' if obs.shape == (66,) else '❌'}")

# 测试2: 模型输入维度
print("\n测试2: 模型输入维度")
from models import ActorCritic

model = ActorCritic(state_dim=66, action_dim=12)
print(f"✅ 模型创建成功")
print(f"  输入维度: 66")
print(f"  输出维度: 12 (动作)")

# 测试前向传播
state_tensor = torch.FloatTensor(obs).unsqueeze(0)
print(f"\n  状态张量形状: {state_tensor.shape}")

try:
    action_probs, values = model(state_tensor)
    print(f"✅ 前向传播成功")
    print(f"  动作概率形状: {action_probs.shape}")
    print(f"  价值形状: {values.shape}")
except Exception as e:
    print(f"❌ 前向传播失败: {e}")

# 测试3: 智能体选择动作
print("\n测试3: 智能体动作选择")
from agents import PPOAgent

agent = PPOAgent(state_dim=66, action_dim=12)
print(f"✅ PPO智能体创建成功")

try:
    action1, action2 = agent.select_action(obs)
    print(f"✅ 动作选择成功: ({action1}, {action2})")
except Exception as e:
    print(f"❌ 动作选择失败: {e}")

# 测试4: 完整流程
print("\n测试4: 完整游戏流程")
obs = env.reset()
done = False
step = 0

try:
    while not done and step < 5:
        # 双方选择动作
        p1_actions = agent.select_action(obs)
        p2_actions = agent.select_action(obs)
        
        # 执行
        obs, p1_reward, p2_reward, done, info = env.step(p1_actions, p2_actions)
        step += 1
        
        print(f"  步骤{step}: 观察维度={obs.shape}, 奖励=({p1_reward:.2f}, {p2_reward:.2f})")
    
    print(f"✅ 完整流程测试成功，共{step}步")
    
except Exception as e:
    print(f"❌ 流程测试失败: {e}")
    import traceback
    traceback.print_exc()

# 汇总
print("\n" + "="*60)
print("📊 验证汇总 / Verification Summary")
print("="*60)
print(f"环境观察维度: {obs.shape[0]} 维")
print(f"模型输入维度: 66 维")
print(f"动作空间大小: 12")
print("="*60)

if obs.shape[0] == 66:
    print("✅ 所有维度匹配！可以开始训练！")
else:
    print(f"❌ 维度不匹配！环境输出{obs.shape[0]}维，模型期望66维")