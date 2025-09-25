from flask import Blueprint, render_template, request, jsonify, send_file
import json
import time
import os
from datetime import datetime
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# 创建蓝图
classroom_bp = Blueprint("classroom", __name__, template_folder="templates")

# 存储课堂数据
classroom_data = {
    'students': {},
    'submissions': [],
    'is_active': False,
    'start_time': None,
    'current_round': 1,  # 当前答题轮次，从1开始
    'round_active': False,  # 当前轮次是否活跃
    'current_answers': {},  # 当前轮次的学生答案
    'answer_times': {},  # 学生答题时间记录
    'correct_answer': '',  # 当前正确答案
    'round_results': []  # 每轮答题结果
}

@classroom_bp.route('/')
def classroom_home():
    """课堂主页"""
    return render_template('classroom.html', 
                         classroom_data=classroom_data)

@classroom_bp.route('/start_class', methods=['POST'])
def start_class():
    """开始课堂"""
    classroom_data['is_active'] = True
    classroom_data['round_active'] = True
    classroom_data['start_time'] = time.time()
    return jsonify({'success': True})

@classroom_bp.route('/add_student', methods=['POST'])
def add_student():
    """添加学生"""
    data = request.get_json()
    student_name = data.get('name', '').strip()
    
    if not student_name:
        return jsonify({'error': '学生姓名不能为空'}), 400
    
    if student_name in classroom_data['students']:
        return jsonify({'error': '学生已存在'}), 400
    
    # 添加新学生
    classroom_data['students'][student_name] = {
        'name': student_name,
        'score': 0,
        'total_rounds': 0,
        'correct_rounds': 0,
        'last_answer_time': 0,
        'expression': 'neutral',
        'animation': 'none',
        'avatar_color': random.choice(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd']),
        'answers': []
    }
    
    return jsonify({'success': True, 'student': classroom_data['students'][student_name]})

@classroom_bp.route('/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """学生提交答案"""
    data = request.get_json()
    student_name = data.get('student_name', '').strip()
    answer = data.get('answer', '').strip()
    
    if not student_name or not answer:
        return jsonify({'error': '学生姓名和答案不能为空'}), 400
    
    if student_name not in classroom_data['students']:
        return jsonify({'error': '学生不存在'}), 400
    
    if not classroom_data['round_active']:
        return jsonify({'error': '当前没有活跃的答题轮次'}), 400
    
    # 记录答题时间
    current_time = time.time()
    if classroom_data['start_time']:
        answer_time = current_time - classroom_data['start_time']
    else:
        answer_time = 0
    
    classroom_data['answer_times'][student_name] = answer_time
    classroom_data['current_answers'][student_name] = answer
    
    return jsonify({'success': True, 'answer_time': answer_time})

@classroom_bp.route('/judge_answers', methods=['POST'])
def judge_answers():
    """评判答案"""
    data = request.get_json()
    correct_answer = data.get('correct_answer', '').strip()
    
    if not correct_answer:
        return jsonify({'error': '正确答案不能为空'}), 400
    
    classroom_data['correct_answer'] = correct_answer
    
    # 评判每个学生的答案
    round_result = {
        'round': classroom_data['current_round'],
        'correct_answer': correct_answer,
        'results': {}
    }
    
    for student_name, answer in classroom_data['current_answers'].items():
        is_correct = answer.lower() == correct_answer.lower()
        
        # 更新学生数据
        student = classroom_data['students'][student_name]
        student['total_rounds'] += 1
        if is_correct:
            student['correct_rounds'] += 1
            student['score'] += 1
            student['expression'] = 'smile'
        else:
            student['expression'] = 'angry'
        
        student['last_answer_time'] = classroom_data['answer_times'].get(student_name, 0)
        
        # 记录提交
        submission = {
            'student_name': student_name,
            'round': classroom_data['current_round'],
            'answer': answer,
            'is_correct': is_correct,
            'earned_score': 1 if is_correct else 0,
            'answer_time': student['last_answer_time'],
            'timestamp': datetime.now().isoformat()
        }
        
        student['answers'].append(submission)
        classroom_data['submissions'].append(submission)
        
        # 记录轮次结果
        round_result['results'][student_name] = {
            'answer': answer,
            'is_correct': is_correct,
            'answer_time': student['last_answer_time']
        }
    
    classroom_data['round_results'].append(round_result)
    
    # 重置当前轮次状态
    classroom_data['round_active'] = False
    classroom_data['current_answers'] = {}
    classroom_data['answer_times'] = {}
    classroom_data['start_time'] = None
    
    return jsonify({'success': True, 'round_result': round_result})

@classroom_bp.route('/next_round', methods=['POST'])
def next_round():
    """进入下一轮"""
    classroom_data['current_round'] += 1
    classroom_data['round_active'] = True
    classroom_data['start_time'] = time.time()
    
    # 重置所有学生表情
    for student in classroom_data['students'].values():
        student['expression'] = 'neutral'
        student['animation'] = 'none'
    
    return jsonify({'success': True, 'current_round': classroom_data['current_round']})

@classroom_bp.route('/get_classroom_data')
def get_classroom_data():
    """获取课堂数据"""
    return jsonify(classroom_data)

@classroom_bp.route('/reset_classroom', methods=['POST'])
def reset_classroom():
    """重置课堂"""
    global classroom_data
    classroom_data = {
        'students': {},
        'submissions': [],
        'is_active': False,
        'start_time': None,
        'current_round': 1,
        'round_active': False,
        'current_answers': {},
        'answer_times': {},
        'correct_answer': '',
        'round_results': []
    }
    return jsonify({'success': True})

@classroom_bp.route('/create_demo_data', methods=['POST'])
def create_demo_data():
    """创建演示数据"""
    demo_students = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']
    
    # 清空现有数据
    classroom_data['students'] = {}
    classroom_data['submissions'] = []
    classroom_data['round_results'] = []
    
    # 创建演示学生数据
    for student_name in demo_students:
        student_submissions = []
        correct_count = 0
        total_score = 0
        
        for round_num in range(1, 6):
            is_correct = random.choice([True, False])
            answer_time = random.uniform(5, 45)
            earned_score = 1 if is_correct else 0
            
            if is_correct:
                correct_count += 1
            total_score += earned_score
            
            submission = {
                'student_name': student_name,
                'round': round_num,
                'answer': f'答案{round_num}',
                'is_correct': is_correct,
                'earned_score': earned_score,
                'answer_time': answer_time,
                'timestamp': datetime.now().isoformat()
            }
            student_submissions.append(submission)
            classroom_data['submissions'].append(submission)
        
        classroom_data['students'][student_name] = {
            'name': student_name,
            'score': total_score,
            'total_rounds': 5,
            'correct_rounds': correct_count,
            'last_answer_time': student_submissions[-1]['answer_time'] if student_submissions else 0,
            'expression': 'neutral',
            'animation': 'none',
            'avatar_color': random.choice(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd']),
            'answers': student_submissions
        }
    
    # 创建轮次结果
    for round_num in range(1, 6):
        round_result = {
            'round': round_num,
            'correct_answer': f'正确答案{round_num}',
            'results': {}
        }
        
        for student_name in demo_students:
            student_submission = next((s for s in classroom_data['submissions'] 
                                     if s['student_name'] == student_name and s['round'] == round_num), None)
            if student_submission:
                round_result['results'][student_name] = {
                    'answer': student_submission['answer'],
                    'is_correct': student_submission['is_correct'],
                    'answer_time': student_submission['answer_time']
                }
        
        classroom_data['round_results'].append(round_result)
    
    classroom_data['current_round'] = 6
    classroom_data['is_active'] = True
    
    return jsonify({'success': True, 'students': list(classroom_data['students'].keys())})

@classroom_bp.route('/generate_student_report/<student_name>')
def generate_student_report(student_name):
    """生成学生个人报告"""
    if student_name not in classroom_data['students']:
        return jsonify({'error': 'Student not found'}), 404
    
    student = classroom_data['students'][student_name]
    
    # 计算统计数据
    total_rounds = student.get('total_rounds', 0)
    correct_rounds = student.get('correct_rounds', 0)
    accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
    
    # 获取学生提交记录
    student_submissions = [s for s in classroom_data['submissions'] 
                          if s['student_name'] == student_name]
    
    # 计算参与率
    total_rounds_available = max(len(classroom_data.get('round_results', [])), student.get('total_rounds', 0))
    student_submissions_count = len(student_submissions)
    participation_rate = (student_submissions_count / total_rounds_available * 100) if total_rounds_available > 0 else 0
    
    # 计算平均反应时间
    if student_submissions:
        avg_response_time = sum(s['answer_time'] for s in student_submissions) / len(student_submissions)
    else:
        avg_response_time = 0
    
    # 计算未参与轮次
    missed_rounds = total_rounds_available - student_submissions_count
    
    # 计算班级平均值
    all_students = list(classroom_data['students'].values())
    if all_students:
        class_avg_accuracy = sum(s.get('correct_rounds', 0) / max(s.get('total_rounds', 1), 1) * 100 for s in all_students) / len(all_students)
        class_avg_participation = sum(len([sub for sub in classroom_data['submissions'] if sub['student_name'] == s['name']]) / max(len(classroom_data.get('round_results', [])), s.get('total_rounds', 1)) * 100 for s in all_students) / len(all_students)
        class_avg_response_time = sum(sum(sub['answer_time'] for sub in classroom_data['submissions'] if sub['student_name'] == s['name']) / max(len([sub for sub in classroom_data['submissions'] if sub['student_name'] == s['name']]), 1) for s in all_students) / len(all_students)
    else:
        class_avg_accuracy = 0
        class_avg_participation = 0
        class_avg_response_time = 0
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('student_report.html',
                         student=student,
                         student_name=student['name'],
                         total_rounds=total_rounds,
                         correct_rounds=correct_rounds,
                         accuracy=accuracy,
                         submissions=student_submissions,
                         student_submissions=student_submissions,
                         round_results=classroom_data.get('round_results', []),
                         current_time=current_time,
                         current_date=current_time.split(' ')[0],
                         participation_rate=round(participation_rate, 1),
                         missed_rounds=missed_rounds,
                         avg_response_time=round(avg_response_time, 1),
                         class_avg_accuracy=round(class_avg_accuracy, 1),
                         class_avg_participation=round(class_avg_participation, 1),
                         class_avg_response_time=round(class_avg_response_time, 1))

@classroom_bp.route('/generate_student_pdf/<student_name>')
def generate_student_pdf(student_name):
    """生成学生个人报告（PDF版）- 与网页版完全一致，一键下载"""
    if student_name not in classroom_data['students']:
        return jsonify({'error': 'Student not found'}), 404
    
    student = classroom_data['students'][student_name]
    
    # 计算统计数据
    total_rounds = student.get('total_rounds', 0)
    correct_rounds = student.get('correct_rounds', 0)
    accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
    
    # 获取学生提交记录
    student_submissions = [s for s in classroom_data['submissions'] 
                          if s['student_name'] == student_name]
    
    # 计算参与率
    total_rounds_available = max(len(classroom_data.get('round_results', [])), student.get('total_rounds', 0))
    student_submissions_count = len(student_submissions)
    participation_rate = (student_submissions_count / total_rounds_available * 100) if total_rounds_available > 0 else 0
    
    # 计算平均反应时间
    if student_submissions:
        avg_response_time = sum(s['answer_time'] for s in student_submissions) / len(student_submissions)
    else:
        avg_response_time = 0
    
    # 计算未参与轮次
    missed_rounds = total_rounds_available - student_submissions_count
    
    # 计算班级平均值
    all_students = list(classroom_data['students'].values())
    if all_students:
        class_avg_accuracy = sum(s.get('correct_rounds', 0) / max(s.get('total_rounds', 1), 1) * 100 for s in all_students) / len(all_students)
        class_avg_participation = sum(len([sub for sub in classroom_data['submissions'] if sub['student_name'] == s['name']]) / max(len(classroom_data.get('round_results', [])), s.get('total_rounds', 1)) * 100 for s in all_students) / len(all_students)
        class_avg_response_time = sum(sum(sub['answer_time'] for sub in classroom_data['submissions'] if sub['student_name'] == s['name']) / max(len([sub for sub in classroom_data['submissions'] if sub['student_name'] == s['name']]), 1) for s in all_students) / len(all_students)
    else:
        class_avg_accuracy = 0
        class_avg_participation = 0
        class_avg_response_time = 0
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 渲染HTML模板，添加自动打印功能
    html_content = render_template('student_report_print.html', 
                                 student=student, 
                                 student_name=student['name'],
                                 total_rounds=total_rounds,
                                 correct_rounds=correct_rounds,
                                 accuracy=accuracy,
                                 submissions=student_submissions,
                                 student_submissions=student_submissions,
                                 round_results=classroom_data.get('round_results', []),
                                 current_time=current_time,
                                 current_date=current_time.split(' ')[0],
                                 participation_rate=round(participation_rate, 1),
                                 missed_rounds=missed_rounds,
                                 avg_response_time=round(avg_response_time, 1),
                                 class_avg_accuracy=round(class_avg_accuracy, 1),
                                 class_avg_participation=round(class_avg_participation, 1),
                                 class_avg_response_time=round(class_avg_response_time, 1))
    
    return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

@classroom_bp.route('/reports')
def reports():
    """报告列表页面"""
    return render_template('reports.html', 
                         students=classroom_data['students'],
                         classroom_data=classroom_data)
