"""
value_network.py
价值网络 - 输入状态，输出状态价值 / Value Network - State to Value Estimation

实现了多种价值网络架构：
- 基础价值网络（Critic）
- Dueling网络架构
- 循环价值网络（LSTM）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import numpy as np


class ValueNetwork(nn.Module):
    """
    价值网络（Critic）
    
    架构：
    输入层: 状态特征 (54维)
    隐藏层: FC(256) -> ReLU -> FC(128) -> ReLU
    输出层: FC(1) (状态价值V(s))
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 hidden_sizes: Tuple[int, ...] = (256, 128),
                 activation: str = 'relu'):
        """
        初始化价值网络
        
        Args:
            state_dim: 状态维度
            hidden_sizes: 隐藏层大小元组
            activation: 激活函数
        """
        super(ValueNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.hidden_sizes = hidden_sizes
        
        # 激活函数
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'elu':
            self.activation = nn.ELU()
        else:
            self.activation = nn.ReLU()
        
        # 构建网络
        layers = []
        input_size = state_dim
        
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(self.activation)
            input_size = hidden_size
        
        self.feature_layers = nn.Sequential(*layers)
        
        # 价值输出层
        self.value_head = nn.Linear(input_size, 1)
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        
        # 价值头使用较小的初始化
        nn.init.orthogonal_(self.value_head.weight, gain=1.0)
        nn.init.constant_(self.value_head.bias, 0.0)
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            state: 状态张量 (batch_size, state_dim)
        
        Returns:
            values: 状态价值 (batch_size, 1)
        """
        # 特征提取
        features = self.feature_layers(state)
        
        # 价值预测
        values = self.value_head(features)
        
        return values


class DuelingNetwork(nn.Module):
    """
    Dueling网络架构
    
    将Q值分解为状态价值V(s)和优势函数A(s,a)：
    Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
    
    适用于DQN等Q-learning算法
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 hidden_sizes: Tuple[int, ...] = (256, 128),
                 activation: str = 'relu'):
        """
        初始化Dueling网络
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_sizes: 隐藏层大小
            activation: 激活函数
        """
        super(DuelingNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 激活函数
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        else:
            self.activation = nn.ReLU()
        
        # 共享特征提取层
        shared_layers = []
        input_size = state_dim
        
        for i, hidden_size in enumerate(hidden_sizes[:-1]):
            shared_layers.append(nn.Linear(input_size, hidden_size))
            shared_layers.append(self.activation)
            input_size = hidden_size
        
        self.shared_layers = nn.Sequential(*shared_layers)
        
        # 状态价值流 V(s)
        self.value_stream = nn.Sequential(
            nn.Linear(input_size, hidden_sizes[-1]),
            self.activation,
            nn.Linear(hidden_sizes[-1], 1)
        )
        
        # 优势流 A(s,a)
        self.advantage_stream = nn.Sequential(
            nn.Linear(input_size, hidden_sizes[-1]),
            self.activation,
            nn.Linear(hidden_sizes[-1], action_dim)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            state: 状态张量 (batch_size, state_dim)
        
        Returns:
            q_values: Q值 (batch_size, action_dim)
        """
        # 共享特征
        features = self.shared_layers(state)
        
        # 状态价值V(s)
        values = self.value_stream(features)  # (batch, 1)
        
        # 优势函数A(s,a)
        advantages = self.advantage_stream(features)  # (batch, action_dim)
        
        # 合并：Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
        # 减去均值使得A的期望为0
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        
        return q_values
    
    def get_value(self, state: torch.Tensor) -> torch.Tensor:
        """
        单独获取状态价值V(s)
        
        Args:
            state: 状态张量
        
        Returns:
            values: 状态价值
        """
        features = self.shared_layers(state)
        values = self.value_stream(features)
        return values


class RecurrentValueNetwork(nn.Module):
    """
    循环价值网络（使用LSTM）
    
    适用于需要历史记忆的价值估计
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 hidden_size: int = 256,
                 num_layers: int = 1):
        """
        初始化循环价值网络
        
        Args:
            state_dim: 状态维度
            hidden_size: LSTM隐藏层大小
            num_layers: LSTM层数
        """
        super(RecurrentValueNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # 输入编码
        self.input_layer = nn.Linear(state_dim, hidden_size)
        
        # LSTM
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True)
        
        # 价值输出
        self.value_head = nn.Linear(hidden_size, 1)
        
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
                hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
                ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        前向传播
        
        Args:
            state: 状态序列 (batch_size, seq_len, state_dim) 或 (batch_size, state_dim)
            hidden_state: LSTM隐藏状态
        
        Returns:
            values: 价值预测 (batch_size, seq_len, 1)
            new_hidden: 新的隐藏状态
        """
        # 确保输入是3D
        if state.dim() == 2:
            state = state.unsqueeze(1)
        
        # 输入编码
        x = F.relu(self.input_layer(state))
        
        # LSTM处理
        if hidden_state is None:
            lstm_out, new_hidden = self.lstm(x)
        else:
            lstm_out, new_hidden = self.lstm(x, hidden_state)
        
        # 价值预测
        values = self.value_head(lstm_out)
        
        return values, new_hidden
    
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
    print("测试 ValueNetwork...")
    
    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    # 测试1: 基础价值网络
    print("\n测试1: 基础价值网络")
    value_net = ValueNetwork(state_dim=54).to(device)
    print(f"模型参数量: {sum(p.numel() for p in value_net.parameters()):,}")
    
    # 创建测试输入
    batch_size = 4
    state = torch.randn(batch_size, 54).to(device)
    
    # 前向传播
    values = value_net(state)
    print(f"输出形状: {values.shape}")
    print(f"价值预测: {values.squeeze()}")
    
    # 测试2: 单个状态
    print("\n测试2: 单个状态输入")
    single_state = torch.randn(54).to(device)
    single_value = value_net(single_state.unsqueeze(0))
    print(f"单状态价值: {single_value.item()}")
    
    # 测试3: Dueling网络
    print("\n测试3: Dueling网络")
    dueling_net = DuelingNetwork(state_dim=54, action_dim=12).to(device)
    print(f"Dueling模型参数量: {sum(p.numel() for p in dueling_net.parameters()):,}")
    
    # 前向传播得到Q值
    q_values = dueling_net(state)
    print(f"Q值形状: {q_values.shape}")
    print(f"示例Q值: {q_values[0]}")
    
    # 获取状态价值
    state_values = dueling_net.get_value(state)
    print(f"状态价值: {state_values.squeeze()}")
    
    # 选择最优动作
    best_actions = torch.argmax(q_values, dim=1)
    print(f"最优动作: {best_actions}")
    
    # 测试4: 循环价值网络
    print("\n测试4: 循环价值网络")
    rnn_value = RecurrentValueNetwork(state_dim=54).to(device)
    print(f"RNN价值模型参数量: {sum(p.numel() for p in rnn_value.parameters()):,}")
    
    # 序列输入
    seq_len = 5
    state_seq = torch.randn(batch_size, seq_len, 54).to(device)
    values_seq, hidden = rnn_value(state_seq)
    print(f"RNN输出形状: {values_seq.shape}")
    print(f"隐藏状态形状: h={hidden[0].shape}, c={hidden[1].shape}")
    print(f"示例价值序列: {values_seq[0].squeeze()}")
    
    # 继续序列
    next_state = torch.randn(batch_size, 1, 54).to(device)
    next_values, new_hidden = rnn_value(next_state, hidden)
    print(f"下一步价值: {next_values.squeeze()}")
    
    # 测试5: 比较不同架构的输出
    print("\n测试5: 不同架构比较")
    test_state = torch.randn(1, 54).to(device)
    
    # 基础价值网络
    basic_value = value_net(test_state).item()
    print(f"基础价值网络预测: {basic_value:.4f}")
    
    # Dueling网络的状态价值
    dueling_value = dueling_net.get_value(test_state).item()
    print(f"Dueling网络V(s): {dueling_value:.4f}")
    
    # Dueling网络的Q值
    dueling_q = dueling_net(test_state)
    print(f"Dueling网络Q值: {dueling_q.squeeze()}")
    print(f"最大Q值: {dueling_q.max().item():.4f}")
    
    # RNN价值网络
    rnn_value_pred, _ = rnn_value(test_state)
    print(f"RNN价值网络预测: {rnn_value_pred.item():.4f}")
    
    # 测试6: 梯度流
    print("\n测试6: 梯度流测试")
    value_net.train()
    optimizer = torch.optim.Adam(value_net.parameters(), lr=1e-3)
    
    # 模拟一个训练步
    pred_values = value_net(state)
    target_values = torch.randn_like(pred_values).to(device)
    loss = F.mse_loss(pred_values, target_values)
    
    optimizer.zero_grad()
    loss.backward()
    
    # 检查梯度
    total_grad_norm = 0.0
    for p in value_net.parameters():
        if p.grad is not None:
            total_grad_norm += p.grad.norm().item() ** 2
    total_grad_norm = total_grad_norm ** 0.5
    
    print(f"损失: {loss.item():.4f}")
    print(f"总梯度范数: {total_grad_norm:.4f}")
    
    optimizer.step()
    print("梯度更新成功！")
    
    print("\n✅ ValueNetwork 测试完成！")