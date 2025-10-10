from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace(
        'postgres://', 'postgresql+psycopg://', 1
    )
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace(
        'postgresql://', 'postgresql+psycopg://', 1
    )

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# 数据库模型
class Class(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    ended_date = db.Column(db.DateTime)
    competition_goal_id = db.Column(
        db.String(36),
        db.ForeignKey('competition_goal.id')
    )

    students = db.relationship(
        'Student',
        backref='class_ref',
        lazy=True,
        cascade='all, delete-orphan'
    )
    courses = db.relationship(
        'Course',
        backref='class_ref',
        lazy=True,
        cascade='all, delete-orphan'
    )
    competition_goal = db.relationship(
        'CompetitionGoal',
        backref='competition_goal_classes',
        lazy=True
    )


class Student(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(
        db.String(36),
        db.ForeignKey('class.id'),
        nullable=False
    )
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(
        db.String(36),
        db.ForeignKey('class.id'),
        nullable=False
    )
    is_active = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


class CompetitionGoal(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_score = db.Column(db.Integer, default=100)
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
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


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
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            'course_id',
            'student_name',
            name='unique_student_per_course'
        ),
    )



class RoundResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            'course_id',
            'round_number',
            name='unique_round_per_course'
        ),
    )


class StudentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    answer = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean, default=False)
    answer_time = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# API路由
@app.route('/')
def index():
    """首页"""
    classes = Class.query.order_by(Class.created_date.desc()).all()
    goals = CompetitionGoal.query.order_by(
        CompetitionGoal.created_date.desc()
    ).all()

    # 计算总学生数量
    total_students = db.session.query(Student).count()

    return render_template(
        'homepage.html',
        classes=classes,
        goals=goals,
        total_students=total_students
    )


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
                'goal_date': None
            }

            # 暂时使用默认进度
            goal_progress = {
                'days_left': 77,
                'weeks_left': 11,
                'lessons_left': 22
            }

    return render_template(
        'class_detail.html',
        class_obj=class_obj,
        students=students,
        goal=goal,
        goal_progress=goal_progress
    )


@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    return render_template(
        'classroom.html',
        class_obj=class_obj,
        students=students
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)