"""
battle_env.py
游戏环境封装 - 符合Gymnasium接口 / Game Environment - Gymnasium Interface

这个环境将原有的游戏逻辑封装成标准的强化学习环境。
"""

import sys
import os
import io
import numpy as np
from typing import Tuple, Dict, Any, Optional

# 添加父目录到路径，以便导入游戏代码
current_dir = os.path.dirname(os.path.abspath(__file__))  # ai_training/environment/
ai_training_dir = os.path.dirname(current_dir)             # ai_training/
project_root = os.path.dirname(ai_training_dir)            # 项目根目录
sys.path.insert(0, project_root)

from player import Player
from combat_manager import CombatManager
from config import *


class BattleEnv:
    """
    回合制战斗游戏环境 / Turn-based Battle Game Environment
    
    符合Gymnasium接口，用于强化学习训练。
    
    状态空间: 66维连续向量
      - 玩家1状态: 18维
      - 玩家2状态: 18维
      - 全局状态: 6维
      - 历史信息: 24维 (P1动作12维 + P2动作12维)
    
    动作空间: 离散动作，每回合选择2个动作（2帧）
    奖励: 基于战斗结果和过程的奖励
    """
    
    # 动作映射
    ACTION_MAP = {
        0: 'attack',
        1: 'charge',
        2: 'control',
        3: 'grab',
        4: 'throw',
        5: 'defend',
        6: 'counter',
        7: 'move_left',
        8: 'move_right',
        9: 'dash_left',
        10: 'dash_right',
        11: 'burst'
    }
    
    def __init__(self, 
                 reward_type: str = 'dense',
                 max_turns: int = MAX_TURNS,
                 verbose: bool = False):
        """
        初始化环境
        
        Args:
            reward_type: 'dense' 或 'sparse' 奖励模式
            max_turns: 最大回合数
            verbose: 是否打印详细信息
        """
        self.reward_type = reward_type
        self.max_turns = max_turns
        self.verbose = verbose
        
        # 游戏对象
        self.player1 = None
        self.player2 = None
        self.combat = None
        
        # 环境状态
        self.current_turn = 0
        self.done = False
        
        # 历史信息（用于状态编码）
        self.p1_action_history = []  # 最近2帧的动作
        self.p2_action_history = []
        
        # 奖励追踪（用于密集奖励）
        self.p1_last_hp = PLAYER_MAX_HP
        self.p2_last_hp = PLAYER_MAX_HP
        
        # 动作和观察空间定义
        self.action_space_n = 12  # 12种动作
        self.observation_space_shape = (66,)  # 66维状态向量（18+18+6+24）
    
    def reset(self) -> np.ndarray:
        """
        重置环境到初始状态
        
        Returns:
            初始观察（状态）
        """
        # 创建玩家
        self.player1 = Player(PLAYER1_NAME, PLAYER1_START_POS)
        self.player2 = Player(PLAYER2_NAME, PLAYER2_START_POS)
        
        # 创建战斗管理器
        self.combat = CombatManager(self.player1, self.player2)
        
        # 重置状态
        self.current_turn = 0
        self.done = False
        
        # 重置历史
        self.p1_action_history = [-1, -1]  # -1表示无动作
        self.p2_action_history = [-1, -1]
        
        # 重置HP追踪
        self.p1_last_hp = self.player1.hp
        self.p2_last_hp = self.player2.hp
        
        # 返回初始观察
        return self._get_observation()
    
    def step(self, 
             p1_actions: Tuple[int, int], 
             p2_actions: Tuple[int, int]) -> Tuple[np.ndarray, float, float, bool, Dict]:
        """
        执行一个完整回合（2帧）
        
        Args:
            p1_actions: (frame1_action, frame2_action) - P1的两个动作
            p2_actions: (frame1_action, frame2_action) - P2的两个动作
        
        Returns:
            observation: 新的观察（状态）
            p1_reward: P1的奖励
            p2_reward: P2的奖励
            done: 是否结束
            info: 额外信息字典
        """
        # 转换动作为游戏可理解的格式
        p1_action_names = [self._action_to_name(a) for a in p1_actions]
        p2_action_names = [self._action_to_name(a) for a in p2_actions]
        
        # 记录回合前的状态
        p1_hp_before = self.player1.hp
        p2_hp_before = self.player2.hp
        
        # 捕获游戏输出（避免干扰训练）
        if not self.verbose:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
        
        try:
            # 执行回合
            self.combat.execute_turn(p1_action_names, p2_action_names)
            self.current_turn = self.combat.turn
        finally:
            if not self.verbose:
                sys.stdout = old_stdout
        
        # 更新动作历史
        self.p1_action_history = list(p1_actions)
        self.p2_action_history = list(p2_actions)
        
        # 检查游戏是否结束
        p1_alive = self.player1.is_alive()
        p2_alive = self.player2.is_alive()
        
        if not p1_alive or not p2_alive or self.current_turn >= self.max_turns:
            self.done = True
        
        # 计算奖励
        p1_reward, p2_reward = self._calculate_rewards(
            p1_hp_before, p2_hp_before,
            self.player1.hp, self.player2.hp,
            p1_alive, p2_alive
        )
        
        # 更新HP追踪
        self.p1_last_hp = self.player1.hp
        self.p2_last_hp = self.player2.hp
        
        # 获取新观察
        observation = self._get_observation()
        
        # 构建info字典
        info = {
            'turn': self.current_turn,
            'p1_hp': self.player1.hp,
            'p2_hp': self.player2.hp,
            'distance': self.combat.get_distance(),
            'p1_alive': p1_alive,
            'p2_alive': p2_alive,
            'winner': self._get_winner()
        }
        
        return observation, p1_reward, p2_reward, self.done, info
    
    def _get_observation(self) -> np.ndarray:
        """
        获取当前观察（状态向量）
        
        Returns:
            66维numpy数组
        """
        obs = []
        
        # ===== 玩家1状态 (18维) =====
        obs.extend(self._encode_player_state(self.player1, self.p1_action_history))
        
        # ===== 玩家2状态 (18维) =====
        obs.extend(self._encode_player_state(self.player2, self.p2_action_history))
        
        # ===== 全局状态 (6维) =====
        # 距离归一化
        obs.append(self.combat.get_distance() / MAP_SIZE)
        
        # 回合数归一化
        obs.append(self.current_turn / self.max_turns)
        
        # 玩家方向
        obs.append(1.0 if self.player1.is_left else 0.0)
        obs.append(1.0 if self.player2.is_left else 0.0)
        
        # 当前帧（模拟，实际在step中处理）- 这里简化处理
        obs.extend([1.0, 0.0])  # 假设当前是准备下一回合
        
        # ===== 历史信息 (12维) =====
        # P1上2帧动作（简化为one-hot编码，每个6维代表动作ID）
        for action_id in self.p1_action_history:
            if action_id == -1:
                obs.extend([0.0] * 6)  # 无动作
            else:
                action_vec = [0.0] * 6
                if action_id < 6:
                    action_vec[action_id] = 1.0
                obs.extend(action_vec)
        
        # P2上2帧动作
        for action_id in self.p2_action_history:
            if action_id == -1:
                obs.extend([0.0] * 6)
            else:
                action_vec = [0.0] * 6
                if action_id < 6:
                    action_vec[action_id] = 1.0
                obs.extend(action_vec)
        
        return np.array(obs, dtype=np.float32)
    
    def _encode_player_state(self, player: Player, action_history: list) -> list:
        """
        编码单个玩家的状态 (18维)
        
        Args:
            player: 玩家对象
            action_history: 动作历史
        
        Returns:
            18维列表
        """
        state = []
        
        # HP归一化 (1维)
        state.append(player.hp / player.max_hp)
        
        # 位置归一化 (1维)
        state.append(player.position / MAP_SIZE)
        
        # 蓄力等级 one-hot (3维)
        charge_vec = [0.0, 0.0, 0.0]
        if player.charge_level < 3:
            charge_vec[player.charge_level] = 1.0
        state.extend(charge_vec)
        
        # 冲刺buff one-hot (3维)
        dash_vec = [0.0, 0.0, 0.0]
        stacks = min(player.dash_buff_stacks, 2)
        dash_vec[stacks] = 1.0
        state.extend(dash_vec)
        
        # 连击数 one-hot (4维)
        combo_vec = [0.0, 0.0, 0.0, 0.0]
        combo = min(player.combo_count, 3)
        combo_vec[combo] = 1.0
        state.extend(combo_vec)
        
        # 被控制状态 (1维)
        state.append(1.0 if player.controlled else 0.0)
        
        # 硬直状态 (1维) - 检查下一回合第一帧是否硬直
        next_turn = self.current_turn + 1
        is_stunned = player.is_frame_locked(next_turn, 1)
        state.append(1.0 if is_stunned else 0.0)
        
        # 上一帧动作简化编码 (4维) - 使用动作类型分类
        # 0: 无动作, 1: 攻击类, 2: 防御类, 3: 移动类, 4: 其他
        if len(action_history) > 0 and action_history[-1] != -1:
            last_action = action_history[-1]
            action_type = self._classify_action(last_action)
            action_vec = [0.0, 0.0, 0.0, 0.0]
            action_vec[action_type] = 1.0
            state.extend(action_vec)
        else:
            state.extend([1.0, 0.0, 0.0, 0.0])  # 无动作
        
        return state
    
    def _classify_action(self, action_id: int) -> int:
        """
        将动作分类
        0: 攻击类 (attack, control, grab, throw, burst)
        1: 防御类 (defend, counter)
        2: 移动类 (move, dash)
        3: 其他 (charge)
        """
        if action_id in [0, 2, 3, 4, 11]:  # attack, control, grab, throw, burst
            return 0
        elif action_id in [5, 6]:  # defend, counter
            return 1
        elif action_id in [7, 8, 9, 10]:  # moves and dashes
            return 2
        else:  # charge
            return 3
    
    def _calculate_rewards(self, 
                          p1_hp_before: int, p2_hp_before: int,
                          p1_hp_after: int, p2_hp_after: int,
                          p1_alive: bool, p2_alive: bool) -> Tuple[float, float]:
        """
        计算双方奖励
        
        Args:
            p1_hp_before, p2_hp_before: 回合前HP
            p1_hp_after, p2_hp_after: 回合后HP
            p1_alive, p2_alive: 存活状态
        
        Returns:
            (p1_reward, p2_reward)
        """
        if self.reward_type == 'sparse':
            return self._sparse_rewards(p1_alive, p2_alive)
        else:
            return self._dense_rewards(
                p1_hp_before, p2_hp_before,
                p1_hp_after, p2_hp_after,
                p1_alive, p2_alive
            )
    
    def _sparse_rewards(self, p1_alive: bool, p2_alive: bool) -> Tuple[float, float]:
        """
        稀疏奖励：只在游戏结束时给奖励
        """
        if not self.done:
            return 0.0, 0.0
        
        # 胜负奖励
        if p1_alive and not p2_alive:
            return 100.0, -100.0
        elif not p1_alive and p2_alive:
            return -100.0, 100.0
        else:  # 平局或双败
            return 0.0, 0.0
    
    def _dense_rewards(self,
                      p1_hp_before: int, p2_hp_before: int,
                      p1_hp_after: int, p2_hp_after: int,
                      p1_alive: bool, p2_alive: bool) -> Tuple[float, float]:
        """
        密集奖励：每回合都给予奖励反馈
        
        奖励组成：
        - 造成/受到伤害
        - 控制成功
        - 连击
        - 血量优势
        - 胜负
        """
        p1_reward = 0.0
        p2_reward = 0.0
        
        # 伤害奖励
        p1_dealt = p2_hp_before - p2_hp_after
        p2_dealt = p1_hp_before - p1_hp_after
        
        p1_reward += p1_dealt * 2.0
        p1_reward -= p2_dealt * 1.5
        
        p2_reward += p2_dealt * 2.0
        p2_reward -= p1_dealt * 1.5
        
        # 控制奖励
        if self.player2.controlled and self.player2.controller == self.player1.name:
            p1_reward += 5.0
        if self.player1.controlled and self.player1.controller == self.player2.name:
            p2_reward += 5.0
        
        # 连击奖励
        if self.player2.combo_count > 0:
            p1_reward += self.player2.combo_count * 2.0
        if self.player1.combo_count > 0:
            p2_reward += self.player1.combo_count * 2.0
        
        # 血量优势奖励（微小）
        hp_diff = p1_hp_after - p2_hp_after
        p1_reward += hp_diff * 0.1
        p2_reward -= hp_diff * 0.1
        
        # 存活奖励（鼓励不早死）
        if not self.done:
            p1_reward += 0.5
            p2_reward += 0.5
        
        # 胜负终结奖励
        if self.done:
            if p1_alive and not p2_alive:
                p1_reward += 100.0
                p2_reward -= 100.0
            elif not p1_alive and p2_alive:
                p1_reward -= 100.0
                p2_reward += 100.0
            # 平局不额外奖惩
        
        return p1_reward, p2_reward
    
    def _action_to_name(self, action_id: int) -> str:
        """转换动作ID为游戏动作名称"""
        if action_id in self.ACTION_MAP:
            return self.ACTION_MAP[action_id]
        return None
    
    def _get_winner(self) -> Optional[str]:
        """获取胜者"""
        if not self.done:
            return None
        
        p1_alive = self.player1.is_alive()
        p2_alive = self.player2.is_alive()
        
        if p1_alive and not p2_alive:
            return self.player1.name
        elif not p1_alive and p2_alive:
            return self.player2.name
        else:
            return "Draw"
    
    def get_valid_actions(self, player_id: int) -> list:
        """
        获取玩家的有效动作列表
        
        Args:
            player_id: 1 或 2
        
        Returns:
            有效动作ID列表
        """
        player = self.player1 if player_id == 1 else self.player2
        opponent = self.player2 if player_id == 1 else self.player1
        next_turn = self.current_turn + 1
        
        # 检查硬直
        if player.is_frame_locked(next_turn, 1):
            return [11]  # 只能爆血
        
        # 检查被控制
        if player.controlled:
            return [5, 11]  # 只能防御或爆血
        
        # 检查grab/throw前置条件
        valid_actions = list(range(12))
        
        if not opponent.controlled:
            # 对手未被控制，不能使用grab/throw
            valid_actions.remove(3)  # grab
            valid_actions.remove(4)  # throw
        
        return valid_actions
    
    def render(self, mode: str = 'human'):
        """
        渲染环境（可选）
        
        Args:
            mode: 渲染模式，'human' 或 'ansi'
        """
        if mode == 'human' or mode == 'ansi':
            print(f"\n{'='*60}")
            print(f"回合 {self.current_turn} | 距离: {self.combat.get_distance()}格")
            self.player1.show_status()
            self.player2.show_status()
            print('='*60)
    
    def close(self):
        """关闭环境"""
        pass


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 BattleEnv...")
    
    # 创建环境
    env = BattleEnv(reward_type='dense', verbose=True)
    
    # 重置
    obs = env.reset()
    print(f"初始观察维度: {obs.shape}")
    print(f"初始观察: {obs[:10]}...")  # 只打印前10维
    
    # 运行几个回合
    for episode in range(3):
        print(f"\n========== Episode {episode + 1} ==========")
        obs = env.reset()
        done = False
        total_p1_reward = 0
        total_p2_reward = 0
        
        while not done:
            # 随机选择动作
            p1_actions = (
                np.random.choice(env.get_valid_actions(1)),
                np.random.choice(env.get_valid_actions(1))
            )
            p2_actions = (
                np.random.choice(env.get_valid_actions(2)),
                np.random.choice(env.get_valid_actions(2))
            )
            
            # 执行
            obs, p1_reward, p2_reward, done, info = env.step(p1_actions, p2_actions)
            
            total_p1_reward += p1_reward
            total_p2_reward += p2_reward
            
            print(f"回合 {info['turn']}: P1奖励={p1_reward:.2f}, P2奖励={p2_reward:.2f}")
        
        print(f"\n游戏结束！")
        print(f"胜者: {info['winner']}")
        print(f"P1总奖励: {total_p1_reward:.2f}")
        print(f"P2总奖励: {total_p2_reward:.2f}")
    
    print("\n✅ BattleEnv 测试完成！")