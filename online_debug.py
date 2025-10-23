#!/usr/bin/env python3
"""
线上Render数据库调试工具
直接在Render平台上运行，用于调试线上数据库问题
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import traceback

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = SQLAlchemy()

def setup_app():
    """设置Flask应用"""
    # 获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    logger.info(f"数据库URL: {database_url[:50]}...")
    
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量")
        return False
    
    # 转换数据库URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        logger.info("已转换postgres://为postgresql+pg8000://")
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        logger.info("已转换postgresql://为postgresql+pg8000://")
    
    # 配置Flask应用
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-secret-key')
    
    # 初始化数据库
    db.init_app(app)
    
    logger.info("Flask应用和数据库初始化完成")
    return True

@app.route('/')
def index():
    """调试主页"""
    return render_template('online_debug.html')

@app.route('/debug/check_scoring')
def check_scoring():
    """检查分数累计问题"""
    try:
        with app.app_context():
            # 检查所有课程
            courses_result = db.session.execute(text("""
                SELECT id, name, class_id, is_active, created_date 
                FROM courses 
                ORDER BY created_date DESC
            """))
            courses = courses_result.fetchall()
            
            debug_info = {
                'courses': [],
                'scoring_issues': [],
                'round_issues': []
            }
            
            for course in courses:
                course_id = course[0]
                course_name = course[1]
                class_id = course[2]
                is_active = course[3]
                
                # 检查该课程的轮次
                rounds_result = db.session.execute(text("""
                    SELECT id, round_number, question_text, correct_answer, question_score, created_date
                    FROM course_rounds 
                    WHERE course_id = :course_id
                    ORDER BY round_number
                """), {'course_id': course_id})
                rounds = rounds_result.fetchall()
                
                # 检查该课程的学生提交
                submissions_result = db.session.execute(text("""
                    SELECT s.id, s.name, cr.round_number, ss.answer, ss.is_correct, ss.answer_time, ss.created_date
                    FROM students s
                    JOIN student_submissions ss ON s.id = ss.student_id
                    JOIN course_rounds cr ON ss.round_id = cr.id
                    WHERE cr.course_id = :course_id
                    ORDER BY s.name, cr.round_number
                """), {'course_id': course_id})
                submissions = submissions_result.fetchall()
                
                # 分析分数累计问题
                student_scores = {}
                for sub in submissions:
                    student_name = sub[1]
                    round_num = sub[2]
                    is_correct = sub[4]
                    
                    if student_name not in student_scores:
                        student_scores[student_name] = {
                            'total_score': 0,
                            'total_rounds': 0,
                            'correct_rounds': 0,
                            'rounds': []
                        }
                    
                    student_scores[student_name]['total_rounds'] += 1
                    if is_correct:
                        student_scores[student_name]['total_score'] += 1
                        student_scores[student_name]['correct_rounds'] += 1
                    
                    student_scores[student_name]['rounds'].append({
                        'round': round_num,
                        'correct': is_correct
                    })
                
                course_info = {
                    'id': course_id,
                    'name': course_name,
                    'class_id': class_id,
                    'is_active': is_active,
                    'rounds': [{'id': r[0], 'round_number': r[1], 'question_text': r[2], 'correct_answer': r[3], 'question_score': r[4]} for r in rounds],
                    'students': student_scores
                }
                
                debug_info['courses'].append(course_info)
                
                # 检查分数累计问题
                for student_name, data in student_scores.items():
                    if len(data['rounds']) > 1:
                        # 检查是否有分数累计问题
                        expected_score = data['correct_rounds']
                        if expected_score > 1 and data['total_score'] != expected_score:
                            debug_info['scoring_issues'].append({
                                'course_id': course_id,
                                'student_name': student_name,
                                'expected_score': expected_score,
                                'actual_score': data['total_score'],
                                'rounds': data['rounds']
                            })
                
                # 检查轮次问题
                if len(rounds) > 0:
                    max_round = max([r[1] for r in rounds])
                    if max_round > 1:
                        debug_info['round_issues'].append({
                            'course_id': course_id,
                            'max_round': max_round,
                            'rounds': [r[1] for r in rounds]
                        })
            
            return jsonify({
                'success': True,
                'debug_info': debug_info
            })
            
    except Exception as e:
        logger.error(f"检查分数问题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'检查失败: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/debug/fix_scoring')
def fix_scoring():
    """修复分数累计问题"""
    try:
        with app.app_context():
            fix_results = []
            
            # 获取所有活跃课程
            courses_result = db.session.execute(text("""
                SELECT id, name FROM courses WHERE is_active = true
            """))
            courses = courses_result.fetchall()
            
            for course in courses:
                course_id = course[0]
                course_name = course[1]
                
                # 重新计算每个学生的分数
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
                    
                    # 计算正确的分数
                    score_result = db.session.execute(text("""
                        SELECT COUNT(*) as correct_count
                        FROM student_submissions ss
                        JOIN course_rounds cr ON ss.round_id = cr.id
                        WHERE ss.student_id = :student_id 
                        AND cr.course_id = :course_id
                        AND ss.is_correct = true
                    """), {'student_id': student_id, 'course_id': course_id})
                    
                    correct_count = score_result.fetchone()[0]
                    
                    # 这里可以添加更新学生分数的逻辑
                    # 由于没有直接的分数字段，我们记录修复结果
                    fix_results.append({
                        'course_id': course_id,
                        'course_name': course_name,
                        'student_name': student_name,
                        'correct_count': correct_count
                    })
            
            return jsonify({
                'success': True,
                'fix_results': fix_results
            })
            
    except Exception as e:
        logger.error(f"修复分数问题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'修复失败: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/debug/check_rounds')
def check_rounds():
    """检查轮次问题"""
    try:
        with app.app_context():
            # 检查所有课程的轮次
            rounds_result = db.session.execute(text("""
                SELECT c.id, c.name, c.is_active, 
                       COUNT(cr.id) as round_count,
                       MAX(cr.round_number) as max_round,
                       MIN(cr.round_number) as min_round
                FROM courses c
                LEFT JOIN course_rounds cr ON c.id = cr.course_id
                GROUP BY c.id, c.name, c.is_active
                ORDER BY c.created_date DESC
            """))
            rounds = rounds_result.fetchall()
            
            round_info = []
            for r in rounds:
                course_id, course_name, is_active, round_count, max_round, min_round = r
                
                # 获取详细的轮次信息
                detail_result = db.session.execute(text("""
                    SELECT round_number, question_text, correct_answer, created_date
                    FROM course_rounds 
                    WHERE course_id = :course_id
                    ORDER BY round_number
                """), {'course_id': course_id})
                details = detail_result.fetchall()
                
                round_info.append({
                    'course_id': course_id,
                    'course_name': course_name,
                    'is_active': is_active,
                    'round_count': round_count,
                    'max_round': max_round,
                    'min_round': min_round,
                    'details': [{'round_number': d[0], 'question_text': d[1], 'correct_answer': d[2], 'created_date': str(d[3])} for d in details]
                })
            
            return jsonify({
                'success': True,
                'round_info': round_info
            })
            
    except Exception as e:
        logger.error(f"检查轮次问题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'检查失败: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/debug/fix_rounds')
def fix_rounds():
    """修复轮次问题"""
    try:
        with app.app_context():
            fix_results = []
            
            # 获取所有活跃课程
            courses_result = db.session.execute(text("""
                SELECT id, name FROM courses WHERE is_active = true
            """))
            courses = courses_result.fetchall()
            
            for course in courses:
                course_id = course[0]
                course_name = course[1]
                
                # 检查轮次编号是否连续
                rounds_result = db.session.execute(text("""
                    SELECT round_number FROM course_rounds 
                    WHERE course_id = :course_id
                    ORDER BY round_number
                """), {'course_id': course_id})
                rounds = [r[0] for r in rounds_result.fetchall()]
                
                if len(rounds) > 0:
                    expected_rounds = list(range(1, len(rounds) + 1))
                    if rounds != expected_rounds:
                        # 重新编号轮次
                        for i, old_round in enumerate(rounds):
                            new_round = i + 1
                            if old_round != new_round:
                                db.session.execute(text("""
                                    UPDATE course_rounds 
                                    SET round_number = :new_round
                                    WHERE course_id = :course_id AND round_number = :old_round
                                """), {'new_round': new_round, 'course_id': course_id, 'old_round': old_round})
                        
                        db.session.commit()
                        
                        fix_results.append({
                            'course_id': course_id,
                            'course_name': course_name,
                            'old_rounds': rounds,
                            'new_rounds': expected_rounds,
                            'fixed': True
                        })
                    else:
                        fix_results.append({
                            'course_id': course_id,
                            'course_name': course_name,
                            'rounds': rounds,
                            'fixed': False
                        })
            
            return jsonify({
                'success': True,
                'fix_results': fix_results
            })
            
    except Exception as e:
        logger.error(f"修复轮次问题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'修复失败: {str(e)}',
            'error_type': type(e).__name__
        })

if __name__ == "__main__":
    if setup_app():
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"启动线上调试服务器: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.error("应用初始化失败")
        sys.exit(1)
