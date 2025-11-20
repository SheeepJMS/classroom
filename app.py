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
import random
import statistics

# 创建Flask应用
app = Flask(__name__)

# 数据库配置
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("⚠️ 警告: DATABASE_URL 环境变量未设置，使用默认SQLite数据库")
    database_url = 'sqlite:///math_homework.db'
elif database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
# 使用pg8000驱动（兼容Python 3.13）

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
    
    # 备用字段 - 用于未来扩展
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据
    extra_field_1 = db.Column(db.String(200))
    extra_field_2 = db.Column(db.String(200))
    extra_field_3 = db.Column(db.String(200))
    extra_number_1 = db.Column(db.Integer)
    extra_number_2 = db.Column(db.Integer)
    extra_boolean_1 = db.Column(db.Boolean)
    extra_boolean_2 = db.Column(db.Boolean)
    
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
    
    # 备用字段 - 用于未来扩展
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据
    extra_field_1 = db.Column(db.String(200))
    extra_field_2 = db.Column(db.String(200))
    extra_number_1 = db.Column(db.Integer)  # 例如：目标分数
    extra_number_2 = db.Column(db.Integer)

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, absent
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 备用字段 - 用于未来扩展
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据
    extra_field_1 = db.Column(db.String(200))  # 例如：学号、座位号、家长联系方式
    extra_field_2 = db.Column(db.String(200))  # 例如：备注信息
    extra_field_3 = db.Column(db.String(200))
    extra_number_1 = db.Column(db.Integer)  # 例如：学生编号
    extra_number_2 = db.Column(db.Integer)
    extra_boolean_1 = db.Column(db.Boolean)  # 例如：是否特殊学生
    extra_boolean_2 = db.Column(db.Boolean)
    
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
    
    # 备用字段 - 用于未来扩展
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据
    extra_field_1 = db.Column(db.String(200))  # 例如：课程主题、课程类型
    extra_field_2 = db.Column(db.String(200))
    extra_number_1 = db.Column(db.Integer)  # 例如：总题数
    extra_number_2 = db.Column(db.Integer)
    extra_boolean_1 = db.Column(db.Boolean)  # 例如：是否公开课
    
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
    
    # 行为记录（新增字段，需要迁移数据库）
    guess_count = db.Column(db.Integer, default=0, nullable=True)  # 猜题次数
    copy_count = db.Column(db.Integer, default=0, nullable=True)  # 抄袭次数
    noisy_count = db.Column(db.Integer, default=0, nullable=True)  # 吵闹次数
    distracted_count = db.Column(db.Integer, default=0, nullable=True)  # 分心次数
    penalty_score = db.Column(db.Integer, default=0, nullable=True)  # 扣分总数

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
            
            # 尝试添加新字段到已存在的 student_submissions 表
            try:
                from sqlalchemy import text
                # 检查字段是否存在并添加
                with db.engine.connect() as conn:
                    # 添加 guess_count
                    conn.execute(text("ALTER TABLE student_submissions ADD COLUMN IF NOT EXISTS guess_count INTEGER DEFAULT 0"))
                    # 添加 copy_count
                    conn.execute(text("ALTER TABLE student_submissions ADD COLUMN IF NOT EXISTS copy_count INTEGER DEFAULT 0"))
                    # 添加 noisy_count
                    conn.execute(text("ALTER TABLE student_submissions ADD COLUMN IF NOT EXISTS noisy_count INTEGER DEFAULT 0"))
                    # 添加 distracted_count
                    conn.execute(text("ALTER TABLE student_submissions ADD COLUMN IF NOT EXISTS distracted_count INTEGER DEFAULT 0"))
                    # 添加 penalty_score
                    conn.execute(text("ALTER TABLE student_submissions ADD COLUMN IF NOT EXISTS penalty_score INTEGER DEFAULT 0"))
                    conn.commit()
                print("✅ 数据库字段添加成功")
            except Exception as e:
                print(f"⚠️ 添加字段时出错（可能已经存在）: {str(e)}")
            
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
        
        # 获取所有非活跃班级（历史班级）
        inactive_classes = Class.query.filter_by(is_active=False).order_by(Class.ended_date.desc()).all()
        
        # 获取所有活跃竞赛目标
        goals = CompetitionGoal.query.filter_by(is_active=True).order_by(CompetitionGoal.created_date.desc()).all()
        
        # 获取所有非活跃竞赛目标
        inactive_goals = CompetitionGoal.query.filter_by(is_active=False).order_by(CompetitionGoal.created_date.desc()).all()
        
        # 计算总学生数量（仅统计未结束/活跃班级中的学生）
        total_students = db.session.query(Student).join(Class, Student.class_id == Class.id).filter(Class.is_active == True).count()
        
        # 为每个班级添加统计数据
        for class_obj in classes:
            class_obj.student_count = len(class_obj.students)
            class_obj.course_count = len(class_obj.courses)
        
        # 为历史班级添加统计数据
        for class_obj in inactive_classes:
            class_obj.student_count = len(class_obj.students)
            class_obj.course_count = len(class_obj.courses)
        
        # 构建classes_json用于前端JavaScript
        classes_json = {class_obj.id: {'id': class_obj.id, 'name': class_obj.name} for class_obj in classes}
        
        return render_template('homepage.html',
                             classes=classes,
                             inactive_classes=inactive_classes,
                             competition_goals=goals,
                             inactive_competition_goals=inactive_goals,
                             total_students=total_students,
                             classes_json=classes_json)
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
def class_management(class_id):
    """班级管理页面 - 显示学生列表、课程列表等"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        
        # 获取学生列表（班级管理页面显示所有学生，包括请假学生，方便恢复）
        # 按状态分组：活跃学生在前面，请假学生在后面
        all_students = Student.query.filter_by(class_id=class_id).all()
        active_students = [s for s in all_students if s.status == 'active']
        absent_students = [s for s in all_students if s.status == 'absent']
        students = active_students + absent_students  # 活跃学生在前面
        
        # 为学生添加统计数据
        all_courses = Course.query.filter_by(class_id=class_id).all()
        for student in students:
            # 计算总得分（所有课程得分的累加）
            total_score = 0
            courses_count = 0
            absences_count = 0
            
            for course in all_courses:
                submissions = StudentSubmission.query.filter_by(
                    student_id=student.id,
                    course_id=course.id
                ).all()
                
                # 如果学生在该课程有提交记录，说明参加了
                if submissions:
                    courses_count += 1
                    for sub in submissions:
                        if sub.is_correct:
                            round_obj = CourseRound.query.filter_by(course_id=course.id, round_number=sub.round_number).first()
                            if round_obj:
                                total_score += round_obj.question_score
                            else:
                                total_score += 1
                else:
                    # 检查是否标记为缺席
                    attendance = CourseAttendance.query.filter_by(
                        student_id=student.id,
                        course_id=course.id
                    ).first()
                    if attendance and attendance.is_absent:
                        absences_count += 1
            
            # 为学生对象添加动态属性（如果字段不存在）
            if not hasattr(student, 'total_score'):
                student.total_score = total_score
            else:
                student.total_score = total_score
            if not hasattr(student, 'courses_count'):
                student.courses_count = courses_count
            else:
                student.courses_count = courses_count
            if not hasattr(student, 'absences_count'):
                student.absences_count = absences_count
            else:
                student.absences_count = absences_count
        
        # 获取课程列表（按时间降序，最新的在前）
        # 如果有结束时间，按结束时间排序；否则按创建时间排序
        from sqlalchemy import case
        courses = Course.query.filter_by(class_id=class_id).order_by(
            case(
                (Course.ended_at.isnot(None), Course.ended_at),
                else_=Course.created_at
            ).desc(),
            Course.created_at.desc()  # 作为次要排序条件
        ).all()
        
        # 为class_obj添加排序后的课程列表（转换为字典格式供模板使用）
        courses_data = []
        for course in courses:
            # 确定显示时间：有结束时间显示结束时间，否则显示创建时间
            display_time = course.ended_at if course.ended_at else course.created_at
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'created_at': course.created_at,
                'created_date': display_time.strftime('%Y-%m-%d %H:%M:%S') if display_time else '',
                'current_round': course.current_round,
                'is_active': course.is_active
            })
        
        # 竞赛目标信息
        goal = None
        goal_progress = None
        if class_obj.competition_goal_id:
            g = CompetitionGoal.query.filter_by(id=class_obj.competition_goal_id).first()
            if g:
                goal = {
                    'id': g.id,
                    'title': g.title,
                    'description': g.description or '',
                    'goal_date': g.goal_date.strftime('%Y-%m-%d') if g.goal_date else None
                }
                # 进度（剩余天/周/估算课次）
                from datetime import date
                if g.goal_date:
                    dleft = max((g.goal_date - date.today()).days, 0)
                    wleft = dleft // 7
                    # 每7天一节课的估算课次
                    lessons_left = wleft
                    goal_progress = {'days_left': dleft, 'weeks_left': wleft, 'lessons_left': lessons_left}

        # 将排序后的课程数据添加到class_obj（创建一个简单的对象包装器）
        class_data_dict = {
            'id': class_obj.id,
            'name': class_obj.name,
            'description': class_obj.description,
            'created_date': class_obj.created_date.strftime('%Y-%m-%d') if class_obj.created_date else '',
            'courses': courses_data  # 已排序的课程列表
        }
        
        return render_template('class_detail.html', 
                             class_data=class_data_dict, 
                             class_obj=class_obj,
                             class_id=class_id,
                             students=students,
                             courses=courses,
                             goal=goal,
                             goal_progress=goal_progress)
    except Exception as e:
        print(f"❌ 加载班级管理页面失败: {str(e)}")
        return jsonify({'error': f'加载班级管理页面失败: {str(e)}'}), 500

@app.route('/course/<course_id>')
def course_page(course_id):
    """课程答题页面"""
    try:
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        class_obj = Class.query.filter_by(id=course.class_id).first()
        students = Student.query.filter_by(class_id=course.class_id, status='active').all()
        
        return render_template('classroom.html', 
                             course_id=course_id,
                             course=course,
                             class_id=course.class_id,
                             class_obj=class_obj, 
                             students=students)
    except Exception as e:
        print(f"❌ 加载课程页面失败: {str(e)}")
        return jsonify({'error': f'加载课程页面失败: {str(e)}'}), 500

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

# 课程报告页面
@app.route('/reports/<course_id>')
def course_reports(course_id):
    """特定课程的报告页面"""
    try:
        # 获取课程
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        # 获取班级
        class_obj = Class.query.filter_by(id=course.class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        
        # 获取该班级的所有学生（排除请假学生）
        students = Student.query.filter_by(class_id=course.class_id, status='active').all()
        
        # 构建学生数据字典
        students_data = {}
        for student in students:
            # 获取该学生在当前课程的所有提交记录
            submissions = StudentSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).all()
            
            # 计算该课程中的统计数据
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            
            for sub in submissions:
                if sub.is_correct:
                    # 获取该轮次的分数
                    round_obj = CourseRound.query.filter_by(
                        course_id=course.id,
                        round_number=sub.round_number
                    ).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
                    correct_rounds += 1
                total_rounds = max(total_rounds, sub.round_number)
            
            # 计算实际参与的轮次数
            unique_rounds = len(set(sub.round_number for sub in submissions))
            if unique_rounds > 0:
                total_rounds = unique_rounds
            
            students_data[student.id] = {
                'id': student.id,
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': getattr(student, 'avatar_color', '#4ecdc4'),
                'last_answer': '',
                'last_answer_time': 0
            }
        
        # 构建课程数据（用于模板）
        classroom_data = {
            'id': course.id,
            'name': course.name,
            'class_id': course.class_id,
            'current_round': course.current_round,
            'students': students_data
        }
        
        return render_template('reports.html',
                             students=students_data,
                             classroom_data=classroom_data,
                             course_id=course_id,
                             course=course,
                             class_obj=class_obj)
    except Exception as e:
        print(f"❌ 加载课程报告页面失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'加载课程报告页面失败: {str(e)}'}), 500

# 学生报告页面
@app.route('/student_report/<student_id>')
def student_report(student_id):
    """学生报告页面"""
    try:
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        # 检查学生状态：请假学生无法查看报告
        if student.status == 'absent':
            return jsonify({'error': '请假状态的学生无法查看报告'}), 403
        
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

# 兼容旧链接：/generate_student_report/<student_id>?course_id=...
@app.route('/generate_student_report/<student_id>')
def generate_student_report(student_id):
    """生成（查看）学生在某课程中的报告，兼容旧URL。"""
    try:
        course_id = request.args.get('course_id')
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        # 检查学生状态：请假学生无法查看报告
        if student.status == 'absent':
            return jsonify({'error': '请假状态的学生无法查看报告'}), 403

        # 根据是否传入 course_id 过滤提交记录
        query = StudentSubmission.query.filter_by(student_id=student_id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        submissions = query.order_by(StudentSubmission.created_at.desc()).all()

        # 统计行为总次数（本课程）
        behavior_totals = {
            'guess_count': sum((s.guess_count or 0) for s in submissions),
            'copy_count': sum((s.copy_count or 0) for s in submissions),
            'noisy_count': sum((s.noisy_count or 0) for s in submissions),
            'distracted_count': sum((s.distracted_count or 0) for s in submissions),
        }

        # 基础学生信息（带 avatar_color 兼容）
        student_view = {
            'id': student.id,
            'name': student.name,
            'avatar_color': getattr(student, 'avatar_color', '#ff6b6b')
        }

        # 课程信息与班级数据
        course = Course.query.filter_by(id=course_id).first() if course_id else None
        
        # 统计（使用总轮次数，未参与算作错误）
        correct_rounds = len(set((sub.course_id, sub.round_number) for sub in submissions if sub.is_correct))
        if course:
            all_rounds = CourseRound.query.filter_by(course_id=course.id).count()
            accuracy = round((correct_rounds / all_rounds) * 100) if all_rounds > 0 else 0
            total_rounds = all_rounds  # 设置total_rounds用于模板渲染
        else:
            total_rounds = len(set((sub.course_id, sub.round_number) for sub in submissions))
            accuracy = round((correct_rounds / total_rounds) * 100) if total_rounds > 0 else 0
        course_data = {
            'name': course.name if course else '数学竞赛课堂'
        }

        # 课程回合与班级统计
        class_avg_accuracy = 0
        class_avg_participation = 0
        avg_response_time = 0
        class_avg_response_time = 0
        student_total_score = 0
        total_possible_score = 0
        class_avg_score = 0
        class_round_stats = []
        class_total_rounds = 0

        participated_rounds = 0
        student_submissions_view = []
        if course:
            rounds = CourseRound.query.filter_by(course_id=course.id).all()
            all_rounds_count = len(rounds)  # 所有轮次数（包括可能作废的）
            # 构造学生每轮的提交视图，按round对齐
            # 速度等级计算函数（每题）
            def get_speed_level_per_question(t_student: float, t_class_avg: float) -> str:
                try:
                    if not t_class_avg or t_class_avg <= 0:
                        return ''
                    # 最低时间保护，防止误触
                    if t_student is None:
                        t_student = 0
                    if t_student < 1.5:
                        t_student = 1.5
                    # 大题：全班平均时间很长时，使用绝对区间
                    if t_class_avg > 25:
                        if t_student <= 0.8 * t_class_avg:
                            return '快'
                        elif t_student <= 1.2 * t_class_avg:
                            return '正常'
                        else:
                            return '稍慢'
                    # 常规题：用比例判定
                    ratio = t_student / t_class_avg
                    if ratio <= 0.6:
                        return '很快'
                    elif ratio <= 1.0:
                        return '快'
                    elif ratio <= 1.4:
                        return '稍慢'
                    else:
                        return '很慢'
                except Exception:
                    return ''

            # 获取活跃学生ID集合（用于过滤请假学生）
            active_students = Student.query.filter_by(class_id=course.class_id, status='active').all()
            active_student_ids = {s.id for s in active_students}
            active_count = len(active_students) if active_students else 1
            
            # 全班提交（需在使用前定义，避免未绑定错误）
            # 只包含活跃学生的提交记录，排除请假学生，确保请假学生不参与数据计算
            all_class_submissions = StudentSubmission.query.filter_by(course_id=course.id).all()
            class_submissions = [s for s in all_class_submissions if s.student_id in active_student_ids]
            
            # 先计算作废轮次（需要先计算，以便后续过滤）
            invalid_rounds = set()  # 作废轮次集合
            round_nums = sorted(set(r.round_number for r in rounds))
            
            # 预先计算哪些轮次是作废的
            for rn in round_nums:
                rs = [s for s in class_submissions if s.round_number==rn]
                students_who_participated = set(s.student_id for s in rs)
                students_who_correct = set(s.student_id for s in rs if s.is_correct)
                correct_count = len(students_who_correct)
                acc = (correct_count/active_count)*100 if active_count>0 else 0
                participants = len(students_who_participated)
                part = (participants/active_count)*100 if active_count>0 else 0
                if rs:
                    times = [s.answer_time for s in rs if s.answer_time is not None]
                    avg_t = round(statistics.mean(times),1) if times else 0
                else:
                    avg_t = 0
                # 判定无效轮次
                is_invalid_round = (part == 0 and acc == 0 and avg_t < 10)
                if is_invalid_round:
                    invalid_rounds.add(rn)
                    print(f"⚠️ 轮次 {rn} 作废（参与率{part}%，正确率{acc}%，平均耗时{avg_t}秒）")

            for r in rounds:
                # 跳过作废轮次，不显示在报告中
                if r.round_number in invalid_rounds:
                    continue
                    
                rs = next((s for s in submissions if s.round_number == r.round_number), None)
                # 识别该轮违规类型（优先级：猜题>抄题>打闹>走神）
                violation_type = None
                if rs:
                    if (rs.guess_count or 0) > 0:
                        violation_type = '猜题'
                    elif (rs.copy_count or 0) > 0:
                        violation_type = '抄题'
                    elif (rs.noisy_count or 0) > 0:
                        violation_type = '打闹'
                    elif (rs.distracted_count or 0) > 0:
                        violation_type = '走神'

                if rs and (rs.answer is not None and str(rs.answer).strip() != ''):
                    participated_rounds += 1
                    is_correct = bool(rs.is_correct)
                    q_score = r.question_score if r and r.question_score else 1
                    # 本题班级平均时间（只计算有作答的同学）
                    round_class_times = [s.answer_time for s in class_submissions if s.round_number == r.round_number and s.answer_time is not None and (s.answer is not None and str(s.answer).strip() != '')]
                    t_class_avg = statistics.mean(round_class_times) if round_class_times else 0
                    t_student = rs.answer_time or 0
                    speed_level = get_speed_level_per_question(t_student, t_class_avg)
                    student_submissions_view.append({
                        'round': r.round_number,
                        'answer': rs.answer,
                        'is_correct': is_correct,
                        'question_score': q_score,
                        'answer_time': rs.answer_time or 0,
                        'violation_type': violation_type,
                        'speed_level': speed_level
                    })
                else:
                    student_submissions_view.append({
                        'round': r.round_number,
                        'answer': '',
                        'is_correct': False,
                        'question_score': r.question_score if r and r.question_score else 1,
                        'answer_time': 0,
                        'violation_type': violation_type,
                        'speed_level': ''
                    })
            # 只计算有效轮次的总分
            total_possible_score = sum((r.question_score or 1) for r in rounds if r.round_number not in invalid_rounds)

            # 学生总分（只计算有效轮次）
            for sub in submissions:
                if sub.is_correct and sub.round_number not in invalid_rounds:
                    r = next((rr for rr in rounds if rr.round_number == sub.round_number), None)
                    student_total_score += (r.question_score if r and r.question_score else 1)

            # 班级平均准确率/参与率/分数
            # 按学生聚合
            from collections import defaultdict
            # 改为按轮次统计（去重），避免多次提交同一轮次时重复计数
            student_correct_rounds = defaultdict(set)
            student_total_rounds = defaultdict(set)
            student_scores = defaultdict(int)

            for s in class_submissions:
                # 跳过作废轮次，不参与统计
                if s.round_number in invalid_rounds:
                    continue
                # 使用round_number作为集合，自动去重
                student_total_rounds[s.student_id].add(s.round_number)
                if s.is_correct:
                    student_correct_rounds[s.student_id].add(s.round_number)
                    r = next((rr for rr in rounds if rr.round_number == s.round_number), None)
                    student_scores[s.student_id] += (r.question_score if r and r.question_score else 1)

            # 平均准确率 - 按轮次计算
            if student_total_rounds:
                acc_list = []
                for sid in student_total_rounds.keys():
                    total_r = len(student_total_rounds[sid])
                    correct_r = len(student_correct_rounds[sid])
                    acc_list.append((correct_r/total_r)*100 if total_r>0 else 0)
                class_avg_accuracy = round(sum(acc_list)/len(acc_list)) if acc_list else 0
                class_avg_score = round(sum(student_scores.values())/len(student_scores)) if student_scores else 0

            # 参与率（参与过任意回合的学生比）
            participated = len(set(s.student_id for s in class_submissions))
            class_avg_participation = round((participated/active_count)*100) if active_count>0 else 0

            # 响应时间
            st_times = [s.answer_time for s in submissions if s.answer_time is not None]
            avg_response_time = round(statistics.mean(st_times),1) if st_times else 0
            class_times = [s.answer_time for s in class_submissions if s.answer_time is not None]
            class_avg_response_time = round(statistics.mean(class_times),1) if class_times else 0

            # 按轮统计（只统计有效轮次）
            valid_rounds_count = 0  # 有效轮次数（排除作废轮次）
            for rn in round_nums:
                # 跳过作废轮次
                if rn in invalid_rounds:
                    continue
                    
                rs = [s for s in class_submissions if s.round_number==rn]
                # 按学生去重，统计有多少学生答对了这一轮
                students_who_participated = set(s.student_id for s in rs)
                students_who_correct = set(s.student_id for s in rs if s.is_correct)
                # 准确率 = 答对的学生数 / 班级总学生数（未参与的学生算作错误）
                correct_count = len(students_who_correct)
                # active_count 是班级总活跃学生数，包括未参与的
                acc = (correct_count/active_count)*100 if active_count>0 else 0
                # 参与率 = 参与的学生数 / 班级总学生数
                participants = len(students_who_participated)
                part = (participants/active_count)*100 if active_count>0 else 0
                # 平均答题时间（只计算参与的学生）
                if rs:
                    times = [s.answer_time for s in rs if s.answer_time is not None]
                    avg_t = round(statistics.mean(times),1) if times else 0
                else:
                    avg_t = 0
                
                # 只统计有效轮次
                class_round_stats.append({'round': rn,'accuracy': round(acc,1),'participation_rate': round(part,1),'avg_time': avg_t})
                valid_rounds_count += 1

        # 参与率：参与轮次 / 有效轮次（排除作废轮次）（供评语使用）
        # 使用有效轮次数而不是总轮次数，排除作废的轮次
        if course:
            # 使用有效轮次数，如果没有有效轮次则使用所有轮次数（避免除零）
            valid_total_rounds = valid_rounds_count if valid_rounds_count > 0 else all_rounds_count
            class_total_rounds = valid_rounds_count  # 更新为有效轮次数，供模板使用
        else:
            valid_total_rounds = class_total_rounds
        participation_rate = round((participated_rounds / valid_total_rounds) * 100) if valid_total_rounds > 0 else 0

        # 生成个性化反馈（优先排名，其次参与率，再看正确率；60%优秀、40%不错、20%以下偏低）
        def build_feedback():
            # 无数据或未参与
            if class_total_rounds == 0 or participation_rate == 0:
                return '本次未参与作答，建议下次按时参与练习；先建立连续参与习惯！'

            parts = []

            # 排名主评语（用班级得分排名或百分位）
            rank_text = ''
            if course:
                # 计算排名 - 使用与student_report_center一致的逻辑
                rank = None
                percentile = None
                try:
                    # 统计比当前学生分数高的学生数
                    higher_count = sum(1 for score in student_scores.values() if score > student_total_score)
                    rank = higher_count + 1 if student_scores else None
                    percentile = round(((rank - 1) / len(student_scores)) * 100, 1) if rank and len(student_scores) else None
                except Exception:
                    rank = None

                if percentile is not None:
                    if percentile <= 5:
                        rank_text = '表现卓越，稳居榜首，持续保持！'
                    elif percentile <= 15:
                        rank_text = '表现非常出色，稳定在前列，继续冲刺！'
                    elif percentile <= 30:
                        rank_text = '表现优秀，稳居班级前列，继续发力！'
                    elif percentile <= 70:
                        rank_text = '表现良好，稳步提升中，坚持复盘可更进一步！'
                    else:
                        rank_text = '具备潜力，建议先稳住基础，逐步追赶班级节奏！'
                else:
                    rank_text = '表现良好，稳步提升中，坚持复盘可更进一步！'
            parts.append(rank_text)

            # 参与率修饰
            if participation_rate >= 90:
                parts.append('课堂投入度很高，保持积极参与！')
            elif participation_rate >= 70:
                parts.append('参与比较稳定，再多坚持几轮会更好！')
            elif participation_rate >= 40:
                parts.append('参与度一般，建议按时作答每一轮，形成稳定节奏！')
            else:
                parts.append('本次参与偏少，优先提升参与率，完整参与每一轮尤为重要！')

            # 正确率修饰（60/40/20）
            if accuracy >= 60:
                parts.append('正确率已达优秀水平，继续冲刺更高分！')
            elif accuracy >= 40:
                parts.append('正确率不错，建议复盘错题，巩固易错点！')
            elif accuracy >= 20:
                parts.append('正确率有提升空间，建议先夯实基础题的稳定性！')
            else:
                parts.append('本次正确率偏低，建议从基础知识点和例题入手，逐步建立信心！')

            # 用时修饰：与班级平均比对，保持与题目“速度等级”口径一致
            if avg_response_time and class_avg_response_time:
                try:
                    ratio = avg_response_time / class_avg_response_time if class_avg_response_time > 0 else 1
                except Exception:
                    ratio = 1
                if ratio <= 0.6:
                    parts.append('反应速度很快，思维敏捷！')
                elif ratio <= 1.0:
                    parts.append('反应速度较快，节奏良好！')
                elif ratio <= 1.4:
                    parts.append('思考节奏略慢，可在熟练题型上提速！')
                else:
                    parts.append('本次节奏偏慢，建议控制用时，先拿稳会做题！')
            elif avg_response_time:
                # 兜底：没有班均时长时用绝对阈值
                if avg_response_time <= 10:
                    parts.append('反应速度较快，节奏良好！')
                elif avg_response_time <= 20:
                    parts.append('思考节奏合理，保持稳定输出！')
                else:
                    parts.append('本次节奏偏慢，建议控制用时，先拿稳会做题！')

            return ' '.join(parts)

        feedback_text = build_feedback()

        # 移动端/微信优先渲染竖屏模板
        ua = (request.headers.get('User-Agent') or '').lower()
        prefer_mobile = any(k in ua for k in ['micromessenger', 'iphone', 'android', 'mobile'])

        template_name = 'student_report_mobile.html' if prefer_mobile else 'student_report.html'

        # 竞赛目标信息（供报告显示）
        competition_goal_name = None
        competition_goal_date = None
        days_to_competition = None
        classes_before_competition = None
        if course:
            cls = Class.query.filter_by(id=course.class_id).first()
            if cls and cls.competition_goal_id:
                g = CompetitionGoal.query.filter_by(id=cls.competition_goal_id).first()
                if g:
                    competition_goal_name = g.title
                    competition_goal_date = g.goal_date.strftime('%Y-%m-%d') if g.goal_date else None
                    if g.goal_date:
                        from datetime import date
                        days_to_competition = max((g.goal_date - date.today()).days, 0)
                        # 每7天一节课估算
                        classes_before_competition = days_to_competition // 7

        return render_template(template_name,
                             student=student_view,
                             student_name=student.name,
                             current_date=datetime.now().strftime('%Y-%m-%d'),
                             course_data=course_data,
                             submissions=submissions,
                             student_submissions=student_submissions_view,
                             total_score=student_total_score,
                             total_rounds=total_rounds,
                             correct_rounds=correct_rounds,
                             accuracy=accuracy,
                             personalized_feedback={'focus_feedback': feedback_text},
                             class_avg_accuracy=class_avg_accuracy,
                             participation_rate=participation_rate,
                             class_avg_participation=class_avg_participation,
                             avg_response_time=avg_response_time,
                             class_avg_response_time=class_avg_response_time,
                             student_total_score=student_total_score,
                             total_possible_score=total_possible_score if total_possible_score>0 else 1,
                             class_avg_score=class_avg_score,
                             class_round_stats=class_round_stats,
                             class_total_rounds=class_total_rounds,
                                 behavior_totals=behavior_totals,
                                 competition_goal_name=competition_goal_name,
                                 competition_goal_date=competition_goal_date,
                                 days_to_competition=days_to_competition,
                                 classes_before_competition=classes_before_competition)
    except Exception as e:
        print(f"❌ 生成学生报告失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'生成学生报告失败: {str(e)}'}), 500

# 学生报告中心页面
@app.route('/student_report_center/<student_id>')
def student_report_center(student_id):
    """学生报告中心页面 - 移动端优化"""
    try:
        # 获取学生信息
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        # 检查学生状态：请假学生无法查看报告
        if student.status == 'absent':
            return jsonify({'error': '请假状态的学生无法查看报告'}), 403
        
        # 获取班级信息
        class_obj = Class.query.filter_by(id=student.class_id).first()
        
        # 获取该学生班级的所有课程（按创建时间降序）
        courses = Course.query.filter_by(class_id=student.class_id).order_by(Course.created_at.desc()).all()
        
        # 构建课程数据
        courses_data = []
        for course in courses:
            # 获取该学生在该课程的所有提交记录
            submissions = StudentSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).all()
            
            if submissions:
                # 计算统计数据
                # 实际参与的轮次数（去重）
                total_rounds = len(set(sub.round_number for sub in submissions))
                # 正确答题的轮次数（去重，只计算每个轮次至少答对一次）
                correct_rounds = len(set(s.round_number for s in submissions if s.is_correct))
                # 计算准确率：正确轮次 / 总轮次数（未参与算作错误）
                all_rounds = CourseRound.query.filter_by(course_id=course.id).count()
                accuracy = (correct_rounds / all_rounds * 100) if all_rounds > 0 else 0
                
                # 计算总分
                total_score = 0
                for s in submissions:
                    if s.is_correct:
                        round_obj = CourseRound.query.filter_by(
                            course_id=course.id,
                            round_number=s.round_number
                        ).first()
                        if round_obj:
                            total_score += round_obj.question_score
                        else:
                            total_score += 1
                
                # 计算参与率（基于轮次数）
                participation_rate = (total_rounds / all_rounds * 100) if all_rounds > 0 else 100
                
                # 计算排名
                all_students = Student.query.filter_by(class_id=student.class_id, status='active').all()
                student_scores = {}
                for class_student in all_students:
                    class_submissions = StudentSubmission.query.filter_by(
                        student_id=class_student.id,
                        course_id=course.id
                    ).all()
                    
                    class_score = 0
                    for s in class_submissions:
                        if s.is_correct:
                            round_obj = CourseRound.query.filter_by(
                                course_id=course.id,
                                round_number=s.round_number
                            ).first()
                            if round_obj:
                                class_score += round_obj.question_score
                            else:
                                class_score += 1
                    student_scores[class_student.id] = class_score
                
                # 计算排名 - 正确的方法是统计比当前学生分数高的学生数
                # 如果有n个学生分数更高，当前学生排名就是n+1
                # 例如：分数 [100, 90, 90, 80]，80分的学生排名是4
                higher_count = sum(1 for score in student_scores.values() if score > total_score)
                rank = higher_count + 1
                
                courses_data.append({
                    'course': course,
                    'date': course.created_at.strftime('%Y年%m月%d日') if course.created_at else '',
                    'course_name': course.name,
                    'participation_rate': round(participation_rate, 1),
                    'accuracy': round(accuracy, 1),
                    'score': total_score,
                    'rank': rank,
                    'total_students': len(all_students)
                })
        
        return render_template(
            'student_report_center.html',
            student=student,
            class_obj=class_obj,
            courses_data=courses_data,
            current_date=datetime.now().strftime('%Y年%m月%d日')
        )
    except Exception as e:
        print(f"❌ 加载学生报告中心失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'加载学生报告中心失败: {str(e)}'}), 500

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

# 删除班级
@app.route('/api/delete_class/<class_id>', methods=['POST'])
def delete_class(class_id):
    """删除班级"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        db.session.delete(class_obj)
        db.session.commit()
        
        print(f"✅ 班级已删除: {class_obj.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 删除班级失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除班级失败: {str(e)}'}), 500

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

# 获取所有可用竞赛目标（活跃）
@app.route('/api/get_competition_goals', methods=['GET'])
def get_competition_goals():
    try:
        goals = CompetitionGoal.query.filter_by(is_active=True).order_by(CompetitionGoal.created_date.desc()).all()
        goal_views = [{
            'id': g.id,
            'title': g.title,
            'description': g.description,
            'goal_date': g.goal_date.isoformat() if g.goal_date else None
        } for g in goals]
        return jsonify({'success': True, 'goals': goal_views})
    except Exception as e:
        print(f"❌ 加载竞赛目标失败: {str(e)}")
        return jsonify({'success': False, 'message': f'加载竞赛目标失败: {str(e)}'}), 500

# 将竞赛目标分配（绑定）到班级
@app.route('/api/assign_goal_to_class', methods=['POST'])
def assign_goal_to_class():
    try:
        data = request.get_json() or {}
        class_id = (data.get('class_id') or '').strip()
        goal_id = (data.get('goal_id') or '').strip()
        if not class_id or not goal_id:
            return jsonify({'success': False, 'message': 'class_id 和 goal_id 必填'}), 400

        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        goal = CompetitionGoal.query.filter_by(id=goal_id).first()
        if not goal:
            return jsonify({'success': False, 'message': '竞赛目标不存在'}), 404

        class_obj.competition_goal_id = goal.id
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ 分配竞赛目标失败: {str(e)}")
        if db.session:
            db.session.rollback()
        return jsonify({'success': False, 'message': f'分配竞赛目标失败: {str(e)}'}), 500

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

# 删除竞赛目标
@app.route('/api/delete_competition_goal/<goal_id>', methods=['DELETE'])
def delete_competition_goal(goal_id):
    """删除竞赛目标"""
    try:
        goal = CompetitionGoal.query.filter_by(id=goal_id).first()
        if not goal:
            return jsonify({'success': False, 'message': '竞赛目标不存在'}), 404
        
        db.session.delete(goal)
        db.session.commit()
        
        print(f"✅ 竞赛目标已删除: {goal.title}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 删除竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除竞赛目标失败: {str(e)}'}), 500

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

# 取消班级的竞赛目标
@app.route('/api/remove_goal_from_class', methods=['POST'])
def remove_goal_from_class():
    """取消班级的竞赛目标"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        # 将竞赛目标ID设置为None，取消绑定
        class_obj.competition_goal_id = None
        db.session.commit()
        
        print(f"✅ 已取消班级 {class_obj.name} 的竞赛目标")
        return jsonify({'success': True, 'message': '竞赛目标已取消'})
        
    except Exception as e:
        print(f"❌ 取消竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'取消竞赛目标失败: {str(e)}'}), 500

# 添加学生
@app.route('/add_student', methods=['POST'])
@app.route('/api/add_student', methods=['POST'])
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
        return jsonify({'success': True, 'message': f'{student.name}已请假'})
        
    except Exception as e:
        print(f"❌ 学生请假失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'学生请假失败: {str(e)}'}), 500

# 学生恢复
@app.route('/api/student_active/<student_id>', methods=['POST'])
def student_active(student_id):
    """学生恢复（取消请假）"""
    try:
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'}), 404
        
        student.status = 'active'
        db.session.commit()
        
        print(f"✅ 学生恢复: {student.name}")
        return jsonify({'success': True, 'message': f'{student.name}已恢复'})
        
    except Exception as e:
        print(f"❌ 学生恢复失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'学生恢复失败: {str(e)}'}), 500

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
        return jsonify({
            'success': True, 
            'course_id': course_id,
            'redirect_url': f'/course/{course_id}'
        })
        
    except Exception as e:
        print(f"❌ 创建课程失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建课程失败: {str(e)}'}), 500

# 创建课程（别名）
@app.route('/api/start_course', methods=['POST'])
def start_course():
    """创建课程（前端调用此接口）"""
    try:
        data = request.get_json()
        # 支持两种参数名：course_name 和 name
        name = data.get('course_name', '').strip()
        if not name:
            name = data.get('name', '').strip()
        
        # 从URL或headers获取class_id
        class_id = data.get('class_id')
        if not class_id:
            class_id = request.headers.get('X-Class-ID')
        
        if not class_id:
            # 尝试从referer获取
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1].split('?')[0]
        
        if not name:
            return jsonify({'success': False, 'message': '课程名称不能为空'}), 400
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
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
        return jsonify({
            'success': True, 
            'course_id': course_id,
            'redirect_url': f'/course/{course_id}'
        })
        
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
        
        # 优先从请求体中获取course_id
        course_id = data.get('course_id')
        
        # 如果没提供course_id，尝试从URL获取
        if not course_id:
            referer = request.headers.get('Referer', '')
            if '/course/' in referer:
                course_id = referer.split('/course/')[-1].split('?')[0]
        
        # 如果仍然没有course_id，尝试从class_id获取活跃课程
        if not course_id:
            class_id = request.headers.get('X-Class-ID')
            if class_id:
                course = Course.query.filter_by(class_id=class_id, is_active=True).first()
                if course:
                    course_id = course.id
        
        if not student_name or not answer or not course_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取课程和学生
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        student = Student.query.filter_by(name=student_name, class_id=course.class_id).first()
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'}), 400
        
        # 检查学生状态：请假学生无法提交答案
        if student.status == 'absent':
            return jsonify({'success': False, 'message': '请假状态的学生无法参与答题'}), 403
        
        # 检查是否已提交
        existing = StudentSubmission.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            round_number=course.current_round
        ).first()
        
        if existing:
            print(f"⚠️ 学生 {student_name} 在轮次 {course.current_round} 已经提交过答案: {existing.answer}")
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
        
        print(f"✅ 学生 {student_name} 在轮次 {course.current_round} 提交答案: {answer}")
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
        
        # 优先从请求体中获取course_id
        course_id = data.get('course_id')
        
        # 如果没提供course_id，尝试从URL获取
        if not course_id:
            referer = request.headers.get('Referer', '')
            if '/course/' in referer:
                course_id = referer.split('/course/')[-1].split('?')[0]
        
        # 如果仍然没有course_id，尝试从class_id获取活跃课程
        if not course_id:
            class_id = request.headers.get('X-Class-ID')
            if class_id:
                course = Course.query.filter_by(class_id=class_id, is_active=True).first()
                if course:
                    course_id = course.id
        
        if not correct_answer or not course_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        
        # 获取课程
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        class_id = course.class_id  # 使用课程对应的班级ID
        
        print(f"🎯 评判轮次 {course.current_round} 的答案，正确答案: {correct_answer}，分数: {question_score}")
        
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
        students_list = Student.query.filter_by(class_id=class_id, status='active').all()
        students_data = {}
        
        for student in students_list:
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
            
            # 先计算历史成绩（不包括当前轮次）
            historical_score = 0
            historical_correct_rounds = 0
            historical_rounds = set()
            
            for sub in all_submissions:
                if sub.round_number < course.current_round:  # 只计算历史轮次
                    historical_rounds.add(sub.round_number)
                    if sub.is_correct:
                        round_obj = CourseRound.query.filter_by(course_id=course.id, round_number=sub.round_number).first()
                        if round_obj:
                            historical_score += round_obj.question_score
                        else:
                            historical_score += 1
            
            # 历史正确轮次数（同一轮次只算一次）
            historical_correct_rounds = len([r for r in historical_rounds if 
                any(sub.is_correct and sub.round_number == r for sub in all_submissions)])
            
            # 判断当前答案
            expression = 'neutral'
            last_answer = ''
            last_answer_time = 0
            current_round_score = 0
            is_current_correct = False
            
            if submission:
                # 判断当前轮次答案是否正确
                print(f"📝 学生 {student.name} 轮次 {course.current_round} 答案: '{submission.answer}' vs 正确答案: '{correct_answer}'")
                is_current_correct = submission.answer.strip().lower() == correct_answer.strip().lower()
                # 更新数据库中的is_correct状态
                submission.is_correct = is_current_correct
                print(f"{'✅ 正确' if is_current_correct else '❌ 错误'}: {is_current_correct}")
                
                if is_current_correct:
                    current_round_score = question_score
                    expression = 'smile'
                else:
                    expression = 'angry'
                
                last_answer = submission.answer
                last_answer_time = submission.answer_time
            else:
                print(f"⚠️ 学生 {student.name} 在轮次 {course.current_round} 没有提交答案")
                expression = 'embarrassed'
            
            # 计算总分数和轮次
            total_score = historical_score + current_round_score
            # total_rounds: 课程的总轮次数（包括未参与的轮次），用于计算准确率
            # 准确率 = 正确轮次数 / 课程总轮次数
            total_rounds = course.current_round  # 使用当前课程的总轮次
            if submission:
                # 有提交记录，正确轮次增加
                correct_rounds = historical_correct_rounds + (1 if is_current_correct else 0)
            else:
                # 没有提交记录，正确轮次不变（未作答算作错误）
                correct_rounds = historical_correct_rounds
            
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
        # 安全获取JSON数据
        try:
            data = request.get_json()
        except:
            data = {}
        
        if not data:
            data = {}
        
        course_id = data.get('course_id')
        class_id = request.headers.get('X-Class-ID')
        
        # 如果没提供course_id，尝试从class_id获取活跃课程
        if not course_id and class_id:
            course = Course.query.filter_by(class_id=class_id, is_active=True).first()
            if course:
                course_id = course.id
        
        # 如果仍然没有，尝试从URL获取
        if not course_id:
            referer = request.headers.get('Referer', '')
            if '/course/' in referer:
                course_id = referer.split('/course/')[-1].split('?')[0]
        
        if not course_id:
            return jsonify({'success': False, 'message': '课程ID不能为空'}), 400
        
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            print(f"❌ 课程不存在: {course_id}")
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        print(f"当前课程轮次: {course.current_round}")
        course.current_round += 1
        db.session.commit()
        
        print(f"✅ 进入下一轮: {course.current_round}")
        
        # 获取更新后的学生数据
        students = Student.query.filter_by(class_id=course.class_id, status='active').all()
        students_data = {}
        
        for student in students:
            submissions = StudentSubmission.query.filter_by(
                student_id=student.id,
                course_id=course_id
            ).all()
            
            print(f"👤 学生 {student.name} 有 {len(submissions)} 条提交记录")
            
            # 计算所有轮次的分数和准确率
            total_score = 0
            correct_rounds = 0
            
            for sub in submissions:
                print(f"  轮次 {sub.round_number}: 答案='{sub.answer}' is_correct={sub.is_correct}")
                if sub.is_correct:
                    round_obj = CourseRound.query.filter_by(course_id=course_id, round_number=sub.round_number).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
            
            # total_rounds: 课程的总轮次数（包括未参与的轮次）
            # correct_rounds: 正确答题的轮次数（同一轮次只算一次）
            total_rounds = course.current_round - 1  # 当前课程的总轮次减1（因为还没进入下一轮）
            correct_rounds = len(set(sub.round_number for sub in submissions if sub.is_correct))
            print(f"  → 总分: {total_score}, 总轮次: {total_rounds}, 正确轮次: {correct_rounds}")
            
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
        
        return jsonify({
            'success': True, 
            'round': course.current_round,
            'round_number': course.current_round,
            'current_round': course.current_round,
            'students': students_data
        })
        
    except Exception as e:
        print(f"❌ 进入下一轮失败: {str(e)}")
        traceback.print_exc()
        if db.session:
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

# 标记学生行为
@app.route('/api/mark_behavior', methods=['POST'])
def mark_behavior():
    """标记学生行为（guess, copy, noisy, distracted）"""
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        behavior = data.get('behavior', '').strip()
        course_id = data.get('course_id')
        
        # 如果没提供course_id，尝试获取
        if not course_id:
            referer = request.headers.get('Referer', '')
            if '/course/' in referer:
                course_id = referer.split('/course/')[-1].split('?')[0]
        
        if not student_name or not behavior or not course_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取课程和学生
        course = Course.query.filter_by(id=course_id).first()
        if not course:
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        student = Student.query.filter_by(name=student_name, class_id=course.class_id).first()
        if not student:
            return jsonify({'success': False, 'message': '学生不存在'}), 404
        
        # 获取或创建当前轮次的提交记录
        submission = StudentSubmission.query.filter_by(
            student_id=student.id,
            course_id=course_id,
            round_number=course.current_round
        ).first()
        
        # 如果学生没有提交记录，创建一个空的提交记录（用于记录行为）
        if not submission:
            submission = StudentSubmission(
                id=str(uuid.uuid4()),
                student_id=student.id,
                course_id=course_id,
                round_number=course.current_round,
                answer='',  # 空答案，表示未提交
                answer_time=0.0,
                is_correct=False
            )
            db.session.add(submission)
        
        # 更新行为计数
        if behavior == 'guess':
            submission.guess_count = (submission.guess_count or 0) + 1
        elif behavior == 'copy':
            submission.copy_count = (submission.copy_count or 0) + 1
        elif behavior == 'noisy':
            submission.noisy_count = (submission.noisy_count or 0) + 1
        elif behavior == 'distracted':
            submission.distracted_count = (submission.distracted_count or 0) + 1
        
        # 标记该题得分为0（无论答案是否正确）
        submission.is_correct = False
        
        db.session.commit()
        
        print(f"✅ 学生 {student_name} 行为标记: {behavior}, 该题得分为0")
        return jsonify({'success': True, 'message': '行为已记录，该题得分为0'})
        
    except Exception as e:
        print(f"❌ 标记行为失败: {str(e)}")
        traceback.print_exc()
        if db.session:
            db.session.rollback()
        return jsonify({'success': False, 'message': f'标记失败: {str(e)}'}), 500

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
                'score': total_score,
                'avatar_color': student.avatar_color if hasattr(student, 'avatar_color') else f'#{random.randint(0, 0xFFFFFF):06x}'
            })
        
        # 按分数排序
        student_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 获取班级信息
        class_obj = Class.query.filter_by(id=course.class_id).first()
        
        course_view = {
            'id': course.id,
            'class_id': course.class_id,
            'name': getattr(course, 'name', ''),
            'created_at': getattr(course, 'created_at', None).strftime('%Y-%m-%d %H:%M:%S') if getattr(course, 'created_at', None) else None,
            'ended_at': getattr(course, 'ended_at', None).strftime('%Y-%m-%d %H:%M:%S') if getattr(course, 'ended_at', None) else None
        }
        class_view = {'id': class_obj.id, 'name': class_obj.name} if class_obj else {'id': course.class_id}
        return render_template('ceremony.html', 
                             course=course_view, 
                             student_scores=student_scores,
                             classroom_data=class_view)
        
    except Exception as e:
        print(f"❌ 加载领奖台失败: {str(e)}")
        return jsonify({'error': f'加载领奖台失败: {str(e)}'}), 500

# 在应用启动时初始化数据库
init_database()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

