"""
reward_shaper.py
奖励塑形 - 设计和计算奖励函数 / Reward Shaping - Design and Calculate Reward Functions

提供多种奖励函数：
- 稀疏奖励：只在游戏结束时给奖励
- 密集奖励：每回合给予详细的奖励反馈
- 课程学习奖励：根据训练阶段动态调整奖励
"""

import sys
import os
from typing import Tuple, Dict

# 添加父目录到路径，以便导入游戏代码
current_dir = os.path.dirname(os.path.abspath(__file__))  # ai_training/environment/
ai_training_dir = os.path.dirname(current_dir)             # ai_training/
project_root = os.path.dirname(ai_training_dir)            # 项目根目录
sys.path.insert(0, project_root)

from player import Player


class RewardShaper:
    """
    奖励塑形器
    
    负责计算和设计奖励函数
    """
    
    def __init__(self, reward_type: str = 'dense', reward_scale: float = 1.0):
        """
        初始化奖励塑形器
        
        Args:
            reward_type: 'sparse', 'dense', 'curriculum'
            reward_scale: 奖励缩放系数
        """
        self.reward_type = reward_type
        self.reward_scale = reward_scale
        
        # 奖励权重（可调）
        self.weights = {
            'damage_dealt': 2.0,        # 造成伤害的奖励
            'damage_taken': -1.5,       # 受到伤害的惩罚
            'control_success': 5.0,     # 控制成功奖励
            'combo': 2.0,               # 连击奖励（每次累计）
            'hp_advantage': 0.1,        # 血量优势奖励
            'survival': 0.5,            # 存活奖励
            'win': 100.0,               # 胜利奖励
            'loss': -100.0,             # 失败惩罚
            'charge_gain': 3.0,         # 获得蓄力奖励
            'charge_interrupt': -5.0,   # 蓄力被打断惩罚
            'dash_buff_gain': 2.0,      # 获得冲刺buff奖励
            'dodge_success': 5.0,       # 闪避成功奖励
            'stun_opponent': 3.0,       # 硬直对手奖励
            'being_stunned': -2.0,      # 被硬直惩罚
        }
    
    def calculate_reward(self,
                        player: Player,
                        opponent: Player,
                        player_hp_before: int,
                        opponent_hp_before: int,
                        player_alive: bool,
                        opponent_alive: bool,
                        is_done: bool,
                        info: Dict = None) -> float:
        """
        计算玩家的奖励
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            player_hp_before: 玩家回合前HP
            opponent_hp_before: 对手回合前HP
            player_alive: 玩家是否存活
            opponent_alive: 对手是否存活
            is_done: 游戏是否结束
            info: 额外信息字典
        
        Returns:
            奖励值
        """
        if self.reward_type == 'sparse':
            return self._sparse_reward(player_alive, opponent_alive, is_done)
        elif self.reward_type == 'dense':
            return self._dense_reward(
                player, opponent,
                player_hp_before, opponent_hp_before,
                player_alive, opponent_alive,
                is_done, info
            )
        elif self.reward_type == 'curriculum':
            return self._curriculum_reward(
                player, opponent,
                player_hp_before, opponent_hp_before,
                player_alive, opponent_alive,
                is_done, info
            )
        else:
            return 0.0
    
    def _sparse_reward(self,
                      player_alive: bool,
                      opponent_alive: bool,
                      is_done: bool) -> float:
        """
        稀疏奖励：只在游戏结束时给奖励
        
        Args:
            player_alive: 玩家是否存活
            opponent_alive: 对手是否存活
            is_done: 游戏是否结束
        
        Returns:
            奖励值
        """
        if not is_done:
            return 0.0
        
        # 胜负奖励
        if player_alive and not opponent_alive:
            return self.weights['win'] * self.reward_scale
        elif not player_alive and opponent_alive:
            return self.weights['loss'] * self.reward_scale
        else:
            # 平局或双败
            return 0.0
    
    def _dense_reward(self,
                     player: Player,
                     opponent: Player,
                     player_hp_before: int,
                     opponent_hp_before: int,
                     player_alive: bool,
                     opponent_alive: bool,
                     is_done: bool,
                     info: Dict = None) -> float:
        """
        密集奖励：每回合给予详细的奖励反馈
        
        Args:
            player: 当前玩家
            opponent: 对手玩家
            player_hp_before: 玩家回合前HP
            opponent_hp_before: 对手回合前HP
            player_alive: 玩家是否存活
            opponent_alive: 对手是否存活
            is_done: 游戏是否结束
            info: 额外信息字典
        
        Returns:
            奖励值
        """
        reward = 0.0
        
        # 1. 伤害奖励/惩罚
        damage_dealt = opponent_hp_before - opponent.hp
        damage_taken = player_hp_before - player.hp
        
        reward += damage_dealt * self.weights['damage_dealt']
        reward += damage_taken * self.weights['damage_taken']
        
        # 2. 控制奖励
        if opponent.controlled and opponent.controller == player.name:
            reward += self.weights['control_success']
        
        # 3. 连击奖励
        if opponent.combo_count > 0:
            reward += opponent.combo_count * self.weights['combo']
        
        # 4. 血量优势奖励
        hp_diff = player.hp - opponent.hp
        reward += hp_diff * self.weights['hp_advantage']
        
        # 5. 蓄力奖励
        if player.charge_level > 0:
            reward += player.charge_level * self.weights['charge_gain']
        
        # 6. 冲刺buff奖励
        if player.dash_buff_stacks > 0:
            reward += player.dash_buff_stacks * self.weights['dash_buff_gain']
        
        # 7. 硬直相关
        # 检查对手是否被硬直（简化检查）
        if info and 'opponent_stunned' in info and info['opponent_stunned']:
            reward += self.weights['stun_opponent']
        
        # 检查自己是否被硬直
        if info and 'player_stunned' in info and info['player_stunned']:
            reward += self.weights['being_stunned']
        
        # 8. 存活奖励（鼓励长期规划）
        if not is_done:
            reward += self.weights['survival']
        
        # 9. 胜负终结奖励
        if is_done:
            if player_alive and not opponent_alive:
                reward += self.weights['win']
            elif not player_alive and opponent_alive:
                reward += self.weights['loss']
            # 平局不额外奖惩
        
        return reward * self.reward_scale
    
    def _curriculum_reward(self,
                          player: Player,
                          opponent: Player,
                          player_hp_before: int,
                          opponent_hp_before: int,
                          player_alive: bool,
                          opponent_alive: bool,
                          is_done: bool,
                          info: Dict = None) -> float:
        """
        课程学习奖励：根据训练阶段动态调整奖励
        
        训练早期：更关注存活和基础操作
        训练后期：更关注胜负和高级策略
        
        Args:
            (same as _dense_reward)
        
        Returns:
            奖励值
        """
        # TODO: 实现课程学习逻辑
        # 目前先使用密集奖励
        return self._dense_reward(
            player, opponent,
            player_hp_before, opponent_hp_before,
            player_alive, opponent_alive,
            is_done, info
        )
    
    def set_weight(self, key: str, value: float):
        """
        设置奖励权重
        
        Args:
            key: 权重名称
            value: 权重值
        """
        if key in self.weights:
            self.weights[key] = value
    
    def get_weight(self, key: str) -> float:
        """
        获取奖励权重
        
        Args:
            key: 权重名称
        
        Returns:
            权重值
        """
        return self.weights.get(key, 0.0)
    
    def scale_rewards(self, scale: float):
        """
        缩放所有奖励权重
        
        Args:
            scale: 缩放系数
        """
        self.reward_scale = scale


