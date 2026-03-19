import PyInstaller.__main__
import os
import shutil

if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

PyInstaller.__main__.run([
    'gameui.py',
    '--name=BattleGame',
    '--onefile',
    '--windowed',
    '--hidden-import=pygame',
    '--hidden-import=socket',
    '--hidden-import=pickle',
    '--hidden-import=threading',
    '--hidden-import=ai_player',
    '--clean',
])

print("\n" + "="*50)
print("✅ 打包完成！")
print("📁 可执行文件: dist/BattleGame.exe")
print("="*50)