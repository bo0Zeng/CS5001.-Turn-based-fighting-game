

# ==================== 招式映射数据 ====================

# 按键 → 招式代码映射
ACTION_KEY_MAP = {
    '1': 'punch',
    '2': 'kick',
    '3': 'control',
    '4': 'grab',
    '5': 'throw',
    '6': 'defend',
    '7': 'move_forward',
    '8': 'move_back',
    '9': 'burst'
}

# 招式代码 → 显示名称（英文）
ACTION_DISPLAY_NAMES = {
    'punch': 'Punch',
    'kick': 'Kick',
    'control': 'Control',
    'grab': 'Grab',
    'throw': 'Throw',
    'defend': 'Defend',
    'move_forward': 'Forward',
    'move_back': 'Back',
    'burst': 'Burst'
}

# ==================== UI文本数据 ====================

# 按键提示文本（用于UI显示）
KEY_HINTS = [
    "1 2 3 - 拳 腿 控制",
    "4 5 6 - 摔 投 防御",
    "7 8 9 - 左 右 爆血",
    "然后按 SPACE 确认"
]

# 控制提示
CONTROL_HINTS = [
    "SPACE - 确认锁定",
    "Backspace - 撤销最后一个",
    "Delete - 清空重选"
]
