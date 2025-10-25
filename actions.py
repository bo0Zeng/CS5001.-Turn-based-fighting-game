"""
actions.py
招式系统 - 纯状态生成（重构版）
Action System - Pure State Generation (Refactored)

重构要点：
1. 所有动作只为自身生成do_xxx状态
2. 不再直接给对方添加状态
3. 蓄力加成通过状态系统处理，不在attack中直接计算
4. 所有验证和对方状态添加在combat_manager的阶段3处理
"""

from state import PositionState, DamageState, DefenseState, ControlState, BuffState, ActionState
from config import *


class Actions:
    """招式系统 - 为自身生成状态 / Action System - Generate states for self"""
    
    @staticmethod
    def attack(attacker):
        """攻击 - 只为自身生成do_attack状态 / Attack - Only generates do_attack state for self"""
        # 基础攻击范围和伤害
        attack_range = ATTACK_RANGE
        base_damage = ATTACK_DAMAGE
        
        # 记录攻击意图，附带基础属性
        attacker.add_action_state('do_attack', attack_range)
        
        print(f"{attacker.name} 尝试攻击（基础范围{attack_range}格，基础伤害{base_damage}）")
        print(f"{attacker.name} attempts attack (base range {attack_range}, base damage {base_damage})")
        
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
        print(f"{player.name} 尝试蓄力{level}... / {player.name} attempts charge {level}...")
        
        # 记录蓄力时机（用于下次判断连续）
        player.last_charge_turn = current_turn
        player.last_charge_frame = frame
        
        return True
    
    @staticmethod
    def control(attacker):
        """控制 - 只为自身生成do_control状态 / Control - Only generates do_control state for self"""
        control_range = CONTROL_RANGE
        
        attacker.add_action_state('do_control', control_range)
        print(f"{attacker.name} 尝试控制（范围{control_range}格）/ {attacker.name} attempts control (range {control_range})")
        
        return True
    
    @staticmethod
    def grab(attacker):
        """抱摔 - 为自身生成do_grab状态 / Grab - Generates do_grab state for self"""
        attacker.add_action_state('do_grab', GRAB_DAMAGE)
        print(f"{attacker.name} 使用抱摔！ / {attacker.name} uses grab!")
        
        return True
    
    @staticmethod
    def throw(attacker):
        """投掷 - 为自身生成do_throw状态 / Throw - Generates do_throw state for self"""
        attacker.add_action_state('do_throw', THROW_DAMAGE)
        print(f"{attacker.name} 使用投掷！ / {attacker.name} uses throw!")
        
        return True
    
    @staticmethod
    def defend(player):
        """防御 - 生成防御状态 / Defend - Generates defense state"""
        print(f"{player.name} 防御姿态 / {player.name} defensive stance")
        player.add_defense_state(DEFEND_REDUCTION)
        return True
    
    @staticmethod
    def counter(player):
        """防御反击 - 生成防御+反击准备状态 / Counter - Generates defense + counter preparation state"""
        print(f"{player.name} 防御反击姿态 / {player.name} counter stance")
        player.add_defense_state(DEFEND_REDUCTION)
        player.add_action_state('do_counter')
        return True
    
    @staticmethod
    def burst(attacker):
        """爆血 - 为自身生成do_burst状态 / Burst - Generates do_burst state for self"""
        print(f"{attacker.name} 爆血！ / {attacker.name} bursts!")
        
        attacker.add_action_state('do_burst')
        
        # 立即解除自己的控制状态
        attacker.add_control_state('release')
        
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
        print(f"{player.name} 尝试冲刺2格... / {player.name} attempts dash 2 tiles...")
        return True