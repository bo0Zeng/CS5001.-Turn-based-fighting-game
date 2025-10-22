"""
combat_manager.py
战斗管理器 - 完全状态化终极版
"""

from player import Player
from actions import Actions
from config import *


class CombatManager:
    """战斗管理器 - 完全状态化执行流程"""
    
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.turn = 0
        
        self.turn_logs = []
        self.current_turn_messages = []
        
        # 确定固定身份（左/右玩家）
        if player1.position < player2.position:
            player1.is_left = True
            player2.is_left = False
        else:
            player1.is_left = False
            player2.is_left = True
    
    def save_turn_log(self, messages):
        self.turn_logs.append((self.turn, messages.copy()))
    
    def get_turn_log(self, turn_number):
        for turn, msgs in self.turn_logs:
            if turn == turn_number:
                return msgs
        return []
    
    def get_distance(self):
        return abs(self.p1.position - self.p2.position)
    
    def execute_turn(self, p1_actions, p2_actions):
        """执行一个完整回合（2帧）"""
        self.turn += 1
        print(f"\n{'='*60}")
        print(f"回合 {self.turn} | 距离: {self.get_distance()}格")
        self.p1.show_status()
        self.p2.show_status()
        print('='*60)
        
        self.p1.clear_old_locks(self.turn)
        self.p2.clear_old_locks(self.turn)
        
        for frame_idx in range(2):
            frame = frame_idx + 1
            print(f"\n--- 第 {frame} 帧 ---")
            
            self.p1.reset_frame()
            self.p2.reset_frame()
            
            p1_act = p1_actions[frame_idx] if frame_idx < len(p1_actions) else None
            p2_act = p2_actions[frame_idx] if frame_idx < len(p2_actions) else None
            
            p1_act = self._preprocess(self.p1, p1_act, frame)
            p2_act = self._preprocess(self.p2, p2_act, frame)
            
            self._execute_frame(p1_act, p2_act, frame)
            
            if not self.p1.is_alive() or not self.p2.is_alive():
                return
    
    def _preprocess(self, player, action, frame):
        """预处理行动（检查所有前置条件）"""
        if not action:
            return None
        
        # 检查硬直
        if player.is_frame_locked(self.turn, frame):
            if action == 'burst':
                print(f"💥 {player.name} 硬直中使用爆血！")
                return action
            else:
                print(f"🔒 {player.name} 第{frame}帧被硬直！")
                return None
        
        # 检查被控制
        if player.controlled and action not in ['defend', 'burst']:
            print(f"⛓️ {player.name} 被控制，只能S或O！")
            return None
        
        # 检查grab/throw的前置条件：对手必须被控制
        if action in ['grab', 'throw']:
            opponent = self.p2 if player == self.p1 else self.p1
            if not opponent.controlled:
                print(f"❌ 对手未被控制，无法使用{action}！")
                return None
        
        return action
    
    def _execute_frame(self, p1_act, p2_act, frame):
        """执行单帧 - 完全状态化流程"""
        
        # ===== 阶段1：生成所有状态 =====
        print("\n[1.生成所有状态]")
        
        # 移动
        if p1_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p1, p1_act)
        if p2_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p2, p2_act)
        
        # 防御
        if p1_act in ['defend', 'counter']:
            self._do_defend(self.p1, p1_act)
        if p2_act in ['defend', 'counter']:
            self._do_defend(self.p2, p2_act)
        
        # 蓄力
        if p1_act == 'charge':
            self._do_charge(self.p1, frame)
        if p2_act == 'charge':
            self._do_charge(self.p2, frame)
        
        # 技能（control/grab/throw直接生成，前置条件已在_preprocess检查）
        if p1_act == 'control':
            Actions.control(self.p1, self.p2)
        elif p1_act == 'grab':
            Actions.grab(self.p1, self.p2)
        elif p1_act == 'throw':
            Actions.throw(self.p1, self.p2)
        elif p1_act == 'attack':
            Actions.attack(self.p1, self.p2, 999)  # 临时距离
        
        if p2_act == 'control':
            Actions.control(self.p2, self.p1)
        elif p2_act == 'grab':
            Actions.grab(self.p2, self.p1)
        elif p2_act == 'throw':
            Actions.throw(self.p2, self.p1)
        elif p2_act == 'attack':
            Actions.attack(self.p2, self.p1, 999)
        
        # ===== 阶段2：预计算位置（直接读取所有position_states）=====
        print("\n[2.预计算位置]")
        pred_p1_pos, pred_p2_pos = self._predict_final_positions()
        pred_distance = abs(pred_p1_pos - pred_p2_pos)
        print(f"   预测：{self.p1.name}→{pred_p1_pos}, {self.p2.name}→{pred_p2_pos}, 距离={pred_distance}")
        
        # ===== 阶段3：基于预计算执行距离相关技能 =====
        print("\n[3.基于预测执行距离技能]")
        
        # 重新生成attack（使用正确的预测距离）
        if p1_act == 'attack':
            self._validate_and_regenerate_attack(self.p1, self.p2, pred_distance, p1_act)
        
        if p2_act == 'attack':
            self._validate_and_regenerate_attack(self.p2, self.p1, pred_distance, p2_act)
        
        # Burst基于预测距离
        if p1_act == 'burst':
            Actions.burst(self.p1, self.p2, pred_distance)
        if p2_act == 'burst':
            Actions.burst(self.p2, self.p1, pred_distance)
        
        # ===== 阶段4：结算标记 =====
        print("\n[4.结算标记]")
        self._settle_marker_states()
        
        # ===== 阶段5：预判定 =====
        print("\n[5.预判定]")
        self._pre_check_dodge(p1_act, p2_act, pred_p1_pos, pred_p2_pos, frame)
        self._pre_check_interrupt(p1_act, p2_act)
        self._pre_check_counter(p1_act, p2_act)
        
        # ===== 阶段6：结算Buff =====
        print("\n[6.结算Buff]")
        self._settle_buff_states()
        
        # ===== 阶段7：结算控制 =====
        print("\n[7.结算控制]")
        self._settle_control_states(frame)
        
        # ===== 阶段8：结算位置 =====
        print("\n[8.结算位置]")
        self._resolve_and_apply_positions(p1_act, p2_act)
        
        # ===== 阶段9：结算伤害 =====
        print("\n[9.结算伤害]")
        self._settle_damage()
        
        # ===== 阶段10：后处理 =====
        print("\n[10.后处理]")
        self._post_check_combo(frame)
        self._post_check_charge_2_stun(frame)
    
    def _do_move(self, player, action):
        direction = 'left' if action in ['move_left', 'dash_left'] else 'right'
        if action in ['dash_left', 'dash_right']:
            Actions.dash(player, direction)
        else:
            Actions.move(player, direction)
    
    def _do_defend(self, player, action):
        if action == 'defend':
            Actions.defend(player)
        else:
            Actions.counter(player)
    
    def _do_charge(self, player, frame):
        """蓄力"""
        can_stack = False
        
        if player.charge_level == 1:
            if player.can_stack_charge(self.turn, frame, player.last_charge_turn, player.last_charge_frame):
                can_stack = True
        
        if can_stack:
            player.add_buff_state('charge', 'gain', 2)
            print(f"✨✨ {player.name} 将获得蓄力2！")
        else:
            player.add_buff_state('charge', 'gain', 1)
            print(f"✨ {player.name} 将获得蓄力1！")
        
        player.last_charge_turn = self.turn
        player.last_charge_frame = frame
    
    def _validate_and_regenerate_attack(self, attacker, defender, pred_distance, action):
        """重新生成攻击状态（使用正确的预测距离）"""
        # 清除之前的临时attack状态
        defender.damage_states = [s for s in defender.damage_states 
                                 if s.source != attacker.name or 'penalty' in s.source or 'interrupt' in s.source]
        attacker.marker_states = [s for s in attacker.marker_states 
                                 if s.type not in ['tried_attack', 'dealt_damage', 'used_charge_2']]
        
        # 重新生成（使用正确的预测距离）
        Actions.attack(attacker, defender, pred_distance)
    
    def _resolve_positions_core(self, p1_states, p2_states, p1_initial, p2_initial):
        """核心冲突检测算法（纯函数，可复用）
        
        Returns:
            (p1_final, p2_final, p1_active, p2_active)
        """
        if not p1_states and not p2_states:
            return p1_initial, p2_initial, 0, 0
        
        p1_active = len(p1_states)
        p2_active = len(p2_states)
        
        # 循环解决冲突
        while True:
            p1_pos = p1_initial + sum(p1_states[i].delta for i in range(p1_active))
            p2_pos = p2_initial + sum(p2_states[i].delta for i in range(p2_active))
            
            p1_pos = max(1, min(MAP_SIZE, p1_pos))
            p2_pos = max(1, min(MAP_SIZE, p2_pos))
            
            has_conflict = False
            
            # 重叠检查
            if p1_pos == p2_pos:
                is_control_overlap = (
                    (self.p1.controlled or self.p2.controlled) and
                    p1_initial == p2_initial
                )
                if not is_control_overlap:
                    has_conflict = True
            
            # 穿越检查
            if not has_conflict:
                if p1_initial < p2_initial and p1_pos > p2_pos:
                    has_conflict = True
                elif p2_initial < p1_initial and p2_pos > p1_pos:
                    has_conflict = True
            
            # 互换方位检查
            if not has_conflict:
                if p1_initial == p2_initial and p1_pos != p2_pos:
                    if (p1_pos < p2_initial and p2_pos > p1_initial) or \
                       (p2_pos < p1_initial and p1_pos > p2_initial):
                        has_conflict = True
            
            if not has_conflict:
                break
            
            if p1_active == 0 and p2_active == 0:
                break
            
            if p1_active > 0:
                p1_active -= 1
            if p2_active > 0:
                p2_active -= 1
        
        return p1_pos, p2_pos, p1_active, p2_active
    
    def _predict_final_positions(self):
        """预计算最终位置（直接读取所有position_states，包含技能位移）"""
        p1_pos, p2_pos, _, _ = self._resolve_positions_core(
            self.p1.position_states,
            self.p2.position_states,
            self.p1.position,
            self.p2.position
        )
        return p1_pos, p2_pos
    
    def _resolve_and_apply_positions(self, p1_act, p2_act):
        """解决位置冲突并应用"""
        p1_states = self.p1.position_states
        p2_states = self.p2.position_states
        
        if not p1_states and not p2_states:
            return 0, 0
        
        p1_initial = self.p1.position
        p2_initial = self.p2.position
        
        p1_final, p2_final, p1_active, p2_active = self._resolve_positions_core(
            p1_states, p2_states, p1_initial, p2_initial
        )
        
        if p1_final != p1_initial:
            print(f"✅ {self.p1.name} 移动：{p1_initial}→{p1_final} (成功{p1_active}/{len(p1_states)})")
            self.p1.position = p1_final
        elif p1_states:
            print(f"❌ {self.p1.name} 移动失败（0/{len(p1_states)}）")
        
        if p2_final != p2_initial:
            print(f"✅ {self.p2.name} 移动：{p2_initial}→{p2_final} (成功{p2_active}/{len(p2_states)})")
            self.p2.position = p2_final
        elif p2_states:
            print(f"❌ {self.p2.name} 移动失败（0/{len(p2_states)}）")
        
        # 冲刺buff（仅主动移动）
        if p1_act in ['dash_left', 'dash_right'] and p1_active > 0:
            if self.p1.dash_buff_stacks < DASH_MAX_STACKS:
                self.p1.add_buff_state('dash', 'gain', 1)
                print(f"🏃 {self.p1.name} 将获得冲刺buff")
        
        if p2_act in ['dash_left', 'dash_right'] and p2_active > 0:
            if self.p2.dash_buff_stacks < DASH_MAX_STACKS:
                self.p2.add_buff_state('dash', 'gain', 1)
                print(f"🏃 {self.p2.name} 将获得冲刺buff")
        
        return p1_active, p2_active
    
    def _pre_check_dodge(self, p1_act, p2_act, pred_p1_pos, pred_p2_pos, frame):
        """预判定闪避（生成硬直状态）"""
        
        # P2攻击，P1移动
        if p2_act == 'attack' and p1_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            if self.p2.has_marker('tried_attack'):
                dist_before = abs(self.p1.position - self.p2.position)
                dist_after = abs(pred_p1_pos - pred_p2_pos)
                
                if (dist_before <= self.p2.attack_range_this_frame and 
                    dist_after > self.p2.attack_range_this_frame and
                    not self.p2.has_marker('dealt_damage')):
                    print(f"💨 {self.p1.name} 将闪避 {self.p2.name}！")
                    self.p2.add_control_state('stun', DODGE_STUN_FRAMES)
        
        # P1攻击，P2移动
        if p1_act == 'attack' and p2_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            if self.p1.has_marker('tried_attack'):
                dist_before = abs(self.p1.position - self.p2.position)
                dist_after = abs(pred_p1_pos - pred_p2_pos)
                
                if (dist_before <= self.p1.attack_range_this_frame and 
                    dist_after > self.p1.attack_range_this_frame and
                    not self.p1.has_marker('dealt_damage')):
                    print(f"💨 {self.p2.name} 将闪避 {self.p1.name}！")
                    self.p1.add_control_state('stun', DODGE_STUN_FRAMES)
    
    def _pre_check_interrupt(self, p1_act, p2_act):
        """预判定打断（生成buff失去状态或伤害状态）"""
        vulnerable = ['attack', 'burst', 'charge']
        
        if p1_act in vulnerable and not self.p1.has_marker('dealt_damage') and self.p2.has_marker('dealt_damage'):
            print(f"⚡ {self.p1.name}的{p1_act}将被打断！")
            if p1_act == 'charge' and self.p1.charge_level > 0:
                print(f"   失去蓄力")
                self.p1.add_buff_state('charge', 'lose')
                self.p1.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="interrupt")
        
        if p2_act in vulnerable and not self.p2.has_marker('dealt_damage') and self.p1.has_marker('dealt_damage'):
            print(f"⚡ {self.p2.name}的{p2_act}将被打断！")
            if p2_act == 'charge' and self.p2.charge_level > 0:
                print(f"   失去蓄力")
                self.p2.add_buff_state('charge', 'lose')
                self.p2.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="interrupt")
    
    def _pre_check_counter(self, p1_act, p2_act):
        """预判定反击（生成准备标记或硬直状态）"""
        
        if p1_act == 'counter':
            will_take_damage = len([s for s in self.p1.damage_states if not s.cancelled]) > 0
            
            if will_take_damage:
                print(f"⚔️ {self.p1.name} 反击准备！")
                self.p1.add_marker_state('prepare_counter')
            else:
                print(f"❌ {self.p1.name} 反击将失败！")
                self.p1.add_control_state('stun', COUNTER_FAIL_STUN_FRAMES)
        
        if p2_act == 'counter':
            will_take_damage = len([s for s in self.p2.damage_states if not s.cancelled]) > 0
            
            if will_take_damage:
                print(f"⚔️ {self.p2.name} 反击准备！")
                self.p2.add_marker_state('prepare_counter')
            else:
                print(f"❌ {self.p2.name} 反击将失败！")
                self.p2.add_control_state('stun', COUNTER_FAIL_STUN_FRAMES)
    
    def _settle_marker_states(self):
        """结算标记状态"""
        self.p1.tried_attack_this_frame = self.p1.has_marker('tried_attack')
        self.p1.dealt_damage_this_frame = self.p1.has_marker('dealt_damage')
        self.p1.used_charge_2_this_frame = self.p1.has_marker('used_charge_2')
        
        self.p2.tried_attack_this_frame = self.p2.has_marker('tried_attack')
        self.p2.dealt_damage_this_frame = self.p2.has_marker('dealt_damage')
        self.p2.used_charge_2_this_frame = self.p2.has_marker('used_charge_2')
    
    def _settle_buff_states(self):
        """结算Buff状态"""
        
        for state in self.p1.buff_states:
            if state.cancelled:
                continue
            
            if state.type == 'charge':
                if state.action == 'gain':
                    self.p1.charge_level = state.value
                    print(f"   {self.p1.name} 获得蓄力{state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p1.charge_level = 0
                    print(f"   {self.p1.name} {'消耗' if state.action == 'consume' else '失去'}蓄力")
            
            elif state.type == 'dash':
                if state.action == 'gain':
                    self.p1.dash_buff_stacks += state.value
                    print(f"   {self.p1.name} 获得冲刺buff（{self.p1.dash_buff_stacks}层）")
                elif state.action == 'consume':
                    self.p1.dash_buff_stacks -= state.value
            
            elif state.type == 'grab_damage':
                if state.action == 'gain':
                    self.p1.grab_damage_buff = state.value
                    print(f"   {self.p1.name} 获得抱摔伤害buff（受伤+{state.value}）")
        
        for state in self.p2.buff_states:
            if state.cancelled:
                continue
            
            if state.type == 'charge':
                if state.action == 'gain':
                    self.p2.charge_level = state.value
                    print(f"   {self.p2.name} 获得蓄力{state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p2.charge_level = 0
                    print(f"   {self.p2.name} {'消耗' if state.action == 'consume' else '失去'}蓄力")
            
            elif state.type == 'dash':
                if state.action == 'gain':
                    self.p2.dash_buff_stacks += state.value
                    print(f"   {self.p2.name} 获得冲刺buff（{self.p2.dash_buff_stacks}层）")
                elif state.action == 'consume':
                    self.p2.dash_buff_stacks -= state.value
            
            elif state.type == 'grab_damage':
                if state.action == 'gain':
                    self.p2.grab_damage_buff = state.value
                    print(f"   {self.p2.name} 获得抱摔伤害buff（受伤+{state.value}）")
    
    def _settle_control_states(self, frame):
        """结算控制状态（拉近、被控制、解除、硬直）"""
        
        for state in self.p1.control_states:
            if state.cancelled:
                continue
            
            if state.type == 'pull':
                self.p1.position = state.target
                print(f"   {self.p1.name} 被拉到位置{state.target}（距离→0）")
            elif state.type == 'controlled':
                self.p1.controlled = True
                self.p1.controller = state.target
                print(f"   {self.p1.name} 被{state.target}控制")
            elif state.type == 'release':
                if self.p1.controlled:
                    self.p1.controlled = False
                    self.p1.controller = None
                    print(f"🔓 {self.p1.name} 解除被控制")
            elif state.type == 'stun':
                print(f"😵 {self.p1.name} 硬直{state.value}帧！")
                self._apply_stun(self.p1, state.value, frame)
        
        for state in self.p2.control_states:
            if state.cancelled:
                continue
            
            if state.type == 'pull':
                self.p2.position = state.target
                print(f"   {self.p2.name} 被拉到位置{state.target}（距离→0）")
            elif state.type == 'controlled':
                self.p2.controlled = True
                self.p2.controller = state.target
                print(f"   {self.p2.name} 被{state.target}控制")
            elif state.type == 'release':
                if self.p2.controlled:
                    self.p2.controlled = False
                    self.p2.controller = None
                    print(f"🔓 {self.p2.name} 解除被控制")
            elif state.type == 'stun':
                print(f"😵 {self.p2.name} 硬直{state.value}帧！")
                self._apply_stun(self.p2, state.value, frame)
    
    def _settle_damage(self):
        """结算伤害"""
        
        # P1受伤
        total_dmg = sum(s.amount for s in self.p1.damage_states if not s.cancelled)
        total_def = sum(s.reduction for s in self.p1.defense_states if not s.cancelled)
        p1_final_dmg = max(0, total_dmg - total_def)
        
        # 冲刺buff加成
        if p1_final_dmg > 0 and self.p1.dash_buff_stacks > 0:
            print(f"🏃 {self.p1.name} 冲锋受伤+{self.p1.dash_buff_stacks}")
            p1_final_dmg += self.p1.dash_buff_stacks
            self.p1.add_buff_state('dash', 'consume', 1)
        
        # 抱摔buff加成
        if p1_final_dmg > 0 and self.p1.grab_damage_buff > 0:
            print(f"🤼 {self.p1.name} 抱摔受伤+{self.p1.grab_damage_buff}")
            p1_final_dmg += self.p1.grab_damage_buff
            self.p1.grab_damage_buff = 0
        
        # 反击伤害
        if self.p1.has_marker('prepare_counter') and p1_final_dmg > 0:
            print(f"⚔️ {self.p1.name} 反击成功！")
            self.p2.add_damage_state(COUNTER_DAMAGE, source=f"{self.p1.name}_counter")
        
        # 应用伤害
        if p1_final_dmg > 0:
            self.p1.hp = max(0, self.p1.hp - p1_final_dmg)
            self.p1.add_marker_state('took_damage')
            print(f"💔 {self.p1.name} 受{p1_final_dmg}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p1.name} 完全格挡！")
        
        # P2受伤
        total_dmg = sum(s.amount for s in self.p2.damage_states if not s.cancelled)
        total_def = sum(s.reduction for s in self.p2.defense_states if not s.cancelled)
        p2_final_dmg = max(0, total_dmg - total_def)
        
        if p2_final_dmg > 0 and self.p2.dash_buff_stacks > 0:
            print(f"🏃 {self.p2.name} 冲锋受伤+{self.p2.dash_buff_stacks}")
            p2_final_dmg += self.p2.dash_buff_stacks
            self.p2.add_buff_state('dash', 'consume', 1)
        
        if p2_final_dmg > 0 and self.p2.grab_damage_buff > 0:
            print(f"🤼 {self.p2.name} 抱摔受伤+{self.p2.grab_damage_buff}")
            p2_final_dmg += self.p2.grab_damage_buff
            self.p2.grab_damage_buff = 0
        
        if self.p2.has_marker('prepare_counter') and p2_final_dmg > 0:
            print(f"⚔️ {self.p2.name} 反击成功！")
            self.p1.add_damage_state(COUNTER_DAMAGE, source=f"{self.p2.name}_counter")
        
        if p2_final_dmg > 0:
            self.p2.hp = max(0, self.p2.hp - p2_final_dmg)
            self.p2.add_marker_state('took_damage')
            print(f"💔 {self.p2.name} 受{p2_final_dmg}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p2.name} 完全格挡！")
        
        # 消耗攻击者buff
        if self.p1.has_marker('dealt_damage') and self.p1.dash_buff_stacks > 0:
            self.p1.dash_buff_stacks -= 1
            print(f"   {self.p1.name}冲刺buff已消耗")
        
        if self.p2.has_marker('dealt_damage') and self.p2.dash_buff_stacks > 0:
            self.p2.dash_buff_stacks -= 1
            print(f"   {self.p2.name}冲刺buff已消耗")
        
        # 更新took_damage标记（用于后续连击判定）
        self.p1.took_damage_this_frame = self.p1.has_marker('took_damage')
        self.p2.took_damage_this_frame = self.p2.has_marker('took_damage')
    
    def _post_check_combo(self, frame):
        """后处理：连击检查"""
        
        # P1被连击
        if self.p1.has_marker('took_damage') and self.p2.has_marker('dealt_damage'):
            if self.p1.is_hit_consecutive(self.turn, frame):
                self.p1.combo_count += 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = frame
                print(f"🎯 {self.p1.name} 连续被击中 {self.p1.combo_count}/3")
                
                if self.p1.combo_count >= COMBO_THRESHOLD:
                    print(f"   触发连击硬直！")
                    self._apply_stun(self.p1, COMBO_STUN_FRAMES, frame)
                    self.p1.combo_count = 0
                    self.p1.last_hit_turn = -1
                    self.p1.last_hit_frame = -1
            else:
                self.p1.combo_count = 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = frame
                print(f"🎯 {self.p1.name} 被击中（不连续）1/3")
        else:
            if self.p1.combo_count > 0:
                print(f"   {self.p1.name} 连击中断，清零")
                self.p1.combo_count = 0
                self.p1.last_hit_turn = -1
                self.p1.last_hit_frame = -1
        
        # P2被连击
        if self.p2.has_marker('took_damage') and self.p1.has_marker('dealt_damage'):
            if self.p2.is_hit_consecutive(self.turn, frame):
                self.p2.combo_count += 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = frame
                print(f"🎯 {self.p2.name} 连续被击中 {self.p2.combo_count}/3")
                
                if self.p2.combo_count >= COMBO_THRESHOLD:
                    print(f"   触发连击硬直！")
                    self._apply_stun(self.p2, COMBO_STUN_FRAMES, frame)
                    self.p2.combo_count = 0
                    self.p2.last_hit_turn = -1
                    self.p2.last_hit_frame = -1
            else:
                self.p2.combo_count = 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = frame
                print(f"🎯 {self.p2.name} 被击中（不连续）1/3")
        else:
            if self.p2.combo_count > 0:
                print(f"   {self.p2.name} 连击中断，清零")
                self.p2.combo_count = 0
                self.p2.last_hit_turn = -1
                self.p2.last_hit_frame = -1
    
    def _post_check_charge_2_stun(self, frame):
        """后处理：蓄力2硬直"""
        if self.p1.has_marker('used_charge_2') and self.p2.has_marker('took_damage'):
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p2, CHARGE_2_STUN_FRAMES, frame)
        
        if self.p2.has_marker('used_charge_2') and self.p1.has_marker('took_damage'):
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p1, CHARGE_2_STUN_FRAMES, frame)
    
    def _apply_stun(self, player, stun_frames, current_frame):
        """施加硬直"""
        turn = self.turn
        frame = current_frame
        
        for _ in range(stun_frames):
            frame += 1
            if frame > 2:
                frame = 1
                turn += 1
            player.lock_frame(turn, frame)
            print(f"   🔒 锁定回合{turn}第{frame}帧")
    
    def get_winner(self):
        if not self.p1.is_alive() and not self.p2.is_alive():
            return "平局"
        elif not self.p1.is_alive():
            return self.p2.name
        elif not self.p2.is_alive():
            return self.p1.name
        return None
    
    def show_final_result(self):
        winner = self.get_winner()
        print(f"\n{'='*60}")
        print(f"🏆 战斗结束！回合数: {self.turn}")
        if winner:
            print(f"胜者: {winner}")
        self.p1.show_status()
        self.p2.show_status()
        print('='*60)