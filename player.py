"""
player.py
玩家类 - 管理玩家状态和基础属性
"""

from config import PLAYER_MAX_HP, COMBO_THRESHOLD


class Player:
    """玩家类 - 存储玩家的所有状态"""
    
    def __init__(self, name, position=1):
        """
        初始化玩家
        
        Args:
            name: 玩家名字
            position: 初始位置
        """
        self.name = name
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.position = position
        
        # 状态标记
        self.controlled = False      # 是否被控制
        self.defending = False       # 是否在防御
        self.combo_count = 0         # 连击计数
        
        # 新硬直机制
        self.stun_frames_remaining = 0  # 剩余硬直帧数
        self.locked_frames = []          # 被锁定的帧列表 [(回合号, 帧号), ...]
        
        # 蓄力相关
        self.charge_buff = 0         # 蓄力buff（0/1/3）
        self.charge_cancel_risk = 0  # 蓄力取消风险窗口
        
        # 快速移动相关
        self.dash_buff = False       # 快速移动buff
    
    def apply_stun(self, frames, current_turn, current_frame):
        """
        应用硬直效果
        
        Args:
            frames: 硬直帧数
            current_turn: 当前回合号
            current_frame: 当前帧号 (1 or 2)
        """
        self.stun_frames_remaining = frames
        
        # 计算被锁定的帧
        locked = []
        turn = current_turn
        frame = current_frame
        
        for _ in range(frames):
            # 移动到下一帧
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
        """
        检查指定帧是否被锁定
        
        Args:
            turn: 回合号
            frame: 帧号 (1 or 2)
        
        Returns:
            bool: 是否被锁定
        """
        return (turn, frame) in self.locked_frames
    
    def clear_expired_locks(self, current_turn):
        """
        清除已过期的锁定
        
        Args:
            current_turn: 当前回合号
        """
        self.locked_frames = [(t, f) for t, f in self.locked_frames if t >= current_turn]
    
    def take_damage(self, damage):
        """
        受到伤害
        
        Args:
            damage: 伤害值
        """
        # 防御减伤
        from config import DEFEND_REDUCTION
        if self.defending:
            original_damage = damage
            damage = max(0, damage - DEFEND_REDUCTION)
            print(f"🛡️ {self.name} 防御！伤害 {original_damage} → {damage}")
        
        # 快速移动额外伤害
        if self.dash_buff:
            damage += 1
            print(f"🏃 {self.name} 冲锋状态，受伤+1")
        
        # 蓄力取消风险
        if self.charge_cancel_risk > 0:
            damage += 1
            print(f"⚠️ {self.name} 蓄力取消风险期，受伤+1")
        
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
        
        # 添加状态标记
        states = []
        if self.controlled:
            states.append("被控制")
        if self.defending:
            states.append("防御中")
        if self.stun_frames_remaining > 0:
            states.append(f"硬直{self.stun_frames_remaining}帧")
        if self.charge_buff > 0:
            states.append(f"蓄力+{self.charge_buff}")
        if self.dash_buff:
            states.append("冲锋")
        if self.combo_count > 0:
            states.append(f"连击{self.combo_count}/3")
        
        if states:
            status += " [" + ", ".join(states) + "]"
        
        print(status)
    
    def reset_frame_status(self):
        """重置单帧状态（每帧结束时调用）"""
        self.defending = False
    
    def update_turn_status(self):
        """更新回合状态（每回合结束时调用）"""
        # 减少蓄力取消风险窗口
        if self.charge_cancel_risk > 0:
            self.charge_cancel_risk -= 1
        
        # 清除快速移动buff
        self.dash_buff = False


if __name__ == "__main__":
    # 测试代码
    print("=== 测试 Player 类 ===\n")
    
    player = Player("Alice", position=2)
    player.show_status()
    
    print("\n测试硬直机制：")
    player.apply_stun(3, current_turn=1, current_frame=1)
    
    print(f"\n回合1第2帧锁定? {player.is_frame_locked(1, 2)}")
    print(f"回合2第1帧锁定? {player.is_frame_locked(2, 1)}")
    print(f"回合3第1帧锁定? {player.is_frame_locked(3, 1)}")
    
    print("\n受到伤害：")
    player.take_damage(5)
    player.show_status()
    
    print(f"\n存活状态: {player.is_alive()}")