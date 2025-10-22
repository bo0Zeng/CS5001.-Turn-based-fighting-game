"""
state.py
状态系统 - 纯数据结构定义（完全状态化终极版）
"""


class PositionState:
    """位置变化状态"""
    def __init__(self, delta):
        self.delta = delta          # 位置变化量（+1/-1）
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        return f"Pos({self.delta:+d})"


class DamageState:
    """伤害状态"""
    def __init__(self, amount, source=""):
        self.amount = amount        # 伤害值
        self.source = source        # 伤害来源
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        return f"Dmg({self.amount})"


class DefenseState:
    """防御状态"""
    def __init__(self, reduction):
        self.reduction = reduction  # 减伤值
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        return f"Def(-{self.reduction})"


class ControlState:
    """控制状态（硬直、被控制、拉近、解除）"""
    def __init__(self, state_type, value=0, target=None):
        self.type = state_type      # 'stun', 'controlled', 'pull', 'release'
        self.value = value          # 持续帧数（stun）
        self.target = target        # 目标位置（pull）或控制者名字（controlled）
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        if self.type == 'stun':
            return f"Stun({self.value}帧)"
        elif self.type == 'controlled':
            return f"Ctrl(by {self.target})"
        elif self.type == 'pull':
            return f"Pull(to {self.target})"
        elif self.type == 'release':
            return "Release"
        return f"Ctrl({self.type})"


class BuffState:
    """Buff变化状态"""
    def __init__(self, buff_type, action, value=0):
        self.type = buff_type       # 'charge', 'dash', 'grab_damage'
        self.action = action        # 'gain', 'consume', 'lose'
        self.value = value          # 等级/层数/值
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        return f"Buff({self.type}:{self.action}={self.value})"


class MarkerState:
    """标记状态（帧内事件标记）"""
    def __init__(self, marker_type):
        self.type = marker_type     # 'tried_attack', 'dealt_damage', 'took_damage', 'used_charge_2', 'prepare_counter'
        self.cancelled = False      # 是否被取消
    
    def __repr__(self):
        return f"Mark({self.type})"