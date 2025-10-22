"""
main.py
主程序入口 - 完全状态化终极版测试
"""

from player import Player
from combat_manager import CombatManager


def test_throw():
    """测试投掷功能"""
    print("=" * 60)
    print("测试：投掷功能（完全状态化版本）")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob")
    combat.execute_turn(['control', 'attack'], ['defend', 'defend'])
    
    print("\n回合2：Alice投掷Bob（应该击退3格）")
    combat.execute_turn(['throw', 'attack'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob最终位置: {bob.position}")
    print(f"预期：5或6（从2被投掷向右3格）")


def test_dodge():
    """测试闪避功能"""
    print("\n" + "=" * 60)
    print("测试：闪避功能（完全状态化版本）")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Bob攻击（距离1），Alice右移闪避")
    combat.execute_turn(['move_right', 'attack'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob的locked_frames: {bob.locked_frames}")
    print(f"预期：Bob应该被硬直（闪避成功）")


def test_combo():
    """测试连击系统"""
    print("\n" + "=" * 60)
    print("测试：连击系统")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Bob连续攻击Alice")
    combat.execute_turn(['defend', 'defend'], ['attack', 'attack'])
    
    print("\n回合2：Bob继续攻击Alice（第3次）")
    combat.execute_turn(['defend', 'defend'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Alice的locked_frames: {alice.locked_frames}")
    print(f"预期：Alice应该被硬直（连击3次）")


def test_dash_collision():
    """测试冲刺碰撞"""
    print("\n" + "=" * 60)
    print("测试：冲刺碰撞检测")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：双方冲刺相向")
    combat.execute_turn(['dash_right', 'attack'], ['dash_left', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ 最终位置：Alice={alice.position}, Bob={bob.position}")
    print(f"预期：应该在3和4相遇（冲突后回退）")


def test_throw_burst_interaction():
    """测试投掷+爆血交互（核心测试）"""
    print("\n" + "=" * 60)
    print("测试：投掷+爆血交互 ⭐ 核心测试")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=2)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob（重叠在位置2）")
    combat.execute_turn(['control', 'attack'], ['defend', 'defend'])
    
    print("\n回合2：Alice投掷Bob，Bob同时爆血")
    print("关键：爆血伤害应该基于'结算后距离'而非当前距离")
    combat.execute_turn(['throw', 'attack'], ['burst', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n验证：")
    print(f"Bob位置={bob.position}（应该是5，从2被投掷+3）")
    print(f"Alice HP={alice.hp}")
    print(f"预期伤害计算：")
    print(f"  - 当前距离=0 → 旧设计：Alice受6伤")
    print(f"  - 结算后距离=3 → 新设计：Alice受3伤 ✅")
    print(f"  - Bob自损：3+3=6")


def test_grab_burst_interaction():
    """测试抱摔+爆血交互（核心测试）"""
    print("\n" + "=" * 60)
    print("测试：抱摔+爆血交互 ⭐ 核心测试")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=2)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob")
    combat.execute_turn(['control', 'attack'], ['defend', 'defend'])
    
    print("\n回合2：Alice抱摔Bob，Bob同时爆血")
    print("关键：抱摔buff+1，爆血基于结算后距离")
    combat.execute_turn(['grab', 'attack'], ['burst', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n验证：")
    print(f"Bob位置={bob.position}（应该从2推到3）")
    print(f"Alice HP={alice.hp}")
    print(f"预期伤害：")
    print(f"  - 如果Bob移动到3：爆血伤=(6-1)+1=6")
    print(f"  - 如果Bob被挡住（距离0）：爆血伤=(6-0)+1=7（满伤）")
    print(f"  - Bob受伤：4(抱摔)+自损")


def test_invalid_grab():
    """测试无效抱摔（对手未被控制）"""
    print("\n" + "=" * 60)
    print("测试：无效抱摔（前置条件检查）")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice尝试抱摔Bob（Bob未被控制）")
    combat.execute_turn(['grab', 'attack'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n验证：")
    print(f"Bob HP={bob.hp}（应该是20，抱摔应该被阻止）")
    print(f"预期：_preprocess阻止了grab，不会生成任何状态")


def main():
    """主函数"""
    while True:
        print("\n" + "=" * 60)
        print("完全状态化终极版 - 测试菜单")
        print("=" * 60)
        print("1. 测试投掷功能")
        print("2. 测试闪避功能")
        print("3. 测试连击系统")
        print("4. 测试冲刺碰撞")
        print("5. 测试投掷+爆血交互 ⭐")
        print("6. 测试抱摔+爆血交互 ⭐")
        print("7. 测试无效抱摔（前置条件）⭐")
        print("8. 退出")
        print("=" * 60)
        
        choice = input("请选择: ").strip()
        
        if choice == "1":
            test_throw()
        elif choice == "2":
            test_dodge()
        elif choice == "3":
            test_combo()
        elif choice == "4":
            test_dash_collision()
        elif choice == "5":
            test_throw_burst_interaction()
        elif choice == "6":
            test_grab_burst_interaction()
        elif choice == "7":
            test_invalid_grab()
        elif choice == "8":
            print("\n测试完成！")
            break
        else:
            print("\n无效选择，请重试")


if __name__ == "__main__":
    main()