"""
main.py - Kivy版本主程序
适配Android触屏操作的回合制战斗游戏
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.popup import Popup

from player import Player
from combat_manager import CombatManager
from config import *
from game_data import ACTION_KEY_MAP, ACTION_DISPLAY_NAMES, SKILL_DESCRIPTIONS

# 设置横屏
Window.rotation = 0


class MenuScreen(Screen):
    """主菜单界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=30)
        
        # 标题
        title = Label(
            text='回合制战斗游戏\nTurn-Based Battle Game',
            font_size='48sp',
            size_hint=(1, 0.3),
            halign='center'
        )
        layout.add_widget(title)
        
        # 按钮容器
        button_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(1, 0.4))
        
        # 本地双人按钮
        local_btn = Button(
            text='本地双人游戏\nLocal 2 Players',
            font_size='32sp',
            size_hint=(1, None),
            height=120,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        local_btn.bind(on_press=self.start_local_game)
        button_layout.add_widget(local_btn)
        
        # 联机游戏按钮（可选）
        online_btn = Button(
            text='联机游戏（开发中）\nOnline (Coming Soon)',
            font_size='28sp',
            size_hint=(1, None),
            height=100,
            background_color=(0.5, 0.5, 0.5, 1),
            disabled=True
        )
        button_layout.add_widget(online_btn)
        
        layout.add_widget(button_layout)
        layout.add_widget(Widget(size_hint=(1, 0.3)))  # 底部空白
        
        self.add_widget(layout)
    
    def start_local_game(self, instance):
        """开始本地游戏"""
        self.manager.current = 'game'
        self.manager.get_screen('game').init_game()


class GameScreen(Screen):
    """游戏主界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 游戏状态
        self.combat = None
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"  # input, executing, game_over
        
        # 主布局：左边游戏区，右边日志区
        main_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        
        # ===== 左侧游戏区 =====
        left_layout = BoxLayout(orientation='vertical', size_hint=(0.55, 1), spacing=10)
        
        # 顶部状态栏
        self.status_label = Label(
            text='回合 1 | 距离: 3格',
            font_size='36sp',
            size_hint=(1, None),
            height=60,
            color=(0, 0, 0, 1)
        )
        left_layout.add_widget(self.status_label)
        
        # 游戏区域（玩家、网格）
        self.game_area = GameArea()
        left_layout.add_widget(self.game_area)
        
        # 当前选择显示
        self.selection_label = Label(
            text='P1: [____] [____]\nP2: [____] [____]',
            font_size='28sp',
            size_hint=(1, None),
            height=100,
            color=(0, 0, 0, 1)
        )
        left_layout.add_widget(self.selection_label)
        
        # 技能按钮区
        self.skill_buttons = SkillButtonGrid(game_screen=self)
        left_layout.add_widget(self.skill_buttons)
        
        # 确认按钮
        confirm_btn = Button(
            text='确认 CONFIRM',
            font_size='32sp',
            size_hint=(1, None),
            height=80,
            background_color=(1, 0.6, 0, 1)
        )
        confirm_btn.bind(on_press=self.confirm_selection)
        left_layout.add_widget(confirm_btn)
        
        main_layout.add_widget(left_layout)
        
        # ===== 右侧日志区 =====
        right_layout = BoxLayout(orientation='vertical', size_hint=(0.45, 1), spacing=10)
        
        # 日志标题和切换按钮
        log_header = BoxLayout(size_hint=(1, None), height=60, spacing=10)
        log_title = Label(
            text='战斗日志 Battle Log',
            font_size='32sp',
            size_hint=(0.7, 1),
            color=(0, 0, 0, 1)
        )
        toggle_btn = Button(
            text='切换\nToggle',
            font_size='24sp',
            size_hint=(0.3, 1),
            background_color=(0.2, 0.5, 1, 1)
        )
        toggle_btn.bind(on_press=self.toggle_log_mode)
        log_header.add_widget(log_title)
        log_header.add_widget(toggle_btn)
        right_layout.add_widget(log_header)
        
        # 日志滚动区
        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text='游戏开始...\nGame Start...',
            font_size='22sp',
            size_hint_y=None,
            color=(0, 0, 0, 1),
            markup=True,
            halign='left',
            valign='top'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_label.bind(width=lambda *x: self.log_label.setter('text_size')(self.log_label, (self.log_label.width, None)))
        self.log_scroll.add_widget(self.log_label)
        right_layout.add_widget(self.log_scroll)
        
        main_layout.add_widget(right_layout)
        
        self.add_widget(main_layout)
        
        # 日志模式
        self.simple_log_mode = False
        self.battle_messages = []
    
    def init_game(self):
        """初始化游戏"""
        player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        self.combat = CombatManager(player1, player2)
        
        self.p1_actions = []
        self.p2_actions = []
        self.p1_locked = False
        self.p2_locked = False
        self.current_player = 1
        self.game_state = "input"
        self.battle_messages = []
        
        self.update_display()
        self.log_label.text = '游戏开始！\nGame Start!\n\n请玩家1选择第1帧行动\nPlayer 1, select frame 1 action'
    
    def on_skill_selected(self, action):
        """技能被选中"""
        if self.game_state != "input":
            return
        
        player = self.combat.p1 if self.current_player == 1 else self.combat.p2
        actions = self.p1_actions if self.current_player == 1 else self.p2_actions
        locked = self.p1_locked if self.current_player == 1 else self.p2_locked
        
        if not locked and len(actions) < 2:
            actions.append(action)
            self.update_display()
            
            # 更新提示
            if len(actions) == 1:
                player_name = "玩家1" if self.current_player == 1 else "玩家2"
                self.log_label.text += f"\n{player_name}选择了 {ACTION_DISPLAY_NAMES[action]}"
    
    def confirm_selection(self, instance):
        """确认选择"""
        if self.game_state != "input":
            return
        
        if self.current_player == 1 and not self.p1_locked:
            if len(self.p1_actions) >= 2:
                self.p1_locked = True
                self.current_player = 2
                self.log_label.text += "\n\n玩家1已确认！\n请玩家2选择行动"
                self.update_display()
        elif self.current_player == 2 and not self.p2_locked:
            if len(self.p2_actions) >= 2:
                self.p2_locked = True
                self.log_label.text += "\n\n玩家2已确认！\n执行回合..."
                self.update_display()
                # 延迟执行，让玩家看到确认信息
                Clock.schedule_once(lambda dt: self.execute_turn(), 1)
    
    def execute_turn(self):
        """执行回合"""
        self.game_state = "executing"
        
        # 捕获输出
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            self.combat.execute_turn(self.p1_actions, self.p2_actions)
            output = sys.stdout.getvalue()
            self.battle_messages.extend(output.split('\n'))
            self.log_label.text = '\n'.join(self.battle_messages[-50:])  # 只显示最近50行
        finally:
            sys.stdout = old_stdout
        
        # 检查游戏是否结束
        if not self.combat.p1.is_alive() or not self.combat.p2.is_alive():
            self.game_state = "game_over"
            winner = self.combat.get_winner()
            self.show_game_over(winner)
        else:
            # 重置回合
            self.p1_actions = []
            self.p2_actions = []
            self.p1_locked = False
            self.p2_locked = False
            self.current_player = 1
            self.game_state = "input"
            self.update_display()
            self.log_label.text += "\n\n" + "="*30 + "\n请玩家1选择行动"
    
    def update_display(self):
        """更新显示"""
        if self.combat:
            # 更新状态栏
            self.status_label.text = f'回合 {self.combat.turn} | 距离: {self.combat.get_distance()}格'
            
            # 更新游戏区域
            self.game_area.update_players(self.combat.p1, self.combat.p2)
            
            # 更新选择显示
            p1_text = self._get_selection_text(1)
            p2_text = self._get_selection_text(2)
            self.selection_label.text = f'{p1_text}\n{p2_text}'
    
    def _get_selection_text(self, player_id):
        """获取选择文本"""
        actions = self.p1_actions if player_id == 1 else self.p2_actions
        locked = self.p1_locked if player_id == 1 else self.p2_locked
        name = PLAYER1_NAME if player_id == 1 else PLAYER2_NAME
        
        if locked:
            return f"{name}: [已确认 Confirmed]"
        elif len(actions) >= 2:
            a1 = ACTION_DISPLAY_NAMES.get(actions[0], '???')
            a2 = ACTION_DISPLAY_NAMES.get(actions[1], '???')
            return f"{name}: [{a1}] [{a2}]"
        elif len(actions) == 1:
            a1 = ACTION_DISPLAY_NAMES.get(actions[0], '???')
            return f"{name}: [{a1}] [____]"
        else:
            return f"{name}: [____] [____]"
    
    def toggle_log_mode(self, instance):
        """切换日志模式"""
        self.simple_log_mode = not self.simple_log_mode
        # TODO: 实现简洁日志
    
    def show_game_over(self, winner):
        """显示游戏结束"""
        content = BoxLayout(orientation='vertical', spacing=20, padding=20)
        
        if winner == "平局 / Draw":
            result_text = "平局！\nDraw!"
        else:
            result_text = f"{winner} 获胜！\n{winner} Wins!"
        
        result_label = Label(text=result_text, font_size='48sp')
        content.add_widget(result_label)
        
        button_layout = BoxLayout(size_hint=(1, None), height=80, spacing=20)
        
        restart_btn = Button(text='重新开始\nRestart', background_color=(0.2, 0.8, 0.2, 1))
        menu_btn = Button(text='返回菜单\nMenu', background_color=(0.8, 0.2, 0.2, 1))
        
        popup = Popup(
            title='游戏结束 Game Over',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        restart_btn.bind(on_press=lambda x: [popup.dismiss(), self.init_game()])
        menu_btn.bind(on_press=lambda x: [popup.dismiss(), setattr(self.manager, 'current', 'menu')])
        
        button_layout.add_widget(restart_btn)
        button_layout.add_widget(menu_btn)
        content.add_widget(button_layout)
        
        popup.open()


class GameArea(Widget):
    """游戏区域（绘制玩家和网格）"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.p1 = None
        self.p2 = None
        
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_bg, pos=self._update_bg)
    
    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos
    
    def update_players(self, p1, p2):
        """更新玩家"""
        self.p1 = p1
        self.p2 = p2
        self.canvas.after.clear()
        
        with self.canvas.after:
            # 绘制网格
            Color(0.7, 0.7, 0.7, 1)
            grid_y = self.y + self.height * 0.3
            grid_width = self.width * 0.8
            grid_x = self.x + self.width * 0.1
            cell_width = grid_width / MAP_SIZE
            
            for i in range(MAP_SIZE + 1):
                x = grid_x + i * cell_width
                Line(points=[x, grid_y, x, grid_y + 80], width=2)
            
            Line(points=[grid_x, grid_y, grid_x + grid_width, grid_y], width=2)
            Line(points=[grid_x, grid_y + 80, grid_x + grid_width, grid_y + 80], width=2)
            
            # 绘制格子编号
            Color(0, 0, 0, 1)
            for i in range(MAP_SIZE):
                # 这里需要用Label，简化处理
                pass
            
            # 绘制玩家1
            if p1:
                x = grid_x + (p1.position - 1) * cell_width + cell_width / 2
                y = grid_y + 40
                
                Color(1, 0.2, 0.2, 1)  # 红色
                Ellipse(pos=(x - 25, y - 25), size=(50, 50))
                
                # 血条
                Color(0.2, 0.8, 0.2, 1)
                hp_ratio = p1.hp / p1.max_hp
                Rectangle(pos=(x - 30, y + 35), size=(60 * hp_ratio, 8))
            
            # 绘制玩家2
            if p2:
                x = grid_x + (p2.position - 1) * cell_width + cell_width / 2
                y = grid_y + 40
                
                Color(0.2, 0.2, 1, 1)  # 蓝色
                Ellipse(pos=(x - 25, y - 25), size=(50, 50))
                
                # 血条
                Color(0.2, 0.8, 0.2, 1)
                hp_ratio = p2.hp / p2.max_hp
                Rectangle(pos=(x - 30, y + 35), size=(60 * hp_ratio, 8))


