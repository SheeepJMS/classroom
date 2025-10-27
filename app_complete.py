#!/usr/bin/env python3
"""
完整的数学课堂管理系统
包含：班级管理、学生管理、竞赛目标、课程答题、报告生成
"""

import os
import sys
from flask import Flask, jsonify, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import traceback
import uuid

# 创建Flask应用
app = Flask(__name__)

# 数据库配置
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("⚠️ 警告: DATABASE_URL 环境变量未设置，使用默认SQLite数据库")
    database_url = 'sqlite:///math_homework.db'
elif database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-secret-key')

db = SQLAlchemy(app)

# ==================== 数据库模型 ====================

class Class(db.Model):
    """班级模型"""
    __tablename__ = 'classes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    ended_date = db.Column(db.DateTime)
    competition_goal_id = db.Column(db.String(36), db.ForeignKey('competition_goals.id'))
    
    # 关系
    students = db.relationship('Student', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    courses = db.relationship('Course', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    competition_goal = db.relationship('CompetitionGoal', backref='classes', foreign_keys=[competition_goal_id])

class CompetitionGoal(db.Model):
    """竞赛目标模型"""
    __tablename__ = 'competition_goals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    goal_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, absent
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    submissions = db.relationship('StudentSubmission', backref='student_ref', lazy=True)
    attendances = db.relationship('CourseAttendance', backref='student_ref', lazy=True)

class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    current_round = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # 关系
    rounds = db.relationship('CourseRound', backref='course_ref', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('StudentSubmission', backref='course_ref', lazy=True)
    attendances = db.relationship('CourseAttendance', backref='course_ref', lazy=True)

class CourseRound(db.Model):
    """课程轮次模型"""
    __tablename__ = 'course_rounds'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    question_score = db.Column(db.Integer, default=1)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentSubmission(db.Model):
    """学生提交模型"""
    __tablename__ = 'student_submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    answer_time = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CourseAttendance(db.Model):
    """课程出勤模型"""
    __tablename__ = 'course_attendances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    is_absent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== 初始化数据库 ====================

def init_database():
    """初始化数据库表"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 如果没有默认班级，创建一个
            default_class = Class.query.filter_by(name="默认班级").first()
            if not default_class:
                default_class = Class(
                    id=str(uuid.uuid4()),
                    name="默认班级",
                    is_active=True
                )
                db.session.add(default_class)
                db.session.commit()
                print("✅ 创建默认班级")
    except Exception as e:
        print(f"❌ 初始化数据库失败: {str(e)}")
        traceback.print_exc()

init_database()

# ==================== 路由 ====================

# 首页路由
@app.route('/')
def index():
    """首页"""
    try:
        # 获取所有活跃班级
        classes = Class.query.filter_by(is_active=True).order_by(Class.created_date.desc()).all()
        
        # 获取所有活跃竞赛目标
        goals = CompetitionGoal.query.filter_by(is_active=True).order_by(CompetitionGoal.created_date.desc()).all()
        
        # 计算总学生数量
        total_students = Student.query.count()
        
        return render_template('homepage.html',
                             classes=classes,
                             goals=goals,
                             total_students=total_students)
    except Exception as e:
        print(f"❌ 加载首页失败: {str(e)}")
        traceback.print_exc()
        return f"<h1>启动成功！</h1><p>但加载主页时出错: {str(e)}</p>", 500

# 课堂路由
@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页 - 重定向到课堂页面"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        return redirect(f'/classroom/{class_id}')
    except Exception as e:
        print(f"❌ 加载班级详情失败: {str(e)}")
        return jsonify({'error': f'加载班级详情失败: {str(e)}'}), 500

@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        
        # 获取学生列表
        students = Student.query.filter_by(class_id=class_id).all()
        
        return render_template('classroom.html', class_id=class_id, class_obj=class_obj, students=students)
    except Exception as e:
        print(f"❌ 加载课堂页面失败: {str(e)}")
        return jsonify({'error': f'加载课堂页面失败: {str(e)}'}), 500

# 报告列表页面
@app.route('/reports')
def reports():
    """报告列表页面"""
    try:
        classes = Class.query.filter_by(is_active=True).all()
        return render_template('reports.html', classes=classes)
    except Exception as e:
        print(f"❌ 加载报告页面失败: {str(e)}")
        return jsonify({'error': f'加载报告页面失败: {str(e)}'}), 500

# 学生报告页面
@app.route('/student_report/<student_id>')
def student_report(student_id):
    """学生报告页面"""
    try:
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        # 获取学生的所有提交记录
        submissions = StudentSubmission.query.filter_by(student_id=student_id).order_by(StudentSubmission.created_at.desc()).all()
        
        # 计算统计数据
        total_score = sum(sub.answer_time for sub in submissions if sub.is_correct)
        total_rounds = len(set((sub.course_id, sub.round_number) for sub in submissions))
        correct_rounds = len(set((sub.course_id, sub.round_number) for sub in submissions if sub.is_correct))
        
        return render_template('student_report.html',
                             student=student,
                             submissions=submissions,
                             total_score=total_score,
                             total_rounds=total_rounds,
                             correct_rounds=correct_rounds)
    except Exception as e:
        print(f"❌ 加载学生报告失败: {str(e)}")
        return jsonify({'error': f'加载学生报告失败: {str(e)}'}), 500

# ==================== API路由 ====================

# 创建班级
@app.route('/api/create_class', methods=['POST'])
def create_class():
    """创建新班级"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': '班级名称不能为空'}), 400
        
        class_id = str(uuid.uuid4())
        new_class = Class(id=class_id, name=name, description=description, is_active=True)
        db.session.add(new_class)
        db.session.commit()
        
        print(f"✅ 创建新班级: {name}")
        return jsonify({'success': True, 'class_id': class_id})
        
    except Exception as e:
        print(f"❌ 创建班级失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建班级失败: {str(e)}'}), 500

# 结束班级
@app.route('/api/end_class/<class_id>', methods=['POST'])
def end_class(class_id):
    """结束班级"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        class_obj.is_active = False
        class_obj.ended_date = datetime.utcnow()
        db.session.commit()
        
        print(f"✅ 班级已结束: {class_obj.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 结束班级失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'结束班级失败: {str(e)}'}), 500

# 创建竞赛目标
@app.route('/api/create_competition_goal', methods=['POST'])
def create_competition_goal():
    """创建新竞赛目标"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        goal_date = data.get('goal_date')
        
        if not title or not goal_date:
            return jsonify({'success': False, 'message': '标题和目标日期不能为空'}), 400
        
        goal_id = str(uuid.uuid4())
        new_goal = CompetitionGoal(id=goal_id, title=title, description=description, goal_date=goal_date, is_active=True)
        db.session.add(new_goal)
        db.session.commit()
        
        print(f"✅ 创建新竞赛目标: {title}")
        return jsonify({'success': True, 'goal_id': goal_id})
        
    except Exception as e:
        print(f"❌ 创建竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建竞赛目标失败: {str(e)}'}), 500

# 结束竞赛目标
@app.route('/api/end_goal/<goal_id>', methods=['POST'])
def end_goal(goal_id):
    """结束竞赛目标"""
    try:
        goal = CompetitionGoal.query.filter_by(id=goal_id).first()
        if not goal:
            return jsonify({'success': False, 'message': '竞赛目标不存在'}), 404
        
        goal.is_active = False
        db.session.commit()
        
        print(f"✅ 竞赛目标已结束: {goal.title}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 结束竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'结束竞赛目标失败: {str(e)}'}), 500

# 绑定竞赛目标
@app.route('/api/bind_goal', methods=['POST'])
def bind_goal():
    """绑定竞赛目标到班级"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        goal_id = data.get('goal_id')
        
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        class_obj.competition_goal_id = goal_id
        db.session.commit()
        
        print(f"✅ 绑定竞赛目标到班级: {class_obj.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 绑定竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'绑定竞赛目标失败: {str(e)}'}), 500

# 添加学生
@app.route('/add_student', methods=['POST'])
def add_student():
    """添加学生"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        class_id = data.get('class_id') or request.headers.get('X-Class-ID')
        
        if not name or not class_id:
            return jsonify({'error': '参数不完整'}), 400
        
        # 检查是否已存在
        existing = Student.query.filter_by(name=name, class_id=class_id).first()
        if existing:
            return jsonify({'error': '该学生已经存在'}), 400
        
        student = Student(id=str(uuid.uuid4()), name=name, class_id=class_id, status='active')
        db.session.add(student)
        db.session.commit()
        
        print(f"✅ 添加学生: {name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 添加学生失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'添加学生失败: {str(e)}'}), 500

# 学生请假
@app.route('/api/student_absent/<student_id>', methods=['POST'])
def student_absent(student_id):
    """学生请假"""
    try:
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'}), 404
        
        student.status = 'absent'
        db.session.commit()
        
        print(f"✅ 学生请假: {student.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 学生请假失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'学生请假失败: {str(e)}'}), 500

# 创建课程
@app.route('/api/create_course', methods=['POST'])
def create_course():
    """创建新课程"""
    try:
        data = request.get_json()
        class_id = data.get('class_id') or request.headers.get('X-Class-ID')
        name = data.get('name', '').strip()
        
        if not class_id or not name:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 结束所有活跃课程
        Course.query.filter_by(class_id=class_id, is_active=True).update({'is_active': False, 'ended_at': datetime.utcnow()})
        
        # 创建新课程
        course_id = str(uuid.uuid4())
        course = Course(id=course_id, class_id=class_id, name=name, current_round=1, is_active=True)
        db.session.add(course)
        db.session.commit()
        
        # 标记学生出勤
        students = Student.query.filter_by(class_id=class_id, status='active').all()
        for student in students:
            attendance = CourseAttendance(
                id=str(uuid.uuid4()),
                course_id=course_id,
                student_id=student.id,
                is_absent=False
            )
            db.session.add(attendance)
        db.session.commit()
        
        print(f"✅ 创建新课程: {name}")
        return jsonify({'success': True, 'course_id': course_id})
        
    except Exception as e:
        print(f"❌ 创建课程失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建课程失败: {str(e)}'}), 500

# 开始课程
@app.route('/api/start_class', methods=['POST'])
def start_class():
    """开始课程（进入第一题）"""
    try:
        data = request.get_json()
        class_id = data.get('class_id') or request.headers.get('X-Class-ID')
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 获取活跃课程
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        print(f"✅ 开始课程: {course.name}")
        return jsonify({'success': True, 'course_id': course.id})
        
    except Exception as e:
        print(f"❌ 开始课程失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'开始课程失败: {str(e)}'}), 500

# 获取课堂数据
@app.route('/get_classroom_data')
def get_classroom_data():
    """获取课堂数据"""
    try:
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1].split('?')[0].split('#')[0]
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 获取课程
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        
        # 获取学生（排除请假学生）
        students = Student.query.filter_by(class_id=class_id, status='active').all()
        students_data = {}
        
        for student in students:
            submissions = []
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            
            if course:
                submissions = StudentSubmission.query.filter_by(student_id=student.id, course_id=course.id).all()
                for sub in submissions:
                    if sub.is_correct:
                        # 获取该轮次的分数
                        round_obj = CourseRound.query.filter_by(course_id=course.id, round_number=sub.round_number).first()
                        if round_obj:
                            total_score += round_obj.question_score
                        else:
                            total_score += 1
                        correct_rounds += 1
                total_rounds = len(set(sub.round_number for sub in submissions))
            
            students_data[student.name] = {
                'name': student.name,
                'id': student.id,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'last_answer': '',
                'last_answer_time': 0
            }
        
        result = {
            'success': True,
            'students': students_data,
            'current_round': course.current_round if course else 1,
            'round_active': False
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 获取课堂数据失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500

# 提交学生答案
@app.route('/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """提交学生答案"""
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        answer = data.get('answer', '').strip()
        answer_time = data.get('answer_time', 0.0)
        
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1].split('?')[0]
        
        if not student_name or not answer or not class_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取课程和学生
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        student = Student.query.filter_by(name=student_name, class_id=class_id).first()
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'}), 400
        
        # 检查是否已提交
        existing = StudentSubmission.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            round_number=course.current_round
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': '您已经提交过答案了'}), 400
        
        # 创建提交记录
        submission = StudentSubmission(
            id=str(uuid.uuid4()),
            student_id=student.id,
            course_id=course.id,
            round_number=course.current_round,
            answer=answer,
            answer_time=float(answer_time),
            is_correct=False  # 稍后评判
        )
        db.session.add(submission)
        db.session.commit()
        
        print(f"✅ 学生 {student_name} 提交答案: {answer}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 提交答案失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500

# 评判答案
@app.route('/judge_answers', methods=['POST'])
def judge_answers():
    """评判答案"""
    try:
        data = request.get_json()
        correct_answer = data.get('correct_answer', '').strip()
        question_score = data.get('question_score', 1)
        
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1].split('?')[0]
        
        if not correct_answer or not class_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取课程
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        # 创建或更新轮次记录
        round_record = CourseRound.query.filter_by(
            course_id=course.id,
            round_number=course.current_round
        ).first()
        
        if not round_record:
            round_record = CourseRound(
                id=str(uuid.uuid4()),
                course_id=course.id,
                round_number=course.current_round,
                correct_answer=correct_answer,
                question_score=question_score,
                is_completed=True
            )
            db.session.add(round_record)
        else:
            round_record.correct_answer = correct_answer
            round_record.question_score = question_score
            round_record.is_completed = True
        
        # 评判所有学生的答案
        students = Student.query.filter_by(class_id=class_id, status='active').all()
        students_data = {}
        
        for student in students:
            submission = StudentSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id,
                round_number=course.current_round
            ).first()
            
            # 计算历史总分数
            all_submissions = StudentSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).all()
            
            total_score = 0
            total_rounds = len(set(sub.round_number for sub in all_submissions))
            correct_rounds = 0
            
            for sub in all_submissions:
                if sub.is_correct:
                    round_obj = CourseRound.query.filter_by(course_id=course.id, round_number=sub.round_number).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
                    correct_rounds += 1
            
            # 判断当前答案
            expression = 'neutral'
            last_answer = ''
            last_answer_time = 0
            
            if submission:
                is_correct = submission.answer.strip().lower() == correct_answer.strip().lower()
                submission.is_correct = is_correct
                
                if is_correct:
                    total_score += question_score
                    correct_rounds += 1
                    expression = 'smile'
                else:
                    expression = 'angry'
                
                last_answer = submission.answer
                last_answer_time = submission.answer_time
            else:
                expression = 'embarrassed'
            
            students_data[student.name] = {
                'name': student.name,
                'id': student.id,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'expression': expression,
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'last_answer': last_answer,
                'last_answer_time': last_answer_time
            }
        
        db.session.commit()
        
        print(f"✅ 评判完成，处理了 {len(students_data)} 个学生")
        return jsonify({
            'success': True,
            'students': students_data,
            'round_number': course.current_round
        })
        
    except Exception as e:
        print(f"❌ 评判答案失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'判断失败: {str(e)}'}), 500

# 进入下一轮
@app.route('/next_round', methods=['POST'])
def next_round():
    """进入下一轮"""
    try:
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1].split('?')[0]
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        course.current_round += 1
        db.session.commit()
        
        print(f"✅ 进入下一轮: {course.current_round}")
        return jsonify({'success': True, 'round_number': course.current_round})
        
    except Exception as e:
        print(f"❌ 进入下一轮失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'进入下一轮失败: {str(e)}'}), 500

# 结束课程
@app.route('/api/end_course/<course_id>', methods=['POST'])
def end_course(course_id):
    """结束课程，显示领奖台"""
    try:
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        course.is_active = False
        course.ended_at = datetime.utcnow()
        db.session.commit()
        
        print(f"✅ 课程已结束: {course.name}")
        return redirect(f'/ceremony/{course_id}')
        
    except Exception as e:
        print(f"❌ 结束课程失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'结束课程失败: {str(e)}'}), 500

# 领奖台页面
@app.route('/ceremony/<course_id>')
def ceremony(course_id):
    """领奖台页面"""
    try:
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        # 计算每个学生的总分
        students = Student.query.filter_by(class_id=course.class_id).all()
        student_scores = []
        
        for student in students:
            submissions = StudentSubmission.query.filter_by(student_id=student.id, course_id=course_id).all()
            total_score = 0
            for sub in submissions:
                if sub.is_correct:
                    round_obj = CourseRound.query.filter_by(course_id=course_id, round_number=sub.round_number).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
            
            student_scores.append({
                'name': student.name,
                'score': total_score
            })
        
        # 按分数排序
        student_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return render_template('ceremony.html', course=course, student_scores=student_scores)
        
    except Exception as e:
        print(f"❌ 加载领奖台失败: {str(e)}")
        return jsonify({'error': f'加载领奖台失败: {str(e)}'}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

