"""
main.py
主程序入口 - 游戏启动文件
"""

# 导入我们自己写的模块
from player import Player
from combat_manager import CombatManager
from config import SEPARATOR


def demo_battle():
    """演示战斗"""
    print("=== 演示战斗 ===\n")
    
    # 创建玩家
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=4)
    
    # 创建战斗管理器
    combat = CombatManager(alice, bob)
    
    # 战斗脚本
    battle_script = [
        # 回合1：试探
        (["kick", "kick"], ["move_back", "kick"]),
        
        # 回合2：接近
        (["move_forward", "move_forward"], ["defend", "kick"]),
        
        # 回合3：控摔组合！
        (["control", "grab"], ["punch", "punch"]),
        
        # 回合4：互殴
        (["punch", "punch"], ["punch", "punch"]),
    ]
    
    # 执行战斗
    for p1_actions, p2_actions in battle_script:
        if not combat.execute_turn(p1_actions, p2_actions):
            break  # 战斗结束
    
    # 显示结果
    combat.show_final_result()


def manual_battle():
    """手动输入战斗"""
    print("=== 手动战斗模式 ===\n")
    
    # 创建玩家
    p1_name = input("玩家1名字: ") or "Alice"
    p2_name = input("玩家2名字: ") or "Bob"
    
    player1 = Player(p1_name, position=2)
    player2 = Player(p2_name, position=4)
    
    combat = CombatManager(player1, player2)
    
    print("\n可用招式：")
    print("攻击: punch, kick")
    print("控制: control, grab, throw")
    print("防御: defend")
    print("移动: move_forward, move_back, dash")
    print("特殊: burst")
    
    # 战斗循环
    while True:
        print(f"\n{SEPARATOR}")
        print(f"请输入行动（每回合2个）")
        
        # 玩家1输入
        print(f"\n{player1.name}的回合：")
        p1_action1 = input("  第1帧: ").strip()
        p1_action2 = input("  第2帧: ").strip()
        
        # 玩家2输入
        print(f"\n{player2.name}的回合：")
        p2_action1 = input("  第1帧: ").strip()
        p2_action2 = input("  第2帧: ").strip()
        
        # 执行回合
        if not combat.execute_turn(
            [p1_action1, p1_action2],
            [p2_action1, p2_action2]
        ):
            break  # 战斗结束
        
        # 检查是否继续
        continue_battle = input("\n继续战斗? (y/n): ").strip().lower()
        if continue_battle != 'y':
            break
    
    # 显示结果
    combat.show_final_result()


def quick_test():
    """快速测试 - 测试所有招式"""
    print("=== 快速测试模式 ===\n")
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    # 测试1：基础攻击
    print("\n测试1：基础攻击")
    combat.execute_turn(["punch", "kick"], ["defend", "punch"])
    
    # 测试2：控摔组合
    print("\n测试2：控摔组合")
    alice.position = 2
    bob.position = 3
    combat.execute_turn(["control", "grab"], ["punch", "punch"])
    
    # 测试3：投掷
    print("\n测试3：投掷")
    alice.position = 2
    bob.position = 3
    combat.execute_turn(["control", "throw"], ["punch", "punch"])
    
    # 测试4：爆血
    print("\n测试4：爆血")
    alice.position = 2
    bob.position = 3
    combat.execute_turn(["burst", "punch"], ["defend", "defend"])
    
    combat.show_final_result()


def show_menu():
    """显示主菜单"""
    print(f"\n{SEPARATOR}")
    print("回合制战斗游戏")
    print(SEPARATOR)
    print("1. 演示战斗（自动）")
    print("2. 手动战斗（输入指令）")
    print("3. 快速测试（测试所有招式）")
    print("4. 退出")
    print(SEPARATOR)


def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("请选择: ").strip()
        
        if choice == "1":
            demo_battle()
        elif choice == "2":
            manual_battle()
        elif choice == "3":
            quick_test()
        elif choice == "4":
            print("\n感谢游玩！")
            break
        else:
            print("\n无效选择，请重试")


if __name__ == "__main__":
    # 当直接运行main.py时，执行主函数
    main()