"""
hyperparameters.py
超参数配置 / Hyperparameters Configuration

定义默认配置和加载配置文件的函数
"""

import yaml
from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    config = {
        # 环境配置
        'environment': {
            'reward_type': 'dense',  # 'dense' or 'sparse'
            'max_turns': 30,
            'verbose': False,
        },
        
        # 智能体配置
        'agent': {
            'hidden_sizes': [256, 128],
            'learning_rate': 3e-4,
            'gamma': 0.99,
            'gae_lambda': 0.95,
            'clip_epsilon': 0.2,
            'value_coef': 0.5,
            'entropy_coef': 0.01,
            'max_grad_norm': 0.5,
        },
        
        # 训练配置
        'training': {
            'num_iterations': 1000,
            'episodes_per_iteration': 100,
            'update_epochs': 4,
            'batch_size': 64,
            'log_interval': 10,
            'save_interval': 50,
            'eval_interval': 20,
            'eval_episodes': 10,
        },
    }
    
    return config


def get_fast_config() -> Dict[str, Any]:
    """
    快速测试配置（小规模）
    
    Returns:
        快速配置字典
    """
    config = get_default_config()
    
    # 减少训练规模
    config['training']['num_iterations'] = 100
    config['training']['episodes_per_iteration'] = 20
    config['training']['update_epochs'] = 2
    config['training']['batch_size'] = 32
    config['training']['log_interval'] = 5
    config['training']['save_interval'] = 20
    config['training']['eval_interval'] = 10
    
    return config


def get_large_config() -> Dict[str, Any]:
    """
    大规模训练配置
    
    Returns:
        大规模配置字典
    """
    config = get_default_config()
    
    # 增加训练规模
    config['agent']['hidden_sizes'] = [512, 256, 128]
    config['training']['num_iterations'] = 5000
    config['training']['episodes_per_iteration'] = 200
    config['training']['update_epochs'] = 8
    config['training']['batch_size'] = 128
    
    return config


def get_aggressive_config() -> Dict[str, Any]:
    """
    激进策略配置（高熵，探索性强）
    
    Returns:
        激进配置字典
    """
    config = get_default_config()
    
    # 增加探索
    config['agent']['entropy_coef'] = 0.05  # 更高的熵系数
    config['agent']['clip_epsilon'] = 0.3   # 更大的裁剪范围
    config['agent']['learning_rate'] = 5e-4  # 更快的学习率
    
    return config


def get_conservative_config() -> Dict[str, Any]:
    """
    保守策略配置（低熵，稳定性强）
    
    Returns:
        保守配置字典
    """
    config = get_default_config()
    
    # 减少探索
    config['agent']['entropy_coef'] = 0.001  # 更低的熵系数
    config['agent']['clip_epsilon'] = 0.1    # 更小的裁剪范围
    config['agent']['learning_rate'] = 1e-4  # 更慢的学习率
    config['agent']['gamma'] = 0.995         # 更关注长期奖励
    
    return config


def load_config(config_path: str) -> Dict[str, Any]:
    """
    从YAML文件加载配置
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 与默认配置合并（填充缺失的键）
    default_config = get_default_config()
    merged_config = _merge_configs(default_config, config)
    
    return merged_config


def save_config(config: Dict[str, Any], save_path: str):
    """
    保存配置到YAML文件
    
    Args:
        config: 配置字典
        save_path: 保存路径
    """
    with open(save_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ 配置已保存到: {save_path}")


def _merge_configs(default: Dict, custom: Dict) -> Dict:
    """
    递归合并配置（custom覆盖default）
    
    Args:
        default: 默认配置
        custom: 自定义配置
    
    Returns:
        合并后的配置
    """
    result = default.copy()
    
    for key, value in custom.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def print_config(config: Dict[str, Any], indent: int = 0):
    """
    打印配置（格式化）
    
    Args:
        config: 配置字典
        indent: 缩进级别
    """
    for key, value in config.items():
        if isinstance(value, dict):
            print("  " * indent + f"{key}:")
            print_config(value, indent + 1)
        else:
            print("  " * indent + f"{key}: {value}")


# 预定义配置集合
PRESET_CONFIGS = {
    'default': get_default_config,
    'fast': get_fast_config,
    'large': get_large_config,
    'aggressive': get_aggressive_config,
    'conservative': get_conservative_config,
}


def get_preset_config(name: str) -> Dict[str, Any]:
    """
    获取预设配置
    
    Args:
        name: 预设名称 ('default', 'fast', 'large', 'aggressive', 'conservative')
    
    Returns:
        配置字典
    """
    if name not in PRESET_CONFIGS:
        raise ValueError(f"未知的预设配置: {name}. 可用: {list(PRESET_CONFIGS.keys())}")
    
    return PRESET_CONFIGS[name]()


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 Hyperparameters...")
    
    # 测试1: 默认配置
    print("\n测试1: 默认配置")
    default_config = get_default_config()
    print("默认配置:")
    print_config(default_config)
    
    # 测试2: 快速配置
    print("\n测试2: 快速配置")
    fast_config = get_fast_config()
    print("快速配置的训练参数:")
    print_config(fast_config['training'])
    
    # 测试3: 激进配置
    print("\n测试3: 激进配置")
    aggressive_config = get_aggressive_config()
    print("激进配置的智能体参数:")
    print_config(aggressive_config['agent'])
    
    # 测试4: 保守配置
    print("\n测试4: 保守配置")
    conservative_config = get_conservative_config()
    print("保守配置的智能体参数:")
    print_config(conservative_config['agent'])
    
    # 测试5: 保存和加载配置
    print("\n测试5: 保存和加载配置")
    test_config_path = "test_config.yaml"
    
    save_config(default_config, test_config_path)
    loaded_config = load_config(test_config_path)
    
    print("加载的配置与原配置一致:", default_config == loaded_config)
    
    # 清理测试文件
    import os
    if os.path.exists(test_config_path):
        os.remove(test_config_path)
        print(f"已删除测试文件: {test_config_path}")
    
    # 测试6: 配置合并
    print("\n测试6: 配置合并")
    custom_config = {
        'agent': {
            'learning_rate': 1e-3,  # 修改学习率
        },
        'training': {
            'batch_size': 128,  # 修改批大小
        }
    }
    
    merged = _merge_configs(default_config, custom_config)
    print("合并后的学习率:", merged['agent']['learning_rate'])
    print("合并后的批大小:", merged['training']['batch_size'])
    print("未修改的gamma:", merged['agent']['gamma'])
    
    # 测试7: 获取所有预设
    print("\n测试7: 所有预设配置")
    print("可用预设:", list(PRESET_CONFIGS.keys()))
    
    for name in PRESET_CONFIGS.keys():
        config = get_preset_config(name)
        print(f"\n{name} 配置:")
        print(f"  迭代次数: {config['training']['num_iterations']}")
        print(f"  学习率: {config['agent']['learning_rate']}")
        print(f"  熵系数: {config['agent']['entropy_coef']}")
    
    print("\n✅ Hyperparameters 测试完成！")