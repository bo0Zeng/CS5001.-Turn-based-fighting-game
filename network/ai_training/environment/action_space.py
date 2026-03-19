"""
action_space.py
动作空间管理 - 处理动作相关的逻辑 / Action Space Management

提供功能：
- 动作验证
- 动作掩码（Mask）生成
- 动作采样
- 动作转换
"""

import sys
import os
import numpy as np
from typing import List, Tuple, Optional

# 添加父目录到路径，以便导入游戏代码
current_dir = os.path.dirname(os.path.abspath(__file__))  # ai_training/environment/
ai_training_dir = os.path.dirname(current_dir)             # ai_training/
project_root = os.path.dirname(ai_training_dir)            # 项目根目录
sys.path.insert(0, project_root)

from player import Player
from config import *


class ActionSpace:
    """
    动作空间管理器
    
    负责处理所有与动作相关的逻辑
    """
    
    # 动作定义
    ACTIONS = {
        0: 'attack',
        1: 'charge',
        2: 'control',
        3: 'grab',
        4: 'throw',
        5: 'defend',
        6: 'counter',
        7: 'move_left',
        8: 'move_right',
        9: 'dash_left',
        10: 'dash_right',
        11: 'burst'
    }
    
    # 反向映射
    ACTION_TO_ID = {v: k for k, v in ACTIONS.items()}
    
    # 动作分类
    ATTACK_ACTIONS = [0, 2, 3, 4, 11]      # attack, control, grab, throw, burst
    DEFENSE_ACTIONS = [5, 6]                # defend, counter
    MOVEMENT_ACTIONS = [7, 8, 9, 10]       # moves and dashes
    CHARGE_ACTIONS = [1]                    # charge
    
    def __init__(self):
        """初始化动作空间"""
        self.n = len(self.ACTIONS)  # 动作数量
    
    def get_action_name(self, action_id: int) -> Optional[str]:
        """
        获取动作名称
        
        Args:
            action_id: 动作ID
        
        Returns:
            动作名称或None
        """
        return self.ACTIONS.get(action_id)
    
    def get_action_id(self, action_name: str) -> Optional[int]:
        """
        获取动作ID
        
        Args:
            action_name: 动作名称
        
        Returns:
            动作ID或None
        """
        return self.ACTION_TO_ID.get(action_name)
    
    def get_valid_actions(self, 
                         player: Player, 
                         opponent: Player,
                         current_turn: int,
                         frame: int = 1) -> List[int]:
        """
        获取玩家在当前状态下的有效动作
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            current_turn: 当前回合数
            frame: 当前帧（1或2）
        
        Returns:
            有效动作ID列表
        """
        next_turn = current_turn + 1
        
        # 检查硬直状态
        if player.is_frame_locked(next_turn, frame):
            return [11]  # 只能使用爆血
        
        # 检查被控制状态
        if player.controlled:
            return [5, 11]  # 只能防御或爆血
        
        # 默认所有动作都有效
        valid_actions = list(range(self.n))
        
        # 检查 grab/throw 的前置条件
        if not opponent.controlled:
            # 对手未被控制，不能使用 grab/throw
            if 3 in valid_actions:
                valid_actions.remove(3)  # grab
            if 4 in valid_actions:
                valid_actions.remove(4)  # throw
        
        return valid_actions
    
    def get_action_mask(self,
                       player: Player,
                       opponent: Player,
                       current_turn: int,
                       frame: int = 1) -> np.ndarray:
        """
        生成动作掩码（用于PPO等算法）
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            current_turn: 当前回合数
            frame: 当前帧
        
        Returns:
            长度为n的布尔数组，True表示动作有效
        """
        mask = np.zeros(self.n, dtype=bool)
        valid_actions = self.get_valid_actions(player, opponent, current_turn, frame)
        
        for action_id in valid_actions:
            mask[action_id] = True
        
        return mask
    
    def sample(self, 
              player: Player,
              opponent: Player,
              current_turn: int,
              frame: int = 1) -> int:
        """
        从有效动作中随机采样一个动作
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            current_turn: 当前回合数
            frame: 当前帧
        
        Returns:
            动作ID
        """
        valid_actions = self.get_valid_actions(player, opponent, current_turn, frame)
        return np.random.choice(valid_actions)
    
    def sample_turn_actions(self,
                           player: Player,
                           opponent: Player,
                           current_turn: int) -> Tuple[int, int]:
        """
        采样一个完整回合的动作（2帧）
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            current_turn: 当前回合数
        
        Returns:
            (frame1_action, frame2_action)
        """
        frame1_action = self.sample(player, opponent, current_turn, frame=1)
        frame2_action = self.sample(player, opponent, current_turn, frame=2)
        return (frame1_action, frame2_action)
    
    def is_action_valid(self,
                       action_id: int,
                       player: Player,
                       opponent: Player,
                       current_turn: int,
                       frame: int = 1) -> bool:
        """
        检查动作是否有效
        
        Args:
            action_id: 动作ID
            player: 当前玩家
            opponent: 对手玩家
            current_turn: 当前回合数
            frame: 当前帧
        
        Returns:
            True if valid
        """
        valid_actions = self.get_valid_actions(player, opponent, current_turn, frame)
        return action_id in valid_actions
    
    def get_action_category(self, action_id: int) -> str:
        """
        获取动作类别
        
        Args:
            action_id: 动作ID
        
        Returns:
            'attack', 'defense', 'movement', 'charge', 'unknown'
        """
        if action_id in self.ATTACK_ACTIONS:
            return 'attack'
        elif action_id in self.DEFENSE_ACTIONS:
            return 'defense'
        elif action_id in self.MOVEMENT_ACTIONS:
            return 'movement'
        elif action_id in self.CHARGE_ACTIONS:
            return 'charge'
        return 'unknown'
    
    def get_all_action_pairs(self) -> List[Tuple[int, int]]:
        """
        获取所有可能的动作对（用于枚举搜索）
        
        Returns:
            所有(action1, action2)组合列表
        """
        pairs = []
        for a1 in range(self.n):
            for a2 in range(self.n):
                pairs.append((a1, a2))
        return pairs
    
    def describe_action(self, action_id: int) -> str:
        """
        获取动作的描述性文本
        
        Args:
            action_id: 动作ID
        
        Returns:
            动作描述
        """
        descriptions = {
            0: "攻击 (Attack): 基础伤害1，距离1格",
            1: "蓄力 (Charge): 提升下次攻击伤害和范围",
            2: "控制 (Control): 距离1格，控制对手",
            3: "抱摔 (Grab): 对被控制对手造成4伤害",
            4: "投掷 (Throw): 对被控制对手造成2伤害+击退3格",
            5: "防御 (Defend): 本帧受伤-1",
            6: "反击 (Counter): 防御+受攻击时反击2伤害",
            7: "左移 (Move Left): 向左移动1格",
            8: "右移 (Move Right): 向右移动1格",
            9: "左冲 (Dash Left): 向左冲刺2格",
            10: "右冲 (Dash Right): 向右冲刺2格",
            11: "爆血 (Burst): 自损伤害，对敌人造成距离相关伤害"
        }
        return descriptions.get(action_id, "未知动作")


