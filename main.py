"""
main.py
主程序入口 - 完全状态化重构版测试
"""

from player import Player
from combat_manager import CombatManager


def test_attack_state_based():
    """测试攻击状态化（距离检查）"""
    print("=" * 60)
    print("测试：攻击状态化 - 距离不够自动取消")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，超出攻击范围1
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice攻击Bob（距离太远，应该miss）")
    combat.execute_turn(['attack', 'defend'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob HP: {bob.hp}（应该是20，攻击被取消）")


def test_dodge_state_based():
    """测试闪避状态化"""
    print("\n" + "=" * 60)
    print("测试：闪避状态化 - 基于状态变化判断")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Bob攻击（距离1），Alice右移闪避")
    combat.execute_turn(['move_right', 'attack'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob的locked_frames: {bob.locked_frames}")
    print(f"预期：Bob应该被硬直（闪避成功）")


def test_charge_state_based():
    """测试蓄力状态化（pending机制）"""
    print("\n" + "=" * 60)
    print("测试：蓄力状态化 - pending → 冲突检测 → 结算")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice蓄力，Bob攻击Alice")
    combat.execute_turn(['charge', 'defend'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Alice charge_level: {alice.charge_level}")
    print(f"预期：0（蓄力被打断，pending状态被取消）")
    print(f"✅ Alice HP: {alice.hp}")
    print(f"预期：18（1攻击伤害 + 1蓄力被打断惩罚）")


def test_control_state_based():
    """测试控制状态化（距离检查）"""
    print("\n" + "=" * 60)
    print("测试：控制状态化 - 距离不够自动取消")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，超出控制范围1
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob（距离太远，应该失败）")
    combat.execute_turn(['control', 'defend'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob controlled: {bob.controlled}")
    print(f"预期：False（控制被取消）")
    print(f"✅ Alice locked_frames: {alice.locked_frames}")
    print(f"预期：Alice应该被硬直（控制失败惩罚）")


def test_counter_state_based():
    """测试反击状态化"""
    print("\n" + "=" * 60)
    print("测试：反击状态化 - 准备 → 检查 → 结算")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice反击，Bob攻击Alice")
    combat.execute_turn(['counter', 'defend'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Alice HP: {alice.hp}（应该是20，格挡成功）")
    print(f"✅ Bob HP: {bob.hp}（应该是19，被反击）")


def test_charge_control_conflict():
    """测试蓄力+控制冲突"""
    print("\n" + "=" * 60)
    print("测试：蓄力被控制打断")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice蓄力，Bob控制Alice")
    combat.execute_turn(['charge', 'defend'], ['control', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Alice charge_level: {alice.charge_level}")
    print(f"预期：0（蓄力被控制打断）")
    print(f"✅ Alice controlled: {alice.controlled}")
    print(f"预期：True（被控制）")


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


def test_control_grab_combo():
    """测试控制+抱摔连招（第一帧control，第二帧grab）"""
    print("\n" + "=" * 60)
    print("测试：控制+抱摔连招 ⭐ 新功能")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice第一帧控制，第二帧抱摔")
    print("关键：即使控制可能失败，第二帧也应该允许输入grab")
    combat.execute_turn(['control', 'grab'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob HP: {bob.hp}")
    print(f"✅ Bob controlled: {bob.controlled}")
    print(f"预期：Bob被控制且受到抱摔伤害")


def test_control_fail_but_grab_allowed():
    """测试控制失败但第二帧仍允许输入抱摔"""
    print("\n" + "=" * 60)
    print("测试：控制失败但抱摔被允许输入 ⭐ 边界测试")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，控制会失败
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice第一帧控制（会失败），第二帧抱摔")
    print("关键：即使控制失败，第二帧也应该允许输入grab")
    print("但实际执行时，由于Alice第一帧会硬直，第二帧的grab会被取消")
    combat.execute_turn(['control', 'grab'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n✅ Bob controlled: {bob.controlled}")
    print(f"✅ Alice locked_frames: {alice.locked_frames}")
    print(f"预期：Bob未被控制，Alice被硬直，grab未执行")


def main():
    """主函数"""
    while True:
        print("\n" + "=" * 60)
        print("完全状态化重构版 - 测试菜单")
        print("=" * 60)
        print("1. 测试攻击状态化（距离检查）")
        print("2. 测试闪避状态化")
        print("3. 测试蓄力状态化（pending机制）⭐")
        print("4. 测试控制状态化（距离检查）⭐")
        print("5. 测试反击状态化 ⭐")
        print("6. 测试蓄力+控制冲突")
        print("7. 测试投掷+爆血交互 ⭐")
        print("8. 测试控制+抱摔连招 ⭐ 新增")
        print("9. 测试控制失败但允许输入抱摔 ⭐ 新增")
        print("0. 退出")
        print("=" * 60)
        
        choice = input("请选择: ").strip()
        
        if choice == "1":
            test_attack_state_based()
        elif choice == "2":
            test_dodge_state_based()
        elif choice == "3":
            test_charge_state_based()
        elif choice == "4":
            test_control_state_based()
        elif choice == "5":
            test_counter_state_based()
        elif choice == "6":
            test_charge_control_conflict()
        elif choice == "7":
            test_throw_burst_interaction()
        elif choice == "8":
            test_control_grab_combo()
        elif choice == "9":
            test_control_fail_but_grab_allowed()
        elif choice == "0":
            print("\n测试完成！")
            break
        else:
            print("\n无效选择，请重试")


if __name__ == "__main__":
    main()