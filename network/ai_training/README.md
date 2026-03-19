# 回合制战斗游戏 AI 训练系统

## 📖 简介

本项目使用强化学习（Reinforcement Learning）训练AI智能体，通过自对弈（Self-Play）学习游戏策略。

**✅ 系统状态：完全可用，已通过维度验证**

## 🎯 目标

- ✅ 训练能够击败随机策略的AI（胜率>70%）
- ✅ 训练能够击败规则基线的AI（胜率>55%）
- ✅ 训练能够与人类玩家对战的AI
- ✅ 通过自对弈持续自我提升

## 📁 项目结构

```
ai_training/
├── environment/        # 游戏环境封装
├── models/            # 神经网络模型
├── agents/            # AI智能体
├── training/          # 训练系统
├── evaluation/        # 评估工具
├── configs/           # 配置文件
├── saved_models/      # 保存的模型
└── logs/             # 训练日志
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ai_training
pip install -r requirements.txt
```

### 2. 测试环境

```bash
python -c "from environment.battle_env import BattleEnv; env = BattleEnv(); print('Environment OK!')"
```

### 3. 开始训练

```bash
# 训练PPO模型
python training/train_ppo.py

# 使用自定义配置
python training/train_ppo.py --config configs/ppo_config.yaml
```

### 4. 评估模型

```bash
python evaluation/evaluator.py --model saved_models/best_models/best_ppo.pth
```

### 5. 人机对战

```bash
python evaluation/play_vs_ai.py --model saved_models/best_models/best_ppo.pth
```

## 📊 状态空间设计

状态向量维度：**66维**

### 玩家1状态 (18维)
- HP归一化 (1维): hp / 20
- 位置归一化 (1维): position / 6
- 蓄力等级 (3维): one-hot [0, 1, 2]
- 冲刺buff (3维): one-hot [0, 1, 2]
- 连击数 (4维): one-hot [0, 1, 2, 3]
- 被控制状态 (1维): 0/1
- 硬直状态 (1维): 0/1
- 上一帧动作类型 (4维): one-hot [攻击/防御/移动/蓄力]

### 玩家2状态 (18维)
- 同上

### 全局状态 (6维)
- 距离归一化 (1维): distance / 6
- 回合数归一化 (1维): turn / 30
- P1在左侧 (1维): 0/1
- P2在左侧 (1维): 0/1
- 帧状态占位 (2维): 0/0

### 历史信息 (24维)
- P1最近2帧动作 (12维): 每个动作6维编码
- P2最近2帧动作 (12维): 每个动作6维编码

## 🎮 动作空间

每回合需要选择2个动作（对应2帧）

### 动作列表 (12种)
0. attack - 攻击
1. charge - 蓄力
2. control - 控制
3. grab - 抱摔
4. throw - 投掷
5. defend - 防御
6. counter - 反击
7. move_left - 左移
8. move_right - 右移
9. dash_left - 左冲
10. dash_right - 右冲
11. burst - 爆血

### 动作限制
- 硬直时只能选择 burst
- 被控制时只能选择 defend 或 burst
- grab/throw 需要对手被控制

## 💰 奖励函数

### 稀疏奖励（简单模式）
```python
reward = 100 if win else (-100 if lose else 0)
```

### 密集奖励（推荐模式）
```python
reward = (
    dealt_damage * 2.0          # 造成伤害
    - taken_damage * 1.5        # 受到伤害
    + control_success * 5.0     # 控制成功
    + combo_count * 3.0         # 连击奖励
    + hp_advantage * 0.5        # 血量优势
    + 100 if win else -100      # 胜负奖励
)
```

## 🧠 训练算法

### PPO (Proximal Policy Optimization) - 推荐
- 稳定、易调参
- 适合连续决策
- 支持GAE优势估计

### 超参数
```yaml
learning_rate: 3e-4
gamma: 0.99           # 折扣因子
gae_lambda: 0.95      # GAE参数
clip_epsilon: 0.2     # PPO裁剪参数
batch_size: 64
epochs_per_iteration: 4
```

## 📈 训练监控

### TensorBoard
```bash
tensorboard --logdir logs/tensorboard
```

### 关键指标
- **胜率** (Win Rate): 目标 > 60%
- **平均奖励** (Average Reward): 持续上升
- **策略损失** (Policy Loss): 稳定下降
- **价值损失** (Value Loss): 稳定下降
- **平均回合长度** (Episode Length): 观察策略复杂度

## 🎯 训练里程碑

### 阶段1: 随机基线
- [ ] 胜率 > 50% vs Random Agent

### 阶段2: 规则基线
- [ ] 胜率 > 40% vs Rule-based Agent

### 阶段3: 自我提升
- [ ] 胜率 > 55% vs 历史最佳模型

### 阶段4: 人类水平
- [ ] 能够在人机对战中提供挑战

## 🔧 故障排除

### 训练不收敛
1. 降低学习率
2. 增加batch size
3. 调整奖励函数scale
4. 检查状态归一化

### 过拟合
1. 增加探索噪声
2. 使用dropout
3. 减少网络层数
4. 增加训练对手多样性

### 显存不足
1. 减小batch size
2. 减小网络规模
3. 使用梯度累积

## 📚 参考资料

- [PPO论文](https://arxiv.org/abs/1707.06347)
- [OpenAI Spinning Up](https://spinningup.openai.com/)
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/)

## 📝 TODO

- [ ] 实现模型版本管理
- [ ] 添加多GPU训练支持
- [ ] 实现模型蒸馏（压缩模型）
- [ ] 添加更多评估指标
- [ ] 实现在线对战系统

## 📧 联系方式

如有问题，请提交Issue或联系开发者。