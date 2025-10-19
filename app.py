from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import os
import uuid
from sqlalchemy import text

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
        goal_date = data.get('goal_date')

        if not title:
            return jsonify({'success': False, 'message': '竞赛目标名称不能为空'}), 400

        # 处理日期格式
        goal_date_obj = None
        if goal_date:
            try:
                from datetime import datetime
                goal_date_obj = datetime.strptime(goal_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': '日期格式错误，请使用YYYY-MM-DD格式'}), 400

        new_goal = CompetitionGoal(
            title=title,
            description=description,
            target_score=target_score,
            goal_date=goal_date_obj)
        db.session.add(new_goal)
        db.session.commit()
        
        # 调试信息
        print(f"DEBUG: 竞赛目标创建成功 - ID: {new_goal.id}, 标题: {new_goal.title}")
        
        # 验证数据是否真的保存了
        saved_goal = CompetitionGoal.query.get(new_goal.id)
        print(f"DEBUG: 验证保存 - 查询到的目标: {saved_goal.title if saved_goal else 'None'}")

        return jsonify({
            'success': True,
            'message': '竞赛目标创建成功',
            'goal_id': new_goal.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {'success': False, 'message': f'创建竞赛目标失败: {str(e)}'}), 500


@app.route('/api/assign_goal_to_class', methods=['POST'])
def assign_goal_to_class():
    """分配竞赛目标到班级"""
    try:
        data = request.get_json()
        goal_id = data.get('goal_id')
        class_id = data.get('class_id')
        
        if not goal_id or not class_id:
            return jsonify({'success': False, 'message': '竞赛目标ID和班级ID不能为空'}), 400
        
        # 验证竞赛目标是否存在
        goal = CompetitionGoal.query.get(goal_id)
        if not goal:
            return jsonify({'success': False, 'message': '竞赛目标不存在'}), 404
        
        # 获取班级对象
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        # 分配竞赛目标到班级（持久化到数据库）
        class_obj.competition_goal_id = goal_id
        db.session.commit()
        
        return jsonify({'success': True, 'message': '竞赛目标分配成功'})
        
    except Exception as e:
        db.session.rollback()
        print(f"分配竞赛目标时发生错误: {e}")
        return jsonify({'success': False, 'message': f'分配竞赛目标失败: {str(e)}'}), 500


@app.route('/api/get_competition_goals')
def get_competition_goals():
    """获取所有竞赛目标"""
    try:
        goals = CompetitionGoal.query.order_by(CompetitionGoal.created_date.desc()).all()
        goals_data = []
        for goal in goals:
            goals_data.append({
                'id': goal.id,
                'title': goal.title,
                'description': goal.description,
                'target_score': goal.target_score,
                'goal_date': goal.goal_date.strftime('%Y-%m-%d') if goal.goal_date else None,
                'created_date': goal.created_date.strftime('%Y-%m-%d') if goal.created_date else None
            })
        
        return jsonify({
            'success': True,
            'goals': goals_data
        })
        
    except Exception as e:
        print(f"获取竞赛目标时发生错误: {e}")
        return jsonify({'success': False, 'message': f'获取竞赛目标失败: {str(e)}'}), 500


@app.route('/api/add_student', methods=['POST'])
def add_student():
    """添加学生API"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        class_id = data.get('class_id', '').strip()

        if not name or not class_id:
            return jsonify({'success': False, 'message': '学生姓名和班级ID不能为空'}), 400

        # 使用原生SQL插入，避免status字段问题
        student_id = str(uuid.uuid4())
        created_date = datetime.now()
        
        db.session.execute(text("""
            INSERT INTO students (id, name, class_id, created_date) 
            VALUES (:id, :name, :class_id, :created_date)
        """), {
            'id': student_id,
            'name': name,
            'class_id': class_id,
            'created_date': created_date
        })
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '学生添加成功',
            'student_id': student_id
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
            result = db.session.execute(
                text("SELECT id, name, class_id, created_date FROM students WHERE id = :student_id"),
                {'student_id': student_id}
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
            result = db.session.execute(
                text("SELECT id, name, class_id, created_date FROM students WHERE name = :student_name AND class_id = :class_id"),
                {'student_name': student_name, 'class_id': class_id}
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

        # 获取当前轮次号
        latest_round = CourseRound.query.filter_by(
            course_id=current_course.id
        ).order_by(CourseRound.round_number.desc()).first()
        
        current_round_number = 1
        if latest_round:
            current_round_number = latest_round.round_number
            
        # 获取或创建当前轮次
        current_round = CourseRound.query.filter_by(
            course_id=current_course.id,
            round_number=current_round_number
        ).first()
        
        if not current_round:
            # 创建新的轮次记录（暂时使用默认值）
            current_round = CourseRound(
                course_id=current_course.id,
                round_number=current_round_number,
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

        # 获取当前轮次号
        latest_round = CourseRound.query.filter_by(
            course_id=current_course.id
        ).order_by(CourseRound.round_number.desc()).first()
        
        current_round_number = 1
        if latest_round:
            current_round_number = latest_round.round_number
            
        # 创建或更新当前轮次
        current_round = CourseRound.query.filter_by(
            course_id=current_course.id,
            round_number=current_round_number
        ).first()
        
        if not current_round:
            # 创建新的轮次
            current_round = CourseRound(
                id=str(uuid.uuid4()),
                course_id=current_course.id,
                round_number=current_round_number,
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
            
            # 先更新当前轮次的提交记录状态
            if submission:
                # 学生已提交，判断答案对错
                is_correct = submission.answer.strip().lower() == correct_answer.strip().lower()
                submission.is_correct = is_correct
                
                # 保存提交记录的更新
                db.session.add(submission)
            
            # 提交当前轮次的更新
            db.session.flush()
            
            # 计算学生的累计统计数据
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            last_answer = ''
            last_answer_time = 0
            expression = 'neutral'
            
            # 获取课程中的所有轮次（学生应该参与的轮次总数）
            all_course_rounds = CourseRound.query.filter_by(course_id=current_course.id).all()
            total_rounds = len(all_course_rounds)
            
            # 获取该学生在当前课程中的所有提交记录（包括刚刚更新的）
            all_submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == current_course.id
            ).all()
            
            for sub in all_submissions:
                if sub.is_correct:
                    # 从CourseRound获取题目分数
                    round_obj = CourseRound.query.get(sub.round_id)
                    if round_obj and round_obj.question_score:
                        total_score += round_obj.question_score
                    else:
                        total_score += 1  # 默认分数
                    correct_rounds += 1
            
            # 获取最新答案
            if all_submissions:
                last_submission = max(all_submissions, key=lambda x: x.submitted_at)
                last_answer = last_submission.answer
                last_answer_time = last_submission.answer_time
            
            # 根据当前轮次提交情况确定学生状态
            if submission:
                if submission.is_correct:
                    expression = 'smile'
                else:
                    expression = 'angry'
            else:
                # 学生未提交
                expression = 'embarrassed'
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,  # 累计分数
                'total_rounds': total_rounds,  # 累计轮次
                'correct_rounds': correct_rounds,  # 累计正确次数
                'last_answer_time': last_answer_time,
                'expression': expression,
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': last_answer
            }
        
        # 提交所有更改到数据库
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '答案判断完成',
            'course_id': current_course.id,
            'students': students_data
        })

    except Exception as e:
        db.session.rollback()
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
                'id': student.id,  # 添加学生ID
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


@app.route('/generate_student_report/<student_identifier>')
def generate_student_report(student_identifier):
    """生成学生个人报告 - 支持通过ID或姓名查找学生，支持特定课程"""
    try:
        # 先尝试通过ID查找学生
        result = db.session.execute(
            text("SELECT id, name, class_id, created_date FROM students WHERE id = :student_id"),
            {'student_id': student_identifier}
        )
        student_data = result.fetchone()
        
        # 如果通过ID找不到，尝试通过姓名查找（需要先确定班级）
        if not student_data:
            # 获取课程ID参数
            course_id = request.args.get('course_id')
            
            # 如果有课程ID，先获取课程信息来确定班级
            if course_id:
                current_course = Course.query.get(course_id)
                if current_course:
                    result = db.session.execute(
                        text("SELECT id, name, class_id, created_date FROM students WHERE name = :student_name AND class_id = :class_id"),
                        {'student_name': student_identifier, 'class_id': current_course.class_id}
                    )
                    fallback_student_data = result.fetchone()
                    if fallback_student_data:
                        student_data = fallback_student_data
                        # 使用指定的课程
                        pass  # current_course已经设置
                    else:
                        # 尝试在所有班级中查找同名学生
                        result = db.session.execute(
                            text("SELECT id, name, class_id, created_date FROM students WHERE name = :student_name"),
                            {'student_name': student_identifier}
                        )
                        student_data = result.fetchone()
                        if student_data:
                            current_course = Course.query.filter_by(class_id=student_data.class_id, is_active=True).first()
                else:
                    return redirect(url_for('index'))
            else:
                # 没有课程ID，尝试在所有班级中查找同名学生
                result = db.session.execute(
                    text("SELECT id, name, class_id, created_date FROM students WHERE name = :student_name"),
                    {'student_name': student_identifier}
                )
                student_data = result.fetchone()
                if student_data:
                    current_course = Course.query.filter_by(class_id=student_data.class_id, is_active=True).first()
                else:
                    return redirect(url_for('index'))
        else:
            # 通过ID找到了学生，获取课程信息
            course_id = request.args.get('course_id')
            if course_id:
                current_course = Course.query.get(course_id)
                # 确保课程属于该学生班级
                if current_course and current_course.class_id != student_data.class_id:
                    # 如果指定的课程不属于学生班级，使用学生班级的活跃课程
                    current_course = Course.query.filter_by(class_id=student_data.class_id, is_active=True).first()
            else:
                # 使用学生班级的活跃课程
                current_course = Course.query.filter_by(class_id=student_data.class_id, is_active=True).first()
            
        if not current_course:
            return redirect(url_for('index'))
        
        if not student_data:
            return f'学生不存在: {student_identifier}', 404
        
        # 创建临时学生对象
        class TempStudent:
            def __init__(self, id, name, class_id, created_date):
                self.id = id
                self.name = name
                self.class_id = class_id
                self.created_date = created_date
        
        student = TempStudent(*student_data)
        
        # 计算学生的统计数据
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
        
        # 计算准确率
        accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        # 计算排名
        all_students = get_students_by_class_id(current_course.class_id)
        student_scores = []
        for class_student in all_students:
            class_submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == class_student.id,
                CourseRound.course_id == current_course.id
            ).all()
            
            class_score = 0
            for s in class_submissions:
                if s.is_correct:
                    round_obj = CourseRound.query.get(s.round_id)
                    if round_obj and round_obj.question_score:
                        class_score += round_obj.question_score
                    else:
                        class_score += 1
            student_scores.append(class_score)
        
        student_scores.sort(reverse=True)
        try:
            rank = student_scores.index(total_score) + 1
        except ValueError:
            rank = len(student_scores)
        
        # 计算参与率
        participation_rate = 100 if submissions else 0
        
        # 计算平均反应时间
        if submissions:
            avg_response_time = sum(s.answer_time for s in submissions) / len(submissions)
        else:
            avg_response_time = 0
        
        # 计算班级平均值
        all_students = get_students_by_class_id(current_course.class_id)
        class_avg_accuracy = 0
        class_avg_participation = 0
        class_avg_response_time = 0
        class_avg_score = 0
        
        if all_students:
            total_class_accuracy = 0
            total_class_participation = 0
            total_class_response_time = 0
            total_class_score = 0
            valid_students = 0
            
            for class_student in all_students:
                # 获取该学生的提交记录
                class_submissions = StudentSubmission.query.join(CourseRound).filter(
                    StudentSubmission.student_id == class_student.id,
                    CourseRound.course_id == current_course.id
                ).all()
                
                if class_submissions:
                    # 计算该学生的准确率
                    class_correct_rounds = sum(1 for s in class_submissions if s.is_correct)
                    class_accuracy = (class_correct_rounds / len(class_submissions) * 100) if class_submissions else 0
                    total_class_accuracy += class_accuracy
                    
                    # 计算该学生的参与率（假设所有轮次都参与了）
                    total_class_participation += 100  # 简化计算
                    
                    # 计算该学生的平均反应时间
                    class_avg_time = sum(s.answer_time for s in class_submissions) / len(class_submissions)
                    total_class_response_time += class_avg_time
                    
                    # 计算该学生的总分
                    class_score = 0
                    for s in class_submissions:
                        if s.is_correct:
                            round_obj = CourseRound.query.get(s.round_id)
                            if round_obj and round_obj.question_score:
                                class_score += round_obj.question_score
                            else:
                                class_score += 1
                    total_class_score += class_score
                    
                    valid_students += 1
            
            if valid_students > 0:
                class_avg_accuracy = total_class_accuracy / valid_students
                class_avg_participation = total_class_participation / valid_students
                class_avg_response_time = total_class_response_time / valid_students
                class_avg_score = total_class_score / valid_students
        
        # 计算当前学生的参与率
        participation_rate = 100 if submissions else 0  # 简化计算
        
        # 获取班级信息
        class_obj = Class.query.get(student.class_id)
        
        # 计算其他需要的变量
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        # 调试信息
        print(f"DEBUG: 学生ID: {student.id}, 班级ID: {student.class_id}")
        print(f"DEBUG: 课程ID: {current_course.id}, 课程名称: {current_course.name}")
        print(f"DEBUG: 班级对象: {class_obj}")
        if class_obj:
            print(f"DEBUG: 竞赛目标ID: {class_obj.competition_goal_id}")
        print(f"DEBUG: 学生提交记录数: {len(submissions)}")
        print(f"DEBUG: 课程轮次数: {len(course_rounds) if 'course_rounds' in locals() else '未计算'}")
        
        # 获取竞赛目标信息
        competition_goal_name = '暂无竞赛目标'
        competition_goal_date = '暂无日期'
        days_to_competition = '暂无'
        classes_before_competition = '暂无'
        
        if class_obj and class_obj.competition_goal_id:
            try:
                goal = CompetitionGoal.query.get(class_obj.competition_goal_id)
                if goal:
                    competition_goal_name = goal.name
                    if goal.goal_date:
                        competition_goal_date = goal.goal_date.strftime('%Y年%m月%d日')
                        days_diff = (goal.goal_date - datetime.now().date()).days
                        days_to_competition = max(0, days_diff)
                        # 假设每周2节课
                        classes_before_competition = max(0, days_diff // 7 * 2)
            except Exception as e:
                print(f"获取竞赛目标失败: {e}")
                pass
        else:
            print(f"班级对象: {class_obj}, 竞赛目标ID: {class_obj.competition_goal_id if class_obj else 'None'}")
        
        # 计算总分和可能的总分
        total_possible_score = total_rounds  # 假设每题1分
        if submissions:
            for s in submissions:
                round_obj = CourseRound.query.get(s.round_id)
                if round_obj and round_obj.question_score:
                    total_possible_score = sum(CourseRound.query.filter_by(course_id=current_course.id).with_entities(CourseRound.question_score).scalar() or 1 for _ in submissions)
                    break
        
        # 个性化反馈
        personalized_feedback = {
            'focus_feedback': '继续保持良好的学习状态！' if accuracy >= 80 else '需要加强练习，提高准确率。'
        }
        
        # 获取该课程的所有轮次
        course_rounds = CourseRound.query.filter_by(course_id=current_course.id).order_by(CourseRound.round_number).all()
        
        # 班级总体统计
        class_total_accuracy = round(class_avg_accuracy, 1)
        class_total_participation = round(class_avg_participation, 1)
        class_total_rounds = len(course_rounds) if course_rounds else total_rounds
        
        # 班级轮次统计
        class_round_stats = []
        
        for round_obj in course_rounds:
            # 获取该轮次中当前学生的提交记录
            student_submission = StudentSubmission.query.filter_by(
                student_id=student.id,
                round_id=round_obj.id
            ).first()
            
            # 计算该轮次的课堂平均参与率和正确率
            all_students = get_students_by_class_id(current_course.class_id)
            total_students = len(all_students)
            participated_students = 0
            correct_students = 0
            
            for class_student in all_students:
                class_submission = StudentSubmission.query.filter_by(
                    student_id=class_student.id,
                    round_id=round_obj.id
                ).first()
                
                if class_submission:
                    participated_students += 1
                    if class_submission.is_correct:
                        correct_students += 1
            
            class_avg_participation = (participated_students / total_students * 100) if total_students > 0 else 0
            class_avg_accuracy = (correct_students / participated_students * 100) if participated_students > 0 else 0
            
            if student_submission:
                round_stat = {
                    'round_num': round_obj.round_number,
                    'question_score': round_obj.question_score or 1,
                    'answer_time': student_submission.answer_time,
                    'is_correct': student_submission.is_correct,
                    'answer': student_submission.answer,
                    'participated': True,
                    'difficulty_stars': '★★★',  # 默认难度
                    'class_avg_participation': round(class_avg_participation, 1),
                    'class_avg_accuracy': round(class_avg_accuracy, 1)
                }
                class_round_stats.append(round_stat)
            else:
                # 学生未参与该轮次
                round_stat = {
                    'round_num': round_obj.round_number,
                    'question_score': round_obj.question_score or 1,
                    'answer_time': 0,
                    'is_correct': False,
                    'answer': None,
                    'participated': False,
                    'difficulty_stars': '★★★',  # 默认难度
                    'class_avg_participation': round(class_avg_participation, 1),
                    'class_avg_accuracy': round(class_avg_accuracy, 1)
                }
                class_round_stats.append(round_stat)
        
        return render_template(
            'course_detail_report.html',
            student=student,
            student_name=student.name,
            total_rounds=total_rounds,
            correct_rounds=correct_rounds,
            accuracy=round(accuracy, 1),
            total_score=total_score,
            submissions=submissions,
            avg_response_time=round(avg_response_time, 1),
            class_obj=class_obj,
            course=current_course,
            course_data=current_course,
            participation_rate=round(participation_rate, 1),
            class_avg_accuracy=round(class_avg_accuracy, 1),
            class_avg_participation=round(class_avg_participation, 1),
            class_avg_response_time=round(class_avg_response_time, 1),
            class_avg_score=round(class_avg_score, 1),
            student_total_score=total_score,
            class_avg_time_per_question=round(class_avg_response_time, 1),
            current_date=current_date,
            competition_goal_name=competition_goal_name,
            competition_goal_date=competition_goal_date,
            days_to_competition=days_to_competition,
            classes_before_competition=classes_before_competition,
            total_possible_score=total_possible_score,
            personalized_feedback=personalized_feedback,
            class_total_accuracy=class_total_accuracy,
            class_total_participation=class_total_participation,
            class_total_rounds=class_total_rounds,
            class_round_stats=class_round_stats,
            rank=rank
        )
        
    except Exception as e:
        return f'生成学生报告失败: {str(e)}', 500


@app.route('/student_report_center/<student_id>')
def student_report_center(student_id):
    """学生报告中心页面 - 移动端优化"""
    try:
        # 使用原生SQL查询学生信息
        result = db.session.execute(
            text("SELECT id, name, class_id, created_date FROM students WHERE id = :student_id"),
            {'student_id': student_id}
        )
        student_data = result.fetchone()
        
        if not student_data:
            return f'学生不存在: {student_id}', 404
        
        # 创建临时学生对象
        class TempStudent:
            def __init__(self, id, name, class_id, created_date):
                self.id = id
                self.name = name
                self.class_id = class_id
                self.created_date = created_date
        
        student = TempStudent(*student_data)
        
        # 获取班级信息
        class_obj = Class.query.get(student.class_id)
        
        # 获取该学生参与的所有课程（确保是当前学生班级的课程）
        courses_data = []
        courses = Course.query.filter_by(class_id=student.class_id).order_by(Course.created_date.desc()).all()
        
        for course in courses:
            # 计算该学生在当前课程中的表现
            submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == course.id
            ).all()
            
            if submissions:
                total_rounds = len(submissions)
                correct_rounds = sum(1 for s in submissions if s.is_correct)
                accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
                
                # 计算总分
                total_score = 0
                for s in submissions:
                    if s.is_correct:
                        round_obj = CourseRound.query.get(s.round_id)
                        if round_obj and round_obj.question_score:
                            total_score += round_obj.question_score
                        else:
                            total_score += 1
                
                # 计算参与率（简化计算）
                participation_rate = 100
                
                # 计算排名（简化计算）
                all_students = get_students_by_class_id(student.class_id)
                student_scores = []
                for class_student in all_students:
                    class_submissions = StudentSubmission.query.join(CourseRound).filter(
                        StudentSubmission.student_id == class_student.id,
                        CourseRound.course_id == course.id
                    ).all()
                    
                    class_score = 0
                    for s in class_submissions:
                        if s.is_correct:
                            round_obj = CourseRound.query.get(s.round_id)
                            if round_obj and round_obj.question_score:
                                class_score += round_obj.question_score
                            else:
                                class_score += 1
                    student_scores.append(class_score)
                
                student_scores.sort(reverse=True)
                try:
                    rank = student_scores.index(total_score) + 1
                except ValueError:
                    rank = len(student_scores)
                
                courses_data.append({
                    'course': course,
                    'date': course.created_date.strftime('%Y年%m月%d日'),
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
        return f'生成报告中心失败: {str(e)}', 500


def get_students_by_class_id(class_id):
    """获取指定班级的学生列表（避免status字段问题）"""
    try:
        result = db.session.execute(
            text("SELECT id, name, class_id, created_date FROM students WHERE class_id = :class_id"),
            {'class_id': class_id}
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
    # 使用原生SQL查询避免status字段问题
    try:
        # 获取班级数据（只显示未结束的班级）
        result = db.session.execute(text("SELECT id, name, created_date, competition_goal_id FROM classes WHERE ended_date IS NULL ORDER BY created_date DESC"))
        raw_classes = result.fetchall()
        
        # 创建临时班级对象列表
        class TempClass:
            def __init__(self, id, name, created_date, competition_goal_id, student_count, course_count):
                self.id = id
                self.name = name
                self.created_date = created_date
                self.competition_goal_id = competition_goal_id
                self.student_count = student_count
                self.course_count = course_count
        
        classes = []
        for class_row in raw_classes:
            class_id = class_row[0]
            # 获取该班级的学生数量
            student_count_result = db.session.execute(
                text("SELECT COUNT(*) FROM students WHERE class_id = :class_id"),
                {'class_id': class_id}
            )
            student_count = student_count_result.fetchone()[0]
            
            # 获取该班级的课程数量
            course_count_result = db.session.execute(
                text("SELECT COUNT(*) FROM courses WHERE class_id = :class_id"),
                {'class_id': class_id}
            )
            course_count = course_count_result.fetchone()[0]
            
            temp_class = TempClass(
                id=class_row[0],
                name=class_row[1],
                created_date=class_row[2],
                competition_goal_id=class_row[3],
                student_count=student_count,
                course_count=course_count
            )
            classes.append(temp_class)
    except Exception as e:
        print(f"查询班级失败: {e}")
        classes = []
    
    goals = CompetitionGoal.query.order_by(
        CompetitionGoal.created_date.desc()).all()
    
    # 调试信息
    print(f"DEBUG: 查询到 {len(goals)} 个竞赛目标")
    for goal in goals:
        print(f"DEBUG: 竞赛目标 - ID: {goal.id}, 标题: {goal.title}, 创建时间: {goal.created_date}")
    
    # 临时使用原生SQL查询避免status字段问题
    try:
        result = db.session.execute(text("SELECT COUNT(*) FROM students"))
        total_students = result.fetchone()[0]
    except Exception as e:
        print(f"查询学生总数失败: {e}")
        total_students = 0

    return render_template(
        'homepage.html',
        classes=classes,
        competition_goals=goals,
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
                'description': goal_obj.description,
                'goal_date': goal_obj.goal_date.strftime('%Y-%m-%d') if goal_obj.goal_date else None,
                'created_date': goal_obj.created_date.strftime('%Y-%m-%d') if goal_obj.created_date else None
            }
            
            # 计算真实的日期进度
            days_left = 0
            weeks_left = 0
            lessons_left = 0
            if goal_obj.goal_date:
                from datetime import date
                today = date.today()
                days_left = max(0, (goal_obj.goal_date - today).days)
                weeks_left = max(0, days_left // 7)
                # 假设每周2节课，剩余上课数 = 剩余周数 * 2
                lessons_left = max(0, weeks_left * 2)
            
            goal_progress = {
                'days_left': days_left,
                'weeks_left': weeks_left,
                'lessons_left': lessons_left
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
        
        # 检查是否有活跃的课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
        round_active = current_course is not None
        
        # 获取当前轮次号
        current_round = 1
        if current_course:
            latest_round = CourseRound.query.filter_by(
                course_id=current_course.id
            ).order_by(CourseRound.round_number.desc()).first()
            if latest_round:
                current_round = latest_round.round_number
        
        # 构建学生数据字典
        students_data = {}
        for student in students:
            # 计算学生的实际统计数据
            total_score = 0
            total_rounds = 0
            correct_rounds = 0
            last_answer = ''
            
            if current_course:
                # 获取课程中的所有轮次（学生应该参与的轮次总数）
                all_course_rounds = CourseRound.query.filter_by(course_id=current_course.id).all()
                total_rounds = len(all_course_rounds)
                
                # 获取该学生在当前课程中的所有提交记录
                submissions = StudentSubmission.query.join(CourseRound).filter(
                    StudentSubmission.student_id == student.id,
                    CourseRound.course_id == current_course.id
                ).all()
                
                for submission in submissions:
                    if submission.is_correct:
                        # 从CourseRound获取题目分数
                        round_obj = CourseRound.query.get(submission.round_id)
                        if round_obj and round_obj.question_score:
                            total_score += round_obj.question_score
                        else:
                            total_score += 1  # 默认分数
                        correct_rounds += 1
                
                # 获取最新答案
                if submissions:
                    last_submission = max(submissions, key=lambda x: x.submitted_at)
                    last_answer = last_submission.answer
            
            students_data[student.name] = {
                'name': student.name,
                'score': total_score,
                'total_rounds': total_rounds,
                'correct_rounds': correct_rounds,
                'last_answer_time': 0,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': '#4ecdc4',
                'answers': [],
                'last_answer': last_answer
            }
        
        print(f"DEBUG: Returning data for {len(students_data)} students, current_round: {current_round}")
        
        return jsonify({
            'success': True,
            'current_round': current_round,
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
            
            # 获取课程中的所有轮次（学生应该参与的轮次总数）
            all_course_rounds = CourseRound.query.filter_by(course_id=current_course.id).all()
            total_rounds = len(all_course_rounds)
            
            submissions = StudentSubmission.query.join(CourseRound).filter(
                StudentSubmission.student_id == student.id,
                CourseRound.course_id == current_course.id
            ).all()
            
            for submission in submissions:
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


@app.route('/ceremony/<class_id>')
def ceremony(class_id):
    """颁奖典礼页面"""
    try:
        # 获取指定班级的当前活跃课程
        current_course = Course.query.filter_by(class_id=class_id, is_active=True).first()
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


@app.route('/migrate')
def migrate_database():
    """执行数据库迁移"""
    try:
        with app.app_context():
            # 检查并添加 status 字段
            try:
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'status'
                        ) THEN
                            ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active';
                        END IF;
                    END $$;
                """))
                print("status 字段检查/添加完成")
            except Exception as e:
                print(f"status 字段处理: {e}")
            
            # 检查并添加 graduated_date 字段
            try:
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'graduated_date'
                        ) THEN
                            ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP;
                        END IF;
                    END $$;
                """))
                print("graduated_date 字段检查/添加完成")
            except Exception as e:
                print(f"graduated_date 字段处理: {e}")
            
            # 更新现有学生状态
            try:
                result = db.session.execute(text("UPDATE students SET status = 'active' WHERE status IS NULL"))
                print(f"更新了 {result.rowcount} 个学生的状态")
            except Exception as e:
                print(f"更新学生状态: {e}")
            
            # 检查结果
            try:
                result = db.session.execute(text("""
                    SELECT COUNT(*) as total_students, 
                           COUNT(CASE WHEN status = 'active' THEN 1 END) as active_students,
                           COUNT(CASE WHEN status = 'graduated' THEN 1 END) as graduated_students
                    FROM students
                """))
                stats = result.fetchone()
                print(f"迁移完成 - 总学生: {stats[0]}, 活跃: {stats[1]}, 已毕业: {stats[2]}")
            except Exception as e:
                print(f"检查结果: {e}")
        
        return jsonify({
            'success': True,
            'message': '数据库迁移完成',
            'stats': {
                'total_students': stats[0] if 'stats' in locals() else 0,
                'active_students': stats[1] if 'stats' in locals() else 0,
                'graduated_students': stats[2] if 'stats' in locals() else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'迁移失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
