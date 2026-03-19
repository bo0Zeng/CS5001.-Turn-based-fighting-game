from player import Player
from actions import Actions
from config import *


class CombatManager:
    """战斗管理器 - 7阶段执行流程 / Combat Manager - 7-Phase Execution Flow"""

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
        """执行一个完整回合（2帧）/ Execute a complete turn (2 frames)"""
        self.turn += 1
        print(f"\n{'='*60}")
        print(f"回合 {self.turn} | 距离: {self.get_distance()}格 / Turn {self.turn} | Distance: {self.get_distance()} cells")
        self.p1.show_status()
        self.p2.show_status()
        print('='*60)
        
        self.p1.clear_old_locks(self.turn)
        self.p2.clear_old_locks(self.turn)
        
        self.p1_first_frame_action = None
        self.p2_first_frame_action = None
        
        for frame_idx in range(2):
            frame = frame_idx + 1
            print(f"\n--- 第 {frame} 帧 / Frame {frame} ---")
            
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
                print(f"{player.name} 硬直中使用爆血 / {player.name} uses burst while stunned")
                return action
            else:
                print(f"{player.name} 第{frame}帧被硬直 / {player.name} frame {frame} stunned")
                return None
        
        # grab/throw前置条件检查
        if action in ['grab', 'throw']:
            opponent = self.p2 if player == self.p1 else self.p1
            
            # 只检查对手当前是否被控制（移除了错误的"第1帧control第2帧可用"逻辑）
            can_use = opponent.controlled
            
            if not can_use:
                print(f"{player.name} 无法使用{action}（对手未被控制）/ {player.name} cannot use {action} (opponent not controlled)")
                return None
        
        return action

    def _execute_frame(self, p1_act, p2_act, frame):
        """执行单帧 - 7阶段流程"""
        self.current_frame = frame
        
        # 阶段1：为自身施加状态
        print("\n[P1.施加状态 / Apply states]")
        self._stage1_apply_actions(p1_act, p2_act, frame)
        
        # 阶段2：自身状态冲突检测
        print("\n[P2.冲突检测 / Conflict detection]")
        self._stage2_resolve_conflicts(p1_act, p2_act)
        
        # 阶段3：生效检测并为对方添加状态
        print("\n[P3.生效检测 / Effectiveness check]")
        self._stage3_validate_and_apply(p1_act, p2_act)
        
        # 阶段4：连击系统
        print("\n[P4.连击系统 / Combo system]")
        self._stage4_combo_system()
        
        # 阶段5：硬直系统
        print("\n[P5.硬直系统 / Stun system]")
        self._stage5_stun_system(frame)
        
        # 阶段6：结算系统
        print("\n[P6.结算系统 / Settlement system]")
        self._stage6_settle_all(p1_act, p2_act, frame)
        
        # 阶段7：控制解除距离调整
        print("\n[P7.控制解除 / Control release]")
        self._stage7_release_adjustment(frame)

    # ========== 阶段1：为自身施加状态 ==========
    def _stage1_apply_actions(self, p1_act, p2_act, frame):
        """阶段1：根据action为自身施加状态（只生成do_xxx）"""
        
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
        
        # 攻击类（只生成do状态）
        if p1_act == 'control':
            Actions.control(self.p1)
        elif p1_act == 'grab':
            Actions.grab(self.p1)
        elif p1_act == 'throw':
            Actions.throw(self.p1)
        elif p1_act == 'attack':
            Actions.attack(self.p1)
        
        if p2_act == 'control':
            Actions.control(self.p2)
        elif p2_act == 'grab':
            Actions.grab(self.p2)
        elif p2_act == 'throw':
            Actions.throw(self.p2)
        elif p2_act == 'attack':
            Actions.attack(self.p2)
        
        # 爆血
        if p1_act == 'burst':
            Actions.burst(self.p1)
            self.p2.add_control_state('release')  # 解除对方控制
        if p2_act == 'burst':
            Actions.burst(self.p2)
            self.p1.add_control_state('release')  # 解除对方控制

    # ========== 阶段2：自身状态冲突检测 ==========
    def _stage2_resolve_conflicts(self, p1_act, p2_act):
        """阶段2：检测并移除冲突的状态"""
        
        # 被控制者的行动冲突
        self._check_controlled_conflicts(self.p1, self.p2, p1_act)
        self._check_controlled_conflicts(self.p2, self.p1, p2_act)
        
        # 重叠时移动方向限制
        self._check_overlap_move_direction()
        
        # 互相控制取消
        self._check_mutual_control()

    def _check_controlled_conflicts(self, player, opponent, action):
        """检查被控制者的状态冲突"""
        if not player.controlled:
            return
        
        if action not in ['defend', 'burst', None]:
            print(f"{player.name} 被控制，{action}无效（仅S/O）/ {player.name} controlled, {action} invalid (only S/O)")
            
            # 移除do状态
            player.action_states = [s for s in player.action_states 
                                   if not s.type.startswith('do_')]
            
            # 只移除自己的位置变化
            removed_count = len([s for s in player.position_states if s.source == "self"])
            player.position_states = [s for s in player.position_states if s.source != "self"]
            if removed_count > 0:
                print(f"  取消{player.name}自身{removed_count}格移动 / Cancel {player.name}'s own {removed_count} tiles movement")
            
            # 移除自己的待定蓄力
            player.buff_states = [s for s in player.buff_states 
                                 if not (s.type == 'charge' and s.action == 'pending')]

    def _check_overlap_move_direction(self):
        """重叠时移动方向限制"""
        if self.get_distance() != 0:
            return
        
        print(f"  距离0，检查移动限制 / Distance 0, check move restrictions")
        
        # P1限制
        for state in list(self.p1.position_states):
            if self.p1.is_left and state.delta > 0:
                self.p1.position_states.remove(state)
                print(f"  {self.p1.name}左侧，不能右移 / {self.p1.name} left side, cannot move right")
            elif not self.p1.is_left and state.delta < 0:
                self.p1.position_states.remove(state)
                print(f"  {self.p1.name}右侧，不能左移 / {self.p1.name} right side, cannot move left")
        
        # P2限制
        for state in list(self.p2.position_states):
            if self.p2.is_left and state.delta > 0:
                self.p2.position_states.remove(state)
                print(f"  {self.p2.name}左侧，不能右移 / {self.p2.name} left side, cannot move right")
            elif not self.p2.is_left and state.delta < 0:
                self.p2.position_states.remove(state)
                print(f"  {self.p2.name}右侧，不能左移 / {self.p2.name} right side, cannot move left")

    def _check_mutual_control(self):
        """互相控制取消"""
        p1_tried = self.p1.has_action('do_control')
        p2_tried = self.p2.has_action('do_control')
        
        if p1_tried and p2_tried:
            print(f"双方同时控制，都取消 / Both control simultaneously, both canceled")
            # 移除do_control状态
            self.p1.action_states = [s for s in self.p1.action_states if s.type != 'do_control']
            self.p2.action_states = [s for s in self.p2.action_states if s.type != 'do_control']

    # ========== 阶段3：生效检测并为对方添加状态 ==========
    def _stage3_validate_and_apply(self, p1_act, p2_act):
        """阶段3：验证有效性，为对方添加 be_xxx状态和实际伤害"""
        
        # 第一次预测（不含pull，用于验证）
        pred_p1_pos, pred_p2_pos = self._predict_final_positions(include_pull=False)
        pred_distance = abs(pred_p1_pos - pred_p2_pos)
        print(f"  预测位置（第一次）：{self.p1.name}->{pred_p1_pos}, {self.p2.name}->{pred_p2_pos}, 距离={pred_distance}")
        print(f"  Predicted pos (1st): {self.p1.name}->{pred_p1_pos}, {self.p2.name}->{pred_p2_pos}, dist={pred_distance}")
        
        # 验证并施加攻击
        self._validate_and_apply_attack(self.p1, self.p2, pred_distance)
        self._validate_and_apply_attack(self.p2, self.p1, pred_distance)
        
        # 验证并施加控制
        self._validate_and_apply_control(self.p1, self.p2, pred_distance)
        self._validate_and_apply_control(self.p2, self.p1, pred_distance)
        
        # 验证并施加 grab/throw
        self._validate_and_apply_grab_throw(self.p1, self.p2)
        self._validate_and_apply_grab_throw(self.p2, self.p1)
        
        # 验证反击
        self._validate_counter(self.p1, self.p2)
        self._validate_counter(self.p2, self.p1)
        
        # 闪避判定
        self._check_dodge(self.p1, self.p2, p1_act, p2_act)
        self._check_dodge(self.p2, self.p1, p2_act, p1_act)
        
        # 第二次预测（含pull，用于爆血）
        final_p1_pos, final_p2_pos = self._predict_final_positions(include_pull=True)
        final_distance = abs(final_p1_pos - final_p2_pos)
        if final_distance != pred_distance:
            print(f"  预测位置（第二次，含pull）：{self.p1.name}->{final_p1_pos}, {self.p2.name}->{final_p2_pos}, 距离={final_distance}")
            print(f"  Predicted pos (2nd, with pull): {self.p1.name}->{final_p1_pos}, {self.p2.name}->{final_p2_pos}, dist={final_distance}")
        
        # 验证并施加爆血
        self._validate_and_apply_burst(self.p1, self.p2, final_distance)
        self._validate_and_apply_burst(self.p2, self.p1, final_distance)

    def _validate_and_apply_attack(self, attacker, defender, pred_distance):
        """验证攻击并为对方添加 be_attacked和伤害状态"""
        if not attacker.has_action('do_attack'):
            return
        
        # 获取基础属性
        base_range = attacker.get_action_value('do_attack')
        base_damage = ATTACK_DAMAGE
        
        # 计算蓄力加成
        attack_range = base_range
        damage = base_damage
        
        if attacker.charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
            damage += CHARGE_1_DAMAGE_BONUS
            print(f"  {attacker.name} 蓄力1加成：范围+{CHARGE_1_RANGE_BONUS}，伤害+{CHARGE_1_DAMAGE_BONUS}")
            print(f"  {attacker.name} Charge1 bonus: range+{CHARGE_1_RANGE_BONUS}, damage+{CHARGE_1_DAMAGE_BONUS}")
            attacker.add_buff_state('charge', 'consume')
        elif attacker.charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
            damage += CHARGE_2_DAMAGE_BONUS
            print(f"  {attacker.name} 蓄力2加成：范围+{CHARGE_2_RANGE_BONUS}，伤害+{CHARGE_2_DAMAGE_BONUS}+硬直")
            print(f"  {attacker.name} Charge2 bonus: range+{CHARGE_2_RANGE_BONUS}, damage+{CHARGE_2_DAMAGE_BONUS}+stun")
            attacker.add_buff_state('charge', 'consume')
            attacker.add_action_state('used_charge_2')
        
        # 计算冲刺加成
        if attacker.dash_buff_stacks > 0:
            damage += attacker.dash_buff_stacks
            print(f"  冲锋加成！伤害+{attacker.dash_buff_stacks} / Dash bonus! damage+{attacker.dash_buff_stacks}")
        
        # 验证距离
        if pred_distance > attack_range:
            print(f"{attacker.name} 攻击未命中（距离{pred_distance}>范围{attack_range}）")
            print(f"{attacker.name} attack missed (dist{pred_distance}>range{attack_range})")
        else:
            print(f"{attacker.name} 攻击命中（距离{pred_distance}<=范围{attack_range}，伤害{damage}）")
            print(f"{attacker.name} attack hit (dist{pred_distance}<=range{attack_range}, damage{damage})")
            
            # 为对方添加 be_attacked和伤害状态
            defender.add_action_state('be_attacked', damage)
            defender.add_damage_state(damage, source=attacker.name)
            
            # 标记造成伤害
            attacker.add_action_state('dealt_damage')
            # ✅ 不在这里设置took_damage，留到阶段6结算

    def _validate_and_apply_control(self, attacker, defender, pred_distance):
        """验证控制并为对方添加 be_controlled状态"""
        if not attacker.has_action('do_control'):
            return
        
        control_range = attacker.get_action_value('do_control')
        
        if attacker.controlled:
            print(f"{attacker.name} 被控制，无法控制他人 / {attacker.name} controlled, cannot control others")
            attacker.add_control_state('stun', CONTROL_MISS_STUN_FRAMES)
        elif pred_distance > control_range:
            print(f"{attacker.name} 控制未命中（距离{pred_distance}>范围{control_range}）")
            print(f"{attacker.name} control missed (dist{pred_distance}>range{control_range})")
            attacker.add_control_state('stun', CONTROL_MISS_STUN_FRAMES)
        else:
            print(f"{attacker.name} 控制成功 / {attacker.name} control successful")
            
            # 为对方添加 be_controlled和pull状态
            defender.add_action_state('be_controlled')
            defender.add_control_state('controlled', target=attacker.name)
            defender.add_control_state('pull', target=attacker.name)
            print(f"  生成pull状态 / Generate pull state")
            
            # 记录被控制前的位置
            if defender.controlled_from_position is None:
                defender.controlled_from_position = defender.position
            
            # 取消被控制者的移动
            if defender.position_states:
                defender.position_states.clear()
                print(f"  {defender.name}移动被控制取消 / {defender.name}'s movement canceled by control")

    def _validate_and_apply_grab_throw(self, attacker, defender):
        """验证并施加 grab/throw"""
        if attacker.has_action('do_grab'):
            damage = attacker.get_action_value('do_grab')
            print(f"{attacker.name} 抱摔 {defender.name}！伤害{damage}")
            print(f"{attacker.name} grabs {defender.name}! damage {damage}")
            
            defender.add_action_state('be_grabbed', damage)
            defender.add_damage_state(damage, source=attacker.name)
            attacker.add_action_state('dealt_damage')
            # ✅ 不在这里设置took_damage
            
            # 立即解除控制
            defender.add_control_state('release')
        
        if attacker.has_action('do_throw'):
            damage = attacker.get_action_value('do_throw')
            print(f"{attacker.name} 投掷 {defender.name}！伤害{damage}")
            print(f"{attacker.name} throws {defender.name}! damage {damage}")
            
            defender.add_action_state('be_thrown', damage)
            defender.add_damage_state(damage, source=attacker.name)
            attacker.add_action_state('dealt_damage')
            # ✅ 不在这里设置took_damage
            
            # 添加位移
            throw_delta = -1 if defender.is_left else 1
            for _ in range(THROW_DISTANCE):
                defender.add_position_state(throw_delta, source=attacker.name)
            
            # 立即解除控制
            defender.add_control_state('release')

    def _validate_counter(self, player, opponent):
        """验证反击是否有效"""
        if not player.has_action('do_counter'):
            return
        
        # 检查是否受到非自伤的攻击
        has_dmg = any(not s.source.endswith("_self") for s in player.damage_states)
        
        if has_dmg:
            player.add_action_state('counter_ready')
            print(f"{player.name} 反击准备就绪 / {player.name} counter ready")
            
            # 对对手施加反击伤害
            opponent.add_action_state('be_countered', COUNTER_DAMAGE)
            opponent.add_damage_state(COUNTER_DAMAGE, source=f"{player.name}_counter")
            player.add_action_state('dealt_damage')
            # ✅ 不在这里设置took_damage
            print(f"  对{opponent.name}施加反击伤害 / Apply counter damage to {opponent.name}")
        else:
            print(f"{player.name} 反击失败（未受攻击）/ {player.name} counter failed (not attacked)")
            player.add_control_state('stun', COUNTER_FAIL_STUN_FRAMES)

    def _validate_and_apply_burst(self, attacker, defender, distance):
        """验证并施加爆血"""
        if not attacker.has_action('do_burst'):
            return
        
        print(f"{attacker.name} 爆血生效（距离{distance}）/ {attacker.name} burst takes effect (dist{distance})")
        
        # 自损
        self_damage = BURST_SELF_DAMAGE + distance
        attacker.add_action_state('burst_self', self_damage)
        attacker.add_damage_state(self_damage, source="burst_self")
        # ✅ 不在这里设置took_damage（自伤不计入连击）
        print(f"   {attacker.name}自损{self_damage}(3+{distance}距离) / {attacker.name} self-damage {self_damage}(3+{distance} dist)")
        
        # 敌伤
        enemy_damage = max(0, BURST_BASE_DAMAGE - distance)
        if enemy_damage > 0:
            defender.add_action_state('be_bursted', enemy_damage)
            defender.add_damage_state(enemy_damage, source=attacker.name)
            attacker.add_action_state('dealt_damage')
            # ✅ 不在这里设置took_damage
            print(f"   {defender.name}受{enemy_damage}伤(6-{distance}距离) / {defender.name} takes {enemy_damage} damage(6-{distance} dist)")
        else:
            print(f"   距离过远，无法伤敌 / Distance too far, cannot damage enemy")

    def _check_dodge(self, mover, attacker, mover_act, attacker_act):
        """闪避判定"""
        if attacker_act != 'attack':
            return
        if mover_act not in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            return
        if not attacker.has_action('do_attack'):
            return
        
        # 移动前能打到，但没有be_attacked状态（说明移动后打不到）
        dist_before = abs(mover.position - attacker.position)
        base_range = attacker.get_action_value('do_attack')
        
        # 计算实际范围（含蓄力加成）
        attack_range = base_range
        if attacker.charge_level == 1:
            attack_range += CHARGE_1_RANGE_BONUS
        elif attacker.charge_level == 2:
            attack_range += CHARGE_2_RANGE_BONUS
        
        would_hit = (dist_before <= attack_range)
        got_attacked = mover.has_action('be_attacked')
        
        if would_hit and not got_attacked:
            print(f"{mover.name} 闪避成功 / {mover.name} dodged successfully")
            attacker.add_control_state('stun', DODGE_STUN_FRAMES)

    # ========== 阶段4：连击系统 ==========
    def _stage4_combo_system(self):
        """阶段4：检查连击，添加硬直状态"""
        # P1连击检查
        if self.p1.has_action('took_damage') and self.p2.has_action('dealt_damage'):
            if self.p1.is_hit_consecutive(self.turn, self.current_frame):
                self.p1.combo_count += 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = self.current_frame
                print(f"{self.p1.name} 连续被击中 {self.p1.combo_count}/3 / {self.p1.name} consecutive hit {self.p1.combo_count}/3")
                
                if self.p1.combo_count >= COMBO_THRESHOLD:
                    print(f"  触发连击硬直 / Trigger combo stun")
                    self.p1.add_control_state('stun', COMBO_STUN_FRAMES)
                    self.p1.combo_count = 0
                    self.p1.last_hit_turn = -1
                    self.p1.last_hit_frame = -1
            else:
                self.p1.combo_count = 1
                self.p1.last_hit_turn = self.turn
                self.p1.last_hit_frame = self.current_frame
                print(f"{self.p1.name} 被击中（不连续）1/3 / {self.p1.name} hit (non-consecutive) 1/3")
        else:
            if self.p1.combo_count > 0:
                print(f"  {self.p1.name} 连击中断，清零 / {self.p1.name} combo interrupted, reset")
                self.p1.combo_count = 0
                self.p1.last_hit_turn = -1
                self.p1.last_hit_frame = -1
        
        # P2连击检查
        if self.p2.has_action('took_damage') and self.p1.has_action('dealt_damage'):
            if self.p2.is_hit_consecutive(self.turn, self.current_frame):
                self.p2.combo_count += 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = self.current_frame
                print(f"{self.p2.name} 连续被击中 {self.p2.combo_count}/3 / {self.p2.name} consecutive hit {self.p2.combo_count}/3")
                
                if self.p2.combo_count >= COMBO_THRESHOLD:
                    print(f"  触发连击硬直 / Trigger combo stun")
                    self.p2.add_control_state('stun', COMBO_STUN_FRAMES)
                    self.p2.combo_count = 0
                    self.p2.last_hit_turn = -1
                    self.p2.last_hit_frame = -1
            else:
                self.p2.combo_count = 1
                self.p2.last_hit_turn = self.turn
                self.p2.last_hit_frame = self.current_frame
                print(f"{self.p2.name} 被击中（不连续）1/3 / {self.p2.name} hit (non-consecutive) 1/3")
        else:
            if self.p2.combo_count > 0:
                print(f"  {self.p2.name} 连击中断，清零 / {self.p2.name} combo interrupted, reset")
                self.p2.combo_count = 0
                self.p2.last_hit_turn = -1
                self.p2.last_hit_frame = -1

    # ========== 阶段5：硬直系统 ==========
    def _stage5_stun_system(self, frame):
        """阶段5：处理各种硬直状态（立即应用）"""
        
        # 应用硬直
        for state in self.p1.control_states:
            if state.type == 'stun':
                print(f"{self.p1.name} 硬直{state.value}帧 / {self.p1.name} stun {state.value} frames")
                self._apply_stun(self.p1, state.value, frame)
        
        for state in self.p2.control_states:
            if state.type == 'stun':
                print(f"{self.p2.name} 硬直{state.value}帧 / {self.p2.name} stun {state.value} frames")
                self._apply_stun(self.p2, state.value, frame)
        
        # 移除已处理的stun状态
        self.p1.control_states = [s for s in self.p1.control_states if s.type != 'stun']
        self.p2.control_states = [s for s in self.p2.control_states if s.type != 'stun']

    # ========== 阶段6：结算系统 ==========
    def _stage6_settle_all(self, p1_act, p2_act, frame):
        """阶段6：结算所有状态"""
        
        # 6.1 结算Buff（前置：蓄力）
        self._settle_buffs_pre()
        
        # 6.2 结算控制（pull和controlled）
        self._settle_control()
        
        # 6.3 结算位置
        self._settle_positions(p1_act, p2_act)
        
        # 6.4 结算伤害
        self._settle_damage()
        
        # 6.5 后处理：蓄力2硬直
        self._post_check_charge_2_stun(frame)
        
        # 6.6 结算Buff（后置：冲刺）
        self._settle_buffs_post()

    def _settle_buffs_pre(self):
        """结算Buff状态（前置：蓄力）"""
        # P1 蓄力结算
        for state in self.p1.buff_states:
            if state.type == 'charge':
                if state.action == 'pending':
                    # 检查蓄力是否被打断
                    has_non_self_dmg = any(
                        not s.source.endswith("_self")
                        for s in self.p1.damage_states
                    )
                    has_ctrl = any(s.type == 'controlled' for s in self.p1.control_states)
                    
                    if has_non_self_dmg or has_ctrl:
                        reason = "被控制" if has_ctrl else "被攻击"
                        print(f"{self.p1.name} 蓄力被打断（{reason}）/ {self.p1.name} charge interrupted ({'controlled' if has_ctrl else 'attacked'})")
                        self.p1.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="charge_interrupt")
                        if self.p1.charge_level > 0:
                            self.p1.charge_level = 0
                            print(f"  失去已有蓄力 / Lost existing charge")
                        continue
                    
                    # 蓄力成功
                    self.p1.charge_level = state.value
                    print(f"  {self.p1.name} 获得蓄力{state.value} / {self.p1.name} gained charge {state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p1.charge_level = 0
                    action_text = "消耗" if state.action == 'consume' else "失去"
                    print(f"  {self.p1.name} {action_text}蓄力 / {self.p1.name} {'consumed' if state.action == 'consume' else 'lost'} charge")
        
        # P2 蓄力结算
        for state in self.p2.buff_states:
            if state.type == 'charge':
                if state.action == 'pending':
                    has_non_self_dmg = any(
                        not s.source.endswith("_self")
                        for s in self.p2.damage_states
                    )
                    has_ctrl = any(s.type == 'controlled' for s in self.p2.control_states)
                    
                    if has_non_self_dmg or has_ctrl:
                        reason = "被控制" if has_ctrl else "被攻击"
                        print(f"{self.p2.name} 蓄力被打断（{reason}）/ {self.p2.name} charge interrupted ({'controlled' if has_ctrl else 'attacked'})")
                        self.p2.add_damage_state(CHARGE_INTERRUPTED_DAMAGE, source="charge_interrupt")
                        if self.p2.charge_level > 0:
                            self.p2.charge_level = 0
                            print(f"  失去已有蓄力 / Lost existing charge")
                        continue
                    
                    self.p2.charge_level = state.value
                    print(f"  {self.p2.name} 获得蓄力{state.value} / {self.p2.name} gained charge {state.value}")
                elif state.action in ['consume', 'lose']:
                    self.p2.charge_level = 0
                    action_text = "消耗" if state.action == 'consume' else "失去"
                    print(f"  {self.p2.name} {action_text}蓄力 / {self.p2.name} {'consumed' if state.action == 'consume' else 'lost'} charge")

    def _settle_buffs_post(self):
        """结算Buff状态（后置：冲刺）"""
        # P1 冲刺buff结算
        for state in self.p1.buff_states:
            if state.type == 'dash':
                if state.action == 'gain':
                    self.p1.dash_buff_stacks += state.value
                    print(f"  {self.p1.name} 获得冲刺buff（{self.p1.dash_buff_stacks}层）/ {self.p1.name} gained dash buff ({self.p1.dash_buff_stacks} stacks)")
                elif state.action == 'consume':
                    self.p1.dash_buff_stacks -= state.value
                    print(f"  {self.p1.name} 消耗冲刺buff -> 剩余{self.p1.dash_buff_stacks}层 / {self.p1.name} consumed dash buff -> {self.p1.dash_buff_stacks} stacks left")
        
        # P2 冲刺buff结算
        for state in self.p2.buff_states:
            if state.type == 'dash':
                if state.action == 'gain':
                    self.p2.dash_buff_stacks += state.value
                    print(f"  {self.p2.name} 获得冲刺buff（{self.p2.dash_buff_stacks}层）/ {self.p2.name} gained dash buff ({self.p2.dash_buff_stacks} stacks)")
                elif state.action == 'consume':
                    self.p2.dash_buff_stacks -= state.value
                    print(f"  {self.p2.name} 消耗冲刺buff -> 剩余{self.p2.dash_buff_stacks}层 / {self.p2.name} consumed dash buff -> {self.p2.dash_buff_stacks} stacks left")

    def _settle_control(self):
        """结算控制状态（pull和controlled）"""
        # Pull（绕过位置状态系统，使用控制者的当前位置）
        for state in self.p1.control_states:
            if state.type == 'pull':
                controller = self.p1 if state.target == self.p1.name else self.p2
                self.p1.position = controller.position
                print(f"  {self.p1.name} 被强制拉到{controller.position}（{controller.name}当前位置）")
                print(f"  {self.p1.name} forced to {controller.position} ({controller.name}'s current position)")
                break
        
        for state in self.p2.control_states:
            if state.type == 'pull':
                controller = self.p1 if state.target == self.p1.name else self.p2
                self.p2.position = controller.position
                print(f"  {self.p2.name} 被强制拉到{controller.position}（{controller.name}当前位置）")
                print(f"  {self.p2.name} forced to {controller.position} ({controller.name}'s current position)")
                break
        
        # Controlled（记录控制开始的时刻）
        for state in self.p1.control_states:
            if state.type == 'controlled':
                self.p1.controlled = True
                self.p1.controller = state.target
                self.p1.controlled_turn = self.turn
                self.p1.controlled_frame = self.current_frame
                print(f"  {self.p1.name} 被{state.target}控制 / {self.p1.name} controlled by {state.target}")
        
        for state in self.p2.control_states:
            if state.type == 'controlled':
                self.p2.controlled = True
                self.p2.controller = state.target
                self.p2.controlled_turn = self.turn
                self.p2.controlled_frame = self.current_frame
                print(f"  {self.p2.name} 被{state.target}控制 / {self.p2.name} controlled by {state.target}")
        
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
            print(f"{self.p1.name} 移动：{p1_initial}->{p1_final} (成功{p1_active}/{len(self.p1.position_states)})")
            print(f"{self.p1.name} moved: {p1_initial}->{p1_final} (success {p1_active}/{len(self.p1.position_states)})")
            self.p1.position = p1_final
        elif self.p1.position_states:
            print(f"{self.p1.name} 移动失败（0/{len(self.p1.position_states)}）/ {self.p1.name} move failed (0/{len(self.p1.position_states)})")
        
        if p2_final != p2_initial:
            print(f"{self.p2.name} 移动：{p2_initial}->{p2_final} (成功{p2_active}/{len(self.p2.position_states)})")
            print(f"{self.p2.name} moved: {p2_initial}->{p2_final} (success {p2_active}/{len(self.p2.position_states)})")
            self.p2.position = p2_final
        elif self.p2.position_states:
            print(f"{self.p2.name} 移动失败（0/{len(self.p2.position_states)}）/ {self.p2.name} move failed (0/{len(self.p2.position_states)})")
        
        # 冲刺buff：生成buff_state（在阶段6.6结算）
        if p1_act in ['dash_left', 'dash_right'] and p1_active > 0:
            if self.p1.dash_buff_stacks < DASH_MAX_STACKS:
                self.p1.add_buff_state('dash', 'gain', 1)
                print(f"{self.p1.name} 将获得冲刺buff / {self.p1.name} will gain dash buff")
        
        if p2_act in ['dash_left', 'dash_right'] and p2_active > 0:
            if self.p2.dash_buff_stacks < DASH_MAX_STACKS:
                self.p2.add_buff_state('dash', 'gain', 1)
                print(f"{self.p2.name} 将获得冲刺buff / {self.p2.name} will gain dash buff")

    def _settle_damage(self):
        """结算伤害（✅ 核心修改：buff在格挡前应用，只有他伤才计入连击）"""
        
        # ===== P1伤害计算 =====
        # 1. 计算基础总伤害
        total_dmg_p1 = sum(s.amount for s in self.p1.damage_states)
        
        # 2. 判定是否有他伤（不以 _self 结尾）
        p1_has_other_damage = any(
            not s.source.endswith("_self")
            for s in self.p1.damage_states
        )
        
        # 3. 如果有他伤且有buff，在格挡前增加伤害
        p1_used_buff_on_damage = False
        if p1_has_other_damage and self.p1.dash_buff_stacks > 0:
            print(f"{self.p1.name} 冲锋受伤+{self.p1.dash_buff_stacks} / {self.p1.name} dash buff damage+{self.p1.dash_buff_stacks}")
            total_dmg_p1 += self.p1.dash_buff_stacks
            p1_used_buff_on_damage = True
        
        # 4. 减去防御
        total_def_p1 = sum(s.reduction for s in self.p1.defense_states)
        p1_final = max(0, total_dmg_p1 - total_def_p1)
        
        # ===== P2伤害计算 =====
        # 1. 计算基础总伤害
        total_dmg_p2 = sum(s.amount for s in self.p2.damage_states)
        
        # 2. 判定是否有他伤（不以 _self 结尾）
        p2_has_other_damage = any(
            not s.source.endswith("_self")
            for s in self.p2.damage_states
        )
        
        # 3. 如果有他伤且有buff，在格挡前增加伤害
        p2_used_buff_on_damage = False
        if p2_has_other_damage and self.p2.dash_buff_stacks > 0:
            print(f"{self.p2.name} 冲锋受伤+{self.p2.dash_buff_stacks} / {self.p2.name} dash buff damage+{self.p2.dash_buff_stacks}")
            total_dmg_p2 += self.p2.dash_buff_stacks
            p2_used_buff_on_damage = True
        
        # 4. 减去防御
        total_def_p2 = sum(s.reduction for s in self.p2.defense_states)
        p2_final = max(0, total_dmg_p2 - total_def_p2)
        
        # ===== 应用伤害 =====
        if p1_final > 0:
            self.p1.hp = max(0, self.p1.hp - p1_final)
            
            # ✅ 只有他伤才设置took_damage（用于连击判定）
            if p1_has_other_damage:
                self.p1.add_action_state('took_damage')
            
            print(f"{self.p1.name} 受{p1_final}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
            print(f"{self.p1.name} took {p1_final} damage, HP: {self.p1.hp}/{self.p1.max_hp}")
        elif sum(s.amount for s in self.p1.damage_states) > 0:
            print(f"{self.p1.name} 完全格挡 / {self.p1.name} completely blocked")
        
        if p2_final > 0:
            self.p2.hp = max(0, self.p2.hp - p2_final)
            
            # ✅ 只有他伤才设置took_damage（用于连击判定）
            if p2_has_other_damage:
                self.p2.add_action_state('took_damage')
            
            print(f"{self.p2.name} 受{p2_final}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
            print(f"{self.p2.name} took {p2_final} damage, HP: {self.p2.hp}/{self.p2.max_hp}")
        elif sum(s.amount for s in self.p2.damage_states) > 0:
            print(f"{self.p2.name} 完全格挡 / {self.p2.name} completely blocked")
        
        # ===== 生成buff消耗状态（在阶段6.6结算） =====
        # P1消耗逻辑
        p1_should_consume = p1_used_buff_on_damage or self.p1.has_action('dealt_damage')
        if p1_should_consume and self.p1.dash_buff_stacks > 0:
            reason = []
            if p1_used_buff_on_damage:
                reason.append("受伤")
            if self.p1.has_action('dealt_damage'):
                reason.append("造成伤害")
            print(f"  {self.p1.name}将消耗冲刺buff（{'+'.join(reason)}）")
            print(f"  {self.p1.name} will consume dash buff ({'+'.join(['damage taken' if r=='受伤' else 'damage dealt' for r in reason])})")
            self.p1.add_buff_state('dash', 'consume', 1)
        
        # P2消耗逻辑
        p2_should_consume = p2_used_buff_on_damage or self.p2.has_action('dealt_damage')
        if p2_should_consume and self.p2.dash_buff_stacks > 0:
            reason = []
            if p2_used_buff_on_damage:
                reason.append("受伤")
            if self.p2.has_action('dealt_damage'):
                reason.append("造成伤害")
            print(f"  {self.p2.name}将消耗冲刺buff（{'+'.join(reason)}）")
            print(f"  {self.p2.name} will consume dash buff ({'+'.join(['damage taken' if r=='受伤' else 'damage dealt' for r in reason])})")
            self.p2.add_buff_state('dash', 'consume', 1)

    def _post_check_charge_2_stun(self, frame):
        """后处理：蓄力2硬直"""
        if self.p1.has_action('used_charge_2') and self.p2.has_action('took_damage'):
            print(f"  蓄力2额外硬直 / Charge 2 extra stun")
            self._apply_stun(self.p2, CHARGE_2_STUN_FRAMES, frame)
        
        if self.p2.has_action('used_charge_2') and self.p1.has_action('took_damage'):
            print(f"  蓄力2额外硬直 / Charge 2 extra stun")
            self._apply_stun(self.p1, CHARGE_2_STUN_FRAMES, frame)

    # ========== 阶段7：控制解除距离调整 ==========
    def _stage7_release_adjustment(self, current_frame):
        """阶段7：处理控制解除后的距离调整"""
        p1_has_release = any(s.type == 'release' for s in self.p1.control_states)
        p2_has_release = any(s.type == 'release' for s in self.p2.control_states)
        
        # 技能触发的解除（grab/throw/burst）
        if p1_has_release or p2_has_release:
            self._handle_skill_release(p1_has_release, p2_has_release)
        
        # 帧结束自动解除控制（只在"下一帧"才解除）
        if self.p1.controlled:
            self._auto_release_control(self.p1, current_frame)
        if self.p2.controlled:
            self._auto_release_control(self.p2, current_frame)
        
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
            return
        
        print(f"  {player.name}控制状态帧结束解除 / {player.name} control state ends at frame end")
        
        distance = self.get_distance()
        
        if distance != 0:
            print(f"  距离{distance}!=0，无需位置调整 / Distance {distance}!=0, no position adjustment needed")
            player.controlled = False
            player.controller = None
            player.controlled_from_position = None
            player.controlled_turn = -1
            player.controlled_frame = -1
            return
        
        print(f"  距离为0，检查是否需要位置调整 / Distance is 0, checking if position adjustment is needed")
        
        # 使用has_action代替临时字段
        p1_took_damage = self.p1.has_action('took_damage')
        p2_took_damage = self.p2.has_action('took_damage')
        
        if p1_took_damage and p2_took_damage:
            print(f"  双方都受伤，都后退一格 / Both players injured, both retreat one tile")
            self._retreat_player(self.p1)
            self._retreat_player(self.p2)
        elif p1_took_damage:
            print(f"  {self.p1.name}受伤，后退一格 / {self.p1.name} injured, retreat one tile")
            self._retreat_player(self.p1)
        elif p2_took_damage:
            print(f"  {self.p2.name}受伤，后退一格 / {self.p2.name} injured, retreat one tile")
            self._retreat_player(self.p2)
        else:
            if player.controlled_from_position is not None:
                print(f"  {player.name}被控制无受伤，后退一格 / {player.name} controlled but not injured, retreat one tile")
                player.position = player.controlled_from_position
                print(f"  {player.name} 回到{player.position} / {player.name} returns to {player.position}")
        
        player.controlled = False
        player.controller = None
        player.controlled_from_position = None
        player.controlled_turn = -1
        player.controlled_frame = -1

    def _handle_skill_release(self, p1_has_release, p2_has_release):
        """处理技能触发的控制解除（grab/throw/burst）"""
        distance = self.get_distance()
        
        if distance != 0:
            print(f"  grab/throw/burst解除：距离{distance}!=0，无需调整")
            print(f"  grab/throw/burst release: distance {distance}!=0, no adjustment needed")
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
        
        print(f"  grab/throw/burst解除：距离为0，需要调整")
        print(f"  grab/throw/burst release: distance is 0, adjustment needed")
        
        # 使用has_action代替临时字段
        p1_took = self.p1.has_action('took_damage')
        p2_took = self.p2.has_action('took_damage')
        
        if p1_took and p2_took:
            # 双方都受伤，都后退（统一使用_retreat_player）
            print(f"  双方都受伤，都后退一格 / Both players injured, both retreat one tile")
            self._retreat_player(self.p1)
            self._retreat_player(self.p2)
        elif p1_took:
            print(f"  {self.p1.name}受伤，后退一格 / {self.p1.name} injured, retreat one tile")
            self._retreat_player(self.p1)
        elif p2_took:
            print(f"  {self.p2.name}受伤，后退一格 / {self.p2.name} injured, retreat one tile")
            self._retreat_player(self.p2)
        else:
            if p1_has_release and self.p1.controlled_from_position is not None:
                print(f"  {self.p1.name}被控制无受伤，后退一格 / {self.p1.name} controlled but not injured, retreat one tile")
                self.p1.position = self.p1.controlled_from_position
            if p2_has_release and self.p2.controlled_from_position is not None:
                print(f"  {self.p2.name}被控制无受伤，后退一格 / {self.p2.name} controlled but not injured, retreat one tile")
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
            print(f"  {player.name} 回到被控制前位置{player.position}")
            print(f"  {player.name} returns to pre-control position {player.position}")
        else:
            # 非被控制者：按方向后退
            retreat_delta = -1 if player.is_left else 1
            new_pos = player.position + retreat_delta
            new_pos = max(1, min(MAP_SIZE, new_pos))  # 边界检查
            player.position = new_pos
            print(f"  {player.name} 按方向后退到{player.position}")
            print(f"  {player.name} retreats to {player.position} based on direction")

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

    def _predict_final_positions(self, include_pull=True):
        """预计算最终位置（可选是否包含pull效果）"""
        # 初始位置
        p1_pos = self.p1.position
        p2_pos = self.p2.position
        
        # 先处理pull（如果可用）
        if include_pull:
            # 检查P1是否会被pull
            for state in self.p1.control_states:
                if state.type == 'pull':
                    # target存的是控制者名字
                    if state.target == self.p2.name:
                        p1_pos = self.p2.position  # 被拉到P2位置
                        print(f"  预测pull: {self.p1.name}将被拉到{p1_pos} / Predict pull: {self.p1.name} will be pulled to {p1_pos}")
                    break
            
            # 检查P2是否会被pull
            for state in self.p2.control_states:
                if state.type == 'pull':
                    if state.target == self.p1.name:
                        p2_pos = self.p1.position  # 被拉到P1位置
                        print(f"  预测pull: {self.p2.name}将被拉到{p2_pos} / Predict pull: {self.p2.name} will be pulled to {p2_pos}")
                    break
        
        # 基于pull后的位置，计算移动
        p1_final, p2_final, _, _ = self._resolve_positions_core(
            self.p1.position_states,
            self.p2.position_states,
            p1_pos,  # 使用pull后的位置作为起点
            p2_pos
        )
        
        return p1_final, p2_final

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
            print(f"  锁定回合{turn}第{frame}帧 / Lock turn {turn} frame {frame}")

    def get_winner(self):
        if not self.p1.is_alive() and not self.p2.is_alive():
            return "平局 / Draw"
        elif not self.p1.is_alive():
            return self.p2.name
        elif not self.p2.is_alive():
            return self.p1.name
        return None

    def show_final_result(self):
        winner = self.get_winner()
        print(f"\n{'='*60}")
        print(f"战斗结束！回合数: {self.turn} / Battle ended! Round: {self.turn}")
        if winner:
            print(f"胜者: {winner} / Winner: {winner}")
        self.p1.show_status()
        self.p2.show_status()
        print('='*60)