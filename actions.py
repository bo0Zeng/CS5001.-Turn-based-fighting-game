"""
actions.py
招式系统 - 纯状态生成（完全状态化重构版） / Action System - Pure State Generation (Fully State-based Refactored Version)

修改： / Changes:
1. 删除抱摔的位移 / Removed grab movement
2. 删除抱摔的受伤buff / Removed grab damage buff
3. 抱摔后二者仍然重叠，由阶段7处理位移 / After grab, both remain overlapping, displacement handled by phase 7
"""

from state import PositionState, DamageState, DefenseState, ControlState, BuffState, MarkerState
from config import *


class Actions:
    """招式系统 - 纯状态生成，不修改Player属性 / Action System - Pure State Generation, does not modify Player attributes"""
    
    @staticmethod
    def attack(attacker, defender):
        """攻击 - 无条件生成状态，距离判断交给combat_manager / Attack - Unconditionally generates states, distance judgment handled by combat_manager"""
        attack_range = ATTACK_RANGE
        damage = ATTACK_DAMAGE
        
        # 蓄力加成
        if attacker.charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
            damage += CHARGE_1_DAMAGE_BONUS
            print(f"{attacker.name} 蓄力1攻击！")
            attacker.add_buff_state('charge', 'consume')
        elif attacker.charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
            damage += CHARGE_2_DAMAGE_BONUS
            print(f"{attacker.name} 蓄力2攻击！")
            attacker.add_buff_state('charge', 'consume')
            attacker.add_marker_state('used_charge_2')
        
        # 冲刺加成
        if attacker.dash_buff_stacks > 0:
            damage += attacker.dash_buff_stacks
            print(f"冲锋加成！伤害+{attacker.dash_buff_stacks}")
        
        # 记录攻击尝试和范围
        attacker.add_marker_state('tried_attack')
        attacker.attack_range_this_frame = attack_range
        
        # 无条件生成伤害状态（距离检查后可能被移除）
        defender.add_damage_state(damage, source=attacker.name)
        
        print(f"{attacker.name} 尝试攻击 {defender.name}（范围{attack_range}格）")
        
        return True
    
    @staticmethod
    def charge(player, frame, current_turn):
        """蓄力 - 生成pending状态 / Charge - Generates pending state"""
        # 判断应该生成蓄力1还是蓄力2
        level = 1
        if player.charge_level == 1:
            if player.can_stack_charge(current_turn, frame, 
                                       player.last_charge_turn, 
                                       player.last_charge_frame):
                level = 2
        
        # 生成pending状态（尚未确定是否成功）
        player.add_buff_state('charge', 'pending', level)
        print(f"{player.name} 尝试蓄力{level}...")
        
        # 记录蓄力时机（用于下次判断连续）
        player.last_charge_turn = current_turn
        player.last_charge_frame = frame
        
        return True
    
    @staticmethod
    def control(attacker, defender):
        """控制 - 无条件生成状态，距离和冲突检查交给combat_manager / Control - Unconditionally generates states, distance and conflict checks handled by combat_manager"""
        print(f"{attacker.name} 尝试控制 {defender.name}！")
        
        # 记录控制范围（用于距离检查）
        attacker.control_range_this_frame = CONTROL_RANGE
        
        # 无条件生成控制状态（距离检查后可能被移除）
        # pull的target存储控制者名字，而不是位置（在结算时使用控制者的当前位置）
        defender.add_control_state('pull', target=attacker.name)
        defender.add_control_state('controlled', target=attacker.name)
        attacker.add_marker_state('tried_control')
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """抱摔 - 纯状态生成（已删除位移和受伤buff） / Grab - Pure state generation (movement and damage buff removed)"""
        print(f"{attacker.name} 抱摔 {defender.name}！")
        
        # 只造成伤害，不推开，不增加受伤buff
        defender.add_damage_state(GRAB_DAMAGE, source=attacker.name)
        attacker.add_marker_state('dealt_damage')
        
        # 抱摔后解除控制（距离调整由阶段7处理）
        defender.add_control_state('release')
        
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """投掷 - 纯状态生成 / Throw - Pure state generation"""
        print(f"{attacker.name} 投掷 {defender.name}！")
        
        defender.add_damage_state(THROW_DAMAGE, source=attacker.name)
        attacker.add_marker_state('dealt_damage')
        
        throw_delta = -1 if defender.is_left else 1
        for _ in range(THROW_DISTANCE):
            defender.add_position_state(throw_delta, source=attacker.name)
        
        # 投掷后解除控制
        defender.add_control_state('release')
        
        return True
    
    @staticmethod
    def defend(player):
        """防御 - 生成防御状态 / Defend - Generates defense state"""
        print(f"{player.name} 防御姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        return True
    
    @staticmethod
    def counter(player):
        """防御反击 - 生成防御+反击准备状态 / Counter - Generates defense + counter preparation state"""
        print(f"{player.name} 防御反击姿态")
        player.add_defense_state(DEFEND_REDUCTION)
        player.add_marker_state('counter_prepared')
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """爆血 - 完全状态化版本 / Burst - Fully state-based version"""
        print(f"{attacker.name} 爆血！")
        
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
        """移动 - 生成位置状态 / Move - Generates position state"""
        delta = -1 if direction == 'left' else 1
        player.add_position_state(delta)
        return True
    
    @staticmethod
    def dash(player, direction):
        """冲刺 - 生成2个位置状态 / Dash - Generates 2 position states"""
        delta = -1 if direction == 'left' else 1
        player.add_position_state(delta)
        player.add_position_state(delta)
        print(f"{player.name} 尝试冲刺2格...")
        return True