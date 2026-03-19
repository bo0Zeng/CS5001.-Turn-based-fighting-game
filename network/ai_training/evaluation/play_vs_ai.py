"""
play_vs_ai.py
人机对战接口 / Human vs AI Interface

允许人类玩家对战训练好的AI

使用方法：
python play_vs_ai.py --model saved_models/ppo/run_XXX/final_model.pth
"""

import sys
import os
import argparse

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

import numpy as np
import torch
from environment import BattleEnv, ActionSpace
from agents import PPOAgent


class HumanVsAI:
    """人机对战管理器"""
    
    def __init__(self, env: BattleEnv, ai_agent: BaseAgent):
        """
        初始化人机对战
        
        Args:
            env: 游戏环境
            ai_agent: AI智能体
        """
        self.env = env
        self.ai_agent = ai_agent
        self.action_space = ActionSpace()
        
        # 设置AI为评估模式
        if hasattr(ai_agent, 'set_training_mode'):
            ai_agent.set_training_mode(False)
    
    def play_game(self, human_is_p1: bool = True) -> Dict[str, any]:
        """
        进行一局游戏
        
        Args:
            human_is_p1: 人类是否是玩家1
        
        Returns:
            游戏结果
        """
        obs = self.env.reset()
        done = False
        turn = 0
        
        print("\n" + "="*60)
        print("🎮 游戏开始！/ Game Start!")
        print("="*60)
        
        while not done:
            turn += 1
            
            # 显示当前状态
            self._show_game_state(turn)
            
            # 获取双方动作
            if human_is_p1:
                p1_actions = self._get_human_actions(player_id=1)
                
                # AI选择动作
                valid_p2 = self.env.get_valid_actions(player_id=2)
                mask_p2 = np.zeros(12, dtype=bool)
                mask_p2[valid_p2] = True
                p2_actions = self.ai_agent.select_action(obs, mask_p2, deterministic=True)
                
                print(f"🤖 AI (P2) 选择: {self._format_actions(p2_actions)}")
            else:
                # AI选择动作
                valid_p1 = self.env.get_valid_actions(player_id=1)
                mask_p1 = np.zeros(12, dtype=bool)
                mask_p1[valid_p1] = True
                p1_actions = self.ai_agent.select_action(obs, mask_p1, deterministic=True)
                
                print(f"🤖 AI (P1) 选择: {self._format_actions(p1_actions)}")
                
                p2_actions = self._get_human_actions(player_id=2)
            
            # 执行回合
            print("\n执行回合...")
            obs, p1_reward, p2_reward, done, info = self.env.step(p1_actions, p2_actions)
            
            # 显示回合结果
            self._show_turn_result(info)
        
        # 游戏结束
        winner = info.get('winner')
        
        print("\n" + "="*60)
        print("🏁 游戏结束！/ Game Over!")
        print("="*60)
        
        if winner == "Draw":
            print("🤝 平局！/ Draw!")
        elif (human_is_p1 and winner == self.env.player1.name) or \
             (not human_is_p1 and winner == self.env.player2.name):
            print("🎉 你赢了！/ You Win!")
        else:
            print("😢 AI赢了！/ AI Wins!")
        
        print(f"\n最终状态:")
        print(f"  {self.env.player1.name}: {self.env.player1.hp}/{self.env.player1.max_hp} HP")
        print(f"  {self.env.player2.name}: {self.env.player2.hp}/{self.env.player2.max_hp} HP")
        print(f"  总回合数: {turn}")
        
        return {
            'winner': winner,
            'turns': turn,
            'p1_hp': self.env.player1.hp,
            'p2_hp': self.env.player2.hp,
        }
    
    def _get_human_actions(self, player_id: int) -> Tuple[int, int]:
        """
        获取人类玩家输入
        
        Args:
            player_id: 玩家ID
        
        Returns:
            (action1, action2)
        """
        player_name = "你 (You)" if player_id == 1 else "你 (You)"
        
        print(f"\n👤 {player_name} 的回合:")
        print("可用动作:")
        self._show_available_actions()
        
        # 获取有效动作
        valid_actions = self.env.get_valid_actions(player_id)
        
        actions = []
        for frame in [1, 2]:
            while True:
                try:
                    action_input = input(f"  第{frame}帧动作 (输入数字0-11): ").strip()
                    action_id = int(action_input)
                    
                    if action_id in valid_actions:
                        action_name = self.action_space.get_action_name(action_id)
                        print(f"    ✅ 选择: {action_name}")
                        actions.append(action_id)
                        break
                    else:
                        print(f"    ❌ 动作{action_id}不可用，请重新选择")
                        print(f"    有效动作: {valid_actions}")
                except (ValueError, KeyboardInterrupt):
                    print("    ❌ 无效输入，请输入0-11的数字")
        
        return tuple(actions)
    
    def _show_available_actions(self):
        """显示可用动作列表"""
        for action_id in range(12):
            action_name = self.action_space.get_action_name(action_id)
            desc = self.action_space.describe_action(action_id)
            print(f"  {action_id}: {action_name:12s} - {desc}")
    
    def _format_actions(self, actions: Tuple[int, int]) -> str:
        """格式化动作显示"""
        name1 = self.action_space.get_action_name(actions[0])
        name2 = self.action_space.get_action_name(actions[1])
        return f"[{name1}, {name2}]"
    
    def _show_game_state(self, turn: int):
        """显示游戏状态"""
        print(f"\n{'─'*60}")
        print(f"📍 回合 {turn} | 距离: {self.env.combat.get_distance()} 格")
        print(f"{'─'*60}")
        
        # 显示玩家状态
        for player in [self.env.player1, self.env.player2]:
            status_icons = []
            if player.controlled:
                status_icons.append("🔒控制")
            if player.charge_level > 0:
                status_icons.append(f"⚡蓄{player.charge_level}")
            if player.dash_buff_stacks > 0:
                status_icons.append(f"💨冲{player.dash_buff_stacks}")
            
            status_str = " ".join(status_icons) if status_icons else ""
            
            hp_bar = "█" * (player.hp * 2) + "░" * ((player.max_hp - player.hp) * 2)
            
            print(f"{player.name:5s}: {hp_bar} {player.hp:2d}/{player.max_hp} HP  位置:{player.position}  {status_str}")
    
    def _show_turn_result(self, info: Dict):
        """显示回合结果"""
        print(f"\n回合结束:")
        print(f"  {self.env.player1.name}: {self.env.player1.hp} HP (位置 {self.env.player1.position})")
        print(f"  {self.env.player2.name}: {self.env.player2.hp} HP (位置 {self.env.player2.position})")
        print(f"  距离: {self.env.combat.get_distance()} 格")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="人类对战AI")
    
    parser.add_argument('--model', type=str, required=True,
                       help='AI模型路径')
    parser.add_argument('--human-first', action='store_true',
                       help='人类先手（玩家1）')
    parser.add_argument('--num-games', type=int, default=1,
                       help='对战局数')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    print("="*60)
    print("🎮 人类 vs AI 对战系统")
    print("="*60)
    
    # 加载AI
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    ai_agent = PPOAgent(state_dim=66, action_dim=12, device=device)
    
    if os.path.exists(args.model):
        ai_agent.load(args.model)
        print(f"✅ AI模型已加载: {args.model}")
    else:
        print(f"⚠️  模型文件不存在，使用未训练的AI: {args.model}")
    
    # 创建环境
    env = BattleEnv(reward_type='dense', verbose=True)
    
    # 创建对战管理器
    game = HumanVsAI(env, ai_agent)
    
    # 开始对战
    human_wins = 0
    ai_wins = 0
    draws = 0
    
    for game_num in range(args.num_games):
        if args.num_games > 1:
            print(f"\n\n{'='*60}")
            print(f"第 {game_num + 1}/{args.num_games} 局")
            print(f"{'='*60}")
        
        result = game.play_game(human_is_p1=args.human_first)
        
        winner = result['winner']
        human_player = env.player1.name if args.human_first else env.player2.name
        
        if winner == human_player:
            human_wins += 1
        elif winner == "Draw":
            draws += 1
        else:
            ai_wins += 1
    
    # 总结
    if args.num_games > 1:
        print("\n" + "="*60)
        print("📊 对战总结 / Match Summary")
        print("="*60)
        print(f"人类胜: {human_wins}")
        print(f"AI胜: {ai_wins}")
        print(f"平局: {draws}")
        print(f"人类胜率: {human_wins / args.num_games * 100:.1f}%")
        print("="*60)


if __name__ == "__main__":
    # 如果没有命令行参数，使用交互式模式
    if len(sys.argv) == 1:
        print("="*60)
        print("🎮 人类 vs AI 对战系统（交互式）")
        print("="*60)
        
        # 创建未训练的AI（用于演示）
        print("\n⚠️  使用未训练的AI进行演示")
        print("如需使用训练好的AI，请用: python play_vs_ai.py --model <模型路径>")
        
        device = torch.device('cpu')
        ai_agent = PPOAgent(state_dim=66, action_dim=12, device=device)
        
        env = BattleEnv(reward_type='dense', verbose=False)
        game = HumanVsAI(env, ai_agent)
        
        game.play_game(human_is_p1=True)
    else:
        main()