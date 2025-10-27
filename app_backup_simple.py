#!/usr/bin/env python3
"""
全新的学生答案提交和评判系统
彻底重写，解决所有已知问题
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
    database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-secret-key')

db = SQLAlchemy(app)

# 简化的数据模型
class SimpleCourse(db.Model):
    __tablename__ = 'simple_courses'
    
    id = db.Column(db.String(36), primary_key=True)
    class_id = db.Column(db.String(36), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    current_round = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SimpleStudent(db.Model):
    __tablename__ = 'simple_students'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SimpleSubmission(db.Model):
    __tablename__ = 'simple_submissions'
    
    id = db.Column(db.String(36), primary_key=True)
    student_id = db.Column(db.String(36), nullable=False)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    answer_time = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SimpleRound(db.Model):
    __tablename__ = 'simple_rounds'
    
    id = db.Column(db.String(36), primary_key=True)
    course_id = db.Column(db.String(36), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    question_score = db.Column(db.Integer, default=1)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SimpleClass(db.Model):
    __tablename__ = 'simple_classes'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 初始化函数：在应用启动时创建数据库表
def init_database():
    """初始化数据库表"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 如果没有默认班级，创建一个
            default_class = SimpleClass.query.filter_by(name="默认班级").first()
            if not default_class:
                default_class = SimpleClass(
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

# 在应用启动时初始化数据库（在所有模型定义之后）
init_database()

# 首页路由
@app.route('/')
def index():
    """首页"""
    try:
        # 获取所有班级
        classes = SimpleClass.query.filter_by(is_active=True).all()
        
        # 计算总学生数量
        total_students = SimpleStudent.query.count()
        
        # 获取所有活跃课程
        active_courses = SimpleCourse.query.filter_by(is_active=True).all()
        total_courses = len(active_courses)
        
        return render_template('homepage.html',
                             classes=classes,
                             total_students=total_students,
                             total_courses=total_courses)
    except Exception as e:
        print(f"❌ 加载首页失败: {str(e)}")
        traceback.print_exc()
        # 返回简化的错误页面
        return f"<h1>启动成功！</h1><p>但加载主页时出错: {str(e)}</p><p>请检查数据库连接。</p>", 500

# 课堂路由 - 重定向 /class 到 /classroom
@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页 - 重定向到课堂页面"""
    try:
        # 查询班级是否存在
        class_obj = SimpleClass.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        
        # 重定向到课堂页面
        return redirect(f'/classroom/{class_id}')
    except Exception as e:
        print(f"❌ 加载班级详情失败: {str(e)}")
        return jsonify({'error': f'加载班级详情失败: {str(e)}'}), 500

@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    try:
        # 查询班级信息
        class_obj = SimpleClass.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'error': '班级不存在'}), 404
        
        # 获取学生列表
        students = SimpleStudent.query.filter_by(class_id=class_id).all()
        
        return render_template('classroom.html', class_id=class_id, class_obj=class_obj, students=students)
    except Exception as e:
        print(f"❌ 加载课堂页面失败: {str(e)}")
        return jsonify({'error': f'加载课堂页面失败: {str(e)}'}), 500

@app.route('/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """全新的学生答案提交逻辑"""
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        answer = data.get('answer', '').strip()
        answer_time = data.get('answer_time', 0.0)
        
        print(f"🎯 学生 {student_name} 提交答案: {answer}")
        
        # 获取班级ID
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        if not student_name or not answer or not class_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取或创建活跃课程
        course = SimpleCourse.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            # 创建新课程
            import uuid
            course_id = str(uuid.uuid4())
            course = SimpleCourse(
                id=course_id,
                class_id=class_id,
                name=f"课堂 {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                current_round=1
            )
            db.session.add(course)
            db.session.flush()
            print(f"✅ 创建新课程: {course.name}")
        
        # 获取或创建学生
        student = SimpleStudent.query.filter_by(name=student_name, class_id=class_id).first()
        if not student:
            import uuid
            student_id = str(uuid.uuid4())
            student = SimpleStudent(
                id=student_id,
                name=student_name,
                class_id=class_id
            )
            db.session.add(student)
            db.session.flush()
            print(f"✅ 创建新学生: {student.name}")
        
        # 检查是否已经提交过当前轮次的答案
        existing_submission = SimpleSubmission.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            round_number=course.current_round
        ).first()
        
        if existing_submission:
            return jsonify({'success': False, 'message': '您已经提交过答案了'}), 400
        
        # 创建提交记录
        import uuid
        submission_id = str(uuid.uuid4())
        submission = SimpleSubmission(
            id=submission_id,
            student_id=student.id,
            course_id=course.id,
            round_number=course.current_round,
            answer=answer,
            answer_time=float(answer_time)
        )
        db.session.add(submission)
        
        db.session.commit()
        
        print(f"✅ 学生 {student_name} 答案提交成功: 轮次 {course.current_round}")
        
        return jsonify({
            'success': True,
            'message': '答案提交成功',
            'course_id': course.id,
            'round_number': course.current_round,
            'submission_id': submission_id
        })
        
    except Exception as e:
        print(f"❌ 提交答案失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500

@app.route('/judge_answers', methods=['POST'])
def judge_answers():
    """全新的答案评判逻辑"""
    try:
        data = request.get_json()
        correct_answer = data.get('correct_answer', '').strip()
        question_score = data.get('question_score', 1)
        
        print(f"🎯 开始评判答案: {correct_answer}, 分数: {question_score}")
        
        # 获取班级ID
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        if not correct_answer or not class_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 获取活跃课程
        course = SimpleCourse.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        # 创建或更新轮次记录
        round_record = SimpleRound.query.filter_by(
            course_id=course.id,
            round_number=course.current_round
        ).first()
        
        if not round_record:
            import uuid
            round_id = str(uuid.uuid4())
            round_record = SimpleRound(
                id=round_id,
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
        
        # 获取所有学生
        students = SimpleStudent.query.filter_by(class_id=class_id).all()
        students_data = {}
        
        for student in students:
            # 获取学生当前轮次的提交
            submission = SimpleSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id,
                round_number=course.current_round
            ).first()
            
            # 计算学生历史总分数
            all_submissions = SimpleSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).all()
            
            total_score = 0
            total_rounds = len(all_submissions)
            correct_rounds = 0
            
            for sub in all_submissions:
                if sub.is_correct:
                    # 获取该轮次的分数
                    round_obj = SimpleRound.query.filter_by(
                        course_id=course.id,
                        round_number=sub.round_number
                    ).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
                    correct_rounds += 1
            
            # 处理当前轮次
            if submission:
                # 判断答案对错
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
                last_answer = ''
                last_answer_time = 0
            
            # 更新total_rounds（包括当前轮次）
            if submission:
                total_rounds += 1
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'last_answer_time': last_answer_time,
                'expression': expression,
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': last_answer
            }
            
            print(f"✅ 学生 {student.name}: 分数={total_score}, 轮次={total_rounds}, 正确={correct_rounds}")
        
        db.session.commit()
        
        print(f"✅ 评判完成，处理了 {len(students_data)} 个学生")
        
        return jsonify({
            'success': True,
            'message': '答案判断完成',
            'course_id': course.id,
            'students': students_data,
            'round_number': course.current_round
        })
        
    except Exception as e:
        print(f"❌ 评判答案失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'判断失败: {str(e)}'}), 500

@app.route('/next_round', methods=['POST'])
def next_round():
    """进入下一轮"""
    try:
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 获取活跃课程
        course = SimpleCourse.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        # 进入下一轮
        course.current_round += 1
        
        db.session.commit()
        
        print(f"✅ 进入下一轮: {course.current_round}")
        
        return jsonify({
            'success': True,
            'message': f'已进入第 {course.current_round} 轮',
            'round_number': course.current_round
        })
        
    except Exception as e:
        print(f"❌ 进入下一轮失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'进入下一轮失败: {str(e)}'}), 500

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
        
        # 创建班级
        class_id = str(uuid.uuid4())
        new_class = SimpleClass(
            id=class_id,
            name=name,
            is_active=True
        )
        db.session.add(new_class)
        db.session.commit()
        
        print(f"✅ 创建新班级: {name} (ID: {class_id})")
        
        return jsonify({
            'success': True,
            'class_id': class_id,
            'message': '班级创建成功'
        })
        
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
        class_obj = SimpleClass.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        # 将班级设置为非活跃
        class_obj.is_active = False
        db.session.commit()
        
        print(f"✅ 班级已结束: {class_obj.name}")
        
        return jsonify({
            'success': True,
            'message': '班级已成功结束'
        })
        
    except Exception as e:
        print(f"❌ 结束班级失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'结束班级失败: {str(e)}'}), 500

# 添加学生
@app.route('/add_student', methods=['POST'])
def add_student():
    """添加学生到课堂"""
    try:
        data = request.get_json()
        student_name = data.get('name', '').strip()
        
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        if not student_name or not class_id:
            return jsonify({'error': '参数不完整'}), 400
        
        # 检查学生是否已存在
        existing_student = SimpleStudent.query.filter_by(name=student_name, class_id=class_id).first()
        if existing_student:
            return jsonify({'error': '该学生已经存在'}), 400
        
        # 创建新学生
        student_id = str(uuid.uuid4())
        student = SimpleStudent(
            id=student_id,
            name=student_name,
            class_id=class_id
        )
        db.session.add(student)
        db.session.commit()
        
        print(f"✅ 添加学生: {student_name}")
        
        return jsonify({
            'success': True,
            'message': '学生添加成功'
        })
        
    except Exception as e:
        print(f"❌ 添加学生失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': f'添加学生失败: {str(e)}'}), 500

# 开始课堂
@app.route('/api/start_class', methods=['POST'])
def start_class():
    """开始课堂"""
    try:
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            data = request.get_json()
            class_id = data.get('class_id')
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 创建或获取活跃课程
        course = SimpleCourse.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            course_id = str(uuid.uuid4())
            course = SimpleCourse(
                id=course_id,
                class_id=class_id,
                name=f"课堂 {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                current_round=1,
                is_active=True
            )
            db.session.add(course)
            db.session.commit()
            print(f"✅ 创建新课程: {course.name}")
        
        return jsonify({
            'success': True,
            'course_id': course.id,
            'message': '课堂已开始'
        })
        
    except Exception as e:
        print(f"❌ 开始课堂失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'开始课堂失败: {str(e)}'}), 500

@app.route('/get_classroom_data')
def get_classroom_data():
    """获取课堂数据"""
    try:
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 获取活跃课程
        course = SimpleCourse.query.filter_by(class_id=class_id, is_active=True).first()
        if not course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        # 获取所有学生
        students = SimpleStudent.query.filter_by(class_id=class_id).all()
        students_data = {}
        
        for student in students:
            # 计算学生历史总分数
            all_submissions = SimpleSubmission.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).all()
            
            total_score = 0
            total_rounds = len(all_submissions)
            correct_rounds = 0
            
            for sub in all_submissions:
                if sub.is_correct:
                    # 获取该轮次的分数
                    round_obj = SimpleRound.query.filter_by(
                        course_id=course.id,
                        round_number=sub.round_number
                    ).first()
                    if round_obj:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1
                    correct_rounds += 1
            
            # 获取最新答案
            last_answer = ''
            last_answer_time = 0
            if all_submissions:
                latest_submission = max(all_submissions, key=lambda x: x.created_at)
                last_answer = latest_submission.answer
                last_answer_time = latest_submission.answer_time
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'last_answer_time': last_answer_time,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': last_answer
            }
        
        return jsonify({
            'success': True,
            'students': students_data,
            'current_round': course.current_round
        })
        
    except Exception as e:
        print(f"❌ 获取课堂数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500

if __name__ == "__main__":
    # 启动服务器
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动全新服务器，端口: {port}")
    print(f"📝 数据库URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    app.run(host='0.0.0.0', port=port, debug=False)
