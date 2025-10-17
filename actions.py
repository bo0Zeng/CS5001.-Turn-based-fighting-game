"""
actions.py
招式系统 - Bug修复版
"""

from config import *


class Actions:
    """招式系统"""
    
    @staticmethod
    def attack(attacker, defender, distance, current_turn, current_frame):
        """普通攻击"""
        attacker.vulnerable_action = 'attack'
        
        attack_range = ATTACK_RANGE
        damage = ATTACK_DAMAGE
        
        # 应用蓄力加成
        charge_level = attacker.charge_level
        if charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
            damage += CHARGE_1_DAMAGE_BONUS
            print(f"💥 {attacker.name} 蓄力1攻击！")
            attacker.used_charge_level = 1
            attacker.consume_charge()
        elif charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
            damage += CHARGE_2_DAMAGE_BONUS
            print(f"💥💥 {attacker.name} 蓄力2攻击！")
            attacker.used_charge_level = 2
            attacker.consume_charge()
        else:
            attacker.used_charge_level = 0
        
        # 快速移动加成
        if attacker.dash_buff:
            damage += DASH_DAMAGE_MODIFIER
            print(f"🏃 冲锋加成！伤害+{DASH_DAMAGE_MODIFIER}")
        
        # 检查距离
        if distance > attack_range:
            print(f"❌ {attacker.name} 攻击距离不够（需要{attack_range}格，实际{distance}格）")
            return False
        
        print(f"⚔️ {attacker.name} 攻击 {defender.name}！")
        
        # 造成伤害
        defender.take_damage(damage)
        attacker.action_dealt_damage = True
        
        # 记录连击
        combo_count = defender.record_hit(current_turn, current_frame)
        
        # 检查是否触发硬直
        if combo_count >= COMBO_THRESHOLD:
            defender.apply_stun(COMBO_STUN_FRAMES, current_turn, current_frame)
            defender.reset_combo()
        
        # 蓄力2造成额外硬直
        if charge_level == 2:
            defender.apply_stun(CHARGE_2_STUN_FRAMES, current_turn, current_frame)
        
        return True
    
    @staticmethod
    def charge(player, current_turn, current_frame):
        """蓄力"""
        player.vulnerable_action = 'charge'
        
        print(f"✨ {player.name} 开始蓄力...")
        player.start_charge(current_turn, current_frame)
        return True
    
    @staticmethod
    def control(attacker, defender, distance, current_turn, current_frame):
        """控制"""
        if distance > CONTROL_RANGE:
            print(f"❌ {attacker.name} 控制未命中（需要{CONTROL_RANGE}格，实际{distance}格）")
            print(f"😵 {attacker.name} 因控制失败而硬直！")
            attacker.apply_stun(CONTROL_MISS_STUN_FRAMES, current_turn, current_frame)
            return False
        
        print(f"🔒 {attacker.name} 控制了 {defender.name}！")
        
        # 被控制者向攻击者移动一格
        if attacker.is_left:
            defender.position -= 1
        else:
            defender.position += 1
        
        print(f"   {defender.name} 被拉到位置 {defender.position}（距离变为0）")
        
        # 设置控制状态
        defender.controlled = True
        defender.actions_cancelled = True
        print(f"   {defender.name} 当前帧及后续行动被取消！")
        
        # 如果对手在蓄力，失去蓄力并受伤
        if defender.is_charging or defender.charge_level > 0:
            defender.lose_charge("（被控制）")
            defender.take_damage(CHARGE_CONTROLLED_DAMAGE)
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """抱摔"""
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法抱摔")
            return False
        
        print(f"🤼 {attacker.name} 抱摔 {defender.name}！")
        
        defender.take_damage(GRAB_DAMAGE)
        
        # 推开对手
        old_pos = defender.position
        if defender.is_left:
            new_pos = max(1, defender.position - 1)
        else:
            new_pos = min(MAP_SIZE, defender.position + 1)
        
        defender.position = new_pos
        if new_pos != old_pos:
            print(f"   {defender.name} 被推到位置 {defender.position}")
        
        defender.controlled = False
        print(f"🔓 解除控制")
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """投掷"""
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法投掷")
            return False
        
        print(f"🌪️ {attacker.name} 投掷 {defender.name}！")
        
        defender.take_damage(THROW_DAMAGE)
        
        # 投掷方向：向被控制者原本的方向
        old_pos = defender.position
        if defender.is_left:
            new_pos = max(1, defender.position - THROW_DISTANCE)
        else:
            new_pos = min(MAP_SIZE, defender.position + THROW_DISTANCE)
        
        defender.position = new_pos
        print(f"   {defender.name} 被投掷到位置 {defender.position}")
        
        defender.controlled = False
        print(f"🔓 解除控制")
        return True
    
    @staticmethod
    def defend(player):
        """防御"""
        print(f"🛡️ {player.name} 防御姿态")
        player.defending = True
        return True
    
    @staticmethod
    def counter(player):
        """防御反击"""
        print(f"⚔️🛡️ {player.name} 防御反击姿态")
        player.defending = True
        player.countering = True
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """爆血 - 无距离限制"""
        attacker.vulnerable_action = 'burst'
        
        print(f"💥 {attacker.name} 爆血！")
        
        # 解除自身被控制状态
        was_controlled = attacker.controlled
        attacker.controlled = False
        
        # 自损
        attacker.take_damage(BURST_SELF_DAMAGE)
        print(f"   {attacker.name}自损{BURST_SELF_DAMAGE}伤害")
        
        # 计算对手伤害（6-距离）
        defender_damage = max(0, BURST_BASE_DAMAGE - distance)
        
        if defender_damage > 0:
            defender.take_damage(defender_damage)
            attacker.action_dealt_damage = True
            
            if was_controlled:
                print(f"🔓 {attacker.name} 解除被控制状态")
            
            # 解除对手的控制
            if defender.controlled:
                defender.controlled = False
                print(f"🔓 {defender.name} 解除被控制状态")
            
            return True
        else:
            print(f"   爆血距离过远（{distance}格），无法伤害对手")
            if was_controlled:
                print(f"🔓 {attacker.name} 解除被控制状态")
            return False
    
    @staticmethod
    def move(player, opponent, direction):
        """移动"""
        # 计算新位置
        if direction == 'left':
            new_position = player.position - 1
            action_name = "向左移动" if player.is_left else "向左移动"
        else:
            new_position = player.position + 1
            action_name = "向右移动"
        
        # 检查边界
        if new_position < 1 or new_position > MAP_SIZE:
            print(f"❌ {player.name} 无法移动，已到达边界")
            return False
        
        # 检查是否会与对手重叠
        if new_position == opponent.position:
            print(f"❌ {player.name} 无法移动，会与对手重叠")
            return False
        
        player.position = new_position
        print(f"🏃 {player.name} 移动到位置 {player.position}")
        return True
    
    @staticmethod
    def dash(player, opponent, direction):
        """快速移动"""
        if direction == 'left':
            target_pos = player.position - 2
        else:
            target_pos = player.position + 2
        
        # 限制在地图内
        target_pos = max(1, min(MAP_SIZE, target_pos))
        
        # 检查是否会穿越对手
        if player.position < opponent.position <= target_pos or target_pos <= opponent.position < player.position:
            if player.position < opponent.position:
                target_pos = opponent.position - 1
            else:
                target_pos = opponent.position + 1
            print(f"🚀 {player.name} 冲刺被对手阻挡，停在位置 {target_pos}")
        else:
            print(f"🚀 {player.name} 冲刺到位置 {target_pos}")
        
        # 检查是否会与对手重叠
        if target_pos == opponent.position:
            print(f"❌ {player.name} 无法冲刺，会与对手重叠")
            return False
        
        player.position = target_pos
        player.dash_buff = True
        print(f"   {player.name}进入冲锋状态")
        return True