from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import time
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 存储课堂数据
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

@app.route('/')
def index():
    return redirect(url_for('classroom'))

@app.route('/classroom')
def classroom():
    # 默认不创建任何学生数据，保持空白状态
    return render_template('classroom.html', classroom_data=classroom_data)

@app.route('/start_class', methods=['POST'])
def start_class():
    classroom_data['is_active'] = True
    classroom_data['round_active'] = True
    classroom_data['start_time'] = time.time()
    return jsonify({'success': True})

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json()
    student_name = data.get('student_name', '').strip()
    
    if student_name and student_name not in classroom_data['students']:
        colors = ['#ff9a9e', '#fecfef', '#a8edea', '#fed6e3', '#d299c2', 
                 '#ffecd2', '#fcb69f', '#ff8a80', '#ffb74d', '#81c784',
                 '#64b5f6', '#ba68c8', '#4db6ac', '#ffd54f', '#f06292']
        avatar_color = random.choice(colors)
        
        classroom_data['students'][student_name] = {
            'name': student_name,
            'avatar_color': avatar_color,
            'expression': 'neutral',  # 默认面无表情
            'animation': 'none',
            'score': 0,
            'total_rounds': 0,
            'correct_rounds': 0,
            'answers': []
        }
        return jsonify({'success': True, 'student': classroom_data['students'][student_name]})
    
    return jsonify({'success': False, 'message': '学生姓名已存在或为空'})

@app.route('/submit_student_answer', methods=['POST'])
def submit_student_answer():
    data = request.get_json()
    student_name = data.get('student_name')
    answer = data.get('answer', '').strip()
    
    print(f"Received student_name: {student_name}")
    print(f"Available students: {list(classroom_data['students'].keys())}")
    
    if student_name not in classroom_data['students']:
        return jsonify({'success': False, 'message': f'Student "{student_name}" not found'})
    
    if not classroom_data['round_active']:
        return jsonify({'success': False, 'message': 'Round not active'})
    
    classroom_data['current_answers'][student_name] = answer
    
    # 设置学生表情为submitted（古灵精怪吐舌头扮鬼脸）
    classroom_data['students'][student_name]['expression'] = 'submitted'
    
    if classroom_data['start_time']:
        answer_time = time.time() - classroom_data['start_time']
        classroom_data['answer_times'][student_name] = answer_time
        classroom_data['students'][student_name]['last_answer_time'] = answer_time
    
    return jsonify({'success': True})

