#!/usr/bin/env python3
"""
数据库迁移脚本：为CompetitionGoal表添加goal_date字段
"""

import os
from app import app
from models import db, CompetitionGoal
from datetime import datetime, date

def migrate_goal_date():
    """为CompetitionGoal表添加goal_date字段"""
    print("=== 开始迁移goal_date字段 ===")
    
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
                print("goal_date字段已存在，跳过迁移")
                return
            
            # 添加goal_date字段
            print("添加goal_date字段...")
            db.session.execute("""
                ALTER TABLE competition_goals 
                ADD COLUMN goal_date DATE
            """)
            
            # 为现有记录设置默认的goal_date（创建日期后77天）
            print("为现有记录设置默认goal_date...")
            existing_goals = CompetitionGoal.query.all()
            for goal in existing_goals:
                if goal.created_date:
                    # 设置默认竞赛日期为创建日期后77天
                    from datetime import timedelta
                    default_goal_date = goal.created_date.date() + timedelta(days=77)
                    goal.goal_date = default_goal_date
                    print(f"设置竞赛目标 {goal.title} 的日期为 {default_goal_date}")
            
            db.session.commit()
            print("goal_date字段迁移完成")
            
        except Exception as e:
            print(f"迁移过程中发生错误: {e}")
            db.session.rollback()
            # 如果字段已存在，忽略错误
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("字段可能已存在，迁移可能已完成")
            else:
                raise e

if __name__ == "__main__":
    migrate_goal_date()
