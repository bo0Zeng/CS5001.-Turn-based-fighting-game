"""
ai_trainer.py
AI训练与优化工具 - 参数调优和策略进化
AI Training and Optimization Tool - Parameter tuning and strategy evolution
"""

import json
import copy
import random
import sys
from typing import Dict, List, Tuple, Any
from datetime import datetime


class AIEvolver:
    """AI进化器 - 通过参数调优提升AI性能"""
    
    def __init__(self):
        self.population = []
        self.generation = 0
        self.best_genome = None
        self.evolution_history = []
    
    def create_genome(self) -> Dict[str, Any]:
        """创建基因组（AI参数配置）"""
        return {
            'id': self._generate_id(),
            'generation': self.generation,
            'parameters': {
                # 预测概率调整
                'attack_prediction_base': 0.35,
                'attack_prediction_modifiers': {
                    'charge2': 0.45,
                    'charge1': 0.15,
                    'buff2': 0.2,
                    'hp_advantage': 0.15,
                    'hp_disadvantage': -0.2,
                    'combo2': -0.3
                },
                'defend_prediction_base': 0.2,
                'defend_prediction_modifiers': {
                    'self_charge2': 0.4,
                    'self_buff2': 0.3,
                    'opp_combo2': 0.4,
                    'hp_disadvantage': 0.3
                },
                
                # 距离战术权重（距离0）
                'distance_0_weights': {
                    'control_grab': 0.5,
                    'dash_retreat': 0.35,
                    'counter': 0.15
                },
                
                # 距离战术权重（距离1）
                'distance_1_weights': {
                    'control': 0.4,
                    'attack': 0.3,
                    'charge': 0.2,
                    'counter': 0.1
                },
                
                # 特殊战术阈值
                'burst_kill_threshold': {0: 0.9, 1: 0.8, 2: 0.7, 3: 0.6},
                'burst_trade_hp_threshold': 10,
                'burst_trade_min_hp': 15,
                'burst_desperate_hp': 6,
                
                # 边界战术
                'boundary_pressure_prob': 0.45,
                'boundary_escape_prob': 0.6,
                
                # 蓄力战术
                'charge2_release_prob': 0.7,
                'charge1_stack_prob': 0.5,
            },
            'fitness': 0.0,
            'matches_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0
        }
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"gen{self.generation}_{datetime.now().strftime('%H%M%S%f')}"
    
    def initialize_population(self, size=10):
        """初始化种群"""
        self.population = []
        for _ in range(size):
            genome = self.create_genome()
            self.population.append(genome)
        
        print(f"初始化种群: {size} 个个体 / Initialized population: {size} individuals")
    
    def mutate(self, genome: Dict[str, Any], mutation_rate=0.1) -> Dict[str, Any]:
        """变异基因组"""
        new_genome = copy.deepcopy(genome)
        new_genome['id'] = self._generate_id()
        new_genome['generation'] = self.generation
        
        params = new_genome['parameters']
        
        # 随机变异部分参数
        if random.random() < mutation_rate:
            params['attack_prediction_base'] += random.uniform(-0.05, 0.05)
            params['attack_prediction_base'] = max(0.1, min(0.9, params['attack_prediction_base']))
        
        if random.random() < mutation_rate:
            params['defend_prediction_base'] += random.uniform(-0.05, 0.05)
            params['defend_prediction_base'] = max(0.1, min(0.9, params['defend_prediction_base']))
        
        # 变异距离战术权重
        for distance_key in ['distance_0_weights', 'distance_1_weights']:
            if random.random() < mutation_rate:
                weights = params[distance_key]
                # 随机调整一个权重
                key = random.choice(list(weights.keys()))
                weights[key] += random.uniform(-0.1, 0.1)
                weights[key] = max(0.0, min(1.0, weights[key]))
                # 归一化
                total = sum(weights.values())
                for k in weights:
                    weights[k] /= total
        
        # 变异特殊战术阈值
        if random.random() < mutation_rate:
            threshold_key = random.choice([0, 1, 2, 3])
            params['burst_kill_threshold'][threshold_key] += random.uniform(-0.1, 0.1)
            params['burst_kill_threshold'][threshold_key] = max(0.5, min(1.0, params['burst_kill_threshold'][threshold_key]))
        
        return new_genome
    
    def crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """交叉两个基因组"""
        child = self.create_genome()
        child['id'] = self._generate_id()
        child['generation'] = self.generation
        
        # 随机选择参数来源
        p1_params = parent1['parameters']
        p2_params = parent2['parameters']
        child_params = child['parameters']
        
        # 基础预测概率
        child_params['attack_prediction_base'] = random.choice([
            p1_params['attack_prediction_base'],
            p2_params['attack_prediction_base']
        ])
        child_params['defend_prediction_base'] = random.choice([
            p1_params['defend_prediction_base'],
            p2_params['defend_prediction_base']
        ])
        
        # 距离战术权重
        for key in ['distance_0_weights', 'distance_1_weights']:
            if random.random() < 0.5:
                child_params[key] = copy.deepcopy(p1_params[key])
            else:
                child_params[key] = copy.deepcopy(p2_params[key])
        
        # 特殊战术阈值
        child_params['burst_kill_threshold'] = copy.deepcopy(
            random.choice([p1_params['burst_kill_threshold'], p2_params['burst_kill_threshold']])
        )
        
        return child
    
    def evaluate_genome(self, genome: Dict[str, Any], num_matches=50) -> float:
        """评估基因组性能"""
        from player import Player
        from combat_manager import CombatManager
        from ai_player import AIPlayer
        from config import PLAYER1_NAME, PLAYER2_NAME, PLAYER1_START_POS, PLAYER2_START_POS, MAX_TURNS
        import io
        
        print(f"  评估 {genome['id']}... ", end='', flush=True)
        
        wins = 0
        losses = 0
        draws = 0
        
        # 禁用print输出
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # 运行真实对局
            for _ in range(num_matches):
                # 初始化玩家
                p1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
                p2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
                combat = CombatManager(p1, p2)
                
                # 创建AI（测试基因组 vs 默认AI）
                test_ai = AIPlayer(p1, p2, combat)
                test_ai.evolved_params = genome['parameters']  # 使用测试参数
                
                default_ai = AIPlayer(p2, p1, combat)
                default_ai.evolved_params = None  # 使用默认参数
                
                # 对局
                while p1.is_alive() and p2.is_alive() and combat.turn < MAX_TURNS:
                    p1_actions = test_ai.choose_turn_actions()
                    p2_actions = default_ai.choose_turn_actions()
                    combat.execute_turn(p1_actions, p2_actions)
                
                # 统计结果
                winner = combat.get_winner()
                if winner == PLAYER1_NAME:
                    wins += 1
                elif winner == PLAYER2_NAME:
                    losses += 1
                else:
                    draws += 1
        
        finally:
            sys.stdout = old_stdout
        
        genome['matches_played'] = num_matches
        genome['wins'] = wins
        genome['losses'] = losses
        genome['draws'] = draws
        
        # 计算适应度
        win_rate = wins / num_matches
        draw_rate = draws / num_matches
        fitness = win_rate + 0.5 * draw_rate
        
        genome['fitness'] = fitness
        
        print(f"胜率: {win_rate*100:.1f}% | 适应度: {fitness:.3f}")
        
        return fitness
    
    def select_parents(self, tournament_size=3) -> Tuple[Dict, Dict]:
        """锦标赛选择父代"""
        def tournament():
            candidates = random.sample(self.population, min(tournament_size, len(self.population)))
            return max(candidates, key=lambda x: x['fitness'])
        
        return tournament(), tournament()
    
    def evolve_generation(self, num_matches=50, elite_ratio=0.2, mutation_rate=0.1):
        """进化一代"""
        self.generation += 1
        
        print(f"\n{'='*60}")
        print(f"进化第 {self.generation} 代 / Evolving Generation {self.generation}")
        print(f"{'='*60}")
        
        # 评估当前种群
        print("评估种群 / Evaluating population...")
        for genome in self.population:
            self.evaluate_genome(genome, num_matches)
        
        # 排序
        self.population.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 记录最佳个体
        best = self.population[0]
        self.best_genome = copy.deepcopy(best)
        
        print(f"\n最佳个体 / Best individual:")
        print(f"  ID: {best['id']}")
        print(f"  适应度: {best['fitness']:.3f}")
        print(f"  胜率: {best['wins']/best['matches_played']*100:.1f}%")
        
        # 精英保留
        elite_size = max(1, int(len(self.population) * elite_ratio))
        new_population = self.population[:elite_size]
        
        print(f"\n保留精英: {elite_size} 个 / Elite preserved: {elite_size}")
        
        # 生成新个体
        while len(new_population) < len(self.population):
            # 选择父代
            parent1, parent2 = self.select_parents()
            
            # 交叉
            child = self.crossover(parent1, parent2)
            
            # 变异
            if random.random() < mutation_rate:
                child = self.mutate(child, mutation_rate)
            
            new_population.append(child)
        
        self.population = new_population
        
        # 记录历史
        generation_stats = {
            'generation': self.generation,
            'best_fitness': best['fitness'],
            'avg_fitness': sum(g['fitness'] for g in self.population) / len(self.population),
            'best_id': best['id']
        }
        self.evolution_history.append(generation_stats)
        
        print(f"\n平均适应度: {generation_stats['avg_fitness']:.3f}")
        print(f"{'='*60}\n")
    
    def train(self, num_generations=10, population_size=10, matches_per_eval=50):
        """运行完整训练流程"""
        print(f"\n{'#'*60}")
        print("开始AI进化训练 / Starting AI Evolution Training")
        print(f"{'#'*60}")
        print(f"代数: {num_generations}")
        print(f"种群大小: {population_size}")
        print(f"每次评估对局数: {matches_per_eval}")
        print(f"{'#'*60}\n")
        
        # 初始化
        self.initialize_population(population_size)
        
        # 进化
        for gen in range(num_generations):
            self.evolve_generation(num_matches=matches_per_eval)
        
        # 总结
        self.print_summary()
        
        return self.best_genome
    
    def print_summary(self):
        """打印训练总结"""
        print(f"\n{'#'*60}")
        print("进化训练总结 / Evolution Training Summary")
        print(f"{'#'*60}")
        
        if not self.evolution_history:
            print("没有训练历史 / No training history")
            return
        
        print(f"总代数: {self.generation}")
        print(f"种群大小: {len(self.population)}")
        
        print(f"\n适应度进化 / Fitness Evolution:")
        for i, stats in enumerate(self.evolution_history, 1):
            print(f"  第{i}代: 最佳={stats['best_fitness']:.3f}, 平均={stats['avg_fitness']:.3f}")
        
        if self.best_genome:
            print(f"\n最终最佳个体 / Final Best Individual:")
            print(f"  ID: {self.best_genome['id']}")
            print(f"  适应度: {self.best_genome['fitness']:.3f}")
            print(f"  胜率: {self.best_genome['wins']/self.best_genome['matches_played']*100:.1f}%")
        
        print(f"{'#'*60}\n")
    
    def save_best_genome(self, filename='best_ai_config.json'):
        """保存最佳基因组"""
        if not self.best_genome:
            print("没有最佳基因组可保存 / No best genome to save")
            return
        
        data = {
            'best_genome': self.best_genome,
            'evolution_history': self.evolution_history,
            'final_generation': self.generation
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"最佳配置已保存到 {filename} / Best configuration saved to {filename}")


