"""
train_and_evaluate.py
完整训练+评估流程 / Complete Training + Evaluation Pipeline

一个完整的脚本，包含：
1. 训练PPO智能体
2. 评估性能
3. 生成可视化图表
4. 保存结果报告
"""

import sys
import os
import json
from datetime import datetime

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = current_dir
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

import torch
import numpy as np
import random

from environment import BattleEnv
from agents import PPOAgent, RandomAgent, RuleBasedAgent
from training import SelfPlayTrainer, get_fast_config
from evaluation import Evaluator, TrainingVisualizer


def run_complete_pipeline(config_type: str = 'fast'):
    """
    运行完整的训练评估流程
    
    Args:
        config_type: 配置类型 ('fast', 'default', 'large')
    """
    print("="*80)
    print("🚀 完整训练+评估流程 / Complete Training + Evaluation Pipeline")
    print("="*80)
    
    # === 1. 初始化 ===
    print("\n📋 步骤1: 初始化系统")
    
    # 设置随机种子
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  设备: {device}")
    print(f"  随机种子: {seed}")
    
    # 加载配置
    if config_type == 'fast':
        from training import get_fast_config
        config = get_fast_config()
    else:
        from training import get_default_config
        config = get_default_config()
    
    print(f"  配置类型: {config_type}")
    print(f"  训练迭代: {config['training']['num_iterations']}")
    
    # === 2. 创建环境和智能体 ===
    print("\n📋 步骤2: 创建环境和智能体")
    
    env = BattleEnv(
        reward_type=config['environment']['reward_type'],
        max_turns=config['environment']['max_turns'],
        verbose=False
    )
    print(f"  ✅ 环境创建完成")
    
    agent = PPOAgent(
        state_dim=66,
        action_dim=12,
        hidden_sizes=tuple(config['agent']['hidden_sizes']),
        learning_rate=config['agent']['learning_rate'],
        gamma=config['agent']['gamma'],
        device=device
    )
    print(f"  ✅ PPO智能体创建完成")
    
    opponent = RandomAgent(action_dim=12)
    print(f"  ✅ 对手创建完成 (随机智能体)")
    
    # === 3. 训练前基线评估 ===
    print("\n📋 步骤3: 训练前基线评估")
    
    evaluator = Evaluator(env, verbose=True)
    
    print("\n评估未训练的PPO...")
    baseline_results = evaluator.benchmark_against_baselines(
        agent=agent,
        agent_name="Untrained PPO",
        num_episodes=20
    )
    
    # === 4. 开始训练 ===
    print("\n📋 步骤4: 开始训练")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"saved_models/complete_run_{timestamp}"
    
    trainer = SelfPlayTrainer(
        env=env,
        agent=agent,
        opponent=opponent,
        save_dir=save_dir,
        log_interval=5,
        save_interval=20,
        eval_interval=10,
        eval_episodes=10
    )
    
    history = trainer.train(
        num_iterations=config['training']['num_iterations'],
        episodes_per_iteration=config['training']['episodes_per_iteration'],
        update_epochs=config['training']['update_epochs'],
        batch_size=config['training']['batch_size']
    )
    
    # === 5. 训练后评估 ===
    print("\n📋 步骤5: 训练后评估")
    
    print("\n评估训练后的PPO...")
    trained_results = evaluator.benchmark_against_baselines(
        agent=agent,
        agent_name="Trained PPO",
        num_episodes=50
    )
    
    # === 6. 生成报告 ===
    print("\n📋 步骤6: 生成报告和可视化")
    
    # 保存训练历史
    history_path = os.path.join(save_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"  ✅ 训练历史已保存: {history_path}")
    
    # 生成可视化
    visualizer = TrainingVisualizer()
    
    # 绘制训练历史
    plot_path = os.path.join(save_dir, 'training_curves.png')
    visualizer.plot_training_history(history, save_path=plot_path)
    print(f"  ✅ 训练曲线已保存: {plot_path}")
    
    # 绘制性能对比
    comparison_data = {
        'vs Random (Before)': baseline_results['vs_random'],
        'vs Random (After)': trained_results['vs_random'],
        'vs Rule (Before)': baseline_results['vs_rule'],
        'vs Rule (After)': trained_results['vs_rule'],
    }
    
    comparison_path = os.path.join(save_dir, 'performance_comparison.png')
    visualizer.plot_comparison(comparison_data, metric='win_rate', save_path=comparison_path)
    print(f"  ✅ 性能对比图已保存: {comparison_path}")
    
    # 生成文本报告
    report_path = os.path.join(save_dir, 'evaluation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("训练评估报告 / Training Evaluation Report\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"训练时间: {timestamp}\n")
        f.write(f"配置类型: {config_type}\n")
        f.write(f"总迭代次数: {len(history['iteration'])}\n\n")
        
        f.write("训练前性能:\n")
        f.write(f"  vs Random: {baseline_results['vs_random']['win_rate']:.1f}%\n")
        f.write(f"  vs Rule: {baseline_results['vs_rule']['win_rate']:.1f}%\n\n")
        
        f.write("训练后性能:\n")
        f.write(f"  vs Random: {trained_results['vs_random']['win_rate']:.1f}%\n")
        f.write(f"  vs Rule: {trained_results['vs_rule']['win_rate']:.1f}%\n\n")
        
        f.write("性能提升:\n")
        improvement_random = trained_results['vs_random']['win_rate'] - baseline_results['vs_random']['win_rate']
        improvement_rule = trained_results['vs_rule']['win_rate'] - baseline_results['vs_rule']['win_rate']
        f.write(f"  vs Random: {improvement_random:+.1f}%\n")
        f.write(f"  vs Rule: {improvement_rule:+.1f}%\n\n")
        
        if history['agent_wins']:
            f.write(f"最终训练胜率: {history['agent_wins'][-1]:.1f}%\n")
            f.write(f"最终平均奖励: {history['avg_reward'][-1]:.2f}\n")
    
    print(f"  ✅ 评估报告已保存: {report_path}")
    
    # === 7. 总结 ===
    print("\n" + "="*80)
    print("🎉 完整流程执行完毕！")
    print("="*80)
    
    print(f"\n📊 训练成果:")
    print(f"  vs Random: {baseline_results['vs_random']['win_rate']:.1f}% → {trained_results['vs_random']['win_rate']:.1f}% ({improvement_random:+.1f}%)")
    print(f"  vs Rule:   {baseline_results['vs_rule']['win_rate']:.1f}% → {trained_results['vs_rule']['win_rate']:.1f}% ({improvement_rule:+.1f}%)")
    
    print(f"\n💾 所有文件已保存到: {save_dir}")
    print(f"  - final_model.pth           (最终模型)")
    print(f"  - training_history.json     (训练历史)")
    print(f"  - training_curves.png       (训练曲线)")
    print(f"  - performance_comparison.png (性能对比)")
    print(f"  - evaluation_report.txt     (评估报告)")
    
    print("\n🎮 下一步:")
    print(f"  - 人机对战: python evaluation/play_vs_ai.py --model {save_dir}/final_model.pth")
    print(f"  - 查看报告: cat {save_dir}/evaluation_report.txt")
    
    return save_dir


if __name__ == "__main__":
    # 运行完整流程
    save_dir = run_complete_pipeline(config_type='fast')
    
    print("\n✅ 完整流程测试完成！")