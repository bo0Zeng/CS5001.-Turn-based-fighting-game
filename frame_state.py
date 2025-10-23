"""
frame_state.py
帧状态系统 - 存储每个玩家在一帧内的状态 / Frame State System - Stores each player's state within a frame
"""


class FrameState:
    """单帧状态 - 存储玩家在一帧内的所有状态 / Single Frame State - Stores all player states within a frame"""
    
    def __init__(self, player):
        """
        初始化帧状态 / Initialize frame state
        
        Args:
            player: 玩家对象 / Player object
        """
        self.player = player
        
        # 位置状态 / Position state
        self.target_position = None  # 目标位置 / Target position
        self.is_moving = False       # 是否在移动 / Whether moving
        self.move_steps = 1          # 移动步数（普通移动1步，冲刺2步） / Move steps (normal move 1 step, dash 2 steps)
        self.move_direction = None   # 移动方向 ('left' 或 'right') / Move direction ('left' or 'right')
        self.position_before = None  # 移动前的位置（用于闪避判定） / Position before move (for dodge judgment)
        self.position_modifiers = []  # [(step:int, kind:str)] kind in {'move','dash'}，按施加顺序记录 / Applied in order
        self.final_position = None    # 冲突解决后的最终位置 / Final position after conflict resolution
        self.successful_move_count = 0  # 成功施加的位移修饰数量 / Number of successfully applied position modifiers
        self.dash_attempted = False   # 本帧是否尝试了冲刺 / Whether dash attempted this frame
        
        # 攻击状态 / Attack state
        self.is_attacking = False    # 是否在攻击 / Whether attacking
        self.attack_damage = 0       # 攻击伤害 / Attack damage
        self.attack_range = 0        # 攻击范围 / Attack range
        
        # 防御状态 / Defense state
        self.is_defending = False    # 是否在防御 / Whether defending
        self.damage_reduction = 0    # 减伤值 / Damage reduction value
        self.is_countering = False   # 是否在反击 / Whether countering
        
        # 控制状态 / Control state
        self.is_controlling = False  # 是否在控制对手 / Whether controlling opponent
        self.control_range = 0       # 控制范围 / Control range
        
        # 特殊状态 / Special state
        self.is_bursting = False     # 是否在爆血 / Whether bursting
        self.is_charging = False     # 是否在蓄力 / Whether charging
        
        # 控制技能 / Control skills
        self.is_grabbing = False     # 是否在抱摔 / Whether grabbing
        self.is_throwing = False     # 是否在投掷 / Whether throwing
        
        # 结算结果 / Settlement results
        self.damage_dealt = 0        # 实际造成的伤害 / Actual damage dealt
        self.damage_taken = 0        # 实际受到的伤害 / Actual damage taken
        self.position_changed = False  # 位置是否改变 / Whether position changed
    
    # ---------------- 位置修饰器接口 / Position Modifier Interface ----------------
    def add_position_modifier(self, step, kind):
        """添加位置修饰器。step为+1或-1，kind为'move'或'dash'。 / Add position modifier. step is +1 or -1, kind is 'move' or 'dash'."""
        if step not in (-1, 1):
            return
        if kind not in ("move", "dash"):
            return
        self.position_modifiers.append((step, kind))
    
    def remove_last_modifier(self):
        """移除最后一次施加的位移修饰，返回被移除的修饰或None。 / Remove the last applied position modifier, return the removed modifier or None."""
        if not self.position_modifiers:
            return None
        return self.position_modifiers.pop()
    
    def get_target_position(self):
        """计算在完全施加当前所有位移修饰后的目标位置。 / Calculate target position after applying all current position modifiers."""
        pos = self.player.position
        for step, _kind in self.position_modifiers:
            pos += step
        return pos
    
    def get_dash_success_step_count(self):
        """统计当前剩余修饰中属于dash的步数。 / Count the number of dash steps in the remaining modifiers."""
        return sum(1 for _step, kind in self.position_modifiers if kind == "dash")
        
    def __repr__(self):
        """字符串表示 / String representation"""
        status = f"{self.player.name}状态: / {self.player.name} status: "
        parts = []
        
        if self.is_moving:
            parts.append(f"移动{self.move_steps}步 / Move {self.move_steps} steps")
        if self.is_attacking:
            parts.append(f"攻击{self.attack_damage}伤害 / Attack {self.attack_damage} damage")
        if self.is_defending:
            parts.append(f"防御-{self.damage_reduction} / Defense -{self.damage_reduction}")
        if self.is_countering:
            parts.append("反击 / Counter")
        if self.is_controlling:
            parts.append("控制 / Control")
        if self.is_bursting:
            parts.append("爆血 / Burst")
        if self.is_charging:
            parts.append("蓄力 / Charge")
        if self.is_grabbing:
            parts.append("抱摔 / Grab")
        if self.is_throwing:
            parts.append("投掷 / Throw")
        
        return status + (", ".join(parts) if parts else "无行动 / No action")


if __name__ == "__main__":
    from player import Player
    
    alice = Player("Alice")
    state = FrameState(alice)
    
    # 测试 / Test
    state.is_defending = True
    state.damage_reduction = 1
    print(state)
    
    state.is_attacking = True
    state.attack_damage = 3
    print(state)