@echo off
chcp 65001 > nul
title LLM Live2D 项目启动

echo 正在激活虚拟环境...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo 错误：无法激活虚拟环境。请先运行 setup.bat。
    pause
    exit /b 1
)

echo 正在启动应用程序 (app.py)...
python app.py
if %errorlevel% neq 0 (
    echo 错误：app.py 运行失败。请检查脚本是否有错误。
    pause
    exit /b 1
)

echo 应用程序已关闭。
pause