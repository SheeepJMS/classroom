#!/usr/bin/env python3
"""
Render数据库调试工具启动器
跨平台启动脚本，支持Windows和Linux
"""

import os
import sys
import subprocess
import platform

def check_python():
    """检查Python环境"""
    print("=== Render数据库调试工具 ===")
    print()
    
    python_version = sys.version_info
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    return True

def check_dependencies():
    """检查依赖包"""
    print("检查依赖包...")
    
    required_packages = ['flask', 'flask_sqlalchemy', 'sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    if missing_packages:
        print(f"\n正在安装缺失的包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages + ['pg8000'])
            print("✅ 依赖包安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖包安装失败")
            return False
    
    return True

def check_environment():
    """检查环境变量"""
    print("\n检查环境变量...")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL 未设置")
        print("请设置DATABASE_URL环境变量")
        if platform.system() == "Windows":
            print("例如: set DATABASE_URL=postgresql://user:pass@host:port/dbname")
        else:
            print("例如: export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return False
    else:
        print("✅ DATABASE_URL 已设置")
        return True

def show_menu():
    """显示菜单"""
    print("\n请选择运行模式:")
    print("1) Web调试界面 (推荐)")
    print("2) 命令行检查")
    print("3) 命令行修复")
    print("4) 检查并修复")
    print("5) 退出")
    print()

def run_web_debugger():
    """运行Web调试界面"""
    print("启动Web调试界面...")
    try:
        import render_database_debugger
        render_database_debugger.main()
    except ImportError:
        print("❌ 找不到render_database_debugger.py文件")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def run_command_line_tool(mode):
    """运行命令行工具"""
    try:
        import fix_render_database
        if mode == "check":
            print("运行数据库检查...")
            fix_render_database.check_database_status()
        elif mode == "fix":
            print("运行数据库修复...")
            fix_render_database.fix_database()
        else:
            print("运行检查并修复...")
            fix_render_database.check_database_status()
            fix_render_database.fix_database()
    except ImportError:
        print("❌ 找不到fix_render_database.py文件")
    except Exception as e:
        print(f"❌ 运行失败: {e}")

def main():
    """主函数"""
    # 检查Python环境
    if not check_python():
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查环境变量
    if not check_environment():
        return
    
    # 主循环
    while True:
        show_menu()
        
        try:
            choice = input("请输入选择 (1-5): ").strip()
        except KeyboardInterrupt:
            print("\n\n程序已退出")
            break
        
        if choice == "1":
            run_web_debugger()
            break
        elif choice == "2":
            run_command_line_tool("check")
            break
        elif choice == "3":
            run_command_line_tool("fix")
            break
        elif choice == "4":
            run_command_line_tool("both")
            break
        elif choice == "5":
            print("程序已退出")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
