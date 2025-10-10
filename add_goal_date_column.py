#!/usr/bin/env python3
"""
添加goal_date字段到competition_goals表
这个脚本可以在Render Shell中运行
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append('/opt/render/project/src')

# 设置环境变量
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')
os.environ['USE_DATABASE'] = 'true'

from app import app
from models import db, CompetitionGoal

def add_goal_date_column():
    """添加goal_date字段到competition_goals表"""
    print("=== 开始添加goal_date字段 ===")
    
    with app.app_context():
        try:
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
            existing_goals = CompetitionGoal.query.all()
            for goal in existing_goals:
                if goal.created_date:
                    default_goal_date = goal.created_date.date() + timedelta(days=77)
                    goal.goal_date = default_goal_date
                    print(f"设置竞赛目标 '{goal.title}' 的日期为 {default_goal_date}")
            
            db.session.commit()
            print("goal_date字段添加成功！")
            
            # 验证字段是否添加成功
            goals = CompetitionGoal.query.all()
            print(f"验证：共有 {len(goals)} 个竞赛目标")
            for goal in goals:
                print(f"  - {goal.title}: goal_date = {goal.goal_date}")
                
        except Exception as e:
            print(f"添加字段时发生错误: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    add_goal_date_column()
