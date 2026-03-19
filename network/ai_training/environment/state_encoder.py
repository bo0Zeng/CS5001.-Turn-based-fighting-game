"""
state_encoder.py
状态编码器 - 将游戏状态转换为神经网络输入 / State Encoder - Convert game state to neural network input

提供多种编码方式：
- 基础编码：简单的归一化向量
- 增强编码：包含更多历史和上下文信息
- 图像编码：将状态转为2D图像（用于CNN）
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
from combat_manager import CombatManager
from config import *


class StateEncoder:
    """
    状态编码器
    
    负责将游戏状态转换为适合神经网络的输入格式
    """
    
    def __init__(self, encoding_type: str = 'basic'):
        """
        初始化编码器
        
        Args:
            encoding_type: 'basic', 'enhanced', 'image'
        """
        self.encoding_type = encoding_type
        
        # 动作类型分类
        self.action_categories = {
            'attack': [0, 2, 3, 4, 11],      # attack, control, grab, throw, burst
            'defend': [5, 6],                 # defend, counter
            'move': [7, 8, 9, 10],           # move_left, move_right, dash_left, dash_right
            'charge': [1]                     # charge
        }
    
    def encode(self, 
               player1: Player, 
               player2: Player, 
               combat: CombatManager,
               p1_action_history: List[int],
               p2_action_history: List[int]) -> np.ndarray:
        """
        编码当前游戏状态
        
        Args:
            player1: 玩家1对象
            player2: 玩家2对象
            combat: 战斗管理器
            p1_action_history: P1动作历史
            p2_action_history: P2动作历史
        
        Returns:
            编码后的状态向量
        """
        if self.encoding_type == 'basic':
            return self._encode_basic(player1, player2, combat, p1_action_history, p2_action_history)
        elif self.encoding_type == 'enhanced':
            return self._encode_enhanced(player1, player2, combat, p1_action_history, p2_action_history)
        elif self.encoding_type == 'image':
            return self._encode_image(player1, player2, combat)
        else:
            raise ValueError(f"Unknown encoding type: {self.encoding_type}")
    
    def _encode_basic(self,
                     player1: Player, 
                     player2: Player, 
                     combat: CombatManager,
                     p1_action_history: List[int],
                     p2_action_history: List[int]) -> np.ndarray:
        """
        基础编码（54维）
        
        组成：
        - 玩家1状态: 18维
        - 玩家2状态: 18维
        - 全局状态: 6维
        - 历史信息: 12维
        """
        features = []
        
        # 玩家1状态
        features.extend(self._encode_player_basic(player1, p1_action_history, combat.turn))
        
        # 玩家2状态
        features.extend(self._encode_player_basic(player2, p2_action_history, combat.turn))
        
        # 全局状态
        features.extend(self._encode_global_state(combat))
        
        # 历史信息
        features.extend(self._encode_action_history(p1_action_history, p2_action_history))
        
        return np.array(features, dtype=np.float32)
    
    def _encode_player_basic(self, 
                            player: Player, 
                            action_history: List[int],
                            current_turn: int) -> List[float]:
        """
        编码单个玩家状态（18维）
        
        Returns:
            18维特征列表
        """
        features = []
        
        # 1. HP归一化 (1维)
        features.append(player.hp / player.max_hp)
        
        # 2. 位置归一化 (1维)
        features.append(player.position / MAP_SIZE)
        
        # 3. 蓄力等级 one-hot (3维)
        charge_vec = [0.0, 0.0, 0.0]
        if 0 <= player.charge_level <= 2:
            charge_vec[player.charge_level] = 1.0
        features.extend(charge_vec)
        
        # 4. 冲刺buff one-hot (3维)
        dash_vec = [0.0, 0.0, 0.0]
        stacks = min(player.dash_buff_stacks, 2)
        dash_vec[stacks] = 1.0
        features.extend(dash_vec)
        
        # 5. 连击数 one-hot (4维)
        combo_vec = [0.0, 0.0, 0.0, 0.0]
        combo = min(player.combo_count, 3)
        combo_vec[combo] = 1.0
        features.extend(combo_vec)
        
        # 6. 被控制状态 (1维)
        features.append(1.0 if player.controlled else 0.0)
        
        # 7. 硬直状态 (1维) - 检查下一回合第一帧
        next_turn = current_turn + 1
        is_stunned = player.is_frame_locked(next_turn, 1)
        features.append(1.0 if is_stunned else 0.0)
        
        # 8. 上一帧动作分类 (4维) - one-hot: [攻击, 防御, 移动, 蓄力]
        if len(action_history) > 0 and action_history[-1] >= 0:
            action_type = self._classify_action_type(action_history[-1])
            action_vec = [0.0, 0.0, 0.0, 0.0]
            action_vec[action_type] = 1.0
            features.extend(action_vec)
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])  # 无动作
        
        return features
    
    def _encode_global_state(self, combat: CombatManager) -> List[float]:
        """
        编码全局状态（6维）
        
        Returns:
            6维特征列表
        """
        features = []
        
        # 1. 距离归一化 (1维)
        features.append(combat.get_distance() / MAP_SIZE)
        
        # 2. 回合数归一化 (1维)
        features.append(combat.turn / MAX_TURNS)
        
        # 3. P1方向 (1维)
        features.append(1.0 if combat.p1.is_left else 0.0)
        
        # 4. P2方向 (1维)
        features.append(1.0 if combat.p2.is_left else 0.0)
        
        # 5-6. 帧状态占位 (2维) - 简化处理
        features.extend([0.0, 0.0])
        
        return features
    
    def _encode_action_history(self,
                               p1_history: List[int],
                               p2_history: List[int]) -> List[float]:
        """
        编码动作历史（12维）
        
        每个玩家最近2个动作，每个动作用分类编码（6维）
        
        Returns:
            12维特征列表
        """
        features = []
        
        # P1最近2个动作
        for i in range(2):
            if i < len(p1_history) and p1_history[-(i+1)] >= 0:
                action_id = p1_history[-(i+1)]
                # 6维编码：[action_id归一化, 动作类型one-hot(4维), 有效标记]
                features.append(action_id / 12.0)  # 归一化
                
                # 动作类型 one-hot
                action_type = self._classify_action_type(action_id)
                type_vec = [0.0, 0.0, 0.0, 0.0]
                type_vec[action_type] = 1.0
                features.extend(type_vec)
                
                features.append(1.0)  # 有效标记
            else:
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # 无效动作
        
        # P2最近2个动作（同样处理）
        # 为了简化，这里直接复制P1的逻辑
        # 实际使用时可以考虑只保留最近1个动作
        features.extend([0.0] * 0)  # 简化：不再编码P2历史，减少维度
        
        return features
    
    def _classify_action_type(self, action_id: int) -> int:
        """
        将动作分类为4种类型
        
        Returns:
            0: 攻击类, 1: 防御类, 2: 移动类, 3: 蓄力
        """
        if action_id in self.action_categories['attack']:
            return 0
        elif action_id in self.action_categories['defend']:
            return 1
        elif action_id in self.action_categories['move']:
            return 2
        elif action_id in self.action_categories['charge']:
            return 3
        return 0  # 默认
    
    def _encode_enhanced(self,
                        player1: Player, 
                        player2: Player, 
                        combat: CombatManager,
                        p1_action_history: List[int],
                        p2_action_history: List[int]) -> np.ndarray:
        """
        增强编码（更多维度，包含更详细的信息）
        
        TODO: 实现更复杂的编码方式
        - 添加更多历史帧
        - 添加相对位置关系
        - 添加预测性特征
        """
        # 目前先使用基础编码
        return self._encode_basic(player1, player2, combat, p1_action_history, p2_action_history)
    
    def _encode_image(self,
                     player1: Player, 
                     player2: Player, 
                     combat: CombatManager) -> np.ndarray:
        """
        图像编码（用于CNN）
        
        将游戏状态转换为2D图像表示
        
        图像尺寸: (C, H, W) = (4, 8, 12)
        - 通道1: 玩家位置
        - 通道2: HP状态
        - 通道3: Buff状态
        - 通道4: 控制/硬直状态
        
        TODO: 完整实现
        """
        # 创建空白图像
        image = np.zeros((4, 8, 12), dtype=np.float32)
        
        # 通道1: 玩家位置
        # 在地图位置上标记玩家
        if 1 <= player1.position <= MAP_SIZE:
            col = int((player1.position - 1) * 12 / MAP_SIZE)
            image[0, 4, col] = 1.0  # P1在中心行
        
        if 1 <= player2.position <= MAP_SIZE:
            col = int((player2.position - 1) * 12 / MAP_SIZE)
            image[0, 3, col] = 1.0  # P2在上一行
        
        # 通道2: HP状态（简化表示）
        image[1, :, :] = player1.hp / player1.max_hp * 0.5  # P1 HP
        image[1, :, :] += player2.hp / player2.max_hp * 0.5  # P2 HP
        
        # TODO: 添加更多通道信息
        
        return image
    
    def get_state_shape(self) -> Tuple:
        """
        获取状态形状
        
        Returns:
            状态shape元组
        """
        if self.encoding_type == 'basic':
            return (66,)  # 更新为66维（18+18+6+24）
        elif self.encoding_type == 'enhanced':
            return (66,)  # 目前与basic相同
        elif self.encoding_type == 'image':
            return (4, 8, 12)
        return (66,)


# ===== 工具函数 =====

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    归一化数值到[0, 1]
    
    Args:
        value: 待归一化的值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        归一化后的值
    """
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def one_hot_encode(index: int, size: int) -> List[float]:
    """
    One-hot编码
    
    Args:
        index: 索引
        size: 向量大小
    
    Returns:
        one-hot向量
    """
    vec = [0.0] * size
    if 0 <= index < size:
        vec[index] = 1.0
    return vec


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 StateEncoder...")
    
    # 创建测试环境
    from player import Player
    from combat_manager import CombatManager
    
    player1 = Player("P1", 2)
    player2 = Player("P2", 5)
    combat = CombatManager(player1, player2)
    
    # 创建编码器
    encoder = StateEncoder(encoding_type='basic')
    
    # 测试基础编码
    p1_history = [0, 7]  # attack, move_left
    p2_history = [1, 5]  # charge, defend
    
    state = encoder.encode(player1, player2, combat, p1_history, p2_history)
    
    print(f"编码后状态维度: {state.shape}")
    print(f"状态前10维: {state[:10]}")
    print(f"状态范围: [{state.min():.3f}, {state.max():.3f}]")
    
    # 测试图像编码
    print("\n测试图像编码...")
    img_encoder = StateEncoder(encoding_type='image')
    img_state = img_encoder.encode(player1, player2, combat, p1_history, p2_history)
    print(f"图像状态维度: {img_state.shape}")
    print(f"图像范围: [{img_state.min():.3f}, {img_state.max():.3f}]")
    
    # 测试工具函数
    print("\n测试工具函数...")
    print(f"归一化 5 (范围0-10): {normalize_value(5, 0, 10)}")
    print(f"One-hot编码 2 (size=5): {one_hot_encode(2, 5)}")
    
    print("\n✅ StateEncoder 测试完成！")