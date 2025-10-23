#!/usr/bin/env python3
"""
清理数据库并创建新的简化表结构
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 数据库配置
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 未找到DATABASE_URL环境变量")
        return None
    
    # 转换数据库URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    return app, db

def clean_database(app, db):
    """清理数据库"""
    print("🧹 开始清理数据库...")
    
    with app.app_context():
        try:
            # 删除旧的复杂表
            tables_to_drop = [
                'student_submissions',
                'course_rounds', 
                'courses',
                'students',
                'classes',
                'competition_goals'
            ]
            
            for table in tables_to_drop:
                try:
                    db.session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    print(f"✅ 删除表: {table}")
                except Exception as e:
                    print(f"⚠️ 删除表 {table} 时出错: {str(e)}")
            
            # 创建新的简化表
            print("🔨 创建新的简化表...")
            
            # 创建 simple_courses 表
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS simple_courses (
                    id VARCHAR(36) PRIMARY KEY,
                    class_id VARCHAR(36) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    current_round INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建 simple_students 表
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS simple_students (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    class_id VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建 simple_submissions 表
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS simple_submissions (
                    id VARCHAR(36) PRIMARY KEY,
                    student_id VARCHAR(36) NOT NULL,
                    course_id VARCHAR(36) NOT NULL,
                    round_number INTEGER NOT NULL,
                    answer VARCHAR(100) NOT NULL,
                    is_correct BOOLEAN DEFAULT FALSE,
                    answer_time FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建 simple_rounds 表
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS simple_rounds (
                    id VARCHAR(36) PRIMARY KEY,
                    course_id VARCHAR(36) NOT NULL,
                    round_number INTEGER NOT NULL,
                    correct_answer VARCHAR(100) NOT NULL,
                    question_score INTEGER DEFAULT 1,
                    is_completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建索引
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_simple_courses_class_id 
                ON simple_courses(class_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_simple_students_class_id 
                ON simple_students(class_id)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_simple_submissions_course_round 
                ON simple_submissions(course_id, round_number)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_simple_rounds_course_round 
                ON simple_rounds(course_id, round_number)
            """))
            
            db.session.commit()
            print("✅ 数据库清理和重建完成！")
            
            # 验证表创建
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'simple_%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 创建的表: {tables}")
            
        except Exception as e:
            print(f"❌ 清理数据库失败: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    print("启动数据库清理脚本...")
    
    app, db = create_app()
    if not app:
        return
    
    clean_database(app, db)

if __name__ == "__main__":
    main()
