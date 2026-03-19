"""
reward_shaper_v2.py
改进的奖励塑形 - 修复"躺平"问题 / Improved Reward Shaping - Fix "Passive Play" Issue

主要改进：
1. 降低survival奖励，避免过度防御
2. 增加进攻奖励
3. 惩罚无效动作（连续防御）
4. 奖励主动性
"""

import sys
import os
from typing import Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)

from player import Player


class ImprovedRewardShaper:
    """
    改进的奖励塑形器
    
    解决"躺平"问题
    """
    
    def __init__(self):
        """初始化改进的奖励权重"""
        self.weights = {
            # 核心奖励
            'damage_dealt': 5.0,        # ⬆️ 大幅提高进攻奖励（从2.0）
            'damage_taken': -2.0,       # ⬇️ 适度降低惩罚（从-1.5）
            'win': 100.0,
            'loss': -100.0,
            
            # 战术奖励
            'control_success': 10.0,    # ⬆️ 提高控制奖励（从5.0）
            'combo': 3.0,
            'charge_gain': 2.0,
            'dash_buff_gain': 2.0,
            
            # 行为塑形
            'survival': 0.1,            # ⬇️ 大幅降低（从0.5），避免躺平
            'hp_advantage': 0.05,       # ⬇️ 降低（从0.1）
            'aggression_bonus': 2.0,    # ⭐ 新增：进攻性奖励
            'passivity_penalty': -1.0,  # ⭐ 新增：惩罚过度防御
            'distance_closing': 1.0,    # ⭐ 新增：鼓励接近对手
        }
        
        # 追踪防御次数
        self.consecutive_defenses = {1: 0, 2: 0}
    
    def calculate_reward(self,
                        player: Player,
                        opponent: Player,
                        player_id: int,
                        player_hp_before: int,
                        opponent_hp_before: int,
                        player_alive: bool,
                        opponent_alive: bool,
                        is_done: bool,
                        distance_before: int,
                        distance_after: int,
                        player_actions: tuple = None) -> float:
        """
        计算改进的奖励
        
        新增参数：
            player_id: 玩家ID（用于追踪防御次数）
            distance_before: 回合前距离
            distance_after: 回合后距离
            player_actions: 玩家选择的动作
        """
        reward = 0.0
        
        # 1. 基础伤害奖励
        damage_dealt = opponent_hp_before - opponent.hp
        damage_taken = player_hp_before - player.hp
        
        reward += damage_dealt * self.weights['damage_dealt']
        reward += damage_taken * self.weights['damage_taken']
        
        # 2. 进攻性奖励（造成伤害额外奖励）
        if damage_dealt > 0:
            reward += self.weights['aggression_bonus']
            # 重置防御计数
            self.consecutive_defenses[player_id] = 0
        
        # 3. 控制奖励
        if opponent.controlled and opponent.controller == player.name:
            reward += self.weights['control_success']
        
        # 4. 连击奖励
        if opponent.combo_count > 0:
            reward += opponent.combo_count * self.weights['combo']
        
        # 5. 距离变化奖励（鼓励接近）
        if distance_after < distance_before:
            reward += self.weights['distance_closing']
        
        # 6. 检测过度防御
        if player_actions:
            # 统计防御动作
            defense_count = sum(1 for a in player_actions if a in [5, 6])  # defend, counter
            
            if defense_count == 2:  # 两帧都是防御
                self.consecutive_defenses[player_id] += 1
                
                # 连续防御惩罚（递增）
                if self.consecutive_defenses[player_id] >= 3:
                    penalty = self.consecutive_defenses[player_id] * self.weights['passivity_penalty']
                    reward += penalty
            else:
                self.consecutive_defenses[player_id] = 0
        
        # 7. 血量优势（微小）
        hp_diff = player.hp - opponent.hp
        reward += hp_diff * self.weights['hp_advantage']
        
        # 8. Buff奖励
        if player.charge_level > 0:
            reward += player.charge_level * self.weights['charge_gain']
        if player.dash_buff_stacks > 0:
            reward += player.dash_buff_stacks * self.weights['dash_buff_gain']
        
        # 9. 存活奖励（极小，避免躺平）
        if not is_done:
            reward += self.weights['survival']
        
        # 10. 胜负奖励
        if is_done:
            if player_alive and not opponent_alive:
                reward += self.weights['win']
            elif not player_alive and opponent_alive:
                reward += self.weights['loss']
        
        return reward
    
    def reset_tracking(self):
        """重置追踪（新episode开始时）"""
        self.consecutive_defenses = {1: 0, 2: 0}


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 ImprovedRewardShaper...")
    
    from player import Player
    
    # 创建测试玩家
    player = Player("P1", 3)
    opponent = Player("P2", 5)
    
    shaper = ImprovedRewardShaper()
    
    # 测试1: 进攻行为
    print("\n测试1: 进攻行为（造成5伤害）")
    player.hp = 18
    opponent.hp = 15  # 从20降到15
    
    reward = shaper.calculate_reward(
        player, opponent, player_id=1,
        player_hp_before=18, opponent_hp_before=20,
        player_alive=True, opponent_alive=True,
        is_done=False,
        distance_before=3, distance_after=3,
        player_actions=(0, 0)  # attack, attack
    )
    
    print(f"进攻奖励: {reward:.2f}")
    print(f"  - 造成5伤害: {5 * shaper.weights['damage_dealt']:.2f}")
    print(f"  - 进攻性奖励: {shaper.weights['aggression_bonus']:.2f}")
    
    # 测试2: 防御行为
    print("\n测试2: 纯防御行为")
    shaper.reset_tracking()
    
    # 连续3回合防御
    for i in range(3):
        reward = shaper.calculate_reward(
            player, opponent, player_id=1,
            player_hp_before=18, opponent_hp_before=15,
            player_alive=True, opponent_alive=True,
            is_done=False,
            distance_before=3, distance_after=3,
            player_actions=(5, 5)  # defend, defend
        )
        print(f"  回合{i+1} 防御奖励: {reward:.2f} (连续防御{i+1}次)")
    
    # 测试3: 接近对手
    print("\n测试3: 接近对手")
    reward = shaper.calculate_reward(
        player, opponent, player_id=1,
        player_hp_before=18, opponent_hp_before=15,
        player_alive=True, opponent_alive=True,
        is_done=False,
        distance_before=5, distance_after=3,  # 距离缩短
        player_actions=(9, 9)  # dash
    )
    print(f"接近奖励: {reward:.2f}")
    print(f"  - 距离缩短奖励: {shaper.weights['distance_closing']:.2f}")
    
    print("\n✅ ImprovedRewardShaper 测试完成！")