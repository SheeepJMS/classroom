from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace(
        'postgres://', 'postgresql+pg8000://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace(
        'postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 导入并初始化数据库
from models import db, Class, Student, Course, CompetitionGoal, CourseRound, StudentSubmission, init_db
init_db(app)


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
        # 优先从请求体获取班级ID
        data = request.get_json() or {}
        class_id = data.get('class_id')
        
        # 如果请求体中没有，则从请求头获取
        if not class_id:
            class_id = request.headers.get('X-Class-ID')
        
        # 如果还没有，尝试从referer URL中提取
        if not class_id:
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]
        
        print(f"DEBUG: start_course called with class_id: {class_id}")
        print(f"DEBUG: request data: {data}")
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400

        # 检查班级是否存在
        class_obj = Class.query.get(class_id)
        if not class_obj:
            print(f"DEBUG: Class not found for class_id: {class_id}")
            return jsonify({'success': False, 'message': '班级不存在'}), 404

        print(f"DEBUG: Found class: {class_obj.name}")

        # 停用该班级的所有活跃课程
        Course.query.filter_by(class_id=class_id, is_active=True).update({'is_active': False})

        # 创建新课程
        course_name = data.get('course_name') or f"课堂 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        course_id = str(uuid.uuid4())
        print(f"DEBUG: Creating course with id: {course_id}, name: {course_name}")
        
        new_course = Course(
            id=course_id,
            name=course_name,
            class_id=class_id,
            is_active=True,
            created_date=datetime.now())
        db.session.add(new_course)
        db.session.commit()

        print(f"DEBUG: Course created successfully with id: {new_course.id}")

        return jsonify({
            'success': True,
            'message': '课程开始成功',
            'course_id': new_course.id
        })

    except Exception as e:
        print(f"DEBUG: Exception in start_course: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'开始课程失败: {str(e)}'}), 500


@app.route('/api/start_class', methods=['POST'])
def start_class():
    """开始答题API"""
    try:
        # 从请求头获取班级ID
        class_id = request.headers.get('X-Class-ID')
        
        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        # 检查是否有活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not current_course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400
        
        # 这里可以添加更多逻辑来开始答题状态
        # 比如设置round_active=True等
        
        return jsonify({
            'success': True,
            'message': '答题开始成功',
            'course_id': current_course.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'开始答题失败: {str(e)}'}), 500


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


@app.route('/api/graduate_student', methods=['POST'])
def graduate_student():
    """学生学业结束API"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', '').strip()

        if not student_id:
            return jsonify({'success': False, 'message': '学生ID不能为空'}), 400

        # 使用原生SQL查询避免status字段问题
        try:
            result = db.engine.execute(
                "SELECT id, name, class_id, created_date FROM students WHERE id = %s",
                (student_id,)
            )
            student_data = result.fetchone()
            if not student_data:
                return jsonify({'success': False, 'message': '学生不存在'}), 404
            
            # 创建临时学生对象
            class TempStudent:
                def __init__(self, id, name, class_id, created_date):
                    self.id = id
                    self.name = name
                    self.class_id = class_id
                    self.created_date = created_date
            
            student = TempStudent(*student_data)
        except Exception as e:
            return jsonify({'success': False, 'message': f'查询学生失败: {str(e)}'}), 500
        
        # 临时注释掉状态更新，等数据库迁移后再启用
        # student.status = 'graduated'
        # student.graduated_date = datetime.now()
        
        # 暂时直接删除学生记录（临时方案）
        db.session.delete(student)
        db.session.commit()

        return jsonify({'success': True, 'message': '学生学业结束成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'学生学业结束失败: {str(e)}'}), 500


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
        answer_time = data.get('answer_time', 0.0)  # 获取答题时间
        
        # 从请求头获取班级ID
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            # 如果没有在header中，尝试从referer URL中提取
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]

        if not student_name or not answer:
            return jsonify({'success': False, 'message': '学生姓名和答案不能为空'}), 400

        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400

        # 获取当前活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not current_course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400

        # 使用原生SQL查询避免status字段问题
        try:
            result = db.engine.execute(
                "SELECT id, name, class_id, created_date FROM students WHERE name = %s AND class_id = %s",
                (student_name, class_id)
            )
            student_data = result.fetchone()
            if not student_data:
                return jsonify({'success': False, 'message': '学生不存在'}), 404
            
            # 创建临时学生对象
            class TempStudent:
                def __init__(self, id, name, class_id, created_date):
                    self.id = id
                    self.name = name
                    self.class_id = class_id
                    self.created_date = created_date
            
            student = TempStudent(*student_data)
        except Exception as e:
            return jsonify({'success': False, 'message': f'查询学生失败: {str(e)}'}), 500

        # 获取或创建当前轮次
        current_round = CourseRound.query.filter_by(
            course_id=current_course.id,
            round_number=1  # 暂时硬编码为第1轮
        ).first()
        
        if not current_round:
            # 创建新的轮次记录（暂时使用默认值）
            current_round = CourseRound(
                course_id=current_course.id,
                round_number=1,
                question_text="数学题目",  # 暂时使用默认值
                correct_answer="1",  # 暂时使用默认值
                question_score=1
            )
            db.session.add(current_round)
            db.session.flush()  # 获取ID

        # 检查学生是否已经提交过答案
        existing_submission = StudentSubmission.query.filter_by(
            student_id=student.id,
            round_id=current_round.id
        ).first()
        
        if existing_submission:
            return jsonify({'success': False, 'message': '您已经提交过答案了'}), 400

        # 计算答题时间（使用前端传递的时间）
        answer_time_seconds = float(answer_time)
        
        # 保存学生提交记录
        submission = StudentSubmission(
            student_id=student.id,
            round_id=current_round.id,
            answer=answer,
            is_correct=False,  # 暂时设为False，等BINGO时判断
            answer_time=answer_time_seconds
        )
        db.session.add(submission)
        db.session.commit()

        return jsonify({
            'success': True, 
            'message': '答案提交成功',
            'course_id': current_course.id,
            'submission_id': submission.id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'提交答案失败: {str(e)}'}), 500


@app.route('/judge_answers', methods=['POST'])
def judge_answers():
    """判断答案对错API"""
    try:
        data = request.get_json()
        correct_answer = data.get('correct_answer', '').strip()
        question_score = data.get('question_score', 1)
        
        # 从请求头获取班级ID
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            # 如果没有在header中，尝试从referer URL中提取
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]

        if not correct_answer:
            return jsonify({'success': False, 'message': '正确答案不能为空'}), 400

        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400

        # 获取当前活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not current_course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400

        # 创建或更新当前轮次
        current_round = CourseRound.query.filter_by(
            course_id=current_course.id,
            round_number=1  # 暂时硬编码为第1轮
        ).first()
        
        if not current_round:
            # 创建新的轮次
            current_round = CourseRound(
                id=str(uuid.uuid4()),
                course_id=current_course.id,
                round_number=1,
                correct_answer=correct_answer,
                question_score=question_score
            )
            db.session.add(current_round)
        else:
            # 更新现有轮次
            current_round.correct_answer = correct_answer
            current_round.question_score = question_score
        
        db.session.commit()

        # 获取班级学生数据并判断答案（临时移除status过滤）
        students = get_students_by_class_id(class_id)
        students_data = {}
        
        for student in students:
            # 获取学生的提交记录
            submission = StudentSubmission.query.filter_by(
                student_id=student.id,
                round_id=current_round.id if current_round else None
            ).first()
            
            # 根据提交情况确定学生状态
            if submission:
                # 学生已提交，判断答案对错
                is_correct = submission.answer.strip().lower() == correct_answer.strip().lower()
                submission.is_correct = is_correct
                
                if is_correct:
                    expression = 'smile'
                    score = question_score
                    correct_rounds = 1
                else:
                    expression = 'angry'
                    score = 0
                    correct_rounds = 0
                    
                last_answer = submission.answer
                last_answer_time = submission.answer_time
            else:
                # 学生未提交
                expression = 'embarrassed'
                score = 0
                correct_rounds = 0
                last_answer = ''
                last_answer_time = 0
            
            students_data[student.name] = {
                'name': student.name,
                'score': score,
                'total_rounds': 1,
                'correct_rounds': correct_rounds,
                'last_answer_time': last_answer_time,
                'expression': expression,
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': last_answer
            }
        
        # 保存提交记录的更新
        if current_round:
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '答案判断完成',
            'course_id': current_course.id,
            'students': students_data
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'判断答案失败: {str(e)}'}), 500


@app.route('/reports/<course_id>')
def generate_report(course_id):
    """生成报告页面"""
    try:
        course = Course.query.get_or_404(course_id)
        class_obj = Class.query.get(course.class_id)
        
        # 获取班级活跃学生数据（临时移除status过滤）
        students = get_students_by_class_id(course.class_id)
        students_data = {}
        
        for student in students:
            # 计算学生的统计数据
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            
            # 获取该学生在当前课程中的所有提交记录
            submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == course_id
            ).all()
            
            for submission in submissions:
                total_rounds += 1
                if submission.is_correct:
                    # 从CourseRound获取题目分数
                    round_obj = CourseRound.query.get(submission.round_id)
                    if round_obj and round_obj.question_score:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1  # 默认分数
                    correct_rounds += 1
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'avatar_color': '#4ecdc4'
            }

        return render_template(
            'reports.html',
            course=course,
            class_obj=class_obj,
            students=students_data)

    except Exception as e:
        return f'生成报告失败: {str(e)}', 500


def get_students_by_class_id(class_id):
    """获取指定班级的学生列表（避免status字段问题）"""
    try:
        result = db.engine.execute(
            "SELECT id, name, class_id, created_date FROM students WHERE class_id = %s",
            (class_id,)
        )
        students_data = result.fetchall()
        
        # 创建临时学生对象列表
        class TempStudent:
            def __init__(self, id, name, class_id, created_date):
                self.id = id
                self.name = name
                self.class_id = class_id
                self.created_date = created_date
        
        students = [TempStudent(*row) for row in students_data]
        return students
    except Exception as e:
        print(f"查询学生失败: {e}")
        return []


@app.route('/')
def index():
    """首页"""
    classes = Class.query.order_by(Class.created_date.desc()).all()
    goals = CompetitionGoal.query.order_by(
        CompetitionGoal.created_date.desc()).all()
    # 临时使用原生SQL查询避免status字段问题
    try:
        result = db.engine.execute("SELECT COUNT(*) FROM students")
        total_students = result.fetchone()[0]
    except Exception as e:
        print(f"查询学生总数失败: {e}")
        total_students = 0

    return render_template(
        'homepage.html',
        classes=classes,
        goals=goals,
        total_students=total_students)


@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页"""
    class_obj = Class.query.get_or_404(class_id)
    # 分别获取活跃学生和历史学员（临时移除status过滤）
    active_students = get_students_by_class_id(class_id)
    graduated_students = []  # 临时设为空

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
        students=active_students,  # 活跃学生
        graduated_students=graduated_students,  # 历史学员
        goal=goal,
        goal_progress=goal_progress)


