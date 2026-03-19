"""
test_full_system.py
完整系统测试 / Full System Test

测试整个AI训练系统是否能正常工作
"""

import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_training_dir = current_dir
project_root = os.path.dirname(ai_training_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, ai_training_dir)

import torch
import numpy as np


def test_imports():
    """测试所有模块是否能正常导入"""
    print("\n" + "="*60)
    print("测试1: 模块导入")
    print("="*60)
    
    try:
        from environment import BattleEnv, StateEncoder, ActionSpace, RewardShaper
        print("✅ environment 模块导入成功")
        
        from models import PolicyNetwork, ValueNetwork, ActorCritic
        print("✅ models 模块导入成功")
        
        from agents import PPOAgent, RandomAgent, RuleBasedAgent
        print("✅ agents 模块导入成功")
        
        from training import SelfPlayTrainer, ReplayBuffer, get_default_config
        print("✅ training 模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_environment():
    """测试环境"""
    print("\n" + "="*60)
    print("测试2: 环境功能")
    print("="*60)
    
    try:
        from environment import BattleEnv
        
        env = BattleEnv(reward_type='dense', verbose=False)
        obs = env.reset()
        
        print(f"✅ 环境创建成功")
        print(f"  观察维度: {obs.shape}")
        
        # 运行一个episode
        done = False
        steps = 0
        while not done and steps < 30:
            p1_actions = (np.random.randint(0, 12), np.random.randint(0, 12))
            p2_actions = (np.random.randint(0, 12), np.random.randint(0, 12))
            
            obs, p1_reward, p2_reward, done, info = env.step(p1_actions, p2_actions)
            steps += 1
        
        print(f"✅ Episode完成: {steps}步, 胜者: {info.get('winner')}")
        return True
        
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agents():
    """测试智能体"""
    print("\n" + "="*60)
    print("测试3: 智能体功能")
    print("="*60)
    
    try:
        from agents import PPOAgent, RandomAgent, RuleBasedAgent
        
        # 测试PPO智能体
        device = torch.device('cpu')
        ppo = PPOAgent(state_dim=66, action_dim=12, device=device)
        print(f"✅ PPOAgent创建成功")
        
        obs = np.random.randn(66)  # 更新为66维
        action1, action2 = ppo.select_action(obs)
        print(f"  PPO选择动作: ({action1}, {action2})")
        
        # 测试随机智能体
        random_agent = RandomAgent(action_dim=12)
        print(f"✅ RandomAgent创建成功")
        
        action1, action2 = random_agent.select_action(obs)
        print(f"  Random选择动作: ({action1}, {action2})")
        
        # 测试规则智能体
        rule_agent = RuleBasedAgent(action_dim=12)
        print(f"✅ RuleBasedAgent创建成功")
        
        action1, action2 = rule_agent.select_action(obs)
        print(f"  Rule选择动作: ({action1}, {action2})")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能体测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_training_loop():
    """测试训练循环"""
    print("\n" + "="*60)
    print("测试4: 训练循环（迷你版）")
    print("="*60)
    
    try:
        from environment import BattleEnv
        from agents import PPOAgent, RandomAgent
        from training import SelfPlayTrainer
        
        # 创建环境和智能体
        env = BattleEnv(reward_type='dense', verbose=False)
        agent = PPOAgent(state_dim=66, action_dim=12, device=torch.device('cpu'))
        opponent = RandomAgent(action_dim=12)
        
        # 创建训练器
        trainer = SelfPlayTrainer(
            env=env,
            agent=agent,
            opponent=opponent,
            save_dir="test_training",
            log_interval=1
        )
        
        print(f"✅ 训练器创建成功")
        
        # 运行短期训练
        print(f"\n开始迷你训练（3次迭代，每次5个episodes）...")
        history = trainer.train(
            num_iterations=3,
            episodes_per_iteration=5,
            update_epochs=2,
            batch_size=16
        )
        
        print(f"\n✅ 训练循环完成")
        print(f"  迭代次数: {len(history['iteration'])}")
        print(f"  最终胜率: {history['agent_wins'][-1]:.1f}%")
        
        # 清理
        import shutil
        if os.path.exists("test_training"):
            shutil.rmtree("test_training")
            print(f"🗑️  已清理测试文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 训练循环测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_save_load():
    """测试模型保存和加载"""
    print("\n" + "="*60)
    print("测试5: 模型保存/加载")
    print("="*60)
    
    try:
        from agents import PPOAgent
        
        # 创建智能体
        agent = PPOAgent(state_dim=66, action_dim=12)
        
        # 修改一些统计数据
        agent.total_steps = 1000
        agent.total_episodes = 50
        
        # 保存
        save_path = "test_save_load.pth"
        agent.save(save_path)
        print(f"✅ 模型保存成功: {save_path}")
        
        # 创建新智能体并加载
        new_agent = PPOAgent(state_dim=66, action_dim=12)
        new_agent.load(save_path)
        print(f"✅ 模型加载成功")
        
        # 验证统计数据
        print(f"  加载后 total_steps: {new_agent.total_steps}")
        print(f"  加载后 total_episodes: {new_agent.total_episodes}")
        
        # 清理
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"🗑️  已清理测试文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存/加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪 "*20)
    print("开始完整系统测试 / Starting Full System Test")
    print("🧪 "*20 + "\n")
    
    results = []
    
    # 测试1: 导入
    results.append(("模块导入", test_imports()))
    
    # 测试2: 环境
    results.append(("环境功能", test_environment()))
    
    # 测试3: 智能体
    results.append(("智能体功能", test_agents()))
    
    # 测试4: 训练循环
    results.append(("训练循环", test_training_loop()))
    
    # 测试5: 保存/加载
    results.append(("模型保存/加载", test_model_save_load()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试汇总 / Test Summary")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 所有测试通过！系统可以正常使用！")
        print("\n💡 下一步:")
        print("  1. 运行快速训练: python quick_train.py")
        print("  2. 运行完整训练: python training/train_ppo.py")
        print("  3. 自定义配置: python training/train_ppo.py --config configs/ppo_config.yaml")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()