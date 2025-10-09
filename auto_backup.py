#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动数据备份系统
在应用启动时自动创建数据备份，防止数据丢失
"""

import os
import json
import shutil
from datetime import datetime

def create_backup():
    """创建数据备份"""
    data_file = 'app_data.json'
    
    if not os.path.exists(data_file):
        print("数据文件不存在，跳过备份")
        return
    
    # 创建备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'app_data.json.backup_{timestamp}'
    
    try:
        # 复制文件
        shutil.copy2(data_file, backup_file)
        print(f"数据备份已创建: {backup_file}")
        
        # 清理旧备份（保留最近10个）
        cleanup_old_backups()
        
    except Exception as e:
        print(f"备份失败: {e}")

def cleanup_old_backups():
    """清理旧的备份文件，只保留最近10个"""
    backup_files = []
    
    # 查找所有备份文件
    for file in os.listdir('.'):
        if file.startswith('app_data.json.backup_') and file.endswith('.json'):
            backup_files.append(file)
    
    # 按修改时间排序
    backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 删除多余的备份文件
    if len(backup_files) > 10:
        for old_backup in backup_files[10:]:
            try:
                os.remove(old_backup)
                print(f"已删除旧备份: {old_backup}")
            except Exception as e:
                print(f"删除备份文件失败 {old_backup}: {e}")

def restore_from_backup(backup_file):
    """从备份恢复数据"""
    if not os.path.exists(backup_file):
        print(f"备份文件不存在: {backup_file}")
        return False
    
    try:
        shutil.copy2(backup_file, 'app_data.json')
        print(f"数据已从备份恢复: {backup_file}")
        return True
    except Exception as e:
        print(f"恢复失败: {e}")
        return False

def list_backups():
    """列出所有可用的备份文件"""
    backup_files = []
    
    for file in os.listdir('.'):
        if file.startswith('app_data.json.backup_'):
            backup_files.append(file)
    
    backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    print("可用的备份文件:")
    for i, backup in enumerate(backup_files, 1):
        mtime = datetime.fromtimestamp(os.path.getmtime(backup))
        print(f"{i}. {backup} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    return backup_files

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'backup':
            create_backup()
        elif command == 'list':
            list_backups()
        elif command == 'restore' and len(sys.argv) > 2:
            backup_file = sys.argv[2]
            restore_from_backup(backup_file)
        else:
            print("用法:")
            print("  python auto_backup.py backup     # 创建备份")
            print("  python auto_backup.py list       # 列出备份")
            print("  python auto_backup.py restore <backup_file>  # 恢复备份")
    else:
        # 默认创建备份
        create_backup()