@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    class_obj = Class.query.get_or_404(class_id)
    # 只显示活跃学生（临时移除status过滤）
    students = get_students_by_class_id(class_id)
    return render_template(
        'classroom.html',
        class_obj=class_obj,
        students=students)

@app.route('/get_classroom_data')
def get_classroom_data():
    """获取课堂数据API"""
    try:
        # 从请求头获取班级ID
        class_id = request.headers.get('X-Class-ID')
        
        # 添加调试日志
        print(f"DEBUG: get_classroom_data called")
        print(f"DEBUG: X-Class-ID header: {class_id}")
        print(f"DEBUG: All headers: {dict(request.headers)}")
        
        if not class_id:
            print("DEBUG: No class_id found in headers")
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400
        
        print(f"DEBUG: Looking for students with class_id: {class_id}")
        
        # 获取指定班级的活跃学生（临时移除status过滤）
        students = get_students_by_class_id(class_id)
        print(f"DEBUG: Found {len(students)} active students")
        
        # 构建学生数据字典
        students_data = {}
        for student in students:
            students_data[student.name] = {
                'name': student.name,
                'score': 0,
                'total_rounds': 0,
                'correct_rounds': 0,
                'last_answer_time': 0,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': ''
            }
        
        print(f"DEBUG: Returning data for {len(students_data)} students")
        
        # 检查是否有活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        round_active = current_course is not None
        
        return jsonify({
            'success': True,
            'current_round': 1,
            'students': students_data,
            'round_active': round_active
        })
    except Exception as e:
        print(f"DEBUG: Exception in get_classroom_data: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/next_round', methods=['POST'])
def next_round():
    """下一轮API"""
    try:
        # 从请求头获取班级ID
        class_id = request.headers.get('X-Class-ID')
        if not class_id:
            # 如果没有在header中，尝试从referer URL中提取
            referer = request.headers.get('Referer', '')
            if '/classroom/' in referer:
                class_id = referer.split('/classroom/')[-1]

        if not class_id:
            return jsonify({'success': False, 'message': '班级ID不能为空'}), 400

        # 获取当前活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        if not current_course:
            return jsonify({'success': False, 'message': '没有活跃的课程'}), 400

        # 获取当前轮次号
        current_round = CourseRound.query.filter_by(
            course_id=current_course.id
        ).order_by(CourseRound.round_number.desc()).first()
        
        next_round_number = 1
        if current_round:
            next_round_number = current_round.round_number + 1

        # 创建新的轮次记录
        new_round = CourseRound(
            course_id=current_course.id,
            round_number=next_round_number,
            question_text="数学题目",  # 暂时使用默认值
            correct_answer="1",  # 暂时使用默认值
            question_score=1
        )
        db.session.add(new_round)
        db.session.commit()

        # 获取班级学生数据并重置状态（临时移除status过滤）
        students = get_students_by_class_id(class_id)
        students_data = {}
        
        for student in students:
            # 获取学生的历史提交记录来计算总分数
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            
            submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == current_course.id
            ).all()
            
            for submission in submissions:
                total_rounds += 1
                if submission.is_correct:
                    total_score += submission.round_ref.question_score
                    correct_rounds += 1
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,  # 保留历史分数
                'total_rounds': total_rounds,  # 保留历史轮次
                'correct_rounds': correct_rounds,  # 保留历史正确次数
                'last_answer_time': 0,  # 重置当前轮次的答题时间
                'expression': 'neutral',  # 重置为中性表情
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': ''  # 重置当前轮次的答案
            }

        return jsonify({
            'success': True,
            'message': '下一轮开始',
            'round': next_round_number,
            'students': students_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/reset_classroom', methods=['POST'])
def reset_classroom():
    """重置课堂API"""
    try:
        # 简单的重置逻辑
        return jsonify({
            'success': True,
            'message': '课堂已重置'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/ceremony')
def ceremony():
    """颁奖典礼页面"""
    try:
        # 获取当前活跃的课程
        current_course = Course.query.filter_by(is_active=True).first()
        if not current_course:
            return redirect(url_for('index'))
        
        # 获取班级活跃学生数据（临时移除status过滤）
        students = get_students_by_class_id(current_course.class_id)
        students_data = {}
        
        for student in students:
            # 计算学生的总分数 - 从StudentSubmission表获取真实数据
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            
            # 获取该学生在当前课程中的所有提交记录
            submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == current_course.id
            ).all()
            
            for submission in submissions:
                total_rounds += 1
                if submission.is_correct:
                    # 从CourseRound获取题目分数
                    round_obj = CourseRound.query.get(submission.round_id)
                    if round_obj and round_obj.question_score:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1  # 默认分数
                    correct_rounds += 1
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'avatar_color': '#4ecdc4'
            }
        
        # 构建课堂数据
        classroom_data = {
            'id': current_course.id,
            'name': current_course.name,
            'students': students_data
        }
        
        return render_template('ceremony.html', classroom_data=classroom_data)
        
    except Exception as e:
        print(f"Error in ceremony route: {str(e)}")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
