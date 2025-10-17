"""
game_ui.py
可视化界面 - 使用Pygame实现
只负责显示和交互，所有数据从配置文件导入
"""

import pygame
import sys
from player import Player
from combat_manager import CombatManager

# ==================== 从config导入所有配置 ====================
from config import (
    # 游戏配置
    MAP_SIZE, PLAYER_MAX_HP,
    PLAYER1_NAME, PLAYER1_START_POS, PLAYER1_COLOR,
    PLAYER2_NAME, PLAYER2_START_POS, PLAYER2_COLOR,
    
    # UI窗口配置
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    
    # 颜色配置
    WHITE, BLACK, RED, BLUE, GREEN, GRAY, DARK_GRAY, YELLOW,
    LIGHT_RED, LIGHT_BLUE, LIGHT_GRAY, ORANGE, PURPLE,
    
    # 布局配置
    GRID_START_X, GRID_START_Y, GRID_WIDTH, CELL_WIDTH, CELL_HEIGHT,
    PLAYER_RADIUS,
    
    # 消息框配置
    MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT,
    
    # 战斗配置
    EXECUTE_DELAY_FRAMES, COMBO_THRESHOLD,
    
    # UI文本
    UI_TEXT
)

# ==================== 从game_data导入游戏数据 ====================
from game_data import (
    ACTION_KEY_MAP,           # 按键映射
    ACTION_DISPLAY_NAMES,     # 招式显示名称
    KEY_HINTS,                # 按键提示文本
    CONTROL_HINTS             # 控制提示文本
)


