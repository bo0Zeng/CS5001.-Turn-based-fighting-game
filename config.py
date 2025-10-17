"""
config.py
游戏配置文件 - 所有常量和配置
"""

# ==================== 游戏基础设置 ====================
MAP_SIZE = 6
MIN_DISTANCE = 0
MAX_DISTANCE = 6

# ==================== 玩家配置 ====================
PLAYER_MAX_HP = 20

PLAYER1_NAME = "Red"
PLAYER1_START_POS = 2
PLAYER1_COLOR = (255, 50, 50)

PLAYER2_NAME = "Blue"
PLAYER2_START_POS = 5
PLAYER2_COLOR = (50, 50, 255)

# ==================== 招式配置 ====================
ATTACK_DAMAGE = 1
ATTACK_RANGE = 1

CHARGE_1_DAMAGE_BONUS = 1
CHARGE_1_RANGE_BONUS = 1
CHARGE_2_DAMAGE_BONUS = 3
CHARGE_2_RANGE_BONUS = 1

GRAB_DAMAGE = 4
GRAB_DAMAGE_BUFF = 2  # 抱摔时执行者受伤+2

THROW_DAMAGE = 2
THROW_DISTANCE = 3

COUNTER_DAMAGE = 1
DEFEND_REDUCTION = 1

BURST_SELF_DAMAGE = 3
BURST_BASE_DAMAGE = 6

CONTROL_RANGE = 1

# ==================== 状态配置 ====================
CHARGE_CONTROLLED_DAMAGE = 1
CHARGE_INTERRUPTED_DAMAGE = 1
DASH_MAX_STACKS = 2

# ==================== 硬直配置 ====================
COMBO_THRESHOLD = 3
COMBO_STUN_FRAMES = 1
CHARGE_2_STUN_FRAMES = 1
CONTROL_MISS_STUN_FRAMES = 1
COUNTER_FAIL_STUN_FRAMES = 1
DODGE_STUN_FRAMES = 1

# ==================== UI配置 ====================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
LIGHT_RED = (255, 200, 200)
LIGHT_BLUE = (200, 200, 255)
LIGHT_GRAY = (240, 240, 240)
ORANGE = (255, 165, 0)
PURPLE = (200, 100, 255)

GRID_START_X = 50
GRID_START_Y = 200
GRID_WIDTH = 600
CELL_WIDTH = GRID_WIDTH // MAP_SIZE
CELL_HEIGHT = 100
PLAYER_RADIUS = 30

HP_BAR_WIDTH = 80
HP_BAR_HEIGHT = 8
HP_BAR_OFFSET_Y = -45
COMBO_DISPLAY_OFFSET_Y = -55

MESSAGE_BOX_X = 870
MESSAGE_BOX_Y = 150
MESSAGE_BOX_WIDTH = 310
MESSAGE_BOX_HEIGHT = 600

# ==================== 游戏配置 ====================
FRAME_DELAY = 60
EXECUTE_DELAY_FRAMES = 90
MAX_TURNS = 30

SEPARATOR = "=" * 60

# ==================== UI文本 ====================
UI_TEXT = {
    'title': '回合制战斗游戏',
    'turn_info': '回合 {turn} | 距离: {distance}格',
    'battle_log_title': '战斗日志',
    'current_selection': '当前选择',
    'alice_turn': 'Alice 第{frame}帧',
    'bob_turn': 'Bob 第{frame}帧',
    'selection_complete': '✓ 已选完，按 SPACE 确认',
    'waiting_bob': '等待Bob确认...',
    'waiting_alice': '等待Alice确认...',
    'both_confirmed': '双方已确认！',
    'controlled_limit': '⛓️ 被控制，只能S或O',
    'alice_needs_more': '⚠ Alice还需要 {count} 个',
    'bob_needs_more': '⚠ Bob还需要 {count} 个',
    'alice_undo': '↩️ Alice撤销: {action}',
    'bob_undo': '↩️ Bob撤销: {action}',
    'no_undo': '⚠ {player}无可撤销',
    'already_selected': '⚠ {player}已选2个',
    'game_over_draw': '平局！',
    'game_over_win': '{winner} 获胜！',
    'restart_hint': '按 R 重新开始 | ESC 退出',
    'turn_based_hint': 'Alice和Bob轮流输入'
}