"""
check_project.py
项目完整性检查 / Project Integrity Check

检查所有必需的文件是否存在
"""

import os
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """检查文件是否存在"""
    exists = os.path.exists(file_path)
    status = "✅" if exists else "❌"
    print(f"{status} {description:50s} {file_path}")
    return exists


def check_project_structure():
    """检查项目结构"""
    print("="*80)
    print("🔍 检查AI训练系统项目结构")
    print("="*80)
    
    all_good = True
    
    # 核心文档
    print("\n📄 核心文档:")
    all_good &= check_file_exists("README.md", "主README")
    all_good &= check_file_exists("QUICKSTART.md", "快速入门指南")
    all_good &= check_file_exists("PROJECT_STATUS.md", "项目状态")
    all_good &= check_file_exists("requirements.txt", "依赖列表")
    
    # 环境模块
    print("\n🌍 环境模块 (environment/):")
    all_good &= check_file_exists("environment/__init__.py", "__init__")
    all_good &= check_file_exists("environment/battle_env.py", "游戏环境")
    all_good &= check_file_exists("environment/state_encoder.py", "状态编码器")
    all_good &= check_file_exists("environment/action_space.py", "动作空间")
    all_good &= check_file_exists("environment/reward_shaper.py", "奖励函数")
    
    # 模型模块
    print("\n🧠 模型模块 (models/):")
    all_good &= check_file_exists("models/__init__.py", "__init__")
    all_good &= check_file_exists("models/policy_network.py", "策略网络")
    all_good &= check_file_exists("models/value_network.py", "价值网络")
    all_good &= check_file_exists("models/actor_critic.py", "Actor-Critic")
    all_good &= check_file_exists("models/model_utils.py", "模型工具")
    
    # 智能体模块
    print("\n🤖 智能体模块 (agents/):")
    all_good &= check_file_exists("agents/__init__.py", "__init__")
    all_good &= check_file_exists("agents/base_agent.py", "基础智能体")
    all_good &= check_file_exists("agents/ppo_agent.py", "PPO智能体")
    all_good &= check_file_exists("agents/random_agent.py", "随机基线")
    all_good &= check_file_exists("agents/rule_based_agent.py", "规则基线")
    
    # 训练模块
    print("\n🎓 训练模块 (training/):")
    all_good &= check_file_exists("training/__init__.py", "__init__")
    all_good &= check_file_exists("training/replay_buffer.py", "经验回放")
    all_good &= check_file_exists("training/selfplay_trainer.py", "训练器")
    all_good &= check_file_exists("training/train_ppo.py", "训练脚本")
    all_good &= check_file_exists("training/hyperparameters.py", "超参数")
    
    # 评估模块
    print("\n📊 评估模块 (evaluation/):")
    all_good &= check_file_exists("evaluation/__init__.py", "__init__")
    all_good &= check_file_exists("evaluation/evaluator.py", "评估器")
    all_good &= check_file_exists("evaluation/visualize.py", "可视化")
    all_good &= check_file_exists("evaluation/play_vs_ai.py", "人机对战")
    
    # 配置文件
    print("\n⚙️ 配置文件 (configs/):")
    check_file_exists("configs/ppo_config.yaml", "PPO配置")
    check_file_exists("configs/fast_test.yaml", "快速测试配置")
    
    # 脚本文件
    print("\n🔧 辅助脚本:")
    all_good &= check_file_exists("quick_train.py", "快速训练")
    all_good &= check_file_exists("test_full_system.py", "系统测试")
    all_good &= check_file_exists("verify_dimensions.py", "维度验证")
    all_good &= check_file_exists("train_and_evaluate.py", "完整流程")
    all_good &= check_file_exists("check_project.py", "项目检查")
    
    # 汇总
    print("\n" + "="*80)
    if all_good:
        print("✅ 所有必需文件都存在！项目结构完整！")
        print("\n🚀 可以开始使用系统！")
        print("\n推荐命令:")
        print("  1. python verify_dimensions.py     # 验证维度")
        print("  2. python test_full_system.py      # 系统测试")
        print("  3. python quick_train.py           # 快速训练")
        print("  4. python train_and_evaluate.py    # 完整流程")
    else:
        print("⚠️ 部分文件缺失，请检查项目结构")
    print("="*80)
    
    return all_good


def show_project_stats():
    """显示项目统计"""
    print("\n" + "="*80)
    print("📊 项目统计")
    print("="*80)
    
    # 统计代码行数
    total_lines = 0
    file_count = 0
    
    for root, dirs, files in os.walk('.'):
        # 跳过特殊目录
        if any(skip in root for skip in ['__pycache__', '.git', 'saved_models', 'logs']):
            continue
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                        file_count += 1
                except:
                    pass
    
    print(f"Python文件数量: {file_count}")
    print(f"代码总行数: {total_lines:,}")
    print(f"平均每文件: {total_lines // file_count if file_count > 0 else 0} 行")
    
    # 模块统计
    modules = {
        'environment': 4,
        'models': 4,
        'agents': 4,
        'training': 4,
        'evaluation': 3,
    }
    
    print(f"\n模块数量: {len(modules)}")
    for module, count in modules.items():
        print(f"  {module}: {count} 个文件")
    
    print("="*80)


if __name__ == "__main__":
    # 检查项目结构
    all_good = check_project_structure()
    
    # 显示统计
    if all_good:
        show_project_stats()