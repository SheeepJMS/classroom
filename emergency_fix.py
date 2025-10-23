#!/usr/bin/env python3
"""
紧急修复脚本 - 解决分数累计和轮次问题
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

def fix_scoring_issues(app, db):
    """修复分数累计问题"""
    print("🔧 开始修复分数累计问题...")
    
    with app.app_context():
        try:
            # 1. 重新计算所有学生的分数
            print("1. 重新计算学生分数...")
            
            # 获取所有活跃课程
            courses_result = db.session.execute(text("""
                SELECT id, name FROM courses WHERE is_active = true
            """))
            courses = courses_result.fetchall()
            
            for course in courses:
                course_id = course[0]
                course_name = course[1]
                print(f"   处理课程: {course_name} (ID: {course_id})")
                
                # 获取该课程的所有学生
                students_result = db.session.execute(text("""
                    SELECT DISTINCT s.id, s.name
                    FROM students s
                    JOIN student_submissions ss ON s.id = ss.student_id
                    JOIN course_rounds cr ON ss.round_id = cr.id
                    WHERE cr.course_id = :course_id
                """), {'course_id': course_id})
                students = students_result.fetchall()
                
                for student in students:
                    student_id = student[0]
                    student_name = student[1]
                    
                    # 重新计算正确答题数
                    correct_count_result = db.session.execute(text("""
                        SELECT COUNT(*) as correct_count
                        FROM student_submissions ss
                        JOIN course_rounds cr ON ss.round_id = cr.id
                        WHERE ss.student_id = :student_id 
                        AND cr.course_id = :course_id
                        AND ss.is_correct = true
                    """), {'student_id': student_id, 'course_id': course_id})
                    
                    correct_count = correct_count_result.fetchone()[0]
                    print(f"     学生 {student_name}: 正确答题 {correct_count} 次")
            
            # 2. 修复轮次编号问题
            print("2. 修复轮次编号问题...")
            
            for course in courses:
                course_id = course[0]
                course_name = course[1]
                
                # 获取该课程的所有轮次
                rounds_result = db.session.execute(text("""
                    SELECT id, round_number FROM course_rounds 
                    WHERE course_id = :course_id
                    ORDER BY created_date
                """), {'course_id': course_id})
                rounds = rounds_result.fetchall()
                
                if len(rounds) > 0:
                    # 重新编号轮次
                    for i, (round_id, old_round) in enumerate(rounds):
                        new_round = i + 1
                        if old_round != new_round:
                            db.session.execute(text("""
                                UPDATE course_rounds 
                                SET round_number = :new_round
                                WHERE id = :round_id
                            """), {'new_round': new_round, 'round_id': round_id})
                            print(f"     轮次 {old_round} -> {new_round}")
            
            # 3. 修复答案提交状态
            print("3. 修复答案提交状态...")
            
            for course in courses:
                course_id = course[0]
                
                # 获取该课程的所有提交记录
                submissions_result = db.session.execute(text("""
                    SELECT ss.id, ss.answer, cr.correct_answer, ss.is_correct
                    FROM student_submissions ss
                    JOIN course_rounds cr ON ss.round_id = cr.id
                    WHERE cr.course_id = :course_id
                """), {'course_id': course_id})
                submissions = submissions_result.fetchall()
                
                for submission in submissions:
                    sub_id, answer, correct_answer, is_correct = submission
                    
                    # 重新判断答案对错
                    if answer and correct_answer:
                        new_is_correct = answer.strip().lower() == correct_answer.strip().lower()
                        if new_is_correct != is_correct:
                            db.session.execute(text("""
                                UPDATE student_submissions 
                                SET is_correct = :is_correct
                                WHERE id = :sub_id
                            """), {'is_correct': new_is_correct, 'sub_id': sub_id})
                            print(f"     提交 {sub_id}: {answer} vs {correct_answer} = {new_is_correct}")
            
            # 提交所有更改
            db.session.commit()
            print("✅ 修复完成！")
            
        except Exception as e:
            print(f"❌ 修复失败: {str(e)}")
            db.session.rollback()

def main():
    """主函数"""
    print("🚀 启动紧急修复脚本...")
    
    app, db = create_app()
    if not app:
        return
    
    fix_scoring_issues(app, db)

if __name__ == "__main__":
    main()
