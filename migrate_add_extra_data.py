#!/usr/bin/env python3
"""
添加 extra_data 字段到 course_attendances 表的迁移脚本
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 导入应用配置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_add_extra_data():
    """添加 extra_data 字段到 course_attendances 表"""
    print("=" * 50)
    print("开始迁移：添加 extra_data 字段到 course_attendances 表")
    print("=" * 50)
    
    with app.app_context():
        try:
            # 检查表是否存在
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'course_attendances'
                );
            """))
            
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("⚠️  course_attendances 表不存在，跳过迁移")
                return True
            
            # 检查 extra_data 字段是否已存在
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'course_attendances' 
                    AND column_name = 'extra_data'
                );
            """))
            
            column_exists = result.fetchone()[0]
            
            if column_exists:
                print("✅ extra_data 字段已存在，无需迁移")
                return True
            
            # 添加 extra_data 字段
            print("正在添加 extra_data 字段...")
            
            # 对于 PostgreSQL
            if 'postgresql' in str(db.engine.url):
                db.session.execute(text("""
                    ALTER TABLE course_attendances 
                    ADD COLUMN extra_data TEXT;
                """))
            # 对于 SQLite
            elif 'sqlite' in str(db.engine.url):
                # SQLite 不支持直接添加列，需要使用 ALTER TABLE ... ADD COLUMN
                db.session.execute(text("""
                    ALTER TABLE course_attendances 
                    ADD COLUMN extra_data TEXT;
                """))
            else:
                # 通用方法
                db.session.execute(text("""
                    ALTER TABLE course_attendances 
                    ADD COLUMN extra_data TEXT;
                """))
            
            db.session.commit()
            print("✅ extra_data 字段添加成功！")
            
            # 验证字段是否添加成功
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'course_attendances' 
                    AND column_name = 'extra_data'
                );
            """))
            
            if result.fetchone()[0]:
                print("✅ 验证：extra_data 字段已成功添加到 course_attendances 表")
                return True
            else:
                print("⚠️  警告：字段可能未成功添加")
                return False
                
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = migrate_add_extra_data()
    if success:
        print("\n🎉 迁移完成！")
        sys.exit(0)
    else:
        print("\n❌ 迁移失败，请检查错误信息")
        sys.exit(1)



