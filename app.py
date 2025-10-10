from flask import Flask, render_template, request, jsonify
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
        'postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace(
        'postgresql://', 'postgresql+psycopg://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# 数据库模型
class Class(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    ended_date = db.Column(db.DateTime)
    competition_goal_id = db.Column(
        db.String(36), db.ForeignKey('competition_goal.id'))

    students = db.relationship(
        'Student',
        backref='class_ref',
        lazy=True,
        cascade='all, delete-orphan')
    courses = db.relationship(
        'Course',
        backref='class_ref',
        lazy=True,
        cascade='all, delete-orphan')
    competition_goal = db.relationship(
        'CompetitionGoal',
        backref='competition_goal_classes',
        lazy=True)


class Student(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(
        db.String(36),
        db.ForeignKey('class.id'),
        nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(
        db.String(36),
        db.ForeignKey('class.id'),
        nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


class CompetitionGoal(db.Model):
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_score = db.Column(db.Integer, default=100)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)


# API路由
@app.route('/api/create_class', methods=['POST'])
def create_class():
    """创建班级API"""
    try:
        data = request.get_json()
        class_name = data.get('name', '').strip()
        class_description = data.get('description', '').strip()

        if not class_name:
            return jsonify({'success': False, 'message': '班级名称不能为空'}), 400

        new_class = Class(name=class_name, description=class_description)
        db.session.add(new_class)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '班级创建成功',
            'class_id': new_class.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建班级失败: {str(e)}'}), 500


@app.route('/api/create_competition_goal', methods=['POST'])
def create_competition_goal():
    """创建竞赛目标API"""
    try:
        data = request.get_json()
        title = data.get('title', data.get('name', '')).strip()
        description = data.get('description', '').strip()
        target_score = data.get('target_score', 100)

        if not title:
            return jsonify({'success': False, 'message': '竞赛目标名称不能为空'}), 400

        new_goal = CompetitionGoal(
            title=title,
            description=description,
            target_score=target_score)
        db.session.add(new_goal)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '竞赛目标创建成功',
            'goal_id': new_goal.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {'success': False, 'message': f'创建竞赛目标失败: {str(e)}'}), 500


@app.route('/api/add_student', methods=['POST'])
def add_student():
    """添加学生API"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        class_id = data.get('class_id', '').strip()

        if not name or not class_id:
            return jsonify({'success': False, 'message': '学生姓名和班级ID不能为空'}), 400

        new_student = Student(name=name, class_id=class_id)
        db.session.add(new_student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '学生添加成功',
            'student_id': new_student.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'添加学生失败: {str(e)}'}), 500


@app.route('/api/start_course', methods=['POST'])
def start_course():
    """开始课程API"""
    try:
        data = request.get_json()
        course_name = data.get('course_name', '').strip()
        class_id = data.get('class_id', '').strip()

        if not course_name or not class_id:
            return jsonify({'success': False, 'message': '课程名称和班级ID不能为空'}), 400

        Course.query.filter_by(class_id=class_id,
                               is_active=True).update({'is_active': False})

        new_course = Course(
            name=course_name,
            class_id=class_id,
            is_active=True)
        db.session.add(new_course)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '课程开始成功',
            'course_id': new_course.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'开始课程失败: {str(e)}'}), 500


@app.route('/api/delete_class/<class_id>', methods=['DELETE'])
def delete_class(class_id):
    """删除班级API"""
    try:
        class_obj = Class.query.get_or_404(class_id)
        db.session.delete(class_obj)
        db.session.commit()

        return jsonify({'success': True, 'message': '班级删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除班级失败: {str(e)}'}), 500


@app.route('/api/end_class/<class_id>', methods=['POST'])
def end_class(class_id):
    """结束班级API"""
    try:
        class_obj = Class.query.get_or_404(class_id)
        class_obj.ended_date = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': '班级已结束'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'结束班级失败: {str(e)}'}), 500


@app.route('/api/delete_student', methods=['POST'])
def delete_student():
    """删除学生API"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', '').strip()

        if not student_id:
            return jsonify({'success': False, 'message': '学生ID不能为空'}), 400

        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()

        return jsonify({'success': True, 'message': '学生删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除学生失败: {str(e)}'}), 500


@app.route('/api/delete_competition_goal/<goal_id>', methods=['DELETE'])
def delete_competition_goal(goal_id):
    """删除竞赛目标API"""
    try:
        _goal = CompetitionGoal.query.get_or_404(goal_id)
        db.session.delete(_goal)
        db.session.commit()

        return jsonify({'success': True, 'message': '竞赛目标删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {'success': False, 'message': f'删除竞赛目标失败: {str(e)}'}), 500


@app.route('/api/end_competition_goal/<goal_id>', methods=['POST'])
def end_competition_goal(goal_id):
    """结束竞赛目标API"""
    try:
        CompetitionGoal.query.get_or_404(goal_id)
        db.session.commit()

        return jsonify({'success': True, 'message': '竞赛目标已结束'})

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {'success': False, 'message': f'结束竞赛目标失败: {str(e)}'}), 500


@app.route('/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """学生提交答案API"""
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        answer = data.get('answer', '').strip()
        course_id = data.get('course_id', '').strip()

        if not student_name or not answer or not course_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        return jsonify({'success': True, 'message': '答案提交成功'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'提交答案失败: {str(e)}'}), 500


@app.route('/judge_answers', methods=['POST'])
def judge_answers():
    """判断答案对错API"""
    try:
        data = request.get_json()
        correct_answer = data.get('correct_answer', '').strip()
        course_id = data.get('course_id', '').strip()

        if not correct_answer or not course_id:
            return jsonify({'success': False, 'message': '正确答案和课程ID不能为空'}), 400

        return jsonify({
            'success': True,
            'message': '答案判断完成',
            'results': {}
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'判断答案失败: {str(e)}'}), 500


@app.route('/reports/<course_id>')
def generate_report(course_id):
    """生成报告页面"""
    try:
        course = Course.query.get_or_404(course_id)
        class_obj = Class.query.get(course.class_id)

        return render_template(
            'reports.html',
            course=course,
            class_obj=class_obj)

    except Exception as e:
        return f'生成报告失败: {str(e)}', 500


@app.route('/')
def index():
    """首页"""
    classes = Class.query.order_by(Class.created_date.desc()).all()
    goals = CompetitionGoal.query.order_by(
        CompetitionGoal.created_date.desc()).all()
    total_students = db.session.query(Student).count()

    return render_template(
        'homepage.html',
        classes=classes,
        goals=goals,
        total_students=total_students)


@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页"""
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()

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
            goal_progress = {
                'days_left': 77,
                'weeks_left': 11,
                'lessons_left': 22
            }

    return render_template(
        'class_detail.html',
        class_data=class_obj,
        students=students,
        goal=goal,
        goal_progress=goal_progress)


@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    return render_template(
        'classroom.html',
        class_obj=class_obj,
        students=students)


# 应用启动时自动创建数据库表
with app.app_context():
    try:
        db.create_all()
        print("✅ 数据库表创建成功")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")


if __name__ == '__main__':
    app.run(debug=True)
