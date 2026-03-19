#!/bin/bash

# ================================================================
# Battle Game - Android APK 自动化构建脚本
# ================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示标题
echo "================================================================"
echo "  Battle Game - Android APK 构建脚本"
echo "================================================================"
echo ""

# 检查操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_info "检测到Linux系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    print_warning "检测到macOS，建议使用Linux环境"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    print_error "检测到Windows，请使用WSL（Windows Subsystem for Linux）"
    exit 1
fi

# 检查Python3
if ! command -v python3 &> /dev/null; then
    print_error "未找到Python3，请先安装"
    exit 1
fi

print_success "Python3已安装: $(python3 --version)"

# 检查pip3
if ! command -v pip3 &> /dev/null; then
    print_error "未找到pip3，请先安装"
    exit 1
fi

print_success "pip3已安装"

# 功能选择菜单
echo ""
echo "请选择操作："
echo "1) 安装依赖（首次使用）"
echo "2) 构建Debug版APK"
echo "3) 构建Release版APK"
echo "4) 清理构建缓存"
echo "5) 安装APK到手机"
echo "6) 查看构建日志"
echo "0) 退出"
echo ""

read -p "请输入选项 (0-6): " choice

case $choice in
    1)
        print_info "开始安装依赖..."
        
        # 更新pip
        python3 -m pip install --user --upgrade pip
        
        # 安装Buildozer
        print_info "安装Buildozer..."
        pip3 install --user --upgrade buildozer
        
        # 安装Cython
        print_info "安装Cython..."
        pip3 install --user --upgrade cython
        
        # 安装Kivy（用于本地测试）
        print_info "安装Kivy..."
        pip3 install --user kivy
        
        # 检查系统依赖
        print_info "检查系统依赖..."
        
        if command -v apt-get &> /dev/null; then
            print_info "检测到apt包管理器，安装系统依赖..."
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                git \
                zip \
                unzip \
                openjdk-17-jdk \
                autoconf \
                libtool \
                pkg-config \
                zlib1g-dev \
                libncurses5-dev \
                libncursesw5-dev \
                libtinfo5 \
                cmake \
                libffi-dev \
                libssl-dev
        fi
        
        # 添加到PATH
        export PATH=$PATH:~/.local/bin
        
        print_success "依赖安装完成！"
        print_info "请运行 'source ~/.bashrc' 或重新打开终端"
        ;;
        
    2)
        print_info "开始构建Debug版APK..."
        
        # 检查buildozer
        if ! command -v buildozer &> /dev/null; then
            print_error "未找到buildozer，请先运行选项1安装依赖"
            exit 1
        fi
        
        # 构建
        print_info "这可能需要30-90分钟（首次）或5-10分钟（后续）"
        buildozer -v android debug 2>&1 | tee build.log
        
        if [ -f "bin/battlegame-1.0-arm64-v8a-debug.apk" ]; then
            print_success "构建成功！"
            print_info "APK位置: bin/battlegame-1.0-arm64-v8a-debug.apk"
            
            # 显示APK信息
            apk_size=$(du -h bin/battlegame-1.0-arm64-v8a-debug.apk | cut -f1)
            print_info "APK大小: $apk_size"
        else
            print_error "构建失败，请查看 build.log"
            exit 1
        fi
        ;;
        
    3)
        print_info "开始构建Release版APK..."
        
        # 检查签名密钥
        if [ ! -f "my-release-key.keystore" ]; then
            print_warning "未找到签名密钥，开始生成..."
            read -p "请输入密钥密码: " keypass
            keytool -genkey -v \
                -keystore my-release-key.keystore \
                -alias my-key-alias \
                -keyalg RSA \
                -keysize 2048 \
                -validity 10000 \
                -storepass "$keypass"
        fi
        
        buildozer android release 2>&1 | tee build.log
        
        if [ -f "bin/battlegame-1.0-arm64-v8a-release.apk" ]; then
            print_success "Release版构建成功！"
            print_info "APK位置: bin/battlegame-1.0-arm64-v8a-release.apk"
        else
            print_error "构建失败，请查看 build.log"
            exit 1
        fi
        ;;
        
    4)
        print_warning "确定要清理构建缓存吗？这将删除所有下载的SDK和NDK"
        read -p "继续? (y/n): " confirm
        
        if [ "$confirm" = "y" ]; then
            print_info "清理中..."
            buildozer android clean
            rm -rf .buildozer
            rm -rf bin
            print_success "清理完成"
        fi
        ;;
        
    5)
        print_info "通过USB安装APK到手机..."
        
        # 检查adb
        if ! command -v adb &> /dev/null; then
            print_error "未找到adb，请先安装Android SDK Platform Tools"
            exit 1
        fi
        
        # 检查设备
        devices=$(adb devices | grep -v "List" | grep "device$" | wc -l)
        if [ $devices -eq 0 ]; then
            print_error "未检测到设备，请确保："
            echo "  1. 手机已连接USB"
            echo "  2. 已开启USB调试"
            echo "  3. 已授权此计算机"
            exit 1
        fi
        
        print_success "检测到 $devices 个设备"
        
        # 查找APK
        if [ -f "bin/battlegame-1.0-arm64-v8a-debug.apk" ]; then
            apk="bin/battlegame-1.0-arm64-v8a-debug.apk"
        elif [ -f "bin/battlegame-1.0-arm64-v8a-release.apk" ]; then
            apk="bin/battlegame-1.0-arm64-v8a-release.apk"
        else
            print_error "未找到APK文件，请先构建"
            exit 1
        fi
        
        print_info "安装: $apk"
        adb install -r "$apk"
        
        print_success "安装完成！"
        print_info "可以运行 'adb logcat | grep python' 查看日志"
        ;;
        
    6)
        print_info "显示最近的构建日志..."
        
        if [ -f "build.log" ]; then
            tail -n 100 build.log
        else
            print_warning "未找到build.log文件"
        fi
        ;;
        
    0)
        print_info "退出"
        exit 0
        ;;
        
    *)
        print_error "无效选项"
        exit 1
        ;;
esac

echo ""
print_success "操作完成！"