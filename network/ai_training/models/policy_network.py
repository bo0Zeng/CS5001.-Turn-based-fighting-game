"""
policy_network.py
策略网络 - 输入状态，输出动作概率分布 / Policy Network - State to Action Probabilities

实现了多种策略网络架构：
- MLP策略网络（全连接）
- 带动作掩码的策略网络
- 循环策略网络（LSTM）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import numpy as np


class PolicyNetwork(nn.Module):
    """
    策略网络（Actor）
    
    架构：
    输入层: 状态特征 (54维)
    隐藏层: FC(256) -> ReLU -> FC(128) -> ReLU
    输出层: FC(12) -> Softmax (12种动作概率分布)
    """
    
    def __init__(self, 
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 hidden_sizes: Tuple[int, ...] = (256, 128),
                 activation: str = 'relu'):
        """
        初始化策略网络
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_sizes: 隐藏层大小元组
            activation: 激活函数 ('relu', 'tanh', 'elu')
        """
        super(PolicyNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_sizes = hidden_sizes
        
        # 选择激活函数
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'elu':
            self.activation = nn.ELU()
        else:
            self.activation = nn.ReLU()
        
        # 构建网络层
        layers = []
        input_size = state_dim
        
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(self.activation)
            input_size = hidden_size
        
        self.feature_layers = nn.Sequential(*layers)
        
        # 输出层 - 动作logits
        self.action_head = nn.Linear(input_size, action_dim)
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        
        # 输出层使用较小的初始化
        nn.init.orthogonal_(self.action_head.weight, gain=0.01)
        nn.init.constant_(self.action_head.bias, 0.0)
    
    def forward(self, state: torch.Tensor, action_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播
        
        Args:
            state: 状态张量 (batch_size, state_dim)
            action_mask: 动作掩码 (batch_size, action_dim), True表示有效动作
        
        Returns:
            action_probs: 动作概率分布 (batch_size, action_dim)
        """
        # 特征提取
        features = self.feature_layers(state)
        
        # 计算动作logits
        action_logits = self.action_head(features)
        
        # 应用动作掩码
        if action_mask is not None:
            # 将无效动作的logit设为极小值
            action_logits = action_logits.masked_fill(~action_mask, -1e8)
        
        # Softmax得到概率分布
        action_probs = F.softmax(action_logits, dim=-1)
        
        return action_probs
    
    def get_action(self, 
                   state: torch.Tensor, 
                   action_mask: Optional[torch.Tensor] = None,
                   deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        根据状态选择动作
        
        Args:
            state: 状态张量 (batch_size, state_dim) 或 (state_dim,)
            action_mask: 动作掩码
            deterministic: 是否确定性选择（贪婪）
        
        Returns:
            actions: 选择的动作 (batch_size,)
            log_probs: 动作的对数概率 (batch_size,)
        """
        # 确保state是2D的
        if state.dim() == 1:
            state = state.unsqueeze(0)
            if action_mask is not None:
                action_mask = action_mask.unsqueeze(0)
            squeeze_output = True
        else:
            squeeze_output = False
        
        # 获取动作概率
        action_probs = self.forward(state, action_mask)
        
        if deterministic:
            # 贪婪选择概率最大的动作
            actions = torch.argmax(action_probs, dim=-1)
        else:
            # 根据概率分布采样
            dist = torch.distributions.Categorical(action_probs)
            actions = dist.sample()
        
        # 计算对数概率
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        
        if squeeze_output:
            actions = actions.squeeze(0)
            log_probs = log_probs.squeeze(0)
        
        return actions, log_probs
    
    def evaluate_actions(self, 
                        state: torch.Tensor, 
                        actions: torch.Tensor,
                        action_mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        评估给定动作的对数概率和熵
        
        Args:
            state: 状态张量 (batch_size, state_dim)
            actions: 动作张量 (batch_size,)
            action_mask: 动作掩码
        
        Returns:
            log_probs: 动作对数概率 (batch_size,)
            entropy: 策略熵 (batch_size,)
        """
        # 获取动作概率
        action_probs = self.forward(state, action_mask)
        
        # 计算对数概率
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8).squeeze(1)
        
        # 计算熵（用于探索）
        entropy = -(action_probs * torch.log(action_probs + 1e-8)).sum(dim=-1)
        
        return log_probs, entropy