# ===== 预定义奖励配置 =====

REWARD_CONFIGS = {
    'aggressive': {
        'damage_dealt': 3.0,
        'damage_taken': -1.0,
        'control_success': 8.0,
        'win': 150.0,
    },
    'defensive': {
        'damage_dealt': 1.5,
        'damage_taken': -2.5,
        'survival': 1.0,
        'hp_advantage': 0.3,
    },
    'balanced': {
        'damage_dealt': 2.0,
        'damage_taken': -1.5,
        'control_success': 5.0,
        'survival': 0.5,
    },
}


def create_reward_shaper(config_name: str = 'balanced', 
                        reward_type: str = 'dense') -> RewardShaper:
    """
    创建预配置的奖励塑形器
    
    Args:
        config_name: 配置名称 ('aggressive', 'defensive', 'balanced')
        reward_type: 奖励类型
    
    Returns:
        RewardShaper实例
    """
    shaper = RewardShaper(reward_type=reward_type)
    
    if config_name in REWARD_CONFIGS:
        for key, value in REWARD_CONFIGS[config_name].items():
            shaper.set_weight(key, value)
    
    return shaper


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 RewardShaper...")
    
    from player import Player
    
    # 创建测试玩家
    player = Player("P1", 3)
    player.hp = 15
    opponent = Player("P2", 5)
    opponent.hp = 18
    
    # 测试稀疏奖励
    print("\n测试1: 稀疏奖励")
    sparse_shaper = RewardShaper(reward_type='sparse')
    
    # 游戏进行中
    reward_ongoing = sparse_shaper.calculate_reward(
        player, opponent,
        player_hp_before=15, opponent_hp_before=18,
        player_alive=True, opponent_alive=True,
        is_done=False
    )
    print(f"游戏进行中奖励: {reward_ongoing}")
    
    # 玩家胜利
    opponent.hp = 0
    reward_win = sparse_shaper.calculate_reward(
        player, opponent,
        player_hp_before=15, opponent_hp_before=18,
        player_alive=True, opponent_alive=False,
        is_done=True
    )
    print(f"玩家胜利奖励: {reward_win}")
    
    # 测试密集奖励
    print("\n测试2: 密集奖励")
    dense_shaper = RewardShaper(reward_type='dense')
    
    # 重置状态
    player.hp = 15
    opponent.hp = 10  # 造成了8点伤害
    opponent.combo_count = 2  # 连击2次
    
    reward_dense = dense_shaper.calculate_reward(
        player, opponent,
        player_hp_before=15, opponent_hp_before=18,
        player_alive=True, opponent_alive=True,
        is_done=False
    )
    print(f"密集奖励: {reward_dense:.2f}")
    print(f"  - 造成8伤害: {8 * dense_shaper.weights['damage_dealt']:.2f}")
    print(f"  - 连击2次: {2 * dense_shaper.weights['combo']:.2f}")
    print(f"  - 血量优势5: {5 * dense_shaper.weights['hp_advantage']:.2f}")
    print(f"  - 存活: {dense_shaper.weights['survival']:.2f}")
    
    # 测试预配置
    print("\n测试3: 预定义配置")
    configs = ['aggressive', 'defensive', 'balanced']
    
    for config_name in configs:
        shaper = create_reward_shaper(config_name)
        reward = shaper.calculate_reward(
            player, opponent,
            player_hp_before=15, opponent_hp_before=18,
            player_alive=True, opponent_alive=True,
            is_done=False
        )
        print(f"{config_name} 配置奖励: {reward:.2f}")
    
    # 测试权重调整
    print("\n测试4: 权重调整")
    custom_shaper = RewardShaper(reward_type='dense')
    print(f"默认 damage_dealt 权重: {custom_shaper.get_weight('damage_dealt')}")
    
    custom_shaper.set_weight('damage_dealt', 5.0)
    print(f"修改后 damage_dealt 权重: {custom_shaper.get_weight('damage_dealt')}")
    
    # 测试奖励缩放
    print("\n测试5: 奖励缩放")
    shaper = RewardShaper(reward_type='dense', reward_scale=1.0)
    reward_normal = shaper.calculate_reward(
        player, opponent,
        player_hp_before=15, opponent_hp_before=18,
        player_alive=True, opponent_alive=True,
        is_done=False
    )
    print(f"正常缩放(1.0)奖励: {reward_normal:.2f}")
    
    shaper.scale_rewards(0.5)
    reward_scaled = shaper.calculate_reward(
        player, opponent,
        player_hp_before=15, opponent_hp_before=18,
        player_alive=True, opponent_alive=True,
        is_done=False
    )
    print(f"缩放后(0.5)奖励: {reward_scaled:.2f}")
    
    print("\n✅ RewardShaper 测试完成！")