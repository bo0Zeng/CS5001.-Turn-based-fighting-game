# 🚀 快速入门指南

## 📦 安装依赖

```bash
cd ai_training
pip install -r requirements.txt
```

## 🧪 测试系统

运行完整系统测试，确保所有模块正常工作：

```bash
python test_full_system.py
```

**期望输出：**
```
🧪 开始完整系统测试
...
📊 测试汇总
模块导入            : ✅ 通过
环境功能            : ✅ 通过
智能体功能          : ✅ 通过
训练循环            : ✅ 通过
模型保存/加载       : ✅ 通过
🎉 所有测试通过！系统可以正常使用！
```

## 🎯 开始训练

### 方式1: 一键快速训练（推荐新手）

```bash
python quick_train.py
```

这将使用快速配置训练50次迭代，大约需要10-20分钟。

### 方式2: 使用配置文件训练

```bash
# 使用默认PPO配置
python training/train_ppo.py

# 使用快速测试配置
python training/train_ppo.py --config configs/fast_test.yaml

# 使用自定义配置
python training/train_ppo.py --config configs/ppo_config.yaml
```

### 方式3: 自定义参数训练

```bash
# 对抗随机智能体，训练100次迭代
python training/train_ppo.py --opponent random --iterations 100

# 对抗规则智能体，训练500次迭代
python training/train_ppo.py --opponent rule --iterations 500

# 自我对弈，训练1000次迭代
python training/train_ppo.py --opponent self --iterations 1000
```

## 📊 训练监控

### 查看训练日志

训练过程中会实时显示：
- 胜率（Win Rate）
- 平均奖励（Average Reward）
- 策略损失（Policy Loss）
- 价值损失（Value Loss）
- 熵（Entropy）

### 训练输出示例

```
迭代 10/1000
收集 100 个episodes...
Episodes: 100%|████████████| 100/100

📈 迭代 10 统计:
  胜/负/平: 55/40/5
  胜率: 55.0%
  平均奖励: 12.34
  平均长度: 8.5
  策略损失: 0.0234
  价值损失: 0.1456
  熵: 2.3456

📊 评估结果:
  胜率 vs 对手: 58.0%
  平均奖励: 15.23

💾 模型已保存: saved_models/ppo/run_20250101_120000/checkpoint_iter_50.pth
```

## 💾 模型文件

训练完成后，模型保存在：

```
saved_models/ppo/run_YYYYMMDD_HHMMSS/
├── checkpoint_iter_50.pth      # 迭代50的检查点
├── checkpoint_iter_100.pth     # 迭代100的检查点
├── final_model.pth             # 最终模型
└── training_history.json       # 训练历史
```

## 🎮 使用训练好的模型

### 加载模型

```python
from agents import PPOAgent

# 创建智能体
agent = PPOAgent(state_dim=54, action_dim=12)

# 加载训练好的模型
agent.load("saved_models/ppo/run_YYYYMMDD_HHMMSS/final_model.pth")

# 设置为评估模式
agent.set_training_mode(False)

# 使用模型
observation = env.reset()
action1, action2 = agent.select_action(observation, deterministic=True)
```

## 📈 训练建议

### 初学者建议

1. **先用快速配置测试**（50迭代，~10分钟）
   ```bash
   python training/train_ppo.py --config configs/fast_test.yaml
   ```

2. **观察是否收敛**
   - 胜率应该从50%左右开始提升
   - 平均奖励应该逐渐上升
   - 策略损失应该稳定下降

3. **如果收敛良好，使用完整配置**（1000迭代，~2-4小时）
   ```bash
   python training/train_ppo.py --config configs/ppo_config.yaml
   ```

### 对手选择建议

| 对手类型 | 难度 | 适用阶段 | 预期胜率 |
|---------|------|----------|---------|
| `random` | ⭐ | 初期训练 | >70% |
| `rule` | ⭐⭐⭐ | 中期训练 | >55% |
| `self` | ⭐⭐⭐⭐⭐ | 高级训练 | ~50% (动态提升) |

### 训练阶段

```
阶段1 (0-200迭代): vs Random
  → 目标: 胜率 >70%
  
阶段2 (200-500迭代): vs Rule
  → 目标: 胜率 >55%
  
阶段3 (500+迭代): Self-Play
  → 目标: 持续自我提升
```

## ⚙️ 调参建议

### 如果训练不收敛

```yaml
agent:
  learning_rate: 0.0001  # 降低学习率
  clip_epsilon: 0.1      # 减小裁剪范围
  entropy_coef: 0.02     # 增加探索
```

### 如果想要更快收敛

```yaml
agent:
  learning_rate: 0.001   # 提高学习率
  batch_size: 128        # 增大批次
  update_epochs: 8       # 更多更新
```

### 如果过拟合

```yaml
agent:
  entropy_coef: 0.05     # 增加探索
  
training:
  episodes_per_iteration: 200  # 更多数据
```

## 🐛 常见问题

### Q: 导入失败？
**A:** 确保在 `ai_training/` 目录下运行，且已安装所有依赖。

### Q: CUDA out of memory？
**A:** 减小 `batch_size` 或使用CPU：
```bash
python training/train_ppo.py --device cpu
```

### Q: 训练太慢？
**A:** 使用快速配置或减少episodes：
```bash
python training/train_ppo.py --config configs/fast_test.yaml
```

### Q: 如何中断训练？
**A:** 按 `Ctrl+C`，模型会自动保存为 `interrupted_model.pth`

### Q: 如何恢复训练？
**A:** 使用 `--resume` 参数：
```bash
python training/train_ppo.py --resume saved_models/ppo/run_XXX/checkpoint_iter_100.pth
```

## 📚 下一步

训练完成后，你可以：

1. **评估模型性能**
   ```bash
   python evaluation/evaluator.py --model saved_models/ppo/run_XXX/final_model.pth
   ```

2. **人机对战**
   ```bash
   python evaluation/play_vs_ai.py --model saved_models/ppo/run_XXX/final_model.pth
   ```

3. **可视化训练曲线**
   ```bash
   python evaluation/visualize.py --history saved_models/ppo/run_XXX/training_history.json
   ```

## 💡 提示

- 训练初期胜率波动是正常的
- 建议至少训练200-500次迭代才能看到稳定提升
- 定期评估模型避免过拟合
- 保存多个检查点方便回滚

祝训练顺利！🎉