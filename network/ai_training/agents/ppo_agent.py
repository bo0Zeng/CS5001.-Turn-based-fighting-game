"""
ppo_agent.py
PPO智能体 - Proximal Policy Optimization / PPO Agent

实现了完整的PPO算法：
- Clipped surrogate objective
- GAE (Generalized Advantage Estimation)
- Value function clipping
- Entropy bonus
"""

import sys
import os
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

from agents.base_agent import RLAgent
from models import ActorCritic, save_model, load_model, clip_gradient


class PPOAgent(RLAgent):
    """
    PPO智能体
    
    使用Actor-Critic架构和PPO算法训练
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 hidden_sizes: Tuple[int, ...] = (256, 128),
                 learning_rate: float = 3e-4,
                 gamma: float = 0.99,
                 gae_lambda: float = 0.95,
                 clip_epsilon: float = 0.2,
                 value_coef: float = 0.5,
                 entropy_coef: float = 0.01,
                 max_grad_norm: float = 0.5,
                 device: Optional[torch.device] = None):
        """
        初始化PPO智能体
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_sizes: 隐藏层大小
            learning_rate: 学习率
            gamma: 折扣因子
            gae_lambda: GAE参数
            clip_epsilon: PPO裁剪参数
            value_coef: 价值损失系数
            entropy_coef: 熵损失系数
            max_grad_norm: 最大梯度范数
            device: 计算设备
        """
        super().__init__(
            state_dim=state_dim,
            action_dim=action_dim,
            agent_name="PPOAgent",
            device=device,
            learning_rate=learning_rate,
            gamma=gamma
        )
        
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        
        # 创建Actor-Critic网络
        self.model = ActorCritic(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_sizes=hidden_sizes
        ).to(self.device)
        
        # 优化器
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate
        )
        
        # 训练模式
        self.training = True
    
    def select_action(self,
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        选择动作
        
        Args:
            observation: 观察
            valid_actions: 有效动作掩码 (action_dim,) 布尔数组
            deterministic: 是否确定性选择
        
        Returns:
            (action1, action2): 两个动作
        """
        # 预处理
        state = self._preprocess_observation(observation)
        action_mask = self._preprocess_action_mask(valid_actions)
        
        with torch.no_grad():
            self.model.eval()
            
            # 选择第一个动作
            actions1, _, _ = self.model.get_action_and_value(
                state, action_mask, deterministic
            )
            
            # 选择第二个动作
            actions2, _, _ = self.model.get_action_and_value(
                state, action_mask, deterministic
            )
            
            if self.training:
                self.model.train()
        
        return actions1.item(), actions2.item()
    
    def update(self,
              states: np.ndarray,
              actions: np.ndarray,
              rewards: np.ndarray,
              next_states: np.ndarray,
              dones: np.ndarray,
              action_masks: Optional[np.ndarray] = None,
              epochs: int = 4,
              batch_size: int = 64) -> Dict[str, float]:
        """
        PPO更新
        
        Args:
            states: 状态 (N, state_dim)
            actions: 动作 (N, 2) - 每个样本2个动作
            rewards: 奖励 (N,)
            next_states: 下一状态 (N, state_dim)
            dones: 是否结束 (N,)
            action_masks: 动作掩码 (N, action_dim)
            epochs: 训练轮数
            batch_size: 批大小
        
        Returns:
            训练指标字典
        """
        # 转换为张量
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)  # (N, 2)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)
        
        # 处理动作掩码
        if action_masks is not None:
            action_masks_t = torch.BoolTensor(action_masks).to(self.device)
        else:
            # 如果没有提供掩码，创建全True的掩码（所有动作都有效）
            action_masks_t = torch.ones(len(states), self.action_dim, dtype=torch.bool).to(self.device)
        
        # 计算优势和回报
        with torch.no_grad():
            # 获取旧的价值和对数概率
            old_values = []
            old_log_probs = []
            
            for i in range(2):  # 两个动作
                action_i = actions_t[:, i]
                log_prob_i, value_i, _ = self.model.evaluate_actions(
                    states_t, action_i, action_masks_t
                )
                old_log_probs.append(log_prob_i)
                old_values.append(value_i)
            
            # 平均价值
            old_values = torch.stack(old_values, dim=1).mean(dim=1)  # (N,)
            
            # 计算优势（使用GAE）
            advantages = self._compute_gae(
                rewards_t, old_values, dones_t
            )
            
            # 回报 = 优势 + 价值
            returns = advantages + old_values
            
            # 归一化优势
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 训练多个epoch
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_loss = 0.0
        update_count = 0
        
        for epoch in range(epochs):
            # 创建数据加载器
            dataset = PPODataset(
                states_t, actions_t, 
                torch.stack(old_log_probs, dim=1),  # (N, 2)
                advantages, returns,
                action_masks_t,
                action_dim=self.action_dim
            )
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            for batch in dataloader:
                batch_states, batch_actions, batch_old_log_probs, \
                batch_advantages, batch_returns, batch_masks = batch
                
                # 计算两个动作的损失
                policy_losses = []
                value_losses = []
                entropies = []
                
                for i in range(2):
                    action_i = batch_actions[:, i]
                    old_log_prob_i = batch_old_log_probs[:, i]
                    
                    # 评估动作
                    log_prob_i, value_i, entropy_i = self.model.evaluate_actions(
                        batch_states, action_i, batch_masks
                    )
                    
                    # 策略损失（PPO-Clip）
                    ratio = torch.exp(log_prob_i - old_log_prob_i)
                    surr1 = ratio * batch_advantages
                    surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                    policy_loss = -torch.min(surr1, surr2).mean()
                    
                    # 价值损失
                    value_loss = F.mse_loss(value_i, batch_returns)
                    
                    policy_losses.append(policy_loss)
                    value_losses.append(value_loss)
                    entropies.append(entropy_i.mean())
                
                # 平均损失
                policy_loss = torch.stack(policy_losses).mean()
                value_loss = torch.stack(value_losses).mean()
                entropy = torch.stack(entropies).mean()
                
                # 总损失
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy
                
                # 反向传播
                self.optimizer.zero_grad()
                loss.backward()
                grad_norm = clip_gradient(self.model, self.max_grad_norm)
                self.optimizer.step()
                
                # 累计统计
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy_loss += entropy.item()
                total_loss += loss.item()
                update_count += 1
        
        self.total_updates += 1
        
        # 返回平均指标
        metrics = {
            'policy_loss': total_policy_loss / update_count,
            'value_loss': total_value_loss / update_count,
            'entropy': total_entropy_loss / update_count,
            'total_loss': total_loss / update_count,
            'update_count': update_count,
        }
        
        return metrics
    
    def _compute_gae(self,
                    rewards: torch.Tensor,
                    values: torch.Tensor,
                    dones: torch.Tensor) -> torch.Tensor:
        """
        计算广义优势估计（GAE）
        
        Args:
            rewards: 奖励 (N,)
            values: 价值 (N,)
            dones: 是否结束 (N,)
        
        Returns:
            advantages: 优势 (N,)
        """
        advantages = torch.zeros_like(rewards)
        last_advantage = 0
        
        # 从后往前计算
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
            
            # TD error
            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            
            # GAE
            advantages[t] = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_advantage
            last_advantage = advantages[t]
        
        return advantages
    
    def save(self, path: str):
        """保存智能体"""
        save_model(
            self.model, path, self.optimizer,
            metadata={
                'total_steps': self.total_steps,
                'total_episodes': self.total_episodes,
                'total_updates': self.total_updates,
            }
        )
    
    def load(self, path: str):
        """加载智能体"""
        checkpoint = load_model(self.model, path, self.optimizer, self.device)
        
        if 'metadata' in checkpoint:
            metadata = checkpoint['metadata']
            self.total_steps = metadata.get('total_steps', 0)
            self.total_episodes = metadata.get('total_episodes', 0)
            self.total_updates = metadata.get('total_updates', 0)
    
    def set_training_mode(self, mode: bool = True):
        """设置训练/评估模式"""
        self.training = mode
        if mode:
            self.model.train()
        else:
            self.model.eval()