@app.route('/judge_answers', methods=['POST'])
def judge_answers():
    data = request.get_json()
    correct_answer = data.get('correct_answer', '').strip()
    question_score = data.get('question_score', 1)
    
    if not correct_answer:
        return jsonify({'success': False, 'message': 'Please enter correct answer'})
    
    classroom_data['correct_answer'] = correct_answer
    classroom_data['round_active'] = False
    
    round_result = {
        'round': classroom_data['current_round'],
        'correct_answer': correct_answer,
        'question_score': question_score,
        'results': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # 处理已答题的学生
    for student_name, answer in classroom_data['current_answers'].items():
        is_correct = answer.lower().strip() == correct_answer.lower().strip()
        
        student = classroom_data['students'][student_name]
        student['total_rounds'] += 1
        if is_correct:
            student['correct_rounds'] += 1
            student['score'] += question_score
            student['expression'] = 'smile'
            student['animation'] = 'celebration'
        else:
            student['expression'] = 'angry'
            student['animation'] = 'anger'
        
        submission = {
            'student_name': student_name,
            'round': classroom_data['current_round'],
            'answer': answer,
            'is_correct': is_correct,
            'question_score': question_score,
            'earned_score': question_score if is_correct else 0,
            'answer_time': classroom_data['answer_times'].get(student_name, 0),
            'timestamp': datetime.now().isoformat()
        }
        if 'answers' not in student:
            student['answers'] = []
        student['answers'].append(submission)
        classroom_data['submissions'].append(submission)
        
        round_result['results'][student_name] = {
            'answer': answer,
            'is_correct': is_correct,
            'question_score': question_score,
            'earned_score': question_score if is_correct else 0,
            'answer_time': classroom_data['answer_times'].get(student_name, 0)
        }
    
    # 处理未答题的学生
    for student_name in classroom_data['students']:
        if student_name not in classroom_data['current_answers']:
            student = classroom_data['students'][student_name]
            student['total_rounds'] += 1
            student['expression'] = 'embarrassed'
            student['animation'] = 'bounce'
            
            submission = {
                'student_name': student_name,
                'round': classroom_data['current_round'],
                'answer': '',
                'is_correct': False,
                'question_score': question_score,
                'earned_score': 0,
                'answer_time': 0,
                'timestamp': datetime.now().isoformat()
            }
            if 'answers' not in student:
                student['answers'] = []
            student['answers'].append(submission)
            classroom_data['submissions'].append(submission)
            
            round_result['results'][student_name] = {
                'answer': '',
                'is_correct': False,
                'question_score': question_score,
                'earned_score': 0,
                'answer_time': 0
            }
    
    classroom_data['round_results'].append(round_result)
    
    return jsonify({
        'success': True,
        'round': classroom_data['current_round'],
        'results': round_result['results'],
        'students': classroom_data['students']
    })

@app.route('/next_round', methods=['POST'])
def next_round():
    classroom_data['current_round'] += 1
    classroom_data['round_active'] = False
    classroom_data['current_answers'] = {}
    classroom_data['answer_times'] = {}
    classroom_data['start_time'] = None
    
    for student_name in classroom_data['students']:
        classroom_data['students'][student_name]['expression'] = 'neutral'  # 回到面无表情
        classroom_data['students'][student_name]['animation'] = 'none'
    
    return jsonify({
        'success': True, 
        'round': classroom_data['current_round'],
        'students': classroom_data['students']
    })

@app.route('/get_classroom_data')
def get_classroom_data():
    return jsonify(classroom_data)

@app.route('/create_demo_data')
def create_demo_data_route():
    create_demo_case_data()
    return jsonify({'success': True, 'message': '演示数据创建成功'})

@app.route('/reports')
def reports_page():
    # 不自动创建演示数据，保持reset后的空状态
    return render_template('reports.html', students=classroom_data['students'])

@app.route('/generate_student_report/<student_name>')
def generate_student_report(student_name):
    # 如果没有案例数据，先创建演示案例数据
    if not classroom_data['students'] or not classroom_data['submissions']:
        create_demo_case_data()
    
    if student_name not in classroom_data['students']:
        return "Student not found", 404
    
    student = classroom_data['students'][student_name]
    student_submissions = [s for s in classroom_data['submissions'] if s['student_name'] == student_name]
    
    # 计算统计数据
    total_rounds_available = len(classroom_data['round_results'])
    participation_rate = min(100, (len(student_submissions) / total_rounds_available * 100)) if total_rounds_available > 0 else 0
    missed_rounds = total_rounds_available - len(student_submissions)
    avg_response_time = sum(s['answer_time'] for s in student_submissions) / len(student_submissions) if student_submissions else 0
    
    # 计算准确率
    accuracy = (student['correct_rounds'] / max(student['total_rounds'], 1) * 100) if student['total_rounds'] > 0 else 0
    
    # 计算班级平均值
    all_students = list(classroom_data['students'].values())
    class_avg_accuracy = sum(s['correct_rounds'] / max(s['total_rounds'], 1) * 100 for s in all_students) / len(all_students) if all_students else 0
    class_avg_participation = sum(min(100, len([sub for sub in classroom_data['submissions'] if sub['student_name'] == name]) / total_rounds_available * 100) for name in classroom_data['students']) / len(classroom_data['students']) if total_rounds_available > 0 else 0
    class_avg_response_time = sum(s['answer_time'] for s in classroom_data['submissions']) / len(classroom_data['submissions']) if classroom_data['submissions'] else 0
    
    return render_template('student_report.html', 
                         student_name=student_name,
                         student=student,
                         submissions=student_submissions,
                         student_submissions=student_submissions,
                         participation_rate=participation_rate,
                         missed_rounds=missed_rounds,
                         total_rounds=total_rounds_available,
                         avg_response_time=avg_response_time,
                         accuracy=accuracy,
                         class_avg_accuracy=class_avg_accuracy,
                         class_avg_participation=class_avg_participation,
                         class_avg_response_time=class_avg_response_time,
                         current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/reset_classroom', methods=['POST'])
def reset_classroom():
    # 完全清空所有数据
    classroom_data['students'] = {}  # 清空所有学生
    classroom_data['current_round'] = 1
    classroom_data['round_active'] = False
    classroom_data['current_answers'] = {}
    classroom_data['answer_times'] = {}
    classroom_data['start_time'] = None
    classroom_data['submissions'] = []
    classroom_data['round_results'] = []
    
    return jsonify({
        'success': True,
        'round': classroom_data['current_round'],
        'students': classroom_data['students']  # 返回空的学生列表
    })

def create_demo_case_data():
    """创建演示案例数据（用于报告生成）"""
    # 清空现有数据
    classroom_data['students'] = {}
    classroom_data['submissions'] = []
    classroom_data['round_results'] = []
    
    # 创建演示学生
    demo_students = [
        'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry'
    ]
    
    for student_name in demo_students:
        # 先创建答题记录，再计算正确轮次
        student_submissions = []
        correct_count = 0
        
        for round_num in range(1, 6):
            is_correct = random.choice([True, False])
            if is_correct:
                correct_count += 1
            student_submissions.append({
                'student_name': student_name,
                'round': round_num,
                'answer': f'答案{round_num}',
                'is_correct': is_correct,
                'earned_score': 1 if is_correct else 0,
                'answer_time': random.uniform(5, 45),
                'timestamp': datetime.now().isoformat()
            })
        
        # 将答题记录添加到总列表
        classroom_data['submissions'].extend(student_submissions)
        
        # 创建学生数据，使用实际计算出的正确轮次
        classroom_data['students'][student_name] = {
            'name': student_name,
            'score': random.randint(5, 20),
            'total_rounds': 5,
            'correct_rounds': correct_count,  # 使用实际计算出的正确轮次
            'last_answer_time': random.uniform(10, 60),
            'expression': 'neutral',  # 默认面无表情
            'animation': 'none',
            'avatar_color': random.choice(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd']),
            'answers': []
        }
    
    # 创建演示轮次结果
    for round_num in range(1, 6):
        classroom_data['round_results'].append({
            'round': round_num,
            'correct_answer': f'正确答案{round_num}',
            'question_score': 1,
            'timestamp': datetime.now().isoformat()
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
