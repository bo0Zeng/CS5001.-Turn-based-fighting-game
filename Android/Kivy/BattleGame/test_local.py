"""
test_local.py - 本地测试Kivy版本（打包前测试）

用法：python3 test_local.py

这个脚本会在电脑上运行Kivy版本，方便在打包前快速测试和调试。
"""

import os
import sys

def check_dependencies():
    """检查依赖是否安装"""
    print("=" * 60)
    print("检查依赖...")
    print("=" * 60)
    
    # 检查Kivy
    try:
        import kivy
        print(f"✓ Kivy已安装: {kivy.__version__}")
    except ImportError:
        print("✗ Kivy未安装")
        print("\n请运行: pip install kivy")
        return False
    
    # 检查必需文件
    required_files = [
        'main.py',
        'player.py',
        'combat_manager.py',
        'config.py',
        'game_data.py',
        'state.py',
        'actions.py'
    ]
    
    missing_files = []
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename} 存在")
        else:
            print(f"✗ {filename} 不存在")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n错误：缺少文件: {', '.join(missing_files)}")
        return False
    
    print("\n" + "=" * 60)
    print("所有依赖检查通过！")
    print("=" * 60)
    return True


def run_game():
    """运行游戏"""
    print("\n启动游戏...\n")
    
    # 导入并运行
    from main import BattleGameApp
    
    try:
        app = BattleGameApp()
        app.run()
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║       Battle Game - Kivy版本本地测试                       ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 检查依赖
    if not check_dependencies():
        print("\n依赖检查失败，请先解决上述问题。")
        sys.exit(1)
    
    # 提示
    print("\n提示:")
    print("  - 使用鼠标模拟触摸操作")
    print("  - 窗口大小可以调整")
    print("  - 按 ESC 可以退出")
    print("  - 如果游戏运行正常，就可以打包APK了！")
    
    input("\n按 Enter 开始...")
    
    # 运行游戏
    success = run_game()
    
    if success:
        print("\n测试完成！")
    else:
        print("\n测试中出现错误，请检查日志。")
        sys.exit(1)


if __name__ == '__main__':
    main()