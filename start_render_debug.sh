#!/bin/bash
# Render数据库调试工具快速启动脚本

echo "=== Render数据库调试工具 ==="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查依赖
echo ""
echo "检查依赖包..."
python3 -c "import flask, flask_sqlalchemy, sqlalchemy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 依赖包已安装"
else
    echo "❌ 缺少依赖包，正在安装..."
    pip3 install flask flask-sqlalchemy sqlalchemy pg8000
fi

# 检查环境变量
echo ""
echo "检查环境变量..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL 未设置"
    echo "请设置DATABASE_URL环境变量"
    echo "例如: export DATABASE_URL='postgresql://user:pass@host:port/dbname'"
    exit 1
else
    echo "✅ DATABASE_URL 已设置"
fi

# 选择运行模式
echo ""
echo "请选择运行模式:"
echo "1) Web调试界面 (推荐)"
echo "2) 命令行检查"
echo "3) 命令行修复"
echo "4) 检查并修复"
echo ""
read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo "启动Web调试界面..."
        python3 render_database_debugger.py
        ;;
    2)
        echo "运行数据库检查..."
        python3 fix_render_database.py --check
        ;;
    3)
        echo "运行数据库修复..."
        python3 fix_render_database.py --fix
        ;;
    4)
        echo "运行检查并修复..."
        python3 fix_render_database.py
        ;;
    *)
        echo "无效选择，启动Web调试界面..."
        python3 render_database_debugger.py
        ;;
esac