class PPODataset(Dataset):
    """PPO训练数据集"""
    
    def __init__(self, 
                 states: torch.Tensor,
                 actions: torch.Tensor,
                 old_log_probs: torch.Tensor,
                 advantages: torch.Tensor,
                 returns: torch.Tensor,
                 action_masks: Optional[torch.Tensor] = None,
                 action_dim: int = 12):
        self.states = states
        self.actions = actions
        self.old_log_probs = old_log_probs
        self.advantages = advantages
        self.returns = returns
        self.action_masks = action_masks
        self.action_dim = action_dim
    
    def __len__(self):
        return len(self.states)
    
    def __getitem__(self, idx):
        # 如果没有掩码，返回全True的掩码（所有动作都有效）
        if self.action_masks is not None:
            mask = self.action_masks[idx]
        else:
            # 创建全True的掩码，大小为action_dim
            # 注意：这里创建的mask会在DataLoader中自动与其他tensor的device对齐
            mask = torch.ones(self.action_dim, dtype=torch.bool)
        
        return (
            self.states[idx],
            self.actions[idx],
            self.old_log_probs[idx],
            self.advantages[idx],
            self.returns[idx],
            mask
        )


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 PPOAgent...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    # 测试1: 创建PPO智能体
    print("\n测试1: 创建PPO智能体")
    agent = PPOAgent(
        state_dim=54,
        action_dim=12,
        learning_rate=3e-4,
        gamma=0.99,
        device=device
    )
    
    stats = agent.get_stats()
    print("智能体统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试2: 动作选择
    print("\n测试2: 动作选择")
    obs = np.random.randn(54)
    
    # 随机选择
    for i in range(3):
        action1, action2 = agent.select_action(obs, deterministic=False)
        print(f"  随机选择 {i+1}: ({action1}, {action2})")
    
    # 确定性选择
    for i in range(3):
        action1, action2 = agent.select_action(obs, deterministic=True)
        print(f"  确定性选择 {i+1}: ({action1}, {action2})")
    
    # 测试3: 带动作掩码的选择
    print("\n测试3: 带动作掩码")
    mask = np.array([True] * 12)
    mask[[3, 4]] = False  # 禁用grab和throw
    
    for i in range(3):
        action1, action2 = agent.select_action(obs, valid_actions=mask)
        print(f"  掩码选择 {i+1}: ({action1}, {action2})")
        if action1 in [3, 4] or action2 in [3, 4]:
            print("    ⚠️ 选择了被禁用的动作！")
    
    # 测试4: 更新（模拟训练）
    print("\n测试4: PPO更新")
    
    # 创建模拟数据
    batch_size = 32
    states = np.random.randn(batch_size, 54)
    actions = np.random.randint(0, 12, size=(batch_size, 2))
    rewards = np.random.randn(batch_size)
    next_states = np.random.randn(batch_size, 54)
    dones = np.random.randint(0, 2, size=batch_size).astype(float)
    
    # 执行更新
    metrics = agent.update(
        states, actions, rewards, next_states, dones,
        epochs=2, batch_size=16
    )
    
    print("更新指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")
    
    # 测试5: 多次更新
    print("\n测试5: 多次更新")
    for i in range(3):
        metrics = agent.update(
            states, actions, rewards, next_states, dones,
            epochs=1, batch_size=16
        )
        print(f"  更新 {i+1}: loss={metrics['total_loss']:.4f}")
    
    # 测试6: 保存和加载
    print("\n测试6: 保存和加载")
    save_path = "test_ppo_agent.pth"
    
    agent.total_steps = 1000
    agent.total_episodes = 50
    agent.save(save_path)
    
    # 创建新智能体并加载
    new_agent = PPOAgent(state_dim=54, action_dim=12, device=device)
    new_agent.load(save_path)
    
    print(f"加载后的统计:")
    print(f"  total_steps: {new_agent.total_steps}")
    print(f"  total_episodes: {new_agent.total_episodes}")
    print(f"  total_updates: {new_agent.total_updates}")
    
    # 清理测试文件
    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"已删除测试文件: {save_path}")
    
    # 测试7: 训练/评估模式
    print("\n测试7: 训练/评估模式")
    agent.set_training_mode(True)
    print(f"训练模式: {agent.model.training}")
    
    agent.set_training_mode(False)
    print(f"评估模式: {agent.model.training}")
    
    # 测试8: GAE计算
    print("\n测试8: GAE计算")
    test_rewards = torch.FloatTensor([1.0, 2.0, 3.0, 4.0, 5.0]).to(device)
    test_values = torch.FloatTensor([0.5, 1.0, 1.5, 2.0, 2.5]).to(device)
    test_dones = torch.FloatTensor([0, 0, 0, 0, 1]).to(device)
    
    advantages = agent._compute_gae(test_rewards, test_values, test_dones)
    print(f"奖励: {test_rewards.cpu().numpy()}")
    print(f"价值: {test_values.cpu().numpy()}")
    print(f"优势: {advantages.cpu().numpy()}")
    
    print("\n✅ PPOAgent 测试完成！")