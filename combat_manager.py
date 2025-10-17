"""
combat_manager.py
战斗管理器 - 基于状态系统的战斗流程
【核心改动】距离为0时的穿透防护+控制逻辑修复+抱摔伤害+2
"""

from player import Player
from actions import Actions
from config import *


class CombatManager:
    """战斗管理器 - 集中处理所有游戏逻辑"""
    
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.turn = 0
        
        # 日志历史
        self.turn_logs = []
        self.current_turn_messages = []
        
        # 确定左右（重要：决定相对位置）
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
        if not action:
            return None
        
        if player.is_frame_locked(self.turn, frame):
            if action == 'burst':
                print(f"💥 {player.name} 硬直中使用爆血！")
                return action
            else:
                print(f"📍 {player.name} 第{frame}帧被硬直！")
                return None
        
        if player.controlled and action not in ['defend', 'burst']:
            print(f"⛓️ {player.name} 被控制，只能S或O！")
            return None
        
        return action
    
    def _execute_frame(self, p1_act, p2_act, frame):
        """执行单帧"""
        
        # 步骤1：施加移动状态
        print("\n[1.移动]")
        if p1_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p1, p1_act)
        if p2_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            self._do_move(self.p2, p2_act)
        
        # 步骤2：解决位置冲突并应用
        print("\n[2.位置结算]")
        p1_success, p2_success = self._resolve_and_apply_positions(p1_act, p2_act)
        
        # 步骤3：施加防御状态
        print("\n[3.防御]")
        if p1_act in ['defend', 'counter']:
            self._do_defend(self.p1, p1_act)
        if p2_act in ['defend', 'counter']:
            self._do_defend(self.p2, p2_act)
        
        # 步骤4：处理蓄力
        if p1_act == 'charge':
            self._do_charge(self.p1, frame)
        if p2_act == 'charge':
            self._do_charge(self.p2, frame)
        
        # 步骤5：施加攻击/技能状态
        print("\n[4.攻击/技能]")
        distance = self.get_distance()
        
        if p1_act == 'attack':
            Actions.attack(self.p1, self.p2, distance)
        elif p1_act == 'control':
            if distance <= CONTROL_RANGE:
                print(f"📍 {self.p1.name} 控制了 {self.p2.name}！")
                Actions.control(self.p1, self.p2)
            else:
                print(f"❌ {self.p1.name} 控制未命中！（距{distance}格 > {CONTROL_RANGE}格）")
                self._apply_stun(self.p1, CONTROL_MISS_STUN_FRAMES, frame)
        elif p1_act == 'grab':
            Actions.grab(self.p1, self.p2)
        elif p1_act == 'throw':
            Actions.throw(self.p1, self.p2)
        elif p1_act == 'burst':
            Actions.burst(self.p1, self.p2, distance)
        
        if p2_act == 'attack':
            Actions.attack(self.p2, self.p1, distance)
        elif p2_act == 'control':
            if distance <= CONTROL_RANGE:
                print(f"📍 {self.p2.name} 控制了 {self.p1.name}！")
                Actions.control(self.p2, self.p1)
            else:
                print(f"❌ {self.p2.name} 控制未命中！（距{distance}格 > {CONTROL_RANGE}格）")
                self._apply_stun(self.p2, CONTROL_MISS_STUN_FRAMES, frame)
        elif p2_act == 'grab':
            Actions.grab(self.p2, self.p1)
        elif p2_act == 'throw':
            Actions.throw(self.p2, self.p1)
        elif p2_act == 'burst':
            Actions.burst(self.p2, self.p1, distance)
        
        # 步骤6：结算伤害
        print("\n[5.伤害结算]")
        self._settle_damage()
        
        # 步骤6.5：控制状态伤害反应（谁受伤谁后退）
        print("\n[5.5控制反应]")
        self._apply_control_knockback()
        
        # 步骤7：特殊机制
        print("\n[6.特殊机制]")
        self._check_interrupt(p1_act, p2_act)
        self._check_dodge(p1_act, p2_act, frame)
        self._check_counter(frame)
        self._check_combo(frame)
        self._check_charge_2_stun(frame)
        self._check_control_release(p1_act, p2_act)
    
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
        can_stack = False
        
        if player.charge_level == 1:
            if player.can_stack_charge(self.turn, frame, player.last_charge_turn, player.last_charge_frame):
                can_stack = True
        
        if can_stack:
            player.charge_level = 2
            print(f"✨✨ {player.name} 蓄力2！")
        else:
            player.charge_level = 1
            print(f"✨ {player.name} 蓄力1！")
        
        player.last_charge_turn = self.turn
        player.last_charge_frame = frame
    
    def _resolve_and_apply_positions(self, p1_act, p2_act):
        """
        【核心算法】解决位置冲突
        关键点：
        1. 记录初始相对位置（is_left标志）
        2. 完全施加所有状态后检查冲突
        3. 检查：重叠、穿越、互换方位（距离=0时也检查）
        4. 有冲突则回退，直到无冲突
        """
        p1_states = self.p1.position_states
        p2_states = self.p2.position_states
        
        if not p1_states and not p2_states:
            return 0, 0
        
        p1_initial = self.p1.position
        p2_initial = self.p2.position
        
        p1_active = len(p1_states)
        p2_active = len(p2_states)
        
        # 循环解决冲突
        while True:
            # 计算当前位置
            p1_pos = p1_initial + sum(p1_states[i].delta for i in range(p1_active))
            p2_pos = p2_initial + sum(p2_states[i].delta for i in range(p2_active))
            
            # 边界限制
            p1_pos = max(1, min(MAP_SIZE, p1_pos))
            p2_pos = max(1, min(MAP_SIZE, p2_pos))
            
            # 检查冲突
            has_conflict = False
            
            # ===== 重叠检查 =====
            if p1_pos == p2_pos:
                # 检查是否是控制导致的合法重叠
                is_control_overlap = (
                    (self.p1.controlled or self.p2.controlled) and
                    p1_initial == p2_initial  # 初始就重叠（被控制状态）
                )
                
                if not is_control_overlap:
                    has_conflict = True
                    print(f"   冲突：重叠在{p1_pos}")
            
            # ===== 穿越检查 =====
            # 即使距离为0也要检查穿越！
            if not has_conflict:
                # P1穿过P2
                if p1_initial < p2_initial and p1_pos > p2_pos:
                    has_conflict = True
                    print(f"   冲突：{self.p1.name}穿越{self.p2.name}")
                # P2穿过P1
                elif p2_initial < p1_initial and p2_pos > p1_pos:
                    has_conflict = True
                    print(f"   冲突：{self.p2.name}穿越{self.p1.name}")
            
            # ===== 互换方位检查（距离=0时最重要） =====
            # 从重叠位置分开时，不能互换相对位置
            if not has_conflict:
                if p1_initial == p2_initial and p1_pos != p2_pos:
                    # 初始重叠，现在要分开
                    # 检查是否互换了方位
                    if (p1_pos < p2_initial and p2_pos > p1_initial) or \
                       (p2_pos < p1_initial and p1_pos > p2_initial):
                        has_conflict = True
                        print(f"   冲突：重叠位置不能互换方位")
            
            if not has_conflict:
                break
            
            # 有冲突，回退
            if p1_active == 0 and p2_active == 0:
                break
            
            if p1_active > 0:
                p1_active -= 1
                print(f"   {self.p1.name}回退1个状态")
            
            if p2_active > 0:
                p2_active -= 1
                print(f"   {self.p2.name}回退1个状态")
        
        # 应用最终位置
        p1_final = p1_initial + sum(p1_states[i].delta for i in range(p1_active))
        p2_final = p2_initial + sum(p2_states[i].delta for i in range(p2_active))
        
        p1_final = max(1, min(MAP_SIZE, p1_final))
        p2_final = max(1, min(MAP_SIZE, p2_final))
        
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
        
        # 冲刺buff
        if p1_act in ['dash_left', 'dash_right'] and p1_active > 0:
            if self.p1.dash_buff_stacks < DASH_MAX_STACKS:
                self.p1.dash_buff_stacks += 1
                print(f"🏃 {self.p1.name} 获得冲刺buff（{self.p1.dash_buff_stacks}层）")
        
        if p2_act in ['dash_left', 'dash_right'] and p2_active > 0:
            if self.p2.dash_buff_stacks < DASH_MAX_STACKS:
                self.p2.dash_buff_stacks += 1
                print(f"🏃 {self.p2.name} 获得冲刺buff（{self.p2.dash_buff_stacks}层）")
        
        return p1_active, p2_active
    
    def _settle_damage(self):
        """
        【伤害结算流程】
        1. 计算总伤害 - 总防御
        2. 如果有冲刺buff：伤害+buff值，消耗1层
        3. 如果有抱摔buff（仅本帧）：伤害+buff值，清零
        4. 应用最终伤害
        """
        # ===== P1 受伤 =====
        total_dmg = sum(s.amount for s in self.p1.damage_states if not s.cancelled)
        total_def = sum(s.reduction for s in self.p1.defense_states if not s.cancelled)
        p1_final_dmg = max(0, total_dmg - total_def)
        
        # 冲刺buff加成（持久跨帧）
        if p1_final_dmg > 0 and self.p1.dash_buff_stacks > 0:
            print(f"🏃 {self.p1.name} 冲锋受伤+{self.p1.dash_buff_stacks}")
            p1_final_dmg += self.p1.dash_buff_stacks
            self.p1.dash_buff_stacks -= 1
        
        # 抱摔buff加成（仅本帧，由reset_frame清零）
        if p1_final_dmg > 0 and self.p1.grab_damage_buff > 0:
            print(f"🤼 {self.p1.name} 抱摔受伤+{self.p1.grab_damage_buff}")
            p1_final_dmg += self.p1.grab_damage_buff
            self.p1.grab_damage_buff = 0
        
        # 应用伤害
        if p1_final_dmg > 0:
            self.p1.hp = max(0, self.p1.hp - p1_final_dmg)
            self.p1.took_damage_this_frame = True
            print(f"💔 {self.p1.name} 受{p1_final_dmg}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p1.name} 完全格挡！")
        
        # ===== P2 受伤 =====
        total_dmg = sum(s.amount for s in self.p2.damage_states if not s.cancelled)
        total_def = sum(s.reduction for s in self.p2.defense_states if not s.cancelled)
        p2_final_dmg = max(0, total_dmg - total_def)
        
        # 冲刺buff加成（持久跨帧）
        if p2_final_dmg > 0 and self.p2.dash_buff_stacks > 0:
            print(f"🏃 {self.p2.name} 冲锋受伤+{self.p2.dash_buff_stacks}")
            p2_final_dmg += self.p2.dash_buff_stacks
            self.p2.dash_buff_stacks -= 1
        
        # 抱摔buff加成（仅本帧，由reset_frame清零）
        if p2_final_dmg > 0 and self.p2.grab_damage_buff > 0:
            print(f"🤼 {self.p2.name} 抱摔受伤+{self.p2.grab_damage_buff}")
            p2_final_dmg += self.p2.grab_damage_buff
            self.p2.grab_damage_buff = 0
        
        # 应用伤害
        if p2_final_dmg > 0:
            self.p2.hp = max(0, self.p2.hp - p2_final_dmg)
            self.p2.took_damage_this_frame = True
            print(f"💔 {self.p2.name} 受{p2_final_dmg}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
        elif total_dmg > 0:
            print(f"🛡️ {self.p2.name} 完全格挡！")
        
        # ===== 消耗攻击者buff =====
        # 冲刺buff消耗（造成伤害后消耗1层）
        if self.p1.dealt_damage_this_frame and self.p1.dash_buff_stacks > 0:
            self.p1.dash_buff_stacks -= 1
            print(f"   {self.p1.name}冲刺buff已消耗")
        
        if self.p2.dealt_damage_this_frame and self.p2.dash_buff_stacks > 0:
            self.p2.dash_buff_stacks -= 1
            print(f"   {self.p2.name}冲刺buff已消耗")
        
        # 抱摔buff会在reset_frame时清零（见player.py）
    
    def _apply_control_knockback(self):
        """
        处理控制状态下的伤害反应
        规则：谁受伤谁后退1格（解除控制）
        """
        # P1被P2控制
        if self.p1.controlled and self.p1.controller == self.p2.name:
            should_release = False
            
            # P1受伤 → P1后退
            if self.p1.took_damage_this_frame:
                print(f"   {self.p1.name}因受伤后退")
                should_release = True
            # P2（控制者）受伤 → P1也后退
            elif self.p2.took_damage_this_frame:
                print(f"   {self.p1.name}随控制者受伤后退")
                should_release = True
            
            if should_release:
                push_delta = -1 if self.p1.is_left else 1
                new_pos = max(1, min(MAP_SIZE, self.p1.position + push_delta))
                if new_pos != self.p1.position:
                    self.p1.position = new_pos
                    print(f"   🔙 {self.p1.name}后退到{new_pos}（解除控制）")
                
                self.p1.controlled = False
                self.p1.controller = None
        
        # P2被P1控制
        if self.p2.controlled and self.p2.controller == self.p1.name:
            should_release = False
            
            # P2受伤 → P2后退
            if self.p2.took_damage_this_frame:
                print(f"   {self.p2.name}因受伤后退")
                should_release = True
            # P1（控制者）受伤 → P2也后退
            elif self.p1.took_damage_this_frame:
                print(f"   {self.p2.name}随控制者受伤后退")
                should_release = True
            
            if should_release:
                push_delta = -1 if self.p2.is_left else 1
                new_pos = max(1, min(MAP_SIZE, self.p2.position + push_delta))
                if new_pos != self.p2.position:
                    self.p2.position = new_pos
                    print(f"   🔙 {self.p2.name}后退到{new_pos}（解除控制）")
                
                self.p2.controlled = False
                self.p2.controller = None
        
        # 处理抱摔后退
        if self.p1.should_knockback:
            push_delta = -1 if self.p2.is_left else 1
            new_pos = max(1, min(MAP_SIZE, self.p2.position + push_delta))
            if new_pos != self.p2.position:
                self.p2.position = new_pos
                print(f"   🔙 {self.p2.name}被抱摔推开到{new_pos}")
        
        if self.p2.should_knockback:
            push_delta = -1 if self.p1.is_left else 1
            new_pos = max(1, min(MAP_SIZE, self.p1.position + push_delta))
            if new_pos != self.p1.position:
                self.p1.position = new_pos
                print(f"   🔙 {self.p1.name}被抱摔推开到{new_pos}")
    
    def _check_interrupt(self, p1_act, p2_act):
        vulnerable = ['attack', 'burst', 'charge']
        
        if p1_act in vulnerable and not self.p1.dealt_damage_this_frame and self.p2.dealt_damage_this_frame:
            print(f"⚡ {self.p1.name}的{p1_act}被打断！")
            if p1_act == 'charge' and self.p1.charge_level > 0:
                print(f"   失去蓄力")
                self.p1.charge_level = 0
                self.p1.hp -= CHARGE_INTERRUPTED_DAMAGE
                print(f"💔 {self.p1.name} 额外受{CHARGE_INTERRUPTED_DAMAGE}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
        
        if p2_act in vulnerable and not self.p2.dealt_damage_this_frame and self.p1.dealt_damage_this_frame:
            print(f"⚡ {self.p2.name}的{p2_act}被打断！")
            if p2_act == 'charge' and self.p2.charge_level > 0:
                print(f"   失去蓄力")
                self.p2.charge_level = 0
                self.p2.hp -= CHARGE_INTERRUPTED_DAMAGE
                print(f"💔 {self.p2.name} 额外受{CHARGE_INTERRUPTED_DAMAGE}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
    
    def _check_dodge(self, p1_act, p2_act, frame):
        if p2_act == 'attack' and p1_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            if self.p2.tried_attack_this_frame:
                dist_before = abs(self.p1.position_before_move - self.p2.position_before_move)
                dist_after = abs(self.p1.position - self.p2.position)
                
                if (dist_before <= self.p2.attack_range_this_frame and 
                    dist_after > self.p2.attack_range_this_frame and
                    not self.p2.dealt_damage_this_frame):
                    print(f"🎨 {self.p1.name} 闪避成功！")
                    self._apply_stun(self.p2, DODGE_STUN_FRAMES, frame)
        
        if p1_act == 'attack' and p2_act in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            if self.p1.tried_attack_this_frame:
                dist_before = abs(self.p1.position_before_move - self.p2.position_before_move)
                dist_after = abs(self.p1.position - self.p2.position)
                
                if (dist_before <= self.p1.attack_range_this_frame and 
                    dist_after > self.p1.attack_range_this_frame and
                    not self.p1.dealt_damage_this_frame):
                    print(f"🎨 {self.p2.name} 闪避成功！")
                    self._apply_stun(self.p1, DODGE_STUN_FRAMES, frame)
    
    def _check_counter(self, frame):
        if self.p1.countering:
            if self.p1.took_damage_this_frame:
                print(f"⚔️ {self.p1.name} 反击成功！")
                self.p2.hp -= COUNTER_DAMAGE
                print(f"💔 {self.p2.name} 受{COUNTER_DAMAGE}伤，HP: {self.p2.hp}/{self.p2.max_hp}")
            else:
                print(f"❌ {self.p1.name} 反击失败，硬直！")
                self._apply_stun(self.p1, COUNTER_FAIL_STUN_FRAMES, frame)
        
        if self.p2.countering:
            if self.p2.took_damage_this_frame:
                print(f"⚔️ {self.p2.name} 反击成功！")
                self.p1.hp -= COUNTER_DAMAGE
                print(f"💔 {self.p1.name} 受{COUNTER_DAMAGE}伤，HP: {self.p1.hp}/{self.p1.max_hp}")
            else:
                print(f"❌ {self.p2.name} 反击失败，硬直！")
                self._apply_stun(self.p2, COUNTER_FAIL_STUN_FRAMES, frame)
    
    def _check_combo(self, frame):
        # P1被连击
        if self.p1.took_damage_this_frame and self.p2.dealt_damage_this_frame:
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
        if self.p2.took_damage_this_frame and self.p1.dealt_damage_this_frame:
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
    
    def _check_charge_2_stun(self, frame):
        if self.p1.used_charge_2_this_frame and self.p2.took_damage_this_frame:
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p2, CHARGE_2_STUN_FRAMES, frame)
        
        if self.p2.used_charge_2_this_frame and self.p1.took_damage_this_frame:
            print(f"   蓄力2额外硬直！")
            self._apply_stun(self.p1, CHARGE_2_STUN_FRAMES, frame)
    
    def _check_control_release(self, p1_act, p2_act):
        if self.p2.controlled and p1_act:
            if p1_act not in ['control', 'grab', 'throw', 'move_left', 'move_right', 'dash_left', 'dash_right']:
                print(f"🔓 {self.p1.name}执行{p1_act}，解除控制")
                
                push_delta = -1 if self.p2.is_left else 1
                new_pos = max(1, min(MAP_SIZE, self.p2.position + push_delta))
                
                if new_pos != self.p2.position:
                    self.p2.position = new_pos
                    print(f"   {self.p2.name}被推到{new_pos}")
                
                self.p2.controlled = False
                self.p2.controller = None
        
        if self.p1.controlled and p2_act:
            if p2_act not in ['control', 'grab', 'throw', 'move_left', 'move_right', 'dash_left', 'dash_right']:
                print(f"🔓 {self.p2.name}执行{p2_act}，解除控制")
                
                push_delta = -1 if self.p1.is_left else 1
                new_pos = max(1, min(MAP_SIZE, self.p1.position + push_delta))
                
                if new_pos != self.p1.position:
                    self.p1.position = new_pos
                    print(f"   {self.p1.name}被推到{new_pos}")
                
                self.p1.controlled = False
                self.p1.controller = None
    
    def _apply_stun(self, player, stun_frames, current_frame):
        print(f"😵 {player.name} 硬直{stun_frames}帧！")
        
        turn = self.turn
        frame = current_frame
        
        for _ in range(stun_frames):
            frame += 1
            if frame > 2:
                frame = 1
                turn += 1
            player.lock_frame(turn, frame)
            print(f"   📍 回合{turn}第{frame}帧")
    
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