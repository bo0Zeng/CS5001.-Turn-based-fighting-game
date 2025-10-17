"""
game_data.py
游戏数据 - 按键映射和UI文本
"""

ACTION_KEY_MAP = {
    'j': 'attack', 'i': 'charge', 'k': 'control',
    '1': 'grab', '2': 'throw', 's': 'defend', 'w': 'counter',
    'a': 'move_left', 'd': 'move_right',
    'q': 'dash_left', 'e': 'dash_right', 'o': 'burst'
}

ACTION_DISPLAY_NAMES = {
    'attack': 'Attack', 'charge': 'Charge', 'control': 'Control',
    'grab': 'Grab', 'throw': 'Throw', 'defend': 'Defend', 'counter': 'Counter',
    'move_left': 'Left', 'move_right': 'Right',
    'dash_left': 'DashL', 'dash_right': 'DashR', 'burst': 'Burst'
}

KEY_HINTS = [
    ("J - 攻击", 'attack'),
    ("I - 蓄力", 'charge'),
    ("K - 控制", 'control'),
    ("1 - 抱摔  2 - 投掷", 'control'),
    ("S - 防御", 'defend'),
    ("W - 反击", 'counter'),
    ("A - 左移  D - 右移", 'move'),
    ("Q - 左冲  E - 右冲", 'dash'),
    ("O - 爆血", 'burst'),
]

SKILL_DESCRIPTIONS = {
    'attack': {
        'name': '攻击 (J)',
        'desc': [
            '消耗1帧，伤害1，距离1格',
            '',
            '蓄力加成：',
            '蓄力1：+1伤害+1距离',
            '蓄力2：+3伤害+1距离+硬直',
            '',
            '冲刺加成：有buff时+层数伤害',
            '造成伤害后消耗1层buff'
        ]
    },
    'charge': {
        'name': '蓄力 (I)',
        'desc': [
            '消耗1帧',
            '',
            '蓄力1：下次攻击+1伤害+1距离',
            '',
            '连续2次→蓄力2：',
            '下次攻击+3伤害+1距离+硬直',
            '',
            '被控制：失去蓄力+受伤+1',
            '被打断：失去蓄力+受伤+1'
        ]
    },
    'control': {
        'name': '控制 (K) + 摔投(1/2)',
        'desc': [
            '控制：距离1格',
            '失败→自己硬直1帧',
            '',
            '成功：拉近(距离→0)',
            '对手只能用S或O',
            '',
            '控制后：',
            '抱摔(1)：4伤+推开',
            '投掷(2)：2伤+退3格'
        ]
    },
    'defend': {
        'name': '防御 (S)',
        'desc': [
            '消耗1帧',
            '本帧受伤-1',
            '',
            '被控制/硬直时可用'
        ]
    },
    'counter': {
        'name': '反击 (W)',
        'desc': [
            '消耗1帧，受伤-1',
            '',
            '成功：对手攻击时反1伤',
            '失败：未被攻击硬直1帧'
        ]
    },
    'move': {
        'name': '移动 (A/D)',
        'desc': [
            'A-左移1格 D-右移1格',
            '',
            '移动优先执行',
            '然后防御，最后攻击',
            '',
            '闪避：对手攻击时移动',
            '脱离范围→对手硬直1帧'
        ]
    },
    'dash': {
        'name': '冲刺 (Q/E)',
        'desc': [
            'Q-左冲2格 E-右冲2格',
            '',
            '成功≥1格→获1层buff(最多2层)',
            '',
            'buff效果：',
            '攻击时伤害+层数，消耗1层',
            '受伤时伤害+层数，消耗1层'
        ]
    },
    'burst': {
        'name': '爆血 (O)',
        'desc': [
            '消耗1帧',
            '任何情况可用(含硬直/控制)',
            '',
            '自损：3+距离',
            '敌伤：6-距离',
            '',
            '示例：',
            '距离0：自损3，敌伤6',
            '距离3：自损6，敌伤3',
            '距离6：自损9，敌伤0',
            '',
            '解除自身控制/硬直'
        ]
    }
}

GAME_MECHANICS = {
    'combo': {
        'name': '连击机制',
        'desc': [
            '连续3帧造成伤害→硬直1帧',
            '必须连续，不能断',
            '未被击中时清零',
            '',
            '任何伤害都算：',
            '攻击/爆血/反击等'
        ]
    },
    'stun': {
        'name': '硬直机制',
        'desc': [
            '硬直时只能用爆血(O)',
            '',
            '触发：',
            '- 连击3次',
            '- 蓄力2命中',
            '- 控制失败',
            '- 反击失败',
            '- 被闪避'
        ]
    }
}