# ===== 工具函数 =====

def convert_actions_to_names(action_ids: List[int]) -> List[str]:
    """
    将动作ID列表转换为名称列表
    
    Args:
        action_ids: 动作ID列表
    
    Returns:
        动作名称列表
    """
    space = ActionSpace()
    return [space.get_action_name(aid) for aid in action_ids]


def convert_names_to_actions(action_names: List[str]) -> List[int]:
    """
    将动作名称列表转换为ID列表
    
    Args:
        action_names: 动作名称列表
    
    Returns:
        动作ID列表
    """
    space = ActionSpace()
    return [space.get_action_id(name) for name in action_names]


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 ActionSpace...")
    
    from player import Player
    
    # 创建测试玩家
    player = Player("P1", 3)
    opponent = Player("P2", 5)
    
    # 创建动作空间
    action_space = ActionSpace()
    
    print(f"动作空间大小: {action_space.n}")
    print(f"\n所有动作:")
    for aid in range(action_space.n):
        print(f"  {aid}: {action_space.describe_action(aid)}")
    
    # 测试有效动作获取
    print(f"\n测试1: 正常状态下的有效动作")
    valid = action_space.get_valid_actions(player, opponent, current_turn=0)
    print(f"有效动作ID: {valid}")
    print(f"有效动作名称: {convert_actions_to_names(valid)}")
    
    # 测试硬直状态
    print(f"\n测试2: 硬直状态")
    player.lock_frame(1, 1)
    valid_stunned = action_space.get_valid_actions(player, opponent, current_turn=0)
    print(f"硬直时有效动作: {valid_stunned}")
    print(f"硬直时有效动作名称: {convert_actions_to_names(valid_stunned)}")
    player.locked_frames = []  # 清除硬直
    
    # 测试被控制状态
    print(f"\n测试3: 被控制状态")
    player.controlled = True
    valid_controlled = action_space.get_valid_actions(player, opponent, current_turn=0)
    print(f"被控制时有效动作: {valid_controlled}")
    print(f"被控制时有效动作名称: {convert_actions_to_names(valid_controlled)}")
    player.controlled = False  # 清除控制
    
    # 测试grab/throw限制
    print(f"\n测试4: grab/throw前置条件")
    print("对手未被控制:")
    valid_no_control = action_space.get_valid_actions(player, opponent, current_turn=0)
    print(f"  可用grab(3)? {3 in valid_no_control}")
    print(f"  可用throw(4)? {4 in valid_no_control}")
    
    print("对手被控制:")
    opponent.controlled = True
    valid_with_control = action_space.get_valid_actions(player, opponent, current_turn=0)
    print(f"  可用grab(3)? {3 in valid_with_control}")
    print(f"  可用throw(4)? {4 in valid_with_control}")
    
    # 测试动作掩码
    print(f"\n测试5: 动作掩码")
    mask = action_space.get_action_mask(player, opponent, current_turn=0)
    print(f"掩码: {mask}")
    print(f"True的位置: {np.where(mask)[0]}")
    
    # 测试随机采样
    print(f"\n测试6: 随机采样")
    for i in range(5):
        action = action_space.sample(player, opponent, current_turn=0)
        print(f"  采样{i+1}: {action} ({action_space.get_action_name(action)})")
    
    # 测试完整回合采样
    print(f"\n测试7: 完整回合采样")
    for i in range(3):
        actions = action_space.sample_turn_actions(player, opponent, current_turn=0)
        names = convert_actions_to_names(actions)
        print(f"  回合{i+1}: {actions} ({names})")
    
    # 测试动作类别
    print(f"\n测试8: 动作类别")
    test_actions = [0, 1, 5, 7, 11]
    for aid in test_actions:
        category = action_space.get_action_category(aid)
        name = action_space.get_action_name(aid)
        print(f"  {name}({aid}): {category}")
    
    print("\n✅ ActionSpace 测试完成！")