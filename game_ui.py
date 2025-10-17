"""
game_ui.py
可视化界面 - 使用Pygame实现（完整最终版）
支持帧帧播放动画 + 独立技能悬停 + 机制说明
"""

import pygame
import sys
import io
from player import Player
from combat_manager import CombatManager

# 导入配置
from config import *
from game_data import ACTION_KEY_MAP, ACTION_DISPLAY_NAMES, KEY_HINTS, SKILL_DESCRIPTIONS, GAME_MECHANICS


class GameUI:
    """游戏可视化界面"""

    def __init__(self):
        """初始化界面"""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(UI_TEXT['title'])
        self.clock = pygame.time.Clock()

        # 加载字体
        self.font = self._load_chinese_font(28)
        self.small_font = self._load_chinese_font(22)
        self.large_font = self._load_chinese_font(48)
        self.tiny_font = self._load_chinese_font(16)

        # 游戏状态
        self.player1 = Player(PLAYER1_NAME, position=PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, position=PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)

        # 输入状态
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1

        # 招式映射
        self.action_map = ACTION_KEY_MAP
        self.action_names = ACTION_DISPLAY_NAMES
        self.skill_descriptions = SKILL_DESCRIPTIONS
        self.game_mechanics = GAME_MECHANICS

        # 游戏状态机
        self.game_state = "input"
        self.battle_messages = []
        
        # 帧播放状态
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.turn_delay_timer = 0
        self.p1_final_actions = []
        self.p2_final_actions = []
        
        # 鼠标悬停状态
        self.hovered_skill = None
        self.hovered_mechanic = None

    def _load_chinese_font(self, size):
        """加载中文字体"""
        import os
        font_candidates = []

        if sys.platform == "win32":
            font_candidates.extend([
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
            ])
        elif sys.platform == "darwin":
            font_candidates.extend([
                "/System/Library/Fonts/PingFang.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ])
        else:
            font_candidates.extend([
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            ])

        for font_path in font_candidates:
            if os.path.exists(font_path):
                try:
                    return pygame.font.Font(font_path, size)
                except:
                    continue

        return pygame.font.Font(None, size)

    def draw_grid(self):
        """绘制地图"""
        for i in range(MAP_SIZE):
            x = GRID_START_X + i * CELL_WIDTH
            y = GRID_START_Y

            rect = pygame.Rect(x, y, CELL_WIDTH, CELL_HEIGHT)
            pygame.draw.rect(self.screen, GRAY, rect, 2)

            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            text_rect = text.get_rect(center=(x + CELL_WIDTH // 2, y + 15))
            self.screen.blit(text, text_rect)

    def draw_hp_bar(self, player, color):
        """绘制血条在玩家头顶"""
        x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
        y = GRID_START_Y + CELL_HEIGHT // 2 + HP_BAR_OFFSET_Y

        bg_rect = pygame.Rect(x - HP_BAR_WIDTH // 2, y, HP_BAR_WIDTH, HP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, DARK_GRAY, bg_rect)

        hp_ratio = player.hp / player.max_hp
        hp_width = int(HP_BAR_WIDTH * hp_ratio)
        hp_rect = pygame.Rect(x - HP_BAR_WIDTH // 2, y, hp_width, HP_BAR_HEIGHT)
        
        if hp_ratio > 0.5:
            hp_color = GREEN
        elif hp_ratio > 0.25:
            hp_color = YELLOW
        else:
            hp_color = RED
        
        pygame.draw.rect(self.screen, hp_color, hp_rect)

        hp_text = f"{player.hp}/{player.max_hp}"
        text = self.tiny_font.render(hp_text, True, WHITE)
        text_rect = text.get_rect(center=(x, y + HP_BAR_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def draw_combo_count(self, player):
        """绘制连击数在玩家头顶"""
        if player.combo_count > 0:
            x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
            y = GRID_START_Y + CELL_HEIGHT // 2 + COMBO_DISPLAY_OFFSET_Y

            combo_text = f"连击 {player.combo_count}/{COMBO_THRESHOLD}"
            text = self.tiny_font.render(combo_text, True, ORANGE)
            text_rect = text.get_rect(center=(x, y))
            
            bg_rect = text_rect.inflate(10, 4)
            pygame.draw.rect(self.screen, BLACK, bg_rect, border_radius=3)
            
            self.screen.blit(text, text_rect)

    def draw_player(self, player, color):
        """绘制玩家"""
        distance = self.combat.get_distance()
        
        if distance == 0:
            if player.controlled:
                return
        
        x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
        y = GRID_START_Y + CELL_HEIGHT // 2

        pygame.draw.circle(self.screen, color, (x, y), PLAYER_RADIUS)
        
        if player.controlled:
            pygame.draw.circle(self.screen, YELLOW, (x, y), PLAYER_RADIUS + 5, 3)
        
        if player.charge_level > 0:
            glow_color = YELLOW if player.charge_level == 1 else ORANGE
            pygame.draw.circle(self.screen, glow_color, (x, y), PLAYER_RADIUS + 8, 2)

        text = self.small_font.render(player.name, True, BLACK)
        text_rect = text.get_rect(center=(x, y))
        self.screen.blit(text, text_rect)
        
        self.draw_hp_bar(player, color)
        self.draw_combo_count(player)

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
        
        if self.game_state == "frame_executing":
            frame_text = f"▶ 正在执行第 {self.current_frame_index + 1} 帧"
            text = self.font.render(frame_text, True, ORANGE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 100))
            self.screen.blit(text, text_rect)
            
            progress_width = 200
            progress_height = 10
            progress_x = WINDOW_WIDTH // 2 - progress_width // 2
            progress_y = 130
            
            pygame.draw.rect(self.screen, GRAY, 
                           (progress_x, progress_y, progress_width, progress_height))
            
            frame_progress = self.frame_delay_timer / FRAME_DELAY
            current_progress = progress_width * frame_progress
            pygame.draw.rect(self.screen, GREEN,
                           (progress_x, progress_y, current_progress, progress_height))
        
        elif self.game_state == "turn_delay":
            hint_text = "回合结束，准备下一回合..."
            text = self.small_font.render(hint_text, True, BLUE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 100))
            self.screen.blit(text, text_rect)

    def draw_key_hints(self):
        """绘制按键提示（每行独立悬停）"""
        x = GRID_START_X
        y = GRID_START_Y + CELL_HEIGHT + 40

        title_text = self.font.render("按键说明", True, BLACK)
        self.screen.blit(title_text, (x, y))

        y += 40
        box_height = len(KEY_HINTS) * 24 + 10
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x - 10, y - 5, 260, box_height), border_radius=5)

        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill = None

        for i, (line_text, skill_key) in enumerate(KEY_HINTS):
            line_y = y + i * 24
            
            line_rect = pygame.Rect(x - 8, line_y - 2, 256, 22)
            is_hovered = line_rect.collidepoint(mouse_pos)
            
            if is_hovered:
                pygame.draw.rect(self.screen, YELLOW, line_rect, border_radius=3)
                self.hovered_skill = skill_key
            
            text = self.tiny_font.render(line_text, True, BLACK if is_hovered else DARK_GRAY)
            self.screen.blit(text, (x, line_y))

    def draw_game_mechanics(self):
        """绘制游戏机制说明（连击和硬直）"""
        x = GRID_START_X + 280
        y = GRID_START_Y + CELL_HEIGHT + 40

        title_text = self.font.render("游戏机制", True, BLACK)
        self.screen.blit(title_text, (x, y))

        y += 40
        
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_mechanic = None

        for i, (mech_key, mech_info) in enumerate(GAME_MECHANICS.items()):
            mech_y = y + i * 30
            
            # 绘制背景框
            mech_rect = pygame.Rect(x - 8, mech_y - 2, 180, 26)
            is_hovered = mech_rect.collidepoint(mouse_pos)
            
            bg_color = LIGHT_BLUE if i == 0 else LIGHT_RED
            if is_hovered:
                bg_color = YELLOW
                self.hovered_mechanic = mech_key
            
            pygame.draw.rect(self.screen, bg_color, mech_rect, border_radius=5)
            
            # 绘制文字
            mech_text = self.small_font.render(mech_info['name'], True, BLACK if is_hovered else DARK_GRAY)
            self.screen.blit(mech_text, (x, mech_y))

    def draw_skill_tooltip(self):
        """绘制技能/机制描述悬停窗口"""
        tooltip_info = None
        
        if self.hovered_skill and self.hovered_skill in self.skill_descriptions:
            tooltip_info = self.skill_descriptions[self.hovered_skill]
        elif self.hovered_mechanic and self.hovered_mechanic in self.game_mechanics:
            tooltip_info = self.game_mechanics[self.hovered_mechanic]
        
        if tooltip_info:
            # 窗口位置（在按键说明和机制说明的右侧）
            tooltip_x = GRID_START_X + 480
            tooltip_y = GRID_START_Y + CELL_HEIGHT + 80
            tooltip_width = 360
            
            # 计算窗口高度
            line_height = 18
            tooltip_height = 40 + len(tooltip_info['desc']) * line_height
            
            # 阴影
            shadow_offset = 3
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (tooltip_x + shadow_offset, tooltip_y + shadow_offset, 
                            tooltip_width, tooltip_height), 
                           border_radius=8)
            
            # 背景
            pygame.draw.rect(self.screen, BLACK, 
                           (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 
                           border_radius=8)
            pygame.draw.rect(self.screen, (250, 250, 250), 
                           (tooltip_x + 2, tooltip_y + 2, tooltip_width - 4, tooltip_height - 4), 
                           border_radius=6)
            
            # 标题
            title_text = self.small_font.render(tooltip_info['name'], True, BLUE)
            self.screen.blit(title_text, (tooltip_x + 10, tooltip_y + 8))
            
            # 分隔线
            pygame.draw.line(self.screen, GRAY, 
                           (tooltip_x + 10, tooltip_y + 33), 
                           (tooltip_x + tooltip_width - 10, tooltip_y + 33), 1)
            
            # 描述
            desc_y = tooltip_y + 38
            for line in tooltip_info['desc']:
                if line:
                    desc_text = self.tiny_font.render(line, True, BLACK)
                    self.screen.blit(desc_text, (tooltip_x + 12, desc_y))
                desc_y += line_height

    def _get_frame_display(self, player, frame_index, actions, is_locked):
        """获取帧的显示内容（硬直帧可能有爆血）"""
        next_turn = self.combat.turn + 1
        frame_num = frame_index + 1
        
        # 检查是否已输入行动
        if frame_index < len(actions):
            if actions[frame_index] is None:
                # None表示被跳过（因为被锁定且没输入爆血）
                return "🔒STUN", PURPLE
            elif actions[frame_index] == 'burst':
                # 硬直帧输入了爆血
                return "Burst💥", ORANGE
            else:
                action_name = self.action_names.get(actions[frame_index], "____")
                return action_name, ORANGE if len(actions) >= 2 else YELLOW
        
        # 未输入 - 检查硬直锁定
        if player.is_frame_locked(next_turn, frame_num):
            return "🔒STUN", PURPLE
        
        # 未输入
        if is_locked:
            return "✓✓✓", LIGHT_GRAY
        else:
            return "____", YELLOW

    def draw_input_status(self):
        """绘制输入状态（移到按键说明下方）"""
        x = GRID_START_X
        y = GRID_START_Y + CELL_HEIGHT + 280  # 调整位置避免重叠

        # 标题
        title_text = self.font.render(UI_TEXT['current_selection'], True, BLACK)
        self.screen.blit(title_text, (x, y))

        y += 45
        next_turn = self.combat.turn + 1

        # 玩家1行动
        if self.current_player == 1 and not self.p1_locked:
            frame1_text, frame1_color = self._get_frame_display(
                self.player1, 0, self.p1_actions, self.p1_locked
            )
            frame2_text, frame2_color = self._get_frame_display(
                self.player1, 1, self.p1_actions, self.p1_locked
            )
            p1_text = f"{PLAYER1_NAME}: [{frame1_text}] [{frame2_text}]"
            bg_color = frame2_color if len(self.p1_actions) >= 1 else frame1_color
        elif self.p1_locked:
            p1_text = f"{PLAYER1_NAME}: [✓✓✓] [✓✓✓]"
            bg_color = LIGHT_RED
        else:
            p1_text = f"{PLAYER1_NAME}: [***] [***]"
            bg_color = LIGHT_RED

        pygame.draw.rect(self.screen, bg_color, (x - 10, y - 5, 350, 35), border_radius=5)
        text = self.small_font.render(p1_text, True, BLACK)
        self.screen.blit(text, (x, y))

        # 玩家2行动
        y += 45
        if self.current_player == 2 and not self.p2_locked:
            frame1_text, frame1_color = self._get_frame_display(
                self.player2, 0, self.p2_actions, self.p2_locked
            )
            frame2_text, frame2_color = self._get_frame_display(
                self.player2, 1, self.p2_actions, self.p2_locked
            )
            p2_text = f"{PLAYER2_NAME}:   [{frame1_text}] [{frame2_text}]"
            bg_color = frame2_color if len(self.p2_actions) >= 1 else frame1_color
        elif self.p2_locked:
            p2_text = f"{PLAYER2_NAME}:   [✓✓✓] [✓✓✓]"
            bg_color = LIGHT_BLUE
        else:
            p2_text = f"{PLAYER2_NAME}:   [***] [***]"
            bg_color = LIGHT_BLUE

        pygame.draw.rect(self.screen, bg_color, (x - 10, y - 5, 350, 35), border_radius=5)
        text = self.small_font.render(p2_text, True, BLACK)
        self.screen.blit(text, (x, y))

        # 提示信息
        y += 45
        if not self.p1_locked and not self.p2_locked:
            if self.current_player == 1:
                next_turn = self.combat.turn + 1
                
                # 检查下一个需要输入的帧
                next_input_frame = None
                for frame_idx in range(2):
                    frame_num = frame_idx + 1
                    is_locked = self.player1.is_frame_locked(next_turn, frame_num)
                    already_input = frame_idx < len(self.p1_actions)
                    
                    if not already_input:
                        if not is_locked or True:  # 硬直帧也算可输入（可以输入爆血）
                            next_input_frame = frame_num
                            break
                
                if self.player1.controlled:
                    hint = UI_TEXT['controlled_limit']
                    color = RED
                elif next_input_frame and self.player1.is_frame_locked(next_turn, next_input_frame):
                    hint = f"😵 第{next_input_frame}帧硬直，可用O(爆血)"
                    color = PURPLE
                elif next_input_frame is None:
                    hint = UI_TEXT['selection_complete']
                    color = ORANGE
                else:
                    hint = UI_TEXT['alice_turn'].format(frame=next_input_frame)
                    color = GREEN
            else:
                next_turn = self.combat.turn + 1
                
                next_input_frame = None
                for frame_idx in range(2):
                    frame_num = frame_idx + 1
                    is_locked = self.player2.is_frame_locked(next_turn, frame_num)
                    already_input = frame_idx < len(self.p2_actions)
                    
                    if not already_input:
                        if not is_locked or True:
                            next_input_frame = frame_num
                            break
                
                if self.player2.controlled:
                    hint = UI_TEXT['controlled_limit']
                    color = RED
                elif next_input_frame and self.player2.is_frame_locked(next_turn, next_input_frame):
                    hint = f"😵 第{next_input_frame}帧硬直，可用O(爆血)"
                    color = PURPLE
                elif next_input_frame is None:
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
        
        y += 30
        turn_hint = "按 SPACE 确认 | Backspace 撤销"
        text = self.tiny_font.render(turn_hint, True, ORANGE)
        self.screen.blit(text, (x, y))

    def draw_battle_messages(self):
        """显示战斗消息"""
        pygame.draw.rect(self.screen, LIGHT_GRAY,
                        (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT),
                        border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT),
                        2, border_radius=10)

        title = self.font.render(UI_TEXT['battle_log_title'], True, BLACK)
        self.screen.blit(title, (MESSAGE_BOX_X + 10, MESSAGE_BOX_Y + 10))

        pygame.draw.line(self.screen, DARK_GRAY,
                        (MESSAGE_BOX_X + 10, MESSAGE_BOX_Y + 45),
                        (MESSAGE_BOX_X + MESSAGE_BOX_WIDTH - 10, MESSAGE_BOX_Y + 45), 2)

        if self.battle_messages:
            y = MESSAGE_BOX_Y + 55
            visible_messages = self.battle_messages[-28:]

            for message in visible_messages:
                clean_msg = message.replace('=', '').strip()
                if not clean_msg or clean_msg.startswith('---'):
                    continue

                if '💔' in message or '受到' in message:
                    color = RED
                elif '✨' in message or '蓄力' in message:
                    color = PURPLE
                elif '⚔️' in message or '攻击' in message:
                    color = BLUE
                elif '🔒' in message or '硬直' in message or '控制' in message:
                    color = ORANGE
                elif '❌' in message:
                    color = DARK_GRAY
                else:
                    color = BLACK

                text = self.tiny_font.render(clean_msg, True, color)

                if text.get_width() > MESSAGE_BOX_WIDTH - 20:
                    while text.get_width() > MESSAGE_BOX_WIDTH - 20 and len(clean_msg) > 0:
                        clean_msg = clean_msg[:-1]
                        text = self.tiny_font.render(clean_msg + "...", True, color)

                self.screen.blit(text, (MESSAGE_BOX_X + 10, y))
                y += 19

                if y > MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 10:
                    break

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        winner = self.combat.get_winner()
        if winner == "平局":
            text = UI_TEXT['game_over_draw']
        else:
            text = UI_TEXT['game_over_win'].format(winner=winner)

        winner_text = self.large_font.render(text, True, YELLOW)
        text_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(winner_text, text_rect)

        hint = UI_TEXT['restart_hint']
        hint_text = self.font.render(hint, True, WHITE)
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(hint_text, hint_rect)

    def handle_input(self, event):
        """处理按键输入"""
        if self.game_state != "input":
            return

        if event.key == pygame.K_BACKSPACE:
            if self.current_player == 1 and not self.p1_locked:
                if len(self.p1_actions) > 0:
                    removed_action = self.p1_actions.pop()
                    print(UI_TEXT['alice_undo'].format(action=self.action_names.get(removed_action, "???")))
                else:
                    print(UI_TEXT['no_undo'].format(player=PLAYER1_NAME))
            elif self.current_player == 2 and not self.p2_locked:
                if len(self.p2_actions) > 0:
                    removed_action = self.p2_actions.pop()
                    print(UI_TEXT['bob_undo'].format(action=self.action_names.get(removed_action, "???")))
                else:
                    print(UI_TEXT['no_undo'].format(player=PLAYER2_NAME))
            return

        if event.key == pygame.K_SPACE:
            next_turn = self.combat.turn + 1
            
            if self.current_player == 1 and not self.p1_locked:
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
                    print(UI_TEXT['alice_needs_more'].format(count=frames_needed - frames_ready))
                    
            elif self.current_player == 2 and not self.p2_locked:
                frames_needed = 2
                frames_ready = 0
                for i in range(2):
                    if i < len(self.p2_actions) or self.player2.is_frame_locked(next_turn, i + 1):
                        frames_ready += 1
                
                if frames_ready == frames_needed:
                    self.p2_locked = True
                    print(f"✓ {PLAYER2_NAME}已锁定选择")
                    if self.p1_locked and self.p2_locked:
                        self.start_turn_execution()
                else:
                    print(UI_TEXT['bob_needs_more'].format(count=frames_needed - frames_ready))
            return

        key_char = pygame.key.name(event.key)
        
        if self.current_player == 1 and not self.p1_locked:
            self._handle_player_input(self.player1, self.p1_actions, key_char, PLAYER1_NAME)
        elif self.current_player == 2 and not self.p2_locked:
            self._handle_player_input(self.player2, self.p2_actions, key_char, PLAYER2_NAME)

    def _handle_player_input(self, player, actions, key_char, player_name):
        """处理玩家输入（允许硬直时输入爆血）"""
        if key_char not in self.action_map:
            return
        
        next_turn = self.combat.turn + 1
        action = self.action_map[key_char]
        
        # 找到需要输入的帧
        frames_to_input = []
        for frame_idx in range(2):
            frame_num = frame_idx + 1
            is_locked = player.is_frame_locked(next_turn, frame_num)
            already_input = frame_idx < len(actions)
            
            # 如果帧被硬直锁定，但输入的是爆血，允许输入
            if is_locked and action == 'burst' and not already_input:
                frames_to_input.append(frame_num)
            # 如果帧没有被锁定，且还没输入，允许输入
            elif not is_locked and not already_input:
                frames_to_input.append(frame_num)
        
        if len(frames_to_input) > 0:
            target_frame = frames_to_input[0]
            
            # 填充被锁定的帧
            while len(actions) < target_frame - 1:
                actions.append(None)
            
            # 检查被控制时的限制
            if player.controlled and action not in ['defend', 'burst']:
                print(f"⛓️ {player_name}被控制，只能使用防御(S)或爆血(O)！")
                return
            
            # 检查硬直时的限制（只能爆血）
            if player.is_frame_locked(next_turn, target_frame) and action != 'burst':
                print(f"😵 {player_name}第{target_frame}帧硬直中，只能使用爆血(O)！")
                return
            
            actions.append(action)
            print(f"{player_name}选择第{target_frame}帧: {self.action_names[action]}")
        else:
            print(UI_TEXT['already_selected'].format(player=player_name))

    def start_turn_execution(self):
        """开始执行回合"""
        self.game_state = "frame_executing"
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        
        next_turn = self.combat.turn + 1
        
        p1_final_actions = []
        for frame_idx in range(2):
            frame_num = frame_idx + 1
            if self.player1.is_frame_locked(next_turn, frame_num):
                p1_final_actions.append(None)
            elif frame_idx < len(self.p1_actions):
                p1_final_actions.append(self.p1_actions[frame_idx])
            else:
                p1_final_actions.append(None)
        
        p2_final_actions = []
        for frame_idx in range(2):
            frame_num = frame_idx + 1
            if self.player2.is_frame_locked(next_turn, frame_num):
                p2_final_actions.append(None)
            elif frame_idx < len(self.p2_actions):
                p2_final_actions.append(self.p2_actions[frame_idx])
            else:
                p2_final_actions.append(None)
        
        self.p1_final_actions = p1_final_actions
        self.p2_final_actions = p2_final_actions
        self.battle_messages = []

    def execute_current_frame(self):
        """执行当前帧"""
        frame_idx = self.current_frame_index
        current_frame = frame_idx + 1
        
        if frame_idx == 0:
            self.combat.turn += 1
            self.combat.player1.clear_expired_locks(self.combat.turn)
            self.combat.player2.clear_expired_locks(self.combat.turn)
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            if frame_idx == 0:
                print(f"\n{'='*60}")
                print(f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格")
                self.player1.show_status()
                self.player2.show_status()
                print('='*60)
            
            print(f"\n--- 第 {current_frame} 帧 ---")
            
            self.player1.reset_frame_status()
            self.player2.reset_frame_status()
            
            p1_action = self.p1_final_actions[frame_idx] if frame_idx < len(self.p1_final_actions) else None
            p2_action = self.p2_final_actions[frame_idx] if frame_idx < len(self.p2_final_actions) else None
            
            # 检查硬直锁定（爆血除外）
            if self.player1.is_frame_locked(self.combat.turn, current_frame):
                if p1_action != 'burst':
                    print(f"🔒 {self.player1.name} 第{current_frame}帧被硬直锁定！")
                    p1_action = None
                else:
                    print(f"💥 {self.player1.name} 硬直中使用爆血！")
            
            if self.player2.is_frame_locked(self.combat.turn, current_frame):
                if p2_action != 'burst':
                    print(f"🔒 {self.player2.name} 第{current_frame}帧被硬直锁定！")
                    p2_action = None
                else:
                    print(f"💥 {self.player2.name} 硬直中使用爆血！")
            
            if self.player1.actions_cancelled and p1_action:
                print(f"⛔ {self.player1.name} 行动已被取消！")
                p1_action = None
            
            if self.player2.actions_cancelled and p2_action:
                print(f"⛔ {self.player2.name} 行动已被取消！")
                p2_action = None
            
            if self.player1.controlled and p1_action:
                if p1_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player1.name} 被控制，只能使用防御或爆血！")
                    p1_action = None
            
            if self.player2.controlled and p2_action:
                if p2_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player2.name} 被控制，只能使用防御或爆血！")
                    p2_action = None
            
            self.combat._execute_frame(p1_action, p2_action, current_frame)
            
            if current_frame == 2:
                self.player1.update_turn_status()
                self.player2.update_turn_status()
            
            output = captured_output.getvalue()
            frame_messages = [line for line in output.split('\n') if line.strip()]
            
            if frame_idx == 0:
                self.battle_messages = frame_messages
            else:
                self.battle_messages.extend(frame_messages)
            
        finally:
            sys.stdout = old_stdout

    def update(self):
        """更新游戏状态"""
        if self.game_state == "frame_executing":
            if self.frame_delay_timer == 0:
                self.execute_current_frame()
            
            self.frame_delay_timer += 1
            
            if self.frame_delay_timer >= FRAME_DELAY:
                self.frame_delay_timer = 0
                self.current_frame_index += 1
                
                if self.current_frame_index >= 2:
                    if not self.player1.is_alive() or not self.player2.is_alive():
                        self.game_state = "game_over"
                    else:
                        self.game_state = "turn_delay"
                        self.turn_delay_timer = 0
        
        elif self.game_state == "turn_delay":
            self.turn_delay_timer += 1
            
            if self.turn_delay_timer >= EXECUTE_DELAY_FRAMES:
                self.reset_for_next_turn()

    def reset_for_next_turn(self):
        """重置为下一回合"""
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"

    def reset_game(self):
        """重置游戏"""
        self.player1 = Player(PLAYER1_NAME, position=PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, position=PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.reset_for_next_turn()
        self.battle_messages = []

    def run(self):
        """主循环"""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_r and self.game_state == "game_over":
                        self.reset_game()

                    elif self.game_state == "input":
                        self.handle_input(event)

            self.update()

            self.screen.fill(WHITE)
            
            self.draw_header()
            self.draw_grid()
            self.draw_player(self.player1, PLAYER1_COLOR)
            self.draw_player(self.player2, PLAYER2_COLOR)
            self.draw_battle_messages()

            if self.game_state == "input":
                self.draw_key_hints()
                self.draw_game_mechanics()
                self.draw_input_status()
                self.draw_skill_tooltip()

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