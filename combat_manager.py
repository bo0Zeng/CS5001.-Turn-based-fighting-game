"""
combat_manager.py
战斗管理器 - 7阶段状态化重构版（Bug修复版）

主要修复：
1. 蓄力打断检测移到阶段6.2（有效性检测后）
2. 连击系统移到阶段4（有效性检测后）
3. 删除抱摔的位移和受伤buff
4. 修复控制解除时的位移逻辑
"""

from player import Player
from actions import Actions
from config import *


class CombatManager:
    """战斗管理器 - 7阶段执行流程"""
    
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.turn = 0
        
        self.turn_logs = []
        self.current_turn_messages = []
        
        self.p1_first_frame_action = None
        self.p2_first_frame_action = None
        
        self.current_frame = 1
        
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
        
        self.p1_first_frame_action = None
        self.p2_first_frame_action = None
        
        for frame_idx in range(2):
            frame = frame_idx + 1
            print(f"\n--- 第 {frame} 帧 ---")
            
            self.p1.reset_frame()
            self.p2.reset_frame()
            
            p1_act = p1_actions[frame_idx] if frame_idx < len(p1_actions) else None
            p2_act = p2_actions[frame_idx] if frame_idx < len(p2_actions) else None
            
            # 预处理：检查硬直和控制前置条件
            p1_act = self._preprocess(self.p1, p1_act, frame)
            p2_act = self._preprocess(self.p2, p2_act, frame)
            
            if frame == 1:
                self.p1_first_frame_action = p1_act
                self.p2_first_frame_action = p2_act
            
            self._execute_frame(p1_act, p2_act, frame)
            
            if not self.p1.is_alive() or not self.p2.is_alive():
                return
    
    def _preprocess(self, player, action, frame):
        """预处理行动（硬直检查、grab/throw前置条件）"""
        if not action:
            return None
        
        # 硬直检查
        if player.is_frame_locked(self.turn, frame):
            if action == 'burst':
                print(f"💥 {player.name} 硬直中使用爆血！")
                return action
            else:
                print(f"🔒 {player.name} 第{frame}帧被硬直！")
                return None
        
        # grab/throw前置条件检查
        if action in ['grab', 'throw']:
            opponent = self.p2 if player == self.p1 else self.p1
            first_frame_action = self.p1_first_frame_action if player == self.p1 else self.p2_first_frame_action
            
            can_use = opponent.controlled or (frame == 2 and first_frame_action == 'control')
            
            if not can_use:
                print(f"❌ 对手未被控制，无法使用{action}！")
                return None
        
        return action
    
    def _execute_frame(self, p1_act, p2_act, frame):
        """执行单帧 - 7阶段流程"""
        self.current_frame = frame
        
        # ===== 阶段1：为自身施加状态 =====
        print("\n[阶段1：为自身施加状态]")
        self._stage1_apply_actions(p1_act, p2_act, frame)
        
        # ===== 阶段2：自身状态冲突检测 =====
        print("\n[阶段2：自身状态冲突检测]")
        self._stage2_resolve_conflicts(p1_act, p2_act)
        
        # ===== 阶段3：有效性检测（距离） =====
        print("\n[阶段3：有效性检测]")
        self._stage3_validate_states(p1_act, p2_act)
        
        # ===== 阶段4：连击系统 =====
        print("\n[阶段4：连击系统]")
        self._stage4_combo_system()
        
        # ===== 阶段5：硬直系统 =====
        print("\n[阶段5：硬直系统]")
        self._stage5_stun_system(frame)
        
        # ===== 阶段6：结算系统 =====
        print("\n[阶段6：结算系统]")
        self._stage6_settle_all(p1_act, p2_act, frame)
        
        # ===== 阶段7：控制解除距离调整 =====
        print("\n[阶段7：控制解除距离调整]")
        self._stage7_release_adjustment(frame)
    
    # ========== 阶段1：为自身施加状态 ==========
    def _stage1_apply_actions(self, p1_act, p2_act, frame):
        """阶段1：根据action为自身施加状态"""
        
        # 移动类
        if p1_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p1, p1_act)
        if p2_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p2, p2_act)
        
        # 防御类
        if p1_act in ['defend', 'counter']:
            self._do_defend(self.p1, p1_act)
        if p2_act in ['defend', 'counter']:
            self._do_defend(self.p2, p2_act)
        
        # 蓄力
        if p1_act == 'charge':
            Actions.charge(self.p1, frame, self.turn)
        if p2_act == 'charge':
            Actions.charge(self.p2, frame, self.turn)
        
        # 攻击类（生成对对方的状态）
        if p1_act == 'control':
            Actions.control(self.p1, self.p2)
        elif p1_act == 'grab':
            Actions.grab(self.p1, self.p2)
        elif p1_act == 'throw':
            Actions.throw(self.p1, self.p2)
        elif p1_act == 'attack':
            Actions.attack(self.p1, self.p2)
        
        if p2_act == 'control':
            Actions.control(self.p2, self.p1)
        elif p2_act == 'grab':
            Actions.grab(self.p2, self.p1)
        elif p2_act == 'throw':
            Actions.throw(self.p2, self.p1)
        elif p2_act == 'attack':
            Actions.attack(self.p2, self.p1)
        
        # 爆血（特殊：需要预计算距离）
        if p1_act == 'burst':
            pred_distance = self._predict_distance_after_positions()
            Actions.burst(self.p1, self.p2, pred_distance)
        if p2_act == 'burst':
            pred_distance = self._predict_distance_after_positions()
            Actions.burst(self.p2, self.p1, pred_distance)
    
    # ========== 阶段2：自身状态冲突检测 ==========
    def _stage2_resolve_conflicts(self, p1_act, p2_act):
        """阶段2：检测并移除冲突的状态（不包括蓄力打断）"""
        
        # 被控制者的行动冲突
        self._check_controlled_conflicts(self.p1, self.p2, p1_act)
        self._check_controlled_conflicts(self.p2, self.p1, p2_act)
        
        # 重叠时移动方向限制
        self._check_overlap_move_direction()
        
        # 互相控制取消
        self._check_mutual_control()
    
    def _check_controlled_conflicts(self, player, opponent, action):
        """检查被控制者的状态冲突（被控制时只能defend和burst）"""
        if not player.controlled:
            return
    
        if action not in ['defend', 'burst', None]:
            print(f"⛔️ {player.name} 被控制，{action}行动无效！（只能防御S或爆血O）")
        
            # 移除对对手造成的伤害
            opponent.damage_states = [s for s in opponent.damage_states if s.source != player.name]
        
            # 只移除自己的位置变化（保留别人施加的）
            removed_count = len([s for s in player.position_states if s.source == "self"])
            player.position_states = [s for s in player.position_states if s.source != "self"]
            if removed_count > 0:
                print(f"   取消{player.name}自己的{removed_count}格移动，保留被动位移")
        
            # 移除对对手的控制
            opponent.control_states = [s for s in opponent.control_states if s.type not in ['pull', 'controlled']]
        
            # 移除自己的待定蓄力
            player.buff_states = [s for s in player.buff_states if not (s.type == 'charge' and s.action == 'pending')]
    
    def _check_overlap_move_direction(self):
        """重叠时移动方向限制"""
        if self.get_distance() != 0:
            return
        
        print(f"   检查重叠时移动方向限制")
        
        # P1限制
        for state in list(self.p1.position_states):
            if self.p1.is_left and state.delta > 0:
                self.p1.position_states.remove(state)
                print(f"   ❌ {self.p1.name}是左边玩家，重叠时不能向右移动")
            elif not self.p1.is_left and state.delta < 0:
                self.p1.position_states.remove(state)
                print(f"   ❌ {self.p1.name}是右边玩家，重叠时不能向左移动")
        
        # P2限制
        for state in list(self.p2.position_states):
            if self.p2.is_left and state.delta > 0:
                self.p2.position_states.remove(state)
                print(f"   ❌ {self.p2.name}是左边玩家，重叠时不能向右移动")
            elif not self.p2.is_left and state.delta < 0:
                self.p2.position_states.remove(state)
                print(f"   ❌ {self.p2.name}是右边玩家，重叠时不能向左移动")
    
    def _check_mutual_control(self):
        """检查双方是否互相控制"""
        p1_tried = self.p1.has_marker('tried_control')
        p2_tried = self.p2.has_marker('tried_control')
        
        if p1_tried and p2_tried:
            p1_has_ctrl = any(s.type in ['pull', 'controlled'] for s in self.p2.control_states)
            p2_has_ctrl = any(s.type in ['pull', 'controlled'] for s in self.p1.control_states)
            
            if p1_has_ctrl and p2_has_ctrl:
                print(f"⚔️ 双方同时控制，都取消！")
                self.p1.control_states = [s for s in self.p1.control_states if s.type not in ['pull', 'controlled']]
                self.p2.control_states = [s for s in self.p2.control_states if s.type not in ['pull', 'controlled']]
    
    # ========== 阶段3：有效性检测 ==========
    def _stage3_validate_states(self, p1_act, p2_act):
        """阶段3：检测状态有效性（主要是距离）"""
        
        # 预计算位置
        pred_p1_pos, pred_p2_pos = self._predict_final_positions()
        pred_distance = abs(pred_p1_pos - pred_p2_pos)
        print(f"   预测：{self.p1.name}→{pred_p1_pos}, {self.p2.name}→{pred_p2_pos}, 距离={pred_distance}")
        
        # 攻击距离检查
        self._validate_attack(self.p1, self.p2, pred_distance)
        self._validate_attack(self.p2, self.p1, pred_distance)
        
        # 控制距离检查
        self._validate_control(self.p1, self.p2, pred_distance)
        self._validate_control(self.p2, self.p1, pred_distance)
        
        # 反击有效性
        self._validate_counter(self.p1, self.p2)
        self._validate_counter(self.p2, self.p1)
        
        # 闪避判定
        self._check_dodge(self.p1, self.p2, p1_act, p2_act)
        self._check_dodge(self.p2, self.p1, p2_act, p1_act)
    
    def _validate_attack(self, attacker, defender, pred_distance):
        """验证攻击是否有效"""
        if not attacker.has_marker('tried_attack'):
            return
        
        if pred_distance > attacker.attack_range_this_frame:
            # 移除伤害
            defender.damage_states = [s for s in defender.damage_states if s.source != attacker.name]
            print(f"❌ {attacker.name} 攻击未命中（距离{pred_distance} > 范围{attacker.attack_range_this_frame}）")
        else:
            attacker.add_marker_state('dealt_damage')
            print(f"✅ {attacker.name} 攻击命中！")
    
    def _validate_control(self, attacker, defender, pred_distance):
        """验证控制是否有效"""
        if not attacker.has_marker('tried_control'):
            return
        
        if attacker.controlled:
            # 被控制者无法控制
            defender.control_states = [s for s in defender.control_states if s.type not in ['pull', 'controlled']]
            print(f"❌ {attacker.name} 被控制，无法控制他人")
            attacker.add_control_state('stun', CONTROL_MISS_STUN_FRAMES)
        elif pred_distance > attacker.control_range_this_frame:
            # 距离不够
            defender.control_states = [s for s in defender.control_states if s.type not in ['pull', 'controlled']]
            print(f"❌ {attacker.name} 控制未命中（距离{pred_distance} > 范围{attacker.control_range_this_frame}）")
            attacker.add_control_state('stun', CONTROL_MISS_STUN_FRAMES)
        else:
            # 控制成功，记录被控制前的位置
            print(f"✅ {attacker.name} 控制成功！")
            
            # 记录被控制前的位置（在pull之前记录）
            if defender.controlled_from_position is None:
                defender.controlled_from_position = defender.position
            
            # 取消被控制者的移动
            if defender.position_states:
                defender.position_states.clear()
                print(f"   🔒 {defender.name}的移动被控制取消")
    
    def _validate_counter(self, player, opponent):
        """验证反击是否有效"""
        if not player.has_marker('counter_prepared'):
            return
        
        # 检查是否受到非自伤的攻击
        has_dmg = any(s.source not in ["burst_self", "charge_penalty", "charge_interrupt"] for s in player.damage_states)
        
        if has_dmg:
            player.add_marker_state('counter_ready')
            print(f"⚔️ {player.name} 反击准备就绪！")
            # 对对手施加反击伤害状态
            opponent.add_damage_state(COUNTER_DAMAGE, source=f"{player.name}_counter")
            # ✅ 反击也标记造成伤害（会触发buff消耗）
            player.add_marker_state('dealt_damage')
            print(f"   对{opponent.name}施加反击伤害")
        else:
            print(f"❌ {player.name} 反击失败（未受攻击）！")
            player.add_control_state('stun', COUNTER_FAIL_STUN_FRAMES)
    
    def _check_dodge(self, mover, attacker, mover_act, attacker_act):
        """闪避判定"""
        if attacker_act != 'attack':
            return
        if mover_act not in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            return
        if not attacker.has_marker('tried_attack'):
            return
        
        # 移动前能打到，但伤害被移除了（说明移动后打不到）
        dist_before = abs(mover.position - attacker.position)
        would_hit = (dist_before <= attacker.attack_range_this_frame)
        dmg_removed = not any(s.source == attacker.name for s in mover.damage_states)
        
        if would_hit and dmg_removed:
            print(f"💨 {mover.name} 闪避 {attacker.name} 成功！")
            attacker.add_control_state('stun', DODGE_STUN_FRAMES)
    
    # ========== 阶段4：连击系统 ==========
    def _stage4_combo_system(self):
        """阶段4：检查连击，添加硬直状态"""
        # P1连击检查
        if self.p1.has_marker('took_damage') and self.p2.has_marker('dealt_damage'):
            if self.p1.is_hit_consecutive(self.turn, self.current_frame):
                self.p1.combo_count += 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = self.current_frame
                print(f"🎯 {self.p1.name} 连续被击中 {self.p1.combo_count}/3")
                
                if self.p1.combo_count >= COMBO_THRESHOLD:
                    print(f"   触发连击硬直！")
                    self.p1.add_control_state('stun', COMBO_STUN_FRAMES)
                    self.p1.combo_count = 0
                    self.p1.last_hit_turn = -1
                    self.p1.last_hit_frame = -1
            else:
                self.p1.combo_count = 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = self.current_frame
                print(f"🎯 {self.p1.name} 被击中（不连续）1/3")
        else:
            if self.p1.combo_count > 0:
                print(f"   {self.p1.name} 连击中断，清零")
                self.p1.combo_count = 0
                self.p1.last_hit_turn = -1
                self.p1.last_hit_frame = -1
        
        # P2连击检查
        if self.p2.has_marker('took_damage') and self.p1.has_marker('dealt_damage'):
            if self.p2.is_hit_consecutive(self.turn, self.current_frame):
                self.p2.combo_count += 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = self.current_frame
                print(f"🎯 {self.p2.name} 连续被击中 {self.p2.combo_count}/3")
                
                if self.p2.combo_count >= COMBO_THRESHOLD:
                    print(f"   触发连击硬直！")
                    self.p2.add_control_state('stun', COMBO_STUN_FRAMES)
                    self.p2.combo_count = 0
                    self.p2.last_hit_turn = -1
                    self.p2.last_hit_frame = -1
            else:
                self.p2.combo_count = 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = self.current_frame
                print(f"🎯 {self.p2.name} 被击中（不连续）1/3")
        else:
            if self.p2.combo_count > 0:
                print(f"   {self.p2.name} 连击中断，清零")
                self.p2.combo_count = 0
                self.p2.last_hit_turn = -1
                self.p2.last_hit_frame = -1
    
    # ========== 阶段5：硬直系统 ==========
    def _stage5_stun_system(self, frame):
        """阶段5：处理各种硬直状态（立即应用）"""
        
        # 应用硬直
        for state in self.p1.control_states:
            if state.type == 'stun':
                print(f"😵 {self.p1.name} 硬直{state.value}帧！")
                self._apply_stun(self.p1, state.value, frame)
        
        for state in self.p2.control_states:
            if state.type == 'stun':
                print(f"😵 {self.p2.name} 硬直{state.value}帧！")
                self._apply_stun(self.p2, state.value, frame)
        
        # 移除已处理的stun状态
        self.p1.control_states = [s for s in self.p1.control_states if s.type != 'stun']
        self.p2.control_states = [s for s in self.p2.control_states if s.type != 'stun']
    
    # ========== 阶段6：结算系统 ==========
    def _stage6_settle_all(self, p1_act, p2_act, frame):
        """阶段6：结算所有状态"""
        
        # 6.1 结算标记
        print("\n[6.1 结算标记]")
        self._settle_markers()
        
        # 6.2 结算Buff（包括蓄力打断检查）
        print("\n[6.2 结算Buff]")
        self._settle_buffs()
        
        # 6.3 结算控制（pull和controlled）
        print("\n[6.3 结算控制]")
        self._settle_control()
        
        # 6.4 结算位置
        print("\n[6.4 结算位置]")
        self._settle_positions(p1_act, p2_act)
        
        # 6.5 结算伤害
        print("\n[6.5 结算伤害]")
        self._settle_damage()
        
        # 6.6 后处理：蓄力2硬直
        print("\n[6.6 后处理]")
        self._post_check_charge_2_stun(frame)
    
    def _settle_markers(self):
        """结算标记状态"""
        self.p1.tried_attack_this_frame = self.p1.has_marker('tried_attack')
        self.p1.dealt_damage_this_frame = self.p1.has_marker('dealt_damage')
        self.p1.used_charge_2_this_frame = self.p1.has_marker('used_charge_2')
        
        self.p2.tried_attack_this_frame = self.p2.has_marker('tried_attack')
        self.p2.dealt_damage_this_frame = self.p2.has_marker('dealt_damage')
        self.p2.used_charge_2_this_frame = self.p2.has_marker('used_charge_2')
    
    def _settle_buffs(self):
        """结算Buff状态（包括蓄力打断检查）"""
        # P1 Buff结算
        for state in self.p1.buff_states:
            if state.type == 'charge':
                if state.action == 'pending':
                    # 检查蓄力是否被打断（在这里检查）
                    has_non_self_dmg = any(
                        s.source not in ["burst_self", "charge_penalty", "charge_interrupt"] 
                        for s in self.p1.damage_states
                    )
                    has_ctrl = any(s.type == 'controlled' for s in self.p1.control_states)
                    
                    if has_non_self_dmg or has_ctrl:
                        print(f"⚡ {self.p1.name} 蓄力被打断（{'被控制' if has_ctrl else '被攻击'}）！")
                        self.p1.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="charge_interrupt")
                        if self.p1.charge_level > 0:
                            self.p1.charge_level = 0
                            print(f"   失去已有蓄力")
                        # pending状态被打断，不生效
                        continue
                    
                    # 蓄力成功
                    self.p1.charge_level = state.value
                    print(f"   {self.p1.name} 获得蓄力{state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p1.charge_level = 0
                    print(f"   {self.p1.name} {'消耗' if state.action == 'consume' else '失去'}蓄力")
        
        # P2 Buff结算
        for state in self.p2.buff_states:
            if state.type == 'charge':
                if state.action == 'pending':
                    # 检查蓄力是否被打断（在这里检查）
                    has_non_self_dmg = any(
                        s.source not in ["burst_self", "charge_penalty", "charge_interrupt"] 
                        for s in self.p2.damage_states
                    )
                    has_ctrl = any(s.type == 'controlled' for s in self.p2.control_states)
                    
                    if has_non_self_dmg or has_ctrl:
                        print(f"⚡ {self.p2.name} 蓄力被打断（{'被控制' if has_ctrl else '被攻击'}）！")
                        self.p2.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="charge_interrupt")
                        if self.p2.charge_level > 0:
                            self.p2.charge_level = 0
                            print(f"   失去已有蓄力")
                        # pending状态被打断，不生效
                        continue
                    
                    # 蓄力成功
                    self.p2.charge_level = state.value
                    print(f"   {self.p2.name} 获得蓄力{state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p2.charge_level = 0
                    print(f"   {self.p2.name} {'消耗' if state.action == 'consume' else '失去'}蓄力")
    
    def _settle_control(self):
        """结算控制状态（pull和controlled）"""
        # Pull（绕过位置状态系统，使用控制者的当前位置）
        for state in self.p1.control_states:
            if state.type == 'pull':
                controller = self.p1 if state.target == self.p1.name else self.p2
                self.p1.position = controller.position
                print(f"   🔗 {self.p1.name} 被强制拉到{controller.position}（{controller.name}当前位置）")
                break
        
        for state in self.p2.control_states:
            if state.type == 'pull':
                controller = self.p1 if state.target == self.p1.name else self.p2
                self.p2.position = controller.position
                print(f"   🔗 {self.p2.name} 被强制拉到{controller.position}（{controller.name}当前位置）")
                break
        
        # Controlled（记录控制开始的时刻）
        for state in self.p1.control_states:
            if state.type == 'controlled':
                self.p1.controlled = True
                self.p1.controller = state.target
                self.p1.controlled_turn = self.turn
                self.p1.controlled_frame = self.current_frame
                print(f"   {self.p1.name} 被{state.target}控制")
        
        for state in self.p2.control_states:
            if state.type == 'controlled':
                self.p2.controlled = True
                self.p2.controller = state.target
                self.p2.controlled_turn = self.turn
                self.p2.controlled_frame = self.current_frame
                print(f"   {self.p2.name} 被{state.target}控制")
        
        # 移除已处理的pull和controlled
        self.p1.control_states = [s for s in self.p1.control_states if s.type not in ['pull', 'controlled']]
        self.p2.control_states = [s for s in self.p2.control_states if s.type not in ['pull', 'controlled']]
    
    def _settle_positions(self, p1_act, p2_act):
        """结算位置（处理冲突）"""
        if not self.p1.position_states and not self.p2.position_states:
            return
        
        p1_initial = self.p1.position
        p2_initial = self.p2.position
        
        p1_final, p2_final, p1_active, p2_active = self._resolve_positions_core(
            self.p1.position_states, self.p2.position_states, p1_initial, p2_initial
        )
        
        # 应用位置
        if p1_final != p1_initial:
            print(f"✅ {self.p1.name} 移动：{p1_initial}→{p1_final} (成功{p1_active}/{len(self.p1.position_states)})")
            self.p1.position = p1_final
        elif self.p1.position_states:
            print(f"❌ {self.p1.name} 移动失败（0/{len(self.p1.position_states)}）")
        
        if p2_final != p2_initial:
            print(f"✅ {self.p2.name} 移动：{p2_initial}→{p2_final} (成功{p2_active}/{len(self.p2.position_states)})")
            self.p2.position = p2_final
        elif self.p2.position_states:
            print(f"❌ {self.p2.name} 移动失败（0/{len(self.p2.position_states)}）")
        
        # 冲刺buff：直接获得（像蓄力一样立即生效）
        if p1_act in ['dash_left', 'dash_right'] and p1_active > 0:
            if self.p1.dash_buff_stacks < DASH_MAX_STACKS:
                self.p1.dash_buff_stacks += 1
                print(f"🏃 {self.p1.name} 获得冲刺buff（{self.p1.dash_buff_stacks}层）")
        
        if p2_act in ['dash_left', 'dash_right'] and p2_active > 0:
            if self.p2.dash_buff_stacks < DASH_MAX_STACKS:
                self.p2.dash_buff_stacks += 1
                print(f"🏃 {self.p2.name} 获得冲刺buff（{self.p2.dash_buff_stacks}层）")
    
    def _settle_damage(self):
        """结算伤害"""
        # P1伤害结算
        total_dmg = sum(s.amount for s in self.p1.damage_states)
        total_def = sum(s.reduction for s in self.p1.defense_states)
        p1_final = max(0, total_dmg - total_def)
        
        if p1_final > 0 and self.p1.dash_buff_stacks > 0:
            print(f"🏃 {self.p1.name} 冲锋受伤+{self.p1.dash_buff_stacks}")
            p1_final += self.p1.dash_buff_stacks
            self.p1.add_buff_state('dash', 'consume', 1)
        
        if self.p1.has_marker('counter_ready') and p1_final > 0:
            print(f"⚔️ {self.p1.name} 反击成功！")
            self.p2.add_damage_state(COUNTER_DAMAGE, source=f"{self.p1.name}_counter")
        
        if p1_final > 0:
            self.p1.hp = max(0, self.p1.hp - p1_final)
            self.p1.add_marker_state('took_damage')
            print(f"💔 {self.p1.name} 受{p1_final}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p1.name} 完全格挡！")
        
        # P2伤害结算
        total_dmg = sum(s.amount for s in self.p2.damage_states)
        total_def = sum(s.reduction for s in self.p2.defense_states)
        p2_final = max(0, total_dmg - total_def)
        
        if p2_final > 0 and self.p2.dash_buff_stacks > 0:
            print(f"🏃 {self.p2.name} 冲锋受伤+{self.p2.dash_buff_stacks}")
            p2_final += self.p2.dash_buff_stacks
            self.p2.add_buff_state('dash', 'consume', 1)
        
        if self.p2.has_marker('counter_ready') and p2_final > 0:
            print(f"⚔️ {self.p2.name} 反击成功！")
            self.p1.add_damage_state(COUNTER_DAMAGE, source=f"{self.p2.name}_counter")
        
        if p2_final > 0:
            self.p2.hp = max(0, self.p2.hp - p2_final)
            self.p2.add_marker_state('took_damage')
            print(f"💔 {self.p2.name} 受{p2_final}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p2.name} 完全格挡！")
        
        # 造成伤害后消耗冲刺buff
        if self.p1.has_marker('dealt_damage') and self.p1.dash_buff_stacks > 0:
            self.p1.dash_buff_stacks -= 1
            print(f"   {self.p1.name}冲刺buff已消耗")
        
        if self.p2.has_marker('dealt_damage') and self.p2.dash_buff_stacks > 0:
            self.p2.dash_buff_stacks -= 1
            print(f"   {self.p2.name}冲刺buff已消耗")
        
        # 记录受伤标记
        self.p1.took_damage_this_frame = self.p1.has_marker('took_damage')
        self.p2.took_damage_this_frame = self.p2.has_marker('took_damage')
    
    def _post_check_charge_2_stun(self, frame):
        """后处理：蓄力2硬直"""
        if self.p1.has_marker('used_charge_2') and self.p2.has_marker('took_damage'):
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p2, CHARGE_2_STUN_FRAMES, frame)
        
        if self.p2.has_marker('used_charge_2') and self.p1.has_marker('took_damage'):
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p1, CHARGE_2_STUN_FRAMES, frame)
    
    # ========== 阶段7：控制解除距离调整 ==========
    def _stage7_release_adjustment(self, current_frame):
        """阶段7：处理控制解除后的距离调整"""
        p1_has_release = any(s.type == 'release' for s in self.p1.control_states)
        p2_has_release = any(s.type == 'release' for s in self.p2.control_states)
        
        # 帧结束自动解除控制（只在"下一帧"才解除）
        if self.p1.controlled:
            self._auto_release_control(self.p1, current_frame)
        if self.p2.controlled:
            self._auto_release_control(self.p2, current_frame)
        
        # 技能触发的解除（grab/throw/burst）
        if p1_has_release or p2_has_release:
            self._handle_skill_release(p1_has_release, p2_has_release)
        
        # 清除release标记
        self.p1.control_states = [s for s in self.p1.control_states if s.type != 'release']
        self.p2.control_states = [s for s in self.p2.control_states if s.type != 'release']
    
    def _auto_release_control(self, player, current_frame):
        """帧结束时自动解除控制"""
        if not player.controlled:
            return
        
        # 检查是否是"下一帧"（控制持续跨帧）
        is_next_frame = False
        
        # 同回合下一帧
        if self.turn == player.controlled_turn and current_frame == player.controlled_frame + 1:
            is_next_frame = True
        # 跨回合下一帧
        elif self.turn == player.controlled_turn + 1 and player.controlled_frame == 2 and current_frame == 1:
            is_next_frame = True
        
        if not is_next_frame:
            # 还不是下一帧，不解除
            return
        
        print(f"   🔓 {player.name}控制状态帧结束解除")
        
        distance = self.get_distance()
        
        if distance != 0:
            print(f"   距离{distance}≠0，无需位置调整")
            player.controlled = False
            player.controller = None
            player.controlled_from_position = None
            player.controlled_turn = -1
            player.controlled_frame = -1
            return
        
        print(f"   距离为0，检查是否需要位置调整")
        
        p1_took_damage = self.p1.took_damage_this_frame
        p2_took_damage = self.p2.took_damage_this_frame
        
        if p1_took_damage and p2_took_damage:
            print(f"   双方都受伤，都后退一格")
            self._retreat_player(self.p1)
            self._retreat_player(self.p2)
        elif p1_took_damage:
            print(f"   {self.p1.name}受伤，后退一格")
            self._retreat_player(self.p1)
        elif p2_took_damage:
            print(f"   {self.p2.name}受伤，后退一格")
            self._retreat_player(self.p2)
        else:
            # 无人受伤，被控制者后退
            if player.controlled_from_position is not None:
                print(f"   {player.name}被控制无受伤，后退一格")
                player.position = player.controlled_from_position
                print(f"   {player.name} 回到{player.position}")
        
        player.controlled = False
        player.controller = None
        player.controlled_from_position = None
        player.controlled_turn = -1
        player.controlled_frame = -1
    
    def _handle_skill_release(self, p1_has_release, p2_has_release):
        """处理技能触发的控制解除"""
        distance = self.get_distance()
        
        if distance != 0:
            print(f"   grab/throw/burst解除：距离{distance}≠0，无需调整")
            if p1_has_release:
                self.p1.controlled = False
                self.p1.controller = None
                self.p1.controlled_from_position = None
                self.p1.controlled_turn = -1
                self.p1.controlled_frame = -1
            if p2_has_release:
                self.p2.controlled = False
                self.p2.controller = None
                self.p2.controlled_from_position = None
                self.p2.controlled_turn = -1
                self.p2.controlled_frame = -1
            return
        
        print(f"   grab/throw/burst解除：距离为0，需要调整")
        
        p1_took = self.p1.took_damage_this_frame
        p2_took = self.p2.took_damage_this_frame
        
        if p1_took and p2_took:
            # 双方都受伤，都后退
            print(f"   双方都受伤，都后退一格")
            self._retreat_player(self.p1)
            self._retreat_player(self.p2)
        elif p1_took:
            # 只有P1受伤
            print(f"   {self.p1.name}受伤，后退一格")
            self._retreat_player(self.p1)
        elif p2_took:
            # 只有P2受伤
            print(f"   {self.p2.name}受伤，后退一格")
            self._retreat_player(self.p2)
        else:
            # 无人受伤，被控制者后退
            if p1_has_release and self.p1.controlled_from_position is not None:
                print(f"   {self.p1.name}被控制无受伤，后退一格")
                self.p1.position = self.p1.controlled_from_position
            if p2_has_release and self.p2.controlled_from_position is not None:
                print(f"   {self.p2.name}被控制无受伤，后退一格")
                self.p2.position = self.p2.controlled_from_position
        
        if p1_has_release:
            self.p1.controlled = False
            self.p1.controller = None
            self.p1.controlled_from_position = None
            self.p1.controlled_turn = -1
            self.p1.controlled_frame = -1
        if p2_has_release:
            self.p2.controlled = False
            self.p2.controller = None
            self.p2.controlled_from_position = None
            self.p2.controlled_turn = -1
            self.p2.controlled_frame = -1
    
    def _retreat_player(self, player):
        """让玩家后退一格（根据方向和是否被控制）"""
        if player.controlled_from_position is not None:
            # 被控制者：回到被控制前的位置
            player.position = player.controlled_from_position
            print(f"   {player.name} 回到被控制前位置{player.position}")
        else:
            # 非被控制者：按方向后退
            retreat_delta = -1 if player.is_left else 1
            new_pos = player.position + retreat_delta
            new_pos = max(1, min(MAP_SIZE, new_pos))  # 边界检查
            player.position = new_pos
            print(f"   {player.name} 按方向后退到{player.position}")
    
    # ========== 辅助方法 ==========
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
    
    def _predict_distance_after_positions(self):
        """预测位置结算后的距离（用于爆血）"""
        pred_p1, pred_p2 = self._predict_final_positions()
        return abs(pred_p1 - pred_p2)
    
    def _predict_final_positions(self):
        """预计算最终位置"""
        p1_pos, p2_pos, _, _ = self._resolve_positions_core(
            self.p1.position_states,
            self.p2.position_states,
            self.p1.position,
            self.p2.position
        )
        return p1_pos, p2_pos
    
    def _resolve_positions_core(self, p1_states, p2_states, p1_initial, p2_initial):
        """核心冲突检测算法（不修改状态，只返回结果）"""
        if not p1_states and not p2_states:
            return p1_initial, p2_initial, 0, 0
        
        p1_active = len(p1_states)
        p2_active = len(p2_states)
        
        while True:
            p1_pos = p1_initial + sum(p1_states[i].delta for i in range(p1_active))
            p2_pos = p2_initial + sum(p2_states[i].delta for i in range(p2_active))
            
            p1_pos = max(1, min(MAP_SIZE, p1_pos))
            p2_pos = max(1, min(MAP_SIZE, p2_pos))
            
            has_conflict = False
            
            if p1_pos == p2_pos:
                is_control_overlap = (
                    (self.p1.controlled or self.p2.controlled) and
                    p1_initial == p2_initial
                )
                if not is_control_overlap:
                    has_conflict = True
            
            if not has_conflict:
                if p1_initial < p2_initial and p1_pos > p2_pos:
                    has_conflict = True
                elif p2_initial < p1_initial and p2_pos > p1_pos:
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