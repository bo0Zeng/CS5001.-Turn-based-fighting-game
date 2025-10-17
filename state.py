"""
state.py
状态系统 - 纯数据结构定义
"""


class PositionState:
    """位置变化状态"""
    def __init__(self, delta):
        self.delta = delta
        self.cancelled = False
    
    def __repr__(self):
        return f"Pos({self.delta:+d})"


class DamageState:
    """伤害状态"""
    def __init__(self, amount, source=""):
        self.amount = amount
        self.source = source
        self.cancelled = False
    
    def __repr__(self):
        return f"Dmg({self.amount})"


class DefenseState:
    """防御状态"""
    def __init__(self, reduction):
        self.reduction = reduction
        self.cancelled = False
    
    def __repr__(self):
        return f"Def(-{self.reduction})"