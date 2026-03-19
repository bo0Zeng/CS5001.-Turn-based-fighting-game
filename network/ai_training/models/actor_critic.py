"""
actor_critic.py
Actor-Critic架构 - 结合策略网络和价值网络 / Actor-Critic Architecture

实现了：
- 基础Actor-Critic
- 共享特征的Actor-Critic
- 适用于PPO的Actor-Critic
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import numpy as np


class ActorCritic(nn.Module):
    """
    Actor-Critic网络（分离式）
    
    包含独立的策略网络(Actor)和价值网络(Critic)
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 hidden_sizes: Tuple[int, ...] = (256, 128),
                 activation: str = 'relu'):
        """
        初始化Actor-Critic网络
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_sizes: 隐藏层大小
            activation: 激活函数
        """
        super(ActorCritic, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 激活函数
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'elu':
            self.activation = nn.ELU()
        else:
            self.activation = nn.ReLU()
        
        # Actor网络
        actor_layers = []
        input_size = state_dim
        for hidden_size in hidden_sizes:
            actor_layers.append(nn.Linear(input_size, hidden_size))
            actor_layers.append(self.activation)
            input_size = hidden_size
        self.actor_features = nn.Sequential(*actor_layers)
        self.actor_head = nn.Linear(input_size, action_dim)
        
        # Critic网络
        critic_layers = []
        input_size = state_dim
        for hidden_size in hidden_sizes:
            critic_layers.append(nn.Linear(input_size, hidden_size))
            critic_layers.append(self.activation)
            input_size = hidden_size
        self.critic_features = nn.Sequential(*critic_layers)
        self.critic_head = nn.Linear(input_size, 1)
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        
        # 输出层特殊初始化
        nn.init.orthogonal_(self.actor_head.weight, gain=0.01)
        nn.init.constant_(self.actor_head.bias, 0.0)
        nn.init.orthogonal_(self.critic_head.weight, gain=1.0)
        nn.init.constant_(self.critic_head.bias, 0.0)
    
    def forward(self, state: torch.Tensor, action_mask: Optional[torch.Tensor] = None
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        Args:
            state: 状态 (batch_size, state_dim)
            action_mask: 动作掩码 (batch_size, action_dim)
        
        Returns:
            action_probs: 动作概率分布 (batch_size, action_dim)
            values: 状态价值 (batch_size, 1)
        """
        # Actor前向
        actor_features = self.actor_features(state)
        action_logits = self.actor_head(actor_features)
        
        # 应用动作掩码
        if action_mask is not None:
            action_logits = action_logits.masked_fill(~action_mask, -1e8)
        
        action_probs = F.softmax(action_logits, dim=-1)
        
        # Critic前向
        critic_features = self.critic_features(state)
        values = self.critic_head(critic_features)
        
        return action_probs, values
    
    def get_action_and_value(self,
                            state: torch.Tensor,
                            action_mask: Optional[torch.Tensor] = None,
                            deterministic: bool = False
                            ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        获取动作和价值
        
        Args:
            state: 状态
            action_mask: 动作掩码
            deterministic: 是否确定性选择
        
        Returns:
            actions: 选择的动作
            log_probs: 对数概率
            values: 状态价值
        """
        action_probs, values = self.forward(state, action_mask)
        
        if deterministic:
            actions = torch.argmax(action_probs, dim=-1)
        else:
            dist = torch.distributions.Categorical(action_probs)
            actions = dist.sample()
        
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        
        return actions, log_probs, values.squeeze(1)
    
    def evaluate_actions(self,
                        state: torch.Tensor,
                        actions: torch.Tensor,
                        action_mask: Optional[torch.Tensor] = None
                        ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        评估动作（用于PPO更新）
        
        Args:
            state: 状态
            actions: 动作
            action_mask: 动作掩码
        
        Returns:
            log_probs: 对数概率
            values: 状态价值
            entropy: 策略熵
        """
        action_probs, values = self.forward(state, action_mask)
        
        # 对数概率
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        
        # 熵（用于探索）
        entropy = -(action_probs * torch.log(action_probs + 1e-8)).sum(dim=-1)
        
        return log_probs, values.squeeze(1), entropy


class SharedActorCritic(nn.Module):
    """
    共享特征的Actor-Critic网络
    
    Actor和Critic共享前面的特征提取层，可以提高样本效率
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 shared_hidden_sizes: Tuple[int, ...] = (256,),
                 actor_hidden_sizes: Tuple[int, ...] = (128,),
                 critic_hidden_sizes: Tuple[int, ...] = (128,),
                 activation: str = 'relu'):
        """
        初始化共享Actor-Critic
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            shared_hidden_sizes: 共享层大小
            actor_hidden_sizes: Actor独立层大小
            critic_hidden_sizes: Critic独立层大小
            activation: 激活函数
        """
        super(SharedActorCritic, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 激活函数
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        else:
            self.activation = nn.ReLU()
        
        # 共享特征层
        shared_layers = []
        input_size = state_dim
        for hidden_size in shared_hidden_sizes:
            shared_layers.append(nn.Linear(input_size, hidden_size))
            shared_layers.append(self.activation)
            input_size = hidden_size
        self.shared_features = nn.Sequential(*shared_layers)
        
        # Actor独立层
        actor_layers = []
        for hidden_size in actor_hidden_sizes:
            actor_layers.append(nn.Linear(input_size, hidden_size))
            actor_layers.append(self.activation)
            input_size = hidden_size
        self.actor_features = nn.Sequential(*actor_layers)
        self.actor_head = nn.Linear(input_size, action_dim)
        
        # Critic独立层
        input_size = shared_hidden_sizes[-1]
        critic_layers = []
        for hidden_size in critic_hidden_sizes:
            critic_layers.append(nn.Linear(input_size, hidden_size))
            critic_layers.append(self.activation)
            input_size = hidden_size
        self.critic_features = nn.Sequential(*critic_layers)
        self.critic_head = nn.Linear(input_size, 1)
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        
        nn.init.orthogonal_(self.actor_head.weight, gain=0.01)
        nn.init.constant_(self.actor_head.bias, 0.0)
        nn.init.orthogonal_(self.critic_head.weight, gain=1.0)
        nn.init.constant_(self.critic_head.bias, 0.0)
    
    def forward(self, state: torch.Tensor, action_mask: Optional[torch.Tensor] = None
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向传播"""
        # 共享特征
        shared_features = self.shared_features(state)
        
        # Actor
        actor_features = self.actor_features(shared_features)
        action_logits = self.actor_head(actor_features)
        
        if action_mask is not None:
            action_logits = action_logits.masked_fill(~action_mask, -1e8)
        
        action_probs = F.softmax(action_logits, dim=-1)
        
        # Critic
        critic_features = self.critic_features(shared_features)
        values = self.critic_head(critic_features)
        
        return action_probs, values
    
    def get_action_and_value(self,
                            state: torch.Tensor,
                            action_mask: Optional[torch.Tensor] = None,
                            deterministic: bool = False
                            ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """获取动作和价值"""
        action_probs, values = self.forward(state, action_mask)
        
        if deterministic:
            actions = torch.argmax(action_probs, dim=-1)
        else:
            dist = torch.distributions.Categorical(action_probs)
            actions = dist.sample()
        
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        
        return actions, log_probs, values.squeeze(1)
    
    def evaluate_actions(self,
                        state: torch.Tensor,
                        actions: torch.Tensor,
                        action_mask: Optional[torch.Tensor] = None
                        ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """评估动作"""
        action_probs, values = self.forward(state, action_mask)
        
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        entropy = -(action_probs * torch.log(action_probs + 1e-8)).sum(dim=-1)
        
        return log_probs, values.squeeze(1), entropy


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 ActorCritic...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    # 测试1: 基础Actor-Critic
    print("\n测试1: 基础Actor-Critic")
    ac = ActorCritic(state_dim=54, action_dim=12).to(device)
    print(f"模型参数量: {sum(p.numel() for p in ac.parameters()):,}")
    
    # 测试输入
    batch_size = 4
    state = torch.randn(batch_size, 54).to(device)
    action_mask = torch.ones(batch_size, 12, dtype=torch.bool).to(device)
    
    # 前向传播
    action_probs, values = ac(state, action_mask)
    print(f"动作概率形状: {action_probs.shape}")
    print(f"价值形状: {values.shape}")
    print(f"示例动作概率: {action_probs[0]}")
    print(f"示例价值: {values[0].item()}")
    
    # 测试2: 获取动作和价值
    print("\n测试2: 获取动作和价值")
    actions, log_probs, values = ac.get_action_and_value(state, action_mask, deterministic=False)
    print(f"采样动作: {actions}")
    print(f"对数概率: {log_probs}")
    print(f"价值: {values}")
    
    # 确定性选择
    det_actions, det_log_probs, det_values = ac.get_action_and_value(state, action_mask, deterministic=True)
    print(f"确定性动作: {det_actions}")
    
    # 测试3: 评估动作
    print("\n测试3: 评估动作")
    test_actions = torch.tensor([0, 5, 7, 11]).to(device)
    log_probs, values, entropy = ac.evaluate_actions(state, test_actions, action_mask)
    print(f"评估对数概率: {log_probs}")
    print(f"评估价值: {values}")
    print(f"策略熵: {entropy}")
    
    # 测试4: 共享Actor-Critic
    print("\n测试4: 共享Actor-Critic")
    shared_ac = SharedActorCritic(
        state_dim=54, 
        action_dim=12,
        shared_hidden_sizes=(256,),
        actor_hidden_sizes=(128,),
        critic_hidden_sizes=(128,)
    ).to(device)
    print(f"共享模型参数量: {sum(p.numel() for p in shared_ac.parameters()):,}")
    
    # 前向传播
    action_probs, values = shared_ac(state, action_mask)
    print(f"动作概率形状: {action_probs.shape}")
    print(f"价值形状: {values.shape}")
    
    # 测试5: 比较两种架构
    print("\n测试5: 比较分离式和共享式")
    test_state = torch.randn(1, 54).to(device)
    test_mask = torch.ones(1, 12, dtype=torch.bool).to(device)
    
    # 分离式
    sep_probs, sep_values = ac(test_state, test_mask)
    sep_action, _, _ = ac.get_action_and_value(test_state, test_mask, deterministic=True)
    
    # 共享式
    shared_probs, shared_values = shared_ac(test_state, test_mask)
    shared_action, _, _ = shared_ac.get_action_and_value(test_state, test_mask, deterministic=True)
    
    print(f"分离式 - 选择动作: {sep_action.item()}, 价值: {sep_values.item():.4f}")
    print(f"共享式 - 选择动作: {shared_action.item()}, 价值: {shared_values.item():.4f}")
    
    # 测试6: 训练循环模拟
    print("\n测试6: 训练循环模拟")
    ac.train()
    optimizer = torch.optim.Adam(ac.parameters(), lr=3e-4)
    
    # 模拟一个训练步
    actions, old_log_probs, old_values = ac.get_action_and_value(state, action_mask)
    
    # 假设收集了奖励和优势
    rewards = torch.randn(batch_size).to(device)
    advantages = torch.randn(batch_size).to(device)
    returns = old_values + advantages
    
    # PPO式更新
    new_log_probs, new_values, entropy = ac.evaluate_actions(state, actions, action_mask)
    
    # 计算损失
    ratio = torch.exp(new_log_probs - old_log_probs)
    policy_loss = -torch.min(
        ratio * advantages,
        torch.clamp(ratio, 0.8, 1.2) * advantages
    ).mean()
    
    value_loss = F.mse_loss(new_values, returns)
    entropy_loss = -entropy.mean()
    
    total_loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss
    
    # 反向传播
    optimizer.zero_grad()
    total_loss.backward()
    torch.nn.utils.clip_grad_norm_(ac.parameters(), 0.5)
    optimizer.step()
    
    print(f"策略损失: {policy_loss.item():.4f}")
    print(f"价值损失: {value_loss.item():.4f}")
    print(f"熵损失: {entropy_loss.item():.4f}")
    print(f"总损失: {total_loss.item():.4f}")
    print("训练步骤完成！")
    
    print("\n✅ ActorCritic 测试完成！")