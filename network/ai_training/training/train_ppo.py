"""
train_ppo.py
PPO训练主脚本 / PPO Training Main Script

使用方法：
python train_ppo.py [--config configs/ppo_config.yaml]
"""

import sys
import os
import argparse
from datetime import datetime

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from environment import BattleEnv
from agents import PPOAgent, RandomAgent, RuleBasedAgent
from training.selfplay_trainer import SelfPlayTrainer
from training.hyperparameters import get_default_config, load_config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="PPO智能体训练")
    
    parser.add_argument('--config', type=str, default=None,
                       help='配置文件路径')
    parser.add_argument('--opponent', type=str, default='self',
                       choices=['self', 'random', 'rule'],
                       help='对手类型: self(自我对弈), random(随机), rule(规则)')
    parser.add_argument('--iterations', type=int, default=None,
                       help='训练迭代次数')
    parser.add_argument('--episodes', type=int, default=None,
                       help='每次迭代的episode数')
    parser.add_argument('--save_dir', type=str, default='saved_models/ppo',
                       help='模型保存目录')
    parser.add_argument('--resume', type=str, default=None,
                       help='从检查点恢复训练')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    parser.add_argument('--device', type=str, default='auto',
                       choices=['auto', 'cpu', 'cuda'],
                       help='计算设备')
    
    return parser.parse_args()


def setup_environment(config: dict):
    """
    设置环境
    
    Args:
        config: 配置字典
    
    Returns:
        BattleEnv实例
    """
    env_config = config.get('environment', {})
    
    env = BattleEnv(
        reward_type=env_config.get('reward_type', 'dense'),
        max_turns=env_config.get('max_turns', 30),
        verbose=env_config.get('verbose', False)
    )
    
    return env


def setup_agent(config: dict, device):
    """
    设置智能体
    
    Args:
        config: 配置字典
        device: 计算设备
    
    Returns:
        PPOAgent实例
    """
    agent_config = config.get('agent', {})
    
    agent = PPOAgent(
        state_dim=66,  # 更新为66维
        action_dim=12,
        hidden_sizes=tuple(agent_config.get('hidden_sizes', [256, 128])),
        learning_rate=agent_config.get('learning_rate', 3e-4),
        gamma=agent_config.get('gamma', 0.99),
        gae_lambda=agent_config.get('gae_lambda', 0.95),
        clip_epsilon=agent_config.get('clip_epsilon', 0.2),
        value_coef=agent_config.get('value_coef', 0.5),
        entropy_coef=agent_config.get('entropy_coef', 0.01),
        max_grad_norm=agent_config.get('max_grad_norm', 0.5),
        device=device
    )
    
    return agent


def setup_opponent(opponent_type: str, config: dict):
    """
    设置对手
    
    Args:
        opponent_type: 对手类型
        config: 配置字典
    
    Returns:
        对手智能体
    """
    if opponent_type == 'random':
        return RandomAgent(action_dim=12)
    elif opponent_type == 'rule':
        return RuleBasedAgent(action_dim=12, aggression=0.7)
    else:  # self
        return None  # 自我对弈时返回None


def main():
    """主训练流程"""
    # 解析参数
    args = parse_args()
    
    # 加载配置
    if args.config:
        config = load_config(args.config)
        print(f"✅ 从 {args.config} 加载配置")
    else:
        config = get_default_config()
        print("✅ 使用默认配置")
    
    # 命令行参数覆盖配置
    if args.iterations:
        config['training']['num_iterations'] = args.iterations
    if args.episodes:
        config['training']['episodes_per_iteration'] = args.episodes
    
    # 设置设备
    if args.device == 'auto':
        import torch
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        import torch
        device = torch.device(args.device)
    
    print(f"🖥️  使用设备: {device}")
    
    # 设置随机种子
    import numpy as np
    import torch
    import random
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(args.seed)
    
    print(f"🎲 随机种子: {args.seed}")
    
    # 创建保存目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(args.save_dir, f"run_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"💾 保存目录: {save_dir}")
    
    # 设置环境
    env = setup_environment(config)
    print(f"🎮 环境: {env.__class__.__name__}")
    
    # 设置智能体
    agent = setup_agent(config, device)
    print(f"🤖 智能体: {agent.get_name()}")
    
    # 从检查点恢复
    if args.resume:
        agent.load(args.resume)
        print(f"📂 从 {args.resume} 恢复训练")
    
    # 设置对手
    opponent = setup_opponent(args.opponent, config)
    if opponent:
        print(f"👾 对手: {opponent.get_name()}")
    else:
        print(f"👾 对手: 自我对弈 (Self-Play)")
    
    # 创建训练器
    training_config = config.get('training', {})
    
    trainer = SelfPlayTrainer(
        env=env,
        agent=agent,
        opponent=opponent,
        save_dir=save_dir,
        log_interval=training_config.get('log_interval', 10),
        save_interval=training_config.get('save_interval', 50),
        eval_interval=training_config.get('eval_interval', 20),
        eval_episodes=training_config.get('eval_episodes', 10)
    )
    
    # 开始训练
    print("\n" + "="*60)
    print("🚀 开始训练！")
    print("="*60)
    
    try:
        history = trainer.train(
            num_iterations=training_config.get('num_iterations', 1000),
            episodes_per_iteration=training_config.get('episodes_per_iteration', 100),
            update_epochs=training_config.get('update_epochs', 4),
            batch_size=training_config.get('batch_size', 64)
        )
        
        # 保存训练历史
        import json
        history_path = os.path.join(save_dir, 'training_history.json')
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"\n📊 训练历史已保存: {history_path}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  训练被中断！")
        print("💾 保存当前模型...")
        agent.save(os.path.join(save_dir, "interrupted_model.pth"))
        print("✅ 模型已保存")
    
    print("\n" + "="*60)
    print("🎉 训练流程结束")
    print("="*60)


if __name__ == "__main__":
    main()