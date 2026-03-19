"""
quick_start.py
快速启动脚本 - 一键运行AI训练
Quick Start Script - One-click AI training
"""

import sys
from self_play import SelfPlayTrainer
from ai_trainer import AIEvolver, ParameterOptimizer


def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("AI训练系统 / AI Training System")
    print("="*60)
    print("1. 快速测试 - 运行10场对局 / Quick Test - Run 10 matches")
    print("2. 标准训练 - 100场对局 / Standard Training - 100 matches")
    print("3. 深度训练 - 500场对局 / Deep Training - 500 matches")
    print("4. 进化训练 - 遗传算法优化 / Evolution Training - Genetic algorithm")
    print("5. 参数优化 - 网格搜索 / Parameter Optimization - Grid search")
    print("6. 查看训练数据 / View Training Data")
    print("7. 分析对局模式 / Analyze Match Patterns")
    print("0. 退出 / Exit")
    print("="*60)


def quick_test():
    """快速测试"""
    print("\n【快速测试模式】Running 10 matches...")
    trainer = SelfPlayTrainer()
    trainer.run_generation(num_matches=10, verbose_interval=2)
    trainer.analyze_patterns(last_n_matches=10)
    trainer.save_training_data('quick_test.json')


def standard_training():
    """标准训练"""
    print("\n【标准训练模式】Running 100 matches...")
    trainer = SelfPlayTrainer()
    trainer.run_generation(num_matches=100, verbose_interval=10)
    trainer.analyze_patterns(last_n_matches=100)
    trainer.save_training_data('standard_training.json')


def deep_training():
    """深度训练"""
    print("\n【深度训练模式】Running 500 matches...")
    trainer = SelfPlayTrainer()
    
    # 分5代运行，每代100场
    for i in range(5):
        print(f"\n>>> 第 {i+1}/5 轮 <<<")
        trainer.run_generation(num_matches=100, verbose_interval=20)
        
        if (i + 1) % 2 == 0:
            trainer.save_training_data(f'deep_training_round_{i+1}.json')
    
    trainer.analyze_patterns(last_n_matches=500)
    trainer.get_summary()
    trainer.save_training_data('deep_training_final.json')


def evolution_training():
    """进化训练"""
    print("\n【进化训练模式】Genetic Algorithm Optimization...")
    
    print("\n请选择配置:")
    print("1. 快速 - 3代, 种群5, 20场评估 / Quick - 3 gen, pop 5, 20 matches")
    print("2. 标准 - 5代, 种群8, 30场评估 / Standard - 5 gen, pop 8, 30 matches")
    print("3. 深度 - 10代, 种群12, 50场评估 / Deep - 10 gen, pop 12, 50 matches")
    
    choice = input("选择 (1-3): ").strip()
    
    configs = {
        '1': (3, 5, 20),
        '2': (5, 8, 30),
        '3': (10, 12, 50)
    }
    
    if choice not in configs:
        print("无效选择 / Invalid choice")
        return
    
    generations, population, matches = configs[choice]
    
    evolver = AIEvolver()
    best = evolver.train(
        num_generations=generations,
        population_size=population,
        matches_per_eval=matches
    )
    evolver.save_best_genome(f'best_ai_evolved_{generations}gen.json')
    
    print(f"\n最佳AI配置已保存 / Best AI config saved")


