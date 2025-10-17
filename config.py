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

# ==================== 招式配置 ====================
PUNCH_DAMAGE = 1       # 拳伤害
PUNCH_RANGE = 1        # 拳距离
KICK_DAMAGE = 1        # 腿伤害
KICK_RANGE = 2         # 腿距离

# 控制链配置
GRAB_DAMAGE = 4        # 抱摔伤害
THROW_DAMAGE = 2       # 投掷伤害
THROW_DISTANCE = 2     # 投掷击退距离

# 防御配置
DEFEND_REDUCTION = 1   # 防御减伤

# 爆血配置
BURST_SELF_DAMAGE = 3      # 爆血自损
BURST_BASE_DAMAGE = 3      # 爆血基础伤害
BURST_MISS_DAMAGE = 6      # 爆血未击中自损
BURST_RANGE = 1            # 爆血距离

# 蓄力配置
CHARGE_FRAMES = 2          # 完整蓄力帧数
CHARGE_FULL_BONUS = 3      # 完整蓄力伤害加成
CHARGE_CANCEL_BONUS = 1    # 取消蓄力伤害加成
CHARGE_CANCEL_RISK = 2     # 取消蓄力风险窗口

# 连击配置
COMBO_THRESHOLD = 3        # 连击触发阈值
COMBO_STUN_FRAMES = 1      # 连击触发硬直帧数

# ==================== UI配置 ====================
# 窗口设置
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
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

# 布局设置
GRID_START_X = 50
GRID_START_Y = 150
GRID_WIDTH = 600
CELL_WIDTH = GRID_WIDTH // MAP_SIZE
CELL_HEIGHT = 80
PLAYER_RADIUS = 25

# 消息框设置
MESSAGE_BOX_X = 670
MESSAGE_BOX_Y = 150
MESSAGE_BOX_WIDTH = 410
MESSAGE_BOX_HEIGHT = 500

# ==================== 游戏玩法配置 ====================
EXECUTE_DELAY_FRAMES = 90  # 回合执行后的延迟帧数（90帧=1.5秒）
MAX_TURNS = 30             # 最大回合数（超时平局）

# 显示配置
SHOW_DETAILED_LOG = True   # 是否显示详细日志
SEPARATOR = "=" * 60       # 分隔符

# 调试模式
DEBUG_MODE = False         # 调试模式开关

# ==================== UI文本配置 ====================
UI_TEXT = {
    'title': '回合制战斗游戏',
    'turn_info': '回合 {turn} | 距离: {distance}格',
    'battle_log_title': '战斗日志',
    'current_selection': '当前选择',
    'key_hints_title': '按键说明',
    
    # 状态提示
    'alice_turn': 'Alice 第{frame}帧 (数字键1-9)',
    'bob_turn': 'Bob 第{frame}帧 (数字键1-9)',
    'selection_complete': '✓ 已选完，按 SPACE 确认',
    'waiting_bob': '等待Bob确认...',
    'waiting_alice': '等待Alice确认...',
    'both_confirmed': '双方已确认！执行回合...',
    'executing': '⏳ 回合执行中... ({time:.1f}s)',
    
    # 警告提示
    'alice_needs_more': '⚠ Alice还需要选择 {count} 个行动',
    'bob_needs_more': '⚠ Bob还需要选择 {count} 个行动',
    'invalid_key': '⚠ 无效按键（请使用数字键1-9）',
    'alice_undo': '↩️ Alice撤销: {action}',
    'bob_undo': '↩️ Bob撤销: {action}',
    'no_undo': '⚠ {player}没有可撤销的动作',
    'already_selected': '⚠ {player}已选择2个行动，请按空格确认',
    
    # 游戏结束
    'game_over_draw': '平局！',
    'game_over_win': '{winner} 获胜！',
    'restart_hint': '按 R 重新开始 | 按 ESC 退出',
    
    # 其他提示
    'use_english_input': '请使用英文输入法',
    'turn_based_hint': 'Alice和Bob轮流输入'
}