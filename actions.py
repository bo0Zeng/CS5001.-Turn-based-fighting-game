"""
actions.py
招式系统 - 只负责生成状态，不包含游戏规则判定
"""

from state import PositionState, DamageState, DefenseState
from config import *


class Actions:
    """招式系统 - 纯状态生成"""
    
    @staticmethod
    def attack(attacker, defender, distance):
        """攻击 - 生成伤害状态"""
        attack_range = ATTACK_RANGE
        damage = ATTACK_DAMAGE
        
        # 蓄力加成
        if attacker.charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
            damage += CHARGE_1_DAMAGE_BONUS
            print(f"💥 {attacker.name} 蓄力1攻击！")
            attacker.charge_level = 0
        elif attacker.charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
            damage += CHARGE_2_DAMAGE_BONUS
            print(f"💥💥 {attacker.name} 蓄力2攻击！")
            attacker.charge_level = 0
            attacker.used_charge_2_this_frame = True
        
        # 冲刺加成
        if attacker.dash_buff_stacks > 0:
            damage += attacker.dash_buff_stacks
            print(f"🏃 冲锋加成！伤害+{attacker.dash_buff_stacks}")
        
        # 记录攻击尝试
        attacker.tried_attack_this_frame = True
        attacker.attack_range_this_frame = attack_range
        
        # 距离检查
        if distance > attack_range:
            print(f"❌ {attacker.name} 攻击距离不够（需{attack_range}格，实际{distance}格）")
            return False
        
        print(f"⚔️ {attacker.name} 攻击 {defender.name}！")
        
        # 生成伤害状态
        defender.add_damage_state(damage, source=attacker.name)
        attacker.dealt_damage_this_frame = True
        
        return True
    
    @staticmethod
    def charge(player):
        """蓄力"""
        print(f"✨ {player.name} 蓄力...")
        return True
    
    @staticmethod
    def control(attacker, defender):
        """
        控制 - 将被控制者拉到控制者位置（距离变为0，两人重叠）
        【设计】直接改变位置，避免冲突检测失败
        """
        # 直接改变位置，使两人重叠在控制者位置
        print(f"   {defender.name} 被拉到位置{attacker.position}（距离→0）")
        defender.position = attacker.position
        
        # 设置控制
        defender.controlled = True
        defender.controller = attacker.name
        
        # 蓄力惩罚
        if defender.charge_level > 0:
            print(f"💔 {defender.name} 失去蓄力（被控制）")
            defender.charge_level = 0
            defender.add_damage_state(CHARGE_CONTROLLED_DAMAGE, source="control_penalty")
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """抱摔"""
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法抱摔")
            return False
        
        print(f"🤼 {attacker.name} 抱摔 {defender.name}！")
        
        defender.add_damage_state(GRAB_DAMAGE, source=attacker.name)
        attacker.dealt_damage_this_frame = True
        
        # 【设计】抱摔时执行者在本帧受伤+2（参考冲刺buff逻辑）
        # 这个buff仅在本帧有效，reset_frame()时会清零
        attacker.grab_damage_buff = GRAB_DAMAGE_BUFF
        print(f"   {attacker.name} 获得抱摔伤害buff（受伤+{GRAB_DAMAGE_BUFF}）")
        
        # 标记：抱摔后被摔者会后退（在伤害结算后处理）
        defender.should_knockback = True
        
        defender.controlled = False
        defender.controller = None
        print(f"🔓 解除控制")
        
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """投掷"""
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法投掷")
            return False
        
        print(f"🌪️ {attacker.name} 投掷 {defender.name}！")
        
        defender.add_damage_state(THROW_DAMAGE, source=attacker.name)
        attacker.dealt_damage_this_frame = True
        
        # 击退3格
        throw_delta = -1 if defender.is_left else 1
        for _ in range(THROW_DISTANCE):
            defender.add_position_state(throw_delta)
        
        defender.controlled = False
        defender.controller = None
        print(f"🔓 解除控制")
        
        return True
    
    @staticmethod
    def defend(player):
        """防御"""
        print(f"🛡️ {player.name} 防御姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        player.defending = True
        return True
    
    @staticmethod
    def counter(player):
        """防御反击"""
        print(f"⚔️🛡️ {player.name} 防御反击姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        player.defending = True
        player.countering = True
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """
        爆血 - 生成自损和伤害状态
        自损：3+距离
        敌伤：6-距离（距离=0时就是6伤）
        """
        print(f"💥 {attacker.name} 爆血！")
        
        # 解除控制
        was_controlled = attacker.controlled
        attacker.controlled = False
        attacker.controller = None
        
        # 自损：3+距离
        self_damage = BURST_SELF_DAMAGE + distance
        attacker.add_damage_state(self_damage, source="burst_self")
        print(f"   {attacker.name}自损{self_damage}(3+{distance}距离)")
        
        # 敌伤：6-距离（距离=0时是6伤）
        enemy_damage = max(0, BURST_BASE_DAMAGE - distance)
        if enemy_damage > 0:
            defender.add_damage_state(enemy_damage, source=attacker.name)
            attacker.dealt_damage_this_frame = True
            print(f"   {defender.name}将受{enemy_damage}伤(6-{distance}距离)")
        else:
            print(f"   距离过远，无法伤敌")
        
        if was_controlled:
            print(f"🔓 {attacker.name} 解除被控制")
        
        if defender.controlled:
            defender.controlled = False
            defender.controller = None
            print(f"🔓 {defender.name} 解除被控制")
        
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