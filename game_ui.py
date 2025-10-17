"""
game_ui.py
可视化界面 - 完整版
支持：日志历史浏览、简洁/详细日志切换
"""

import pygame
import sys
import io
from player import Player
from combat_manager import CombatManager
from config import *
from game_data import ACTION_KEY_MAP, ACTION_DISPLAY_NAMES, KEY_HINTS, SKILL_DESCRIPTIONS, GAME_MECHANICS


class GameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(UI_TEXT['title'])
        self.clock = pygame.time.Clock()

        self.font = self._load_font(28)
        self.small_font = self._load_font(22)
        self.large_font = self._load_font(48)
        self.tiny_font = self._load_font(16)

        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)

        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1

        self.action_map = ACTION_KEY_MAP
        self.action_names = ACTION_DISPLAY_NAMES

        self.game_state = "input"
        self.battle_messages = []
        
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.turn_delay_timer = 0
        self.p1_final_actions = []
        self.p2_final_actions = []
        
        self.hovered_skill = None
        self.hovered_mechanic = None
        
        # 日志系统
        self.viewing_turn = 0
        self.is_viewing_history = False
        self.simple_log_mode = False

    def _load_font(self, size):
        import os
        fonts = []
        if sys.platform == "win32":
            fonts = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]
        elif sys.platform == "darwin":
            fonts = ["/System/Library/Fonts/PingFang.ttc"]
        else:
            fonts = ["/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
        
        for f in fonts:
            if os.path.exists(f):
                try:
                    return pygame.font.Font(f, size)
                except:
                    pass
        return pygame.font.Font(None, size)

    def _extract_simple_log(self, messages):
        """
        提取简易日志 - 格式：
        第X回合 距离: Y格
        第1帧: Alice[行动] Bob[行动] → Alice HP X Bob HP Y
        第2帧: Alice[行动] Bob[行动] → Alice HP X Bob HP Y
        """
        simple = []
        current_frame = None
        frame_actions = {'alice': None, 'bob': None}
        frame_results = {'alice': None, 'bob': None}
        
        for msg in messages:
            msg_clean = msg.replace('=', '').strip()
            if not msg_clean:
                continue
            
            # 回合信息
            if "回合" in msg and "距离:" in msg:
                if current_frame is not None:
                    # 保存上一帧
                    self._append_frame_summary(simple, current_frame, frame_actions, frame_results)
                
                simple.append(msg_clean)
                current_frame = None
                continue
            
            # 帧标记
            if "---" in msg and "帧" in msg:
                if current_frame is not None:
                    self._append_frame_summary(simple, current_frame, frame_actions, frame_results)
                
                # 提取帧数
                frame_num = msg.replace('-', '').replace('---', '').strip()
                current_frame = frame_num
                frame_actions = {'alice': None, 'bob': None}
                frame_results = {'alice': None, 'bob': None}
                continue
            
            # 提取行动
            if "⚔️" in msg or "攻击" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "攻击"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "攻击"
            elif "💥" in msg or "爆血" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "爆血"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "爆血"
            elif "✨" in msg or "蓄力" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "蓄力"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "蓄力"
            elif "📍" in msg and "控制" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "控制"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "控制"
            elif "🤼" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "抱摔"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "抱摔"
            elif "🌪️" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "投掷"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "投掷"
            elif "🛡️" in msg:
                if "反击" in msg:
                    if PLAYER1_NAME in msg:
                        frame_actions['alice'] = "反击"
                    if PLAYER2_NAME in msg:
                        frame_actions['bob'] = "反击"
                elif "防御" in msg:
                    if PLAYER1_NAME in msg:
                        frame_actions['alice'] = "防御"
                    if PLAYER2_NAME in msg:
                        frame_actions['bob'] = "防御"
            elif "✅" in msg and "移动" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "移动"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "移动"
            elif "🏃" in msg and "获得" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "冲刺"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "冲刺"
            elif "❌" in msg and "移动失败" in msg:
                if PLAYER1_NAME in msg:
                    frame_actions['alice'] = "移动失败"
                if PLAYER2_NAME in msg:
                    frame_actions['bob'] = "移动失败"
            
            # 提取结果（HP变化）
            if "💔" in msg and "受" in msg and "伤" in msg:
                if PLAYER1_NAME in msg:
                    # 格式: "💔 Alice 受X伤，HP: Y/Z"
                    parts = msg.split("HP:")
                    if len(parts) > 1:
                        hp_info = parts[1].strip()
                        frame_results['alice'] = f"HP {hp_info}"
                if PLAYER2_NAME in msg:
                    parts = msg.split("HP:")
                    if len(parts) > 1:
                        hp_info = parts[1].strip()
                        frame_results['bob'] = f"HP {hp_info}"
            elif "🛡️" in msg and "完全格挡" in msg:
                if PLAYER1_NAME in msg:
                    frame_results['alice'] = "格挡"
                if PLAYER2_NAME in msg:
                    frame_results['bob'] = "格挡"
        
        # 保存最后一帧
        if current_frame is not None:
            self._append_frame_summary(simple, current_frame, frame_actions, frame_results)
        
        return simple if simple else ["（无信息）"]
    
    def _append_frame_summary(self, simple, frame_label, actions, results):
        """添加帧摘要到简易日志"""
        alice_act = actions.get('alice') or "—"
        bob_act = actions.get('bob') or "—"
        alice_res = results.get('alice') or ""
        bob_res = results.get('bob') or ""
        
        line = f"{frame_label}: {PLAYER1_NAME}[{alice_act}] {PLAYER2_NAME}[{bob_act}]"
        if alice_res or bob_res:
            line += f" → {alice_res} | {bob_res}"
        
        simple.append(line)

    def draw_grid(self):
        for i in range(MAP_SIZE):
            x = GRID_START_X + i * CELL_WIDTH
            y = GRID_START_Y
            pygame.draw.rect(self.screen, GRAY, (x, y, CELL_WIDTH, CELL_HEIGHT), 2)
            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            self.screen.blit(text, (x + CELL_WIDTH//2 - 10, y + 15))

    def draw_player(self, player, color):
        """绘制玩家，处理重叠情况"""
        distance = self.combat.get_distance()
        
        # 如果距离为0且被控制，不显示被控制者（只显示控制者）
        if distance == 0 and player.controlled:
            return
        
        x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
        y = GRID_START_Y + CELL_HEIGHT // 2
        
        # 如果距离为0且是控制者，控制者显示在上层
        if distance == 0 and not player.controlled:
            y -= 15  # 稍微往上移动
        
        pygame.draw.circle(self.screen, color, (x, y), PLAYER_RADIUS)
        
        # 被控制状态显示
        if player.controlled:
            pygame.draw.circle(self.screen, YELLOW, (x, y), PLAYER_RADIUS + 5, 3)
            # 在旁边显示"被控制"文字
            status_text = self.tiny_font.render("⛓️被控", True, YELLOW)
            self.screen.blit(status_text, (x - 15, y + 45))
        
        # 蓄力显示
        if player.charge_level > 0:
            c = YELLOW if player.charge_level == 1 else ORANGE
            pygame.draw.circle(self.screen, c, (x, y), PLAYER_RADIUS + 8, 2)
        
        # 玩家名字
        text = self.small_font.render(player.name, True, BLACK)
        self.screen.blit(text, (x - 20, y - 10))
        
        # 血条
        hx = x - HP_BAR_WIDTH // 2
        hy = y + HP_BAR_OFFSET_Y
        pygame.draw.rect(self.screen, DARK_GRAY, (hx, hy, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        
        hp_ratio = player.hp / player.max_hp
        hp_w = int(HP_BAR_WIDTH * hp_ratio)
        hp_color = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
        pygame.draw.rect(self.screen, hp_color, (hx, hy, hp_w, HP_BAR_HEIGHT))
        
        hp_text = self.tiny_font.render(f"{player.hp}/{player.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (x - 15, hy))
        
        # 连击数显示
        if player.combo_count > 0:
            combo_text = f"连击{player.combo_count}/3"
            t = self.tiny_font.render(combo_text, True, ORANGE)
            tr = t.get_rect(center=(x, y + COMBO_DISPLAY_OFFSET_Y))
            pygame.draw.rect(self.screen, BLACK, tr.inflate(8, 4), border_radius=3)
            self.screen.blit(t, tr)

    def draw_header(self):
        text = self.large_font.render(f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格", True, BLACK)
        self.screen.blit(text, (WINDOW_WIDTH//2 - 200, 50))
        
        if self.game_state == "frame_executing":
            t = self.font.render(f"▶ 执行第 {self.current_frame_index + 1} 帧", True, ORANGE)
            self.screen.blit(t, (WINDOW_WIDTH//2 - 100, 100))
            
            px = WINDOW_WIDTH//2 - 100
            py = 130
            pygame.draw.rect(self.screen, GRAY, (px, py, 200, 10))
            prog = int(200 * self.frame_delay_timer / FRAME_DELAY)
            pygame.draw.rect(self.screen, GREEN, (px, py, prog, 10))

    def draw_key_hints(self):
        x, y = GRID_START_X, GRID_START_Y + CELL_HEIGHT + 40
        self.screen.blit(self.font.render("按键说明", True, BLACK), (x, y))
        
        y += 40
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x-10, y-5, 260, len(KEY_HINTS)*24+10), border_radius=5)
        
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill = None
        
        for i, (line, skill) in enumerate(KEY_HINTS):
            ly = y + i * 24
            rect = pygame.Rect(x-8, ly-2, 256, 22)
            hover = rect.collidepoint(mouse_pos)
            
            if hover:
                pygame.draw.rect(self.screen, YELLOW, rect, border_radius=3)
                self.hovered_skill = skill
            
            t = self.tiny_font.render(line, True, BLACK if hover else DARK_GRAY)
            self.screen.blit(t, (x, ly))

    def draw_mechanics(self):
        x, y = GRID_START_X + 280, GRID_START_Y + CELL_HEIGHT + 40
        self.screen.blit(self.font.render("游戏机制", True, BLACK), (x, y))
        
        y += 40
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_mechanic = None
        
        for i, (key, info) in enumerate(GAME_MECHANICS.items()):
            my = y + i * 30
            rect = pygame.Rect(x-8, my-2, 180, 26)
            hover = rect.collidepoint(mouse_pos)
            
            bg = LIGHT_BLUE if i == 0 else LIGHT_RED
            if hover:
                bg = YELLOW
                self.hovered_mechanic = key
            
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            t = self.small_font.render(info['name'], True, BLACK if hover else DARK_GRAY)
            self.screen.blit(t, (x, my))

    def draw_tooltip(self):
        info = None
        if self.hovered_skill and self.hovered_skill in SKILL_DESCRIPTIONS:
            info = SKILL_DESCRIPTIONS[self.hovered_skill]
        elif self.hovered_mechanic:
            info = GAME_MECHANICS[self.hovered_mechanic]
        
        if info:
            x, y = GRID_START_X + 480, GRID_START_Y + CELL_HEIGHT + 80
            h = 40 + len(info['desc']) * 18
            
            pygame.draw.rect(self.screen, (100,100,100), (x+3, y+3, 360, h), border_radius=8)
            pygame.draw.rect(self.screen, BLACK, (x, y, 360, h), border_radius=8)
            pygame.draw.rect(self.screen, (250,250,250), (x+2, y+2, 356, h-4), border_radius=6)
            
            self.screen.blit(self.small_font.render(info['name'], True, BLUE), (x+10, y+8))
            pygame.draw.line(self.screen, GRAY, (x+10, y+33), (x+350, y+33))
            
            dy = y + 38
            for line in info['desc']:
                if line:
                    self.screen.blit(self.tiny_font.render(line, True, BLACK), (x+12, dy))
                dy += 18

    def draw_messages(self):
        """绘制战斗日志"""
        pygame.draw.rect(self.screen, LIGHT_GRAY, (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT), 2, border_radius=10)
        
        # 标题
        title_text = "战斗日志"
        if self.simple_log_mode:
            title_text += " (简洁)"
        
        if self.is_viewing_history and self.viewing_turn > 0:
            title_text += f" - 回合{self.viewing_turn}"
            title_color = ORANGE
        else:
            title_color = BLACK
        
        self.screen.blit(self.font.render(title_text, True, title_color), (MESSAGE_BOX_X+10, MESSAGE_BOX_Y+10))
        pygame.draw.line(self.screen, DARK_GRAY, (MESSAGE_BOX_X+10, MESSAGE_BOX_Y+45), (MESSAGE_BOX_X+MESSAGE_BOX_WIDTH-10, MESSAGE_BOX_Y+45), 2)
        
        # 获取消息
        if self.is_viewing_history and self.viewing_turn > 0:
            messages = self.combat.get_turn_log(self.viewing_turn)
        else:
            messages = self.battle_messages
        
        # 简洁模式
        if self.simple_log_mode:
            messages = self._extract_simple_log(messages)
        
        # 显示消息
        y = MESSAGE_BOX_Y + 55
        for msg in messages[-28:]:
            clean = msg.replace('=','').strip()
            if not clean:
                y += 5
                continue
            
            color = BLACK
            if '💔' in msg: color = RED
            elif '✨' in msg: color = PURPLE
            elif '⚔️' in msg: color = BLUE
            elif '📍' in msg or '硬直' in msg: color = ORANGE
            elif '❌' in msg: color = DARK_GRAY
            elif '✅' in msg: color = GREEN
            elif '第' in msg and '帧' in msg: color = BLUE
            
            t = self.tiny_font.render(clean, True, color)
            if t.get_width() > MESSAGE_BOX_WIDTH - 20:
                while len(clean) > 0 and t.get_width() > MESSAGE_BOX_WIDTH - 20:
                    clean = clean[:-1]
                    t = self.tiny_font.render(clean + "...", True, color)
            
            self.screen.blit(t, (MESSAGE_BOX_X+10, y))
            y += 19
            if y > MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 80:
                break
        
        # 底部提示
        hint_y = MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 65
        pygame.draw.line(self.screen, DARK_GRAY, (MESSAGE_BOX_X+10, hint_y-5), (MESSAGE_BOX_X+MESSAGE_BOX_WIDTH-10, hint_y-5), 1)
        
        t = self.tiny_font.render("TAB - 切换简洁/详细", True, DARK_GRAY)
        self.screen.blit(t, (MESSAGE_BOX_X+10, hint_y))
        
        if len(self.combat.turn_logs) > 0:
            t = self.tiny_font.render("← → 浏览历史", True, DARK_GRAY)
            self.screen.blit(t, (MESSAGE_BOX_X+10, hint_y+18))
            
            if self.is_viewing_history:
                view_text = f"查看：回合{self.viewing_turn}/{self.combat.turn}"
                color = ORANGE
            else:
                view_text = f"当前：回合{self.combat.turn}（最新）"
                color = GREEN
            
            t = self.tiny_font.render(view_text, True, color)
            self.screen.blit(t, (MESSAGE_BOX_X+10, hint_y+36))

    def draw_selection(self):
        x, y = GRID_START_X, GRID_START_Y + CELL_HEIGHT + 280
        self.screen.blit(self.font.render("当前选择", True, BLACK), (x, y))
        
        y += 45
        next_turn = self.combat.turn + 1
        
        # P1
        f1, c1 = self._get_display(self.player1, 0, self.p1_actions, self.p1_locked, next_turn)
        f2, c2 = self._get_display(self.player1, 1, self.p1_actions, self.p1_locked, next_turn)
        
        if self.current_player == 1 and not self.p1_locked:
            p1_text = f"{PLAYER1_NAME}: [{f1}] [{f2}]"
            bg = c2 if len(self.p1_actions) >= 1 else c1
        elif self.p1_locked:
            p1_text = f"{PLAYER1_NAME}: [✓✓✓] [✓✓✓]"
            bg = LIGHT_RED
        else:
            p1_text = f"{PLAYER1_NAME}: [***] [***]"
            bg = LIGHT_RED
        
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 350, 35), border_radius=5)
        self.screen.blit(self.small_font.render(p1_text, True, BLACK), (x, y))
        
        # P2
        y += 45
        f1, c1 = self._get_display(self.player2, 0, self.p2_actions, self.p2_locked, next_turn)
        f2, c2 = self._get_display(self.player2, 1, self.p2_actions, self.p2_locked, next_turn)
        
        if self.current_player == 2 and not self.p2_locked:
            p2_text = f"{PLAYER2_NAME}:   [{f1}] [{f2}]"
            bg = c2 if len(self.p2_actions) >= 1 else c1
        elif self.p2_locked:
            p2_text = f"{PLAYER2_NAME}:   [✓✓✓] [✓✓✓]"
            bg = LIGHT_BLUE
        else:
            p2_text = f"{PLAYER2_NAME}:   [***] [***]"
            bg = LIGHT_BLUE
        
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 350, 35), border_radius=5)
        self.screen.blit(self.small_font.render(p2_text, True, BLACK), (x, y))
        
        # 提示
        y += 45
        hint, color = self._get_hint()
        self.screen.blit(self.small_font.render(hint, True, color), (x, y))
        
        y += 30
        self.screen.blit(self.tiny_font.render("SPACE确认 | Backspace撤销", True, ORANGE), (x, y))

    def _get_display(self, player, idx, actions, locked, next_turn):
        if idx < len(actions):
            if actions[idx] is None:
                return "📍STUN", PURPLE
            elif actions[idx] == 'burst':
                return "Burst💥", ORANGE
            else:
                return self.action_names[actions[idx]], ORANGE if len(actions)==2 else YELLOW
        
        if player.is_frame_locked(next_turn, idx+1):
            return "📍STUN", PURPLE
        
        return ("✓✓✓" if locked else "____"), (LIGHT_GRAY if locked else YELLOW)

    def _get_hint(self):
        if self.p1_locked and self.p2_locked:
            return (UI_TEXT['both_confirmed'], ORANGE)
        if self.p1_locked:
            return (UI_TEXT['waiting_bob'], BLUE)
        if self.p2_locked:
            return (UI_TEXT['waiting_alice'], RED)
        
        player = self.player1 if self.current_player == 1 else self.player2
        actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        next_turn = self.combat.turn + 1
        
        if player.controlled:
            return (UI_TEXT['controlled_limit'], RED)
        
        for i in range(2):
            if i >= len(actions):
                if player.is_frame_locked(next_turn, i+1):
                    return (f"😵 第{i+1}帧硬直，可用O", PURPLE)
                else:
                    key = 'alice_turn' if self.current_player == 1 else 'bob_turn'
                    return (UI_TEXT[key].format(frame=i+1), GREEN)
        
        return (UI_TEXT['selection_complete'], ORANGE)

    def draw_game_over(self):
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        s.set_alpha(200)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))
        
        winner = self.combat.get_winner()
        text = "平局！" if winner == "平局" else f"{winner} 获胜！"
        
        t = self.large_font.render(text, True, YELLOW)
        self.screen.blit(t, (WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 50))
        
        h = self.font.render("按 R 重新开始 | ESC 退出", True, WHITE)
        self.screen.blit(h, (WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 50))

    def handle_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            if self.current_player == 1 and not self.p1_locked and self.p1_actions:
                removed = self.p1_actions.pop()
                print(f"↩️ Alice撤销: {self.action_names.get(removed, '???')}")
            elif self.current_player == 2 and not self.p2_locked and self.p2_actions:
                removed = self.p2_actions.pop()
                print(f"↩️ Bob撤销: {self.action_names.get(removed, '???')}")
            return
        
        if event.key == pygame.K_SPACE:
            self._confirm()
            return
        
        key = pygame.key.name(event.key)
        if key in self.action_map:
            player = self.player1 if self.current_player == 1 else self.player2
            actions = self.p1_actions if self.current_player == 1 else self.p2_actions
            locked = self.p1_locked if self.current_player == 1 else self.p2_locked
            name = PLAYER1_NAME if self.current_player == 1 else PLAYER2_NAME
            
            if not locked:
                self._add_action(player, actions, key, name)

    def _add_action(self, player, actions, key, name):
        next_turn = self.combat.turn + 1
        action = self.action_map[key]
        
        for i in range(2):
            if i < len(actions):
                continue
            
            locked = player.is_frame_locked(next_turn, i+1)
            
            if player.controlled and action not in ['defend', 'burst']:
                print(f"⛓️ {name}被控制，只能S或O！")
                return
            
            if locked:
                if action == 'burst':
                    while len(actions) < i:
                        actions.append(None)
                    actions.append(action)
                    print(f"{name}选择第{i+1}帧(硬直): {self.action_names[action]}")
                    return
                else:
                    continue
            
            while len(actions) < i:
                actions.append(None)
            
            actions.append(action)
            print(f"{name}选择第{i+1}帧: {self.action_names[action]}")
            return
        
        print(f"⚠ {name}已选2个")

    def _confirm(self):
        next_turn = self.combat.turn + 1
        
        if self.current_player == 1 and not self.p1_locked:
            ready = True
            for i in range(2):
                if i < len(self.p1_actions):
                    continue
                if not self.player1.is_frame_locked(next_turn, i+1):
                    ready = False
                    break
            
            if ready:
                for i in range(2):
                    if self.player1.is_frame_locked(next_turn, i+1) and i >= len(self.p1_actions):
                        while len(self.p1_actions) < i:
                            self.p1_actions.append(None)
                        self.p1_actions.append(None)
                
                self.p1_locked = True
                self.current_player = 2
                print(f"✓ Alice已确定")
            else:
                print("⚠ Alice还需要输入")
        
        elif self.current_player == 2 and not self.p2_locked:
            ready = True
            for i in range(2):
                if i < len(self.p2_actions):
                    continue
                if not self.player2.is_frame_locked(next_turn, i+1):
                    ready = False
                    break
            
            if ready:
                for i in range(2):
                    if self.player2.is_frame_locked(next_turn, i+1) and i >= len(self.p2_actions):
                        while len(self.p2_actions) < i:
                            self.p2_actions.append(None)
                        self.p2_actions.append(None)
                
                self.p2_locked = True
                print(f"✓ Bob已确定")
                if self.p1_locked:
                    self.start_execution()
            else:
                print("⚠ Bob还需要输入")

    def start_execution(self):
        self.game_state = "frame_executing"
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.battle_messages = []
        
        self.p1_final_actions = self._prepare(self.player1, self.p1_actions)
        self.p2_final_actions = self._prepare(self.player2, self.p2_actions)

    def _prepare(self, player, actions):
        next_turn = self.combat.turn + 1
        final = []
        for i in range(2):
            if player.is_frame_locked(next_turn, i+1):
                if i < len(actions) and actions[i] == 'burst':
                    final.append('burst')
                else:
                    final.append(None)
            elif i < len(actions):
                final.append(actions[i])
            else:
                final.append(None)
        return final

    def execute_frame(self):
        idx = self.current_frame_index
        frame = idx + 1
        
        if idx == 0:
            self.combat.turn += 1
            self.combat.p1.clear_old_locks(self.combat.turn)
            self.combat.p2.clear_old_locks(self.combat.turn)
            self.combat.current_turn_messages = []
        
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            if idx == 0:
                print(f"\n{'='*60}")
                print(f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格")
                self.combat.p1.show_status()
                self.combat.p2.show_status()
                print('='*60)
            
            print(f"\n--- 第 {frame} 帧 ---")
            
            self.combat.p1.reset_frame()
            self.combat.p2.reset_frame()
            
            p1_act = self.p1_final_actions[idx]
            p2_act = self.p2_final_actions[idx]
            
            p1_act = self.combat._preprocess(self.combat.p1, p1_act, frame)
            p2_act = self.combat._preprocess(self.combat.p2, p2_act, frame)
            
            self.combat._execute_frame(p1_act, p2_act, frame)
            
            output = sys.stdout.getvalue()
            msgs = [l for l in output.split('\n') if l.strip()]
            
            if idx == 0:
                self.battle_messages = msgs
                self.combat.current_turn_messages = msgs.copy()
            else:
                self.battle_messages.extend(msgs)
                self.combat.current_turn_messages.extend(msgs)
            
            if idx == 1:
                self.combat.save_turn_log(self.combat.current_turn_messages)
        finally:
            sys.stdout = old_stdout

    def update(self):
        if self.game_state == "frame_executing":
            if self.frame_delay_timer == 0:
                self.execute_frame()
            
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
                self.reset_turn()

    def reset_turn(self):
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"
        self.viewing_turn = 0
        self.is_viewing_history = False

    def reset_game(self):
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.reset_turn()
        self.battle_messages = []
        self.viewing_turn = 0
        self.is_viewing_history = False

    def _navigate_history(self, direction):
        if len(self.combat.turn_logs) == 0:
            return
        
        if direction == 'left':
            if self.viewing_turn == 0:
                self.viewing_turn = self.combat.turn
                self.is_viewing_history = True
            elif self.viewing_turn > 1:
                self.viewing_turn -= 1
            print(f"📖 查看回合{self.viewing_turn}")
        
        elif direction == 'right':
            if self.is_viewing_history:
                if self.viewing_turn < self.combat.turn:
                    self.viewing_turn += 1
                    print(f"📖 查看回合{self.viewing_turn}")
                
                if self.viewing_turn == self.combat.turn:
                    self.viewing_turn = 0
                    self.is_viewing_history = False
                    print(f"📖 返回最新")

    def run(self):
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
                    
                    # TAB切换日志模式
                    elif event.key == pygame.K_TAB:
                        self.simple_log_mode = not self.simple_log_mode
                        mode = "简洁" if self.simple_log_mode else "详细"
                        print(f"📋 切换到{mode}日志")
                    
                    # 左右箭头浏览历史
                    elif event.key == pygame.K_LEFT:
                        self._navigate_history('left')
                    elif event.key == pygame.K_RIGHT:
                        self._navigate_history('right')
                    
                    # 输入阶段
                    elif self.game_state == "input":
                        self.handle_input(event)
            
            self.update()
            
            self.screen.fill(WHITE)
            self.draw_header()
            self.draw_grid()
            self.draw_player(self.player1, PLAYER1_COLOR)
            self.draw_player(self.player2, PLAYER2_COLOR)
            self.draw_messages()
            
            if self.game_state == "input":
                self.draw_key_hints()
                self.draw_mechanics()
                self.draw_selection()
                self.draw_tooltip()
            
            if self.game_state == "game_over":
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    game = GameUI()
    game.run()


if __name__ == "__main__":
    main()