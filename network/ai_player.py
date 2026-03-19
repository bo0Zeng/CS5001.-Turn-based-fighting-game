"""
ai_player.py
决策树AI玩家 - 优化版
AI Player based on decision tree - Optimized
"""

import random
import json
from typing import List, Dict, Any, Tuple


class AIPlayer:
    """AI玩家 - 使用决策树进行决策"""
    
    def __init__(self, player, opponent, combat_manager):
        self.player = player
        self.opponent = opponent
        self.combat = combat_manager
        self.is_left = player.is_left
        
        self.evolved_params = self._load_evolved_config()
        self.decision_tree = self._load_decision_tree()
        
        self.stats = {
            'total_decisions': 0,
            'layer_usage': {1: 0, 2: 0, 3: 0, 4: 0},
            'action_counts': {},
            'win_rate': 0.0
        }
    
    def _load_evolved_config(self):
        """加载进化后的AI配置"""
        try:
            import json
            import os
            
            files = [f for f in os.listdir('.') if f.startswith('best_ai_evolved') and f.endswith('.json')]
            if files:
                latest = sorted(files)[-1]
                with open(latest, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[AI] 加载进化配置: {latest} (fitness={data['best_genome'].get('fitness', 0):.3f})")
                    return data['best_genome']['parameters']
        except Exception as e:
            print(f"[AI] 使用默认配置")
        return None
    
    def _load_decision_tree(self):
        """加载决策树配置"""
        return {
            'priority_layers': [
                self._get_layer_1(),
                self._get_layer_2(),
                self._get_layer_3(),
                self._get_layer_4()
            ],
            'direction_mapping': {
                True: {
                    'retreat': 'move_left',
                    'dash_retreat': 'dash_left',
                    'approach': 'move_right',
                    'dash_approach': 'dash_right'
                },
                False: {
                    'retreat': 'move_right',
                    'dash_retreat': 'dash_right',
                    'approach': 'move_left',
                    'dash_approach': 'dash_left'
                }
            }
        }
    
    def choose_turn_actions(self) -> List[str]:
        """选择一个回合的2帧动作"""
        frame1 = self.choose_frame_action(1)
        frame2 = self.choose_frame_action(2)
        
        self.stats['total_decisions'] += 2
        
        return [frame1, frame2]
    
    def choose_frame_action(self, frame: int) -> str:
        """选择单帧动作"""
        next_turn = self.combat.turn + 1
        distance = self.combat.get_distance()
        
        for layer_idx, layer in enumerate(self.decision_tree['priority_layers'], 1):
            action = self._evaluate_layer(layer, frame, next_turn, distance)
            if action:
                self.stats['layer_usage'][layer_idx] += 1
                self._record_action(action)
                return action
        
        return 'defend'
    
    def _evaluate_layer(self, layer, frame, next_turn, distance):
        """评估决策层"""
        layer_num = layer['layer']
        
        if layer_num == 1:
            return self._layer_1_forced_state(frame, next_turn)
        elif layer_num == 2:
            return self._layer_2_combo_system()
        elif layer_num == 3:
            return self._layer_3_tactical_decision(distance, frame)
        elif layer_num == 4:
            return self._layer_4_special_tactics(distance)
        
        return None
    
    def _layer_1_forced_state(self, frame, next_turn):
        """层1: 强制状态（硬直、控制）"""
        # 硬直检查
        if self.player.is_frame_locked(next_turn, frame):
            if self._can_burst():
                return 'burst'
            return None
        
        # 被控制检查
        if self.player.controlled:
            distance = self.combat.get_distance()
            if distance <= 2 and self.opponent.hp <= 6 - distance:
                if random.random() < 0.3:
                    return 'burst'
            return 'defend'
        
        # 对手被控制
        if self.opponent.controlled and self.opponent.controller == self.player.name:
            if self.opponent.hp <= 4 or self._at_boundary(self.player):
                return 'grab'
            else:
                return 'throw' if random.random() < 0.4 else 'grab'
        
        return None
    
    def _layer_2_combo_system(self):
        """层2: 连击系统"""
        distance = self.combat.get_distance()
        
        # 自己连击2，避免第3击
        if self.player.combo_count == 2:
            if distance <= 1 and self._predict_opponent_attack() > 0.5:
                return self._get_dash_retreat()
            else:
                return 'defend'
        
        # 对手连击2，触发硬直 - 提高激进度
        if self.opponent.combo_count == 2:
            if distance <= 1:
                if random.random() < 0.85:  # 从0.7提升到0.85
                    return 'attack'
            elif distance == 2:
                if random.random() < 0.6:  # 从0.5提升到0.6
                    return self._get_approach()
        
        return None
    
    def _layer_3_tactical_decision(self, distance, frame):
        """层3: 战术决策（整合蓄力威胁+距离战术）"""
        # 蓄力威胁应对（最高优先级）
        charge_response = self._handle_charge_threat(distance)
        if charge_response:
            return charge_response
        
        # 距离战术
        return self._distance_tactics(distance, frame)
    
    def _handle_charge_threat(self, distance):
        """处理蓄力威胁"""
        # 对手蓄力2 - 危险！
        if self.opponent.charge_level == 2:
            if distance <= 1:
                # 距离0-1：优先打断
                choices = [
                    ('control', 0.7),
                    (self._get_dash_retreat(), 0.2),
                    ('counter', 0.1)
                ]
            elif distance == 2:
                # 距离2：撤退为主
                choices = [
                    (self._get_dash_retreat(), 0.6),
                    ('control', 0.25),
                    ('defend', 0.15)
                ]
            else:
                # 距离3+：防御等待
                choices = [
                    ('defend', 0.5),
                    ('charge', 0.3),
                    (self._get_dash_retreat(), 0.2)
                ]
            return self._weighted_choice(choices)
        
        # 自己蓄力2 - 释放时机
        if self.player.charge_level == 2:
            hp_adv = self.player.hp - self.opponent.hp
            release_prob = self.evolved_params.get('charge2_release_prob', 0.7) if self.evolved_params else 0.7
            
            if distance <= 2:
                if hp_adv >= 5 or self._predict_opponent_defend() > 0.5:
                    return 'attack' if random.random() < release_prob else 'control'
                else:
                    return 'attack'
            elif distance >= 3:
                return self._get_approach()
        
        # 对手蓄力1
        if self.opponent.charge_level == 1:
            if distance <= 1:
                return 'control' if random.random() < 0.5 else 'attack'
            elif distance == 2:
                return self._get_approach() if random.random() < 0.4 else 'control'
        
        # 自己蓄力1
        if self.player.charge_level == 1:
            stack_prob = self.evolved_params.get('charge1_stack_prob', 0.5) if self.evolved_params else 0.5
            
            if distance >= 3 and not self._predict_opponent_interrupt():
                return 'charge' if random.random() < stack_prob else 'attack'
            elif distance <= 2:
                return 'attack'
        
        return None
    
    def _distance_tactics(self, distance, frame):
        """距离战术"""
        if distance == 0:
            # 距离0理论上不会到这里（Layer 1已处理）
            # 异常兜底：立即撤退
            return self._get_dash_retreat()
        elif distance == 1:
            return self._tactics_distance_1()
        elif distance == 2:
            return self._tactics_distance_2()
        elif distance == 3:
            return self._tactics_distance_3()
        else:
            return self._tactics_distance_4_plus()
    
    def _tactics_distance_1(self):
        """距离1战术 - 利用buff优势"""
        # 有冲刺buff - 激进进攻
        if self.player.dash_buff_stacks > 0:
            choices = [
                ('attack', 0.7),  # 利用buff高伤
                ('control', 0.2),
                (self._get_approach(), 0.1)
            ]
            return self._weighted_choice(choices)
        
        # 对手有高蓄力 - 保守应对
        if self.opponent.charge_level >= 1:
            choices = [
                ('control', 0.5),
                (self._get_dash_retreat(), 0.3),
                ('counter', 0.2)
            ]
            return self._weighted_choice(choices)
        
        # 常规战术
        choices = [
            ('attack', 0.4),
            ('control', 0.3),
            ('charge', 0.2),
            ('counter', 0.1)
        ]
        return self._weighted_choice(choices)
    
    def _tactics_distance_2(self):
        """距离2战术"""
        # 自己蓄力2 - 进攻
        if self.player.charge_level == 2:
            choices = [
                ('attack', 0.6),
                (self._get_approach(), 0.3),
                (self._get_dash_approach(), 0.1)
            ]
            return self._weighted_choice(choices)
        
        # 对手蓄力高 - 防守
        if self.opponent.charge_level >= 1:
            choices = [
                ('defend', 0.4),
                (self._get_dash_retreat(), 0.3),
                ('counter', 0.2),
                ('charge', 0.1)
            ]
            return self._weighted_choice(choices)
        
        # 有buff - 接近
        if self.player.dash_buff_stacks > 0:
            choices = [
                (self._get_dash_approach(), 0.5),
                (self._get_approach(), 0.3),
                ('attack', 0.2)
            ]
            return self._weighted_choice(choices)
        
        # 常规 - 蓄力为主
        choices = [
            ('charge', 0.45),
            (self._get_approach(), 0.25),
            (self._get_dash_approach(), 0.2),
            ('defend', 0.1)
        ]
        return self._weighted_choice(choices)
    
    def _tactics_distance_3(self):
        """距离3战术"""
        hp_adv = self.player.hp - self.opponent.hp
        
        if hp_adv >= 10 and self.opponent.hp <= 6:
            return 'burst' if random.random() < 0.5 else self._get_dash_approach()
        elif hp_adv >= 10:
            choices = [
                ('charge', 0.5),
                (self._get_dash_approach(), 0.3),
                ('defend', 0.2)
            ]
        elif hp_adv <= -10:
            choices = [
                ('defend', 0.4),
                ('charge', 0.35),
                (self._get_dash_retreat(), 0.25)
            ]
        else:
            choices = [
                ('charge', 0.5),
                (self._get_dash_approach(), 0.25),
                ('defend', 0.15),
                ('burst', 0.1)
            ]
        return self._weighted_choice(choices)
    
    def _tactics_distance_4_plus(self):
        """距离4+战术"""
        choices = [
            ('charge', 0.55),
            (self._get_dash_approach(), 0.25),
            ('defend', 0.15),
            (self._get_approach(), 0.05)
        ]
        return self._weighted_choice(choices)
    
    def _layer_4_special_tactics(self, distance):
        """层4: 特殊战术（爆血、边界）"""
        # 边界压制
        if self._at_boundary(self.opponent):
            prob = self.evolved_params.get('boundary_pressure_prob', 0.45) if self.evolved_params else 0.45
            if distance <= 2 and random.random() < prob:
                return 'control' if random.random() < 0.45 else 'attack'
        
        # 边界逃脱
        if self._at_boundary(self.player):
            prob = self.evolved_params.get('boundary_escape_prob', 0.6) if self.evolved_params else 0.6
            if random.random() < prob:
                return self._get_retreat()
        
        # 爆血击杀 - 改进判断
        if self._can_burst_kill():
            # 考虑对手防御能力
            opponent_def_bonus = 0
            if self.opponent.dash_buff_stacks > 0:
                opponent_def_bonus = self.opponent.dash_buff_stacks
            if self.opponent.charge_level > 0:
                opponent_def_bonus += 1
            
            enemy_damage = max(0, 6 - distance)
            if self.opponent.hp <= enemy_damage - opponent_def_bonus:
                kill_probs = {0: 0.95, 1: 0.85, 2: 0.75, 3: 0.65}
                prob = kill_probs.get(distance, 0.5)
                if random.random() < prob:
                    return 'burst'
        
        # 优势换血
        hp_adv = self.player.hp - self.opponent.hp
        hp_threshold = self.evolved_params.get('burst_trade_hp_threshold', 10) if self.evolved_params else 10
        min_hp = self.evolved_params.get('burst_trade_min_hp', 15) if self.evolved_params else 15
        
        if hp_adv >= hp_threshold and self.player.hp >= min_hp and distance <= 2:
            if random.random() < 0.4:
                return 'burst'
        
        # 绝境爆血 - 更保守
        desperate_hp = self.evolved_params.get('burst_desperate_hp', 5) if self.evolved_params else 5
        if self.player.hp <= desperate_hp and self.opponent.hp <= 8:
            if distance <= 1 and self.opponent.hp <= desperate_hp:
                if random.random() < 0.7:
                    return 'burst'
            elif distance == 2:
                if random.random() < 0.5:
                    return 'burst'
        
        return None
    
    # ===== 辅助方法 =====
    
    def _get_approach(self):
        return self.decision_tree['direction_mapping'][self.is_left]['approach']
    
    def _get_retreat(self):
        return self.decision_tree['direction_mapping'][self.is_left]['retreat']
    
    def _get_dash_approach(self):
        return self.decision_tree['direction_mapping'][self.is_left]['dash_approach']
    
    def _get_dash_retreat(self):
        return self.decision_tree['direction_mapping'][self.is_left]['dash_retreat']
    
    def _predict_opponent_attack(self) -> float:
        """预测对手攻击概率 - 增强版"""
        if self.evolved_params:
            prob = self.evolved_params.get('attack_prediction_base', 0.4)
            mods = self.evolved_params.get('attack_prediction_modifiers', {})
        else:
            prob = 0.4
            mods = {
                'charge2': 0.45, 'charge1': 0.15, 'buff2': 0.25,
                'hp_advantage': 0.15, 'hp_disadvantage': -0.2, 
                'combo2': -0.35, 'buff_self': 0.2
            }
        
        # 蓄力状态
        if self.opponent.charge_level == 2:
            prob += mods.get('charge2', 0.45)
        elif self.opponent.charge_level == 1:
            prob += mods.get('charge1', 0.15)
        
        # buff状态
        if self.opponent.dash_buff_stacks == 2:
            prob += mods.get('buff2', 0.25)
        elif self.opponent.dash_buff_stacks == 1:
            prob += mods.get('buff1', 0.15)
        
        # HP差距
        hp_diff = self.opponent.hp - self.player.hp
        if hp_diff > 5:
            prob += mods.get('hp_advantage', 0.15)
        elif hp_diff < -5:
            prob += mods.get('hp_disadvantage', -0.2)
        
        # 连击状态
        if self.opponent.combo_count == 2:
            prob += mods.get('combo2', -0.35)
        
        # 自己有高buff，对手更可能攻击
        if self.player.dash_buff_stacks >= 1:
            prob += mods.get('buff_self', 0.2)
        
        return max(0.1, min(0.9, prob))
    
    def _predict_opponent_defend(self) -> float:
        """预测对手防御概率 - 增强版"""
        if self.evolved_params:
            prob = self.evolved_params.get('defend_prediction_base', 0.25)
            mods = self.evolved_params.get('defend_prediction_modifiers', {})
        else:
            prob = 0.25
            mods = {
                'self_charge2': 0.4, 'self_buff2': 0.3,
                'opp_combo2': 0.4, 'hp_disadvantage': 0.3
            }
        
        if self.player.charge_level == 2:
            prob += mods.get('self_charge2', 0.4)
        if self.player.dash_buff_stacks == 2:
            prob += mods.get('self_buff2', 0.3)
        if self.opponent.combo_count == 2:
            prob += mods.get('opp_combo2', 0.4)
        
        hp_diff = self.opponent.hp - self.player.hp
        if hp_diff < -10:
            prob += mods.get('hp_disadvantage', 0.3)
        
        return max(0.1, min(0.9, prob))
    
    def _predict_opponent_interrupt(self) -> bool:
        """预测对手是否会打断蓄力"""
        distance = self.combat.get_distance()
        prob = 0.3
        
        if distance <= 1:
            prob += 0.4
        elif distance == 2:
            prob += 0.2
        
        if self.opponent.charge_level > 0:
            prob -= 0.3
        
        return random.random() < max(0.1, min(0.9, prob))
    
    def _can_burst(self) -> bool:
        return True
    
    def _can_burst_kill(self) -> bool:
        """爆血是否能击杀 - 考虑对手防御"""
        distance = self.combat.get_distance()
        enemy_damage = max(0, 6 - distance)
        
        # 考虑对手可能的防御
        possible_def = 0
        if self.opponent.dash_buff_stacks > 0:
            possible_def = self.opponent.dash_buff_stacks
        
        return self.opponent.hp <= enemy_damage - possible_def
    
    def _at_boundary(self, player) -> bool:
        return player.position == 1 or player.position == 6
    
    def _weighted_choice(self, choices: List[Tuple[str, float]]) -> str:
        total = sum(prob for _, prob in choices)
        r = random.uniform(0, total)
        
        cumulative = 0
        for action, prob in choices:
            cumulative += prob
            if r <= cumulative:
                return action
        
        return choices[-1][0]
    
    def _record_action(self, action: str):
        if action not in self.stats['action_counts']:
            self.stats['action_counts'][action] = 0
        self.stats['action_counts'][action] += 1
    
    def _get_layer_1(self):
        return {'layer': 1, 'name': '强制状态'}
    
    def _get_layer_2(self):
        return {'layer': 2, 'name': '连击系统'}
    
    def _get_layer_3(self):
        return {'layer': 3, 'name': '战术决策'}
    
    def _get_layer_4(self):
        return {'layer': 4, 'name': '特殊战术'}
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()
    
    def reset_stats(self):
        self.stats = {
            'total_decisions': 0,
            'layer_usage': {1: 0, 2: 0, 3: 0, 4: 0},
            'action_counts': {},
            'win_rate': 0.0
        }