class SkillButtonGrid(GridLayout):
    """技能按钮网格"""
    
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.cols = 6
        self.rows = 2
        self.spacing = 10
        self.size_hint = (1, None)
        self.height = 220
        self.game_screen = game_screen
        
        skills = [
            ('attack', 'J\n攻击\nAttack', (1, 0.2, 0.2, 1)),
            ('charge', 'I\n蓄力\nCharge', (0.8, 0.2, 1, 1)),
            ('control', 'K\n控制\nControl', (1, 0.6, 0, 1)),
            ('grab', '1\n抱摔\nGrab', (1, 0.6, 0, 1)),
            ('throw', '2\n投掷\nThrow', (1, 0.6, 0, 1)),
            ('defend', 'S\n防御\nDefend', (0.2, 0.8, 0.2, 1)),
            ('counter', 'W\n反击\nCounter', (0.2, 0.8, 0.2, 1)),
            ('move_left', 'A\n左移\nLeft', (0.2, 0.5, 1, 1)),
            ('move_right', 'D\n右移\nRight', (0.2, 0.5, 1, 1)),
            ('dash_left', 'Q\n左冲\nDashL', (0.2, 0.5, 1, 1)),
            ('dash_right', 'E\n右冲\nDashR', (0.2, 0.5, 1, 1)),
            ('burst', 'O\n爆血\nBurst', (1, 0.4, 0, 1)),
        ]
        
        for action, text, color in skills:
            btn = Button(
                text=text,
                font_size='20sp',
                background_color=color,
                background_normal=''
            )
            btn.bind(on_press=lambda x, a=action: self.game_screen.on_skill_selected(a))
            self.add_widget(btn)


class BattleGameApp(App):
    """主应用"""
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm


if __name__ == '__main__':
    BattleGameApp().run()