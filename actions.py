"""
actions.py
招式系统 - 所有招式的实现
"""

from config import (
    PUNCH_DAMAGE, PUNCH_RANGE,
    KICK_DAMAGE, KICK_RANGE,
    GRAB_DAMAGE, THROW_DAMAGE, THROW_DISTANCE,
    BURST_SELF_DAMAGE, BURST_BASE_DAMAGE, BURST_MISS_DAMAGE, BURST_RANGE, BURST_KNOCKBACK,
    MAP_SIZE, COMBO_THRESHOLD, STUN_FRAMES
)


class Actions:
    """招式系统 - 所有招式作为静态方法"""
    
    @staticmethod
    def punch(attacker, defender, distance, current_turn, current_frame):
        """
        拳攻击
        
        Args:
            attacker: 攻击者
            defender: 防御者
            distance: 当前距离
            current_turn: 当前回合号
            current_frame: 当前帧号
        
        Returns:
            bool: 是否成功
        """
        if distance > PUNCH_RANGE:
            print(f"❌ {attacker.name} 拳攻击距离不够（需要{PUNCH_RANGE}格，实际{distance}格）")
            return False
        
        print(f"⚔️ {attacker.name} 拳攻击 {defender.name}！")
        
        # 基础伤害
        damage = PUNCH_DAMAGE
        
        # 应用蓄力buff
        if attacker.charge_buff > 0:
            damage += attacker.charge_buff
            print(f"💥 蓄力加成！伤害+{attacker.charge_buff}")
            attacker.charge_buff = 0  # 消耗buff
        
        defender.take_damage(damage)
        
        # 累积连击
        defender.combo_count += 1
        print(f"🎯 {defender.name} 连击计数：{defender.combo_count}/{COMBO_THRESHOLD}")
        
        if defender.combo_count >= COMBO_THRESHOLD:
            # 使用配置的硬直帧数
            stun_frames = STUN_FRAMES.get('combo', 1)
            defender.apply_stun(stun_frames, current_turn, current_frame)
            defender.combo_count = 0
        
        return True
    
    @staticmethod
    def kick(attacker, defender, distance, current_turn, current_frame):
        """腿攻击"""
        if distance > KICK_RANGE:
            print(f"❌ {attacker.name} 腿攻击距离不够（需要{KICK_RANGE}格，实际{distance}格）")
            return False
        
        print(f"🦵 {attacker.name} 腿攻击 {defender.name}！")
        
        damage = KICK_DAMAGE
        
        if attacker.charge_buff > 0:
            damage += attacker.charge_buff
            print(f"💥 蓄力加成！伤害+{attacker.charge_buff}")
            attacker.charge_buff = 0
        
        defender.take_damage(damage)
        
        # 累积连击
        defender.combo_count += 1
        print(f"🎯 {defender.name} 连击计数：{defender.combo_count}/{COMBO_THRESHOLD}")
        
        if defender.combo_count >= COMBO_THRESHOLD:
            stun_frames = STUN_FRAMES.get('combo', 1)
            defender.apply_stun(stun_frames, current_turn, current_frame)
            defender.combo_count = 0
        
        return True
    
    @staticmethod
    def control(attacker, defender, distance):
        """
        控制对手
        新机制：控制成功时，双方距离变为0，防御者向攻击者移动一格
        被控制者当前帧行动被打断，后续行动被取消
        """
        if distance > 1:
            print(f"❌ {attacker.name} 控制距离不够（需要1格，实际{distance}格）")
            return False
        
        print(f"🔒 {attacker.name} 控制了 {defender.name}！")
        
        # 被控制者向攻击者移动一格（距离变为0）
        if attacker.is_left:
            # 攻击者在左边，被控制者向左移动
            defender.position -= 1
        else:
            # 攻击者在右边，被控制者向右移动
            defender.position += 1
        
        print(f"   {defender.name} 被拉到位置 {defender.position}（距离变为0）")
        
        # 设置控制状态
        defender.controlled = True
        
        # 取消被控制者的后续行动
        defender.actions_cancelled = True
        print(f"   {defender.name} 当前帧及后续行动被取消！")
        
        # 如果对手有蓄力buff，失去并受伤
        if defender.charge_buff > 0:
            defender.charge_buff = 0
            defender.take_damage(1)
            print(f"💔 {defender.name} 失去蓄力buff并受到1伤害")
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """
        抱摔（需要对手被控制）
        执行后自动解除控制，并将对手推开1格
        """
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法抱摔")
            return False
        
        print(f"🤼 {attacker.name} 抱摔 {defender.name}！")
        
        damage = GRAB_DAMAGE
        
        # 应用蓄力buff
        if attacker.charge_buff > 0:
            damage += attacker.charge_buff
            print(f"💥 蓄力加成！伤害+{attacker.charge_buff}")
            attacker.charge_buff = 0
        
        defender.take_damage(damage)
        
        # 将对手推开1格（向其原本方向）
        old_pos = defender.position
        if defender.is_left:
            # 向左推
            new_pos = max(1, defender.position - 1)
        else:
            # 向右推
            new_pos = min(MAP_SIZE, defender.position + 1)
        
        defender.position = new_pos
        if new_pos != old_pos:
            print(f"   {defender.name} 被推到位置 {defender.position}")
        
        defender.controlled = False
        print(f"🔓 解除控制")
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """
        投掷（需要对手被控制）
        执行后自动解除控制
        """
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
        defender.controlled = False
        
        print(f"   {defender.name} 被投掷到位置 {defender.position}")
        print(f"🔓 解除控制")
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """
        爆血
        新机制：伤害改为 6-距离，解除自身被控制，击退对手最多2格
        """
        print(f"💥 {attacker.name} 爆血！")
        
        # 解除自身被控制状态（在计算伤害之前）
        was_controlled = attacker.controlled
        attacker.controlled = False
        
        if distance > BURST_RANGE:
            # 未击中
            attacker.take_damage(BURST_MISS_DAMAGE)
            print(f"   爆血未击中！{attacker.name}自损{BURST_MISS_DAMAGE}伤害")
            if was_controlled:
                print(f"🔓 {attacker.name} 解除被控制状态")
            return False
        else:
            # 击中
            defender_damage = BURST_BASE_DAMAGE - distance
            attacker.take_damage(BURST_SELF_DAMAGE)
            defender.take_damage(defender_damage)
            
            print(f"   {attacker.name}自损{BURST_SELF_DAMAGE}伤害")
            print(f"   {defender.name}受到{defender_damage}伤害")
            
            if was_controlled:
                print(f"🔓 {attacker.name} 解除被控制状态")
            
            # 解除对手的控制状态
            if defender.controlled:
                defender.controlled = False
                print(f"🔓 {defender.name} 解除被控制状态")
            
            # 击退效果：对手向其原本方向击退最多2格
            old_pos = defender.position
            if defender.is_left:
                # 对手在左边，向左击退（减少位置）
                new_pos = max(1, defender.position - BURST_KNOCKBACK)
            else:
                # 对手在右边，向右击退（增加位置）
                new_pos = min(MAP_SIZE, defender.position + BURST_KNOCKBACK)
            
            defender.position = new_pos
            knockback_distance = abs(new_pos - old_pos)
            
            if knockback_distance > 0:
                print(f"   {defender.name} 被击退{knockback_distance}格到位置 {defender.position}")
            else:
                print(f"   {defender.name} 已在边界，无法击退")
            
            return True
    
    @staticmethod
    def defend(player):
        """防御"""
        print(f"🛡️ {player.name} 防御姿态")
        player.defending = True
        return True
    
    @staticmethod
    def move_forward(player, opponent):
        """
        前进
        新增opponent参数用于检查距离限制
        """
        # 检查是否在边界
        if player.is_left and player.position >= MAP_SIZE:
            print(f"❌ {player.name} 无法前进，已到达边界")
            return False
        elif not player.is_left and player.position <= 1:
            print(f"❌ {player.name} 无法前进，已到达边界")
            return False
        
        # 计算前进后的位置
        if player.is_left:
            new_position = player.position + 1
        else:
            new_position = player.position - 1
        
        # 检查是否会导致距离为0（穿越对手）
        if new_position == opponent.position:
            print(f"❌ {player.name} 无法前进，会与对手重叠")
            return False
        
        player.position = new_position
        print(f"🏃 {player.name} 前进到位置 {player.position}")
        return True
    
    @staticmethod
    def move_back(player, opponent):
        """
        后退
        新增opponent参数用于检查距离限制
        """
        # 检查是否在边界
        if player.is_left and player.position <= 1:
            print(f"❌ {player.name} 无法后退，已到达边界")
            return False
        elif not player.is_left and player.position >= MAP_SIZE:
            print(f"❌ {player.name} 无法后退，已到达边界")
            return False
        
        # 计算后退后的位置
        if player.is_left:
            new_position = player.position - 1
        else:
            new_position = player.position + 1
        
        # 检查是否会导致距离为0（虽然后退一般不会）
        if new_position == opponent.position:
            print(f"❌ {player.name} 无法后退，会与对手重叠")
            return False
        
        player.position = new_position
        print(f"🏃 {player.name} 后退到位置 {player.position}")
        return True
    
    @staticmethod
    def dash(player, opponent):
        """
        快速移动
        新增opponent参数用于检查距离限制
        """
        # 计算冲刺后的位置
        if player.is_left:
            # 在左边，向右冲刺2格
            if player.position + 2 > MAP_SIZE:
                new_position = MAP_SIZE
            else:
                new_position = player.position + 2
        else:
            # 在右边，向左冲刺2格
            if player.position - 2 < 1:
                new_position = 1
            else:
                new_position = player.position - 2
        
        # 检查是否会穿越对手
        if player.is_left:
            # 左边玩家向右冲，检查是否越过右边的对手
            if player.position < opponent.position <= new_position:
                new_position = opponent.position - 1
                print(f"🚀 {player.name} 快速移动被对手阻挡，停在位置 {new_position}")
        else:
            # 右边玩家向左冲，检查是否越过左边的对手
            if player.position > opponent.position >= new_position:
                new_position = opponent.position + 1
                print(f"🚀 {player.name} 快速移动被对手阻挡，停在位置 {new_position}")
        
        if new_position == opponent.position:
            print(f"❌ {player.name} 无法冲刺，会与对手重叠")
            return False
        
        player.position = new_position
        if player.position == MAP_SIZE or player.position == 1:
            print(f"🚀 {player.name} 快速移动到边界位置 {player.position}")
        else:
            print(f"🚀 {player.name} 快速移动到位置 {player.position}")
        
        player.dash_buff = True
        print(f"   下回合{player.name}造成和受到伤害+1")
        return True


if __name__ == "__main__":
    # 测试代码
    from player import Player
    
    print("=== 测试 Actions ===\n")
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    
    distance = abs(alice.position - bob.position)
    
    print("测试拳攻击：")
    Actions.punch(alice, bob, distance, current_turn=1, current_frame=1)
    
    print("\n测试控制+抱摔：")
    alice.position = 2
    bob.position = 3
    distance = 1
    Actions.control(alice, bob, distance)
    Actions.grab(alice, bob)