"""
main.py
主程序入口 - 测试 / Version Test
"""

from player import Player
from combat_manager import CombatManager


def test_attack_state_based():
    """测试攻击状态化（距离检查） / Test attack state-based (distance check)"""
    print("=" * 60)
    print("测试：攻击状态化 - 距离不够自动取消 / Test: Attack state-based - Auto-cancel when distance insufficient")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，超出攻击范围1 / Distance 3, exceeds attack range 1
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice攻击Bob（距离太远，应该miss） / Round 1: Alice attacks Bob (distance too far, should miss)")
    combat.execute_turn(['attack', 'defend'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nBob HP: {bob.hp}（应该是20，攻击被取消） / Bob HP: {bob.hp} (should be 20, attack cancelled)")


def test_dodge_state_based():
    """测试闪避状态化 / Test dodge state-based"""
    print("\n" + "=" * 60)
    print("测试：闪避状态化 - 基于状态变化判断 / Test: Dodge state-based - Judgment based on state changes")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Bob攻击（距离1），Alice右移闪避 / Round 1: Bob attacks (distance 1), Alice moves right to dodge")
    combat.execute_turn(['move_right', 'attack'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nBob的locked_frames: {bob.locked_frames} / Bob's locked_frames: {bob.locked_frames}")
    print(f"预期：Bob应该被硬直（闪避成功） / Expected: Bob should be stunned (dodge successful)")


def test_charge_state_based():
    """测试蓄力状态化（pending机制） / Test charge state-based (pending mechanism)"""
    print("\n" + "=" * 60)
    print("测试：蓄力状态化 - pending → 冲突检测 → 结算 / Test: Charge state-based - pending → conflict detection → settlement")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice蓄力，Bob攻击Alice / Round 1: Alice charges, Bob attacks Alice")
    combat.execute_turn(['charge', 'defend'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nAlice charge_level: {alice.charge_level} / Alice charge_level: {alice.charge_level}")
    print(f"预期：0（蓄力被打断，pending状态被取消） / Expected: 0 (charge interrupted, pending state cancelled)")
    print(f"Alice HP: {alice.hp} / Alice HP: {alice.hp}")
    print(f"预期：18（1攻击伤害 + 1蓄力被打断惩罚） / Expected: 18 (1 attack damage + 1 charge interruption penalty)")


def test_control_state_based():
    """测试控制状态化（距离检查） / Test control state-based (distance check)"""
    print("\n" + "=" * 60)
    print("测试：控制状态化 - 距离不够自动取消 / Test: Control state-based - Auto-cancel when distance insufficient")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，超出控制范围1 / Distance 3, exceeds control range 1
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob（距离太远，应该失败） / Round 1: Alice controls Bob (distance too far, should fail)")
    combat.execute_turn(['control', 'defend'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nBob controlled: {bob.controlled} / Bob controlled: {bob.controlled}")
    print(f"预期：False（控制被取消） / Expected: False (control cancelled)")
    print(f"Alice locked_frames: {alice.locked_frames} / Alice locked_frames: {alice.locked_frames}")
    print(f"预期：Alice应该被硬直（控制失败惩罚） / Expected: Alice should be stunned (control failure penalty)")


def test_counter_state_based():
    """测试反击状态化 / Test counter state-based"""
    print("\n" + "=" * 60)
    print("测试：反击状态化 - 准备 → 检查 → 结算 / Test: Counter state-based - Prepare → Check → Settlement")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice反击，Bob攻击Alice / Round 1: Alice counters, Bob attacks Alice")
    combat.execute_turn(['counter', 'defend'], ['attack', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nAlice HP: {alice.hp}（应该是20，格挡成功） / Alice HP: {alice.hp} (should be 20, block successful)")
    print(f"Bob HP: {bob.hp}（应该是19，被反击） / Bob HP: {bob.hp} (should be 19, countered)")


def test_charge_control_conflict():
    """测试蓄力+控制冲突 / Test charge + control conflict"""
    print("\n" + "=" * 60)
    print("测试：蓄力被控制打断 / Test: Charge interrupted by control")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice蓄力，Bob控制Alice / Round 1: Alice charges, Bob controls Alice")
    combat.execute_turn(['charge', 'defend'], ['control', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nAlice charge_level: {alice.charge_level} / Alice charge_level: {alice.charge_level}")
    print(f"预期：0（蓄力被控制打断） / Expected: 0 (charge interrupted by control)")
    print(f"Alice controlled: {alice.controlled} / Alice controlled: {alice.controlled}")
    print(f"预期：True（被控制） / Expected: True (controlled)")


def test_throw_burst_interaction():
    """测试投掷+爆血交互（核心测试） / Test throw + burst interaction (core test)"""
    print("\n" + "=" * 60)
    print("测试：投掷+爆血交互 ⭐ 核心测试 / Test: Throw + burst interaction ⭐ Core test")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=2)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice控制Bob（重叠在位置2） / Round 1: Alice controls Bob (overlapping at position 2)")
    combat.execute_turn(['control', 'attack'], ['defend', 'defend'])
    
    print("\n回合2：Alice投掷Bob，Bob同时爆血 / Round 2: Alice throws Bob, Bob bursts simultaneously")
    print("关键：爆血伤害应该基于'结算后距离'而非当前距离 / Key: Burst damage should be based on 'settled distance' not current distance")
    combat.execute_turn(['throw', 'attack'], ['burst', 'defend'])
    
    combat.show_final_result()
    
    print(f"\n验证： / Verification:")
    print(f"Bob位置={bob.position}（应该是5，从2被投掷+3） / Bob position={bob.position} (should be 5, thrown from 2 + 3)")
    print(f"Alice HP={alice.hp} / Alice HP={alice.hp}")
    print(f"预期伤害计算： / Expected damage calculation:")
    print(f"  - 当前距离=0 → 旧设计：Alice受6伤 / - Current distance=0 → Old design: Alice takes 6 damage")
    print(f"  - 结算后距离=3 → 新设计：Alice受3伤 / - Settled distance=3 → New design: Alice takes 3 damage")
    print(f"  - Bob自损：3+3=6 / - Bob self-damage: 3+3=6")


def test_control_grab_combo():
    """测试控制+抱摔连招（第一帧control，第二帧grab） / Test control + grab combo (first frame control, second frame grab)"""
    print("\n" + "=" * 60)
    print("测试：控制+抱摔连招 ⭐ 新功能 / Test: Control + grab combo ⭐ New feature")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=3)
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice第一帧控制，第二帧抱摔 / Round 1: Alice first frame control, second frame grab")
    print("关键：即使控制可能失败，第二帧也应该允许输入grab / Key: Even if control might fail, second frame should allow grab input")
    combat.execute_turn(['control', 'grab'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nBob HP: {bob.hp} / Bob HP: {bob.hp}")
    print(f"Bob controlled: {bob.controlled} / Bob controlled: {bob.controlled}")
    print(f"预期：Bob被控制且受到抱摔伤害 / Expected: Bob controlled and takes grab damage")


def test_control_fail_but_grab_allowed():
    """测试控制失败但第二帧仍允许输入抱摔 / Test control fails but grab is still allowed in second frame"""
    print("\n" + "=" * 60)
    print("测试：控制失败但抱摔被允许输入 ⭐ 边界测试 / Test: Control fails but grab is allowed ⭐ Edge case test")
    print("=" * 60)
    
    alice = Player("Alice", position=2)
    bob = Player("Bob", position=5)  # 距离3，控制会失败 / Distance 3, control will fail
    combat = CombatManager(alice, bob)
    
    print("\n回合1：Alice第一帧控制（会失败），第二帧抱摔 / Round 1: Alice first frame control (will fail), second frame grab")
    print("关键：即使控制失败，第二帧也应该允许输入grab / Key: Even if control fails, second frame should allow grab input")
    print("但实际执行时，由于Alice第一帧会硬直，第二帧的grab会被取消 / But in actual execution, since Alice will be stunned in first frame, second frame grab will be cancelled")
    combat.execute_turn(['control', 'grab'], ['defend', 'defend'])
    
    combat.show_final_result()
    
    print(f"\nBob controlled: {bob.controlled} / Bob controlled: {bob.controlled}")
    print(f"Alice locked_frames: {alice.locked_frames} / Alice locked_frames: {alice.locked_frames}")
    print(f"预期：Bob未被控制，Alice被硬直，grab未执行 / Expected: Bob not controlled, Alice stunned, grab not executed")


def main():
    """主函数 / Main function"""
    while True:
        print("\n" + "=" * 60)
        print("完全状态化重构版 - 测试菜单 / Fully State-based Refactored Version - Test Menu")
        print("=" * 60)
        print("1. 测试攻击状态化（距离检查） / Test attack state-based (distance check)")
        print("2. 测试闪避状态化 / Test dodge state-based")
        print("3. 测试蓄力状态化（pending机制）⭐ / Test charge state-based (pending mechanism) ⭐")
        print("4. 测试控制状态化（距离检查）⭐ / Test control state-based (distance check) ⭐")
        print("5. 测试反击状态化 ⭐ / Test counter state-based ⭐")
        print("6. 测试蓄力+控制冲突 / Test charge + control conflict")
        print("7. 测试投掷+爆血交互 ⭐ / Test throw + burst interaction ⭐")
        print("8. 测试控制+抱摔连招 ⭐ 新增 / Test control + grab combo ⭐ New")
        print("9. 测试控制失败但允许输入抱摔 ⭐ 新增 / Test control fails but grab allowed ⭐ New")
        print("0. 退出 / Exit")
        print("=" * 60)
        
        choice = input("请选择: / Please choose: ").strip()
        
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
            print("\n测试完成！ / Test completed!")
            break
        else:
            print("\n无效选择，请重试 / Invalid choice, please try again")


if __name__ == "__main__":
    main()