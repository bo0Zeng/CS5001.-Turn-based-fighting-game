"""
game_ui_mobile.py
移动端触屏适配版 / Mobile Touch-Optimized Version

适配特性 / Features:
1. 横屏分辨率适配 (2100x948 和 2400x1080)
2. 触摸按钮代替键盘
3. 手势支持：滑动、长按、双击
4. 移动端优化布局
"""

import pygame
import sys
import io
from player import Player
from combat_manager import CombatManager
from config import *
from game_data import ACTION_KEY_MAP, ACTION_DISPLAY_NAMES, KEY_HINTS, SKILL_DESCRIPTIONS, GAME_MECHANICS

# ========== 移动端配置 / Mobile Configuration ==========
MOBILE_WIDTH = 2100  # 横屏宽度
MOBILE_HEIGHT = 948  # 横屏高度

# 按钮配置
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 100
BUTTON_SPACING = 15
BUTTON_START_X = 50
BUTTON_START_Y = 650

# 网格配置（缩小以适应移动端）
MOBILE_GRID_START_X = 50
MOBILE_GRID_START_Y = 150
MOBILE_GRID_WIDTH = 800
MOBILE_CELL_WIDTH = MOBILE_GRID_WIDTH // MAP_SIZE
MOBILE_CELL_HEIGHT = 80
MOBILE_PLAYER_RADIUS = 25

# 日志框配置
MOBILE_LOG_X = 1100
MOBILE_LOG_Y = 50
MOBILE_LOG_WIDTH = 950
MOBILE_LOG_HEIGHT = 850

# 选择显示配置
MOBILE_SELECT_X = 50
MOBILE_SELECT_Y = 50

# 手势识别阈值
SWIPE_THRESHOLD = 100  # 滑动最小距离
LONG_PRESS_TIME = 500  # 长按时间(ms)
DOUBLE_TAP_TIME = 300  # 双击间隔(ms)


class TouchButton:
    """触摸按钮类"""
    def __init__(self, x, y, width, height, action, display_name, color=GRAY):
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.display_name = display_name
        self.color = color
        self.pressed = False
        self.long_press_start = 0
        
    def handle_touch(self, pos, event_type):
        """处理触摸事件"""
        if self.rect.collidepoint(pos):
            if event_type == 'down':
                self.pressed = True
                self.long_press_start = pygame.time.get_ticks()
                return None
            elif event_type == 'up':
                self.pressed = False
                # 检查是否是长按
                press_duration = pygame.time.get_ticks() - self.long_press_start
                if press_duration < LONG_PRESS_TIME:
                    return ('click', self.action)
                else:
                    return ('long_press', self.action)
        return None
    
    def draw(self, screen, font, is_disabled=False):
        """绘制按钮"""
        color = DARK_GRAY if is_disabled else (YELLOW if self.pressed else self.color)
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 3, border_radius=10)
        
        # 绘制文字（支持换行）
        lines = self.display_name.split('\n')
        total_height = len(lines) * 30
        start_y = self.rect.centery - total_height // 2
        
        for i, line in enumerate(lines):
            text = font.render(line, True, WHITE if not is_disabled else GRAY)
            text_rect = text.get_rect(center=(self.rect.centerx, start_y + i * 30))
            screen.blit(text, text_rect)


class MobileGameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((MOBILE_WIDTH, MOBILE_HEIGHT))
        pygame.display.set_caption("Battle Game Mobile")
        self.clock = pygame.time.Clock()

        self.font = self._load_font(36)
        self.small_font = self._load_font(28)
        self.large_font = self._load_font(56)
        self.tiny_font = self._load_font(24)

        # 游戏状态
        self.game_phase = "menu"
        self.game_state = "input"
        
        # 玩家对象
        self.player1 = None
        self.player2 = None
        self.combat = None
        
        # 输入相关
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1

        self.action_names = ACTION_DISPLAY_NAMES

        self.battle_messages = []
        
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.turn_delay_timer = 0
        self.p1_final_actions = []
        self.p2_final_actions = []
        
        # 日志相关
        self.viewing_turn = 0
        self.is_viewing_history = False
        self.simple_log_mode = False
        self.log_scroll_offset = 0
        self.log_max_lines = 35
        
        # 触摸相关
        self.touch_start_pos = None
        self.touch_start_time = 0
        self.last_tap_time = 0
        self.last_tap_pos = None
        self.showing_tooltip = False
        self.tooltip_action = None
        
        # 创建触摸按钮
        self.create_buttons()

    def _load_font(self, size):
        import os
        fonts = []
        if sys.platform == "win32":
            fonts = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]
        elif sys.platform == "darwin":
            fonts = ["/System/Library/Fonts/PingFang.ttc"]
        else:
            fonts = ["/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 
                    "/system/fonts/DroidSansFallback.ttf"]  # Android字体路径
        
        for f in fonts:
            if os.path.exists(f):
                try:
                    return pygame.font.Font(f, size)
                except:
                    pass
        return pygame.font.Font(None, size)

    def create_buttons(self):
        """创建技能按钮"""
        actions = [
            ('attack', 'J\n攻击\nAttack', RED),
            ('charge', 'I\n蓄力\nCharge', PURPLE),
            ('control', 'K\n控制\nControl', ORANGE),
            ('grab', '1\n抱摔\nGrab', ORANGE),
            ('throw', '2\n投掷\nThrow', ORANGE),
            ('defend', 'S\n防御\nDefend', GREEN),
            ('counter', 'W\n反击\nCounter', GREEN),
            ('move_left', 'A\n左移\nLeft', BLUE),
            ('move_right', 'D\n右移\nRight', BLUE),
            ('dash_left', 'Q\n左冲\nDashL', BLUE),
            ('dash_right', 'E\n右冲\nDashR', BLUE),
            ('burst', 'O\n爆血\nBurst', (255, 100, 0)),
        ]
        
        self.buttons = []
        x = BUTTON_START_X
        y = BUTTON_START_Y
        
        for i, (action, name, color) in enumerate(actions):
            button = TouchButton(x, y, BUTTON_WIDTH, BUTTON_HEIGHT, action, name, color)
            self.buttons.append(button)
            
            x += BUTTON_WIDTH + BUTTON_SPACING
            if (i + 1) % 6 == 0:  # 每行6个按钮
                x = BUTTON_START_X
                y += BUTTON_HEIGHT + BUTTON_SPACING

    def init_game(self):
        """初始化游戏对象"""
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.reset_turn()
        self.battle_messages = []

    # ========== 手势识别 / Gesture Recognition ==========
    
    def handle_touch_down(self, pos):
        """处理触摸开始"""
        self.touch_start_pos = pos
        self.touch_start_time = pygame.time.get_ticks()
        
        # 检查双击
        current_time = pygame.time.get_ticks()
        if self.last_tap_time and current_time - self.last_tap_time < DOUBLE_TAP_TIME:
            if self.last_tap_pos and self._distance(pos, self.last_tap_pos) < 50:
                self.handle_double_tap(pos)
                self.last_tap_time = 0
                return
        
        self.last_tap_time = current_time
        self.last_tap_pos = pos
        
        # 处理按钮按下
        for button in self.buttons:
            button.handle_touch(pos, 'down')
    
    def handle_touch_up(self, pos):
        """处理触摸结束"""
        if self.touch_start_pos:
            # 检查是否是滑动
            dx = pos[0] - self.touch_start_pos[0]
            dy = pos[1] - self.touch_start_pos[1]
            
            if abs(dx) > SWIPE_THRESHOLD or abs(dy) > SWIPE_THRESHOLD:
                self.handle_swipe(dx, dy)
            else:
                # 检查按钮点击
                for button in self.buttons:
                    result = button.handle_touch(pos, 'up')
                    if result:
                        event_type, action = result
                        if event_type == 'click':
                            self.handle_button_click(action)
                        elif event_type == 'long_press':
                            self.handle_button_long_press(action)
        
        self.touch_start_pos = None
    
    def handle_swipe(self, dx, dy):
        """处理滑动手势"""
        if abs(dy) > abs(dx):
            # 垂直滑动 - 滚动日志
            if dy > 0:
                self.log_scroll_offset = max(0, self.log_scroll_offset - 3)
            else:
                self.log_scroll_offset += 3
        else:
            # 水平滑动 - 浏览历史
            if dx > 0:
                self._navigate_history('left')
            else:
                self._navigate_history('right')
    
    def handle_double_tap(self, pos):
        """处理双击 - 取消已选动作"""
        if self.game_state != "input":
            return
        
        actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        locked = self.p1_locked if self.current_player == 1 else self.p2_locked
        
        if not locked and actions:
            removed = actions.pop()
            name = PLAYER1_NAME if self.current_player == 1 else PLAYER2_NAME
            print(f"{name}撤销: {self.action_names.get(removed, '???')}")
    
    def handle_button_click(self, action):
        """处理按钮点击"""
        if self.game_state != "input":
            return
        
        player = self.player1 if self.current_player == 1 else self.player2
        actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        locked = self.p1_locked if self.current_player == 1 else self.p2_locked
        name = PLAYER1_NAME if self.current_player == 1 else PLAYER2_NAME
        
        if not locked:
            self._add_action(player, actions, action, name)
    
    def handle_button_long_press(self, action):
        """处理按钮长按 - 显示技能说明"""
        self.showing_tooltip = True
        self.tooltip_action = action
    
    def _distance(self, pos1, pos2):
        """计算两点距离"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

    # ========== 日志相关 / Log Related ==========
    
    def _extract_simple_log(self, messages):
        """提取简洁日志"""
        simple = []
        turn_info = None
        current_frame = None
        frame_data = {1: {'p1': None, 'p2': None}, 2: {'p1': None, 'p2': None}}
        
        for msg in messages:
            msg_clean = msg.strip()
            if not msg_clean or '=' in msg:
                continue
            
            if "回合" in msg and "距离:" in msg:
                turn_info = msg_clean
                continue
            
            if "--- 第" in msg and "帧" in msg:
                if "第 1 帧" in msg:
                    current_frame = 1
                elif "第 2 帧" in msg:
                    current_frame = 2
                continue
            
            if current_frame is None:
                continue
            
            self._parse_frame_message(msg_clean, frame_data[current_frame])
        
        if turn_info:
            simple.append(turn_info)
            simple.append("")
        
        for frame_num in [1, 2]:
            if frame_data[frame_num]['p1'] or frame_data[frame_num]['p2']:
                simple.append(f"帧{frame_num} / Frame {frame_num}")
                
                if frame_data[frame_num]['p1']:
                    simple.append(f"  {PLAYER1_NAME}: {frame_data[frame_num]['p1']}")
                if frame_data[frame_num]['p2']:
                    simple.append(f"  {PLAYER2_NAME}: {frame_data[frame_num]['p2']}")
                
                simple.append("")
        
        return simple if simple else ["(无信息) / (No information)"]
    
    def _parse_frame_message(self, msg, frame_data):
        """解析帧消息"""
        p1_name = PLAYER1_NAME
        p2_name = PLAYER2_NAME
        
        if msg.startswith('[P') and ']' in msg:
            return
        
        # 简化的解析逻辑
        if "攻击命中" in msg:
            if p1_name in msg:
                frame_data['p1'] = "攻击命中"
            if p2_name in msg:
                frame_data['p2'] = "攻击命中"
        elif "控制成功" in msg:
            if p1_name in msg:
                frame_data['p1'] = "控制成功"
            if p2_name in msg:
                frame_data['p2'] = "控制成功"
        elif "爆血" in msg:
            if p1_name in msg:
                frame_data['p1'] = "爆血"
            if p2_name in msg:
                frame_data['p2'] = "爆血"

    # ========== 绘制方法 / Drawing Methods ==========
    
    def draw_menu(self):
        """绘制主菜单"""
        self.screen.fill(WHITE)
        
        title = self.large_font.render("回合制战斗游戏", True, BLACK)
        title_en = self.font.render("Turn-Based Battle Game", True, DARK_GRAY)
        title_rect = title.get_rect(center=(MOBILE_WIDTH//2, 150))
        title_en_rect = title_en.get_rect(center=(MOBILE_WIDTH//2, 220))
        self.screen.blit(title, title_rect)
        self.screen.blit(title_en, title_en_rect)
        
        # 开始按钮
        start_button = pygame.Rect(MOBILE_WIDTH//2 - 250, 400, 500, 120)
        pygame.draw.rect(self.screen, GREEN, start_button, border_radius=20)
        pygame.draw.rect(self.screen, BLACK, start_button, 5, border_radius=20)
        
        start_text = self.font.render("开始游戏 / Start Game", True, WHITE)
        start_rect = start_text.get_rect(center=start_button.center)
        self.screen.blit(start_text, start_rect)
        
        # 检测触摸
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if start_button.collidepoint(pos):
                self.init_game()
                self.game_phase = "game"
    
    def draw_game(self):
        """绘制游戏界面"""
        self.screen.fill(WHITE)
        
        # 绘制标题
        self.draw_header()
        
        # 绘制网格
        self.draw_grid()
        
        # 绘制玩家
        self.draw_player(self.player1, PLAYER1_COLOR)
        self.draw_player(self.player2, PLAYER2_COLOR)
        
        # 绘制日志
        self.draw_messages()
        
        if self.game_state == "input":
            # 绘制按钮
            self.draw_buttons()
            
            # 绘制选择显示
            self.draw_selection()
        
        # 绘制工具提示
        if self.showing_tooltip and self.tooltip_action:
            self.draw_tooltip()
        
        if self.game_state == "game_over":
            self.draw_game_over()
    
    def draw_header(self):
        """绘制标题"""
        text = f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格"
        text_surface = self.large_font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=(MOBILE_WIDTH//2, 30))
        self.screen.blit(text_surface, text_rect)
        
        if self.game_state == "frame_executing":
            exec_text = f"执行第 {self.current_frame_index + 1} 帧"
            exec_surface = self.font.render(exec_text, True, ORANGE)
            exec_rect = exec_surface.get_rect(center=(MOBILE_WIDTH//2, 80))
            self.screen.blit(exec_surface, exec_rect)
    
    def draw_grid(self):
        """绘制网格"""
        for i in range(MAP_SIZE):
            x = MOBILE_GRID_START_X + i * MOBILE_CELL_WIDTH
            y = MOBILE_GRID_START_Y
            pygame.draw.rect(self.screen, GRAY, (x, y, MOBILE_CELL_WIDTH, MOBILE_CELL_HEIGHT), 2)
            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            self.screen.blit(text, (x + MOBILE_CELL_WIDTH//2 - 10, y + 10))
    
    def draw_player(self, player, color):
        """绘制玩家"""
        x = MOBILE_GRID_START_X + (player.position - 1) * MOBILE_CELL_WIDTH + MOBILE_CELL_WIDTH // 2
        y = MOBILE_GRID_START_Y + MOBILE_CELL_HEIGHT // 2
        
        pygame.draw.circle(self.screen, color, (x, y), MOBILE_PLAYER_RADIUS)
        
        if player.controlled:
            pygame.draw.circle(self.screen, YELLOW, (x, y), MOBILE_PLAYER_RADIUS + 5, 3)
        
        if player.charge_level > 0:
            c = YELLOW if player.charge_level == 1 else ORANGE
            pygame.draw.circle(self.screen, c, (x, y), MOBILE_PLAYER_RADIUS + 8, 2)
        
        # 玩家名字
        text = self.small_font.render(player.name, True, BLACK)
        self.screen.blit(text, (x - 30, y - 50))
        
        # 血条
        hp_ratio = player.hp / player.max_hp
        hp_w = int(80 * hp_ratio)
        hp_color = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
        pygame.draw.rect(self.screen, DARK_GRAY, (x - 40, y + 40, 80, 10))
        pygame.draw.rect(self.screen, hp_color, (x - 40, y + 40, hp_w, 10))
        
        hp_text = self.tiny_font.render(f"{player.hp}/{player.max_hp}", True, BLACK)
        self.screen.blit(hp_text, (x - 30, y + 55))
    
    def draw_buttons(self):
        """绘制技能按钮"""
        player = self.player1 if self.current_player == 1 else self.player2
        
        for button in self.buttons:
            # 检查按钮是否应该禁用
            is_disabled = False
            if player.controlled and button.action not in ['defend', 'burst']:
                is_disabled = True
            
            button.draw(self.screen, self.small_font, is_disabled)
    
    def draw_selection(self):
        """绘制当前选择"""
        x, y = MOBILE_SELECT_X, MOBILE_SELECT_Y
        
        # P1显示
        p1_text = self._get_selection_text(1)
        p1_surface = self.font.render(p1_text, True, BLACK)
        bg_rect = pygame.Rect(x - 10, y - 5, 500, 50)
        pygame.draw.rect(self.screen, LIGHT_RED, bg_rect, border_radius=5)
        self.screen.blit(p1_surface, (x, y))
        
        # P2显示
        y += 60
        p2_text = self._get_selection_text(2)
        p2_surface = self.font.render(p2_text, True, BLACK)
        bg_rect = pygame.Rect(x - 10, y - 5, 500, 50)
        pygame.draw.rect(self.screen, LIGHT_BLUE, bg_rect, border_radius=5)
        self.screen.blit(p2_surface, (x, y))
        
        # 确认按钮
        confirm_button = pygame.Rect(x, y + 70, 200, 80)
        pygame.draw.rect(self.screen, ORANGE, confirm_button, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, confirm_button, 3, border_radius=10)
        confirm_text = self.font.render("确认", True, WHITE)
        confirm_rect = confirm_text.get_rect(center=confirm_button.center)
        self.screen.blit(confirm_text, confirm_rect)
        
        # 检测确认按钮点击
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if confirm_button.collidepoint(pos):
                self._confirm()
    
    def _get_selection_text(self, player_id):
        """获取选择文本"""
        actions = self.p1_actions if player_id == 1 else self.p2_actions
        locked = self.p1_locked if player_id == 1 else self.p2_locked
        name = PLAYER1_NAME if player_id == 1 else PLAYER2_NAME
        
        if locked:
            return f"{name}: [已确认]"
        elif len(actions) >= 2:
            a1 = self.action_names.get(actions[0], '???')
            a2 = self.action_names.get(actions[1], '???')
            return f"{name}: [{a1}] [{a2}]"
        elif len(actions) == 1:
            a1 = self.action_names.get(actions[0], '???')
            return f"{name}: [{a1}] [____]"
        else:
            return f"{name}: [____] [____]"
    
    def draw_messages(self):
        """绘制战斗日志"""
        pygame.draw.rect(self.screen, LIGHT_GRAY, (MOBILE_LOG_X, MOBILE_LOG_Y, MOBILE_LOG_WIDTH, MOBILE_LOG_HEIGHT), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, (MOBILE_LOG_X, MOBILE_LOG_Y, MOBILE_LOG_WIDTH, MOBILE_LOG_HEIGHT), 3, border_radius=10)
        
        title_text = "战斗日志"
        if self.simple_log_mode:
            title_text += " (简洁)"
        
        self.screen.blit(self.font.render(title_text, True, BLACK), (MOBILE_LOG_X + 20, MOBILE_LOG_Y + 20))
        
        # 切换按钮
        toggle_button = pygame.Rect(MOBILE_LOG_X + MOBILE_LOG_WIDTH - 150, MOBILE_LOG_Y + 20, 130, 50)
        pygame.draw.rect(self.screen, BLUE, toggle_button, border_radius=5)
        toggle_text = self.tiny_font.render("切换", True, WHITE)
        toggle_rect = toggle_text.get_rect(center=toggle_button.center)
        self.screen.blit(toggle_text, toggle_rect)
        
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if toggle_button.collidepoint(pos):
                self.simple_log_mode = not self.simple_log_mode
        
        messages = self.battle_messages
        if self.simple_log_mode:
            messages = self._extract_simple_log(messages)
        
        # 显示消息
        y = MOBILE_LOG_Y + 90
        start_line = self.log_scroll_offset
        
        for i, msg in enumerate(messages[start_line:start_line + self.log_max_lines]):
            text_surface = self.tiny_font.render(msg, True, BLACK)
            self.screen.blit(text_surface, (MOBILE_LOG_X + 20, y))
            y += 24
    
    def draw_tooltip(self):
        """绘制技能说明"""
        if self.tooltip_action not in SKILL_DESCRIPTIONS:
            return
        
        info = SKILL_DESCRIPTIONS[self.tooltip_action]
        
        # 半透明背景
        overlay = pygame.Surface((MOBILE_WIDTH, MOBILE_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 技能说明框
        box_width = 900
        box_height = 600
        box_x = (MOBILE_WIDTH - box_width) // 2
        box_y = (MOBILE_HEIGHT - box_height) // 2
        
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), border_radius=20)
        pygame.draw.rect(self.screen, BLACK, (box_x, box_y, box_width, box_height), 5, border_radius=20)
        
        # 标题
        title_lines = info['name'].split('\n')
        y = box_y + 30
        for line in title_lines:
            text = self.font.render(line, True, BLUE)
            text_rect = text.get_rect(center=(MOBILE_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50
        
        # 说明
        y += 20
        for line in info['desc']:
            if line:
                text = self.tiny_font.render(line, True, BLACK)
                self.screen.blit(text, (box_x + 40, y))
            y += 30
    
    def draw_game_over(self):
        """绘制游戏结束"""
        overlay = pygame.Surface((MOBILE_WIDTH, MOBILE_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        winner = self.combat.get_winner()
        text = "平局！" if winner == "平局 / Draw" else f"{winner} 获胜！"
        
        text_surface = self.large_font.render(text, True, YELLOW)
        text_rect = text_surface.get_rect(center=(MOBILE_WIDTH // 2, MOBILE_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    # ========== 游戏逻辑 / Game Logic ==========
    
    def _add_action(self, player, actions, action, name):
        """添加行动"""
        next_turn = self.combat.turn + 1
        
        for i in range(2):
            if i < len(actions):
                continue
            
            locked = player.is_frame_locked(next_turn, i+1)
            
            if locked:
                if action == 'burst':
                    while len(actions) < i:
                        actions.append(None)
                    actions.append(action)
                    print(f"{name}选择第{i+1}帧(硬直): Burst")
                    return
                else:
                    continue
            
            while len(actions) < i:
                actions.append(None)
            
            actions.append(action)
            print(f"{name}选择第{i+1}帧: {self.action_names[action]}")
            return
    
    def _confirm(self):
        """确认选择"""
        if self.current_player == 1 and not self.p1_locked:
            if len(self.p1_actions) >= 2:
                self.p1_locked = True
                self.current_player = 2
                print("P1已确认")
        elif self.current_player == 2 and not self.p2_locked:
            if len(self.p2_actions) >= 2:
                self.p2_locked = True
                print("P2已确认")
                if self.p1_locked:
                    self.start_execution()
    
    def start_execution(self):
        """开始执行"""
        self.game_state = "frame_executing"
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.p1_final_actions = self.p1_actions[:]
        self.p2_final_actions = self.p2_actions[:]
    
    def execute_frame(self):
        """执行帧"""
        # 简化版执行逻辑
        pass
    
    def reset_turn(self):
        """重置回合"""
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"
    
    def _navigate_history(self, direction):
        """浏览历史"""
        if len(self.combat.turn_logs) == 0:
            return
        
        if direction == 'left':
            if self.viewing_turn == 0:
                self.viewing_turn = self.combat.turn
            elif self.viewing_turn > 1:
                self.viewing_turn -= 1
        elif direction == 'right':
            if self.viewing_turn < self.combat.turn:
                self.viewing_turn += 1
            if self.viewing_turn == self.combat.turn:
                self.viewing_turn = 0

    # ========== 主循环 / Main Loop ==========
    
    def run(self):
        """主循环"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_touch_down(event.pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_touch_up(event.pos)
                    # 关闭工具提示
                    self.showing_tooltip = False
            
            # 绘制
            if self.game_phase == "menu":
                self.draw_menu()
            else:
                self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()


def main():
    """启动移动端游戏"""
    game = MobileGameUI()
    game.run()


if __name__ == "__main__":
    main()