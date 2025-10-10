#!/usr/bin/env python3
"""
简单的goal_date字段添加脚本
专门用于Render环境
"""

import os
import sys
from datetime import datetime, timedelta

# 设置环境变量
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')
os.environ['USE_DATABASE'] = 'true'

def add_goal_date_column():
    """添加goal_date字段到competition_goals表"""
    print("=== 开始添加goal_date字段 ===")
    
    try:
        # 导入Flask应用
        from app import app, db
        
        with app.app_context():
            # 检查goal_date字段是否已存在
            result = db.session.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='competition_goals' 
                AND column_name='goal_date'
            """).fetchone()
            
            if result:
                print("goal_date字段已存在，跳过添加")
                return
            
            print("添加goal_date字段...")
            # 添加goal_date字段
            db.session.execute("ALTER TABLE competition_goals ADD COLUMN goal_date DATE")
            
            print("为现有记录设置默认goal_date...")
            # 为现有记录设置默认的goal_date（创建日期后77天）
            db.session.execute("""
                UPDATE competition_goals 
                SET goal_date = created_date::date + INTERVAL '77 days' 
                WHERE created_date IS NOT NULL
            """)
            
            db.session.commit()
            print("✅ goal_date字段添加成功！")
            
            # 验证字段是否添加成功
            result = db.session.execute("SELECT COUNT(*) FROM competition_goals").scalar()
            print(f"验证：共有 {result} 个竞赛目标")
                
    except Exception as e:
        print(f"❌ 添加字段时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_goal_date_column()
