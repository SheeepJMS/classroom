@echo off
REM Render数据库调试工具快速启动脚本 (Windows版本)

echo === Render数据库调试工具 ===
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未添加到PATH
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version

REM 检查依赖
echo.
echo 检查依赖包...
python -c "import flask, flask_sqlalchemy, sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 缺少依赖包，正在安装...
    pip install flask flask-sqlalchemy sqlalchemy pg8000
)

REM 检查环境变量
echo.
echo 检查环境变量...
if "%DATABASE_URL%"=="" (
    echo ⚠️  DATABASE_URL 未设置
    echo 请设置DATABASE_URL环境变量
    echo 例如: set DATABASE_URL=postgresql://user:pass@host:port/dbname
    pause
    exit /b 1
) else (
    echo ✅ DATABASE_URL 已设置
)

REM 选择运行模式
echo.
echo 请选择运行模式:
echo 1) Web调试界面 (推荐)
echo 2) 命令行检查
echo 3) 命令行修复
echo 4) 检查并修复
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo 启动Web调试界面...
    python render_database_debugger.py
) else if "%choice%"=="2" (
    echo 运行数据库检查...
    python fix_render_database.py --check
) else if "%choice%"=="3" (
    echo 运行数据库修复...
    python fix_render_database.py --fix
) else if "%choice%"=="4" (
    echo 运行检查并修复...
    python fix_render_database.py
) else (
    echo 无效选择，启动Web调试界面...
    python render_database_debugger.py
)

pause
