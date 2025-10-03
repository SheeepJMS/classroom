#!/usr/bin/env python3
"""
数据同步脚本：将本地JSON数据同步到PostgreSQL数据库
这个脚本应该在部署环境中运行，将JSON数据迁移到数据库
"""

import json
import os
import sys
from datetime import datetime
from app import app
from models import db, Class, Student, CompetitionGoal, Course

def sync_json_to_database():
    """将JSON数据同步到数据库"""
    print("=== 开始数据同步 ===")
    
    with app.app_context():
        # 检查JSON数据文件
        data_file = 'app_data.json'
        if not os.path.exists(data_file):
            print(f"JSON数据文件 {data_file} 不存在")
            return
        
        # 读取JSON数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"读取JSON数据完成")
        
        # 清空现有数据库数据（仅在开发环境）
        if os.environ.get('FLASK_ENV') == 'development':
            print("开发环境：清空现有数据...")
            StudentSubmission.query.delete()
            CourseRound.query.delete()
            Course.query.delete()
            Student.query.delete()
            Class.query.delete()
            CompetitionGoal.query.delete()
            db.session.commit()
        
        # 同步竞赛目标
        print("同步竞赛目标...")
        for goal_id, goal_data in data.get('competition_goals', {}).items():
            existing_goal = CompetitionGoal.query.get(goal_id)
            if not existing_goal:
                goal = CompetitionGoal(
                    id=goal_id,
                    title=goal_data.get('name', ''),
                    description=goal_data.get('description', ''),
                    target_score=goal_data.get('target_score', 100),
                    created_date=datetime.utcnow()
                )
                db.session.add(goal)
                print(f"  添加竞赛目标: {goal_data.get('name', '')}")
        
        # 同步班级
        print("同步班级...")
        for class_id, class_data in data.get('classes', {}).items():
            existing_class = Class.query.get(class_id)
            if not existing_class:
                class_obj = Class(
                    id=class_id,
                    name=class_data.get('name', ''),
                    description=class_data.get('description', ''),
                    is_active=class_data.get('is_active', True),
                    created_date=datetime.utcnow(),
                    competition_goal_id=class_data.get('competition_goal_id')
                )
                db.session.add(class_obj)
                print(f"  添加班级: {class_data.get('name', '')}")
        
        # 同步学生
        print("同步学生...")
        for student_id, student_data in data.get('students', {}).items():
            existing_student = Student.query.get(student_id)
            if not existing_student:
                student = Student(
                    id=student_id,
                    name=student_data.get('name', ''),
                    class_id=student_data.get('class_id', ''),
                    created_date=datetime.utcnow()
                )
                db.session.add(student)
                print(f"  添加学生: {student_data.get('name', '')}")
        
        # 同步课程
        print("同步课程...")
        for course_id, course_data in data.get('courses', {}).items():
            existing_course = Course.query.get(course_id)
            if not existing_course:
                course = Course(
                    id=course_id,
                    name=course_data.get('name', ''),
                    class_id=course_data.get('class_id', ''),
                    is_active=course_data.get('is_active', True),
                    created_date=datetime.utcnow()
                )
                db.session.add(course)
                print(f"  添加课程: {course_data.get('name', '')}")
        
        # 提交所有更改
        db.session.commit()
        print("数据同步完成！")
        
        # 显示同步统计
        print(f"同步统计:")
        print(f"- 竞赛目标: {CompetitionGoal.query.count()}")
        print(f"- 班级: {Class.query.count()}")
        print(f"- 学生: {Student.query.count()}")
        print(f"- 课程: {Course.query.count()}")

if __name__ == '__main__':
    sync_json_to_database()
