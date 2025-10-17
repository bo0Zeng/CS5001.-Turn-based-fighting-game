"""
player.py
玩家类 - 只管理玩家状态，不包含游戏规则
"""

from config import PLAYER_MAX_HP


class Player:
    """玩家类 - 纯状态管理"""
    
    def __init__(self, name, position=1):
        self.name = name
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.position = position
        self.is_left = None
        
        # ===== 持久状态 =====
        self.controlled = False
        self.controller = None  # 记录控制者名字
        self.charge_level = 0
        self.last_charge_turn = -1
        self.last_charge_frame = -1
        self.dash_buff_stacks = 0
        
        # ===== 连击追踪 =====
        self.combo_count = 0
        self.last_hit_turn = -1
        self.last_hit_frame = -1
        
        # ===== 硬直追踪 =====
        self.locked_frames = []
        
        # ===== 待处理状态队列 =====
        self.position_states = []
        self.damage_states = []
        self.defense_states = []
        
        # ===== 单帧临时标记 =====
        self.defending = False
        self.countering = False
        self.position_before_move = position
        self.attack_range_this_frame = 0
        self.tried_attack_this_frame = False
        self.dealt_damage_this_frame = False
        self.took_damage_this_frame = False
        self.used_charge_2_this_frame = False
        self.should_knockback = False
        self.grab_damage_buff = 0  # 抱摔伤害+2（仅本帧有效）
    
    # ========== 状态队列管理 ==========
    def add_position_state(self, delta):
        from state import PositionState
        self.position_states.append(PositionState(delta))
    
    def add_damage_state(self, amount, source=""):
        from state import DamageState
        self.damage_states.append(DamageState(amount, source))
    
    def add_defense_state(self, reduction):
        from state import DefenseState
        self.defense_states.append(DefenseState(reduction))
    
    def clear_all_states(self):
        self.position_states = []
        self.damage_states = []
        self.defense_states = []
    
    # ========== 硬直管理 ==========
    def lock_frame(self, turn, frame):
        if (turn, frame) not in self.locked_frames:
            self.locked_frames.append((turn, frame))
    
    def is_frame_locked(self, turn, frame):
        return (turn, frame) in self.locked_frames
    
    def clear_old_locks(self, current_turn):
        self.locked_frames = [(t, f) for t, f in self.locked_frames if t >= current_turn]
    
    # ========== 蓄力管理 ==========
    def can_stack_charge(self, current_turn, current_frame, last_turn, last_frame):
        if current_turn == last_turn and current_frame == last_frame + 1:
            return True
        if current_turn == last_turn + 1 and last_frame == 2 and current_frame == 1:
            return True
        return False
    
    # ========== 连击管理 ==========
    def is_hit_consecutive(self, current_turn, current_frame):
        if self.combo_count == 0:
            return True
        if current_turn == self.last_hit_turn and current_frame == self.last_hit_frame + 1:
            return True
        if current_turn == self.last_hit_turn + 1 and self.last_hit_frame == 2 and current_frame == 1:
            return True
        return False
    
    # ========== 帧重置 ==========
    def reset_frame(self):
        """重置单帧状态"""
        self.defending = False
        self.countering = False
        self.position_before_move = self.position
        self.attack_range_this_frame = 0
        self.tried_attack_this_frame = False
        self.dealt_damage_this_frame = False
        self.took_damage_this_frame = False
        self.used_charge_2_this_frame = False
        self.should_knockback = False
        self.grab_damage_buff = 0  # 清零抱摔buff（仅本帧有效）
        self.clear_all_states()
    
    # ========== 显示 ==========
    def show_status(self):
        status = f"📊 {self.name}: HP={self.hp}/{self.max_hp}, 位置={self.position}"
        
        states = []
        if self.controlled:
            states.append(f"被{self.controller}控制")
        if self.charge_level > 0:
            states.append(f"蓄力{self.charge_level}")
        if self.dash_buff_stacks > 0:
            states.append(f"冲锋x{self.dash_buff_stacks}")
        if self.grab_damage_buff > 0:
            states.append(f"抱摔伤+{self.grab_damage_buff}")
        if self.combo_count > 0:
            states.append(f"连击{self.combo_count}/3")
        
        if states:
            status += " [" + ", ".join(states) + "]"
        
        print(status)
    
    def is_alive(self):
        return self.hp > 0