class ParameterOptimizer:
    """参数优化器 - 网格搜索和随机搜索"""
    
    def __init__(self):
        self.results = []
    
    def _merge_with_defaults(self, partial_params):
        """合并部分参数和默认参数"""
        evolver = AIEvolver()
        default_genome = evolver.create_genome()
        full_params = copy.deepcopy(default_genome['parameters'])
        full_params.update(partial_params)
        return full_params
    
    def grid_search(self, param_grid: Dict[str, List], num_matches=50):
        """网格搜索"""
        print(f"\n{'='*60}")
        print("开始网格搜索 / Starting Grid Search")
        print(f"{'='*60}\n")
        
        import itertools
        keys = list(param_grid.keys())
        values = [param_grid[k] for k in keys]
        combinations = list(itertools.product(*values))
        
        print(f"总组合数: {len(combinations)} / Total combinations: {len(combinations)}")
        
        for i, combo in enumerate(combinations, 1):
            params = dict(zip(keys, combo))
            print(f"\n测试 {i}/{len(combinations)}: {params}")
            
            # 创建临时基因组并真实评估
            temp_genome = {
                'id': f'grid_{i}',
                'parameters': self._merge_with_defaults(params),
                'fitness': 0.0
            }
            
            evolver = AIEvolver()
            fitness = evolver.evaluate_genome(temp_genome, num_matches)
            
            result = {
                'parameters': params,
                'fitness': fitness,
                'matches': num_matches
            }
            self.results.append(result)
        
        self.results.sort(key=lambda x: x['fitness'], reverse=True)
        
        print(f"\n{'='*60}")
        print("网格搜索完成 / Grid Search Complete")
        print(f"{'='*60}")
        print(f"最佳参数: {self.results[0]['parameters']}")
        print(f"最佳适应度: {self.results[0]['fitness']:.3f}")
        print(f"{'='*60}\n")
        
        return self.results[0]
    
    def _merge_with_defaults(self, partial_params):
        """合并部分参数和默认参数"""
        evolver = AIEvolver()
        default_genome = evolver.create_genome()
        full_params = copy.deepcopy(default_genome['parameters'])
        full_params.update(partial_params)
        return full_params
    
    def random_search(self, param_ranges: Dict[str, Tuple], num_trials=20, num_matches=50):
        """随机搜索"""
        print(f"\n{'='*60}")
        print("开始随机搜索 / Starting Random Search")
        print(f"{'='*60}\n")
        print(f"试验次数: {num_trials} / Number of trials: {num_trials}")
        
        for i in range(num_trials):
            # 随机采样参数
            params = {}
            for key, (min_val, max_val) in param_ranges.items():
                params[key] = random.uniform(min_val, max_val)
            
            print(f"\n试验 {i+1}/{num_trials}:")
            print(f"  参数: {params}")
            
            # 创建临时基因组并真实评估
            temp_genome = {
                'id': f'random_{i}',
                'parameters': self._merge_with_defaults(params),
                'fitness': 0.0
            }
            
            evolver = AIEvolver()
            fitness = evolver.evaluate_genome(temp_genome, num_matches)
            
            result = {
                'parameters': params,
                'fitness': fitness,
                'matches': num_matches
            }
            self.results.append(result)
        
        self.results.sort(key=lambda x: x['fitness'], reverse=True)
        
        print(f"\n{'='*60}")
        print("随机搜索完成 / Random Search Complete")
        print(f"{'='*60}")
        print(f"最佳参数: {self.results[0]['parameters']}")
        print(f"最佳适应度: {self.results[0]['fitness']:.3f}")
        print(f"{'='*60}\n")
        
        return self.results[0]


def main():
    """主函数 - 演示训练流程"""
    print("AI训练与优化系统 / AI Training and Optimization System")
    print("="*60)
    
    # 方式1: 进化算法
    print("\n【方式1】进化算法训练 / Evolutionary Algorithm Training")
    print("警告: 这将运行真实对局，需要较长时间")
    confirm = input("继续? (y/n): ").strip().lower()
    
    if confirm == 'y':
        evolver = AIEvolver()
        best_genome = evolver.train(
            num_generations=3,
            population_size=5,
            matches_per_eval=20
        )
        evolver.save_best_genome('best_ai_evolved_real.json')
        print("\n真实进化训练完成！")
    
    print("\n训练完成！ / Training Complete!")


if __name__ == "__main__":
    main()