"""
frame_state.py
帧状态系统 - 存储每个玩家在一帧内的状态
"""


class FrameState:
    """单帧状态 - 存储玩家在一帧内的所有状态"""
    
    def __init__(self, player):
        """
        初始化帧状态
        
        Args:
            player: 玩家对象
        """
        self.player = player
        
        # 位置状态
        self.target_position = None  # 目标位置
        self.is_moving = False       # 是否在移动
        self.move_steps = 1          # 移动步数（普通移动1步，冲刺2步）
        self.move_direction = None   # 移动方向 ('left' 或 'right')
        self.position_before = None  # 移动前的位置（用于闪避判定）
        self.position_modifiers = []  # [(step:int, kind:str)] kind in {'move','dash'}，按施加顺序记录
        self.final_position = None    # 冲突解决后的最终位置
        self.successful_move_count = 0  # 成功施加的位移修饰数量
        self.dash_attempted = False   # 本帧是否尝试了冲刺
        
        # 攻击状态
        self.is_attacking = False    # 是否在攻击
        self.attack_damage = 0       # 攻击伤害
        self.attack_range = 0        # 攻击范围
        
        # 防御状态
        self.is_defending = False    # 是否在防御
        self.damage_reduction = 0    # 减伤值
        self.is_countering = False   # 是否在反击
        
        # 控制状态
        self.is_controlling = False  # 是否在控制对手
        self.control_range = 0       # 控制范围
        
        # 特殊状态
        self.is_bursting = False     # 是否在爆血
        self.is_charging = False     # 是否在蓄力
        
        # 控制技能
        self.is_grabbing = False     # 是否在抱摔
        self.is_throwing = False     # 是否在投掷
        
        # 结算结果
        self.damage_dealt = 0        # 实际造成的伤害
        self.damage_taken = 0        # 实际受到的伤害
        self.position_changed = False  # 位置是否改变
    
    # ---------------- 位置修饰器接口 ----------------
    def add_position_modifier(self, step, kind):
        """添加位置修饰器。step为+1或-1，kind为'move'或'dash'。"""
        if step not in (-1, 1):
            return
        if kind not in ("move", "dash"):
            return
        self.position_modifiers.append((step, kind))
    
    def remove_last_modifier(self):
        """移除最后一次施加的位移修饰，返回被移除的修饰或None。"""
        if not self.position_modifiers:
            return None
        return self.position_modifiers.pop()
    
    def get_target_position(self):
        """计算在完全施加当前所有位移修饰后的目标位置。"""
        pos = self.player.position
        for step, _kind in self.position_modifiers:
            pos += step
        return pos
    
    def get_dash_success_step_count(self):
        """统计当前剩余修饰中属于dash的步数。"""
        return sum(1 for _step, kind in self.position_modifiers if kind == "dash")
        
    def __repr__(self):
        """字符串表示"""
        status = f"{self.player.name}状态: "
        parts = []
        
        if self.is_moving:
            parts.append(f"移动{self.move_steps}步")
        if self.is_attacking:
            parts.append(f"攻击{self.attack_damage}伤害")
        if self.is_defending:
            parts.append(f"防御-{self.damage_reduction}")
        if self.is_countering:
            parts.append("反击")
        if self.is_controlling:
            parts.append("控制")
        if self.is_bursting:
            parts.append("爆血")
        if self.is_charging:
            parts.append("蓄力")
        if self.is_grabbing:
            parts.append("抱摔")
        if self.is_throwing:
            parts.append("投掷")
        
        return status + (", ".join(parts) if parts else "无行动")


if __name__ == "__main__":
    from player import Player
    
    alice = Player("Alice")
    state = FrameState(alice)
    
    # 测试
    state.is_defending = True
    state.damage_reduction = 1
    print(state)
    
    state.is_attacking = True
    state.attack_damage = 3
    print(state)