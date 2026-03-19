"""
replay_buffer.py
经验回放缓冲区 / Experience Replay Buffer

用于存储和采样训练数据
"""

import sys
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import deque

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)


class ReplayBuffer:
    """
    经验回放缓冲区
    
    存储(state, action, reward, next_state, done)经验
    """
    
    def __init__(self, capacity: int = 10000):
        """
        初始化缓冲区
        
        Args:
            capacity: 最大容量
        """
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
    
    def push(self,
            state: np.ndarray,
            action: Tuple[int, int],
            reward: float,
            next_state: np.ndarray,
            done: bool,
            action_mask: Optional[np.ndarray] = None):
        """
        添加一条经验
        
        Args:
            state: 状态
            action: 动作元组(action1, action2)
            reward: 奖励
            next_state: 下一状态
            done: 是否结束
            action_mask: 动作掩码
        """
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'action_mask': action_mask
        }
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> Dict[str, np.ndarray]:
        """
        随机采样一批经验
        
        Args:
            batch_size: 批大小
        
        Returns:
            经验批次字典
        """
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        action_masks = []
        
        for idx in indices:
            exp = self.buffer[idx]
            states.append(exp['state'])
            actions.append(exp['action'])
            rewards.append(exp['reward'])
            next_states.append(exp['next_state'])
            dones.append(exp['done'])
            if exp['action_mask'] is not None:
                action_masks.append(exp['action_mask'])
        
        batch = {
            'states': np.array(states),
            'actions': np.array(actions),
            'rewards': np.array(rewards),
            'next_states': np.array(next_states),
            'dones': np.array(dones)
        }
        
        if action_masks:
            batch['action_masks'] = np.array(action_masks)
        
        return batch
    
    def get_all(self) -> Dict[str, np.ndarray]:
        """
        获取所有经验
        
        Returns:
            所有经验的字典
        """
        if len(self.buffer) == 0:
            return None
        
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        action_masks = []
        
        for exp in self.buffer:
            states.append(exp['state'])
            actions.append(exp['action'])
            rewards.append(exp['reward'])
            next_states.append(exp['next_state'])
            dones.append(exp['done'])
            if exp['action_mask'] is not None:
                action_masks.append(exp['action_mask'])
        
        batch = {
            'states': np.array(states),
            'actions': np.array(actions),
            'rewards': np.array(rewards),
            'next_states': np.array(next_states),
            'dones': np.array(dones)
        }
        
        if action_masks:
            batch['action_masks'] = np.array(action_masks)
        
        return batch
    
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
    
    def __len__(self):
        """返回缓冲区大小"""
        return len(self.buffer)


class EpisodeBuffer:
    """
    Episode缓冲区
    
    专门用于存储完整episode的数据（适合PPO等on-policy算法）
    """
    
    def __init__(self):
        """初始化episode缓冲区"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.action_masks = []
        
        self.episode_count = 0
    
    def push(self,
            state: np.ndarray,
            action: Tuple[int, int],
            reward: float,
            next_state: np.ndarray,
            done: bool,
            action_mask: Optional[np.ndarray] = None):
        """
        添加一条经验
        
        Args:
            state: 状态
            action: 动作
            reward: 奖励
            next_state: 下一状态
            done: 是否结束
            action_mask: 动作掩码
        """
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)
        
        if action_mask is not None:
            self.action_masks.append(action_mask)
        
        if done:
            self.episode_count += 1
    
    def get_all(self) -> Dict[str, np.ndarray]:
        """
        获取所有数据
        
        Returns:
            数据字典
        """
        if len(self.states) == 0:
            return None
        
        batch = {
            'states': np.array(self.states),
            'actions': np.array(self.actions),
            'rewards': np.array(self.rewards),
            'next_states': np.array(self.next_states),
            'dones': np.array(self.dones)
        }
        
        if self.action_masks:
            batch['action_masks'] = np.array(self.action_masks)
        
        return batch
    
    def clear(self):
        """清空缓冲区"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.action_masks = []
        self.episode_count = 0
    
    def __len__(self):
        """返回样本数量"""
        return len(self.states)


