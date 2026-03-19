"""
game_ui.py
可视化界面 - 完整版（支持联机）/ Visual Interface - Complete Version (Network Support)

新功能 / New Features:
1. 主菜单系统 / Main menu system
2. 局域网联机 / LAN multiplayer
3. P1/P2独立输入，互相不可见 / P1/P2 independent input, mutually invisible
4. 双方同时输入 / Simultaneous input
5. 回合结束后才显示对方输入 / Show opponent's input after round ends
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

        # 游戏状态
        self.game_phase = "menu"  # "menu", "waiting", "game"
        self.game_state = "input"  # "input", "frame_executing", "turn_delay", "game_over"
        
        # 网络模式
        self.network_mode = None  # None(本地), 'host', 'client'
        self.network_server = None
        self.network_client = None
        self.my_player_id = None  # 1 or 2，表示我控制哪个玩家
        
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

        self.action_map = ACTION_KEY_MAP
        self.action_names = ACTION_DISPLAY_NAMES

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
        
        # 战斗日志滚动控制
        self.log_scroll_offset = 0
        self.log_max_lines = 25
        
        # 菜单相关
        self.menu_host_ip = ""
        self.menu_input_mode = None  # None, 'ip_input'
        self.ip_input_text = ""

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

    def init_game(self):
        """初始化游戏对象 / Initialize game objects"""
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(self.player1, self.player2)
        self.reset_turn()
        self.battle_messages = []

    # ========== 菜单相关 / Menu Related ==========
    
    def draw_menu(self):
        """绘制主菜单 / Draw main menu"""
        self.screen.fill(WHITE)
        
        # 标题
        title = self.large_font.render("回合制战斗游戏", True, BLACK)
        title_en = self.font.render("Turn-Based Battle Game", True, DARK_GRAY)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        title_en_rect = title_en.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        self.screen.blit(title_en, title_en_rect)
        
        # 菜单选项
        menu_y = 250
        
        if self.menu_input_mode == 'ip_input':
            # IP输入界面
            self.draw_ip_input()
        else:
            # 主菜单
            options = [
                ("1 - 本地双人游戏", "1 - Local 2 Players", (WINDOW_WIDTH//2, menu_y)),
                ("2 - 创建房间（我是P1）", "2 - Host Room (I am P1)", (WINDOW_WIDTH//2, menu_y + 70)),
                ("3 - 加入房间（我是P2）", "3 - Join Room (I am P2)", (WINDOW_WIDTH//2, menu_y + 140)),
                ("", "ESC - Exit", (WINDOW_WIDTH//2, menu_y + 240))
            ]
            
            for cn_text, en_text, pos in options:
                if cn_text:
                    rendered_cn = self.small_font.render(cn_text, True, DARK_GRAY)
                    rect_cn = rendered_cn.get_rect(center=(pos[0], pos[1] - 12))
                    self.screen.blit(rendered_cn, rect_cn)
                
                rendered_en = self.tiny_font.render(en_text, True, GRAY)
                rect_en = rendered_en.get_rect(center=(pos[0], pos[1] + 12))
                self.screen.blit(rendered_en, rect_en)
            
            # 如果是主机模式，显示等待信息
            if self.network_mode == 'host' and self.network_server:
                info_y = 480
                
                # 显示IP和端口
                from network import get_local_ip
                ip_text = f"你的IP地址: {get_local_ip()}"
                ip_text_en = f"Your IP Address: {get_local_ip()}"
                port_text = "端口 / Port: 5555"
                
                ip_surface = self.font.render(ip_text, True, BLUE)
                ip_surface_en = self.tiny_font.render(ip_text_en, True, BLUE)
                port_surface = self.small_font.render(port_text, True, BLUE)
                
                ip_rect = ip_surface.get_rect(center=(WINDOW_WIDTH//2, info_y))
                ip_rect_en = ip_surface_en.get_rect(center=(WINDOW_WIDTH//2, info_y + 30))
                port_rect = port_surface.get_rect(center=(WINDOW_WIDTH//2, info_y + 55))
                
                self.screen.blit(ip_surface, ip_rect)
                self.screen.blit(ip_surface_en, ip_rect_en)
                self.screen.blit(port_surface, port_rect)
                
                # 显示等待或就绪状态
                if not self.network_server.has_client():
                    wait_text = "等待玩家2连接..."
                    wait_text_en = "Waiting for Player 2..."
                    wait_surface = self.font.render(wait_text, True, ORANGE)
                    wait_surface_en = self.tiny_font.render(wait_text_en, True, ORANGE)
                    wait_rect = wait_surface.get_rect(center=(WINDOW_WIDTH//2, info_y + 95))
                    wait_rect_en = wait_surface_en.get_rect(center=(WINDOW_WIDTH//2, info_y + 125))
                    self.screen.blit(wait_surface, wait_rect)
                    self.screen.blit(wait_surface_en, wait_rect_en)
                else:
                    ready_text = "玩家2已连接！"
                    ready_text_en = "Player 2 connected! Press SPACE to start"
                    ready_surface = self.font.render(ready_text, True, GREEN)
                    ready_surface_en = self.tiny_font.render(ready_text_en, True, GREEN)
                    ready_rect = ready_surface.get_rect(center=(WINDOW_WIDTH//2, info_y + 95))
                    ready_rect_en = ready_surface_en.get_rect(center=(WINDOW_WIDTH//2, info_y + 125))
                    self.screen.blit(ready_surface, ready_rect)
                    self.screen.blit(ready_surface_en, ready_rect_en)
                    
                    hint_text = "按 SPACE 开始游戏"
                    hint_surface = self.small_font.render(hint_text, True, GREEN)
                    hint_rect = hint_surface.get_rect(center=(WINDOW_WIDTH//2, info_y + 155))
                    self.screen.blit(hint_surface, hint_rect)

    def draw_ip_input(self):
        """绘制IP输入界面 / Draw IP input interface"""
        y = 300
        
        prompt = "请输入主机IP地址:"
        prompt_en = "Enter Host IP Address:"
        prompt_surface = self.font.render(prompt, True, BLACK)
        prompt_surface_en = self.tiny_font.render(prompt_en, True, DARK_GRAY)
        prompt_rect = prompt_surface.get_rect(center=(WINDOW_WIDTH//2, y))
        prompt_rect_en = prompt_surface_en.get_rect(center=(WINDOW_WIDTH//2, y + 30))
        self.screen.blit(prompt_surface, prompt_rect)
        self.screen.blit(prompt_surface_en, prompt_rect_en)
        
        # IP输入框
        input_box = pygame.Rect(WINDOW_WIDTH//2 - 150, y + 60, 300, 40)
        pygame.draw.rect(self.screen, WHITE, input_box)
        pygame.draw.rect(self.screen, BLACK, input_box, 2)
        
        # 显示输入的文本
        text_surface = self.font.render(self.ip_input_text, True, BLACK)
        self.screen.blit(text_surface, (input_box.x + 10, input_box.y + 8))
        
        # 提示
        hint = "回车确认 / ENTER to confirm | ESC 返回 / ESC to back"
        hint_surface = self.tiny_font.render(hint, True, GRAY)
        hint_rect = hint_surface.get_rect(center=(WINDOW_WIDTH//2, y + 120))
        self.screen.blit(hint_surface, hint_rect)
        
        # 示例
        example = "示例 / Example: 192.168.1.100"
        example_surface = self.tiny_font.render(example, True, GRAY)
        example_rect = example_surface.get_rect(center=(WINDOW_WIDTH//2, y + 145))
        self.screen.blit(example_surface, example_rect)

    def handle_menu_input(self, event):
        """处理菜单输入 / Handle menu input"""
        if self.menu_input_mode == 'ip_input':
            # IP输入模式
            if event.key == pygame.K_RETURN:
                # 确认连接
                if self.ip_input_text.strip():
                    self.connect_to_host(self.ip_input_text.strip())
                self.menu_input_mode = None
                self.ip_input_text = ""
            elif event.key == pygame.K_ESCAPE:
                # 返回主菜单
                self.menu_input_mode = None
                self.ip_input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                # 删除字符
                self.ip_input_text = self.ip_input_text[:-1]
            else:
                # 输入字符
                char = event.unicode
                if char and (char.isdigit() or char == '.'):
                    self.ip_input_text += char
        else:
            # 主菜单模式
            if event.key == pygame.K_1:
                # 本地双人
                self.network_mode = None
                self.my_player_id = None
                self.init_game()
                self.game_phase = "game"
                print("开始本地双人游戏 / Starting local 2P game")
                
            elif event.key == pygame.K_2:
                # 创建房间
                self.start_host()
                
            elif event.key == pygame.K_3:
                # 加入房间 - 显示IP输入界面
                self.menu_input_mode = 'ip_input'
                self.ip_input_text = ""
                
            elif event.key == pygame.K_SPACE:
                # 主机确认开始
                if self.network_mode == 'host' and self.network_server and self.network_server.has_client():
                    self.init_game()
                    self.game_phase = "game"
                    # 通知客户端开始游戏
                    self.network_server.send_to_client({'action': 'start_game'})
                    print("游戏开始！ / Game started!")

    def start_host(self):
        """启动主机 / Start host"""
        from network import NetworkServer, get_local_ip
        self.network_server = NetworkServer()
        ip, port = self.network_server.start()
        if ip:
            self.network_mode = 'host'
            self.my_player_id = 1  # 主机是P1
            print(f"房间已创建 / Room created")
            print(f"IP: {get_local_ip()}")
            print(f"端口 / Port: {port}")

    def connect_to_host(self, host_ip):
        """连接到主机 / Connect to host"""
        from network import NetworkClient
        print(f"正在连接到 / Connecting to: {host_ip}")
        
        self.network_client = NetworkClient()
        if self.network_client.connect(host_ip):
            self.network_mode = 'client'
            self.my_player_id = 2  # 客户端是P2
            self.game_phase = "waiting"
            print("成功连接到主机，等待主机开始游戏...")
            print("Successfully connected, waiting for host to start...")
        else:
            print("连接失败！ / Connection failed!")
            self.network_client = None

    # ========== 网络同步 / Network Sync ==========
    
    def update_network(self):
        """更新网络数据 / Update network data"""
        if self.network_mode == 'host' and self.network_server:
            # 主机：接收P2的数据
            data = self.network_server.get_client_data(2)
            if data:
                if data.get('action') == 'player_confirmed':
                    # P2确认了输入
                    self.p2_actions = data['actions']
                    self.p2_locked = True
                    print("收到P2的行动 / Received P2's actions")
                    
                    # 如果P1也确认了，开始执行
                    if self.p1_locked and self.p2_locked:
                        # 发送P1的行动给P2
                        self.network_server.send_to_client({
                            'action': 'execute_turn',
                            'p1_actions': self.p1_actions,
                            'p2_actions': self.p2_actions
                        })
                        self.start_execution()
        
        elif self.network_mode == 'client' and self.network_client:
            # 客户端：接收主机的数据
            data = self.network_client.get_received_data()
            if data:
                if data.get('action') == 'start_game':
                    # 游戏开始
                    self.init_game()
                    self.game_phase = "game"
                    print("主机开始了游戏！ / Host started the game!")
                    
                elif data.get('action') == 'execute_turn':
                    # 收到完整的回合数据
                    self.p1_actions = data['p1_actions']
                    self.p2_actions = data['p2_actions']
                    self.p1_locked = True
                    self.p2_locked = True
                    print("收到完整回合数据 / Received complete turn data")
                    self.start_execution()

    def send_my_actions(self):
        """发送我的行动 / Send my actions"""
        if self.network_mode == 'host':
            # 主机发送P1的行动
            # 注意：主机不需要发送给自己，只需标记已确认
            pass
        elif self.network_mode == 'client':
            # 客户端发送P2的行动
            self.network_client.send({
                'action': 'player_confirmed',
                'player': 2,
                'actions': self.p2_actions
            })
            print("已发送P2的行动 / Sent P2's actions")

    # ========== 游戏绘制 / Game Drawing ==========

    def _extract_simple_log(self, messages):
        """提取简洁日志（适配新格式）/ Extract simple log (adapted to new format)"""
        simple = []
        
        # 解析回合信息
        turn_info = None
        current_frame = None
        frame_data = {1: {'p1': None, 'p2': None}, 2: {'p1': None, 'p2': None}}
        
        for msg in messages:
            msg_clean = msg.strip()
            if not msg_clean or '=' in msg:
                continue
            
            # 回合标题
            if "回合" in msg and "距离:" in msg:
                turn_info = msg_clean
                continue
            
            # 帧标记
            if "--- 第" in msg and "帧" in msg:
                if "第 1 帧" in msg:
                    current_frame = 1
                elif "第 2 帧" in msg:
                    current_frame = 2
                continue
            
            if current_frame is None:
                continue
            
            # 提取关键信息
            self._parse_frame_message(msg_clean, frame_data[current_frame])
        
        # 生成简洁日志
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
        """解析帧消息并提取关键信息 / Parse frame message and extract key information"""
        p1_name = PLAYER1_NAME
        p2_name = PLAYER2_NAME
        
        # 忽略阶段标题
        if msg.startswith('[P') and ']' in msg:
            return
        
        # 提取动作和结果
        if "爆血" in msg:
            if p1_name in msg:
                frame_data['p1'] = "爆血 / Burst"
            if p2_name in msg:
                frame_data['p2'] = "爆血 / Burst"
        
        elif "抱摔" in msg:
            if p1_name in msg and p1_name in msg[:msg.index("抱摔")]:
                frame_data['p1'] = "抱摔 / Grab"
            if p2_name in msg and p2_name in msg[:msg.index("抱摔")]:
                frame_data['p2'] = "抱摔 / Grab"
        
        elif "投掷" in msg:
            if p1_name in msg and p1_name in msg[:msg.index("投掷")]:
                frame_data['p1'] = "投掷 / Throw"
            if p2_name in msg and p2_name in msg[:msg.index("投掷")]:
                frame_data['p2'] = "投掷 / Throw"
        
        elif "攻击命中" in msg:
            if p1_name in msg:
                frame_data['p1'] = "攻击命中 / Attack hit"
            if p2_name in msg:
                frame_data['p2'] = "攻击命中 / Attack hit"
        
        elif "攻击未命中" in msg:
            if p1_name in msg:
                frame_data['p1'] = "攻击未中 / Attack missed"
            if p2_name in msg:
                frame_data['p2'] = "攻击未中 / Attack missed"
        
        elif "控制成功" in msg:
            if p1_name in msg:
                frame_data['p1'] = "控制成功 / Control success"
            if p2_name in msg:
                frame_data['p2'] = "控制成功 / Control success"
        
        elif "控制未命中" in msg:
            if p1_name in msg:
                frame_data['p1'] = "控制未中 / Control missed"
            if p2_name in msg:
                frame_data['p2'] = "控制未中 / Control missed"
        
        elif "反击准备就绪" in msg:
            if p1_name in msg:
                frame_data['p1'] = "反击成功 / Counter success"
            if p2_name in msg:
                frame_data['p2'] = "反击成功 / Counter success"
        
        elif "反击失败" in msg:
            if p1_name in msg:
                frame_data['p1'] = "反击失败 / Counter failed"
            if p2_name in msg:
                frame_data['p2'] = "反击失败 / Counter failed"
        
        elif "闪避成功" in msg:
            if p1_name in msg:
                frame_data['p1'] = "闪避成功 / Dodge success"
            if p2_name in msg:
                frame_data['p2'] = "闪避成功 / Dodge success"
        
        elif "获得蓄力" in msg:
            if p1_name in msg:
                level = "2" if "蓄力2" in msg else "1"
                frame_data['p1'] = f"蓄力{level} / Charge{level}"
            if p2_name in msg:
                level = "2" if "蓄力2" in msg else "1"
                frame_data['p2'] = f"蓄力{level} / Charge{level}"
        
        elif "移动" in msg and "->" in msg:
            if p1_name in msg:
                parts = msg.split("->")
                if len(parts) >= 2:
                    end_pos = parts[1].split()[0].split('(')[0]
                    frame_data['p1'] = f"移动到{end_pos} / Move to {end_pos}"
            if p2_name in msg:
                parts = msg.split("->")
                if len(parts) >= 2:
                    end_pos = parts[1].split()[0].split('(')[0]
                    frame_data['p2'] = f"移动到{end_pos} / Move to {end_pos}"
        
        elif "受" in msg and "伤" in msg and "HP:" in msg:
            if p1_name in msg:
                damage = msg.split("受")[1].split("伤")[0]
                hp_part = msg.split("HP:")[1].split()[0]
                frame_data['p1'] = f"受{damage}伤 HP:{hp_part} / Took {damage}dmg HP:{hp_part}"
            if p2_name in msg:
                damage = msg.split("受")[1].split("伤")[0]
                hp_part = msg.split("HP:")[1].split()[0]
                frame_data['p2'] = f"受{damage}伤 HP:{hp_part} / Took {damage}dmg HP:{hp_part}"

    def draw_grid(self):
        """绘制地图网格 / Draw map grid"""
        for i in range(MAP_SIZE):
            x = GRID_START_X + i * CELL_WIDTH
            y = GRID_START_Y
            pygame.draw.rect(self.screen, GRAY, (x, y, CELL_WIDTH, CELL_HEIGHT), 2)
            text = self.small_font.render(str(i + 1), True, DARK_GRAY)
            self.screen.blit(text, (x + CELL_WIDTH//2 - 10, y + 15))

    def draw_player(self, player, color):
        """绘制玩家 / Draw player"""
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
            status_text = self.tiny_font.render("被控 / Controlled", True, YELLOW)
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
            combo_text = f"被连击{player.combo_count}/3 / Combo {player.combo_count}/3"
            t = self.tiny_font.render(combo_text, True, ORANGE)
            tr = t.get_rect(center=(x, y + COMBO_DISPLAY_OFFSET_Y))
            pygame.draw.rect(self.screen, BLACK, tr.inflate(8, 4), border_radius=3)
            self.screen.blit(t, tr)

    def draw_header(self):
        """绘制标题 / Draw header"""
        text_cn = f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格"
        text_en = f"Round {self.combat.turn} | Distance: {self.combat.get_distance()} cells"
        text_surface_cn = self.large_font.render(text_cn, True, BLACK)
        text_surface_en = self.large_font.render(text_en, True, BLACK)
        
        # 居中显示
        cn_rect = text_surface_cn.get_rect(center=(WINDOW_WIDTH//2, 60))
        en_rect = text_surface_en.get_rect(center=(WINDOW_WIDTH//2, 100))
        
        self.screen.blit(text_surface_cn, cn_rect)
        self.screen.blit(text_surface_en, en_rect)
        
        if self.game_state == "frame_executing":
            t = self.font.render(f"执行第 {self.current_frame_index + 1} 帧 / Executing frame {self.current_frame_index + 1}", True, ORANGE)
            t_rect = t.get_rect(center=(WINDOW_WIDTH//2, 140))
            self.screen.blit(t, t_rect)
            
            # 进度条居中
            bar_width = 200
            px = WINDOW_WIDTH//2 - bar_width//2
            py = 165
            pygame.draw.rect(self.screen, GRAY, (px, py, bar_width, 10))
            prog = int(bar_width * self.frame_delay_timer / FRAME_DELAY)
            pygame.draw.rect(self.screen, GREEN, (px, py, prog, 10))

    def draw_key_hints(self):
        """绘制按键说明（根据玩家状态动态显示）/ Draw key hints (dynamically displayed based on player state)"""
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
            title = "按键说明 / Key Hints"
            status_msg = None
        else:
            # 检查这一帧是否受限
            is_this_frame_locked = (current_frame_idx == 0 and is_locked_frame1) or \
                                   (current_frame_idx == 1 and is_locked_frame2)
            
            if is_this_frame_locked:
                # 硬直：只能爆血
                title = f"第{current_frame_idx+1}帧硬直 / Frame {current_frame_idx+1} Stunned"
                status_msg = "只能使用爆血(O)\nCan only use burst (O)"
                key_hints = [
                    ("O - 爆血\nBurst", 'burst'),
                ]
            elif is_controlled and current_frame_idx == 0:
                # 被控制：只能防御和爆血（只在第1帧检查）
                title = "被控制状态 / Controlled State"
                status_msg = "只能使用防御(S)或爆血(O)\nCan only use defend (S) or burst (O)"
                key_hints = [
                    ("S - 防御\nDefend", 'defend'),
                    ("O - 爆血\nBurst", 'burst'),
                ]
            else:
                # 正常状态
                title = "按键说明 / Key Hints"
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
            warning_height = len(warning_lines) * 22 + 10
            pygame.draw.rect(self.screen, (255, 240, 200), (x-10, y-5, 260, warning_height), border_radius=5)
            pygame.draw.rect(self.screen, ORANGE, (x-10, y-5, 260, warning_height), 2, border_radius=5)
            
            for i, line in enumerate(warning_lines):
                warning_text = self.tiny_font.render(line, True, RED)
                self.screen.blit(warning_text, (x, y + i * 22))
            
            y += warning_height + 10
        
        # 绘制按键提示背景
        hint_height = len(key_hints) * 44 + 10
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x-10, y-5, 260, hint_height), border_radius=5)
        
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_skill = None
        
        for i, (line, skill) in enumerate(key_hints):
            ly = y + i * 44
            rect = pygame.Rect(x-8, ly-2, 256, 40)
            hover = rect.collidepoint(mouse_pos)
            
            if hover:
                pygame.draw.rect(self.screen, YELLOW, rect, border_radius=3)
                self.hovered_skill = skill
            
            # 如果是受限状态，用绿色高亮可用按键
            text_color = GREEN if status_msg else (BLACK if hover else DARK_GRAY)
            
            # 处理多行文本（每个按键说明）
            lines = line.split('\n')
            for j, text_line in enumerate(lines):
                t = self.tiny_font.render(text_line, True, text_color)
                self.screen.blit(t, (x, ly + j * 20))

    def draw_mechanics(self):
        """绘制游戏机制 / Draw game mechanics"""
        x, y = GRID_START_X + 280, GRID_START_Y + CELL_HEIGHT + 40
        self.screen.blit(self.font.render("游戏机制 / Game Mechanics", True, BLACK), (x, y))
        
        y += 40
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_mechanic = None
        
        for i, (key, info) in enumerate(GAME_MECHANICS.items()):
            my = y + i * 50
            rect = pygame.Rect(x-8, my-2, 200, 46)
            hover = rect.collidepoint(mouse_pos)
            
            bg_colors = [LIGHT_BLUE, LIGHT_RED, (200, 255, 200)]
            bg = bg_colors[i % len(bg_colors)]
            if hover:
                bg = YELLOW
                self.hovered_mechanic = key
            
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            
            # 处理多行文本
            name_lines = info['name'].split('\n')
            for j, line in enumerate(name_lines):
                t = self.small_font.render(line, True, BLACK if hover else DARK_GRAY)
                self.screen.blit(t, (x, my + j * 22))

    def draw_tooltip(self):
        """绘制技能提示 / Draw skill tooltip"""
        info = None
        if self.hovered_skill and self.hovered_skill in SKILL_DESCRIPTIONS:
            info = SKILL_DESCRIPTIONS[self.hovered_skill]
        elif self.hovered_mechanic:
            info = GAME_MECHANICS[self.hovered_mechanic]
        
        if info:
            x, y = GRID_START_X + 480, GRID_START_Y + CELL_HEIGHT + 80
            tooltip_width = 480
            max_text_width = tooltip_width - 24
            
            # 计算所有文本行（包括自动换行后的行数）
            title_lines = info['name'].split('\n')
            
            # 处理描述文本的自动换行
            wrapped_desc_lines = []
            for line in info['desc']:
                if not line:
                    wrapped_desc_lines.append('')
                    continue
                
                # 检查文本是否超出宽度
                test_surface = self.tiny_font.render(line, True, BLACK)
                if test_surface.get_width() > max_text_width:
                    # 需要换行
                    words = line.split()
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + word + " "
                        test_surface = self.tiny_font.render(test_line, True, BLACK)
                        
                        if test_surface.get_width() > max_text_width:
                            if current_line:
                                wrapped_desc_lines.append(current_line.strip())
                                current_line = word + " "
                            else:
                                # 单个词就超出宽度，强制添加
                                wrapped_desc_lines.append(word)
                                current_line = ""
                        else:
                            current_line = test_line
                    
                    if current_line.strip():
                        wrapped_desc_lines.append(current_line.strip())
                else:
                    wrapped_desc_lines.append(line)
            
            # 计算总高度
            h = 40 + len(title_lines) * 22 + len(wrapped_desc_lines) * 20
            
            # 绘制浮窗背景（阴影、边框、内容区）
            pygame.draw.rect(self.screen, (100,100,100), (x+3, y+3, tooltip_width, h), border_radius=8)
            pygame.draw.rect(self.screen, BLACK, (x, y, tooltip_width, h), border_radius=8)
            pygame.draw.rect(self.screen, (250,250,250), (x+2, y+2, tooltip_width-4, h-4), border_radius=6)
            
            # 渲染多行标题
            title_y = y + 8
            for line in title_lines:
                self.screen.blit(self.small_font.render(line, True, BLUE), (x+10, title_y))
                title_y += 22
            
            pygame.draw.line(self.screen, GRAY, (x+10, title_y), (x+tooltip_width-10, title_y))
            
            # 渲染描述文本（已经处理了换行）
            dy = title_y + 5
            for line in wrapped_desc_lines:
                if line:
                    self.screen.blit(self.tiny_font.render(line, True, BLACK), (x+12, dy))
                dy += 20

    def draw_messages(self):
        """绘制战斗日志 / Draw battle log"""
        # 使用更大的日志框
        log_box_height = 660
        
        pygame.draw.rect(self.screen, LIGHT_GRAY, (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, log_box_height), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, (MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, log_box_height), 2, border_radius=10)
        
        title_text = "战斗日志 / Battle Log"
        if self.simple_log_mode:
            title_text += " (简洁) / (Simple)"
        
        if self.is_viewing_history and self.viewing_turn > 0:
            title_text += f" - 回合{self.viewing_turn} / Turn{self.viewing_turn}"
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
        
        # 处理消息，展开所有需要换行的文本
        all_lines = []
        max_width = MESSAGE_BOX_WIDTH - 30
        
        for msg in messages:
            clean = msg.replace('=','').strip()
            if not clean:
                all_lines.append(('', BLACK))
                continue
            
            # 确定颜色
            color = BLACK
            if '受' in msg and '伤' in msg: 
                color = RED
            elif '蓄力' in msg: 
                color = PURPLE
            elif '攻击' in msg or '反击' in msg: 
                color = BLUE
            elif '控制' in msg or '硬直' in msg: 
                color = ORANGE
            elif '失败' in msg or '未命中' in msg: 
                color = DARK_GRAY
            elif '成功' in msg or '命中' in msg: 
                color = GREEN
            elif '第' in msg and '帧' in msg: 
                color = BLUE
            elif '预测' in msg: 
                color = PURPLE
            elif msg.startswith('[P') and ']' in msg:
                color = BLUE
            
            # 自动换行处理
            t = self.tiny_font.render(clean, True, color)
            if t.get_width() > max_width:
                # 需要分行 - 按字符分割而不是按单词
                current_line = ""
                
                for char in clean:
                    test_line = current_line + char
                    test_surface = self.tiny_font.render(test_line, True, color)
                    
                    if test_surface.get_width() > max_width:
                        if current_line:
                            all_lines.append((current_line, color))
                            current_line = char
                        else:
                            all_lines.append((char, color))
                            current_line = ""
                    else:
                        current_line = test_line
                
                if current_line:
                    all_lines.append((current_line, color))
            else:
                all_lines.append((clean, color))
        
        # 计算可显示的总行数
        total_lines = len(all_lines)
        
        # 限制滚动范围
        max_scroll = max(0, total_lines - self.log_max_lines)
        self.log_scroll_offset = max(0, min(self.log_scroll_offset, max_scroll))
        
        # 显示从offset开始的行
        y = MESSAGE_BOX_Y + 55
        start_line = self.log_scroll_offset
        end_line = min(start_line + self.log_max_lines, total_lines)
        
        # 计算最大显示Y坐标（确保不超出框，与hint_y对应）
        max_y = MESSAGE_BOX_Y + log_box_height - 110
        
        line_height = 19
        for i in range(start_line, end_line):
            if y >= max_y:
                break
            line, color = all_lines[i]
            if line:
                t = self.tiny_font.render(line, True, color)
                self.screen.blit(t, (MESSAGE_BOX_X+10, y))
            y += line_height
        
        # 绘制滚动指示器 - 固定在合适的位置
        hint_y = MESSAGE_BOX_Y + log_box_height - 105
        pygame.draw.line(self.screen, DARK_GRAY, (MESSAGE_BOX_X+10, hint_y-5), (MESSAGE_BOX_X+MESSAGE_BOX_WIDTH-10, hint_y-5), 1)
        
        # 滚动提示
        if total_lines > self.log_max_lines:
            scroll_hints = [
                "上下滚动 PgUp/PgDn",
                "Up/Down Scroll PgUp/Dn"
            ]
            for i, hint in enumerate(scroll_hints):
                self.screen.blit(self.tiny_font.render(hint, True, DARK_GRAY), (MESSAGE_BOX_X+10, hint_y+i*18))
        
        # 其他提示
        hint_lines = [
            ("TAB - 切换简洁/详细", DARK_GRAY),
            ("TAB - Toggle Simple/Detailed", DARK_GRAY)
        ]
        
        hint_start_y = hint_y + (36 if total_lines > self.log_max_lines else 0)
        for i, (line, color) in enumerate(hint_lines):
            t = self.tiny_font.render(line, True, color)
            self.screen.blit(t, (MESSAGE_BOX_X+10, hint_start_y + i*18))
        
        if len(self.combat.turn_logs) > 0:
            history_y = hint_start_y + 32
            history_lines = [
                ("左右 浏览历史", DARK_GRAY),
                ("Left/Right Browse History", DARK_GRAY)
            ]
            
            for i, (line, color) in enumerate(history_lines):
                t = self.tiny_font.render(line, True, color)
                self.screen.blit(t, (MESSAGE_BOX_X+10, history_y + i*18))

    def draw_selection(self):
        """绘制当前选择（带状态提示）/ Draw current selection (with status hints)"""
        # 放在游戏机制下方
        x, y = GRID_START_X + 280, GRID_START_Y + CELL_HEIGHT + 190
        self.screen.blit(self.font.render("当前选择 / Current Selection", True, BLACK), (x, y))
        
        y += 45
        next_turn = self.combat.turn + 1
        
        # ======= 关键修改：根据网络模式决定显示内容 =======
        
        # P1显示
        f1_p1, c1_p1 = self._get_display(self.player1, 0, self.p1_actions, self.p1_locked, next_turn)
        f2_p1, c2_p1 = self._get_display(self.player1, 1, self.p1_actions, self.p1_locked, next_turn)
        
        # 添加状态图标
        p1_status = self._get_player_status_icon(self.player1, next_turn)
        
        # 根据网络模式决定显示内容
        if self.network_mode == 'client':
            # 客户端（P2）：P1的输入显示为隐藏
            if not self.p1_locked:
                p1_text = f"{PLAYER1_NAME}: [???] [???]"
            else:
                p1_text = f"{PLAYER1_NAME}: [已确认] / [Confirmed]"
            bg = LIGHT_RED
        elif self.network_mode == 'host' and self.current_player == 2:
            # 主机但当前是P2输入：显示P1已确认或隐藏
            if not self.p1_locked:
                p1_text = f"{PLAYER1_NAME}: [???] [???]"
            else:
                p1_text = f"{PLAYER1_NAME}: [已确认] / [Confirmed]"
            bg = LIGHT_RED
        else:
            # 本地模式或主机P1输入：正常显示
            if self.current_player == 1 and not self.p1_locked:
                p1_text = f"{PLAYER1_NAME}: [{f1_p1}] [{f2_p1}]"
                bg = c2_p1 if len(self.p1_actions) >= 1 else c1_p1
            elif self.p1_locked:
                p1_text = f"{PLAYER1_NAME}: [已确认] / [Confirmed]"
                bg = LIGHT_RED
            else:
                p1_text = f"{PLAYER1_NAME}: [***] [***]"
                bg = LIGHT_RED
        
        box_height = 35
        
        # 绘制背景框
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 450, box_height), border_radius=5)
        
        # 渲染主文本（单行）
        self.screen.blit(self.small_font.render(p1_text, True, BLACK), (x, y))
        
        # 渲染状态图标（分行显示，位置靠右）
        if p1_status and self.network_mode != 'client':  # 客户端不显示P1状态
            status_lines = p1_status.split('\n')
            status_x = x + 280
            for i, line in enumerate(status_lines):
                self.screen.blit(self.tiny_font.render(line, True, DARK_GRAY), (status_x, y + i*16))
        
        # P2显示
        y += box_height + 15
        f1_p2, c1_p2 = self._get_display(self.player2, 0, self.p2_actions, self.p2_locked, next_turn)
        f2_p2, c2_p2 = self._get_display(self.player2, 1, self.p2_actions, self.p2_locked, next_turn)
        
        # 添加状态图标
        p2_status = self._get_player_status_icon(self.player2, next_turn)
        
        # 根据网络模式决定显示内容
        if self.network_mode == 'host':
            # 主机（P1）：P2的输入显示为隐藏
            if not self.p2_locked:
                p2_text = f"{PLAYER2_NAME}: [???] [???]"
            else:
                p2_text = f"{PLAYER2_NAME}: [已确认] / [Confirmed]"
            bg = LIGHT_BLUE
        elif self.network_mode == 'client' and self.current_player == 1:
            # 客户端但当前是P1输入（不应该发生，但保险起见）
            if not self.p2_locked:
                p2_text = f"{PLAYER2_NAME}: [???] [???]"
            else:
                p2_text = f"{PLAYER2_NAME}: [已确认] / [Confirmed]"
            bg = LIGHT_BLUE
        else:
            # 本地模式或客户端P2输入：正常显示
            if self.current_player == 2 and not self.p2_locked:
                p2_text = f"{PLAYER2_NAME}: [{f1_p2}] [{f2_p2}]"
                bg = c2_p2 if len(self.p2_actions) >= 1 else c1_p2
            elif self.p2_locked:
                p2_text = f"{PLAYER2_NAME}: [已确认] / [Confirmed]"
                bg = LIGHT_BLUE
            else:
                p2_text = f"{PLAYER2_NAME}: [***] [***]"
                bg = LIGHT_BLUE
        
        box_height = 35
        
        # 绘制背景框
        pygame.draw.rect(self.screen, bg, (x-10, y-5, 450, box_height), border_radius=5)
        
        # 渲染主文本（单行）
        self.screen.blit(self.small_font.render(p2_text, True, BLACK), (x, y))
        
        # 渲染状态图标（分行显示，位置靠右）
        if p2_status and self.network_mode != 'host':  # 主机不显示P2状态
            status_lines = p2_status.split('\n')
            status_x = x + 280
            for i, line in enumerate(status_lines):
                self.screen.blit(self.tiny_font.render(line, True, DARK_GRAY), (status_x, y + i*16))
        
        # 提示信息
        y += box_height + 10
        hint, color = self._get_hint()
        
        # 如果提示信息包含中英文分隔符，分行显示
        if ' / ' in hint:
            hint_lines = hint.split(' / ')
            for line in hint_lines:
                self.screen.blit(self.small_font.render(line.strip(), True, color), (x, y))
                y += 25
        else:
            self.screen.blit(self.small_font.render(hint, True, color), (x, y))
            y += 30
        
        y += 5
        self.screen.blit(self.tiny_font.render("SPACE确认 | Backspace撤销", True, ORANGE), (x, y))
        y += 20
        self.screen.blit(self.tiny_font.render("SPACE Confirm | Backspace Undo", True, ORANGE), (x, y))
    
    def _get_player_status_icon(self, player, next_turn):
        """获取玩家状态图标"""
        icons = []
        
        # 检查被控制
        if player.controlled:
            icons.append("被控\nControlled")
        
        # 检查硬直
        if player.is_frame_locked(next_turn, 1) or player.is_frame_locked(next_turn, 2):
            icons.append("硬直\nStunned")
        
        # 检查蓄力
        if player.charge_level > 0:
            icons.append(f"蓄力{player.charge_level}\nCharge{player.charge_level}")
        
        # 检查冲刺buff
        if player.dash_buff_stacks > 0:
            icons.append(f"冲刺x{player.dash_buff_stacks}\nDashx{player.dash_buff_stacks}")
        
        return "\n".join(icons) if icons else ""

    def _get_display(self, player, idx, actions, locked, next_turn):
        """获取显示文本和颜色"""
        if idx < len(actions):
            if actions[idx] is None:
                return "STUN", PURPLE
            elif actions[idx] == 'burst':
                return "Burst", ORANGE
            else:
                return self.action_names[actions[idx]], ORANGE if len(actions)==2 else YELLOW
        
        if player.is_frame_locked(next_turn, idx+1):
            return "STUN", PURPLE
        
        if locked:
            return "已确认", LIGHT_GRAY
        else:
            return "____", YELLOW

    def _get_hint(self):
        """获取提示信息"""
        # 网络模式下的特殊提示
        if self.network_mode:
            if self.p1_locked and self.p2_locked:
                return ("双方已确认，执行中... / Both confirmed, executing...", ORANGE)
            elif self.network_mode == 'host':
                if self.p1_locked:
                    return ("等待P2确认... / Waiting for P2...", BLUE)
                else:
                    return ("P1输入中 (P2看不到) / P1 inputting (P2 can't see)", GREEN)
            elif self.network_mode == 'client':
                if self.p2_locked:
                    return ("等待P1确认... / Waiting for P1...", RED)
                else:
                    return ("P2输入中 (P1看不到) / P2 inputting (P1 can't see)", GREEN)
        
        # 本地模式的提示
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
                    return (f"第{i+1}帧硬直，可用O / Frame{i+1} Stunned, use O", PURPLE)
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
        text = "平局！ / Draw!" if winner == "平局 / Draw" else f"{winner} 获胜！ / {winner} Wins!"
        
        t = self.large_font.render(text, True, YELLOW)
        self.screen.blit(t, (WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 50))
        
        h = self.font.render("按 R 重新开始 | ESC 退出 / Press R to Restart | ESC to Exit", True, WHITE)
        self.screen.blit(h, (WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 + 50))

    # ========== 输入处理 / Input Handling ==========

    def handle_input(self, event):
        """处理输入"""
        # 网络模式下的输入限制
        if self.network_mode == 'host':
            # 主机只能控制玩家1
            if self.current_player == 2:
                return
        elif self.network_mode == 'client':
            # 客户端只能控制玩家2
            if self.current_player == 1:
                return
        
        if event.key == pygame.K_BACKSPACE:
            if self.current_player == 1 and not self.p1_locked and self.p1_actions:
                removed = self.p1_actions.pop()
                print(f"{PLAYER1_NAME}撤销: {self.action_names.get(removed, '???')}")
            elif self.current_player == 2 and not self.p2_locked and self.p2_actions:
                removed = self.p2_actions.pop()
                print(f"{PLAYER2_NAME}撤销: {self.action_names.get(removed, '???')}")
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
        """添加行动（UI层只负责收集输入）/ Add action (UI layer only responsible for collecting input)"""
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
                    print(f"{name}选择第{i+1}帧(硬直): {self.action_names[action]} / {name} selects frame {i+1} (stunned): {self.action_names[action]}")
                    return
                else:
                    continue
            
            while len(actions) < i:
                actions.append(None)
            
            actions.append(action)
            print(f"{name}选择第{i+1}帧: {self.action_names[action]} / {name} selects frame {i+1}: {self.action_names[action]}")
            return
        
        print(f"{name}已选2个 / {name} has selected 2 actions")

    def _confirm(self):
        """确认选择 / Confirm selection"""
        next_turn = self.combat.turn + 1

        # 根据网络模式处理确认
        if self.network_mode == 'host':
            # 主机只确认P1
            if not self.p1_locked:
                ready = self._check_ready(self.player1, self.p1_actions, next_turn)
                if ready:
                    self._finalize_actions(self.player1, self.p1_actions, next_turn)
                    self.p1_locked = True
                    print(f"{PLAYER1_NAME}已确定 / {PLAYER1_NAME} confirmed")
                
                    # 检查是否双方都已确认
                    if self.p1_locked and self.p2_locked:
                        # 发送P1的行动给P2
                        self.network_server.send_to_client({
                            'action': 'execute_turn',
                            'p1_actions': self.p1_actions,
                            'p2_actions': self.p2_actions
                        })
                        self.start_execution()
                else:
                    print(f"{PLAYER1_NAME}还需要输入 / {PLAYER1_NAME} needs more input")
        
        elif self.network_mode == 'client':
            # 客户端只确认P2
            if not self.p2_locked:
                ready = self._check_ready(self.player2, self.p2_actions, next_turn)
                if ready:
                    self._finalize_actions(self.player2, self.p2_actions, next_turn)
                    self.p2_locked = True
                    print(f"{PLAYER2_NAME}已确定 / {PLAYER2_NAME} confirmed")
                    self.send_my_actions()
                else:
                    print(f"{PLAYER2_NAME}还需要输入 / {PLAYER2_NAME} needs more input")
        
        else:
            # 本地模式 - 原有逻辑
            if self.current_player == 1 and not self.p1_locked:
                ready = self._check_ready(self.player1, self.p1_actions, next_turn)
                if ready:
                    self._finalize_actions(self.player1, self.p1_actions, next_turn)
                    self.p1_locked = True
                    self.current_player = 2
                    print(f"{PLAYER1_NAME}已确定 / {PLAYER1_NAME} confirmed")
                else:
                    print(f"{PLAYER1_NAME}还需要输入 / {PLAYER1_NAME} needs more input")
            
            elif self.current_player == 2 and not self.p2_locked:
                ready = self._check_ready(self.player2, self.p2_actions, next_turn)
                if ready:
                    self._finalize_actions(self.player2, self.p2_actions, next_turn)
                    self.p2_locked = True
                    print(f"{PLAYER2_NAME}已确定 / {PLAYER2_NAME} confirmed")
                    if self.p1_locked:
                        self.start_execution()
                else:
                    print(f"{PLAYER2_NAME}还需要输入 / {PLAYER2_NAME} needs more input")
    
    def _check_ready(self, player, actions, next_turn):
        """检查是否准备好 / Check if ready"""
        for i in range(2):
            if i < len(actions):
                continue
            if not player.is_frame_locked(next_turn, i+1):
                return False
        return True
    
    def _finalize_actions(self, player, actions, next_turn):
        """完善行动列表 / Finalize action list"""
        for i in range(2):
            if player.is_frame_locked(next_turn, i+1) and i >= len(actions):
                while len(actions) < i:
                    actions.append(None)
                actions.append(None)

    def start_execution(self):
        """开始执行 / Start execution"""
        self.game_state = "frame_executing"
        self.current_frame_index = 0
        self.frame_delay_timer = 0
        self.log_scroll_offset = 9999  # 执行新回合时滚动到底部
        
        # 准备最终行动列表 / Prepare final action list
        self.p1_final_actions = self._prepare(self.player1, self.p1_actions)
        self.p2_final_actions = self._prepare(self.player2, self.p2_actions)

    def _prepare(self, player, actions):
        """准备行动列表 / Prepare action list"""
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
        """执行帧 / Execute frame"""
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
                print(f"回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格 / Round {self.combat.turn} | Distance: {self.combat.get_distance()} cells")
                self.combat.p1.show_status()
                self.combat.p2.show_status()
                print('='*60)
            
            print(f"\n--- 第 {frame} 帧 / Frame {frame} ---")
            
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
                self.log_scroll_offset = 9999  # 新消息添加后滚动到底部
        finally:
            sys.stdout = old_stdout

    def update(self):
        """更新游戏状态 / Update game state"""
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
        """重置回合 / Reset turn"""
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        
        # 网络模式下，根据角色设置当前玩家
        if self.network_mode == 'host':
            self.current_player = 1
        elif self.network_mode == 'client':
            self.current_player = 2
        else:
            self.current_player = 1
        
        self.game_state = "input"
        self.viewing_turn = 0
        self.is_viewing_history = False
        self.log_scroll_offset = 9999  # 滚动到底部显示最新内容

    def reset_game(self):
        """重置游戏 / Reset game"""
        self.init_game()
        self.viewing_turn = 0
        self.is_viewing_history = False
        self.log_scroll_offset = 0

    def _navigate_history(self, direction):
        """浏览历史 / Navigate history"""
        if len(self.combat.turn_logs) == 0:
            return
        
        if direction == 'left':
            if self.viewing_turn == 0:
                self.viewing_turn = self.combat.turn
                self.is_viewing_history = True
            elif self.viewing_turn > 1:
                self.viewing_turn -= 1
            print(f"查看回合{self.viewing_turn}")
            self.log_scroll_offset = 0  # 重置滚动
        
        elif direction == 'right':
            if self.is_viewing_history:
                if self.viewing_turn < self.combat.turn:
                    self.viewing_turn += 1
                    print(f"查看回合{self.viewing_turn}")
                
                if self.viewing_turn == self.combat.turn:
                    self.viewing_turn = 0
                    self.is_viewing_history = False
                    print(f"返回最新")
                
                self.log_scroll_offset = 0  # 重置滚动

    def run(self):
        """主循环 / Main loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_phase == "game":
                            # 从游戏返回菜单
                            self.game_phase = "menu"
                            if self.network_server:
                                self.network_server.close()
                                self.network_server = None
                            if self.network_client:
                                self.network_client.close()
                                self.network_client = None
                            self.network_mode = None
                        else:
                            # 从菜单退出
                            running = False
                    
                    elif self.game_phase == "menu":
                        self.handle_menu_input(event)
                    
                    elif self.game_phase == "waiting":
                        # 等待主机开始，不处理输入
                        pass
                    
                    elif self.game_phase == "game":
                        if event.key == pygame.K_r and self.game_state == "game_over":
                            self.reset_game()
                        
                        elif event.key == pygame.K_TAB:
                            self.simple_log_mode = not self.simple_log_mode
                            mode = "简洁" if self.simple_log_mode else "详细"
                            print(f"切换到{mode}日志")
                            self.log_scroll_offset = 0  # 重置滚动
                        
                        elif event.key == pygame.K_LEFT:
                            self._navigate_history('left')
                        elif event.key == pygame.K_RIGHT:
                            self._navigate_history('right')
                        
                        elif event.key == pygame.K_UP:
                            self.log_scroll_offset = max(0, self.log_scroll_offset - 1)
                        elif event.key == pygame.K_DOWN:
                            self.log_scroll_offset += 1
                        elif event.key == pygame.K_PAGEUP:
                            self.log_scroll_offset = max(0, self.log_scroll_offset - 5)
                        elif event.key == pygame.K_PAGEDOWN:
                            self.log_scroll_offset += 5
                        elif event.key == pygame.K_HOME:
                            self.log_scroll_offset = 0
                        elif event.key == pygame.K_END:
                            self.log_scroll_offset = 9999
                        
                        elif self.game_state == "input":
                            self.handle_input(event)
            
            # 更新网络数据
            if self.game_phase == "game" or self.game_phase == "waiting":
                self.update_network()
            
            # 更新游戏状态
            if self.game_phase == "game":
                self.update()
            
            # 绘制
            if self.game_phase == "menu":
                self.draw_menu()
            elif self.game_phase == "waiting":
                self.screen.fill(WHITE)
                wait_text = "等待主机开始游戏..."
                wait_text_en = "Waiting for host to start..."
                wait_surface = self.large_font.render(wait_text, True, ORANGE)
                wait_surface_en = self.font.render(wait_text_en, True, ORANGE)
                wait_rect = wait_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 20))
                wait_rect_en = wait_surface_en.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30))
                self.screen.blit(wait_surface, wait_rect)
                self.screen.blit(wait_surface_en, wait_rect_en)
            else:
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
        
        # 清理网络连接
        if self.network_server:
            self.network_server.close()
        if self.network_client:
            self.network_client.close()
        
        pygame.quit()


def main():
    """启动图形界面 / Launch graphical interface"""
    game = GameUI()
    game.run()


if __name__ == "__main__":
    main()