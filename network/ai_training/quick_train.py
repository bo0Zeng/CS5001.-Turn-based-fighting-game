"""
quick_train.py
快速训练脚本 - 一键开始训练 / Quick Training Script - One-Click Start

使用方法：
python quick_train.py
"""

import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = current_dir
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

import torch
import numpy as np
import random
from datetime import datetime

from environment import BattleEnv
from agents import PPOAgent, RandomAgent
from training import SelfPlayTrainer, get_fast_config


def main():
    """快速训练主函数"""
    
    print("="*60)
    print("🚀 快速训练模式 / Quick Training Mode")
    print("="*60)
    
    # 设置随机种子
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  设备: {device}")
    print(f"🎲 随机种子: {seed}")
    
    # 加载快速配置
    config = get_fast_config()
    
    print(f"\n📋 训练配置:")
    print(f"  迭代次数: {config['training']['num_iterations']}")
    print(f"  每次迭代episodes: {config['training']['episodes_per_iteration']}")
    print(f"  批大小: {config['training']['batch_size']}")
    
    # 创建环境
    print(f"\n🎮 创建环境...")
    env = BattleEnv(
        reward_type=config['environment']['reward_type'],
        max_turns=config['environment']['max_turns'],
        verbose=False
    )
    
    # 创建智能体
    print(f"🤖 创建PPO智能体...")
    agent = PPOAgent(
        state_dim=54,
        action_dim=12,
        hidden_sizes=tuple(config['agent']['hidden_sizes']),
        learning_rate=config['agent']['learning_rate'],
        gamma=config['agent']['gamma'],
        device=device
    )
    
    # 创建对手（随机智能体）
    print(f"👾 创建对手（随机智能体）...")
    opponent = RandomAgent(action_dim=12)
    
    # 创建保存目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"saved_models/quick_train_{timestamp}"
    os.makedirs(save_dir, exist_ok=True)
    print(f"💾 保存目录: {save_dir}")
    
    # 创建训练器
    print(f"\n📚 创建训练器...")
    trainer = SelfPlayTrainer(
        env=env,
        agent=agent,
        opponent=opponent,
        save_dir=save_dir,
        log_interval=5,
        save_interval=20,
        eval_interval=10,
        eval_episodes=5
    )
    
    # 开始训练
    print("\n" + "="*60)
    print("🎓 开始训练！")
    print("="*60)
    
    try:
        history = trainer.train(
            num_iterations=config['training']['num_iterations'],
            episodes_per_iteration=config['training']['episodes_per_iteration'],
            update_epochs=config['training']['update_epochs'],
            batch_size=config['training']['batch_size']
        )
        
        # 保存训练历史
        import json
        history_path = os.path.join(save_dir, 'training_history.json')
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"\n📊 训练历史已保存: {history_path}")
        
        # 打印最终统计
        print("\n" + "="*60)
        print("📈 训练总结 / Training Summary")
        print("="*60)
        
        if history['agent_wins']:
            final_winrate = history['agent_wins'][-1]
            final_reward = history['avg_reward'][-1]
            
            print(f"最终胜率: {final_winrate:.1f}%")
            print(f"最终平均奖励: {final_reward:.2f}")
            
            # 计算改进
            if len(history['agent_wins']) > 10:
                initial_winrate = np.mean(history['agent_wins'][:10])
                improvement = final_winrate - initial_winrate
                print(f"胜率提升: {improvement:+.1f}%")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  训练被中断！")
        print("💾 保存当前模型...")
        agent.save(os.path.join(save_dir, "interrupted_model.pth"))
        print("✅ 模型已保存")
    
    print("\n🎉 训练完成！")
    print(f"💾 模型保存在: {save_dir}")


if __name__ == "__main__":
    main()