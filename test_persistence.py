#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据持久化
验证数据库是否正确保存数据
"""

from app import app
from models import db, Class, CompetitionGoal

def test_data_persistence():
    """测试数据持久化"""
    print("=== 测试数据持久化 ===")
    
    try:
        with app.app_context():
            # 测试创建班级
            test_class = Class(
                id='test-class-001',
                name='测试班级',
                description='这是一个测试班级',
                is_active=True
            )
            
            # 检查是否已存在
            existing = Class.query.get('test-class-001')
            if existing:
                print("✅ 测试班级已存在，数据持久化正常")
                print(f"班级名称: {existing.name}")
            else:
                db.session.add(test_class)
                db.session.commit()
                print("✅ 测试班级创建成功，数据持久化正常")
            
            # 测试创建竞赛目标
            test_goal = CompetitionGoal(
                id='test-goal-001',
                title='测试竞赛目标',
                description='这是一个测试竞赛目标',
                target_score=100
            )
            
            existing_goal = CompetitionGoal.query.get('test-goal-001')
            if existing_goal:
                print("✅ 测试竞赛目标已存在，数据持久化正常")
                print(f"竞赛目标: {existing_goal.title}")
            else:
                db.session.add(test_goal)
                db.session.commit()
                print("✅ 测试竞赛目标创建成功，数据持久化正常")
            
            # 显示所有数据
            classes = Class.query.all()
            goals = CompetitionGoal.query.all()
            
            print(f"\n=== 数据库中的实际数据 ===")
            print(f"班级数量: {len(classes)}")
            for cls in classes:
                print(f"  - {cls.name} (ID: {cls.id})")
            
            print(f"竞赛目标数量: {len(goals)}")
            for goal in goals:
                print(f"  - {goal.title} (ID: {goal.id})")
                
    except Exception as e:
        print(f"❌ 数据持久化测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_data_persistence()
