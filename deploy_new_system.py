#!/usr/bin/env python3
"""
部署全新系统的脚本
"""

import os
import sys
import subprocess

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} 失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} 出错: {str(e)}")
        return False
    return True

def main():
    """主函数"""
    print("🚀 开始部署全新系统...")
    
    # 1. 备份当前app.py
    if run_command("cp app.py app_backup_old.py", "备份当前app.py"):
        print("✅ 已备份当前app.py为app_backup_old.py")
    
    # 2. 替换app.py
    if run_command("cp app_new.py app.py", "替换app.py"):
        print("✅ 已替换app.py")
    
    # 3. 清理数据库
    print("🧹 清理数据库...")
    if run_command("python clean_database.py", "清理数据库"):
        print("✅ 数据库清理完成")
    
    # 4. 提交到Git
    if run_command("git add .", "添加文件到Git"):
        if run_command("git commit -m '完全重写后端系统 - 解决所有已知问题'", "提交更改"):
            if run_command("git push origin main", "推送到远程仓库"):
                print("✅ 部署完成！")
                print("🎉 全新系统已部署到Render")
                print("📋 新系统特点:")
                print("   - 简化的数据模型")
                print("   - 可靠的轮次管理")
                print("   - 正确的分数累计")
                print("   - 清晰的错误处理")
            else:
                print("❌ 推送到远程仓库失败")
        else:
            print("❌ 提交更改失败")
    else:
        print("❌ 添加文件到Git失败")

if __name__ == "__main__":
    main()
