[app]

# 应用名称
title = Battle Game

# 包名（使用反向域名格式）
package.name = battlegame

# 域名
package.domain = com.yourdomain

# 源代码目录
source.dir = .

# 源代码包含的文件
source.include_exts = py,png,jpg,kv,atlas,json

# 入口文件
source.main = main.py

# 版本号
version = 1.0

# 需求的Python模块
requirements = python3,kivy

# Android权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Android API版本
android.api = 31

# 最小API版本
android.minapi = 21

# Android NDK版本
android.ndk = 25b

# 是否接受SDK许可
android.accept_sdk_license = True

# 屏幕方向（landscape = 横屏）
orientation = landscape

# 全屏模式
fullscreen = 0

# Android架构
android.archs = arm64-v8a,armeabi-v7a

# 日志级别
log_level = 2

# 警告级别
warn_on_root = 1


[buildozer]

# 日志级别 (0 = error only, 1 = info, 2 = debug)
log_level = 2

# 警告作为错误
warn_on_root = 1
