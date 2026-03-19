#!/bin/bash

# ================================================================
# Battle Game - 虚拟环境构建脚本
# 使用前请先运行 setup_venv.sh 创建虚拟环境
# ================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

VENV_DIR="venv_battlegame"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    print_error "虚拟环境不存在！"
    echo ""
    echo "请先运行: ./setup_venv.sh"
    exit 1
fi

# 检查是否已激活虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    print_info "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
    print_success "虚拟环境已激活"
else
    print_info "虚拟环境已激活: $VIRTUAL_ENV"
fi

# 显示标题
echo ""
echo "================================================================"
echo "  Battle Game - 构建脚本（虚拟环境）"
echo "================================================================"
echo ""

# 验证buildozer
if ! command -v buildozer &> /dev/null; then
    print_error "未找到buildozer！"
    echo ""
    echo "请先运行: ./setup_venv.sh"
    exit 1
fi

print_success "Buildozer已安装: $(buildozer --version 2>&1 | head -1)"

# 功能选择菜单
echo ""
echo "请选择操作："
echo "1) 构建Debug版APK"
echo "2) 构建Release版APK"
echo "3) 清理构建缓存"
echo "4) 安装APK到手机"
echo "5) 查看构建日志"
echo "6) 本地测试"
echo "7) 显示环境信息"
echo "0) 退出"
echo ""

read -p "请输入选项 (0-7): " choice

case $choice in
    1)
        print_info "开始构建Debug版APK..."
        print_warning "首次构建需要60-90分钟，请耐心等待"
        
        buildozer -v android debug 2>&1 | tee build.log
        
        if [ -f "bin/battlegame-1.0-arm64-v8a-debug.apk" ]; then
            print_success "构建成功！"
            apk_size=$(du -h bin/battlegame-1.0-arm64-v8a-debug.apk | cut -f1)
            echo ""
            echo "📦 APK信息："
            echo "   位置: bin/battlegame-1.0-arm64-v8a-debug.apk"
            echo "   大小: $apk_size"
            echo ""
            echo "💡 安装方法："
            echo "   adb install -r bin/battlegame-1.0-arm64-v8a-debug.apk"
        else
            print_error "构建失败，请查看 build.log"
            exit 1
        fi
        ;;
        
    2)
        print_info "开始构建Release版APK..."
        
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
            echo "APK位置: bin/battlegame-1.0-arm64-v8a-release.apk"
        else
            print_error "构建失败，请查看 build.log"
            exit 1
        fi
        ;;
        
    3)
        print_warning "确定要清理构建缓存吗？"
        echo "这将删除："
        echo "  - .buildozer/ 目录（SDK/NDK等，约2-3GB）"
        echo "  - bin/ 目录"
        echo ""
        read -p "继续? (y/n): " confirm
        
        if [ "$confirm" = "y" ]; then
            print_info "清理中..."
            buildozer android clean
            rm -rf .buildozer
            rm -rf bin
            print_success "清理完成"
        fi
        ;;
        
    4)
        print_info "通过USB安装APK到手机..."
        
        if ! command -v adb &> /dev/null; then
            print_error "未找到adb"
            echo ""
            echo "请安装Android SDK Platform Tools："
            echo "  Ubuntu: sudo apt-get install adb"
            echo "  或从官网下载: https://developer.android.com/studio/releases/platform-tools"
            exit 1
        fi
        
        devices=$(adb devices | grep -v "List" | grep "device$" | wc -l)
        if [ $devices -eq 0 ]; then
            print_error "未检测到设备"
            echo ""
            echo "请确保："
            echo "  1. 手机已连接USB"
            echo "  2. 已开启USB调试"
            echo "  3. 已授权此计算机"
            exit 1
        fi
        
        print_success "检测到 $devices 个设备"
        
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
        ;;
        
    5)
        print_info "显示最近100行构建日志..."
        
        if [ -f "build.log" ]; then
            tail -n 100 build.log
        else
            print_warning "未找到build.log文件"
        fi
        ;;
        
    6)
        print_info "运行本地测试..."
        
        if [ -f "test_local.py" ]; then
            python test_local.py
        elif [ -f "main.py" ]; then
            python main.py
        else
            print_error "未找到测试文件"
        fi
        ;;
        
    7)
        print_info "环境信息"
        echo ""
        echo "📍 虚拟环境："
        echo "   $VIRTUAL_ENV"
        echo ""
        echo "🐍 Python版本："
        python --version
        echo ""
        echo "📦 已安装的包："
        pip list | grep -E "buildozer|cython|kivy"
        echo ""
        echo "💾 Buildozer缓存："
        if [ -d "$HOME/.buildozer" ]; then
            du -sh "$HOME/.buildozer" 2>/dev/null || echo "   ~/.buildozer/"
        else
            echo "   未创建（首次构建时会自动创建）"
        fi
        echo ""
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
echo ""
print_info "退出虚拟环境: deactivate"