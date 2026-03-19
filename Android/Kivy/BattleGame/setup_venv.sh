#!/bin/bash

# ================================================================
# Battle Game - 虚拟环境安装脚本
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

echo "================================================================"
echo "  Battle Game - 虚拟环境配置脚本"
echo "================================================================"
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    print_error "未找到Python3，请先安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_success "Python3已安装: $PYTHON_VERSION"

# 虚拟环境目录
VENV_DIR="venv_battlegame"

# 检查是否已存在虚拟环境
if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在: $VENV_DIR"
    read -p "是否删除并重新创建？(y/n): " recreate
    if [ "$recreate" = "y" ]; then
        print_info "删除旧虚拟环境..."
        rm -rf "$VENV_DIR"
    else
        print_info "使用现有虚拟环境"
    fi
fi

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    print_info "创建虚拟环境: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    print_success "虚拟环境创建完成"
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
print_info "升级pip..."
python -m pip install --upgrade pip

# 安装依赖
print_info "安装项目依赖..."

echo ""
echo "安装以下包："
echo "  - buildozer (APK打包工具)"
echo "  - cython (Python编译器)"
echo "  - kivy (UI框架)"
echo ""

pip install buildozer cython kivy

print_success "Python依赖安装完成！"

# 检查系统依赖
echo ""
print_info "检查系统依赖..."

if command -v apt-get &> /dev/null; then
    print_info "检测到apt包管理器"
    
    read -p "是否安装系统依赖（需要sudo）？(y/n): " install_sys
    
    if [ "$install_sys" = "y" ]; then
        print_info "安装系统依赖..."
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
        
        print_success "系统依赖安装完成"
    fi
else
    print_warning "未检测到apt，请手动安装系统依赖"
    print_info "参考：https://buildozer.readthedocs.io/en/latest/installation.html"
fi

# 显示虚拟环境信息
echo ""
echo "================================================================"
print_success "虚拟环境配置完成！"
echo "================================================================"
echo ""
echo "📍 虚拟环境位置："
echo "   $(pwd)/$VENV_DIR"
echo ""
echo "📦 已安装的包："
pip list | grep -E "buildozer|cython|kivy"
echo ""
echo "💡 使用方法："
echo ""
echo "1. 激活虚拟环境："
echo "   source $VENV_DIR/bin/activate"
echo ""
echo "2. 运行构建："
echo "   buildozer android debug"
echo ""
echo "3. 退出虚拟环境："
echo "   deactivate"
echo ""
echo "4. 快速激活脚本（可选）："
cat > activate.sh << 'EOF'
#!/bin/bash
source venv_battlegame/bin/activate
echo "✓ 虚拟环境已激活"
echo "💡 运行 'deactivate' 退出虚拟环境"
EOF
chmod +x activate.sh
echo "   已创建 activate.sh 快捷脚本"
echo "   运行: source ./activate.sh"
echo ""
echo "================================================================"
echo ""

# 创建 .gitignore
if [ ! -f ".gitignore" ]; then
    print_info "创建 .gitignore 文件..."
    cat > .gitignore << 'EOF'
# 虚拟环境
venv_battlegame/
venv/
env/
ENV/

# Buildozer
.buildozer/
bin/
build.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Android
*.apk
*.aab
*.keystore

# IDE
.vscode/
.idea/
*.swp

# 其他
.DS_Store
EOF
    print_success "已创建 .gitignore"
fi

# 保持激活状态
print_warning "注意：这个脚本结束后虚拟环境会自动退出"
print_info "请手动运行: source $VENV_DIR/bin/activate"