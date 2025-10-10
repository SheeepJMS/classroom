from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Class(db.Model):
    """班级模型"""
    __tablename__ = 'classes'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    ended_date = db.Column(db.DateTime)
    competition_goal_id = db.Column(db.String(36), db.ForeignKey('competition_goals.id'))
    
    # 关系
    students = db.relationship('Student', backref='class_ref', lazy=True)
    courses = db.relationship('Course', backref='class_ref', lazy=True)
    competition_goal = db.relationship('CompetitionGoal', backref='competition_goal_classes')

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    submissions = db.relationship('StudentSubmission', backref='student_ref', lazy=True)

class CompetitionGoal(db.Model):
    """竞赛目标模型"""
    __tablename__ = 'competition_goals'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_score = db.Column(db.Integer, default=100)
    goal_date = db.Column(db.Date, nullable=False)  # 竞赛目标日期
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    classes = db.relationship('Class', backref='competition_goal_ref', lazy=True)

class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), db.ForeignKey('classes.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    rounds = db.relationship('CourseRound', backref='course_ref', lazy=True)

class CourseRound(db.Model):
    """课程轮次模型"""
    __tablename__ = 'course_rounds'
    
    id = db.Column(db.String(36), primary_key=True)
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    question_score = db.Column(db.Integer, default=1)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    submissions = db.relationship('StudentSubmission', backref='round_ref', lazy=True)

class StudentSubmission(db.Model):
    """学生提交记录模型"""
    __tablename__ = 'student_submissions'
    
    id = db.Column(db.String(36), primary_key=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    round_id = db.Column(db.String(36), db.ForeignKey('course_rounds.id'), nullable=False)
    answer = db.Column(db.String(10), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    answer_time = db.Column(db.Float, nullable=False)  # 答题时间（秒）
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 确保每个学生每轮只能提交一次
    __table_args__ = (db.UniqueConstraint('student_id', 'round_id', name='unique_student_round'),)

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
