#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "      🎨 Writer Studio 全自动流程        "
echo "========================================"

# 1. 先运行生成器
echo "Step 1: 正在生成黑金排版..."
python3 app.py

# 2. 如果生成成功，继续运行发布器
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Step 2: 正在启动上传助手..."
    python3 publisher.py
else
    echo "❌ 生成过程出错，已停止。"
fi

echo ""
echo "✅ 所有任务结束。请按回车键关闭..."
read