class PrioritizedReplayBuffer:
    """
    优先级经验回放缓冲区（Prioritized Experience Replay）
    
    根据TD-error优先采样重要的经验
    """
    
    def __init__(self, capacity: int = 10000, alpha: float = 0.6, beta: float = 0.4):
        """
        初始化优先级缓冲区
        
        Args:
            capacity: 最大容量
            alpha: 优先级指数（0=均匀采样，1=完全按优先级）
            beta: 重要性采样权重（0=不修正，1=完全修正）
        """
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.size = 0
    
    def push(self,
            state: np.ndarray,
            action: Tuple[int, int],
            reward: float,
            next_state: np.ndarray,
            done: bool,
            action_mask: Optional[np.ndarray] = None):
        """添加经验（最大优先级）"""
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'action_mask': action_mask
        }
        
        # 新经验赋予最大优先级
        max_priority = self.priorities.max() if self.size > 0 else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
    
    def sample(self, batch_size: int) -> Tuple[Dict[str, np.ndarray], np.ndarray, np.ndarray]:
        """
        按优先级采样
        
        Args:
            batch_size: 批大小
        
        Returns:
            (batch, weights, indices)
        """
        # 计算采样概率
        priorities = self.priorities[:self.size]
        probs = priorities ** self.alpha
        probs /= probs.sum()
        
        # 采样
        indices = np.random.choice(self.size, batch_size, p=probs, replace=False)
        
        # 计算重要性采样权重
        total = self.size
        weights = (total * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # 收集经验
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        action_masks = []
        
        for idx in indices:
            exp = self.buffer[idx]
            states.append(exp['state'])
            actions.append(exp['action'])
            rewards.append(exp['reward'])
            next_states.append(exp['next_state'])
            dones.append(exp['done'])
            if exp['action_mask'] is not None:
                action_masks.append(exp['action_mask'])
        
        batch = {
            'states': np.array(states),
            'actions': np.array(actions),
            'rewards': np.array(rewards),
            'next_states': np.array(next_states),
            'dones': np.array(dones)
        }
        
        if action_masks:
            batch['action_masks'] = np.array(action_masks)
        
        return batch, weights, indices
    
    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray):
        """
        更新优先级
        
        Args:
            indices: 索引
            priorities: 新的优先级（通常是TD-error）
        """
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-6  # 避免0优先级
    
    def __len__(self):
        return self.size


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 ReplayBuffer...")
    
    # 测试1: 基础缓冲区
    print("\n测试1: 基础ReplayBuffer")
    buffer = ReplayBuffer(capacity=100)
    
    # 添加经验
    for i in range(50):
        state = np.random.randn(54)
        action = (np.random.randint(0, 12), np.random.randint(0, 12))
        reward = np.random.randn()
        next_state = np.random.randn(54)
        done = i % 10 == 9
        
        buffer.push(state, action, reward, next_state, done)
    
    print(f"缓冲区大小: {len(buffer)}")
    
    # 采样
    batch = buffer.sample(batch_size=16)
    print(f"采样批次形状:")
    for key, value in batch.items():
        print(f"  {key}: {value.shape}")
    
    # 测试2: Episode缓冲区
    print("\n测试2: EpisodeBuffer")
    episode_buffer = EpisodeBuffer()
    
    # 模拟3个episode
    for episode in range(3):
        for step in range(10):
            state = np.random.randn(54)
            action = (np.random.randint(0, 12), np.random.randint(0, 12))
            reward = np.random.randn()
            next_state = np.random.randn(54)
            done = step == 9
            
            episode_buffer.push(state, action, reward, next_state, done)
    
    print(f"Episode数量: {episode_buffer.episode_count}")
    print(f"样本数量: {len(episode_buffer)}")
    
    # 获取所有数据
    all_data = episode_buffer.get_all()
    print(f"所有数据形状:")
    for key, value in all_data.items():
        print(f"  {key}: {value.shape}")
    
    # 清空
    episode_buffer.clear()
    print(f"清空后大小: {len(episode_buffer)}")
    
    # 测试3: 优先级缓冲区
    print("\n测试3: PrioritizedReplayBuffer")
    prio_buffer = PrioritizedReplayBuffer(capacity=100, alpha=0.6, beta=0.4)
    
    # 添加经验
    for i in range(50):
        state = np.random.randn(54)
        action = (np.random.randint(0, 12), np.random.randint(0, 12))
        reward = np.random.randn()
        next_state = np.random.randn(54)
        done = i % 10 == 9
        
        prio_buffer.push(state, action, reward, next_state, done)
    
    print(f"优先级缓冲区大小: {len(prio_buffer)}")
    
    # 采样
    batch, weights, indices = prio_buffer.sample(batch_size=16)
    print(f"采样批次形状:")
    for key, value in batch.items():
        print(f"  {key}: {value.shape}")
    print(f"权重形状: {weights.shape}")
    print(f"索引: {indices}")
    
    # 更新优先级
    new_priorities = np.random.rand(16) * 10
    prio_buffer.update_priorities(indices, new_priorities)
    print(f"已更新{len(indices)}个优先级")
    
    # 测试4: 容量限制
    print("\n测试4: 容量限制测试")
    small_buffer = ReplayBuffer(capacity=10)
    
    for i in range(20):
        state = np.random.randn(54)
        action = (i % 12, (i+1) % 12)
        small_buffer.push(state, action, 0, state, False)
    
    print(f"添加20个经验后，缓冲区大小: {len(small_buffer)} (最大10)")
    
    # 测试5: 带动作掩码
    print("\n测试5: 带动作掩码")
    buffer_with_mask = ReplayBuffer(capacity=50)
    
    for i in range(20):
        state = np.random.randn(54)
        action = (np.random.randint(0, 12), np.random.randint(0, 12))
        reward = np.random.randn()
        next_state = np.random.randn(54)
        done = False
        mask = np.random.rand(12) > 0.5  # 随机掩码
        
        buffer_with_mask.push(state, action, reward, next_state, done, action_mask=mask)
    
    batch_with_mask = buffer_with_mask.sample(8)
    print("带掩码的批次:")
    for key, value in batch_with_mask.items():
        print(f"  {key}: {value.shape}")
    
    print("\n✅ ReplayBuffer 测试完成！")