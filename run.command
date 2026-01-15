#!/bin/bash

# 1. 强制进入当前脚本所在的文件夹
cd "$(dirname "$0")"

echo "📂 正在定位工作目录..."
pwd

echo "--------------------------------"

# 2. 智能判断：优先使用虚拟环境，没有则用系统环境
if [ -f "venv/bin/python3" ]; then
    echo "✅ 检测到 venv 虚拟环境，正在通过虚拟环境启动..."
    ./venv/bin/python3 app.py
else
    echo "⚠️ 未检测到虚拟环境文件夹 (venv)，尝试使用系统默认 Python..."
    python3 app.py
fi

echo "--------------------------------"
echo "🛑 程序运行结束。"
echo "👇 如果上面有报错信息 (Error)，请截图发给我。"
# 3. 关键：暂停在这里，等待用户按回车才关闭
read -p "按回车键关闭窗口..."