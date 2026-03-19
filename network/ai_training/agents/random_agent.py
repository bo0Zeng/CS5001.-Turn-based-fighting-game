"""
random_agent.py
随机智能体 - 用于基线对比 / Random Agent - Baseline for Comparison

随机选择有效动作，用于评估训练智能体的性能提升
"""

import sys
import os
from typing import Tuple, Optional, Dict, Any
import numpy as np

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from agents.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    """
    随机智能体
    
    从有效动作中随机选择，不进行学习
    """
    
    def __init__(self, 
                 action_dim: int = 12,
                 seed: Optional[int] = None):
        """
        初始化随机智能体
        
        Args:
            action_dim: 动作维度
            seed: 随机种子
        """
        super().__init__(agent_name="RandomAgent")
        
        self.action_dim = action_dim
        
        if seed is not None:
            np.random.seed(seed)
            self.seed = seed
        else:
            self.seed = None
    
    def select_action(self,
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        随机选择动作
        
        Args:
            observation: 观察（不使用）
            valid_actions: 有效动作掩码
            deterministic: 是否确定性选择（不使用，总是随机）
        
        Returns:
            (action1, action2): 两个随机动作
        """
        # 确定有效动作列表
        if valid_actions is not None:
            # 如果是布尔数组
            if valid_actions.dtype == bool:
                valid_action_ids = np.where(valid_actions)[0]
            else:
                # 假设是动作ID列表
                valid_action_ids = valid_actions
        else:
            # 所有动作都有效
            valid_action_ids = np.arange(self.action_dim)
        
        # 随机选择两个动作
        action1 = np.random.choice(valid_action_ids)
        action2 = np.random.choice(valid_action_ids)
        
        return int(action1), int(action2)
    
    def update(self, *args, **kwargs) -> Dict[str, float]:
        """
        随机智能体不需要更新
        
        Returns:
            空字典
        """
        return {}
    
    def save(self, path: str):
        """随机智能体不需要保存"""
        print(f"RandomAgent 不需要保存模型")
    
    def load(self, path: str):
        """随机智能体不需要加载"""
        print(f"RandomAgent 不需要加载模型")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            'action_dim': self.action_dim,
            'seed': self.seed,
        })
        return stats


class UniformRandomAgent(RandomAgent):
    """
    均匀随机智能体
    
    在所有动作上均匀随机选择（不考虑有效性）
    用于最基础的性能基线
    """
    
    def __init__(self, action_dim: int = 12, seed: Optional[int] = None):
        super().__init__(action_dim, seed)
        self.agent_name = "UniformRandomAgent"
    
    def select_action(self,
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        均匀随机选择（忽略有效性）
        
        Returns:
            (action1, action2): 两个随机动作
        """
        action1 = np.random.randint(0, self.action_dim)
        action2 = np.random.randint(0, self.action_dim)
        return action1, action2


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 RandomAgent...")
    
    # 测试1: 基础随机智能体
    print("\n测试1: 基础随机智能体")
    agent = RandomAgent(action_dim=12, seed=42)
    
    print(f"智能体名称: {agent.get_name()}")
    print(f"动作维度: {agent.action_dim}")
    
    # 测试2: 无掩码的随机选择
    print("\n测试2: 无掩码的随机选择")
    obs = np.random.randn(54)
    
    for i in range(5):
        action1, action2 = agent.select_action(obs)
        print(f"  选择 {i+1}: ({action1}, {action2})")
    
    # 测试3: 带掩码的随机选择
    print("\n测试3: 带掩码的随机选择")
    
    # 布尔掩码
    mask = np.array([True] * 12)
    mask[[3, 4, 11]] = False  # 禁用 grab, throw, burst
    
    print("有效动作: ", np.where(mask)[0])
    
    action_counts = {i: 0 for i in range(12)}
    num_samples = 1000
    
    for _ in range(num_samples):
        action1, action2 = agent.select_action(obs, valid_actions=mask)
        action_counts[action1] += 1
        action_counts[action2] += 1
    
    print(f"采样 {num_samples} 次，动作分布:")
    for action_id, count in action_counts.items():
        if count > 0:
            print(f"  动作 {action_id}: {count} 次 ({count/num_samples/2*100:.1f}%)")
        else:
            print(f"  动作 {action_id}: 0 次 (应该被禁用)")
    
    # 验证禁用的动作没有被选择
    if action_counts[3] == 0 and action_counts[4] == 0 and action_counts[11] == 0:
        print("✅ 掩码工作正常！")
    else:
        print("❌ 掩码失效！")
    
    # 测试4: 统计信息
    print("\n测试4: 统计信息")
    stats = agent.get_stats()
    print("智能体统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试5: 更新（应该什么都不做）
    print("\n测试5: 更新")
    metrics = agent.update()
    print(f"更新返回: {metrics}")
    
    # 测试6: 保存和加载（应该什么都不做）
    print("\n测试6: 保存和加载")
    agent.save("test.pth")
    agent.load("test.pth")
    
    # 测试7: 均匀随机智能体
    print("\n测试7: 均匀随机智能体")
    uniform_agent = UniformRandomAgent(action_dim=12, seed=123)
    
    print(f"智能体名称: {uniform_agent.get_name()}")
    
    # 即使有掩码，也会忽略
    for i in range(5):
        action1, action2 = uniform_agent.select_action(obs, valid_actions=mask)
        print(f"  选择 {i+1}: ({action1}, {action2})")
        if action1 in [3, 4, 11] or action2 in [3, 4, 11]:
            print(f"    → 选择了被禁用的动作（这是预期的）")
    
    # 测试8: 随机种子效果
    print("\n测试8: 随机种子效果")
    
    agent1 = RandomAgent(action_dim=12, seed=999)
    agent2 = RandomAgent(action_dim=12, seed=999)
    agent3 = RandomAgent(action_dim=12, seed=111)
    
    # 相同种子应该产生相同序列
    actions1 = [agent1.select_action(obs) for _ in range(5)]
    actions2 = [agent2.select_action(obs) for _ in range(5)]
    actions3 = [agent3.select_action(obs) for _ in range(5)]
    
    print("Agent1 (seed=999):", actions1)
    print("Agent2 (seed=999):", actions2)
    print("Agent3 (seed=111):", actions3)
    
    if actions1 == actions2:
        print("✅ 相同种子产生相同序列")
    else:
        print("❌ 种子失效")
    
    if actions1 != actions3:
        print("✅ 不同种子产生不同序列")
    else:
        print("⚠️ 不同种子产生了相同序列（小概率事件）")
    
    # 测试9: 性能测试
    print("\n测试9: 性能测试")
    import time
    
    agent = RandomAgent(action_dim=12)
    num_selections = 10000
    
    start_time = time.time()
    for _ in range(num_selections):
        agent.select_action(obs, valid_actions=mask)
    end_time = time.time()
    
    elapsed = end_time - start_time
    selections_per_sec = num_selections / elapsed
    
    print(f"完成 {num_selections} 次动作选择")
    print(f"耗时: {elapsed:.4f} 秒")
    print(f"速度: {selections_per_sec:.0f} 次/秒")
    
    print("\n✅ RandomAgent 测试完成！")