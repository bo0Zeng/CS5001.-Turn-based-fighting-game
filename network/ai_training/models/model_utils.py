"""
model_utils.py
模型工具函数 / Model Utility Functions

提供：
- 模型保存/加载
- 模型参数统计
- 梯度裁剪
- 模型初始化
- 模型复制
"""

import torch
import torch.nn as nn
from typing import Dict, Any, Optional
import os
from pathlib import Path


def save_model(model: nn.Module, 
               path: str, 
               optimizer: Optional[torch.optim.Optimizer] = None,
               epoch: Optional[int] = None,
               metadata: Optional[Dict[str, Any]] = None):
    """
    保存模型
    
    Args:
        model: PyTorch模型
        path: 保存路径
        optimizer: 优化器（可选）
        epoch: 训练轮次（可选）
        metadata: 额外元数据（可选）
    """
    # 确保目录存在
    save_dir = os.path.dirname(path)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    
    # 构建保存字典
    checkpoint = {
        'model_state_dict': model.state_dict(),
    }
    
    if optimizer is not None:
        checkpoint['optimizer_state_dict'] = optimizer.state_dict()
    
    if epoch is not None:
        checkpoint['epoch'] = epoch
    
    if metadata is not None:
        checkpoint['metadata'] = metadata
    
    # 保存
    torch.save(checkpoint, path)
    print(f"✅ 模型已保存到: {path}")


