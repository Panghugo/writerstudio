#!/bin/bash
# 1. 进入当前文件夹
cd "$(dirname "$0")"

# 2. 运行图形界面程序 (自动检测虚拟环境)
if [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 WriterStudio_GUI.py
else
    python3 WriterStudio_GUI.py
fi