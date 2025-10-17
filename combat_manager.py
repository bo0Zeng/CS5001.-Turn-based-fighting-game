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
            p1_actions: 玩家1的行动列表 ["punch", "kick"]
            p2_actions: 玩家2的行动列表 ["defend", "punch"]
        
        Returns:
            bool: 战斗是否继续（True=继续，False=结束）
        """
        self.turn += 1
        self.show_battle_status()
        
        print(f"\n{self.player1.name} 行动: {p1_actions}")
        print(f"{self.player2.name} 行动: {p2_actions}")
        
        # 执行2帧
        for frame in range(2):
            print(f"\n--- 第 {frame + 1} 帧 ---")
            
            # 重置单帧状态
            self.player1.reset_frame_status()
            self.player2.reset_frame_status()
            
            # 获取当前帧的行动
            p1_action = p1_actions[frame] if frame < len(p1_actions) else None
            p2_action = p2_actions[frame] if frame < len(p2_actions) else None
            
            # 检查被控制状态
            if self.player1.controlled and p1_action:
                print(f"⛓️ {self.player1.name} 被控制，无法行动！")
                p1_action = None
            
            if self.player2.controlled and p2_action:
                print(f"⛓️ {self.player2.name} 被控制，无法行动！")
                p2_action = None
            
            # 检查硬直状态
            if self.player1.stun_frames > 0 and p1_action:
                print(f"😵 {self.player1.name} 硬直中，无法行动！")
                p1_action = None
            
            if self.player2.stun_frames > 0 and p2_action:
                print(f"😵 {self.player2.name} 硬直中，无法行动！")
                p2_action = None
            
            # 执行行动（同时执行）
            if p1_action:
                self._execute_action(self.player1, self.player2, p1_action)
            
            if p2_action:
                self._execute_action(self.player2, self.player1, p2_action)
            
            # 检查胜负
            if not self.player1.is_alive() or not self.player2.is_alive():
                return False
        
        # 回合结束处理
        self.player1.update_turn_status()
        self.player2.update_turn_status()
        
        return True
    
    def _execute_action(self, actor, target, action):
        """
        执行单个行动
        
        Args:
            actor: 行动者
            target: 目标
            action: 行动名称
        """
        distance = self.get_distance()
        
        # 攻击类
        if action == "punch":
            Actions.punch(actor, target, distance)
        elif action == "kick":
            Actions.kick(actor, target, distance)
        
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
        
        # 移动类
        elif action == "move_forward":
            Actions.move_forward(actor)
        elif action == "move_back":
            Actions.move_back(actor)
        elif action == "dash":
            Actions.dash(actor)
        
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