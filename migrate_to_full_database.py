#!/usr/bin/env python3
"""
完全迁移到数据库模式
移除所有JSON文件依赖
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append('.')

# 设置环境变量
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
os.environ['USE_DATABASE'] = 'true'

from app import app, global_data
from models import db, Course, Student, Class, CompetitionGoal

def migrate_to_full_database():
    """完全迁移到数据库模式"""
    print("=== 开始完全数据库化迁移 ===")
    
    with app.app_context():
        try:
            # 1. 创建新的数据库表来存储课堂状态
            print("1. 创建课堂状态表...")
            
            # 创建课堂状态表
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS classroom_states (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR(36) NOT NULL,
                    current_round INTEGER DEFAULT 1,
                    round_active BOOLEAN DEFAULT FALSE,
                    correct_answer VARCHAR(10),
                    start_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建学生状态表
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS student_states (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR(36) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    score INTEGER DEFAULT 0,
                    total_rounds INTEGER DEFAULT 0,
                    correct_rounds INTEGER DEFAULT 0,
                    expression VARCHAR(20) DEFAULT 'neutral',
                    animation VARCHAR(20) DEFAULT 'none',
                    avatar_color VARCHAR(7) DEFAULT '#4ecdc4',
                    last_answer_time INTEGER DEFAULT 0,
                    last_answer VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(course_id, student_name)
                )
            """)
            
            # 创建轮次结果表
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS round_results (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR(36) NOT NULL,
                    round_number INTEGER NOT NULL,
                    correct_answer VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建学生提交记录表
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS student_submissions (
                    id SERIAL PRIMARY KEY,
                    course_id VARCHAR(36) NOT NULL,
                    round_number INTEGER NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    answer VARCHAR(10),
                    is_correct BOOLEAN DEFAULT FALSE,
                    answer_time INTEGER DEFAULT 0,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.session.commit()
            print("   ✅ 数据库表创建成功")
            
            # 2. 迁移现有数据
            print("2. 迁移现有数据...")
            
            # 从JSON文件迁移数据到数据库
            if 'courses' in global_data:
                for course_id, course_data in global_data['courses'].items():
                    print(f"   迁移课程 {course_id}...")
                    
                    # 创建课堂状态记录
                    db.session.execute("""
                        INSERT INTO classroom_states (course_id, current_round, round_active, correct_answer, start_time)
                        VALUES (:course_id, :current_round, :round_active, :correct_answer, :start_time)
                        ON CONFLICT (course_id) DO UPDATE SET
                            current_round = EXCLUDED.current_round,
                            round_active = EXCLUDED.round_active,
                            correct_answer = EXCLUDED.correct_answer,
                            start_time = EXCLUDED.start_time,
                            updated_at = CURRENT_TIMESTAMP
                    """, {
                        'course_id': course_id,
                        'current_round': course_data.get('current_round', 1),
                        'round_active': course_data.get('round_active', False),
                        'correct_answer': course_data.get('correct_answer', ''),
                        'start_time': course_data.get('start_time')
                    })
                    
                    # 迁移学生状态
                    if 'students' in course_data:
                        for student_name, student_data in course_data['students'].items():
                            db.session.execute("""
                                INSERT INTO student_states (
                                    course_id, student_name, score, total_rounds, correct_rounds,
                                    expression, animation, avatar_color, last_answer_time, last_answer
                                ) VALUES (
                                    :course_id, :student_name, :score, :total_rounds, :correct_rounds,
                                    :expression, :animation, :avatar_color, :last_answer_time, :last_answer
                                )
                                ON CONFLICT (course_id, student_name) DO UPDATE SET
                                    score = EXCLUDED.score,
                                    total_rounds = EXCLUDED.total_rounds,
                                    correct_rounds = EXCLUDED.correct_rounds,
                                    expression = EXCLUDED.expression,
                                    animation = EXCLUDED.animation,
                                    avatar_color = EXCLUDED.avatar_color,
                                    last_answer_time = EXCLUDED.last_answer_time,
                                    last_answer = EXCLUDED.last_answer,
                                    updated_at = CURRENT_TIMESTAMP
                            """, {
                                'course_id': course_id,
                                'student_name': student_name,
                                'score': student_data.get('score', 0),
                                'total_rounds': student_data.get('total_rounds', 0),
                                'correct_rounds': student_data.get('correct_rounds', 0),
                                'expression': student_data.get('expression', 'neutral'),
                                'animation': student_data.get('animation', 'none'),
                                'avatar_color': student_data.get('avatar_color', '#4ecdc4'),
                                'last_answer_time': student_data.get('last_answer_time', 0),
                                'last_answer': student_data.get('last_answer', '')
                            })
                    
                    # 迁移轮次结果
                    if 'round_results' in course_data:
                        for i, round_result in enumerate(course_data['round_results']):
                            db.session.execute("""
                                INSERT INTO round_results (course_id, round_number, correct_answer)
                                VALUES (:course_id, :round_number, :correct_answer)
                                ON CONFLICT (course_id, round_number) DO UPDATE SET
                                    correct_answer = EXCLUDED.correct_answer
                            """, {
                                'course_id': course_id,
                                'round_number': i + 1,
                                'correct_answer': round_result.get('correct_answer', '')
                            })
                            
                            # 迁移学生提交记录
                            if 'results' in round_result:
                                for student_name, result in round_result['results'].items():
                                    db.session.execute("""
                                        INSERT INTO student_submissions (
                                            course_id, round_number, student_name, answer, is_correct, answer_time
                                        ) VALUES (
                                            :course_id, :round_number, :student_name, :answer, :is_correct, :answer_time
                                        )
                                    """, {
                                        'course_id': course_id,
                                        'round_number': i + 1,
                                        'student_name': student_name,
                                        'answer': result.get('answer', ''),
                                        'is_correct': result.get('correct', False),
                                        'answer_time': result.get('answer_time', 0)
                                    })
            
            db.session.commit()
            print("   ✅ 数据迁移完成")
            
            # 3. 验证迁移结果
            print("3. 验证迁移结果...")
            
            # 统计迁移的数据
            classroom_count = db.session.execute("SELECT COUNT(*) FROM classroom_states").scalar()
            student_count = db.session.execute("SELECT COUNT(*) FROM student_states").scalar()
            round_count = db.session.execute("SELECT COUNT(*) FROM round_results").scalar()
            submission_count = db.session.execute("SELECT COUNT(*) FROM student_submissions").scalar()
            
            print(f"   课堂状态记录: {classroom_count}")
            print(f"   学生状态记录: {student_count}")
            print(f"   轮次结果记录: {round_count}")
            print(f"   提交记录: {submission_count}")
            
            print("✅ 完全数据库化迁移完成！")
            print("\n下一步：")
            print("1. 修改app.py，移除所有JSON文件依赖")
            print("2. 所有数据操作直接使用数据库")
            print("3. 简化代码逻辑，提高稳定性")
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_to_full_database()
