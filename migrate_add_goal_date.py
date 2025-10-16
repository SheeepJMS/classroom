#!/usr/bin/env python3
"""
数据库迁移脚本：为competition_goals表添加goal_date字段
"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def migrate_add_goal_date():
    """为competition_goals表添加goal_date字段"""
    print("=== 开始添加goal_date字段 ===")
    
    # 获取数据库URL
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
    
    # 转换PostgreSQL URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    
    try:
        # 创建数据库连接
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 检查goal_date字段是否已存在
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='competition_goals' 
            AND column_name='goal_date'
        """))
        
        if result.fetchone():
            print("✅ goal_date字段已存在，跳过添加")
        else:
            print("添加goal_date字段...")
            # 添加goal_date字段
            session.execute(text("ALTER TABLE competition_goals ADD COLUMN goal_date DATE"))
            
            print("为现有记录设置默认goal_date...")
            # 为现有记录设置默认的goal_date（创建日期后77天）
            session.execute(text("""
                UPDATE competition_goals 
                SET goal_date = created_date::date + INTERVAL '77 days' 
                WHERE goal_date IS NULL
            """))
            
            session.commit()
            print("✅ goal_date字段添加成功！")
        
        # 验证结果
        result = session.execute(text("SELECT id, title, goal_date FROM competition_goals LIMIT 5"))
        goals = result.fetchall()
        if goals:
            print("\n验证结果:")
            for goal in goals:
                print(f"  - {goal[1]}: goal_date = {goal[2]}")
        
        session.close()
        print("\n🎉 迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        if 'sqlite' in database_url:
            print("SQLite数据库不支持此迁移，请手动处理")
        raise

if __name__ == '__main__':
    migrate_add_goal_date()
