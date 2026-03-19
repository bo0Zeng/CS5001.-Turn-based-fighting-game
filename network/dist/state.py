"""
state.py
状态系统 - 纯数据结构定义（重构版）
State System - Pure Data Structure Definitions (Refactored)

"""


class PositionState:
    """位置变化状态 / Position Change State"""
    def __init__(self, delta, source="self"):
        self.delta = delta          # 位置变化量（+1/-1） / Position change amount (+1/-1)
        self.source = source        # 来源："self" 或 玩家名字 / Source: "self" or player name
    
    def __repr__(self):
        return f"Pos({self.delta:+d}, from={self.source})"


class DamageState:
    """伤害状态 / Damage State"""
    def __init__(self, amount, source=""):
        self.amount = amount        # 伤害值 / Damage value
        self.source = source        # 伤害来源 / Damage source
    
    def __repr__(self):
        return f"Dmg({self.amount})"


class DefenseState:
    """防御状态 / Defense State"""
    def __init__(self, reduction):
        self.reduction = reduction  # 减伤值 / Damage reduction value
    
    def __repr__(self):
        return f"Def(-{self.reduction})"


class ControlState:
    """控制状态（硬直、被控制、拉近、解除） / Control State (Stun, Controlled, Pull, Release)"""
    def __init__(self, state_type, value=0, target=None):
        self.type = state_type      # 'stun', 'controlled', 'pull', 'release'
        self.value = value          # 持续帧数（stun） / Duration in frames (stun)
        self.target = target        # 目标位置（pull）或控制者名字（controlled） / Target position (pull) or controller name (controlled)
    
    def __repr__(self):
        if self.type == 'stun':
            return f"Stun({self.value}帧) / Stun({self.value} frames)"
        elif self.type == 'controlled':
            return f"Ctrl(by {self.target})"
        elif self.type == 'pull':
            return f"Pull(to {self.target})"
        elif self.type == 'release':
            return "Release"
        return f"Ctrl({self.type})"


class BuffState:
    """Buff变化状态 / Buff Change State"""
    def __init__(self, buff_type, action, value=0):
        self.type = buff_type       # 'charge', 'dash'
        self.action = action        # 'gain', 'consume', 'lose', 'pending'
        self.value = value          # 等级/层数/值 / Level/layers/value
    
    def __repr__(self):
        return f"Buff({self.type}:{self.action}={self.value})"


class ActionState:
    """行动状态（帧内事件标记，原MarkerState）/ Action State (In-frame Event Markers)"""
    def __init__(self, action_type, value=0):
        self.type = action_type     # 'do_attack', 'do_control', 'do_burst', 'be_attacked', 'be_controlled', etc.
        self.value = value          # 附加值（如攻击范围、伤害等） / Additional value (e.g., attack range, damage)
    
    def __repr__(self):
        return f"Action({self.type}, val={self.value})"