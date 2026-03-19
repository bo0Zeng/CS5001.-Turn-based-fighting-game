"""
base_agent.py
基础智能体类 - 定义智能体接口 / Base Agent Class - Define Agent Interface

所有智能体都应继承这个基类
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import numpy as np
import torch

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # ai_training/agents/
ai_training_dir = os.path.dirname(current_dir)             # ai_training/
project_root = os.path.dirname(ai_training_dir)            # 项目根目录
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)


class BaseAgent(ABC):
    """
    基础智能体抽象类
    
    定义了所有智能体必须实现的接口
    """
    
    def __init__(self, 
                 agent_name: str = "Agent",
                 device: Optional[torch.device] = None):
        """
        初始化基础智能体
        
        Args:
            agent_name: 智能体名称
            device: 计算设备
        """
        self.agent_name = agent_name
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        print(f"✅ {self.agent_name} 初始化完成，使用设备: {self.device}")
    
    @abstractmethod
    def select_action(self, 
                     observation: np.ndarray,
                     valid_actions: Optional[np.ndarray] = None,
                     deterministic: bool = False) -> Tuple[int, int]:
        """
        选择动作（一个完整回合的2个动作）
        
        Args:
            observation: 当前观察（状态）
            valid_actions: 有效动作掩码
            deterministic: 是否确定性选择
        
        Returns:
            (action1, action2): 两个动作的元组
        """
        raise NotImplementedError
    
    @abstractmethod
    def update(self, *args, **kwargs) -> Dict[str, float]:
        """
        更新智能体（训练）
        
        Returns:
            训练指标字典
        """
        raise NotImplementedError
    
    def save(self, path: str):
        """
        保存智能体
        
        Args:
            path: 保存路径
        """
        raise NotImplementedError("子类需要实现 save() 方法")
    
    def load(self, path: str):
        """
        加载智能体
        
        Args:
            path: 加载路径
        """
        raise NotImplementedError("子类需要实现 load() 方法")
    
    def reset(self):
        """
        重置智能体状态（用于新episode开始）
        """
        pass
    
    def get_name(self) -> str:
        """获取智能体名称"""
        return self.agent_name
    
    def set_training_mode(self, mode: bool = True):
        """
        设置训练/评估模式
        
        Args:
            mode: True为训练模式，False为评估模式
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取智能体统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'agent_name': self.agent_name,
            'device': str(self.device),
        }


class RLAgent(BaseAgent):
    """
    强化学习智能体基类
    
    为强化学习算法提供通用功能
    """
    
    def __init__(self,
                 state_dim: int = 66,  # 更新默认值为66
                 action_dim: int = 12,
                 agent_name: str = "RLAgent",
                 device: Optional[torch.device] = None,
                 learning_rate: float = 3e-4,
                 gamma: float = 0.99):
        """
        初始化RL智能体
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            agent_name: 智能体名称
            device: 计算设备
            learning_rate: 学习率
            gamma: 折扣因子
        """
        super().__init__(agent_name, device)
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        
        # 训练统计
        self.total_steps = 0
        self.total_episodes = 0
        self.total_updates = 0
    
    def _preprocess_observation(self, observation: np.ndarray) -> torch.Tensor:
        """
        预处理观察
        
        Args:
            observation: numpy数组
        
        Returns:
            torch张量
        """
        if not isinstance(observation, torch.Tensor):
            observation = torch.FloatTensor(observation)
        
        if observation.dim() == 1:
            observation = observation.unsqueeze(0)
        
        return observation.to(self.device)
    
    def _preprocess_action_mask(self, valid_actions: Optional[np.ndarray]) -> Optional[torch.Tensor]:
        """
        预处理动作掩码
        
        Args:
            valid_actions: numpy数组
        
        Returns:
            torch布尔张量
        """
        if valid_actions is None:
            return None
        
        if not isinstance(valid_actions, torch.Tensor):
            valid_actions = torch.BoolTensor(valid_actions)
        
        if valid_actions.dim() == 1:
            valid_actions = valid_actions.unsqueeze(0)
        
        return valid_actions.to(self.device)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'total_steps': self.total_steps,
            'total_episodes': self.total_episodes,
            'total_updates': self.total_updates,
        })
        return stats


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 BaseAgent...")
    
    # 测试1: 基础智能体（会失败，因为是抽象类）
    print("\n测试1: 尝试实例化抽象类")
    try:
        base = BaseAgent()
    except TypeError as e:
        print(f"✅ 预期错误: {e}")
    
    # 测试2: 创建具体子类
    print("\n测试2: 创建具体子类")
    
    class DummyAgent(RLAgent):
        """测试用的简单智能体"""
        
        def select_action(self, observation, valid_actions=None, deterministic=False):
            # 随机选择动作
            action1 = np.random.randint(0, self.action_dim)
            action2 = np.random.randint(0, self.action_dim)
            return action1, action2
        
        def update(self, *args, **kwargs):
            self.total_updates += 1
            return {'loss': 0.5}
        
        def save(self, path):
            print(f"保存到 {path}")
        
        def load(self, path):
            print(f"从 {path} 加载")
    
    # 创建测试智能体
    agent = DummyAgent(
        state_dim=54,
        action_dim=12,
        agent_name="TestAgent",
        learning_rate=3e-4,
        gamma=0.99
    )
    
    print(f"智能体名称: {agent.get_name()}")
    print(f"设备: {agent.device}")
    
    # 测试3: 动作选择
    print("\n测试3: 动作选择")
    obs = np.random.randn(54)
    
    for i in range(3):
        action1, action2 = agent.select_action(obs)
        print(f"  选择 {i+1}: ({action1}, {action2})")
    
    # 测试4: 预处理函数
    print("\n测试4: 预处理函数")
    
    # 预处理观察
    obs_tensor = agent._preprocess_observation(obs)
    print(f"观察形状: {obs_tensor.shape}, 设备: {obs_tensor.device}")
    
    # 预处理动作掩码
    mask = np.array([True] * 12)
    mask_tensor = agent._preprocess_action_mask(mask)
    print(f"掩码形状: {mask_tensor.shape}, 设备: {mask_tensor.device}")
    
    # 测试5: 统计信息
    print("\n测试5: 统计信息")
    agent.total_steps = 1000
    agent.total_episodes = 50
    
    stats = agent.get_stats()
    print("智能体统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试6: 更新
    print("\n测试6: 更新")
    for i in range(3):
        metrics = agent.update()
        print(f"  更新 {i+1}: {metrics}, 总更新次数: {agent.total_updates}")
    
    # 测试7: 保存和加载
    print("\n测试7: 保存和加载")
    agent.save("test_agent.pth")
    agent.load("test_agent.pth")
    
    # 测试8: 训练模式切换
    print("\n测试8: 训练模式")
    agent.set_training_mode(True)
    print("训练模式已启用")
    agent.set_training_mode(False)
    print("评估模式已启用")
    
    # 测试9: 重置
    print("\n测试9: 重置")
    agent.reset()
    print("智能体已重置")
    
    print("\n✅ BaseAgent 测试完成！")