def parameter_optimization():
    """参数优化"""
    print("\n【参数优化模式】Parameter Optimization...")
    
    print("\n请选择方法:")
    print("1. 网格搜索 - 系统化测试所有组合 / Grid Search - Test all combinations")
    print("2. 随机搜索 - 随机采样参数空间 / Random Search - Random sampling")
    
    choice = input("选择 (1-2): ").strip()
    
    optimizer = ParameterOptimizer()
    
    if choice == '1':
        # 网格搜索
        param_grid = {
            'attack_prediction_base': [0.30, 0.35, 0.40],
            'defend_prediction_base': [0.15, 0.20, 0.25],
            'charge2_release_prob': [0.6, 0.7, 0.8]
        }
        print(f"\n网格大小: {3 * 3 * 3 == 27} 组合")
        confirm = input("继续? (y/n): ").strip().lower()
        
        if confirm == 'y':
            best = optimizer.grid_search(param_grid, num_matches=30)
            print(f"\n最佳参数: {best['parameters']}")
    
    elif choice == '2':
        # 随机搜索
        param_ranges = {
            'attack_prediction_base': (0.25, 0.45),
            'defend_prediction_base': (0.10, 0.30),
            'charge2_release_prob': (0.5, 0.9),
            'burst_kill_threshold_0': (0.7, 0.95)
        }
        
        trials = int(input("试验次数 (10-50): ").strip() or "20")
        best = optimizer.random_search(param_ranges, num_trials=trials, num_matches=30)
        print(f"\n最佳参数: {best['parameters']}")
    
    else:
        print("无效选择 / Invalid choice")


def view_training_data():
    """查看训练数据"""
    import os
    import json
    
    print("\n【训练数据】Training Data")
    print("="*60)
    
    # 查找所有训练数据文件
    files = [f for f in os.listdir('.') if f.endswith('.json') and 'training' in f]
    
    if not files:
        print("没有找到训练数据文件 / No training data files found")
        return
    
    print(f"找到 {len(files)} 个数据文件:\n")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    
    choice = input("\n选择文件编号查看详情 (0取消): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            with open(files[idx], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n文件: {files[idx]}")
            print("-"*60)
            
            if 'stats' in data:
                stats = data['stats']
                print(f"总对局数: {stats.get('total_matches', 0)}")
                print(f"平均回合数: {stats.get('avg_turns_per_match', 0):.2f}")
                print(f"Red胜利: {stats.get('p1_wins', 0)}")
                print(f"Blue胜利: {stats.get('p2_wins', 0)}")
                print(f"平局: {stats.get('draws', 0)}")
            
            if 'best_genome' in data:
                genome = data['best_genome']
                print(f"\n最佳AI ID: {genome.get('id', 'N/A')}")
                print(f"适应度: {genome.get('fitness', 0):.3f}")
                print(f"胜率: {genome.get('wins', 0) / max(1, genome.get('matches_played', 1)) * 100:.1f}%")
    
    except (ValueError, IndexError):
        print("无效选择 / Invalid choice")
    except Exception as e:
        print(f"错误: {e} / Error: {e}")


def analyze_patterns():
    """分析对局模式"""
    print("\n【对局模式分析】Match Pattern Analysis")
    print("="*60)
    
    trainer = SelfPlayTrainer()
    
    # 尝试加载最近的训练数据
    import os
    files = sorted([f for f in os.listdir('.') if 'training' in f and f.endswith('.json')])
    
    if files:
        latest = files[-1]
        print(f"加载最新数据: {latest}")
        trainer.load_training_data(latest)
        
        if trainer.match_history:
            n = min(100, len(trainer.match_history))
            print(f"\n分析最近 {n} 场对局...")
            trainer.analyze_patterns(last_n_matches=n)
        else:
            print("没有对局历史数据 / No match history")
    else:
        print("没有找到训练数据 / No training data found")
        print("请先运行训练 / Please run training first")


def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("\n请选择 (0-7): ").strip()
        
        if choice == '0':
            print("\n再见! / Goodbye!")
            break
        elif choice == '1':
            quick_test()
        elif choice == '2':
            standard_training()
        elif choice == '3':
            deep_training()
        elif choice == '4':
            evolution_training()
        elif choice == '5':
            parameter_optimization()
        elif choice == '6':
            view_training_data()
        elif choice == '7':
            analyze_patterns()
        else:
            print("无效选择，请重试 / Invalid choice, please try again")
        
        input("\n按回车继续... / Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n训练中断 / Training interrupted")
        sys.exit(0)