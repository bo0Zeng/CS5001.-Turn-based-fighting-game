"""
player.py
玩家类 - 纯状态管理（完全状态化终极版）
"""

from config import PLAYER_MAX_HP


class Player:
    """玩家类 - 纯状态管理"""
    
    def __init__(self, name, position=1):
        self.name = name
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.position = position
        self.is_left = None  # 固定身份（在CombatManager中设置）
        
        # ===== 持久状态 =====
        self.controlled = False
        self.controller = None
        self.charge_level = 0
        self.last_charge_turn = -1
        self.last_charge_frame = -1
        self.dash_buff_stacks = 0
        
        # ===== 连击追踪 =====
        self.combo_count = 0
        self.last_hit_turn = -1
        self.last_hit_frame = -1
        
        # ===== 硬直追踪 =====
        self.locked_frames = []  # [(turn, frame), ...]
        
        # ===== 待处理状态队列 =====
        self.position_states = []   # 位置变化状态
        self.damage_states = []     # 伤害状态
        self.defense_states = []    # 防御状态
        self.control_states = []    # 控制状态
        self.buff_states = []       # Buff变化状态
        self.marker_states = []     # 标记状态
        
        # ===== 单帧临时标记（通过marker_states设置）=====
        self.position_before_move = position
        self.attack_range_this_frame = 0
        self.tried_attack_this_frame = False
        self.dealt_damage_this_frame = False
        self.took_damage_this_frame = False
        self.used_charge_2_this_frame = False
        self.grab_damage_buff = 0
    
    # ========== 状态队列管理 ==========
    def add_position_state(self, delta):
        """添加位置变化状态"""
        from state import PositionState
        self.position_states.append(PositionState(delta))
    
    def add_damage_state(self, amount, source=""):
        """添加伤害状态"""
        from state import DamageState
        self.damage_states.append(DamageState(amount, source))
    
    def add_defense_state(self, reduction):
        """添加防御状态"""
        from state import DefenseState
        self.defense_states.append(DefenseState(reduction))
    
    def add_control_state(self, state_type, value=0, target=None):
        """添加控制状态"""
        from state import ControlState
        self.control_states.append(ControlState(state_type, value, target))
    
    def add_buff_state(self, buff_type, action, value=0):
        """添加Buff变化状态"""
        from state import BuffState
        self.buff_states.append(BuffState(buff_type, action, value))
    
    def add_marker_state(self, marker_type):
        """添加标记状态"""
        from state import MarkerState
        self.marker_states.append(MarkerState(marker_type))
    
    def clear_all_states(self):
        """清空所有状态队列"""
        self.position_states = []
        self.damage_states = []
        self.defense_states = []
        self.control_states = []
        self.buff_states = []
        self.marker_states = []
    
    def has_marker(self, marker_type):
        """检查是否有某个标记
        
        Args:
            marker_type: 标记类型
            
        Returns:
            bool: True=有这个标记
        """
        return any(s.type == marker_type and not s.cancelled for s in self.marker_states)
    
    # ========== 硬直管理 ==========
    def lock_frame(self, turn, frame):
        """锁定某一帧"""
        if (turn, frame) not in self.locked_frames:
            self.locked_frames.append((turn, frame))
    
    def is_frame_locked(self, turn, frame):
        """检查某一帧是否被锁定"""
        return (turn, frame) in self.locked_frames
    
    def clear_old_locks(self, current_turn):
        """清理过期的硬直记录"""
        self.locked_frames = [(t, f) for t, f in self.locked_frames if t >= current_turn]
    
    # ========== 蓄力管理 ==========
    def can_stack_charge(self, current_turn, current_frame, last_turn, last_frame):
        """检查是否可以叠加蓄力（连续两帧）"""
        # 同回合连续帧
        if current_turn == last_turn and current_frame == last_frame + 1:
            return True
        # 跨回合连续帧
        if current_turn == last_turn + 1 and last_frame == 2 and current_frame == 1:
            return True
        return False
    
    # ========== 连击管理 ==========
    def is_hit_consecutive(self, current_turn, current_frame):
        """检查是否连续被击中"""
        if self.combo_count == 0:
            return True
        # 同回合连续帧
        if current_turn == self.last_hit_turn and current_frame == self.last_hit_frame + 1:
            return True
        # 跨回合连续帧
        if current_turn == self.last_hit_turn + 1 and self.last_hit_frame == 2 and current_frame == 1:
            return True
        return False
    
    # ========== 帧重置 ==========
    def reset_frame(self):
        """重置单帧状态（每帧开始时调用）"""
        self.position_before_move = self.position
        self.attack_range_this_frame = 0
        self.tried_attack_this_frame = False
        self.dealt_damage_this_frame = False
        self.took_damage_this_frame = False
        self.used_charge_2_this_frame = False
        self.grab_damage_buff = 0
        self.clear_all_states()
    
    # ========== 显示 ==========
    def show_status(self):
        """显示玩家状态"""
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
        """检查是否存活"""
        return self.hp > 0