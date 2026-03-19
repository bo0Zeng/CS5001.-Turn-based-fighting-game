"""
environment package
游戏环境封装模块 / Game Environment Package

导出主要类和函数供外部使用
"""

from .battle_env import BattleEnv
from .state_encoder import StateEncoder, normalize_value, one_hot_encode
from .action_space import ActionSpace, convert_actions_to_names, convert_names_to_actions
from .reward_shaper import RewardShaper, create_reward_shaper, REWARD_CONFIGS

__all__ = [
    # 主要类
    'BattleEnv',
    'StateEncoder',
    'ActionSpace',
    'RewardShaper',
    
    # 工具函数
    'normalize_value',
    'one_hot_encode',
    'convert_actions_to_names',
    'convert_names_to_actions',
    'create_reward_shaper',
    
    # 配置
    'REWARD_CONFIGS',
]