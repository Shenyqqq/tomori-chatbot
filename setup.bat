@echo off

chcp 65001 > nul

title LLM Live2D 项目安装



echo 正在检查 Python 安装...

python --version >nul 2>&1

if %errorlevel% neq 0 (
    echo 错误：未检测到 Python。请确保 Python 已安装并添加到 PATH。
    echo 建议从 https://www.python.org/downloads/ 安装 Python 3.9 或更高版本。
    pause
    exit /b 1
)



echo 正在创建虚拟环境 'venv'...

python -m venv venv

if %errorlevel% neq 0 (
    echo 错误：虚拟环境创建失败。
    pause
    exit /b 1
)



echo 正在激活虚拟环境并安装依赖...

call venv\Scripts\activate

if %errorlevel% neq 0 (
    echo 错误：无法激活虚拟环境。
    pause
    exit /b 1
)



python.exe -m pip install --upgrade pip

if %errorlevel% neq 0 (
    echo 警告：pip 升级失败，但可能不影响后续安装。
)



pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

if %errorlevel% neq 0 (
    echo 错误：PyTorch 及其相关库安装失败。请检查命令和网络连接。
    pause
    exit /b 1
)



pip install -r requirements.txt --index-url https://pypi.org/simple/

if %errorlevel% neq 0 (
    echo 错误：依赖安装失败。请检查 requirements.txt 文件和网络连接。
    pause
    exit /b 1
)



echo 正在运行 build_VecDB.py 构建 RAG 数据库...

python build_VecDB.py

if %errorlevel% neq 0 (
    echo 错误：build_VecDB.py 运行失败。请检查脚本是否有错误。
    pause
    exit /b 1
)



echo.

echo 安装和数据库构建完成！

echo 您现在可以运行 start.bat 来启动应用程序。

pause