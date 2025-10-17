"""
player.py
玩家类 - 管理玩家状态和基础属性
"""

from config import PLAYER_MAX_HP, COMBO_THRESHOLD


class Player:
    """玩家类 - 存储玩家的所有状态"""
    
    def __init__(self, name, position=1):
        """初始化玩家"""
        self.name = name
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.position = position
        
        # 基础状态
        self.controlled = False      # 是否被控制
        self.defending = False       # 是否在防御
        self.countering = False      # 是否在防御反击
        self.is_left = None          # 是否在左边
        self.actions_cancelled = False  # 当前回合行动是否被取消
        
        # 硬直机制
        self.stun_frames_remaining = 0
        self.locked_frames = []      # [(回合号, 帧号), ...]
        
        # 蓄力系统
        self.charge_level = 0        # 蓄力等级 (0/1/2)
        self.last_charge_turn = -1   # 上次蓄力的回合
        self.last_charge_frame = -1  # 上次蓄力的帧
        self.is_charging = False     # 当前帧是否在蓄力
        
        # 连击系统（必须连续）
        self.combo_count = 0         # 连续连击计数
        self.last_hit_turn = -1      # 上次被击中的回合
        self.last_hit_frame = -1     # 上次被击中的帧
        
        # 快速移动buff
        self.dash_buff = False
        
        # 打断追踪
        self.vulnerable_action = None  # 当前帧的脆弱行动（attack/charge/burst）
        self.action_dealt_damage = False  # 当前帧行动是否造成了伤害
    
    def apply_stun(self, frames, current_turn, current_frame):
        """应用硬直效果"""
        self.stun_frames_remaining = frames
        locked = []
        turn = current_turn
        frame = current_frame
        
        for _ in range(frames):
            frame += 1
            if frame > 2:
                frame = 1
                turn += 1
            locked.append((turn, frame))
        
        self.locked_frames.extend(locked)
        print(f"😵 {self.name} 受到 {frames} 帧硬直！")
        for t, f in locked:
            print(f"   🔒 回合{t}第{f}帧被锁定")
    
    def is_frame_locked(self, turn, frame):
        """检查指定帧是否被锁定"""
        return (turn, frame) in self.locked_frames
    
    def clear_expired_locks(self, current_turn):
        """清除已过期的锁定"""
        self.locked_frames = [(t, f) for t, f in self.locked_frames if t >= current_turn]
    
    def start_charge(self, current_turn, current_frame):
        """开始蓄力"""
        # 检查是否可以叠加蓄力
        can_stack = False
        if self.charge_level == 1:
            # 检查是否紧接着上次蓄力
            if current_turn == self.last_charge_turn and current_frame == self.last_charge_frame + 1:
                can_stack = True  # 同回合连续帧
            elif current_turn == self.last_charge_turn + 1 and self.last_charge_frame == 2 and current_frame == 1:
                can_stack = True  # 跨回合连续帧
        
        if can_stack:
            self.charge_level = 2
            print(f"✨ {self.name} 蓄力2！下次攻击伤害+3，距离+1，造成硬直")
        else:
            self.charge_level = 1
            print(f"✨ {self.name} 蓄力1！下次攻击伤害+1，距离+1")
        
        self.last_charge_turn = current_turn
        self.last_charge_frame = current_frame
        self.is_charging = True
    
    def consume_charge(self):
        """消耗蓄力状态"""
        level = self.charge_level
        self.charge_level = 0
        self.last_charge_turn = -1
        self.last_charge_frame = -1
        return level
    
    def lose_charge(self, reason=""):
        """失去蓄力状态"""
        if self.charge_level > 0:
            self.charge_level = 0
            self.last_charge_turn = -1
            self.last_charge_frame = -1
            print(f"💔 {self.name} 失去蓄力状态{reason}")
    
    def record_hit(self, current_turn, current_frame):
        """记录被击中（用于连击判定）"""
        # 检查是否连续
        is_consecutive = False
        if self.combo_count > 0:
            if current_turn == self.last_hit_turn and current_frame == self.last_hit_frame + 1:
                is_consecutive = True  # 同回合连续帧
            elif current_turn == self.last_hit_turn + 1 and self.last_hit_frame == 2 and current_frame == 1:
                is_consecutive = True  # 跨回合连续帧
        else:
            is_consecutive = True  # 第一次被击中
        
        if is_consecutive:
            self.combo_count += 1
            self.last_hit_turn = current_turn
            self.last_hit_frame = current_frame
            print(f"🎯 {self.name} 连续被击中 {self.combo_count}/{COMBO_THRESHOLD} 次")
            return self.combo_count
        else:
            # 不连续，重置
            self.combo_count = 1
            self.last_hit_turn = current_turn
            self.last_hit_frame = current_frame
            print(f"🎯 {self.name} 被击中（不连续，重置计数）1/{COMBO_THRESHOLD} 次")
            return 1
    
    def reset_combo(self):
        """重置连击"""
        self.combo_count = 0
        self.last_hit_turn = -1
        self.last_hit_frame = -1
    
    def take_damage(self, damage):
        """受到伤害"""
        from config import DEFEND_REDUCTION
        
        # 防御减伤
        if self.defending:
            original_damage = damage
            damage = max(0, damage - DEFEND_REDUCTION)
            print(f"🛡️ {self.name} 防御！伤害 {original_damage} → {damage}")
        
        # 快速移动额外伤害
        if self.dash_buff:
            damage += 1
            print(f"🏃 {self.name} 冲刺状态，受伤+1")
        
        # 应用伤害
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        
        if damage > 0:
            print(f"💔 {self.name} 受到 {damage} 伤害，HP: {self.hp}/{self.max_hp}")
        else:
            print(f"🛡️ {self.name} 完全格挡！")
    
    def is_alive(self):
        """检查是否存活"""
        return self.hp > 0
    
    def show_status(self):
        """显示玩家状态"""
        status = f"📊 {self.name}: HP={self.hp}/{self.max_hp}, 位置={self.position}"
        
        states = []
        if self.controlled:
            states.append("被控制")
        if self.defending:
            states.append("防御中")
        if self.countering:
            states.append("反击姿态")
        if self.stun_frames_remaining > 0:
            states.append(f"硬直{self.stun_frames_remaining}帧")
        if self.charge_level > 0:
            states.append(f"蓄力{self.charge_level}")
        if self.dash_buff:
            states.append("冲锋")
        if self.combo_count > 0:
            states.append(f"连击{self.combo_count}/{COMBO_THRESHOLD}")
        
        if states:
            status += " [" + ", ".join(states) + "]"
        
        print(status)
    
    def reset_frame_status(self):
        """重置单帧状态"""
        self.defending = False
        self.countering = False
        self.actions_cancelled = False
        self.is_charging = False
        self.vulnerable_action = None
        self.action_dealt_damage = False
    
    def update_turn_status(self):
        """更新回合状态"""
        self.dash_buff = False


if __name__ == "__main__":
    print("=== 测试 Player 类 ===\n")
    player = Player("Alice", position=2)
    player.show_status()