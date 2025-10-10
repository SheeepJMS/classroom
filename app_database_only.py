#!/usr/bin/env python3
"""
完全数据库化的Flask应用
移除所有JSON文件依赖，所有数据操作直接使用数据库
"""

from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import uuid
import random
import string

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 数据库模型
class Class(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    ended_date = db.Column(db.DateTime)
    competition_goal_id = db.Column(db.String(36), db.ForeignKey('competition_goal.id'))
    
    # 关系
    students = db.relationship('Student', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    courses = db.relationship('Course', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    competition_goal = db.relationship('CompetitionGoal', backref='competition_goal_classes', lazy=True)

class Student(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('class.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('class.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class CompetitionGoal(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_score = db.Column(db.Integer, default=100)
    goal_date = db.Column(db.Date, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

# 新增的课堂状态表
class ClassroomState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False, unique=True)
    current_round = db.Column(db.Integer, default=1)
    round_active = db.Column(db.Boolean, default=False)
    correct_answer = db.Column(db.String(10))
    start_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StudentState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_rounds = db.Column(db.Integer, default=0)
    correct_rounds = db.Column(db.Integer, default=0)
    expression = db.Column(db.String(20), default='neutral')
    animation = db.Column(db.String(20), default='none')
    avatar_color = db.Column(db.String(7), default='#4ecdc4')
    last_answer_time = db.Column(db.Integer, default=0)
    last_answer = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('course_id', 'student_name', name='unique_student_per_course'),)

class RoundResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('course_id', 'round_number', name='unique_round_per_course'),)

class StudentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    answer = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean, default=False)
    answer_time = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# 数据库辅助函数
def get_or_create_classroom_state(course_id):
    """获取或创建课堂状态"""
    state = ClassroomState.query.filter_by(course_id=course_id).first()
    if not state:
        state = ClassroomState(course_id=course_id)
        db.session.add(state)
        db.session.commit()
    return state

def get_or_create_student_state(course_id, student_name):
    """获取或创建学生状态"""
    state = StudentState.query.filter_by(course_id=course_id, student_name=student_name).first()
    if not state:
        state = StudentState(course_id=course_id, student_name=student_name)
        db.session.add(state)
        db.session.commit()
    return state

def get_student_states(course_id):
    """获取课程中所有学生的状态"""
    return StudentState.query.filter_by(course_id=course_id).all()

def get_round_results(course_id):
    """获取课程的轮次结果"""
    return RoundResult.query.filter_by(course_id=course_id).order_by(RoundResult.round_number).all()

def get_student_submissions(course_id, round_number=None):
    """获取学生提交记录"""
    query = StudentSubmission.query.filter_by(course_id=course_id)
    if round_number:
        query = query.filter_by(round_number=round_number)
    return query.order_by(StudentSubmission.submitted_at).all()

# API路由
@app.route('/')
def index():
    """首页"""
    classes = Class.query.order_by(Class.created_date.desc()).all()
    goals = CompetitionGoal.query.order_by(CompetitionGoal.created_date.desc()).all()
    
    # 计算总学生数量
    total_students = db.session.query(Student).count()
    
    return render_template('homepage.html', 
                         classes=classes, 
                         goals=goals,
                         total_students=total_students)

@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页"""
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    
    # 获取竞赛目标信息
    goal = None
    goal_progress = None
    if class_obj.competition_goal_id:
        goal_obj = CompetitionGoal.query.get(class_obj.competition_goal_id)
        if goal_obj:
            goal = {
                'id': goal_obj.id,
                'title': goal_obj.title,
                'name': goal_obj.title,
                'goal_date': goal_obj.goal_date.strftime('%Y-%m-%d') if goal_obj.goal_date else None
            }
            
            # 计算进度
            if goal_obj.goal_date:
                days_left = (goal_obj.goal_date - datetime.now().date()).days
                weeks_left = days_left // 7
                lessons_left = days_left // 7 * 2  # 假设每周2节课
                
                goal_progress = {
                    'days_left': max(0, days_left),
                    'weeks_left': max(0, weeks_left),
                    'lessons_left': max(0, lessons_left)
                }
    
    return render_template('class_detail.html', 
                         class_obj=class_obj, 
                         students=students,
                         goal=goal,
                         goal_progress=goal_progress)

@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    return render_template('classroom.html', class_obj=class_obj, students=students)

@app.route('/api/start_course', methods=['POST'])
def start_course():
    """开始课程"""
    data = request.get_json()
    class_id = data.get('class_id')
    course_name = data.get('course_name', '')
    
    if not class_id:
        return jsonify({'error': '班级ID不能为空'}), 400
    
    try:
        # 结束当前活跃课程
        Course.query.filter_by(class_id=class_id, is_active=True).update({'is_active': False})
        
        # 创建新课程
        course = Course(
            id=str(uuid.uuid4()),
            name=course_name,
            class_id=class_id,
            is_active=True
        )
        db.session.add(course)
        
        # 创建课堂状态
        classroom_state = ClassroomState(
            course_id=course.id,
            current_round=1,
            round_active=False
        )
        db.session.add(classroom_state)
        
        # 初始化学生状态
        students = Student.query.filter_by(class_id=class_id).all()
        for student in students:
            student_state = StudentState(
                course_id=course.id,
                student_name=student.name
            )
            db.session.add(student_state)
        
        db.session.commit()
        
        return jsonify({'success': True, 'course_id': course.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_classroom_data')
def get_classroom_data():
    """获取课堂数据"""
    class_id = request.headers.get('X-Class-ID')
    if not class_id:
        return jsonify({'error': '班级ID不能为空'}), 400
    
    try:
        # 获取活跃课程
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'error': '没有活跃课程'}), 400
        
        # 获取课堂状态
        classroom_state = get_or_create_classroom_state(course.id)
        
        # 获取学生状态
        student_states = get_student_states(course.id)
        students_data = {}
        for state in student_states:
            students_data[state.student_name] = {
                'name': state.student_name,
                'score': state.score,
                'total_rounds': state.total_rounds,
                'correct_rounds': state.correct_rounds,
                'last_answer_time': state.last_answer_time,
                'expression': state.expression,
                'animation': state.animation,
                'avatar_color': state.avatar_color,
                'last_answer': state.last_answer
            }
        
        # 获取轮次结果
        round_results = get_round_results(course.id)
        round_results_data = []
        for result in round_results:
            submissions = get_student_submissions(course.id, result.round_number)
            results = {}
            for submission in submissions:
                results[submission.student_name] = {
                    'answer': submission.answer,
                    'correct': submission.is_correct,
                    'answer_time': submission.answer_time
                }
            
            round_results_data.append({
                'round': result.round_number,
                'correct_answer': result.correct_answer,
                'results': results
            })
        
        course_data = {
            'id': course.id,
            'name': course.name,
            'class_id': course.class_id,
            'is_active': course.is_active,
            'created_date': course.created_date.strftime('%Y-%m-%d'),
            'students': students_data,
            'round_results': round_results_data,
            'current_round': classroom_state.current_round,
            'round_active': classroom_state.round_active,
            'correct_answer': classroom_state.correct_answer,
            'start_time': classroom_state.start_time.isoformat() if classroom_state.start_time else None
        }
        
        return jsonify(course_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_class', methods=['POST'])
def start_class():
    """开始答题"""
    data = request.get_json()
    course_id = data.get('course_id')
    correct_answer = data.get('correct_answer', '')
    
    if not course_id:
        return jsonify({'error': '课程ID不能为空'}), 400
    
    try:
        # 更新课堂状态
        classroom_state = get_or_create_classroom_state(course_id)
        classroom_state.round_active = True
        classroom_state.correct_answer = correct_answer
        classroom_state.start_time = datetime.utcnow()
        classroom_state.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """学生提交答案"""
    data = request.get_json()
    course_id = data.get('course_id')
    student_name = data.get('student_name')
    answer = data.get('answer', '')
    
    if not all([course_id, student_name]):
        return jsonify({'error': '参数不完整'}), 400
    
    try:
        # 获取课堂状态
        classroom_state = get_or_create_classroom_state(course_id)
        if not classroom_state.round_active or not classroom_state.start_time:
            return jsonify({'error': '当前没有活跃的答题轮次'}), 400
        
        # 计算答题时间
        current_time = datetime.utcnow()
        answer_time = int((current_time - classroom_state.start_time).total_seconds())
        
        # 更新学生状态
        student_state = get_or_create_student_state(course_id, student_name)
        student_state.last_answer_time = answer_time
        student_state.last_answer = answer
        student_state.updated_at = current_time
        
        db.session.commit()
        
        return jsonify({'success': True, 'answer_time': answer_time})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/judge_answers', methods=['POST'])
def judge_answers():
    """判定答案"""
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': '课程ID不能为空'}), 400
    
    try:
        # 获取课堂状态
        classroom_state = get_or_create_classroom_state(course_id)
        if not classroom_state.round_active:
            return jsonify({'error': '当前没有活跃的答题轮次'}), 400
        
        correct_answer = classroom_state.correct_answer
        current_round = classroom_state.current_round
        
        # 获取所有学生状态
        student_states = get_student_states(course_id)
        
        # 判定每个学生的答案
        round_result = RoundResult(
            course_id=course_id,
            round_number=current_round,
            correct_answer=correct_answer
        )
        db.session.add(round_result)
        
        for student_state in student_states:
            # 判定答案
            is_correct = student_state.last_answer == correct_answer
            
            # 更新学生状态
            student_state.total_rounds += 1
            if is_correct:
                student_state.correct_rounds += 1
                student_state.score += 1
                student_state.expression = 'happy'
            else:
                student_state.expression = 'sad'
            
            student_state.updated_at = datetime.utcnow()
            
            # 创建提交记录
            submission = StudentSubmission(
                course_id=course_id,
                round_number=current_round,
                student_name=student_state.student_name,
                answer=student_state.last_answer,
                is_correct=is_correct,
                answer_time=student_state.last_answer_time
            )
            db.session.add(submission)
        
        # 更新课堂状态
        classroom_state.round_active = False
        classroom_state.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 返回更新后的学生状态
        updated_student_states = get_student_states(course_id)
        students_data = {}
        for state in updated_student_states:
            students_data[state.student_name] = {
                'name': state.student_name,
                'score': state.score,
                'total_rounds': state.total_rounds,
                'correct_rounds': state.correct_rounds,
                'last_answer_time': state.last_answer_time,
                'expression': state.expression,
                'animation': state.animation,
                'avatar_color': state.avatar_color,
                'last_answer': state.last_answer
            }
        
        return jsonify({
            'success': True,
            'students': students_data,
            'round_result': {
                'round': current_round,
                'correct_answer': correct_answer,
                'results': {name: data for name, data in students_data.items()}
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/next_round', methods=['POST'])
def next_round():
    """下一轮"""
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': '课程ID不能为空'}), 400
    
    try:
        # 更新课堂状态
        classroom_state = get_or_create_classroom_state(course_id)
        classroom_state.current_round += 1
        classroom_state.round_active = False
        classroom_state.correct_answer = ''
        classroom_state.start_time = None
        classroom_state.updated_at = datetime.utcnow()
        
        # 重置学生表情
        student_states = get_student_states(course_id)
        for student_state in student_states:
            student_state.expression = 'neutral'
            student_state.animation = 'none'
            student_state.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'current_round': classroom_state.current_round})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
