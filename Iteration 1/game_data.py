"""
game_data.py
游戏数据 - 按键映射和UI文本 / Game Data - Key Mapping and UI Text
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
    ("J - 攻击\nAttack", 'attack'),
    ("I - 蓄力\nCharge", 'charge'),
    ("K - 控制\nControl", 'control'),
    ("1 - 抱摔  2 - 投掷\nGrab Throw", 'control'),
    ("S - 防御\nDefend", 'defend'),
    ("W - 反击\nCounter", 'counter'),
    ("A - 左移  D - 右移\nMove", 'move'),
    ("Q - 左冲  E - 右冲\nDash", 'dash'),
    ("O - 爆血\nBurst", 'burst'),
]

SKILL_DESCRIPTIONS = {
    'attack': {
        'name': '攻击 (J)\nAttack (J)',
        'desc': [
            '伤害1，距离1格\nDamage 1, Range 1',
            '',
            '蓄力加成：\nCharge Bonus:',
            '蓄力1：+1伤害+1距离\nCharge1: +1 Damage +1 Range',
            '蓄力2：+3伤害+1距离+硬直\nCharge2: +3 Damage +1 Range + Stun',
            '',
            '冲刺加成：有buff时+层数伤害\nDash Bonus: +Stack Damage with buff',
            '造成伤害后消耗1层buff\nConsumes 1 stack after dealing damage'
        ]
    },
    'charge': {
        'name': '蓄力 (I)\nCharge (I)',
        'desc': [
            '蓄力1：下次攻击+1伤害+1距离\nCharge1: Next attack +1 Damage +1 Range',
            '',
            '连续2次→蓄力2：\n2 consecutive charges → Charge2:',
            '蓄力2：下次攻击+3伤害+1距离+硬直\nCharge2: Next attack +3 Damage +1 Range + Stun',
            '',
            '被控制/打断：失去蓄力 + 此帧受伤+1\nControlled/Interrupted: Lose charge + Take +1 damage this frame',
        ]
    },
    'control': {
        'name': '控制 (K) + 摔投(1/2)\nControl (K) + Throw(1/2)',
        'desc': [
            '控制：距离1格\nControl: Range 1',
            '失败→自己硬直1帧\nFail → Self stun 1 frame',
            '',
            '成功：拉近(距离→0)\nSuccess: Pull closer (distance→0)',
            '对手只能用S或O\nOpponent can only use S or O',
            '',
            '控制后可用：\nAvailable after control:',
            '抱摔(1)：4伤\nGrab(1): 4 damage',
            '投掷(2)：2伤+对手退3格\nThrow(2): 2 damage + Opponent moves back 3 spaces'
        ]
    },
    'defend': {
        'name': '防御 (S)\nDefend (S)',
        'desc': [
            '本帧受伤-1\nDamage -1 this frame',
            '',
            '被控制时可用\nAvailable when controlled'
        ]
    },
    'counter': {
        'name': '反击 (W)\nCounter (W)',
        'desc': [
            '受伤-1\nDamage -1',
            '',
            '成功：对手攻击时反2伤\nSuccess: Counter 2 damage when attacked',
            '失败：未被攻击硬直1帧\nFail: Stun 1 frame if not attacked'
        ]
    },
    'move': {
        'name': '移动 (A/D)\nMove (A/D)',
        'desc': [
            'A-左移1格 D-右移1格\nA-Left 1 space D-Right 1 space',
            '闪避：对手攻击时移动\nDodge: Move when opponent attacks',
            '脱离范围→对手硬直1帧\nOut of range → Opponent stun 1 frame'
        ]
    },
    'dash': {
        'name': '冲刺 (Q/E)\nDash (Q/E)',
        'desc': [
            'Q-左冲2格 E-右冲2格\nQ-Left dash 2 spaces E-Right dash 2 spaces',
            '',
            '成功≥1格→获1层buff(最多2层)\nSuccess ≥1 space → Gain 1 stack (max 2)',
            '',
            'buff效果：\nBuff effect:',
            '攻击时伤害+层数，消耗1层\nAttack: +Stack damage, consume 1 stack',
            '受伤时伤害+层数，消耗1层\nTake damage: +Stack damage, consume 1 stack'
        ]
    },
    'burst': {
        'name': '爆血 (O)\nBurst (O)',
        'desc': [
            '消耗1帧\nConsumes 1 frame',
            '任何情况可用(含硬直/控制)\nAvailable in any state (including stun/control)',
            '',
            '伤害基于结算后距离：\nDamage based on final distance:',
            '自损：3+距离\nSelf damage: 3 + distance',
            '敌伤：6-距离\nEnemy damage: 6 - distance',
            '',
            '示例：\nExample:',
            '距离0：自损3，敌伤6\nDistance 0: Self 3, Enemy 6',
            '距离3：自损6，敌伤3\nDistance 3: Self 6, Enemy 3',
            '距离6：自损9，敌伤0\nDistance 6: Self 9, Enemy 0',
            '',
            '注意：考虑投掷等位移\nNote: Consider throws and other movement'
        ]
    }
}

GAME_MECHANICS = {
    'combo': {
        'name': '连击机制\nCombo System',
        'desc': [
            '连续3帧造成伤害→硬直1帧\n3 consecutive damage frames → Stun 1 frame',
            '必须连续，不能断\nMust be consecutive, cannot break',
            '未被击中时清零\nReset when not hit',
            '',
            '任何伤害都算：\nAny damage counts:',
            '攻击/爆血/反击等\nAttack/Burst/Counter etc.'
        ]
    },
    'stun': {
        'name': '硬直机制\nStun System',
        'desc': [
            '硬直时只能用爆血(O)\nCan only use Burst (O) when stunned',
            '',
            '触发：\nTriggers:',
            '- 连击3次\n- 3-hit combo',
            '- 蓄力2命中\n- Charge2 hit',
            '- 控制失败\n- Control miss',
            '- 反击失败\n- Counter fail',
            '- 被闪避\n- Dodged'
        ]
    },
}