def load_model(model: nn.Module,
               path: str,
               optimizer: Optional[torch.optim.Optimizer] = None,
               device: Optional[torch.device] = None,
               strict: bool = True) -> Dict[str, Any]:
    """
    加载模型
    
    Args:
        model: PyTorch模型
        path: 加载路径
        optimizer: 优化器（可选）
        device: 设备（可选）
        strict: 是否严格匹配参数
    
    Returns:
        checkpoint字典
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"模型文件不存在: {path}")
    
    # 加载checkpoint
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    checkpoint = torch.load(path, map_location=device)
    
    # 加载模型参数
    model.load_state_dict(checkpoint['model_state_dict'], strict=strict)
    
    # 加载优化器参数
    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    print(f"✅ 模型已从 {path} 加载")
    
    return checkpoint


def count_parameters(model: nn.Module, trainable_only: bool = False) -> int:
    """
    统计模型参数数量
    
    Args:
        model: PyTorch模型
        trainable_only: 是否只统计可训练参数
    
    Returns:
        参数数量
    """
    if trainable_only:
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    else:
        return sum(p.numel() for p in model.parameters())


def get_parameter_stats(model: nn.Module) -> Dict[str, Any]:
    """
    获取模型参数统计信息
    
    Args:
        model: PyTorch模型
    
    Returns:
        统计信息字典
    """
    total_params = count_parameters(model, trainable_only=False)
    trainable_params = count_parameters(model, trainable_only=True)
    
    # 按层统计
    layer_params = {}
    for name, module in model.named_children():
        layer_params[name] = count_parameters(module)
    
    stats = {
        'total_parameters': total_params,
        'trainable_parameters': trainable_params,
        'non_trainable_parameters': total_params - trainable_params,
        'layer_parameters': layer_params,
    }
    
    return stats


def print_model_summary(model: nn.Module):
    """
    打印模型摘要
    
    Args:
        model: PyTorch模型
    """
    print("=" * 60)
    print("模型摘要 / Model Summary")
    print("=" * 60)
    
    stats = get_parameter_stats(model)
    
    print(f"总参数量: {stats['total_parameters']:,}")
    print(f"可训练参数: {stats['trainable_parameters']:,}")
    print(f"不可训练参数: {stats['non_trainable_parameters']:,}")
    
    if stats['layer_parameters']:
        print("\n各层参数量:")
        for name, params in stats['layer_parameters'].items():
            print(f"  {name}: {params:,}")
    
    print("=" * 60)


def clip_gradient(model: nn.Module, max_norm: float = 1.0) -> float:
    """
    梯度裁剪
    
    Args:
        model: PyTorch模型
        max_norm: 最大梯度范数
    
    Returns:
        裁剪前的总梯度范数
    """
    total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm)
    return total_norm.item()


def freeze_model(model: nn.Module):
    """
    冻结模型（不更新参数）
    
    Args:
        model: PyTorch模型
    """
    for param in model.parameters():
        param.requires_grad = False
    print("✅ 模型已冻结")


def unfreeze_model(model: nn.Module):
    """
    解冻模型（允许更新参数）
    
    Args:
        model: PyTorch模型
    """
    for param in model.parameters():
        param.requires_grad = True
    print("✅ 模型已解冻")


def copy_model_params(source_model: nn.Module, target_model: nn.Module):
    """
    复制模型参数（用于目标网络更新等）
    
    Args:
        source_model: 源模型
        target_model: 目标模型
    """
    target_model.load_state_dict(source_model.state_dict())


def soft_update_model_params(source_model: nn.Module, 
                             target_model: nn.Module, 
                             tau: float = 0.005):
    """
    软更新模型参数（Polyak averaging）
    
    target = tau * source + (1 - tau) * target
    
    Args:
        source_model: 源模型
        target_model: 目标模型
        tau: 更新系数（0-1之间）
    """
    for target_param, source_param in zip(target_model.parameters(), source_model.parameters()):
        target_param.data.copy_(
            tau * source_param.data + (1.0 - tau) * target_param.data
        )


def initialize_weights(module: nn.Module, init_type: str = 'orthogonal'):
    """
    初始化模型权重
    
    Args:
        module: PyTorch模块
        init_type: 初始化类型 ('orthogonal', 'xavier', 'kaiming')
    """
    if isinstance(module, (nn.Linear, nn.Conv2d)):
        if init_type == 'orthogonal':
            nn.init.orthogonal_(module.weight)
        elif init_type == 'xavier':
            nn.init.xavier_uniform_(module.weight)
        elif init_type == 'kaiming':
            nn.init.kaiming_uniform_(module.weight, nonlinearity='relu')
        
        if module.bias is not None:
            nn.init.constant_(module.bias, 0.0)


def get_model_device(model: nn.Module) -> torch.device:
    """
    获取模型所在设备
    
    Args:
        model: PyTorch模型
    
    Returns:
        设备
    """
    return next(model.parameters()).device


def move_to_device(obj, device: torch.device):
    """
    将对象移动到指定设备
    
    支持Tensor, list, tuple, dict
    
    Args:
        obj: 对象
        device: 目标设备
    
    Returns:
        移动后的对象
    """
    if isinstance(obj, torch.Tensor):
        return obj.to(device)
    elif isinstance(obj, list):
        return [move_to_device(item, device) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(move_to_device(item, device) for item in obj)
    elif isinstance(obj, dict):
        return {key: move_to_device(value, device) for key, value in obj.items()}
    else:
        return obj


def get_model_size_mb(model: nn.Module) -> float:
    """
    获取模型大小（MB）
    
    Args:
        model: PyTorch模型
    
    Returns:
        模型大小（MB）
    """
    param_size = 0
    buffer_size = 0
    
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()
    
    for buffer in model.buffers():
        buffer_size += buffer.nelement() * buffer.element_size()
    
    size_all_mb = (param_size + buffer_size) / 1024 / 1024
    return size_all_mb


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 model_utils...")
    
    # 创建测试模型
    from actor_critic import ActorCritic
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ActorCritic(state_dim=54, action_dim=12).to(device)
    
    # 测试1: 参数统计
    print("\n测试1: 参数统计")
    print_model_summary(model)
    
    stats = get_parameter_stats(model)
    print(f"\n可训练参数占比: {stats['trainable_parameters'] / stats['total_parameters'] * 100:.2f}%")
    
    # 测试2: 模型大小
    print("\n测试2: 模型大小")
    size_mb = get_model_size_mb(model)
    print(f"模型大小: {size_mb:.2f} MB")
    
    # 测试3: 保存和加载
    print("\n测试3: 保存和加载")
    save_path = "test_model.pth"
    
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    metadata = {
        'epoch': 100,
        'win_rate': 0.65,
        'avg_reward': 50.0
    }
    
    save_model(model, save_path, optimizer, epoch=100, metadata=metadata)
    
    # 创建新模型并加载
    new_model = ActorCritic(state_dim=54, action_dim=12).to(device)
    new_optimizer = torch.optim.Adam(new_model.parameters(), lr=3e-4)
    
    checkpoint = load_model(new_model, save_path, new_optimizer, device)
    
    print(f"加载的元数据: {checkpoint.get('metadata')}")
    
    # 清理测试文件
    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"已删除测试文件: {save_path}")
    
    # 测试4: 梯度裁剪
    print("\n测试4: 梯度裁剪")
    
    # 创造一些梯度
    state = torch.randn(4, 54).to(device)
    actions, log_probs, values = model.get_action_and_value(state)
    loss = -log_probs.mean() + values.mean()
    
    model.zero_grad()
    loss.backward()
    
    # 裁剪前的梯度范数
    grad_norm_before = sum(p.grad.norm().item() ** 2 for p in model.parameters() if p.grad is not None) ** 0.5
    print(f"裁剪前梯度范数: {grad_norm_before:.4f}")
    
    # 梯度裁剪
    clipped_norm = clip_gradient(model, max_norm=1.0)
    print(f"裁剪后返回的范数: {clipped_norm:.4f}")
    
    grad_norm_after = sum(p.grad.norm().item() ** 2 for p in model.parameters() if p.grad is not None) ** 0.5
    print(f"裁剪后实际范数: {grad_norm_after:.4f}")
    
    # 测试5: 冻结/解冻
    print("\n测试5: 冻结/解冻模型")
    
    trainable_before = count_parameters(model, trainable_only=True)
    print(f"冻结前可训练参数: {trainable_before:,}")
    
    freeze_model(model)
    trainable_frozen = count_parameters(model, trainable_only=True)
    print(f"冻结后可训练参数: {trainable_frozen:,}")
    
    unfreeze_model(model)
    trainable_unfrozen = count_parameters(model, trainable_only=True)
    print(f"解冻后可训练参数: {trainable_unfrozen:,}")
    
    # 测试6: 模型参数复制
    print("\n测试6: 模型参数复制")
    
    source_model = ActorCritic(state_dim=54, action_dim=12).to(device)
    target_model = ActorCritic(state_dim=54, action_dim=12).to(device)
    
    # 初始状态不同
    test_input = torch.randn(1, 54).to(device)
    source_output = source_model(test_input)
    target_output = target_model(test_input)
    
    diff_before = (source_output[0] - target_output[0]).abs().sum().item()
    print(f"复制前输出差异: {diff_before:.6f}")
    
    # 复制参数
    copy_model_params(source_model, target_model)
    
    target_output_after = target_model(test_input)
    diff_after = (source_output[0] - target_output_after[0]).abs().sum().item()
    print(f"复制后输出差异: {diff_after:.6f}")
    
    # 测试7: 软更新
    print("\n测试7: 软更新")
    
    # 重新初始化目标模型
    target_model = ActorCritic(state_dim=54, action_dim=12).to(device)
    
    # 获取某个参数的初始值
    source_param = list(source_model.parameters())[0].data.clone()
    target_param = list(target_model.parameters())[0].data.clone()
    
    print(f"软更新前 - 源参数均值: {source_param.mean().item():.6f}")
    print(f"软更新前 - 目标参数均值: {target_param.mean().item():.6f}")
    
    # 软更新（tau=0.1）
    soft_update_model_params(source_model, target_model, tau=0.1)
    
    target_param_after = list(target_model.parameters())[0].data
    print(f"软更新后 - 目标参数均值: {target_param_after.mean().item():.6f}")
    
    # 验证公式：target = 0.1 * source + 0.9 * target
    expected = 0.1 * source_param + 0.9 * target_param
    diff = (expected - target_param_after).abs().sum().item()
    print(f"软更新公式验证差异: {diff:.10f} (应该接近0)")
    
    # 测试8: 设备相关
    print("\n测试8: 设备相关")
    
    model_device = get_model_device(model)
    print(f"模型所在设备: {model_device}")
    
    # 测试move_to_device
    test_data = {
        'tensor': torch.randn(2, 3),
        'list': [torch.randn(2), torch.randn(3)],
        'nested': {
            'a': torch.randn(1),
            'b': [torch.randn(2), torch.randn(3)]
        }
    }
    
    moved_data = move_to_device(test_data, device)
    print(f"数据已移动到: {moved_data['tensor'].device}")
    
    print("\n✅ model_utils 测试完成！")