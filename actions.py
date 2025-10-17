"""
actions.py
招式系统 - 所有招式的实现
"""

from config import (
    PUNCH_DAMAGE, PUNCH_RANGE,
    KICK_DAMAGE, KICK_RANGE,
    GRAB_DAMAGE, THROW_DAMAGE, THROW_DISTANCE,
    BURST_SELF_DAMAGE, BURST_BASE_DAMAGE, BURST_MISS_DAMAGE, BURST_RANGE,
    MAP_SIZE, COMBO_THRESHOLD
)


class Actions:
    """招式系统 - 所有招式作为静态方法"""
    
    @staticmethod
    def punch(attacker, defender, distance):
        """
        拳攻击
        
        Args:
            attacker: 攻击者
            defender: 防御者
            distance: 当前距离
        
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
            defender.stun_frames += 1
            defender.combo_count = 0
            print(f"💫 {defender.name} 连击触发硬直！")
        
        return True
    
    @staticmethod
    def kick(attacker, defender, distance):
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
            defender.stun_frames += 1
            defender.combo_count = 0
            print(f"💫 {defender.name} 连击触发硬直！")
        
        return True
    
    @staticmethod
    def control(attacker, defender, distance):
        """控制对手"""
        if distance > 1:
            print(f"❌ {attacker.name} 控制距离不够")
            return False
        
        print(f"🔒 {attacker.name} 控制了 {defender.name}！")
        defender.controlled = True
        
        # 如果对手有蓄力buff，失去并受伤
        if defender.charge_buff > 0:
            defender.charge_buff = 0
            defender.take_damage(1)
            print(f"💔 {defender.name} 失去蓄力buff并受到1伤害")
        
        return True
    
    @staticmethod
    def grab(attacker, defender):
        """抱摔（需要对手被控制）"""
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
        defender.controlled = False
        return True
    
    @staticmethod
    def throw(attacker, defender):
        """投掷（需要对手被控制）"""
        if not defender.controlled:
            print(f"❌ {defender.name} 未被控制，无法投掷")
            return False
        
        print(f"🌪️ {attacker.name} 投掷 {defender.name}！")
        
        defender.take_damage(THROW_DAMAGE)
        defender.position = min(MAP_SIZE, defender.position + THROW_DISTANCE)
        defender.controlled = False
        
        print(f"   {defender.name} 被击退到位置 {defender.position}")
        return True
    
    @staticmethod
    def burst(attacker, defender, distance):
        """爆血"""
        print(f"💥 {attacker.name} 爆血！")
        
        if distance > BURST_RANGE:
            # 未击中
            attacker.take_damage(BURST_MISS_DAMAGE)
            print(f"   爆血未击中！{attacker.name}自损{BURST_MISS_DAMAGE}伤害")
            return False
        else:
            # 击中
            defender_damage = BURST_BASE_DAMAGE - distance
            attacker.take_damage(BURST_SELF_DAMAGE)
            defender.take_damage(defender_damage)
            
            print(f"   {attacker.name}自损{BURST_SELF_DAMAGE}伤害")
            print(f"   {defender.name}受到{defender_damage}伤害")
            
            # 解除控制
            attacker.controlled = False
            defender.controlled = False
            
            return True
    
    @staticmethod
    def defend(player):
        """防御"""
        print(f"🛡️ {player.name} 防御姿态")
        player.defending = True
        return True
    
    @staticmethod
    def move_forward(player):
        """前进"""
        if player.position >= MAP_SIZE:
            print(f"❌ {player.name} 无法前进，已到达边界")
            return False
        
        player.position += 1
        print(f"🏃 {player.name} 前进到位置 {player.position}")
        return True
    
    @staticmethod
    def move_back(player):
        """后退"""
        if player.position <= 1:
            print(f"❌ {player.name} 无法后退，已到达边界")
            return False
        
        player.position -= 1
        print(f"🏃 {player.name} 后退到位置 {player.position}")
        return True
    
    @staticmethod
    def dash(player):
        """快速移动"""
        if player.position + 2 > MAP_SIZE:
            # 移动到边界
            player.position = MAP_SIZE
            print(f"🚀 {player.name} 快速移动到边界位置 {player.position}")
        else:
            player.position += 2
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
    Actions.punch(alice, bob, distance)
    
    print("\n测试控制+抱摔：")
    alice.position = 2
    bob.position = 3
    distance = 1
    Actions.control(alice, bob, distance)
    Actions.grab(alice, bob)