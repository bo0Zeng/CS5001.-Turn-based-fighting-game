"""
config.py
游戏配置文件 - 存储所有常量和配置
"""

# ==================== 游戏基础设置 ====================
MAP_SIZE = 6           # 地图大小
MIN_DISTANCE = 1       # 最小距离
MAX_DISTANCE = 6       # 最大距离

# ==================== 玩家配置 ====================
PLAYER_MAX_HP = 20     # 玩家初始生命值

# 玩家1配置
PLAYER1_NAME = input("请输入玩家1姓名: ") or "Alice"
PLAYER1_START_POS = 2
PLAYER1_COLOR = (255, 50, 50)  # RED

# 玩家2配置
PLAYER2_NAME = input("请输入玩家2姓名: ") or "Bob"
PLAYER2_START_POS = 5
PLAYER2_COLOR = (50, 50, 255)  # BLUE

# ==================== 招式伤害配置 ====================
ATTACK_DAMAGE = 1          # 普通攻击伤害
ATTACK_RANGE = 1           # 普通攻击距离

CHARGE_1_DAMAGE_BONUS = 1  # 蓄力1伤害加成
CHARGE_1_RANGE_BONUS = 1   # 蓄力1距离加成
CHARGE_2_DAMAGE_BONUS = 3  # 蓄力2伤害加成
CHARGE_2_RANGE_BONUS = 1   # 蓄力2距离加成

GRAB_DAMAGE = 4            # 抱摔伤害
THROW_DAMAGE = 2           # 投掷伤害
THROW_DISTANCE = 3         # 投掷击退距离

COUNTER_DAMAGE = 1         # 防御反击伤害
DEFEND_REDUCTION = 1       # 防御减伤

BURST_SELF_DAMAGE = 3      # 爆血自损
BURST_BASE_DAMAGE = 6      # 爆血基础伤害
BURST_MISS_DAMAGE = 6      # 爆血未击中自损（已废弃，爆血无距离限制）
BURST_RANGE = 999          # 爆血距离（无限制）
BURST_KNOCKBACK = 2        # 爆血击退距离

DASH_DAMAGE_MODIFIER = 1   # 快速移动伤害修正

# ==================== 状态效果配置 ====================
# 蓄力惩罚
CHARGE_CONTROLLED_DAMAGE = 1   # 蓄力时被控制额外伤害
CHARGE_INTERRUPTED_DAMAGE = 1  # 蓄力时被打断额外伤害

# 控制配置
CONTROL_RANGE = 1              # 控制距离

# ==================== 硬直配置 ====================
COMBO_THRESHOLD = 3            # 连击触发阈值（必须连续）
COMBO_STUN_FRAMES = 1          # 连击触发硬直帧数
CHARGE_2_STUN_FRAMES = 1       # 蓄力2攻击造成的硬直
CONTROL_MISS_STUN_FRAMES = 1   # 控制未命中自己硬直
COUNTER_FAIL_STUN_FRAMES = 1   # 防御反击失败硬直
DODGE_STUN_FRAMES = 1          # 闪避成功造成对手硬直

# ==================== UI配置 ====================
# 窗口设置
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# 颜色定义
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

# 布局设置
GRID_START_X = 50
GRID_START_Y = 200
GRID_WIDTH = 600
CELL_WIDTH = GRID_WIDTH // MAP_SIZE
CELL_HEIGHT = 100
PLAYER_RADIUS = 30

# 血条设置
HP_BAR_WIDTH = 80
HP_BAR_HEIGHT = 8
HP_BAR_OFFSET_Y = -45

# 连击数显示设置
COMBO_DISPLAY_OFFSET_Y = -55

# 消息框设置
MESSAGE_BOX_X = 870
MESSAGE_BOX_Y = 150
MESSAGE_BOX_WIDTH = 310
MESSAGE_BOX_HEIGHT = 600

# ==================== 游戏玩法配置 ====================
FRAME_DELAY = 60               # 每帧执行后的延迟（60帧=1秒）
EXECUTE_DELAY_FRAMES = 90      # 回合执行后的延迟帧数
MAX_TURNS = 30                 # 最大回合数

# 显示配置
SHOW_DETAILED_LOG = True
SEPARATOR = "=" * 60

# 调试模式
DEBUG_MODE = False

# ==================== UI文本配置 ====================
UI_TEXT = {
    'title': '回合制战斗游戏',
    'turn_info': '回合 {turn} | 距离: {distance}格',
    'frame_info': '第 {frame} 帧执行中...',
    'battle_log_title': '战斗日志',
    'current_selection': '当前选择',
    'key_hints_title': '按键说明',
    
    # 状态提示
    'alice_turn': 'Alice 第{frame}帧',
    'bob_turn': 'Bob 第{frame}帧',
    'selection_complete': '✓ 已选完，按 SPACE 确认',
    'waiting_bob': '等待Bob确认...',
    'waiting_alice': '等待Alice确认...',
    'both_confirmed': '双方已确认！执行回合...',
    'executing': '⏳ 回合执行中...',
    
    # 硬直相关提示
    'frame_locked': '🔒 第{frame}帧被硬直锁定',
    'controlled_limit': '⛓️ 被控制，只能使用S(防御)或O(爆血)',
    
    # 警告提示
    'alice_needs_more': '⚠ Alice还需要选择 {count} 个行动',
    'bob_needs_more': '⚠ Bob还需要选择 {count} 个行动',
    'alice_undo': '↩️ Alice撤销: {action}',
    'bob_undo': '↩️ Bob撤销: {action}',
    'no_undo': '⚠ {player}没有可撤销的动作',
    'already_selected': '⚠ {player}已选择2个行动，请按空格确认',
    
    # 游戏结束
    'game_over_draw': '平局！',
    'game_over_win': '{winner} 获胜！',
    'restart_hint': '按 R 重新开始 | 按 ESC 退出',
    
    # 其他提示
    'turn_based_hint': 'Alice和Bob轮流输入'
}