#!/usr/bin/env python3
"""
Render 数据库迁移脚本：为学生表添加状态字段
在 Render 上运行此脚本来更新数据库结构
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

# 创建 Flask 应用
app = Flask(__name__)

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    with app.app_context():
        try:
            # 检查 students 表是否存在
            result = db.engine.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'students'
                );
            """)
            
            if not result.fetchone()[0]:
                print("students 表不存在，跳过迁移")
                return
            
            # 检查 status 字段是否存在
            result = db.engine.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'students' 
                    AND column_name = 'status'
                );
            """)
            
            if result.fetchone()[0]:
                print("status 字段已存在")
            else:
                print("添加 status 字段...")
                db.engine.execute('ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT \'active\'')
                print("status 字段添加成功")
            
            # 检查 graduated_date 字段是否存在
            result = db.engine.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'students' 
                    AND column_name = 'graduated_date'
                );
            """)
            
            if result.fetchone()[0]:
                print("graduated_date 字段已存在")
            else:
                print("添加 graduated_date 字段...")
                db.engine.execute('ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP')
                print("graduated_date 字段添加成功")
            
            # 更新现有学生的状态为 active
            print("更新现有学生状态...")
            db.engine.execute("UPDATE students SET status = 'active' WHERE status IS NULL")
            
            # 检查更新了多少条记录
            result = db.engine.execute("SELECT COUNT(*) FROM students WHERE status = 'active'")
            count = result.fetchone()[0]
            print(f"更新了 {count} 个学生的状态")
            
            print("数据库迁移完成！")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("Render 数据库迁移脚本")
    print("=" * 50)
    
    if not DATABASE_URL:
        print("错误: 未找到 DATABASE_URL 环境变量")
        sys.exit(1)
    
    print(f"数据库 URL: {DATABASE_URL[:50]}...")
    
    success = migrate_database()
    
    if success:
        print("迁移成功完成！")
        sys.exit(0)
    else:
        print("迁移失败！")
        sys.exit(1)
