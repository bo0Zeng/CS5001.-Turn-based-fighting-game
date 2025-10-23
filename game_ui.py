"""
game_ui.py
可视化界面 - 完整版（兼容7阶段状态化重构版）
支持：日志历史浏览、简洁/详细日志切换、自动换行

修复：
1. 改进简洁日志提取逻辑
2. 更清晰地显示行动和结果
3. 添加关键状态变化（硬直、控制、连击等）
4. 优化格式和可读性
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
        """提取简洁日志（改进版）"""
        simple = []
        
        # 解析回合信息
        turn_info = None
        frames = {}  # {frame_num: {'p1': {}, 'p2': {}}}
        current_frame = None
        
        for msg in messages:
            msg_clean = msg.strip()
            if not msg_clean or '=' in msg:
                continue
            
            # 回合标题
            if "回合" in msg and "距离:" in msg:
                turn_info = msg_clean
                continue
            
            # 帧标记
            if "第" in msg and "帧" in msg and "---" in msg:
                frame_num = 1 if "第 1 帧" in msg else 2
                current_frame = frame_num
                if current_frame not in frames:
                    frames[current_frame] = {
                        'p1': {'action': None, 'result': []},
                        'p2': {'action': None, 'result': []}
                    }
                continue
            
            if current_frame is None:
                continue
            
            frame_data = frames[current_frame]
            
            # 提取行动和结果
            self._parse_message_for_simple_log(msg_clean, frame_data)
        
        # 生成简洁日志
        if turn_info:
            simple.append(turn_info)
            simple.append("")
        
        for frame_num in sorted(frames.keys()):
            frame_data = frames[frame_num]
            simple.append(f"帧{frame_num}:")
            
            # P1行动
            p1_line = self._format_player_action(
                PLAYER1_NAME, 
                frame_data['p1']['action'], 
                frame_data['p1']['result']
            )
            simple.append(p1_line)
            
            # P2行动
            p2_line = self._format_player_action(
                PLAYER2_NAME, 
                frame_data['p2']['action'], 
                frame_data['p2']['result']
            )
            simple.append(p2_line)
            
            simple.append("")
        
        return simple if simple else ["（无信息）"]
    
    def _parse_message_for_simple_log(self, msg, frame_data):
        """解析消息并填充到frame_data"""
        p1_name = PLAYER1_NAME
        p2_name = PLAYER2_NAME
        
        # 识别行动（阶段1）
        # 优先处理不含"尝试/姿态"关键词的行动
        if "投掷" in msg and "🌪️" in msg:
            # 🌪️ Red 投掷 Blue！
            if p1_name in msg and msg.index(p1_name) < msg.index("投掷"):
                frame_data['p1']['action'] = "投掷"
            if p2_name in msg and msg.index(p2_name) < msg.index("投掷"):
                frame_data['p2']['action'] = "投掷"
        elif "抱摔" in msg and "🤼" in msg:
            # 🤼 Red 抱摔 Blue！
            if p1_name in msg and msg.index(p1_name) < msg.index("抱摔"):
                frame_data['p1']['action'] = "抱摔"
            if p2_name in msg and msg.index(p2_name) < msg.index("抱摔"):
                frame_data['p2']['action'] = "抱摔"
        elif "爆血" in msg and "💥" in msg:
            # 💥 Red 爆血！
            if p1_name in msg:
                frame_data['p1']['action'] = "爆血"
            if p2_name in msg:
                frame_data['p2']['action'] = "爆血"
        elif "尝试" in msg or "姿态" in msg or "移动" in msg:
            if "攻击" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "攻击"
                if p2_name in msg:
                    frame_data['p2']['action'] = "攻击"
            elif "蓄力" in msg:
                if p1_name in msg:
                    level = "2" if "蓄力2" in msg else "1"
                    frame_data['p1']['action'] = f"蓄力{level}"
                if p2_name in msg:
                    level = "2" if "蓄力2" in msg else "1"
                    frame_data['p2']['action'] = f"蓄力{level}"
            elif "控制" in msg and "尝试" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "控制"
                if p2_name in msg:
                    frame_data['p2']['action'] = "控制"
            elif "防御" in msg and "姿态" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "防御"
                if p2_name in msg:
                    frame_data['p2']['action'] = "防御"
            elif "反击" in msg and "姿态" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "反击"
                if p2_name in msg:
                    frame_data['p2']['action'] = "反击"
            elif "冲刺" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "冲刺"
                if p2_name in msg:
                    frame_data['p2']['action'] = "冲刺"
            elif "移动" in msg and "→" in msg:
                if p1_name in msg:
                    frame_data['p1']['action'] = "移动"
                if p2_name in msg:
                    frame_data['p2']['action'] = "移动"
        
        # 识别结果（阶段3-6）
        # 命中/失败
        if "命中" in msg or "成功" in msg:
            if p1_name in msg:
                if "攻击命中" in msg:
                    frame_data['p1']['result'].append("✓攻击")
                elif "控制成功" in msg:
                    frame_data['p1']['result'].append("✓控制")
                elif "反击成功" in msg:
                    frame_data['p1']['result'].append("✓反击")
                elif "闪避" in msg and "成功" in msg:
                    frame_data['p1']['result'].append("✓闪避")
            if p2_name in msg:
                if "攻击命中" in msg:
                    frame_data['p2']['result'].append("✓攻击")
                elif "控制成功" in msg:
                    frame_data['p2']['result'].append("✓控制")
                elif "反击成功" in msg:
                    frame_data['p2']['result'].append("✓反击")
                elif "闪避" in msg and "成功" in msg:
                    frame_data['p2']['result'].append("✓闪避")
        
        if "未命中" in msg or "失败" in msg:
            if p1_name in msg:
                if "攻击未命中" in msg:
                    frame_data['p1']['result'].append("✗攻击miss")
                elif "控制未命中" in msg:
                    frame_data['p1']['result'].append("✗控制miss")
                elif "反击失败" in msg:
                    frame_data['p1']['result'].append("✗反击失败")
            if p2_name in msg:
                if "攻击未命中" in msg:
                    frame_data['p2']['result'].append("✗攻击miss")
                elif "控制未命中" in msg:
                    frame_data['p2']['result'].append("✗控制miss")
                elif "反击失败" in msg:
                    frame_data['p2']['result'].append("✗反击失败")
        
        # 伤害
        if "💔" in msg and "受" in msg and "伤" in msg:
            parts = msg.split("受")
            if len(parts) > 1:
                damage_part = parts[1].split("伤")[0]
                if p1_name in msg:
                    frame_data['p1']['result'].append(f"受{damage_part}伤")
                if p2_name in msg:
                    frame_data['p2']['result'].append(f"受{damage_part}伤")
        
        # 格挡
        if "完全格挡" in msg:
            if p1_name in msg:
                frame_data['p1']['result'].append("完全格挡")
            if p2_name in msg:
                frame_data['p2']['result'].append("完全格挡")
        
        # 硬直
        if "硬直" in msg and "😵" in msg:
            if p1_name in msg:
                frame_data['p1']['result'].append("⚠硬直")
            if p2_name in msg:
                frame_data['p2']['result'].append("⚠硬直")
        
        # 蓄力成功/失败
        if "获得蓄力" in msg:
            if p1_name in msg:
                level = msg.split("蓄力")[1][0] if "蓄力" in msg else "?"
                frame_data['p1']['result'].append(f"✓蓄力{level}")
            if p2_name in msg:
                level = msg.split("蓄力")[1][0] if "蓄力" in msg else "?"
                frame_data['p2']['result'].append(f"✓蓄力{level}")
        
        if "蓄力被打断" in msg:
            if p1_name in msg:
                frame_data['p1']['result'].append("✗蓄力断")
            if p2_name in msg:
                frame_data['p2']['result'].append("✗蓄力断")
        
        # 连击
        if "连续被击中" in msg:
            if p1_name in msg and "/" in msg:
                combo = msg.split("连续被击中")[1].strip().split()[0]
                frame_data['p1']['result'].append(f"连击{combo}")
            if p2_name in msg and "/" in msg:
                combo = msg.split("连续被击中")[1].strip().split()[0]
                frame_data['p2']['result'].append(f"连击{combo}")
        
        # 被控制
        if "被" in msg and "控制" in msg and ("🔒" in msg or "✅" in msg):
            if p1_name in msg and "被" in msg:
                frame_data['p1']['result'].append("⛓被控")
            if p2_name in msg and "被" in msg:
                frame_data['p2']['result'].append("⛓被控")
        
        # 冲刺buff
        if "获得冲刺buff" in msg:
            if p1_name in msg:
                frame_data['p1']['result'].append("↗冲刺+1")
            if p2_name in msg:
                frame_data['p2']['result'].append("↗冲刺+1")
        
        # 位置移动
        if "→" in msg and "移动：" in msg:
            parts = msg.split("移动：")
            if len(parts) > 1 and "→" in parts[1]:
                pos_info = parts[1].split()[0]
                if p1_name in msg:
                    frame_data['p1']['result'].append(f"→{pos_info}")
                if p2_name in msg:
                    frame_data['p2']['result'].append(f"→{pos_info}")
    
    def _format_player_action(self, name, action, results):
        """格式化玩家行动和结果"""
        if action is None:
            action = "待机"
        
        line = f"  {name}[{action}]"
        
        if results:
            line += " → " + " ".join(results)
        
        return line

    def draw_grid(self):
        """绘制地图网格"""
        for i in range(MAP_SIZE):
            x = GRID_START_X + i * CELL_WIDTH
            y = GRID_START_Y
            pygame.draw.rect(self.screen, GRAY, (x, y, CELL_WIDTH, CELL_HEIGHT), 2)
            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            self.screen.blit(text, (x + CELL_WIDTH//2 - 10, y + 15))

    def draw_player(self, player, color):
        """绘制玩家"""
        distance = self.combat.get_distance()
        opponent = self.player2 if player == self.player1 else self.player1
    
        # 如果距离为0且自己被控制，不绘制（让控制者显示在上层）
        if distance == 0 and player.controlled:
            return
    
        x = GRID_START_X + (player.position - 1) * CELL_WIDTH + CELL_WIDTH // 2
        y = GRID_START_Y + CELL_HEIGHT // 2
    
        # 如果距离为0且自己是控制者，稍微往上移（叠加显示）
        if distance == 0 and opponent.controlled and opponent.controller == player.name:
            y -= 15
    
        pygame.draw.circle(self.screen, color, (x, y), PLAYER_RADIUS)
    
        # 被控制状态显示
        if player.controlled:
            pygame.draw.circle(self.screen, YELLOW, (x, y), PLAYER_RADIUS + 5, 3)
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
            combo_text = f"被连击{player.combo_count}/3"
            t = self.tiny_font.render(combo_text, True, ORANGE)
            tr = t.get_rect(center=(x, y + COMBO_DISPLAY_OFFSET_Y))
            pygame.draw.rect(self.screen, BLACK, tr.inflate(8, 4), border_radius=3)
            self.screen.blit(t, tr)

    def draw_header(self):
        """绘制标题"""
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
        """绘制按键说明（根据玩家状态动态显示）"""
        x, y = GRID_START_X, GRID_START_Y + CELL_HEIGHT + 40
        
        # 获取当前输入玩家和状态
        current_player = self.player1 if self.current_player == 1 else self.player2
        next_turn = self.combat.turn + 1
        
        # 检查玩家在下一回合是否被限制
        is_controlled = current_player.controlled
        is_locked_frame1 = current_player.is_frame_locked(next_turn, 1)
        is_locked_frame2 = current_player.is_frame_locked(next_turn, 2)
        
        # 确定当前要输入的帧
        current_actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        current_frame_idx = len(current_actions)  # 0=第1帧, 1=第2帧
        
        if current_frame_idx >= 2:
            # 已经选完了，显示标准提示
            key_hints = KEY_HINTS
            title = "按键说明"
            status_msg = None
        else:
            # 检查这一帧是否受限
            is_this_frame_locked = (current_frame_idx == 0 and is_locked_frame1) or \
                                   (current_frame_idx == 1 and is_locked_frame2)
            
            if is_this_frame_locked:
                # 硬直：只能爆血
                title = f"⚠️ 第{current_frame_idx+1}帧硬直"
                status_msg = "只能使用爆血（O）"
                key_hints = [
                    ("O - 爆血", 'burst'),
                ]
            elif is_controlled and current_frame_idx == 0:
                # 被控制：只能防御和爆血（只在第1帧检查）
                title = "⛓️ 被控制状态"
                status_msg = "只能使用防御（S）或爆血（O）\n其他行动将被视为无效"
                key_hints = [
                    ("S - 防御", 'defend'),
                    ("O - 爆血", 'burst'),
                ]
            else:
                # 正常状态
                title = "按键说明"
                status_msg = None
                key_hints = KEY_HINTS
        
        # 绘制标题
        title_color = ORANGE if status_msg else BLACK
        self.screen.blit(self.font.render(title, True, title_color), (x, y))
        
        y += 40
        
        # 如果有状态提示，先显示
        if status_msg:
            # 绘制警告框
            warning_lines = status_msg.split('\n')
            warning_height = len(warning_lines) * 20 + 15
            pygame.draw.rect(self.screen, (255, 240, 200), (x-10, y-5, 260, warning_height), border_radius=5)
            pygame.draw.rect(self.screen, ORANGE, (x-10, y-5, 260, warning_height), 2, border_radius=5)
            
            for i, line in enumerate(warning_lines):
                warning_text = self.tiny_font.render(line, True, RED)
                self.screen.blit(warning_text, (x, y + i * 20))
            
            y += warning_height + 10
        
        # 绘制按键提示背景
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x-10, y-5, 260, len(key_hints)*24+10), border_radius=5)
        
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill = None
        
        for i, (line, skill) in enumerate(key_hints):
            ly = y + i * 24
            rect = pygame.Rect(x-8, ly-2, 256, 22)
            hover = rect.collidepoint(mouse_pos)
            
            if hover:
                pygame.draw.rect(self.screen, YELLOW, rect, border_radius=3)
                self.hovered_skill = skill
            
            # 如果是受限状态，用绿色高亮可用按键
            text_color = GREEN if status_msg else (BLACK if hover else DARK_GRAY)
            t = self.tiny_font.render(line, True, text_color)
            self.screen.blit(t, (x, ly))

    def draw_mechanics(self):
        """绘制游戏机制"""
        x, y = GRID_START_X + 280, GRID_START_Y + CELL_HEIGHT + 40
        self.screen.blit(self.font.render("游戏机制", True, BLACK), (x, y))
        
        y += 40
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_mechanic = None
        
        for i, (key, info) in enumerate(GAME_MECHANICS.items()):
            my = y + i * 30
            rect = pygame.Rect(x-8, my-2, 180, 26)
            hover = rect.collidepoint(mouse_pos)
            
            bg_colors = [LIGHT_BLUE, LIGHT_RED, (200, 255, 200)]
            bg = bg_colors[i % len(bg_colors)]
            if hover:
                bg = YELLOW
                self.hovered_mechanic = key
            
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            t = self.small_font.render(info['name'], True, BLACK if hover else DARK_GRAY)
            self.screen.blit(t, (x, my))

    def draw_tooltip(self):
        """绘制技能提示"""
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
        
        if self.is_viewing_history and self.viewing_turn > 0:
            messages = self.combat.get_turn_log(self.viewing_turn)
        else:
            messages = self.battle_messages
        
        if self.simple_log_mode:
            messages = self._extract_simple_log(messages)
        
        y = MESSAGE_BOX_Y + 55
        max_width = MESSAGE_BOX_WIDTH - 20
        
        for msg in messages[-28:]:
            clean = msg.replace('=','').strip()
            if not clean:
                y += 5
                continue
            
            color = BLACK
            if '💔' in msg: color = RED
            elif '✨' in msg: color = PURPLE
            elif '⚔️' in msg: color = BLUE
            elif '🔒' in msg or '硬直' in msg: color = ORANGE
            elif '❌' in msg or '✗' in msg: color = DARK_GRAY
            elif '✅' in msg or '✓' in msg: color = GREEN
            elif '第' in msg and '帧' in msg: color = BLUE
            elif '预测' in msg: color = PURPLE
            
            # 自动换行处理
            t = self.tiny_font.render(clean, True, color)
            if t.get_width() > max_width:
                # 需要分行
                words = []
                current_line = ""
                
                for char in clean:
                    test_line = current_line + char
                    test_surface = self.tiny_font.render(test_line, True, color)
                    
                    if test_surface.get_width() > max_width:
                        if current_line:
                            words.append(current_line)
                            current_line = char
                        else:
                            words.append(char)
                            current_line = ""
                    else:
                        current_line = test_line
                
                if current_line:
                    words.append(current_line)
                
                # 渲染所有行
                for line in words:
                    t = self.tiny_font.render(line, True, color)
                    self.screen.blit(t, (MESSAGE_BOX_X+10, y))
                    y += 19
                    if y > MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 80:
                        break
            else:
                # 不需要换行，直接渲染
                self.screen.blit(t, (MESSAGE_BOX_X+10, y))
                y += 19
            
            if y > MESSAGE_BOX_Y + MESSAGE_BOX_HEIGHT - 80:
                break
        
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
        """绘制当前选择（带状态提示）"""
        x, y = GRID_START_X, GRID_START_Y + CELL_HEIGHT + 300
        self.screen.blit(self.font.render("当前选择", True, BLACK), (x, y))
        
        y += 45
        next_turn = self.combat.turn + 1
        
        # P1显示
        f1, c1 = self._get_display(self.player1, 0, self.p1_actions, self.p1_locked, next_turn)
        f2, c2 = self._get_display(self.player1, 1, self.p1_actions, self.p1_locked, next_turn)
        
        # 添加状态图标
        p1_status = self._get_player_status_icon(self.player1, next_turn)
        
        if self.current_player == 1 and not self.p1_locked:
            p1_text = f"{PLAYER1_NAME}{p1_status}: [{f1}] [{f2}]"
            bg = c2 if len(self.p1_actions) >= 1 else c1
        elif self.p1_locked:
            p1_text = f"{PLAYER1_NAME}{p1_status}: [✓✓✓] [✓✓✓]"
            bg = LIGHT_RED
        else:
            p1_text = f"{PLAYER1_NAME}{p1_status}: [***] [***]"
            bg = LIGHT_RED
        
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 350, 35), border_radius=5)
        self.screen.blit(self.small_font.render(p1_text, True, BLACK), (x, y))
        
        # P2显示
        y += 45
        f1, c1 = self._get_display(self.player2, 0, self.p2_actions, self.p2_locked, next_turn)
        f2, c2 = self._get_display(self.player2, 1, self.p2_actions, self.p2_locked, next_turn)
        
        # 添加状态图标
        p2_status = self._get_player_status_icon(self.player2, next_turn)
        
        if self.current_player == 2 and not self.p2_locked:
            p2_text = f"{PLAYER2_NAME}{p2_status}:   [{f1}] [{f2}]"
            bg = c2 if len(self.p2_actions) >= 1 else c1
        elif self.p2_locked:
            p2_text = f"{PLAYER2_NAME}{p2_status}:   [✓✓✓] [✓✓✓]"
            bg = LIGHT_BLUE
        else:
            p2_text = f"{PLAYER2_NAME}{p2_status}:   [***] [***]"
            bg = LIGHT_BLUE
        
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 350, 35), border_radius=5)
        self.screen.blit(self.small_font.render(p2_text, True, BLACK), (x, y))
        
        # 提示信息
        y += 45
        hint, color = self._get_hint()
        self.screen.blit(self.small_font.render(hint, True, color), (x, y))
        
        y += 30
        self.screen.blit(self.tiny_font.render("SPACE确认 | Backspace撤销", True, ORANGE), (x, y))
    
    def _get_player_status_icon(self, player, next_turn):
        """获取玩家状态图标"""
        icons = []
        
        # 检查被控制
        if player.controlled:
            icons.append("⛓️")
        
        # 检查硬直
        if player.is_frame_locked(next_turn, 1) or player.is_frame_locked(next_turn, 2):
            icons.append("😵")
        
        # 检查蓄力
        if player.charge_level > 0:
            icons.append(f"✨{player.charge_level}")
        
        # 检查冲刺buff
        if player.dash_buff_stacks > 0:
            icons.append(f"🏃x{player.dash_buff_stacks}")
        
        return "".join(icons) if icons else ""

    def _get_display(self, player, idx, actions, locked, next_turn):
        """获取显示文本和颜色"""
        if idx < len(actions):
            if actions[idx] is None:
                return "🔒STUN", PURPLE
            elif actions[idx] == 'burst':
                return "Burst💥", ORANGE
            else:
                return self.action_names[actions[idx]], ORANGE if len(actions)==2 else YELLOW
        
        if player.is_frame_locked(next_turn, idx+1):
            return "🔒STUN", PURPLE
        
        return ("✓✓✓" if locked else "____"), (LIGHT_GRAY if locked else YELLOW)

    def _get_hint(self):
        """获取提示信息"""
        if self.p1_locked and self.p2_locked:
            return (UI_TEXT['both_confirmed'], ORANGE)
        if self.p1_locked:
            return (UI_TEXT['waiting_bob'], BLUE)
        if self.p2_locked:
            return (UI_TEXT['waiting_alice'], RED)
        
        player = self.player1 if self.current_player == 1 else self.player2
        actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        next_turn = self.combat.turn + 1
        
        for i in range(2):
            if i >= len(actions):
                if player.is_frame_locked(next_turn, i+1):
                    return (f"😵 第{i+1}帧硬直，可用O", PURPLE)
                else:
                    key = 'alice_turn' if self.current_player == 1 else 'bob_turn'
                    return (UI_TEXT[key].format(frame=i+1), GREEN)
        
        return (UI_TEXT['selection_complete'], ORANGE)

    def draw_game_over(self):
        """绘制游戏结束画面"""
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
        """处理输入"""
        if event.key == pygame.K_BACKSPACE:
            if self.current_player == 1 and not self.p1_locked and self.p1_actions:
                removed = self.p1_actions.pop()
                print(f"↩️ {PLAYER1_NAME}撤销: {self.action_names.get(removed, '???')}")
            elif self.current_player == 2 and not self.p2_locked and self.p2_actions:
                removed = self.p2_actions.pop()
                print(f"↩️ {PLAYER2_NAME}撤销: {self.action_names.get(removed, '???')}")
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
        """添加行动（UI层只负责收集输入）"""
        next_turn = self.combat.turn + 1
        action = self.action_map[key]
        
        for i in range(2):
            if i < len(actions):
                continue
            
            locked = player.is_frame_locked(next_turn, i+1)
            
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
        """确认选择"""
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
                print(f"✓ {PLAYER1_NAME}已确定")
            else:
                print(f"⚠ {PLAYER1_NAME}还需要输入")
        
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
                print(f"✓ {PLAYER2_NAME}已确定")
                if self.p1_locked:
                    self.start_execution()
            else:
                print(f"⚠ {PLAYER2_NAME}还需要输入")

    def start_execution(self):
        """开始执行"""
        self.game_state = "frame_executing"
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.battle_messages = []
        
        self.p1_final_actions = self._prepare(self.player1, self.p1_actions)
        self.p2_final_actions = self._prepare(self.player2, self.p2_actions)

    def _prepare(self, player, actions):
        """准备行动列表"""
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
        """执行帧"""
        idx = self.current_frame_index
        frame = idx + 1
        
        if idx == 0:
            self.combat.turn += 1
            self.combat.p1.clear_old_locks(self.combat.turn)
            self.combat.p2.clear_old_locks(self.combat.turn)
            self.combat.current_turn_messages = []
            self.combat.p1_first_frame_action = None
            self.combat.p2_first_frame_action = None
        
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
            
            if frame == 1:
                self.combat.p1_first_frame_action = p1_act
                self.combat.p2_first_frame_action = p2_act
            
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
        """更新游戏状态"""
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
        """重置回合"""
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"
        self.viewing_turn = 0
        self.is_viewing_history = False

    def reset_game(self):
        """重置游戏"""
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.reset_turn()
        self.battle_messages = []
        self.viewing_turn = 0
        self.is_viewing_history = False

    def _navigate_history(self, direction):
        """浏览历史"""
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
                    
                    elif event.key == pygame.K_TAB:
                        self.simple_log_mode = not self.simple_log_mode
                        mode = "简洁" if self.simple_log_mode else "详细"
                        print(f"📋 切换到{mode}日志")
                    
                    elif event.key == pygame.K_LEFT:
                        self._navigate_history('left')
                    elif event.key == pygame.K_RIGHT:
                        self._navigate_history('right')
                    
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
    """启动图形界面"""
    game = GameUI()
    game.run()


if __name__ == "__main__":
    main()