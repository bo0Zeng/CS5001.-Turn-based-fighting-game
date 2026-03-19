"""
visualize.py
可视化工具 - 绘制训练曲线和性能图表 / Visualization - Plot Training Curves

提供：
- 训练曲线绘制
- 性能对比图
- 保存图表
"""

import sys
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)


class TrainingVisualizer:
    """训练可视化器"""
    
    def __init__(self, style: str = 'default'):
        """
        初始化可视化器
        
        Args:
            style: matplotlib样式
        """
        plt.style.use(style)
        self.fig_size = (12, 8)
    
    def plot_training_history(self,
                             history: Dict[str, List],
                             save_path: Optional[str] = None):
        """
        绘制完整的训练历史
        
        Args:
            history: 训练历史字典
            save_path: 保存路径（可选）
        """
        fig, axes = plt.subplots(2, 2, figsize=self.fig_size)
        fig.suptitle('训练历史 / Training History', fontsize=16, fontweight='bold')
        
        iterations = history.get('iteration', [])
        
        # 子图1: 胜率
        ax1 = axes[0, 0]
        if 'agent_wins' in history:
            ax1.plot(iterations, history['agent_wins'], 'b-', label='胜率 / Win Rate', linewidth=2)
            ax1.fill_between(iterations, 0, history['agent_wins'], alpha=0.3)
        ax1.set_xlabel('迭代 / Iteration')
        ax1.set_ylabel('胜率 % / Win Rate %')
        ax1.set_title('胜率变化 / Win Rate Progress')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 子图2: 平均奖励
        ax2 = axes[0, 1]
        if 'avg_reward' in history:
            rewards = history['avg_reward']
            ax2.plot(iterations, rewards, 'g-', label='平均奖励 / Avg Reward', linewidth=2)
            
            # 添加移动平均
            if len(rewards) > 10:
                window = min(10, len(rewards) // 10)
                moving_avg = np.convolve(rewards, np.ones(window)/window, mode='valid')
                ax2.plot(iterations[window-1:], moving_avg, 'r--', 
                        label=f'{window}点移动平均 / MA', linewidth=1.5)
        
        ax2.set_xlabel('迭代 / Iteration')
        ax2.set_ylabel('平均奖励 / Average Reward')
        ax2.set_title('奖励变化 / Reward Progress')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 子图3: 损失
        ax3 = axes[1, 0]
        if 'policy_loss' in history and history['policy_loss']:
            ax3.plot(iterations, history['policy_loss'], 'r-', 
                    label='策略损失 / Policy Loss', linewidth=1.5)
        if 'value_loss' in history and history['value_loss']:
            ax3.plot(iterations, history['value_loss'], 'b-', 
                    label='价值损失 / Value Loss', linewidth=1.5)
        
        ax3.set_xlabel('迭代 / Iteration')
        ax3.set_ylabel('损失 / Loss')
        ax3.set_title('训练损失 / Training Loss')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # 子图4: 熵和Episode长度
        ax4 = axes[1, 1]
        if 'entropy' in history and history['entropy']:
            ax4_twin = ax4.twinx()
            ax4.plot(iterations, history['entropy'], 'purple', 
                    label='策略熵 / Entropy', linewidth=1.5)
            ax4.set_ylabel('熵 / Entropy', color='purple')
            ax4.tick_params(axis='y', labelcolor='purple')
            
            if 'avg_episode_length' in history:
                ax4_twin.plot(iterations, history['avg_episode_length'], 'orange',
                            label='Episode长度 / Length', linewidth=1.5)
                ax4_twin.set_ylabel('长度 / Length', color='orange')
                ax4_twin.tick_params(axis='y', labelcolor='orange')
        
        ax4.set_xlabel('迭代 / Iteration')
        ax4.set_title('熵与Episode长度 / Entropy & Episode Length')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 图表已保存: {save_path}")
        
        plt.show()
    
    def plot_win_rate_only(self,
                           history: Dict[str, List],
                           save_path: Optional[str] = None):
        """
        只绘制胜率曲线
        
        Args:
            history: 训练历史
            save_path: 保存路径
        """
        plt.figure(figsize=(10, 6))
        
        iterations = history.get('iteration', [])
        win_rates = history.get('agent_wins', [])
        
        plt.plot(iterations, win_rates, 'b-', linewidth=2, label='胜率 / Win Rate')
        plt.fill_between(iterations, 0, win_rates, alpha=0.3)
        
        # 添加移动平均
        if len(win_rates) > 10:
            window = min(20, len(win_rates) // 10)
            moving_avg = np.convolve(win_rates, np.ones(window)/window, mode='valid')
            plt.plot(iterations[window-1:], moving_avg, 'r--', 
                    linewidth=2, label=f'{window}点移动平均 / MA')
        
        # 添加基准线
        plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='50%基准线')
        plt.axhline(y=70, color='green', linestyle='--', alpha=0.5, label='70%目标线')
        
        plt.xlabel('迭代次数 / Iteration', fontsize=12)
        plt.ylabel('胜率 % / Win Rate %', fontsize=12)
        plt.title('训练胜率变化 / Training Win Rate Progress', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 胜率图已保存: {save_path}")
        
        plt.show()
    
    def plot_comparison(self,
                       results_dict: Dict[str, Dict],
                       metric: str = 'win_rate',
                       save_path: Optional[str] = None):
        """
        绘制多个智能体的对比图
        
        Args:
            results_dict: 结果字典 {agent_name: results}
            metric: 对比指标
            save_path: 保存路径
        """
        names = list(results_dict.keys())
        values = [results_dict[name][metric] for name in names]
        
        plt.figure(figsize=(10, 6))
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(names)))
        bars = plt.bar(names, values, color=colors, edgecolor='black', linewidth=1.5)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.1f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.ylabel(metric.replace('_', ' ').title(), fontsize=12)
        plt.title(f'{metric.replace("_", " ").title()} 对比 / Comparison', 
                 fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 对比图已保存: {save_path}")
        
        plt.tight_layout()
        plt.show()


def load_and_plot(history_path: str, output_dir: Optional[str] = None):
    """
    从JSON加载训练历史并绘图
    
    Args:
        history_path: 训练历史JSON文件路径
        output_dir: 图表输出目录（可选）
    """
    # 加载历史
    with open(history_path, 'r') as f:
        history = json.load(f)
    
    print(f"✅ 已加载训练历史: {history_path}")
    print(f"  总迭代次数: {len(history.get('iteration', []))}")
    
    # 创建可视化器
    visualizer = TrainingVisualizer()
    
    # 绘制完整历史
    save_path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, 'training_history.png')
    
    visualizer.plot_training_history(history, save_path)
    
    # 绘制胜率
    if output_dir:
        save_path = os.path.join(output_dir, 'win_rate.png')
    
    visualizer.plot_win_rate_only(history, save_path)


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 TrainingVisualizer...")
    
    # 创建模拟训练历史
    print("\n生成模拟训练数据...")
    
    num_iterations = 100
    history = {
        'iteration': list(range(1, num_iterations + 1)),
        'agent_wins': [],
        'avg_reward': [],
        'policy_loss': [],
        'value_loss': [],
        'entropy': [],
        'avg_episode_length': [],
    }
    
    # 模拟训练进度（胜率逐渐提升）
    for i in range(num_iterations):
        # 胜率从40%逐渐提升到70%
        base_win_rate = 40 + (i / num_iterations) * 30
        noise = np.random.randn() * 5
        history['agent_wins'].append(max(0, min(100, base_win_rate + noise)))
        
        # 奖励逐渐增加
        base_reward = -10 + (i / num_iterations) * 30
        history['avg_reward'].append(base_reward + np.random.randn() * 5)
        
        # 损失逐渐下降
        history['policy_loss'].append(max(0.01, 1.0 - i / num_iterations * 0.8 + np.random.rand() * 0.1))
        history['value_loss'].append(max(0.05, 2.0 - i / num_iterations * 1.5 + np.random.rand() * 0.2))
        
        # 熵逐渐降低
        history['entropy'].append(max(0.5, 2.4 - i / num_iterations * 1.0 + np.random.rand() * 0.1))
        
        # Episode长度
        history['avg_episode_length'].append(8 + np.random.randn() * 2)
    
    # 创建可视化器
    visualizer = TrainingVisualizer()
    
    # 测试1: 绘制完整历史
    print("\n测试1: 绘制完整训练历史")
    visualizer.plot_training_history(history)
    
    # 测试2: 只绘制胜率
    print("\n测试2: 绘制胜率曲线")
    visualizer.plot_win_rate_only(history)
    
    # 测试3: 对比图
    print("\n测试3: 绘制性能对比")
    
    comparison_results = {
        'Random': {'win_rate': 45.0, 'avg_reward': 5.0},
        'Rule': {'win_rate': 62.0, 'avg_reward': 15.0},
        'Trained PPO': {'win_rate': 75.0, 'avg_reward': 25.0},
    }
    
    visualizer.plot_comparison(comparison_results, metric='win_rate')
    
    print("\n✅ TrainingVisualizer 测试完成！")
    print("提示: 关闭图表窗口以继续...")