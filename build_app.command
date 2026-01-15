#!/bin/bash

# Writer Studio 一键打包脚本
# 使用方法：双击运行或在终端执行 ./build_app.command

echo "🚀 Writer Studio 打包工具"
echo "=========================="
echo ""

# 获取脚本所在目录
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "📂 项目目录: $PROJECT_DIR"
echo ""

# 检查 PyInstaller 是否安装
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller 未安装"
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
    
    if [ $? -ne 0 ]; then
        echo "❌ PyInstaller 安装失败，请手动安装："
        echo "   pip3 install pyinstaller"
        read -p "按回车键退出..."
        exit 1
    fi
fi

echo "✅ PyInstaller 已就绪"
echo ""

# 询问是否清理旧构建
read -p "是否清理旧的构建文件？(y/n) [推荐: y]: " CLEAN
if [ "$CLEAN" = "y" ] || [ "$CLEAN" = "Y" ] || [ "$CLEAN" = "" ]; then
    echo "🧹 清理旧构建..."
    rm -rf build dist
    echo "✅ 清理完成"
    echo ""
fi

# 开始打包
echo "📦 开始打包..."
echo "   这可能需要几分钟时间，请耐心等待..."
echo ""

pyinstaller "Writer Studio.spec"

# 检查打包结果
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 打包成功！"
    echo ""
    echo "📍 应用位置: $PROJECT_DIR/dist/Writer Studio.app"
    echo ""
    
    # 询问是否创建分发包
    read -p "是否创建 ZIP 分发包？(y/n) [推荐: y]: " CREATE_ZIP
    if [ "$CREATE_ZIP" = "y" ] || [ "$CREATE_ZIP" = "Y" ] || [ "$CREATE_ZIP" = "" ]; then
        echo "📦 创建 ZIP 包..."
        cd dist
        
        # 添加时间戳到文件名
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        ZIP_NAME="Writer_Studio_${TIMESTAMP}.zip"
        
        zip -r "$ZIP_NAME" "Writer Studio.app" > /dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ ZIP 包创建成功: $ZIP_NAME"
            echo "   大小: $(du -h "$ZIP_NAME" | cut -f1)"
        else
            echo "❌ ZIP 包创建失败"
        fi
        cd ..
    fi
    
    echo ""
    echo "📋 后续步骤："
    echo "   1. 测试应用: 双击 'dist/Writer Studio.app'"
    echo "   2. 分发给他人: 发送 'dist/Writer_Studio_*.zip'"
    echo "   3. 首次打开可能需要右键 -> 打开（macOS 安全提示）"
    echo ""
    
    # 询问是否打开 dist 文件夹
    read -p "是否打开 dist 文件夹查看结果？(y/n): " OPEN_DIST
    if [ "$OPEN_DIST" = "y" ] || [ "$OPEN_DIST" = "Y" ]; then
        open dist
    fi
    
else
    echo ""
    echo "❌ 打包失败！"
    echo ""
    echo "🔍 排查建议："
    echo "   1. 查看上方错误信息"
    echo "   2. 检查 build/Writer Studio/warn-Writer Studio.txt"
    echo "   3. 确认所有依赖已安装: pip3 install customtkinter pillow requests"
    echo ""
fi

echo ""
read -p "按回车键退出..."
