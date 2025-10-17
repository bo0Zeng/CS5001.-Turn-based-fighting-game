"""
combat_manager.py
战斗管理器 - 管理整个战斗流程
"""

from player import Player
from actions import Actions
from config import SEPARATOR


class CombatManager:
    """战斗管理器 - 控制战斗流程"""
    
    def __init__(self, player1, player2):
        """
        初始化战斗
        
        Args:
            player1: 玩家1
            player2: 玩家2
        """
        self.player1 = player1
        self.player2 = player2
        self.turn = 0
        self.battle_log = []  # 战斗日志
        
        # 确定玩家的左右位置（根据初始位置）
        if player1.position < player2.position:
            player1.is_left = True
            player2.is_left = False
        else:
            player1.is_left = False
            player2.is_left = True
    
    def get_distance(self):
        """计算两个玩家之间的距离"""
        return abs(self.player1.position - self.player2.position)
    
    def show_battle_status(self):
        """显示战场状态"""
        print(f"\n{SEPARATOR}")
        print(f"回合 {self.turn} | 距离: {self.get_distance()}格")
        self.player1.show_status()
        self.player2.show_status()
        print(SEPARATOR)
    
    def execute_turn(self, p1_actions, p2_actions):
        """
        执行一个回合（2帧）
        
        Args:
            p1_actions: 玩家1的行动列表 ["punch", "kick"] 或 ["punch", None]（硬直锁定）
            p2_actions: 玩家2的行动列表 ["defend", "punch"] 或 [None, "punch"]（硬直锁定）
        
        Returns:
            bool: 战斗是否继续（True=继续，False=结束）
        """
        self.turn += 1
        self.show_battle_status()
        
        # 清理过期的锁定
        self.player1.clear_expired_locks(self.turn)
        self.player2.clear_expired_locks(self.turn)
        
        print(f"\n{self.player1.name} 行动: {p1_actions}")
        print(f"{self.player2.name} 行动: {p2_actions}")
        
        # 执行2帧
        for frame in range(2):
            current_frame = frame + 1
            print(f"\n--- 第 {current_frame} 帧 ---")
            
            # 重置单帧状态
            self.player1.reset_frame_status()
            self.player2.reset_frame_status()
            
            # 获取当前帧的行动
            p1_action = p1_actions[frame] if frame < len(p1_actions) else None
            p2_action = p2_actions[frame] if frame < len(p2_actions) else None
            
            # 检查硬直锁定（优先级最高）
            if self.player1.is_frame_locked(self.turn, current_frame):
                print(f"🔒 {self.player1.name} 第{current_frame}帧被硬直锁定！")
                p1_action = None
            
            if self.player2.is_frame_locked(self.turn, current_frame):
                print(f"🔒 {self.player2.name} 第{current_frame}帧被硬直锁定！")
                p2_action = None
            
            # 检查行动取消状态（控制导致的）
            if self.player1.actions_cancelled and p1_action:
                print(f"⛔ {self.player1.name} 行动已被取消！")
                p1_action = None
            
            if self.player2.actions_cancelled and p2_action:
                print(f"⛔ {self.player2.name} 行动已被取消！")
                p2_action = None
            
            # 检查被控制状态（被控制时只能用防御和爆血）
            if self.player1.controlled and p1_action:
                if p1_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player1.name} 被控制，只能使用防御或爆血！")
                    p1_action = None
            
            if self.player2.controlled and p2_action:
                if p2_action not in ['defend', 'burst']:
                    print(f"⛓️ {self.player2.name} 被控制，只能使用防御或爆血！")
                    p2_action = None
            
            # 执行行动（同时执行）
            if p1_action:
                self._execute_action(self.player1, self.player2, p1_action, 
                                   self.turn, current_frame)
                
                # 控制者执行非移动动作，解除控制并推开对手
                if self.player2.controlled and p1_action not in ['move_forward', 'move_back', 'dash']:
                    if p1_action not in ['control', 'grab', 'throw']:  # grab和throw已经处理了推开
                        print(f"🔓 {self.player1.name}执行了{p1_action}，解除对{self.player2.name}的控制")
                        
                        # 将被控制者推开1格
                        old_pos = self.player2.position
                        if self.player2.is_left:
                            new_pos = max(1, self.player2.position - 1)
                        else:
                            new_pos = min(MAP_SIZE, self.player2.position + 1)
                        
                        self.player2.position = new_pos
                        if new_pos != old_pos:
                            print(f"   {self.player2.name} 被推到位置 {self.player2.position}")
                        
                        self.player2.controlled = False
            
            if p2_action:
                self._execute_action(self.player2, self.player1, p2_action, 
                                   self.turn, current_frame)
                
                # 控制者执行非移动动作，解除控制并推开对手
                if self.player1.controlled and p2_action not in ['move_forward', 'move_back', 'dash']:
                    if p2_action not in ['control', 'grab', 'throw']:  # grab和throw已经处理了推开
                        print(f"🔓 {self.player2.name}执行了{p2_action}，解除对{self.player1.name}的控制")
                        
                        # 将被控制者推开1格
                        old_pos = self.player1.position
                        if self.player1.is_left:
                            new_pos = max(1, self.player1.position - 1)
                        else:
                            new_pos = min(MAP_SIZE, self.player1.position + 1)
                        
                        self.player1.position = new_pos
                        if new_pos != old_pos:
                            print(f"   {self.player1.name} 被推到位置 {self.player1.position}")
                        
                        self.player1.controlled = False
            
            # 检查胜负
            if not self.player1.is_alive() or not self.player2.is_alive():
                return False
        
        # 回合结束处理
        self.player1.update_turn_status()
        self.player2.update_turn_status()
        
        return True
    
    def _execute_action(self, actor, target, action, current_turn, current_frame):
        """
        执行单个行动
        
        Args:
            actor: 行动者
            target: 目标
            action: 行动名称
            current_turn: 当前回合号
            current_frame: 当前帧号
        """
        distance = self.get_distance()
        
        # 攻击类（需要传递回合和帧信息）
        if action == "punch":
            Actions.punch(actor, target, distance, current_turn, current_frame)
        elif action == "kick":
            Actions.kick(actor, target, distance, current_turn, current_frame)
        
        # 控制类
        elif action == "control":
            Actions.control(actor, target, distance)
        elif action == "grab":
            Actions.grab(actor, target)
        elif action == "throw":
            Actions.throw(actor, target)
        
        # 防御类
        elif action == "defend":
            Actions.defend(actor)
        
        # 移动类（需要传递opponent参数）
        elif action == "move_forward":
            Actions.move_forward(actor, target)
        elif action == "move_back":
            Actions.move_back(actor, target)
        elif action == "dash":
            Actions.dash(actor, target)
        
        # 特殊类
        elif action == "burst":
            Actions.burst(actor, target, distance)
        
        else:
            print(f"❓ 未知行动: {action}")
    
    def get_winner(self):
        """
        获取胜者
        
        Returns:
            str: 胜者名字，或"平局"，或None（战斗继续）
        """
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
        else:
            print(f"战斗未结束")
        
        print(f"\n最终状态：")
        self.player1.show_status()
        self.player2.show_status()
        print(SEPARATOR)


if __name__ == "__main__":
    # 测试代码
    print("=== 测试 CombatManager ===\n")
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=4)
    
    combat = CombatManager(alice, bob)
    
    # 回合1
    combat.execute_turn(
        ["kick", "kick"],
        ["move_back", "defend"]
    )
    
    # 回合2
    combat.execute_turn(
        ["move_forward", "punch"],
        ["punch", "punch"]
    )
    
    combat.show_final_result()