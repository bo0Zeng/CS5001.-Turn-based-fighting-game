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
        self.stun_frames = 0         # 硬直帧数
        
        # 蓄力相关
        self.charge_buff = 0         # 蓄力buff（0/1/3）
        self.charge_cancel_risk = 0  # 蓄力取消风险窗口
        
        # 快速移动相关
        self.dash_buff = False       # 快速移动buff
    
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
        if self.stun_frames > 0:
            states.append(f"硬直{self.stun_frames}帧")
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
        # 减少硬直
        if self.stun_frames > 0:
            self.stun_frames -= 1
        
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
    
    print("\n受到伤害：")
    player.take_damage(5)
    player.show_status()
    
    print(f"\n存活状态: {player.is_alive()}")