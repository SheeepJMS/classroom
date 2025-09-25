from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# 创建数据库实例
db = SQLAlchemy()

def init_db(app):
    """初始化数据库"""
    # 从环境变量获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # 如果是PostgreSQL URL，需要转换格式
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # 默认使用SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///math_homework.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建表
    with app.app_context():
        db.create_all()

# 学生模型
class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    score = db.Column(db.Integer, default=0)
    total_rounds = db.Column(db.Integer, default=0)
    correct_rounds = db.Column(db.Integer, default=0)
    last_answer_time = db.Column(db.Float, default=0)
    expression = db.Column(db.String(20), default='neutral')
    animation = db.Column(db.String(20), default='none')
    avatar_color = db.Column(db.String(20), default='#ff6b6b')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    submissions = db.relationship('Submission', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'score': self.score,
            'total_rounds': self.total_rounds,
            'correct_rounds': self.correct_rounds,
            'last_answer_time': self.last_answer_time,
            'expression': self.expression,
            'animation': self.animation,
            'avatar_color': self.avatar_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 提交记录模型
class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    earned_score = db.Column(db.Integer, default=0)
    answer_time = db.Column(db.Float, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'round': self.round_number,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'earned_score': self.earned_score,
            'answer_time': self.answer_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# 课堂会话模型
class ClassroomSession(db.Model):
    __tablename__ = 'classroom_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    current_round = db.Column(db.Integer, default=1)
    round_active = db.Column(db.Boolean, default=False)
    correct_answer = db.Column(db.String(200), default='')
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'session_name': self.session_name,
            'is_active': self.is_active,
            'current_round': self.current_round,
            'round_active': self.round_active,
            'correct_answer': self.correct_answer,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 轮次结果模型
class RoundResult(db.Model):
    __tablename__ = 'round_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('classroom_sessions.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'round': self.round_number,
            'correct_answer': self.correct_answer,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
