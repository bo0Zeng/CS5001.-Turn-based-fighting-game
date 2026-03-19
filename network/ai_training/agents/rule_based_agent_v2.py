"""
rule_based_agent_v2.py
改进的规则智能体 - 修复过度防御问题 / Improved Rule-Based Agent - Fix Over-Defensive Issue

主要改进：
1. 不再总是防御
2. 更主动的进攻策略
3. 距离感知更好
4. 避免陷入防御循环
"""

import sys
import os
from typing import Tuple, Optional, Dict, Any
import numpy as np
from collections import defaultdict

current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from agents.base_agent import BaseAgent


class ImprovedRuleAgent(BaseAgent):
    """
    改进的规则智能体
    
    更主动、更有攻击性的策略
    """
    
    def __init__(self, aggression: float = 0.8):
        """
        初始化改进规则智能体
        
        Args:
            aggression: 攻击性 (0.5-1.0推荐)
        """
        super().__init__(agent_name="ImprovedRuleAgent")
        
        self.aggression = aggression
        
        # 动作映射
        self.ACTION_MAP = {
            'attack': 0, 'charge': 1, 'control': 2,
            'grab': 3, 'throw': 4, 'defend': 5, 'counter': 6,
            'move_left': 7, 'move_right': 8,
            'dash_left': 9, 'dash_right': 10, 'burst': 11
        }
        
        # 状态索引
        self.IDX_P1_HP = 0
        self.IDX_P1_POS = 1
        self.IDX_P1_CHARGE = 2
        self.IDX_P1_CONTROLLED = 8
        self.IDX_P2_HP = 18
        self.IDX_P2_POS = 19
        self.IDX_DISTANCE = 36
        
        # 防御计数器（避免过度防御）
        self.defense_count = 0
        self.last_action = None
    
    def select_action(self,
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        基于改进规则选择动作
        
        Args:
            observation: 66维状态
            valid_actions: 有效动作掩码
            deterministic: 是否确定性
        
        Returns:
            (action1, action2)
        """
        # 解析状态
        my_hp = observation[self.IDX_P1_HP]
        opp_hp = observation[self.IDX_P2_HP]
        distance_norm = observation[self.IDX_DISTANCE]
        distance = int(distance_norm * 6)
        
        charge_vec = observation[self.IDX_P1_CHARGE:self.IDX_P1_CHARGE+3]
        charge_level = int(np.argmax(charge_vec))
        
        is_controlled = observation[self.IDX_P1_CONTROLLED] > 0.5
        
        # 有效动作
        if valid_actions is not None:
            valid_ids = np.where(valid_actions)[0] if valid_actions.dtype == bool else valid_actions
        else:
            valid_ids = np.arange(12)
        
        # 选择两个动作
        action1 = self._decide_action_v2(
            distance, my_hp, opp_hp, charge_level, is_controlled, valid_ids
        )
        action2 = self._decide_action_v2(
            distance, my_hp, opp_hp, charge_level, is_controlled, valid_ids,
            previous_action=action1
        )
        
        # 更新防御计数
        if action1 in [5, 6] and action2 in [5, 6]:
            self.defense_count += 1
        else:
            self.defense_count = 0
        
        return action1, action2
    
    def _decide_action_v2(self,
                         distance: int,
                         my_hp: float,
                         opp_hp: float,
                         charge_level: int,
                         is_controlled: bool,
                         valid_actions: np.ndarray,
                         previous_action: Optional[int] = None) -> int:
        """
        改进的决策逻辑（更激进）
        
        优先级：
        1. 被控制 → 爆血/防御
        2. 连续防御>3次 → 强制进攻
        3. 距离0 → grab/throw
        4. 距离1-2 → 攻击（主要策略）
        5. 有蓄力 → 攻击
        6. 远距离 → 接近
        7. 低血量 → 偶尔防御
        """
        ACT = self.ACTION_MAP
        
        # 规则1: 被控制状态
        if is_controlled:
            if np.random.random() < 0.3 and ACT['burst'] in valid_actions:
                return ACT['burst']
            elif ACT['defend'] in valid_actions:
                return ACT['defend']
        
        # 规则2: 强制打破防御循环（关键修复！）
        if self.defense_count >= 3:
            # 强制选择非防御动作
            offensive_actions = [a for a in valid_actions if a not in [5, 6]]
            if offensive_actions:
                # 优先选择攻击
                if ACT['attack'] in offensive_actions:
                    return ACT['attack']
                # 其次选择移动
                if ACT['dash_right'] in offensive_actions:
                    return ACT['dash_right']
                return int(np.random.choice(offensive_actions))
        
        # 规则3: 距离0，使用grab/throw
        if distance == 0:
            if ACT['grab'] in valid_actions:
                return ACT['grab']
            elif ACT['throw'] in valid_actions:
                return ACT['throw']
        
        # 规则4: 近距离（1-2格）- 主动进攻！
        if 1 <= distance <= 2:
            # 有蓄力立即攻击
            if charge_level >= 1 and ACT['attack'] in valid_actions:
                return ACT['attack']
            
            # 高概率攻击
            if np.random.random() < self.aggression:
                if ACT['attack'] in valid_actions:
                    return ACT['attack']
                elif ACT['control'] in valid_actions:
                    return ACT['control']
            
            # 否则蓄力
            if charge_level == 0 and ACT['charge'] in valid_actions:
                if previous_action != ACT['charge']:  # 避免两次都蓄力
                    return ACT['charge']
            
            # 最后才考虑防御（低概率）
            if np.random.random() < (1 - self.aggression) * 0.5:
                if ACT['counter'] in valid_actions:
                    return ACT['counter']
        
        # 规则5: 中距离（3-4格）
        if 3 <= distance <= 4:
            # 蓄力准备
            if charge_level == 0 and ACT['charge'] in valid_actions:
                if previous_action != ACT['charge']:
                    return ACT['charge']
            
            # 尝试接近
            if ACT['dash_right'] in valid_actions and np.random.random() < 0.5:
                return ACT['dash_right']
            
            # 尝试控制
            if ACT['control'] in valid_actions and np.random.random() < 0.4:
                return ACT['control']
        
        # 规则6: 远距离（>4格）- 主动接近
        if distance > 4:
            if ACT['dash_right'] in valid_actions:
                return ACT['dash_right']
            elif ACT['move_right'] in valid_actions:
                return ACT['move_right']
        
        # 规则7: 低血量应急
        if my_hp < 0.25:
            # 爆血反击
            if distance <= 2 and ACT['burst'] in valid_actions:
                if np.random.random() < 0.5:
                    return ACT['burst']
            # 防御
            if ACT['counter'] in valid_actions and np.random.random() < 0.4:
                return ACT['counter']
        
        # 默认：优先进攻性动作
        priority_actions = [
            ACT['attack'], ACT['control'], ACT['charge'],
            ACT['move_right'], ACT['dash_right']
        ]
        
        for action in priority_actions:
            if action in valid_actions:
                return action
        
        # 实在没办法才随机
        return int(np.random.choice(valid_actions))
    
    def update(self, *args, **kwargs) -> Dict[str, float]:
        return {}
    
    def save(self, path: str):
        print(f"ImprovedRuleAgent 不需要保存")
    
    def load(self, path: str):
        print(f"ImprovedRuleAgent 不需要加载")
    
    def reset(self):
        """重置状态（新episode）"""
        self.defense_count = 0
        self.last_action = None


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 ImprovedRuleAgent...")
    
    agent = ImprovedRuleAgent(aggression=0.8)
    
    # 创建测试状态
    def create_state(distance_norm=0.5):
        state = np.zeros(66)
        state[0] = 1.0          # HP
        state[1] = 0.5          # 位置
        state[2:5] = [1, 0, 0]  # 无蓄力
        state[36] = distance_norm  # 距离
        return state
    
    print("\n测试不同距离下的动作选择:")
    
    for dist in [0, 1, 2, 3, 5]:
        state = create_state(distance_norm=dist/6)
        
        action_dist = defaultdict(int)
        for _ in range(20):
            a1, a2 = agent.select_action(state)
            action_dist[a1] += 1
            action_dist[a2] += 1
        
        top_actions = sorted(action_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        
        action_names = {v: k for k, v in agent.ACTION_MAP.items()}
        top_names = [(action_names[a], c) for a, c in top_actions]
        
        print(f"  距离{dist}: {top_names}")
    
    print("\n✅ ImprovedRuleAgent 测试完成！")