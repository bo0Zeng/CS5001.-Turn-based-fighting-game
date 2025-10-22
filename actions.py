"""
actions.py
招式系统 - 纯状态生成（完全解耦终极版）
"""

from state import PositionState, DamageState, DefenseState, ControlState, BuffState, MarkerState
from config import *


class Actions:
    """招式系统 - 纯状态生成，不修改Player属性"""
    
    @staticmethod
    def attack(attacker, defender, distance):
        """攻击 - 完全状态化版本
        
        Args:
            attacker: 攻击者
            defender: 防守者
            distance: 预计算的距离
        """
        attack_range = ATTACK_RANGE
        damage = ATTACK_DAMAGE
        
        # 蓄力加成
        if attacker.charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
            damage += CHARGE_1_DAMAGE_BONUS
            print(f"💥 {attacker.name} 蓄力1攻击！")
            attacker.add_buff_state('charge', 'consume')
        elif attacker.charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
            damage += CHARGE_2_DAMAGE_BONUS
            print(f"💥💥 {attacker.name} 蓄力2攻击！")
            attacker.add_buff_state('charge', 'consume')
            attacker.add_marker_state('used_charge_2')
        
        # 冲刺加成
        if attacker.dash_buff_stacks > 0:
            damage += attacker.dash_buff_stacks
            print(f"🏃 冲锋加成！伤害+{attacker.dash_buff_stacks}")
        
        # 记录攻击尝试
        attacker.add_marker_state('tried_attack')
        attacker.attack_range_this_frame = attack_range
        
        # 距离检查
        if distance > attack_range:
            print(f"❌ {attacker.name} 攻击距离不够（需{attack_range}格，实际{distance}格）")
            return False
        
        print(f"⚔️ {attacker.name} 攻击 {defender.name}！")
        
        # 生成伤害状态
        defender.add_damage_state(damage, source=attacker.name)
        attacker.add_marker_state('dealt_damage')
        
        return True
    
    @staticmethod
    def charge(player):
        """蓄力
        
        注意：蓄力的堆叠逻辑在combat_manager中处理
        """
        print(f"✨ {player.name} 蓄力...")
        return True
    
    @staticmethod
    def control(attacker, defender):
        """控制 - 完全状态化版本
        
        生成：
        - 拉近状态（pull）
        - 被控制状态（controlled）
        - 蓄力惩罚（如果有）
        """
        print(f"🔒 {attacker.name} 控制 {defender.name}！")
        
        # 生成拉近状态
        defender.add_control_state('pull', target=attacker.position)
        
        # 生成被控制状态
        defender.add_control_state('controlled', target=attacker.name)
        
        # 蓄力惩罚
        if defender.charge_level > 0:
            print(f"💔 {defender.name} 失去蓄力（被控制）")
            defender.add_buff_state('charge', 'lose')
            defender.add_damage_state(CHARGE_CONTROLLED_DAMAGE, source="control_penalty")
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """抱摔 - 纯状态生成
        
        前置条件：defender必须被控制
        注意：前置条件已在combat_manager._preprocess()中检查
              这里直接生成状态，无需验证
        """
        print(f"🤼 {attacker.name} 抱摔 {defender.name}！")
        
        defender.add_damage_state(GRAB_DAMAGE, source=attacker.name)
        attacker.add_marker_state('dealt_damage')
        attacker.add_buff_state('grab_damage', 'gain', GRAB_DAMAGE_BUFF)
        
        push_delta = -1 if defender.is_left else 1
        defender.add_position_state(push_delta)
        
        defender.add_control_state('release')
        
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """投掷 - 纯状态生成
        
        前置条件：defender必须被控制
        注意：前置条件已在combat_manager._preprocess()中检查
              这里直接生成状态，无需验证
        """
        print(f"🌪️ {attacker.name} 投掷 {defender.name}！")
        
        defender.add_damage_state(THROW_DAMAGE, source=attacker.name)
        attacker.add_marker_state('dealt_damage')
        
        throw_delta = -1 if defender.is_left else 1
        for _ in range(THROW_DISTANCE):
            defender.add_position_state(throw_delta)
        
        defender.add_control_state('release')
        
        return True
    
    @staticmethod
    def defend(player):
        """防御 - 生成防御状态"""
        print(f"🛡️ {player.name} 防御姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        return True
    
    @staticmethod
    def counter(player):
        """防御反击 - 生成防御状态
        
        注意：反击判定在combat_manager中处理
        """
        print(f"⚔️🛡️ {player.name} 防御反击姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """爆血 - 完全状态化版本
        
        Args:
            distance: 预计算的距离（包含所有位移后）
        
        伤害公式：
        - 自损 = 3 + 距离
        - 敌伤 = 6 - 距离
        """
        print(f"💥 {attacker.name} 爆血！")
        
        # 自损
        self_damage = BURST_SELF_DAMAGE + distance
        attacker.add_damage_state(self_damage, source="burst_self")
        print(f"   {attacker.name}自损{self_damage}(3+{distance}距离)")
        
        # 敌伤
        enemy_damage = max(0, BURST_BASE_DAMAGE - distance)
        if enemy_damage > 0:
            defender.add_damage_state(enemy_damage, source=attacker.name)
            attacker.add_marker_state('dealt_damage')
            print(f"   {defender.name}将受{enemy_damage}伤(6-{distance}距离)")
        else:
            print(f"   距离过远，无法伤敌")
        
        # 解除控制（双方）
        attacker.add_control_state('release')
        defender.add_control_state('release')
        
        return True
    
    @staticmethod
    def move(player, direction):
        """移动 - 生成位置状态"""
        delta = -1 if direction == 'left' else 1
        player.add_position_state(delta)
        return True
    
    @staticmethod
    def dash(player, direction):
        """冲刺 - 生成2个位置状态"""
        delta = -1 if direction == 'left' else 1
        player.add_position_state(delta)
        player.add_position_state(delta)
        print(f"🚀 {player.name} 尝试冲刺2格...")
        return True