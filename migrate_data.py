#!/usr/bin/env python3
"""
数据迁移脚本：将JSON文件数据迁移到PostgreSQL数据库
"""

import json
import os
import uuid
from datetime import datetime
from app import app
from models import db, Class, Student, CompetitionGoal, Course, CourseRound, StudentSubmission

def migrate_data():
    """迁移数据从JSON文件到PostgreSQL"""
    
    # 检查是否存在JSON数据文件
    data_file = 'app_data.json'
    if not os.path.exists(data_file):
        print(f"数据文件 {data_file} 不存在，跳过迁移")
        return
    
    with app.app_context():
        # 读取JSON数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("开始迁移数据...")
        
        # 迁移竞赛目标
        print("迁移竞赛目标...")
        for goal_id, goal_data in data.get('competition_goals', {}).items():
            if not CompetitionGoal.query.get(goal_id):
                goal = CompetitionGoal(
                    id=goal_id,
                    title=goal_data.get('title', ''),
                    description=goal_data.get('description', ''),
                    target_score=goal_data.get('target_score', 100),
                    created_date=datetime.utcnow()
                )
                db.session.add(goal)
        
        # 迁移班级
        print("迁移班级...")
        for class_id, class_data in data.get('classes', {}).items():
            if not Class.query.get(class_id):
                class_obj = Class(
                    id=class_id,
                    name=class_data.get('name', ''),
                    description=class_data.get('description', ''),
                    is_active=class_data.get('is_active', True),
                    created_date=datetime.utcnow(),
                    competition_goal_id=class_data.get('competition_goal_id')
                )
                db.session.add(class_obj)
        
        # 迁移学生
        print("迁移学生...")
        for student_id, student_data in data.get('students', {}).items():
            if not Student.query.get(student_id):
                student = Student(
                    id=student_id,
                    name=student_data.get('name', ''),
                    class_id=student_data.get('class_id', ''),
                    created_date=datetime.utcnow()
                )
                db.session.add(student)
        
        # 迁移课程
        print("迁移课程...")
        for course_id, course_data in data.get('courses', {}).items():
            if not Course.query.get(course_id):
                course = Course(
                    id=course_id,
                    name=course_data.get('name', ''),
                    class_id=course_data.get('class_id', ''),
                    is_active=course_data.get('is_active', True),
                    created_date=datetime.utcnow()
                )
                db.session.add(course)
        
        # 迁移课程轮次和学生提交
        print("迁移课程轮次和学生提交...")
        for course_id, course_data in data.get('courses', {}).items():
            round_results = course_data.get('round_results', {})
            
            for round_num_str, round_data in round_results.items():
                try:
                    round_number = int(round_num_str)
                except ValueError:
                    continue
                
                # 创建课程轮次
                round_id = f"{course_id}_round_{round_number}"
                if not CourseRound.query.get(round_id):
                    round_obj = CourseRound(
                        id=round_id,
                        course_id=course_id,
                        round_number=round_number,
                        question_text=round_data.get('question', ''),
                        correct_answer=round_data.get('correct_answer', ''),
                        question_score=round_data.get('question_score', 1),
                        created_date=datetime.utcnow()
                    )
                    db.session.add(round_obj)
                
                # 迁移学生提交
                student_submissions = round_data.get('student_submissions', {})
                for student_id, submission_data in student_submissions.items():
                    submission_id = f"{student_id}_{round_id}"
                    if not StudentSubmission.query.get(submission_id):
                        submission = StudentSubmission(
                            id=submission_id,
                            student_id=student_id,
                            round_id=round_id,
                            answer=submission_data.get('answer', ''),
                            is_correct=submission_data.get('is_correct', False),
                            answer_time=submission_data.get('answer_time', 0.0),
                            submitted_at=datetime.utcnow()
                        )
                        db.session.add(submission)
        
        # 提交所有更改
        db.session.commit()
        print("数据迁移完成！")
        
        # 显示迁移统计
        print(f"迁移统计:")
        print(f"- 竞赛目标: {CompetitionGoal.query.count()}")
        print(f"- 班级: {Class.query.count()}")
        print(f"- 学生: {Student.query.count()}")
        print(f"- 课程: {Course.query.count()}")
        print(f"- 课程轮次: {CourseRound.query.count()}")
        print(f"- 学生提交: {StudentSubmission.query.count()}")

if __name__ == '__main__':
    migrate_data()
