"""
build.py
自动打包脚本
"""

import PyInstaller.__main__
import os
import shutil

# 清理旧的打包文件
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

# 打包配置
PyInstaller.__main__.run([
    'game_ui.py',
    '--name=BattleGame',
    '--onedir',  # 使用文件夹模式（更稳定）
    '--windowed',  # Windows下不显示控制台
    '--add-data=*.py:.',
    '--hidden-import=pygame',
    '--hidden-import=socket',
    '--hidden-import=pickle',
    '--hidden-import=threading',
    '--clean',
])

print("\n" + "="*50)
print("✅ 打包完成！")
print("📁 可执行文件在: dist/BattleGame/")
print("="*50)