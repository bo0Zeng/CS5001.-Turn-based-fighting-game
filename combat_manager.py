"""
combat_manager.py
战斗管理器 - Bug修复版（基于旧版本）
"""

from player import Player
from actions import Actions
from config import *


class CombatManager:
    """战斗管理器"""
    
    def __init__(self, player1, player2):
        """初始化战斗"""
        self.player1 = player1
        self.player2 = player2
        self.turn = 0
        self.battle_log = []
        
        # 确定玩家的左右位置
        if player1.position < player2.position:
            player1.is_left = True
            player2.is_left = False
        else:
            player1.is_left = False
            player2.is_left = True
    
    def get_distance(self):
        """计算距离"""
        return abs(self.player1.position - self.player2.position)
    
    def show_battle_status(self):
        """显示战场状态"""
        print(f"\n{SEPARATOR}")
        print(f"回合 {self.turn} | 距离: {self.get_distance()}格")
        self.player1.show_status()
        self.player2.show_status()
        print(SEPARATOR)
    
    def execute_turn(self, p1_actions, p2_actions):
        """执行一个回合（2帧）"""
        self.turn += 1
        self.show_battle_status()
        
        self.player1.clear_expired_locks(self.turn)
        self.player2.clear_expired_locks(self.turn)
        
        print(f"\n{self.player1.name} 行动: {p1_actions}")
        print(f"{self.player2.name} 行动: {p2_actions}")
        
        frame_results = []
        
        # 执行2帧
        for frame_idx in range(2):
            current_frame = frame_idx + 1
            print(f"\n--- 第 {current_frame} 帧 ---")
            
            # 重置单帧状态
            self.player1.reset_frame_status()
            self.player2.reset_frame_status()
            
            # 获取当前帧的行动
            p1_action = p1_actions[frame_idx] if frame_idx < len(p1_actions) else None
            p2_action = p2_actions[frame_idx] if frame_idx < len(p2_actions) else None
            
            # 检查硬直锁定（爆血除外）
            if self.player1.is_frame_locked(self.turn, current_frame):
                if p1_action != 'burst':
                    print(f"🔒 {self.player1.name} 第{current_frame}帧被硬直锁定！")
                    p1_action = None
                else:
                    print(f"💥 {self.player1.name} 硬直中使用爆血！")
            
            if self.player2.is_frame_locked(self.turn, current_frame):
                if p2_action != 'burst':
                    print(f"🔒 {self.player2.name} 第{current_frame}帧被硬直锁定！")
                    p2_action = None
                else:
                    print(f"💥 {self.player2.name} 硬直中使用爆血！")
            
            # 检查行动取消状态
            if self.player1.actions_cancelled and p1_action:
                print(f"⛔ {self.player1.name} 行动已被取消！")
                p1_action = None
            
            if self.player2.actions_cancelled and p2_action:
                print(f"⛔ {self.player2.name} 行动已被取消！")
                p2_action = None
            
            # 检查被控制状态
            if self.player1.controlled and p1_action:
                if p1_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player1.name} 被控制，只能使用防御或爆血！")
                    p1_action = None
            
            if self.player2.controlled and p2_action:
                if p2_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player2.name} 被控制，只能使用防御或爆血！")
                    p2_action = None
            
            # 执行行动
            frame_result = self._execute_frame(p1_action, p2_action, current_frame)
            frame_results.append(frame_result)
            
            # 检查胜负
            if not self.player1.is_alive() or not self.player2.is_alive():
                return frame_results
        
        # 回合结束处理
        self.player1.update_turn_status()
        self.player2.update_turn_status()
        
        return frame_results
    
    def _execute_frame(self, p1_action, p2_action, current_frame):
        """
        执行单帧的行动
        分三个阶段：1.移动阶段 2.防御阶段 3.技能阶段
        """
        result = {
            'p1_action': p1_action,
            'p2_action': p2_action,
            'messages': [],
            'p1_hp': self.player1.hp,
            'p2_hp': self.player2.hp,
            'distance': self.get_distance()
        }
        
        # 保存移动前的位置（用于闪避判定）
        p1_pos_before = self.player1.position
        p2_pos_before = self.player2.position
        
        # 第一阶段：先执行所有移动
        move_actions = ['move_left', 'move_right', 'dash_left', 'dash_right']
        
        if p1_action in move_actions:
            self._execute_action(self.player1, self.player2, p1_action, self.turn, current_frame)
        
        if p2_action in move_actions:
            self._execute_action(self.player2, self.player1, p2_action, self.turn, current_frame)
        
        # 第二阶段：执行所有防御类行动（必须在攻击前生效）
        defend_actions = ['defend', 'counter']
        
        if p1_action in defend_actions:
            self._execute_action(self.player1, self.player2, p1_action, self.turn, current_frame)
        
        if p2_action in defend_actions:
            self._execute_action(self.player2, self.player1, p2_action, self.turn, current_frame)
        
        # 第三阶段：执行所有攻击和其他行动
        other_actions = move_actions + defend_actions
        
        if p1_action and p1_action not in other_actions:
            self._execute_action(self.player1, self.player2, p1_action, self.turn, current_frame)
        
        if p2_action and p2_action not in other_actions:
            self._execute_action(self.player2, self.player1, p2_action, self.turn, current_frame)
        
        # 检查打断
        self._check_interrupts()
        
        # 检查闪避（传递current_frame）
        self._check_dodge(p1_action, p2_action, p1_pos_before, p2_pos_before, current_frame)
        
        # 检查防御反击（传递current_frame）
        self._check_counter(current_frame)
        
        # 处理控制解除
        self._handle_control_release(p1_action, p2_action)
        
        return result
    
    def _execute_action(self, actor, target, action, current_turn, current_frame):
        """执行单个行动"""
        distance = self.get_distance()
        
        if action == 'attack':
            Actions.attack(actor, target, distance, current_turn, current_frame)
        elif action == 'charge':
            Actions.charge(actor, current_turn, current_frame)
        elif action == 'control':
            Actions.control(actor, target, distance, current_turn, current_frame)
        elif action == 'grab':
            Actions.grab(actor, target)
        elif action == 'throw':
            Actions.throw(actor, target)
        elif action == 'defend':
            Actions.defend(actor)
        elif action == 'counter':
            Actions.counter(actor)
        elif action == 'move_left':
            Actions.move(actor, target, 'left')
        elif action == 'move_right':
            Actions.move(actor, target, 'right')
        elif action == 'dash_left':
            Actions.dash(actor, target, 'left')
        elif action == 'dash_right':
            Actions.dash(actor, target, 'right')
        elif action == 'burst':
            Actions.burst(actor, target, distance)
        else:
            if action:
                print(f"❓ 未知行动: {action}")
    
    def _check_interrupts(self):
        """检查打断"""
        from config import CHARGE_INTERRUPTED_DAMAGE
        
        # 检查玩家1是否被打断
        if self.player1.vulnerable_action and not self.player1.action_dealt_damage:
            if self.player2.action_dealt_damage:
                print(f"⚡ {self.player1.name}的{self.player1.vulnerable_action}被打断！")
                if self.player1.vulnerable_action == 'charge':
                    self.player1.lose_charge("（被打断）")
                    self.player1.take_damage(CHARGE_INTERRUPTED_DAMAGE)
        
        # 检查玩家2是否被打断
        if self.player2.vulnerable_action and not self.player2.action_dealt_damage:
            if self.player1.action_dealt_damage:
                print(f"⚡ {self.player2.name}的{self.player2.vulnerable_action}被打断！")
                if self.player2.vulnerable_action == 'charge':
                    self.player2.lose_charge("（被打断）")
                    self.player2.take_damage(CHARGE_INTERRUPTED_DAMAGE)
    
    def _check_dodge(self, p1_action, p2_action, p1_pos_before, p2_pos_before, current_frame):
        """检查闪避（对手攻击时移动，移动前会被打到但移动后脱离攻击范围）"""
        from config import DODGE_STUN_FRAMES, ATTACK_RANGE, CHARGE_1_RANGE_BONUS, CHARGE_2_RANGE_BONUS
        
        # 检查玩家1是否闪避了玩家2的攻击
        if p2_action == 'attack' and p1_action in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            # 计算玩家2的攻击距离
            attack_range = ATTACK_RANGE
            if self.player2.used_charge_level == 1:
                attack_range += CHARGE_1_RANGE_BONUS
            elif self.player2.used_charge_level == 2:
                attack_range += CHARGE_2_RANGE_BONUS
            
            # 计算移动前后的距离
            distance_before = abs(p1_pos_before - p2_pos_before)
            distance_after = abs(self.player1.position - self.player2.position)
            
            # 判断闪避
            if (distance_before <= attack_range and 
                distance_after > attack_range and 
                self.player2.vulnerable_action == 'attack' and 
                not self.player2.action_dealt_damage):
                print(f"💨 {self.player1.name} 闪避了{self.player2.name}的攻击！")
                self.player2.apply_stun(DODGE_STUN_FRAMES, self.turn, current_frame)
        
        # 检查玩家2是否闪避了玩家1的攻击
        if p1_action == 'attack' and p2_action in ['move_left', 'move_right', 'dash_left', 'dash_right']:
            # 计算玩家1的攻击距离
            attack_range = ATTACK_RANGE
            if self.player1.used_charge_level == 1:
                attack_range += CHARGE_1_RANGE_BONUS
            elif self.player1.used_charge_level == 2:
                attack_range += CHARGE_2_RANGE_BONUS
            
            # 计算移动前后的距离
            distance_before = abs(p1_pos_before - p2_pos_before)
            distance_after = abs(self.player1.position - self.player2.position)
            
            # 判断闪避
            if (distance_before <= attack_range and 
                distance_after > attack_range and 
                self.player1.vulnerable_action == 'attack' and 
                not self.player1.action_dealt_damage):
                print(f"💨 {self.player2.name} 闪避了{self.player1.name}的攻击！")
                self.player1.apply_stun(DODGE_STUN_FRAMES, self.turn, current_frame)
    
    def _check_counter(self, current_frame):
        """检查防御反击"""
        from config import COUNTER_DAMAGE, COUNTER_FAIL_STUN_FRAMES
        
        # 检查玩家1的反击
        if self.player1.countering:
            if self.player2.action_dealt_damage:
                print(f"⚔️ {self.player1.name} 反击成功！")
                self.player2.take_damage(COUNTER_DAMAGE)
            else:
                print(f"❌ {self.player1.name} 反击失败，硬直！")
                self.player1.apply_stun(COUNTER_FAIL_STUN_FRAMES, self.turn, current_frame)
        
        # 检查玩家2的反击
        if self.player2.countering:
            if self.player1.action_dealt_damage:
                print(f"⚔️ {self.player2.name} 反击成功！")
                self.player1.take_damage(COUNTER_DAMAGE)
            else:
                print(f"❌ {self.player2.name} 反击失败，硬直！")
                self.player2.apply_stun(COUNTER_FAIL_STUN_FRAMES, self.turn, current_frame)
    
    def _handle_control_release(self, p1_action, p2_action):
        """处理控制解除"""
        # 玩家1控制着玩家2
        if self.player2.controlled and p1_action:
            if p1_action not in ['control', 'grab', 'throw', 'move_left', 'move_right', 'dash_left', 'dash_right']:
                print(f"🔓 {self.player1.name}执行了{p1_action}，解除对{self.player2.name}的控制")
                
                old_pos = self.player2.position
                if self.player2.is_left:
                    new_pos = max(1, self.player2.position - 1)
                else:
                    new_pos = min(MAP_SIZE, self.player2.position + 1)
                
                self.player2.position = new_pos
                if new_pos != old_pos:
                    print(f"   {self.player2.name} 被推到位置 {self.player2.position}")
                
                self.player2.controlled = False
        
        # 玩家2控制着玩家1
        if self.player1.controlled and p2_action:
            if p2_action not in ['control', 'grab', 'throw', 'move_left', 'move_right', 'dash_left', 'dash_right']:
                print(f"🔓 {self.player2.name}执行了{p2_action}，解除对{self.player1.name}的控制")
                
                old_pos = self.player1.position
                if self.player1.is_left:
                    new_pos = max(1, self.player1.position - 1)
                else:
                    new_pos = min(MAP_SIZE, self.player1.position + 1)
                
                self.player1.position = new_pos
                if new_pos != old_pos:
                    print(f"   {self.player1.name} 被推到位置 {self.player1.position}")
                
                self.player1.controlled = False
    
    def get_winner(self):
        """获取胜者"""
        if not self.player1.is_alive() and not self.player2.is_alive():
            return "平局"
        elif not self.player1.is_alive():
            return self.player2.name
        elif not self.player2.is_alive():
            return self.player1.name
        return None
    
    def show_final_result(self):
        """显示最终结果"""
        winner = self.get_winner()
        
        print(f"\n{SEPARATOR}")
        print(f"🏆 战斗结束！")
        print(f"回合数: {self.turn}")
        
        if winner == "平局":
            print(f"结果: 平局")
        elif winner:
            print(f"胜者: {winner}")
        
        print(f"\n最终状态：")
        self.player1.show_status()
        self.player2.show_status()
        print(SEPARATOR)


if __name__ == "__main__":
    print("=== 测试 CombatManager ===\n")
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=4)
    
    combat = CombatManager(alice, bob)
    combat.execute_turn(["charge", "attack"], ["defend", "attack"])
    combat.show_final_result()