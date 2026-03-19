"""
rule_based_agent.py
规则基线智能体 - 基于简单规则的策略 / Rule-Based Agent - Simple Heuristic Strategy

提供基础的游戏策略作为训练对比基线
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


class RuleBasedAgent(BaseAgent):
    """
    规则基线智能体
    
    使用简单的启发式规则进行决策：
    1. 近距离优先攻击
    2. 中距离尝试控制
    3. 远距离移动接近
    4. 低血量时防御
    5. 蓄力提升伤害
    """
    
    def __init__(self, 
                 action_dim: int = 12,
                 aggression: float = 0.7):
        """
        初始化规则智能体
        
        Args:
            action_dim: 动作维度
            aggression: 攻击性系数 (0-1)，越高越激进
        """
        super().__init__(agent_name="RuleBasedAgent")
        
        self.action_dim = action_dim
        self.aggression = aggression
        
        # 动作映射（与环境对应）
        self.ACTION_MAP = {
            'attack': 0,
            'charge': 1,
            'control': 2,
            'grab': 3,
            'throw': 4,
            'defend': 5,
            'counter': 6,
            'move_left': 7,
            'move_right': 8,
            'dash_left': 9,
            'dash_right': 10,
            'burst': 11
        }
        
        # 状态解析索引（基于StateEncoder的54维编码）
        self.IDX_P1_HP = 0        # 玩家1 HP
        self.IDX_P1_POS = 1       # 玩家1 位置
        self.IDX_P1_CHARGE = 2    # 玩家1 蓄力（one-hot 3维）
        self.IDX_P1_CONTROLLED = 8  # 玩家1 被控制
        
        self.IDX_P2_HP = 18       # 玩家2 HP
        self.IDX_P2_POS = 19      # 玩家2 位置
        
        self.IDX_DISTANCE = 36    # 距离
        self.IDX_TURN = 37        # 回合数
    
    def select_action(self,
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        基于规则选择动作
        
        Args:
            observation: 观察（54维状态向量）
            valid_actions: 有效动作掩码
            deterministic: 是否确定性（规则总是确定性的）
        
        Returns:
            (action1, action2): 两个动作
        """
        # 解析状态
        my_hp = observation[self.IDX_P1_HP]
        my_pos = observation[self.IDX_P1_POS]
        opp_hp = observation[self.IDX_P2_HP]
        opp_pos = observation[self.IDX_P2_POS]
        distance_norm = observation[self.IDX_DISTANCE]
        
        # 计算实际距离（反归一化，假设MAP_SIZE=6）
        distance = int(distance_norm * 6)
        
        # 解析蓄力等级
        charge_vec = observation[self.IDX_P1_CHARGE:self.IDX_P1_CHARGE+3]
        charge_level = int(np.argmax(charge_vec))
        
        # 被控制状态
        is_controlled = observation[self.IDX_P1_CONTROLLED] > 0.5
        
        # 确定有效动作
        if valid_actions is not None:
            valid_action_ids = np.where(valid_actions)[0] if valid_actions.dtype == bool else valid_actions
        else:
            valid_action_ids = np.arange(self.action_dim)
        
        # 规则决策
        action1 = self._decide_action(
            distance, my_hp, opp_hp, charge_level, is_controlled, valid_action_ids
        )
        action2 = self._decide_action(
            distance, my_hp, opp_hp, charge_level, is_controlled, valid_action_ids,
            previous_action=action1
        )
        
        return action1, action2
    
    def _decide_action(self,
                      distance: int,
                      my_hp: float,
                      opp_hp: float,
                      charge_level: int,
                      is_controlled: bool,
                      valid_actions: np.ndarray,
                      previous_action: Optional[int] = None) -> int:
        """
        根据规则决定一个动作
        
        Args:
            distance: 距离
            my_hp: 我的血量（归一化）
            opp_hp: 对手血量（归一化）
            charge_level: 蓄力等级
            is_controlled: 是否被控制
            valid_actions: 有效动作列表
            previous_action: 上一个动作（如果是第二个动作）
        
        Returns:
            动作ID
        """
        # 如果被控制，只能防御或爆血
        if is_controlled:
            if self.ACTION_MAP['defend'] in valid_actions:
                return self.ACTION_MAP['defend']
            elif self.ACTION_MAP['burst'] in valid_actions:
                return self.ACTION_MAP['burst']
        
        # 规则1: 低血量（<30%）时优先防御
        if my_hp < 0.3:
            if self.ACTION_MAP['counter'] in valid_actions:
                return self.ACTION_MAP['counter']
            elif self.ACTION_MAP['defend'] in valid_actions:
                return self.ACTION_MAP['defend']
        
        # 规则2: 距离为0，尝试grab/throw
        if distance == 0:
            if self.ACTION_MAP['grab'] in valid_actions:
                return self.ACTION_MAP['grab']
            elif self.ACTION_MAP['throw'] in valid_actions:
                return self.ACTION_MAP['throw']
        
        # 规则3: 近距离（距离<=1）优先攻击
        if distance <= 1:
            # 如果有蓄力2，直接攻击
            if charge_level == 2 and self.ACTION_MAP['attack'] in valid_actions:
                return self.ACTION_MAP['attack']
            
            # 根据攻击性决定
            if np.random.random() < self.aggression:
                if self.ACTION_MAP['attack'] in valid_actions:
                    return self.ACTION_MAP['attack']
            else:
                # 防御反击
                if self.ACTION_MAP['counter'] in valid_actions:
                    return self.ACTION_MAP['counter']
        
        # 规则4: 中距离（距离2-3）尝试控制或蓄力
        if 2 <= distance <= 3:
            # 如果没有蓄力，先蓄力
            if charge_level == 0 and self.ACTION_MAP['charge'] in valid_actions:
                # 避免连续两次蓄力
                if previous_action != self.ACTION_MAP['charge']:
                    return self.ACTION_MAP['charge']
            
            # 尝试控制
            if self.ACTION_MAP['control'] in valid_actions and np.random.random() < 0.6:
                return self.ACTION_MAP['control']
        
        # 规则5: 远距离（距离>3）接近对手
        if distance > 3:
            # 判断对手在左还是右（简化处理）
            # 假设左移是接近（需要根据实际位置判断）
            if self.ACTION_MAP['dash_right'] in valid_actions and np.random.random() < 0.7:
                return self.ACTION_MAP['dash_right']
            elif self.ACTION_MAP['move_right'] in valid_actions:
                return self.ACTION_MAP['move_right']
        
        # 规则6: 有蓄力但未使用，优先攻击
        if charge_level > 0 and self.ACTION_MAP['attack'] in valid_actions:
            return self.ACTION_MAP['attack']
        
        # 默认：随机选择有效动作
        return int(np.random.choice(valid_actions))
    
    def update(self, *args, **kwargs) -> Dict[str, float]:
        """规则智能体不需要更新"""
        return {}
    
    def save(self, path: str):
        """规则智能体不需要保存"""
        print(f"RuleBasedAgent 不需要保存模型")
    
    def load(self, path: str):
        """规则智能体不需要加载"""
        print(f"RuleBasedAgent 不需要加载模型")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            'action_dim': self.action_dim,
            'aggression': self.aggression,
        })
        return stats


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 RuleBasedAgent...")
    
    # 测试1: 创建规则智能体
    print("\n测试1: 创建规则智能体")
    agent = RuleBasedAgent(action_dim=12, aggression=0.7)
    
    stats = agent.get_stats()
    print("智能体统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试2: 不同场景下的决策
    print("\n测试2: 不同场景下的决策")
    
    # 创建模拟状态
    def create_test_state(my_hp=1.0, distance_norm=0.5, charge_level=0, controlled=False):
        state = np.zeros(54)
        state[0] = my_hp         # 我的HP
        state[1] = 0.5           # 我的位置
        state[2:5] = [1, 0, 0]   # 蓄力one-hot
        if charge_level == 1:
            state[2:5] = [0, 1, 0]
        elif charge_level == 2:
            state[2:5] = [0, 0, 1]
        state[8] = 1.0 if controlled else 0.0  # 被控制
        state[18] = 0.8          # 对手HP
        state[19] = 0.7          # 对手位置
        state[36] = distance_norm  # 距离
        return state
    
    # 场景1: 近距离，满血
    print("\n场景1: 近距离(距离1)，满血")
    state1 = create_test_state(my_hp=1.0, distance_norm=1/6)
    for i in range(3):
        action1, action2 = agent.select_action(state1)
        print(f"  尝试 {i+1}: ({action1}, {action2})")
    
    # 场景2: 中距离，需要蓄力
    print("\n场景2: 中距离(距离3)，无蓄力")
    state2 = create_test_state(my_hp=1.0, distance_norm=3/6, charge_level=0)
    for i in range(3):
        action1, action2 = agent.select_action(state2)
        print(f"  尝试 {i+1}: ({action1}, {action2})")
    
    # 场景3: 低血量
    print("\n场景3: 近距离，低血量(20%)")
    state3 = create_test_state(my_hp=0.2, distance_norm=1/6)
    for i in range(3):
        action1, action2 = agent.select_action(state3)
        print(f"  尝试 {i+1}: ({action1}, {action2})")
    
    # 场景4: 被控制
    print("\n场景4: 被控制状态")
    state4 = create_test_state(my_hp=0.8, distance_norm=0, controlled=True)
    for i in range(3):
        action1, action2 = agent.select_action(state4)
        print(f"  尝试 {i+1}: ({action1}, {action2})")
    
    # 场景5: 有蓄力2
    print("\n场景5: 近距离，有蓄力2")
    state5 = create_test_state(my_hp=0.8, distance_norm=1/6, charge_level=2)
    for i in range(3):
        action1, action2 = agent.select_action(state5)
        print(f"  尝试 {i+1}: ({action1}, {action2})")
    
    # 测试3: 不同攻击性参数
    print("\n测试3: 不同攻击性参数")
    
    state = create_test_state(my_hp=0.5, distance_norm=1/6)
    
    aggressive_agent = RuleBasedAgent(aggression=0.9)
    defensive_agent = RuleBasedAgent(aggression=0.3)
    
    print("激进智能体 (aggression=0.9):")
    for i in range(3):
        action1, action2 = aggressive_agent.select_action(state)
        print(f"  选择 {i+1}: ({action1}, {action2})")
    
    print("\n保守智能体 (aggression=0.3):")
    for i in range(3):
        action1, action2 = defensive_agent.select_action(state)
        print(f"  选择 {i+1}: ({action1}, {action2})")
    
    # 测试4: 动作分布统计
    print("\n测试4: 动作分布统计")
    
    state = create_test_state(my_hp=0.8, distance_norm=2/6)
    action_counts = {i: 0 for i in range(12)}
    
    num_samples = 100
    for _ in range(num_samples):
        action1, action2 = agent.select_action(state)
        action_counts[action1] += 1
        action_counts[action2] += 1
    
    print(f"在中距离场景下，采样{num_samples}次的动作分布:")
    action_names = ['attack', 'charge', 'control', 'grab', 'throw', 
                   'defend', 'counter', 'move_l', 'move_r', 
                   'dash_l', 'dash_r', 'burst']
    
    for action_id, count in action_counts.items():
        if count > 0:
            percentage = count / (num_samples * 2) * 100
            print(f"  {action_names[action_id]:8s} ({action_id:2d}): {count:3d} 次 ({percentage:5.1f}%)")
    
    # 测试5: 性能测试
    print("\n测试5: 性能测试")
    import time
    
    state = create_test_state()
    num_selections = 10000
    
    start_time = time.time()
    for _ in range(num_selections):
        agent.select_action(state)
    end_time = time.time()
    
    elapsed = end_time - start_time
    selections_per_sec = num_selections / elapsed
    
    print(f"完成 {num_selections} 次决策")
    print(f"耗时: {elapsed:.4f} 秒")
    print(f"速度: {selections_per_sec:.0f} 次/秒")
    
    print("\n✅ RuleBasedAgent 测试完成！")