class RecurrentPolicyNetwork(nn.Module):
    """
    循环策略网络（使用LSTM处理序列信息）
    
    适用于需要记忆历史的场景
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 hidden_size: int = 256,
                 num_layers: int = 1):
        """
        初始化循环策略网络
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_size: LSTM隐藏层大小
            num_layers: LSTM层数
        """
        super(RecurrentPolicyNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # 输入编码层
        self.input_layer = nn.Linear(state_dim, hidden_size)
        
        # LSTM层
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True)
        
        # 输出层
        self.action_head = nn.Linear(hidden_size, action_dim)
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.orthogonal_(param, gain=np.sqrt(2))
            elif 'bias' in name:
                nn.init.constant_(param, 0.0)
    
    def forward(self, 
                state: torch.Tensor, 
                hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
                action_mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        前向传播
        
        Args:
            state: 状态序列 (batch_size, seq_len, state_dim) 或 (batch_size, state_dim)
            hidden_state: LSTM隐藏状态 (h, c)
            action_mask: 动作掩码
        
        Returns:
            action_probs: 动作概率 (batch_size, seq_len, action_dim)
            new_hidden: 新的隐藏状态
        """
        # 确保输入是3D的
        if state.dim() == 2:
            state = state.unsqueeze(1)  # (batch, 1, state_dim)
        
        batch_size, seq_len, _ = state.size()
        
        # 输入编码
        x = F.relu(self.input_layer(state))
        
        # LSTM处理
        if hidden_state is None:
            lstm_out, new_hidden = self.lstm(x)
        else:
            lstm_out, new_hidden = self.lstm(x, hidden_state)
        
        # 输出动作logits
        action_logits = self.action_head(lstm_out)
        
        # 应用掩码
        if action_mask is not None:
            if action_mask.dim() == 2:
                action_mask = action_mask.unsqueeze(1).expand_as(action_logits)
            action_logits = action_logits.masked_fill(~action_mask, -1e8)
        
        # Softmax
        action_probs = F.softmax(action_logits, dim=-1)
        
        return action_probs, new_hidden
    
    def init_hidden(self, batch_size: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        初始化LSTM隐藏状态
        
        Args:
            batch_size: 批大小
            device: 设备
        
        Returns:
            (h, c): 初始化的隐藏状态
        """
        h = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        c = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        return (h, c)


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 PolicyNetwork...")
    
    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    # 测试1: 基础策略网络
    print("\n测试1: 基础策略网络")
    policy = PolicyNetwork(state_dim=54, action_dim=12).to(device)
    print(f"模型参数量: {sum(p.numel() for p in policy.parameters()):,}")
    
    # 创建测试输入
    batch_size = 4
    state = torch.randn(batch_size, 54).to(device)
    
    # 前向传播
    action_probs = policy(state)
    print(f"输出形状: {action_probs.shape}")
    print(f"概率和: {action_probs.sum(dim=1)}")  # 应该都是1
    print(f"示例概率: {action_probs[0]}")
    
    # 测试2: 带动作掩码
    print("\n测试2: 带动作掩码")
    action_mask = torch.ones(batch_size, 12, dtype=torch.bool).to(device)
    action_mask[:, [3, 4]] = False  # 禁用grab和throw
    
    masked_probs = policy(state, action_mask)
    print(f"掩码后的概率[0]: {masked_probs[0]}")
    print(f"动作3和4的概率: {masked_probs[0, [3, 4]]}")  # 应该接近0
    
    # 测试3: 动作选择
    print("\n测试3: 动作选择")
    actions, log_probs = policy.get_action(state, action_mask, deterministic=False)
    print(f"采样的动作: {actions}")
    print(f"对数概率: {log_probs}")
    
    # 确定性选择
    det_actions, det_log_probs = policy.get_action(state, action_mask, deterministic=True)
    print(f"贪婪动作: {det_actions}")
    
    # 测试4: 动作评估
    print("\n测试4: 动作评估")
    test_actions = torch.tensor([0, 5, 7, 11]).to(device)
    log_probs, entropy = policy.evaluate_actions(state, test_actions, action_mask)
    print(f"评估对数概率: {log_probs}")
    print(f"策略熵: {entropy}")
    
    # 测试5: 单个状态输入
    print("\n测试5: 单个状态输入")
    single_state = torch.randn(54).to(device)
    single_mask = torch.ones(12, dtype=torch.bool).to(device)
    single_action, single_log_prob = policy.get_action(single_state, single_mask)
    print(f"单状态动作: {single_action.item()}")
    print(f"单状态对数概率: {single_log_prob.item()}")
    
    # 测试6: 循环策略网络
    print("\n测试6: 循环策略网络")
    rnn_policy = RecurrentPolicyNetwork(state_dim=54, action_dim=12).to(device)
    print(f"RNN模型参数量: {sum(p.numel() for p in rnn_policy.parameters()):,}")
    
    # 序列输入
    seq_len = 5
    state_seq = torch.randn(batch_size, seq_len, 54).to(device)
    action_probs_seq, hidden = rnn_policy(state_seq)
    print(f"RNN输出形状: {action_probs_seq.shape}")
    print(f"隐藏状态形状: h={hidden[0].shape}, c={hidden[1].shape}")
    
    # 继续序列
    next_state = torch.randn(batch_size, 1, 54).to(device)
    next_probs, new_hidden = rnn_policy(next_state, hidden)
    print(f"下一步输出形状: {next_probs.shape}")
    
    print("\n✅ PolicyNetwork 测试完成！")