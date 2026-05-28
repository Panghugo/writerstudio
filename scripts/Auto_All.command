#!/bin/bash
cd "$(dirname "$0")/.."

echo "========================================"
echo "      Writer Studio legacy CLI flow     "
echo "========================================"
echo "This all-in-one terminal flow is deprecated."
echo "For the current web app, use ./Start_Web.command and open http://localhost:5001."
echo ""

if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

# 1. 先运行生成器
echo "Step 1: 正在生成黑金排版..."
"$PYTHON_CMD" app.py

# 2. 如果生成成功，继续运行发布器
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Step 2: 正在启动上传助手..."
    "$PYTHON_CMD" publisher.py
else
    echo "❌ 生成过程出错，已停止。"
fi

echo ""
echo "✅ 所有任务结束。请按回车键关闭..."
read -r
