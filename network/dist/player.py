"""
player.py
玩家类 - 纯状态管理（重构版）
Player Class - Pure State Management (Refactored)

"""

from config import PLAYER_MAX_HP


class Player:
    """玩家类 - 纯状态管理 / Player Class - Pure State Management"""
    
    def __init__(self, name, position=1):
        self.name = name
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.position = position
        self.is_left = None
        
        # ===== 持久状态 ===== / ===== Persistent State =====
        self.controlled = False
        self.controller = None
        self.controlled_turn = -1
        self.controlled_frame = -1
        self.charge_level = 0
        self.last_charge_turn = -1
        self.last_charge_frame = -1
        self.dash_buff_stacks = 0
        
        # ===== 连击追踪 ===== / ===== Combo Tracking =====
        self.combo_count = 0
        self.last_hit_turn = -1
        self.last_hit_frame = -1
        
        # ===== 硬直追踪 ===== / ===== Stun Tracking =====
        self.locked_frames = []
        
        # ===== 待处理状态队列 ===== / ===== Pending State Queues =====
        self.position_states = []
        self.damage_states = []
        self.defense_states = []
        self.control_states = []
        self.buff_states = []
        self.action_states = []  # 原marker_states
        
        # ===== 单帧临时属性 ===== / ===== Single Frame Temporary Properties =====
        # （这些将通过action_states查询，不再需要单独字段）
    
    # ========== 状态队列管理 ==========
    def add_position_state(self, delta, source="self"):
        """添加位置变化状态 / Add position change state"""
        from state import PositionState
        self.position_states.append(PositionState(delta, source))
    
    def add_damage_state(self, amount, source=""):
        """添加伤害状态 / Add damage state"""
        from state import DamageState
        self.damage_states.append(DamageState(amount, source))
    
    def add_defense_state(self, reduction):
        """添加防御状态 / Add defense state"""
        from state import DefenseState
        self.defense_states.append(DefenseState(reduction))
    
    def add_control_state(self, state_type, value=0, target=None):
        """添加控制状态 / Add control state"""
        from state import ControlState
        self.control_states.append(ControlState(state_type, value, target))
    
    def add_buff_state(self, buff_type, action, value=0):
        """添加Buff变化状态 / Add buff change state"""
        from state import BuffState
        self.buff_states.append(BuffState(buff_type, action, value))
    
    def add_action_state(self, action_type, value=0):
        """添加行动状态（原add_marker_state）/ Add action state"""
        from state import ActionState
        self.action_states.append(ActionState(action_type, value))
    
    def clear_all_states(self):
        """清空所有状态队列 / Clear all state queues"""
        self.position_states = []
        self.damage_states = []
        self.defense_states = []
        self.control_states = []
        self.buff_states = []
        self.action_states = []
    
    def has_action(self, action_type):
        """检查是否有某个行动状态（原has_marker）/ Check if has a specific action state"""
        return any(s.type == action_type for s in self.action_states)
    
    def get_action_value(self, action_type):
        """获取行动状态的值 / Get action state value"""
        for s in self.action_states:
            if s.type == action_type:
                return s.value
        return 0
    
    # ========== 硬直管理 ==========
    def lock_frame(self, turn, frame):
        """锁定某一帧 / Lock a specific frame"""
        if (turn, frame) not in self.locked_frames:
            self.locked_frames.append((turn, frame))
    
    def is_frame_locked(self, turn, frame):
        """检查某一帧是否被锁定 / Check if a specific frame is locked"""
        return (turn, frame) in self.locked_frames
    
    def clear_old_locks(self, current_turn):
        """清理过期的硬直记录 / Clear expired stun records"""
        self.locked_frames = [(t, f) for t, f in self.locked_frames if t >= current_turn]
    
    # ========== 蓄力管理 ==========
    def can_stack_charge(self, current_turn, current_frame, last_turn, last_frame):
        """检查是否可以叠加蓄力（连续两帧） / Check if charge can be stacked (consecutive two frames)"""
        # 同回合连续帧
        if current_turn == last_turn and current_frame == last_frame + 1:
            return True
        # 跨回合连续帧
        if current_turn == last_turn + 1 and last_frame == 2 and current_frame == 1:
            return True
        return False
    
    # ========== 连击管理 ==========
    def is_hit_consecutive(self, current_turn, current_frame):
        """检查是否连续被击中 / Check if hit consecutively"""
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
        """重置单帧状态（每帧开始时调用） / Reset single frame state (called at the start of each frame)"""
        self.clear_all_states()
    
    # ========== 显示 ==========
    def show_status(self):
        """显示玩家状态 / Show player status"""
        status = f"{self.name}: HP={self.hp}/{self.max_hp}, 位置={self.position} / Position={self.position}"
        
        states = []
        if self.controlled:
            states.append(f"被{self.controller}控制 / Controlled by {self.controller}")
        if self.charge_level > 0:
            states.append(f"蓄力{self.charge_level} / Charge {self.charge_level}")
        if self.dash_buff_stacks > 0:
            states.append(f"冲锋x{self.dash_buff_stacks} / Dash x{self.dash_buff_stacks}")
        if self.combo_count > 0:
            states.append(f"连击{self.combo_count}/3 / Combo {self.combo_count}/3")
        
        if states:
            status += " [" + ", ".join(states) + "]"
        
        print(status)
    
    def is_alive(self):
        """检查是否存活 / Check if alive"""
        return self.hp > 0