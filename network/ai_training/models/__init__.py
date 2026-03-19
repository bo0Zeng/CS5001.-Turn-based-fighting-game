"""
models package
神经网络模型模块 / Neural Network Models Package

导出主要类和函数供外部使用
"""

from .policy_network import PolicyNetwork, RecurrentPolicyNetwork
from .value_network import ValueNetwork, DuelingNetwork, RecurrentValueNetwork
from .actor_critic import ActorCritic, SharedActorCritic
from .model_utils import (
    save_model,
    load_model,
    count_parameters,
    get_parameter_stats,
    print_model_summary,
    clip_gradient,
    freeze_model,
    unfreeze_model,
    copy_model_params,
    soft_update_model_params,
    initialize_weights,
    get_model_device,
    move_to_device,
    get_model_size_mb,
)

__all__ = [
    # 策略网络
    'PolicyNetwork',
    'RecurrentPolicyNetwork',
    
    # 价值网络
    'ValueNetwork',
    'DuelingNetwork',
    'RecurrentValueNetwork',
    
    # Actor-Critic架构
    'ActorCritic',
    'SharedActorCritic',
    
    # 工具函数
    'save_model',
    'load_model',
    'count_parameters',
    'get_parameter_stats',
    'print_model_summary',
    'clip_gradient',
    'freeze_model',
    'unfreeze_model',
    'copy_model_params',
    'soft_update_model_params',
    'initialize_weights',
    'get_model_device',
    'move_to_device',
    'get_model_size_mb',
]