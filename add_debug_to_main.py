#!/usr/bin/env python3
"""
在主应用中添加调试功能
不需要创建新服务器，直接在主应用中调试
"""

import os
import sys
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import traceback

def add_debug_routes(app, db):
    """在主应用中添加调试路由"""
    
    @app.route('/debug')
    def debug_home():
        """调试主页"""
        return render_template('debug_home.html')
    
    @app.route('/debug/check_scoring')
    def check_scoring():
        """检查分数累计问题"""
        try:
            with app.app_context():
                # 获取所有活跃课程
                courses_result = db.session.execute(text("""
                    SELECT id, name, class_id, is_active, created_date 
                    FROM courses 
                    WHERE is_active = true
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
                        'rounds': [{'id': r[0], 'round_number': r[1], 'question_text': r[2], 'correct_answer': r[3], 'question_score': r[4]} for r in rounds],
                        'students': student_scores
                    }
                    
                    debug_info['courses'].append(course_info)
                    
                    # 检查分数累计问题
                    for student_name, data in student_scores.items():
                        if len(data['rounds']) > 1:
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
            return jsonify({
                'success': False,
                'message': f'修复失败: {str(e)}',
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
            return jsonify({
                'success': False,
                'message': f'修复失败: {str(e)}',
                'error_type': type(e).__name__
            })

if __name__ == "__main__":
    print("调试路由已添加到主应用中")
    print("访问 /debug 即可使用调试功能")