class GameUI:
    """游戏可视化界面 - 只负责显示和交互"""

    def __init__(self):
        """初始化界面"""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(UI_TEXT['title'])
        self.clock = pygame.time.Clock()

        # 加载中文字体
        self.font = self._load_chinese_font(32)
        self.small_font = self._load_chinese_font(24)
        self.large_font = self._load_chinese_font(48)
        self.tiny_font = self._load_chinese_font(18)

        # 游戏状态 - 从配置创建玩家
        self.player1 = Player(PLAYER1_NAME, position=PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, position=PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)

        # 输入状态
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.current_frame = 1

        # 招式映射 - 从game_data导入
        self.action_map = ACTION_KEY_MAP
        self.action_names = ACTION_DISPLAY_NAMES

        # 游戏状态
        self.game_state = "input"
        self.battle_messages = []
        self.execute_delay_timer = 0

    def _load_chinese_font(self, size):
        """
        加载中文字体
        尝试多个常见的系统字体路径
        """
        import os
        import sys

        # 字体候选列表（按优先级）
        font_candidates = []

        # Windows字体
        if sys.platform == "win32":
            font_candidates.extend([
                "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",    # 黑体
                "C:/Windows/Fonts/simsun.ttc",    # 宋体
                "C:/Windows/Fonts/simkai.ttf",    # 楷体
            ])

        # macOS字体
        elif sys.platform == "darwin":
            font_candidates.extend([
                "/System/Library/Fonts/PingFang.ttc",           # 苹方
                "/Library/Fonts/Arial Unicode.ttf",              # Arial Unicode
                "/System/Library/Fonts/STHeiti Light.ttc",       # 黑体
            ])

        # Linux字体
        else:
            font_candidates.extend([
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",    # 文泉驿微米黑
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ])

        # 尝试加载字体
        for font_path in font_candidates:
            if os.path.exists(font_path):
                try:
                    return pygame.font.Font(font_path, size)
                except:
                    continue

        # 如果都失败，使用默认字体（不支持中文）
        print("Warning: No Chinese font found, using default font")
        return pygame.font.Font(None, size)

    def draw_grid(self):
        """绘制地图"""
        for i in range(MAP_SIZE):
            x = GRID_START_X + i * CELL_WIDTH
            y = GRID_START_Y

            # 绘制格子
            rect = pygame.Rect(x, y, CELL_WIDTH, CELL_HEIGHT)
            pygame.draw.rect(self.screen, GRAY, rect, 2)

            # 绘制格子编号
            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            text_rect = text.get_rect(center=(x + CELL_WIDTH // 2, y + 15))
            self.screen.blit(text, text_rect)

    def draw_player(self, player, color):
        """绘制玩家（处理重叠情况）"""
        distance = self.combat.get_distance()
        
        # 如果距离为0（重叠），只显示控制者
        if distance == 0:
            if player.controlled:
                # 这个玩家被控制，不显示
                return
        
        x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
        y = GRID_START_Y + CELL_HEIGHT // 2

        # 绘制玩家圆点
        pygame.draw.circle(self.screen, color, (x, y), PLAYER_RADIUS)

        # 绘制玩家名字
        text = self.small_font.render(player.name, True, BLACK)
        text_rect = text.get_rect(center=(x, y))
        self.screen.blit(text, text_rect)

    def draw_status(self):
        """绘制玩家状态"""
        y = GRID_START_Y + CELL_HEIGHT + 30

        # 玩家1状态
        p1_text = f"{self.player1.name}: HP {self.player1.hp}/{self.player1.max_hp}  连击 {self.player1.combo_count}/{COMBO_THRESHOLD}"
        if self.player1.charge_buff > 0:
            p1_text += f"  蓄力+{self.player1.charge_buff}"
        if self.player1.controlled:
            p1_text += "  [被控制]"
        if self.player1.stun_frames_remaining > 0:
            p1_text += f"  [硬直{self.player1.stun_frames_remaining}帧]"

        text = self.font.render(p1_text, True, PLAYER1_COLOR)
        self.screen.blit(text, (GRID_START_X, y))

        # 玩家2状态
        p2_text = f"{self.player2.name}: HP {self.player2.hp}/{self.player2.max_hp}  连击 {self.player2.combo_count}/{COMBO_THRESHOLD}"
        if self.player2.charge_buff > 0:
            p2_text += f"  蓄力+{self.player2.charge_buff}"
        if self.player2.controlled:
            p2_text += "  [被控制]"
        if self.player2.stun_frames_remaining > 0:
            p2_text += f"  [硬直{self.player2.stun_frames_remaining}帧]"

        text = self.font.render(p2_text, True, PLAYER2_COLOR)
        self.screen.blit(text, (GRID_START_X, y + 40))

    def draw_key_hints(self):
        """绘制按键提示 - 数据从配置导入"""
        x = GRID_START_X
        y = GRID_START_Y + CELL_HEIGHT + 140

        # 标题
        text = self.font.render(UI_TEXT['key_hints_title'], True, BLACK)
        self.screen.blit(text, (x, y))

        y += 50

        # 按键说明框（使用配置的文本）
        box_height = len(KEY_HINTS) * 22 + 10
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x - 10, y - 5, 280, box_height), border_radius=5)

        for line in KEY_HINTS:
            text = self.tiny_font.render(line, True, DARK_GRAY)
            self.screen.blit(text, (x, y))
            y += 22

        # 提示
        y += 10
        hint = UI_TEXT['turn_based_hint']
        text = self.tiny_font.render(hint, True, ORANGE)
        self.screen.blit(text, (x, y))

    def _get_frame_display(self, player, frame_index, actions, is_locked):
        """
        获取帧的显示内容
        
        Args:
            player: 玩家对象
            frame_index: 帧索引 (0或1)
            actions: 行动列表
            is_locked: 是否已锁定
        
        Returns:
            tuple: (显示文本, 背景颜色)
        """
        next_turn = self.combat.turn + 1
        frame_num = frame_index + 1
        
        # 检查这一帧是否被硬直锁定
        if player.is_frame_locked(next_turn, frame_num):
            return "🔒STUN", PURPLE
        
        # 已经输入的行动
        if frame_index < len(actions):
            if actions[frame_index] is None:
                # None表示被跳过（因为被锁定）
                return "🔒STUN", PURPLE
            else:
                action_name = self.action_names.get(actions[frame_index], "____")
                return action_name, ORANGE if len(actions) == 2 else YELLOW
        
        # 未输入
        if is_locked:
            return "✓✓✓", LIGHT_GRAY
        else:
            return "____", YELLOW

    def draw_input_status(self):
        """绘制输入状态（显示硬直锁定）- 双盲模式"""
        x = GRID_START_X + 300
        y = GRID_START_Y + CELL_HEIGHT + 120

        # 标题
        text = self.font.render(UI_TEXT['current_selection'], True, BLACK)
        self.screen.blit(text, (x, y))

        y += 50
        
        next_turn = self.combat.turn + 1

        # 玩家1行动 - 只有当前是玩家1时才显示详细信息
        if self.current_player == 1 and not self.p1_locked:
            # 玩家1正在输入，显示详细信息
            frame1_text, frame1_color = self._get_frame_display(
                self.player1, 0, self.p1_actions, self.p1_locked
            )
            frame2_text, frame2_color = self._get_frame_display(
                self.player1, 1, self.p1_actions, self.p1_locked
            )
            p1_text = f"{PLAYER1_NAME}: [{frame1_text}] [{frame2_text}]"
            bg_color = frame2_color if len(self.p1_actions) >= 1 else frame1_color
        elif self.p1_locked:
            # 玩家1已锁定，显示已确认但不显示具体内容
            p1_text = f"{PLAYER1_NAME}: [✓✓✓] [✓✓✓]"
            bg_color = LIGHT_RED
        else:
            # 玩家1还未输入（当前是玩家2的回合）
            p1_text = f"{PLAYER1_NAME}: [***] [***]"
            bg_color = LIGHT_RED

        pygame.draw.rect(self.screen, bg_color, (x - 10, y - 5, 300, 35), border_radius=5)
        text = self.small_font.render(p1_text, True, BLACK)
        self.screen.blit(text, (x, y))

        # 玩家2行动 - 只有当前是玩家2时才显示详细信息
        y += 50
        if self.current_player == 2 and not self.p2_locked:
            # 玩家2正在输入，显示详细信息
            frame1_text, frame1_color = self._get_frame_display(
                self.player2, 0, self.p2_actions, self.p2_locked
            )
            frame2_text, frame2_color = self._get_frame_display(
                self.player2, 1, self.p2_actions, self.p2_locked
            )
            p2_text = f"{PLAYER2_NAME}:   [{frame1_text}] [{frame2_text}]"
            bg_color = frame2_color if len(self.p2_actions) >= 1 else frame1_color
        elif self.p2_locked:
            # 玩家2已锁定，显示已确认但不显示具体内容
            p2_text = f"{PLAYER2_NAME}:   [✓✓✓] [✓✓✓]"
            bg_color = LIGHT_BLUE
        else:
            # 玩家2还未输入（当前是玩家1的回合）
            p2_text = f"{PLAYER2_NAME}:   [***] [***]"
            bg_color = LIGHT_BLUE

        pygame.draw.rect(self.screen, bg_color, (x - 10, y - 5, 300, 35), border_radius=5)
        text = self.small_font.render(p2_text, True, BLACK)
        self.screen.blit(text, (x, y))

        # 提示信息 - 使用配置的文本
        y += 60
        if self.game_state == "executing":
            remaining = self.execute_delay_timer / 60.0
            hint = UI_TEXT['executing'].format(time=remaining)
            text = self.small_font.render(hint, True, ORANGE)
            self.screen.blit(text, (x, y))
        elif not self.p1_locked and not self.p2_locked:
            if self.current_player == 1:
                next_turn = self.combat.turn + 1
                
                # 检查是否被控制
                if self.player1.controlled:
                    hint = UI_TEXT['controlled_limit']
                    color = RED
                else:
                    # 找到下一个需要输入的帧
                    next_input_frame = None
                    for frame_idx in range(2):
                        frame_num = frame_idx + 1
                        if not self.player1.is_frame_locked(next_turn, frame_num) and frame_idx >= len(self.p1_actions):
                            next_input_frame = frame_num
                            break
                    
                    if next_input_frame is None:
                        # 所有帧都已输入或锁定
                        hint = UI_TEXT['selection_complete']
                        color = ORANGE
                    else:
                        hint = UI_TEXT['alice_turn'].format(frame=next_input_frame)
                        color = GREEN
            else:
                next_turn = self.combat.turn + 1
                
                # 检查是否被控制
                if self.player2.controlled:
                    hint = UI_TEXT['controlled_limit']
                    color = RED
                else:
                    # 找到下一个需要输入的帧
                    next_input_frame = None
                    for frame_idx in range(2):
                        frame_num = frame_idx + 1
                        if not self.player2.is_frame_locked(next_turn, frame_num) and frame_idx >= len(self.p2_actions):
                            next_input_frame = frame_num
                            break
                    
                    if next_input_frame is None:
                        # 所有帧都已输入或锁定
                        hint = UI_TEXT['selection_complete']
                        color = ORANGE
                    else:
                        hint = UI_TEXT['bob_turn'].format(frame=next_input_frame)
                        color = GREEN
            text = self.small_font.render(hint, True, color)
            self.screen.blit(text, (x, y))
        elif self.p1_locked and not self.p2_locked:
            hint = UI_TEXT['waiting_bob']
            text = self.small_font.render(hint, True, BLUE)
            self.screen.blit(text, (x, y))
        elif not self.p1_locked and self.p2_locked:
            hint = UI_TEXT['waiting_alice']
            text = self.small_font.render(hint, True, RED)
            self.screen.blit(text, (x, y))
        else:
            hint = UI_TEXT['both_confirmed']
            text = self.small_font.render(hint, True, ORANGE)
            self.screen.blit(text, (x, y))

    def draw_header(self):
        """绘制顶部信息"""
        distance = self.combat.get_distance()
        header_text = UI_TEXT['turn_info'].format(
            turn=self.combat.turn,
            distance=distance
        )

        text = self.large_font.render(header_text, True, BLACK)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(text, text_rect)

    def draw_battle_messages(self):
        """显示战斗消息（右侧消息框）"""
        # 绘制消息框背景
        pygame.draw.rect(self.screen, LIGHT_GRAY,
                        (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT),
                        border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT),
                        2, border_radius=10)

        # 标题
        title = self.font.render(UI_TEXT['battle_log_title'], True, BLACK)
        self.screen.blit(title, (MESSAGE_BOX_X + 10, MESSAGE_BOX_Y + 10))

        # 绘制分隔线
        pygame.draw.line(self.screen, DARK_GRAY,
                        (MESSAGE_BOX_X + 10, MESSAGE_BOX_Y + 50),
                        (MESSAGE_BOX_X + MESSAGE_BOX_WIDTH - 10, MESSAGE_BOX_Y + 50), 2)

        # 显示消息（最新的在下面）
        if self.battle_messages:
            y = MESSAGE_BOX_Y + 60
            visible_messages = self.battle_messages[-20:]

            for message in visible_messages:
                # 清理消息
                clean_msg = message.replace('=', '').strip()
                if not clean_msg or clean_msg.startswith('---'):
                    continue

                # 根据内容选择颜色
                if '💔' in message or '受到' in message:
                    color = RED
                elif '✨' in message or '成功' in message:
                    color = GREEN
                elif '⚔️' in message or '🦵' in message:
                    color = BLUE
                elif '🔒' in message or '硬直' in message:
                    color = PURPLE
                elif '❌' in message:
                    color = DARK_GRAY
                else:
                    color = BLACK

                text = self.tiny_font.render(clean_msg, True, color)

                # 如果文字太长，截断
                if text.get_width() > MESSAGE_BOX_WIDTH - 20:
                    while text.get_width() > MESSAGE_BOX_WIDTH - 20 and len(clean_msg) > 0:
                        clean_msg = clean_msg[:-1]
                        text = self.tiny_font.render(clean_msg + "...", True, color)

                self.screen.blit(text, (MESSAGE_BOX_X + 10, y))
                y += 22

                if y > MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 10:
                    break

        # 提示
        if self.game_state == "executing":
            remaining_seconds = self.execute_delay_timer / 60.0
            hint = f"战斗中... ({remaining_seconds:.1f}s)"
            hint_text = self.tiny_font.render(hint, True, ORANGE)
            self.screen.blit(hint_text, (MESSAGE_BOX_X + 10, MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 25))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 胜者文字
        winner = self.combat.get_winner()
        if winner == "平局":
            text = UI_TEXT['game_over_draw']
        else:
            text = UI_TEXT['game_over_win'].format(winner=winner)

        winner_text = self.large_font.render(text, True, YELLOW)
        text_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(winner_text, text_rect)

        # 提示重新开始
        hint = UI_TEXT['restart_hint']
        hint_text = self.font.render(hint, True, WHITE)
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(hint_text, hint_rect)

    def handle_input(self, event):
        """处理按键输入"""
        if self.game_state != "input":
            return

        # Backspace撤销
        if event.key == pygame.K_BACKSPACE:
            if self.current_player == 1 and not self.p1_locked:
                if len(self.p1_actions) > 0:
                    removed_action = self.p1_actions.pop()
                    self.current_frame = len(self.p1_actions) + 1
                    print(UI_TEXT['alice_undo'].format(action=self.action_names[removed_action]))
                else:
                    print(UI_TEXT['no_undo'].format(player=PLAYER1_NAME))
            elif self.current_player == 2 and not self.p2_locked:
                if len(self.p2_actions) > 0:
                    removed_action = self.p2_actions.pop()
                    self.current_frame = len(self.p2_actions) + 1
                    print(UI_TEXT['bob_undo'].format(action=self.action_names[removed_action]))
                else:
                    print(UI_TEXT['no_undo'].format(player=PLAYER2_NAME))
            return

        # 空格键确认锁定
        if event.key == pygame.K_SPACE:
            next_turn = self.combat.turn + 1
            
            if self.current_player == 1 and not self.p1_locked:
                # 检查是否所有需要的帧都已输入或锁定
                frames_needed = 2
                frames_ready = 0
                for i in range(2):
                    if i < len(self.p1_actions) or self.player1.is_frame_locked(next_turn, i + 1):
                        frames_ready += 1
                
                if frames_ready == frames_needed:
                    self.p1_locked = True
                    self.current_player = 2
                    print(f"✓ {PLAYER1_NAME}已锁定选择")
                else:
                    needed = frames_needed - frames_ready
                    print(UI_TEXT['alice_needs_more'].format(count=needed))
                    
            elif self.current_player == 2 and not self.p2_locked:
                # 检查是否所有需要的帧都已输入或锁定
                frames_needed = 2
                frames_ready = 0
                for i in range(2):
                    if i < len(self.p2_actions) or self.player2.is_frame_locked(next_turn, i + 1):
                        frames_ready += 1
                
                if frames_ready == frames_needed:
                    self.p2_locked = True
                    print(f"✓ {PLAYER2_NAME}已锁定选择")
                    # 双方都锁定，执行回合
                    if self.p1_locked and self.p2_locked:
                        self.execute_turn()
                else:
                    needed = frames_needed - frames_ready
                    print(UI_TEXT['bob_needs_more'].format(count=needed))
            return

        # 玩家1输入（数字键1-9）
        if self.current_player == 1 and not self.p1_locked:
            key_map = {
                pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3',
                pygame.K_4: '4', pygame.K_5: '5', pygame.K_6: '6',
                pygame.K_7: '7', pygame.K_8: '8', pygame.K_9: '9'
            }

            if event.key in key_map:
                next_turn = self.combat.turn + 1
                
                # 检查还需要输入哪些帧
                frames_to_input = []
                for frame_idx in range(2):
                    frame_num = frame_idx + 1
                    # 如果这一帧没有被锁定，且还没有输入，则需要输入
                    if not self.player1.is_frame_locked(next_turn, frame_num) and frame_idx >= len(self.p1_actions):
                        frames_to_input.append(frame_num)
                
                if len(frames_to_input) > 0:
                    # 输入到第一个需要输入的帧
                    target_frame = frames_to_input[0]
                    
                    # 如果第1帧被锁定，但我们要输入第2帧，需要先填充第1帧为None
                    while len(self.p1_actions) < target_frame - 1:
                        self.p1_actions.append(None)
                    
                    key = key_map[event.key]
                    action = self.action_map[key]
                    
                    # 检查被控制时的行动限制
                    if self.player1.controlled and action not in ['defend', 'burst']:
                        print(f"⛓️ {PLAYER1_NAME}被控制，只能使用防御或爆血！")
                        return
                    
                    self.p1_actions.append(action)
                    self.current_frame = len(self.p1_actions) + 1
                    print(f"{PLAYER1_NAME}选择第{target_frame}帧: {self.action_names[action]}")
                else:
                    print(UI_TEXT['already_selected'].format(player=PLAYER1_NAME))

        # 玩家2输入（数字键1-9）
        elif self.current_player == 2 and not self.p2_locked:
            letter_map = {
                pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3',
                pygame.K_4: '4', pygame.K_5: '5', pygame.K_6: '6',
                pygame.K_7: '7', pygame.K_8: '8', pygame.K_9: '9'
            }

            if event.key in letter_map:
                next_turn = self.combat.turn + 1
                
                # 检查还需要输入哪些帧
                frames_to_input = []
                for frame_idx in range(2):
                    frame_num = frame_idx + 1
                    # 如果这一帧没有被锁定，且还没有输入，则需要输入
                    if not self.player2.is_frame_locked(next_turn, frame_num) and frame_idx >= len(self.p2_actions):
                        frames_to_input.append(frame_num)
                
                if len(frames_to_input) > 0:
                    # 输入到第一个需要输入的帧
                    target_frame = frames_to_input[0]
                    
                    # 如果第1帧被锁定，但我们要输入第2帧，需要先填充第1帧为None
                    while len(self.p2_actions) < target_frame - 1:
                        self.p2_actions.append(None)
                    
                    key = letter_map[event.key]
                    action = self.action_map[key]
                    
                    # 检查被控制时的行动限制
                    if self.player2.controlled and action not in ['defend', 'burst']:
                        print(f"⛓️ {PLAYER2_NAME}被控制，只能使用防御或爆血！")
                        return
                    
                    self.p2_actions.append(action)
                    self.current_frame = len(self.p2_actions) + 1
                    print(f"{PLAYER2_NAME}选择第{target_frame}帧: {self.action_names[action]}")
                else:
                    print(UI_TEXT['already_selected'].format(player=PLAYER2_NAME))

    def execute_turn(self):
        """执行回合"""
        import io
        import sys

        self.game_state = "executing"
        self.battle_messages = []

        # 捕获打印输出
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            # 为被硬直锁定的帧填充None
            next_turn = self.combat.turn + 1
            
            # 准备玩家1的行动列表
            p1_final_actions = []
            for frame_idx in range(2):
                frame_num = frame_idx + 1
                if self.player1.is_frame_locked(next_turn, frame_num):
                    p1_final_actions.append(None)  # 硬直锁定的帧
                elif frame_idx < len(self.p1_actions):
                    p1_final_actions.append(self.p1_actions[frame_idx])
                else:
                    p1_final_actions.append(None)
            
            # 准备玩家2的行动列表
            p2_final_actions = []
            for frame_idx in range(2):
                frame_num = frame_idx + 1
                if self.player2.is_frame_locked(next_turn, frame_num):
                    p2_final_actions.append(None)  # 硬直锁定的帧
                elif frame_idx < len(self.p2_actions):
                    p2_final_actions.append(self.p2_actions[frame_idx])
                else:
                    p2_final_actions.append(None)
            
            # 执行战斗
            continue_battle = self.combat.execute_turn(p1_final_actions, p2_final_actions)

            # 获取输出
            output = captured_output.getvalue()
            self.battle_messages = [line for line in output.split('\n') if line.strip()]

        finally:
            sys.stdout = old_stdout

        # 设置延迟计时器（使用配置的值）
        self.execute_delay_timer = EXECUTE_DELAY_FRAMES

        # 检查游戏是否结束
        if not continue_battle:
            self.game_state = "game_over"

    def reset_game(self):
        """重置游戏 - 使用配置的值"""
        self.player1 = Player(PLAYER1_NAME, position=PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, position=PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.current_frame = 1
        self.game_state = "input"
        self.battle_messages = []
        self.execute_delay_timer = 0

    def run(self):
        """主循环"""
        running = True

        while running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    # ESC退出
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    # 游戏结束时按R重新开始
                    elif event.key == pygame.K_r and self.game_state == "game_over":
                        self.reset_game()

                    # 输入状态处理按键
                    elif self.game_state == "input":
                        self.handle_input(event)

            # 更新执行延迟计时器（非阻塞）
            if self.game_state == "executing" and self.execute_delay_timer > 0:
                self.execute_delay_timer -= 1

                # 计时器归零，重置输入状态
                if self.execute_delay_timer <= 0:
                    self.p1_actions = []
                    self.p2_actions = []
                    self.p1_locked = False
                    self.p2_locked = False
                    self.current_player = 1
                    self.current_frame = 1

                    # 如果不是game_over，返回input状态
                    if self.game_state != "game_over":
                        self.game_state = "input"

            # 绘制
            self.screen.fill(WHITE)

            # 绘制各个元素
            self.draw_header()
            self.draw_grid()
            self.draw_player(self.player1, PLAYER1_COLOR)  # 使用配置的颜色
            self.draw_player(self.player2, PLAYER2_COLOR)  # 使用配置的颜色
            self.draw_status()
            self.draw_battle_messages()

            if self.game_state == "input" or self.game_state == "executing":
                self.draw_key_hints()
                self.draw_input_status()

            if self.game_state == "game_over":
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """主函数"""
    game = GameUI()
    game.run()


if __name__ == "__main__":
    main()