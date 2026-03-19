"""
human_vs_ai.py
人机对战模式 - 玩家 vs AI
Human vs AI Mode - Player vs AI
"""

import sys
from player import Player
from combat_manager import CombatManager
from ai_player import AIPlayer
from config import *
from game_data import ACTION_KEY_MAP, ACTION_DISPLAY_NAMES


class HumanVsAI:
    """人机对战管理器"""
    
    def __init__(self, player_is_p1=True):
        """
        初始化
        player_is_p1: True表示玩家控制P1(Red), False表示玩家控制P2(Blue)
        """
        self.player_is_p1 = player_is_p1
        self.player1 = None
        self.player2 = None
        self.combat = None
        self.ai = None
        
        self.human_actions = []
        self.ai_actions = []
        
    def start_game(self):
        """开始游戏"""
        print("\n" + "="*60)
        print("人机对战模式 / Human vs AI Mode")
        print("="*60)
        
        # 初始化玩家
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        
        # 初始化战斗管理器
        self.combat = CombatManager(self.player1, self.player2)
        
        # 创建AI
        if self.player_is_p1:
            self.ai = AIPlayer(self.player2, self.player1, self.combat)
            print(f"你控制: {PLAYER1_NAME} (Red)")
            print(f"AI控制: {PLAYER2_NAME} (Blue)")
        else:
            self.ai = AIPlayer(self.player1, self.player2, self.combat)
            print(f"AI控制: {PLAYER1_NAME} (Red)")
            print(f"你控制: {PLAYER2_NAME} (Blue)")
        
        print("="*60)
        
        self._show_controls()
        input("\n按回车开始游戏... / Press Enter to start...")
        
        # 游戏循环
        self._game_loop()
    
    def _show_controls(self):
        """显示操作说明"""
        print("\n【操作说明 / Controls】")
        print("-"*60)
        print("J - 攻击 Attack       | I - 蓄力 Charge      | K - 控制 Control")
        print("1 - 抱摔 Grab         | 2 - 投掷 Throw       | S - 防御 Defend")
        print("W - 反击 Counter      | O - 爆血 Burst")
        print("A - 左移 Left         | D - 右移 Right")
        print("Q - 左冲 Dash Left    | E - 右冲 Dash Right")
        print("-"*60)
        print("提示: 每回合输入2个动作（两帧），输入完成后按回车确认")
        print("Tip: Enter 2 actions per turn (two frames), press Enter to confirm")
        print("-"*60)
    
    def _game_loop(self):
        """游戏主循环"""
        while self.player1.is_alive() and self.player2.is_alive() and self.combat.turn < MAX_TURNS:
            self._show_game_state()
            
            # 玩家输入
            print(f"\n【回合 {self.combat.turn + 1} / Turn {self.combat.turn + 1}】")
            self.human_actions = self._get_human_actions()
            
            # AI决策
            self.ai_actions = self.ai.choose_turn_actions()
            print(f"AI已选择动作... / AI has chosen actions...")
            
            # 执行回合
            if self.player_is_p1:
                self.combat.execute_turn(self.human_actions, self.ai_actions)
            else:
                self.combat.execute_turn(self.ai_actions, self.human_actions)
            
            # 显示AI的动作
            self._reveal_ai_actions()
            
            input("\n按回车继续... / Press Enter to continue...")
        
        # 游戏结束
        self._show_game_over()
    
    def _show_game_state(self):
        """显示当前游戏状态"""
        print("\n" + "="*60)
        print("【当前状态 / Current State】")
        print("="*60)
        
        # 显示玩家信息
        self.player1.show_status()
        self.player2.show_status()
        print(f"距离: {self.combat.get_distance()}格 / Distance: {self.combat.get_distance()} spaces")
        
        # 显示位置图
        self._draw_position_map()
        
        print("="*60)
    
    def _draw_position_map(self):
        """绘制位置图（简单版本）"""
        print("\n位置图 / Position Map:")
        
        # 创建地图
        map_line = [' . '] * 6
        
        # 标记玩家位置
        p1_pos = self.player1.position - 1
        p2_pos = self.player2.position - 1
        
        if p1_pos == p2_pos:
            map_line[p1_pos] = '[RB]'
        else:
            map_line[p1_pos] = '[R]'
            map_line[p2_pos] = '[B]'
        
        # 打印地图
        print(' '.join(map_line))
        print(' '.join(f' {i+1} ' for i in range(6)))
        
        # 图例
        print("图例: [R]=Red  [B]=Blue  [RB]=重叠 / Legend: [R]=Red  [B]=Blue  [RB]=Overlap")
    
    def _get_human_actions(self) -> list:
        """获取玩家输入的动作"""
        actions = []
        next_turn = self.combat.turn + 1
        
        # 获取玩家的Player对象
        human_player = self.player1 if self.player_is_p1 else self.player2
        
        for frame in range(1, 3):
            # 检查是否硬直
            if human_player.is_frame_locked(next_turn, frame):
                print(f"第{frame}帧: 硬直状态！只能使用爆血(O) / Frame {frame}: Stunned! Can only use Burst (O)")
                action = self._input_action(frame, stunned=True)
            # 检查是否被控制
            elif human_player.controlled and frame == 1:
                print(f"第{frame}帧: 被控制！只能使用防御(S)或爆血(O) / Frame {frame}: Controlled! Can only use Defend (S) or Burst (O)")
                action = self._input_action(frame, controlled=True)
            else:
                action = self._input_action(frame)
            
            actions.append(action)
            
            # 显示已选择的动作
            if action:
                action_name = ACTION_DISPLAY_NAMES.get(action, action)
                print(f"  ✓ 第{frame}帧: {action_name}")
        
        return actions
    
    def _input_action(self, frame: int, stunned=False, controlled=False) -> str:
        """输入单个动作"""
        while True:
            prompt = f"第{frame}帧动作 / Frame {frame} action: "
            key = input(prompt).strip().lower()
            
            if not key:
                print("无效输入！请输入动作按键 / Invalid input! Please enter action key")
                continue
            
            # 检查按键是否有效
            if key not in ACTION_KEY_MAP:
                print(f"未知按键: {key} / Unknown key: {key}")
                continue
            
            action = ACTION_KEY_MAP[key]
            
            # 硬直状态检查
            if stunned and action != 'burst':
                print("硬直状态只能使用爆血(O)！ / Can only use Burst (O) when stunned!")
                continue
            
            # 被控制状态检查
            if controlled and action not in ['defend', 'burst']:
                print("被控制状态只能使用防御(S)或爆血(O)！ / Can only use Defend (S) or Burst (O) when controlled!")
                continue
            
            return action
    
    def _reveal_ai_actions(self):
        """显示AI的动作"""
        print("\n" + "-"*60)
        print("【AI动作揭晓 / AI Actions Revealed】")
        
        ai_name = PLAYER2_NAME if self.player_is_p1 else PLAYER1_NAME
        
        for i, action in enumerate(self.ai_actions, 1):
            if action:
                action_name = ACTION_DISPLAY_NAMES.get(action, action)
                print(f"{ai_name} 第{i}帧: {action_name}")
            else:
                print(f"{ai_name} 第{i}帧: (无动作/硬直)")
        
        print("-"*60)
    
    def _show_game_over(self):
        """显示游戏结束"""
        print("\n" + "="*60)
        print("【游戏结束 / Game Over】")
        print("="*60)
        
        winner = self.combat.get_winner()
        
        if winner == "平局 / Draw":
            print("平局！ / Draw!")
        else:
            # 判断玩家是否获胜
            player_name = PLAYER1_NAME if self.player_is_p1 else PLAYER2_NAME
            if winner == player_name:
                print(f"🎉 恭喜！你获胜了！ / Congratulations! You win!")
            else:
                print(f"💔 很遗憾，AI获胜了！ / Sorry, AI wins!")
        
        print(f"\n最终状态 / Final State:")
        self.player1.show_status()
        self.player2.show_status()
        print(f"总回合数: {self.combat.turn} / Total turns: {self.combat.turn}")
        
        print("="*60)
        
        # 显示AI统计
        self._show_ai_stats()
    
    def _show_ai_stats(self):
        """显示AI统计信息"""
        stats = self.ai.get_stats()
        
        print("\n【AI统计 / AI Statistics】")
        print("-"*60)
        print(f"总决策数: {stats['total_decisions']} / Total decisions: {stats['total_decisions']}")
        
        print("\n决策层使用 / Layer usage:")
        for layer, count in sorted(stats['layer_usage'].items()):
            percentage = count / stats['total_decisions'] * 100 if stats['total_decisions'] > 0 else 0
            layer_names = {
                1: "强制状态 / Forced",
                2: "连击系统 / Combo",
                3: "蓄力威胁 / Charge",
                4: "距离战术 / Distance",
                5: "特殊战术 / Special"
            }
            print(f"  层{layer} ({layer_names.get(layer, 'Unknown')}): {count} ({percentage:.1f}%)")
        
        print("\n动作分布 / Action distribution:")
        sorted_actions = sorted(stats['action_counts'].items(), key=lambda x: x[1], reverse=True)
        for action, count in sorted_actions[:10]:  # 显示前10个
            percentage = count / stats['total_decisions'] * 100
            action_name = ACTION_DISPLAY_NAMES.get(action, action)
            print(f"  {action_name:15s}: {count:3d} ({percentage:.1f}%)")
        
        print("-"*60)


def main():
    """主函数"""
    print("\n" + "#"*60)
    print("欢迎来到人机对战模式！ / Welcome to Human vs AI Mode!")
    print("#"*60)
    
    # 选择玩家方
    print("\n请选择你要控制的角色 / Choose your character:")
    print("1. Red (玩家1，左侧起始)")
    print("2. Blue (玩家2，右侧起始)")
    
    while True:
        choice = input("\n选择 (1/2): ").strip()
        if choice == '1':
            player_is_p1 = True
            break
        elif choice == '2':
            player_is_p1 = False
            break
        else:
            print("无效选择，请输入1或2 / Invalid choice, please enter 1 or 2")
    
    # 开始游戏
    game = HumanVsAI(player_is_p1)
    game.start_game()
    
    # 询问是否再来一局
    while True:
        again = input("\n再来一局? (y/n): ").strip().lower()
        if again == 'y':
            game = HumanVsAI(player_is_p1)
            game.start_game()
        elif again == 'n':
            print("\n感谢游玩！ / Thanks for playing!")
            break
        else:
            print("无效输入 / Invalid input")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n游戏中断 / Game interrupted")
        sys.exit(0)