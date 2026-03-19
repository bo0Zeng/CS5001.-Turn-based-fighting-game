"""
self_play.py
Self-Play训练框架 - AI vs AI自我对弈
Self-Play Training Framework - AI vs AI matches
"""

import json
import time
from typing import List, Dict, Any
from datetime import datetime
from player import Player
from combat_manager import CombatManager
from ai_player import AIPlayer
from config import *


class SelfPlayTrainer:
    """Self-Play训练器"""
    
    def __init__(self):
        self.match_history = []
        self.generation = 0
        self.training_stats = {
            'total_matches': 0,
            'total_turns': 0,
            'avg_turns_per_match': 0.0,
            'p1_wins': 0,
            'p2_wins': 0,
            'draws': 0,
            'generation_history': []
        }
    
    def run_match(self, verbose=False) -> Dict[str, Any]:
        """运行一场AI vs AI对局"""
        # 初始化玩家
        player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        
        # 初始化战斗管理器
        combat = CombatManager(player1, player2)
        
        # 创建AI玩家
        ai1 = AIPlayer(player1, player2, combat)
        ai2 = AIPlayer(player2, player1, combat)
        
        match_data = {
            'start_time': datetime.now().isoformat(),
            'turns': [],
            'winner': None,
            'total_turns': 0,
            'final_hp': {'p1': 0, 'p2': 0},
            'ai1_stats': None,
            'ai2_stats': None
        }
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"开始新对局 / Starting New Match")
            print(f"{'='*60}")
        
        # 对局循环
        while player1.is_alive() and player2.is_alive() and combat.turn < MAX_TURNS:
            # AI选择动作
            p1_actions = ai1.choose_turn_actions()
            p2_actions = ai2.choose_turn_actions()
            
            if verbose:
                print(f"\n回合 {combat.turn + 1}:")
                print(f"  {PLAYER1_NAME}: {p1_actions}")
                print(f"  {PLAYER2_NAME}: {p2_actions}")
            
            # 记录回合数据
            turn_data = {
                'turn_number': combat.turn + 1,
                'p1_actions': p1_actions,
                'p2_actions': p2_actions,
                'distance_before': combat.get_distance(),
                'hp_before': {'p1': player1.hp, 'p2': player2.hp}
            }
            
            # 执行回合
            combat.execute_turn(p1_actions, p2_actions)
            
            turn_data['distance_after'] = combat.get_distance()
            turn_data['hp_after'] = {'p1': player1.hp, 'p2': player2.hp}
            match_data['turns'].append(turn_data)
            
            if verbose:
                print(f"  结果: {PLAYER1_NAME} HP={player1.hp}, {PLAYER2_NAME} HP={player2.hp}, 距离={combat.get_distance()}")
        
        # 记录最终结果
        match_data['total_turns'] = combat.turn
        match_data['final_hp'] = {'p1': player1.hp, 'p2': player2.hp}
        match_data['winner'] = combat.get_winner()
        match_data['ai1_stats'] = ai1.get_stats()
        match_data['ai2_stats'] = ai2.get_stats()
        match_data['end_time'] = datetime.now().isoformat()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"对局结束 / Match Ended")
            print(f"获胜者: {match_data['winner']} / Winner: {match_data['winner']}")
            print(f"回合数: {match_data['total_turns']} / Turns: {match_data['total_turns']}")
            print(f"最终HP: {PLAYER1_NAME}={player1.hp}, {PLAYER2_NAME}={player2.hp}")
            print(f"{'='*60}")
        
        # 更新统计
        self._update_stats(match_data)
        self.match_history.append(match_data)
        
        return match_data
    
    def run_generation(self, num_matches=100, verbose_interval=10):
        """运行一代训练（多场对局）"""
        self.generation += 1
        
        print(f"\n{'#'*60}")
        print(f"开始第 {self.generation} 代训练 / Starting Generation {self.generation}")
        print(f"对局数: {num_matches} / Matches: {num_matches}")
        print(f"{'#'*60}\n")
        
        generation_data = {
            'generation': self.generation,
            'num_matches': num_matches,
            'matches': [],
            'stats': {
                'p1_wins': 0,
                'p2_wins': 0,
                'draws': 0,
                'avg_turns': 0.0,
                'avg_final_hp_diff': 0.0
            }
        }
        
        start_time = time.time()
        
        for i in range(num_matches):
            verbose = (i + 1) % verbose_interval == 0
            match_data = self.run_match(verbose=verbose)
            generation_data['matches'].append(match_data)
            
            # 更新代统计
            winner = match_data['winner']
            if winner == PLAYER1_NAME:
                generation_data['stats']['p1_wins'] += 1
            elif winner == PLAYER2_NAME:
                generation_data['stats']['p2_wins'] += 1
            else:
                generation_data['stats']['draws'] += 1
            
            if (i + 1) % verbose_interval == 0:
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed
                print(f"进度: {i+1}/{num_matches} ({(i+1)/num_matches*100:.1f}%) | "
                      f"速度: {speed:.2f} 局/秒 | "
                      f"预计剩余: {(num_matches-i-1)/speed:.1f}秒")
        
        # 计算平均统计
        total_turns = sum(m['total_turns'] for m in generation_data['matches'])
        generation_data['stats']['avg_turns'] = total_turns / num_matches
        
        total_hp_diff = sum(
            abs(m['final_hp']['p1'] - m['final_hp']['p2'])
            for m in generation_data['matches']
        )
        generation_data['stats']['avg_final_hp_diff'] = total_hp_diff / num_matches
        
        # 保存代数据
        self.training_stats['generation_history'].append(generation_data['stats'])
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'#'*60}")
        print(f"第 {self.generation} 代完成 / Generation {self.generation} Complete")
        print(f"{'#'*60}")
        print(f"{PLAYER1_NAME} 胜利: {generation_data['stats']['p1_wins']} "
              f"({generation_data['stats']['p1_wins']/num_matches*100:.1f}%)")
        print(f"{PLAYER2_NAME} 胜利: {generation_data['stats']['p2_wins']} "
              f"({generation_data['stats']['p2_wins']/num_matches*100:.1f}%)")
        print(f"平局: {generation_data['stats']['draws']} "
              f"({generation_data['stats']['draws']/num_matches*100:.1f}%)")
        print(f"平均回合数: {generation_data['stats']['avg_turns']:.2f}")
        print(f"平均HP差: {generation_data['stats']['avg_final_hp_diff']:.2f}")
        print(f"总耗时: {elapsed_time:.2f}秒")
        print(f"速度: {num_matches/elapsed_time:.2f} 局/秒")
        print(f"{'#'*60}\n")
        
        return generation_data
    
    def _update_stats(self, match_data: Dict[str, Any]):
        """更新总体统计"""
        self.training_stats['total_matches'] += 1
        self.training_stats['total_turns'] += match_data['total_turns']
        self.training_stats['avg_turns_per_match'] = (
            self.training_stats['total_turns'] / self.training_stats['total_matches']
        )
        
        winner = match_data['winner']
        if winner == PLAYER1_NAME:
            self.training_stats['p1_wins'] += 1
        elif winner == PLAYER2_NAME:
            self.training_stats['p2_wins'] += 1
        else:
            self.training_stats['draws'] += 1
    
    def analyze_patterns(self, last_n_matches=100):
        """分析最近N场对局的模式"""
        if not self.match_history:
            print("没有对局数据 / No match history")
            return
        
        recent_matches = self.match_history[-last_n_matches:]
        
        print(f"\n{'='*60}")
        print(f"分析最近 {len(recent_matches)} 场对局 / Analyzing Last {len(recent_matches)} Matches")
        print(f"{'='*60}\n")
        
        # 统计动作使用频率
        action_counts = {}
        for match in recent_matches:
            for turn in match['turns']:
                for action in turn['p1_actions'] + turn['p2_actions']:
                    if action:
                        action_counts[action] = action_counts.get(action, 0) + 1
        
        print("动作使用频率 / Action Usage:")
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        for action, count in sorted_actions:
            percentage = count / sum(action_counts.values()) * 100
            print(f"  {action:15s}: {count:5d} ({percentage:5.2f}%)")
        
        # 统计获胜方式
        print("\n获胜统计 / Win Statistics:")
        winner_stats = {'Red': 0, 'Blue': 0, '平局 / Draw': 0}
        for match in recent_matches:
            winner = match['winner']
            if winner in winner_stats:
                winner_stats[winner] += 1
            else:
                winner_stats['平局 / Draw'] += 1
        
        for winner, count in winner_stats.items():
            percentage = count / len(recent_matches) * 100
            print(f"  {winner:15s}: {count:5d} ({percentage:5.2f}%)")
        
        # 统计回合数分布
        turn_counts = [m['total_turns'] for m in recent_matches]
        avg_turns = sum(turn_counts) / len(turn_counts)
        min_turns = min(turn_counts)
        max_turns = max(turn_counts)
        
        print(f"\n回合数统计 / Turn Statistics:")
        print(f"  平均回合数 / Average: {avg_turns:.2f}")
        print(f"  最少回合数 / Minimum: {min_turns}")
        print(f"  最多回合数 / Maximum: {max_turns}")
        
        # 统计HP差
        hp_diffs = [abs(m['final_hp']['p1'] - m['final_hp']['p2']) for m in recent_matches]
        avg_hp_diff = sum(hp_diffs) / len(hp_diffs)
        
        print(f"\n最终HP差 / Final HP Difference:")
        print(f"  平均HP差 / Average: {avg_hp_diff:.2f}")
        
        print(f"\n{'='*60}\n")
    
    def save_training_data(self, filename='training_data.json'):
        """保存训练数据"""
        data = {
            'generation': self.generation,
            'stats': self.training_stats,
            'match_history': self.match_history[-1000:]  # 只保存最近1000场
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"训练数据已保存到 {filename} / Training data saved to {filename}")
    
    def load_training_data(self, filename='training_data.json'):
        """加载训练数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.generation = data['generation']
            self.training_stats = data['stats']
            self.match_history = data['match_history']
            
            print(f"训练数据已从 {filename} 加载 / Training data loaded from {filename}")
            print(f"当前代数: {self.generation} / Current generation: {self.generation}")
            print(f"总对局数: {self.training_stats['total_matches']} / Total matches: {self.training_stats['total_matches']}")
        except FileNotFoundError:
            print(f"文件 {filename} 不存在 / File {filename} not found")
        except Exception as e:
            print(f"加载失败: {e} / Loading failed: {e}")
    
    def get_summary(self):
        """获取训练总结"""
        print(f"\n{'='*60}")
        print("训练总结 / Training Summary")
        print(f"{'='*60}")
        print(f"代数 / Generation: {self.generation}")
        print(f"总对局数 / Total Matches: {self.training_stats['total_matches']}")
        print(f"总回合数 / Total Turns: {self.training_stats['total_turns']}")
        print(f"平均回合/局 / Avg Turns/Match: {self.training_stats['avg_turns_per_match']:.2f}")
        print(f"\n胜率统计 / Win Rate:")
        
        total = self.training_stats['total_matches']
        if total > 0:
            p1_rate = self.training_stats['p1_wins'] / total * 100
            p2_rate = self.training_stats['p2_wins'] / total * 100
            draw_rate = self.training_stats['draws'] / total * 100
            
            print(f"  {PLAYER1_NAME}: {self.training_stats['p1_wins']} ({p1_rate:.2f}%)")
            print(f"  {PLAYER2_NAME}: {self.training_stats['p2_wins']} ({p2_rate:.2f}%)")
            print(f"  平局 / Draws: {self.training_stats['draws']} ({draw_rate:.2f}%)")
        
        print(f"{'='*60}\n")


def main():
    """主函数 - 运行训练"""
    trainer = SelfPlayTrainer()
    
    print("Self-Play AI训练系统 / Self-Play AI Training System")
    print("="*60)
    
    # 运行训练
    num_generations = 5
    matches_per_generation = 100
    
    for gen in range(num_generations):
        trainer.run_generation(num_matches=matches_per_generation, verbose_interval=20)
        
        # 每代结束后分析
        if (gen + 1) % 1 == 0:
            trainer.analyze_patterns(last_n_matches=matches_per_generation)
        
        # 保存数据
        if (gen + 1) % 2 == 0:
            trainer.save_training_data(f'training_gen_{gen+1}.json')
    
    # 最终总结
    trainer.get_summary()
    trainer.save_training_data('training_final.json')
    
    print("\n训练完成！ / Training Complete!")


if __name__ == "__main__":
    main()