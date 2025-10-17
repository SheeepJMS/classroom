#!/usr/bin/env python3
"""
数据库迁移脚本：为学生表添加状态字段
"""

from flask import Flask
from models import db, Student, init_db
from datetime import datetime

def migrate_student_status():
    """迁移学生状态字段"""
    app = Flask(__name__)
    
    # 数据库配置
    import os
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace(
            'postgres://', 'postgresql+pg8000://', 1)
    elif DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace(
            'postgresql://', 'postgresql+pg8000://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    init_db(app)
    
    with app.app_context():
        try:
            # 检查是否已经存在status字段
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('students')]
            
            if 'status' not in columns:
                print("添加status字段...")
                db.engine.execute('ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT \'active\'')
                print("status字段添加成功")
            else:
                print("status字段已存在")
                
            if 'graduated_date' not in columns:
                print("添加graduated_date字段...")
                db.engine.execute('ALTER TABLE students ADD COLUMN graduated_date DATETIME')
                print("graduated_date字段添加成功")
            else:
                print("graduated_date字段已存在")
                
            # 更新现有学生的状态为active
            students = Student.query.filter(Student.status.is_(None)).all()
            for student in students:
                student.status = 'active'
            
            db.session.commit()
            print(f"更新了 {len(students)} 个学生的状态")
            
            print("迁移完成！")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_student_status()
