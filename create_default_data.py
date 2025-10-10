#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认数据脚本
在数据库为空时创建默认的竞赛目标
"""

from app import app
from models import db, CompetitionGoal, Class

def create_default_data():
    """创建默认数据"""
    with app.app_context():
        # 检查是否已有数据
        existing_goals = CompetitionGoal.query.count()
        existing_classes = Class.query.count()
        
        if existing_goals > 0 or existing_classes > 0:
            print(f"数据库已有数据 - 竞赛目标: {existing_goals}, 班级: {existing_classes}")
            return
        
        print("数据库为空，创建默认数据...")
        
        # 创建默认竞赛目标
        default_goals = [
            {
                'id': 'amc8-2025',
                'title': 'AMC 8竞赛',
                'description': '美国数学竞赛 AMC 8准备',
                'target_score': 25
            },
            {
                'id': 'amc10-2025', 
                'title': 'AMC 10竞赛',
                'description': '美国数学竞赛 AMC 10准备',
                'target_score': 150
            }
        ]
        
        for goal_data in default_goals:
            goal = CompetitionGoal(**goal_data)
            db.session.add(goal)
        
        db.session.commit()
        print("默认竞赛目标创建完成")

if __name__ == '__main__':
    create_default_data()
