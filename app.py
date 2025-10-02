from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import json
import time
import os
import uuid
from datetime import datetime
import random
from io import BytesIO
from models import db, Class, Student, CompetitionGoal, Course, CourseRound, StudentSubmission, init_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 数据库配置（可选）
USE_DATABASE = os.environ.get('USE_DATABASE', 'false').lower() == 'true'
if USE_DATABASE:
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    init_db(app)
    print("数据库模式已启用")
else:
    print("使用JSON文件模式")

# 应用配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 数据文件路径
DATA_FILE = 'app_data.json'

# 全局数据结构
global_data = {
    'classes': {},
    'competition_goals': {},
    'courses': {},
    'current_course': None,
    'students': {}
}

def load_data():
    """加载数据"""
    global global_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                global_data.update(data)
                
                # 迁移旧格式的课程数据到新格式
                migrate_course_data()
                
                print(f"使用现有数据 - 班级数量: {len(global_data['classes'])}, 竞赛目标数量: {len(global_data['competition_goals'])}, 课程数量: {len(global_data['courses'])}")
        except Exception as e:
            print(f"加载数据失败: {e}")
            init_default_data()
    else:
        init_default_data()

def migrate_course_data():
    """迁移旧格式的课程数据到新格式"""
    global global_data
    
    # 如果全局courses为空，尝试从班级中迁移课程数据
    if not global_data.get('courses'):
        global_data['courses'] = {}
    
    # 遍历所有班级，查找课程数据
    for class_id, class_data in global_data.get('classes', {}).items():
        if 'courses' in class_data and isinstance(class_data['courses'], list):
            for course in class_data['courses']:
                course_id = course.get('id')
                if course_id and course_id not in global_data['courses']:
                    # 迁移课程数据到新格式
                    global_data['courses'][course_id] = {
                        'id': course_id,
                        'students': {},
                        'submissions': [],
                        'is_active': course.get('is_active', False),
                        'start_time': course.get('start_time'),
                        'current_round': course.get('current_round', 1),
                        'round_active': course.get('round_active', False),
                        'current_answers': {},
                        'answer_times': {},
                        'correct_answer': '',
                        'round_results': [],
                        'created_date': course.get('start_date', datetime.now().isoformat())
                    }
                    
                    # 如果有学生数据，也迁移过来
                    if 'students' in course:
                        for student_id, student_data in course['students'].items():
                            global_data['courses'][course_id]['students'][student_data.get('name', student_id)] = {
                                'name': student_data.get('name', student_id),
                                'score': student_data.get('score', 0),
                                'total_rounds': student_data.get('total_rounds', 0),
                                'correct_rounds': student_data.get('correct_rounds', 0),
                                'last_answer_time': student_data.get('last_answer_time', 0),
                                'expression': student_data.get('expression', 'neutral'),
                                'animation': student_data.get('animation', 'none'),
                                'avatar_color': student_data.get('avatar_color', '#ff6b6b'),
                                'answers': student_data.get('answers', []),
                                'last_answer': student_data.get('last_answer', '')
                            }
    
    # 保存迁移后的数据
    save_data()

def save_data():
    """保存数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(global_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存数据失败: {e}")

def init_default_data():
    """初始化默认数据"""
    global global_data
    
    # 创建默认竞赛目标
    goal_id_1 = str(uuid.uuid4())
    goal_id_2 = str(uuid.uuid4())
    
    global_data['competition_goals'] = {
        goal_id_1: {
            'id': goal_id_1,
            'name': 'AMC 8 竞赛',
            'description': '111',
            'start_date': '2025-01-15',
            'end_date': '2025-01-15',
            'total_weeks': 11,
            'lessons_per_week': 1,
            'created_date': '2025-09-26',
            'is_active': True,
            'ended_date': None
        },
        goal_id_2: {
            'id': goal_id_2,
            'name': 'amc10',
            'description': '',
            'start_date': '2025-01-15',
            'end_date': '2025-01-15',
            'total_weeks': 11,
            'lessons_per_week': 1,
            'created_date': '2025-09-26',
            'is_active': True,
            'ended_date': None
        }
    }
    
    # 创建默认班级
    class_id_1 = str(uuid.uuid4())
    class_id_2 = str(uuid.uuid4())
    class_id_3 = str(uuid.uuid4())
    
    global_data['classes'] = {
        class_id_1: {
            'id': class_id_1,
            'name': '数学竞赛班',
            'description': 'AMC 8 数学竞赛准备班级',
            'created_date': '2025-09-26',
            'competition_goal_id': goal_id_1,
            'students': {},
            'courses': [],
            'active_course': None
        },
        class_id_2: {
            'id': class_id_2,
            'name': '123',
            'description': '1',
            'created_date': '2025-09-26',
            'competition_goal_id': goal_id_2,
            'students': {},
            'courses': [],
            'active_course': None
        },
        class_id_3: {
            'id': class_id_3,
            'name': '1',
            'description': '',
            'created_date': '2025-09-26',
            'competition_goal_id': goal_id_2,
            'students': {},
            'courses': [],
            'active_course': None
        }
    }
    
    save_data()
    print("初始化默认数据完成")

# 在应用启动时加载数据
load_data()

# 如果启用了数据库模式，同步数据
if USE_DATABASE:
    try:
        # 延迟导入避免循环导入
        import migrate_data
        migrate_data.migrate_data()
        print("数据同步到数据库完成")
    except Exception as e:
        print(f"数据同步失败: {e}")
        print("继续使用JSON文件模式")
        # 如果数据库同步失败，强制使用JSON模式
        USE_DATABASE = False

@app.route('/')
def index():
    """数学竞赛课堂管理系统主页"""
    if USE_DATABASE:
        # 使用数据库
        with app.app_context():
            # 只显示活跃的班级
            active_classes = Class.query.filter_by(is_active=True).all()
            inactive_classes = Class.query.filter_by(is_active=False).all()
            
            # 区分活跃和历史竞赛目标
            active_goals = CompetitionGoal.query.all()  # 暂时所有目标都是活跃的
            inactive_goals = []  # 暂时没有历史目标
            
            print(f"首页访问 - 活跃班级数量: {len(active_classes)}, 历史班级数量: {len(inactive_classes)}, 活跃竞赛目标数量: {len(active_goals)}, 历史竞赛目标数量: {len(inactive_goals)}")
            
            return render_template('homepage.html',
                                 classes=active_classes,
                                 inactive_classes=inactive_classes,
                                 competition_goals=active_goals,
                                 inactive_competition_goals=inactive_goals)
    else:
        # 使用JSON文件
        # 只显示活跃的班级
        active_classes = [cls for cls in global_data['classes'].values() if cls.get('is_active', True)]
        inactive_classes = [cls for cls in global_data['classes'].values() if not cls.get('is_active', True)]
        
        # 区分活跃和历史竞赛目标
        active_goals = [goal for goal in global_data['competition_goals'].values() if goal.get('is_active', True)]
        inactive_goals = [goal for goal in global_data['competition_goals'].values() if not goal.get('is_active', True)]
        
        print(f"首页访问 - 活跃班级数量: {len(active_classes)}, 历史班级数量: {len(inactive_classes)}, 活跃竞赛目标数量: {len(active_goals)}, 历史竞赛目标数量: {len(inactive_goals)}")
        
        return render_template('homepage.html',
                             classes=active_classes,
                             inactive_classes=inactive_classes,
                             competition_goals=active_goals,
                             inactive_competition_goals=inactive_goals)

@app.route('/class/<class_id>')
def class_detail(class_id):
    """班级详情页面"""
    if class_id not in global_data['classes']:
        return redirect(url_for('index'))
    
    class_data = global_data['classes'][class_id]
    goal_data = global_data['competition_goals'].get(class_data['competition_goal_id'], {})
    
    return render_template('class_detail.html',
                         class_data=class_data,
                         goal_data=goal_data)

@app.route('/api/set_current_course/<course_id>')
def set_current_course(course_id):
    """设置当前课程"""
    global_data['current_course'] = course_id
    save_data()
    return jsonify({'success': True})

@app.route('/start_course')
def start_course():
    """开始课程页面"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return redirect(url_for('index'))
    
    # 创建新课程数据
    if current_course_id not in global_data['courses']:
        global_data['courses'][current_course_id] = {
            'id': current_course_id,
            'students': {},
            'submissions': [],
            'is_active': False,
            'start_time': None,
            'current_round': 1,
            'round_active': False,
            'current_answers': {},
            'answer_times': {},
            'correct_answer': '',
            'round_results': [],
            'created_date': datetime.now().isoformat()
        }
        save_data()
    
    return render_template('start_course.html',
                         course_id=current_course_id)

@app.route('/class/<class_id>/classroom')
def class_classroom(class_id):
    """班级课堂页面"""
    # 获取班级数据
    class_data = global_data['classes'].get(class_id)
    if not class_data:
        return redirect(url_for('index'))
    
    # 获取当前课程
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return redirect(url_for('class_detail', class_id=class_id))
    
    # 获取课程数据
    course_data = global_data['courses'].get(current_course_id, {})
    if not course_data:
        return redirect(url_for('class_detail', class_id=class_id))
    
    return render_template('classroom.html',
                         classroom_data=course_data,
                         class_data=class_data,
                         course_id=current_course_id)

@app.route('/classroom')
def classroom():
    """课堂页面"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return redirect(url_for('index'))
    
    course_data = global_data['courses'].get(current_course_id, {})
    return render_template('classroom.html',
                         classroom_data=course_data,
                         course_id=current_course_id)

@app.route('/ceremony')
def ceremony():
    """颁奖仪式页面"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return redirect(url_for('index'))
    
    course_data = global_data['courses'].get(current_course_id, {})
    
    # 计算排名
    students_ranking = []
    for student_name, student_data in course_data.get('students', {}).items():
        students_ranking.append({
            'name': student_name,
            'score': student_data.get('score', 0),
            'accuracy': (student_data.get('correct_rounds', 0) / max(student_data.get('total_rounds', 1), 1)) * 100,
            'avatar_color': student_data.get('avatar_color', '#ff6b6b')
        })
    
    students_ranking.sort(key=lambda x: x['score'], reverse=True)
    
    # 添加课程ID到course_data中
    course_data['id'] = current_course_id
    
    return render_template('ceremony.html',
                         students=students_ranking,
                         classroom_data=course_data)

@app.route('/reports')
def reports_list():
    """报告列表页面"""
    # 获取所有课程数据
    courses = global_data.get('courses', {})
    
    # 如果没有课程数据，返回主页
    if not courses:
        return redirect('/')
    
    # 获取第一个课程作为默认显示
    first_course_id = list(courses.keys())[0] if courses else None
    
    if first_course_id:
        course_data = courses[first_course_id]
        return render_template('reports.html',
                             students=course_data.get('students', {}),
                             classroom_data=course_data,
                             course_id=first_course_id)
    else:
        return redirect('/')

@app.route('/reports/<course_id>')
def reports(course_id):
    """报告页面"""
    course_data = global_data['courses'].get(course_id, {})
    return render_template('reports.html',
                         students=course_data.get('students', {}),
                         classroom_data=course_data,
                         course_id=course_id)

@app.route('/generate_student_report/<student_name>')
@app.route('/generate_student_report/<student_name>/<course_id>')
def generate_student_report(student_name, course_id=None):
    """生成学生个人报告"""
    # 优先使用传入的course_id，否则使用current_course_id
    if course_id:
        target_course_id = course_id
    else:
        target_course_id = global_data.get('current_course')
    
    # 如果没有指定课程，尝试找到包含该学生的第一个课程
    if not target_course_id:
        for course_id, course_data in global_data['courses'].items():
            if student_name in course_data.get('students', {}):
                target_course_id = course_id
                break
    
    if not target_course_id:
        return redirect(url_for('index'))
    
    course_data = global_data['courses'].get(target_course_id, {})
    
    if student_name not in course_data.get('students', {}):
        return redirect(url_for('reports', course_id=target_course_id))
    
    student = course_data['students'][student_name]
    
    # 计算统计数据
    total_rounds = student.get('total_rounds', 0)
    correct_rounds = student.get('correct_rounds', 0)
    accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
    
    # 从round_results中计算统计数据
    round_results = course_data.get('round_results', [])
    total_rounds_available = len(round_results)
    
    # 计算参与率（学生有答案的轮次数）
    participated_rounds = 0
    total_answer_time = 0
    answer_times = []
    
    for round_result in round_results:
        if student_name in round_result.get('results', {}):
            student_result = round_result['results'][student_name]
            if student_result.get('answer', '').strip():  # 有答案
                participated_rounds += 1
                # 模拟答题时间（实际应用中应该有真实的时间记录）
                answer_time = 30 + (participated_rounds * 5)  # 模拟时间
                answer_times.append(answer_time)
                total_answer_time += answer_time
    
    participation_rate = (participated_rounds / total_rounds_available * 100) if total_rounds_available > 0 else 0
    
    # 计算平均反应时间
    avg_response_time = (total_answer_time / participated_rounds) if participated_rounds > 0 else 0
    
    # 计算学生实际得分
    student_total_score = 0
    total_possible_score = 0
    for round_result in round_results:
        question_score = round_result.get('question_score', 1)
        total_possible_score += question_score
        if student_name in round_result.get('results', {}):
            student_result = round_result['results'][student_name]
            if student_result.get('correct', False):
                student_total_score += question_score
    
    # 计算未参与轮次
    missed_rounds = total_rounds_available - participated_rounds
    
    # 计算班级平均值
    all_students = list(course_data.get('students', {}).values())
    if all_students:
        class_avg_accuracy = sum(s.get('correct_rounds', 0) / max(s.get('total_rounds', 1), 1) * 100 for s in all_students) / len(all_students)
        
        # 计算班级平均参与率
        class_participation_sum = 0
        class_response_time_sum = 0
        class_response_time_count = 0
        
        for student in all_students:
            student_name = student.get('name', '')
            student_participated = 0
            
            for round_result in round_results:
                if student_name in round_result.get('results', {}):
                    student_result = round_result['results'][student_name]
                    if student_result.get('answer', '').strip():
                        student_participated += 1
                        # 模拟答题时间
                        answer_time = 30 + (student_participated * 5)
                        class_response_time_sum += answer_time
                        class_response_time_count += 1
            
            student_participation_rate = (student_participated / total_rounds_available * 100) if total_rounds_available > 0 else 0
            class_participation_sum += student_participation_rate
        
        class_avg_participation = class_participation_sum / len(all_students)
        class_avg_response_time = (class_response_time_sum / class_response_time_count) if class_response_time_count > 0 else 0
        
        # 计算班级平均得分
        class_total_score_sum = 0
        for student in all_students:
            student_name_inner = student.get('name', '')
            student_score = 0
            for round_result in round_results:
                question_score = round_result.get('question_score', 1)
                if student_name_inner in round_result.get('results', {}):
                    student_result = round_result['results'][student_name_inner]
                    if student_result.get('correct', False):
                        student_score += question_score
            class_total_score_sum += student_score
        
        class_avg_score = class_total_score_sum / len(all_students) if all_students else 0
    else:
        class_avg_accuracy = 0
        class_avg_participation = 0
        class_avg_response_time = 0
        class_avg_score = 0
    
    # 生成个性化评价
    personalized_feedback = generate_personalized_feedback(
        accuracy, avg_response_time, participation_rate,
        class_avg_accuracy, class_avg_response_time, class_avg_participation
    )
    
    # 计算班级每题统计数据
    class_round_stats = []
    total_class_correct = 0
    total_class_participation = 0
    total_class_time = 0
    total_class_time_count = 0
    
    for i, round_result in enumerate(round_results):
        round_correct_count = 0
        round_participation_count = 0
        round_total_time = 0
        round_time_count = 0
        
        # 统计这一轮所有学生的表现
        for student_id, student_data in course_data.get('students', {}).items():
            if student_id in round_result.get('results', {}):
                student_result = round_result['results'][student_id]
                if student_result.get('answer', '').strip():  # 有参与
                    round_participation_count += 1
                    if student_result.get('correct', False):  # 答对了
                        round_correct_count += 1
                    # 模拟答题时间
                    answer_time = 30 + (i + 1) * 5
                    round_total_time += answer_time
                    round_time_count += 1
        
        total_students = len(course_data.get('students', {}))
        round_accuracy = (round_correct_count / round_participation_count * 100) if round_participation_count > 0 else 0
        round_participation_rate = (round_participation_count / total_students * 100) if total_students > 0 else 0
        round_avg_time = (round_total_time / round_time_count) if round_time_count > 0 else 0
        
        class_round_stats.append({
            'round': i + 1,
            'accuracy': round_accuracy,
            'participation_rate': round_participation_rate,
            'avg_time': round_avg_time
        })
        
        total_class_correct += round_correct_count
        total_class_participation += round_participation_count
        total_class_time += round_total_time
        total_class_time_count += round_time_count
    
    # 计算班级总体统计
    class_total_accuracy = (total_class_correct / total_class_participation * 100) if total_class_participation > 0 else 0
    class_total_participation = (total_class_participation / (len(course_data.get('students', {})) * len(round_results)) * 100) if len(course_data.get('students', {})) > 0 and len(round_results) > 0 else 0
    class_avg_time_per_question = (total_class_time / total_class_time_count) if total_class_time_count > 0 else 0
    
    # 生成学生提交记录（从round_results中提取）
    student_submissions = []
    for i, round_result in enumerate(round_results):
        if student_name in round_result.get('results', {}):
            student_result = round_result['results'][student_name]
            submission = {
                'round': i + 1,
                'answer': student_result.get('answer', ''),
                'correct': student_result.get('correct', False),
                'is_correct': student_result.get('correct', False),  # 为了兼容模板
                'score': student_result.get('score', 0),
                'time': 30 + (i + 1) * 5,  # 模拟时间
                'answer_time': 30 + (i + 1) * 5,  # 为了兼容模板
                'question_score': round_result.get('question_score', 1)  # 题目分数
            }
            student_submissions.append(submission)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('student_report.html',
                         student=student,
                         student_name=student['name'],
                         total_rounds=total_rounds,
                         correct_rounds=correct_rounds,
                         accuracy=accuracy,
                         submissions=student_submissions,
                         student_submissions=student_submissions,
                         round_results=course_data.get('round_results', []),
                         current_time=current_time,
                         current_date=current_time.split(' ')[0],
                         participation_rate=round(participation_rate, 1),
                         missed_rounds=missed_rounds,
                         avg_response_time=round(avg_response_time, 1),
                         class_avg_accuracy=round(class_avg_accuracy, 1),
                         class_avg_participation=round(class_avg_participation, 1),
                         class_avg_response_time=round(class_avg_response_time, 1),
                         student_total_score=student_total_score,
                         total_possible_score=total_possible_score,
                         class_avg_score=round(class_avg_score, 1),
                         personalized_feedback=personalized_feedback,
                         # 新增班级统计数据
                         class_round_stats=class_round_stats,
                         class_total_accuracy=round(class_total_accuracy, 1),
                         class_total_participation=round(class_total_participation, 1),
                         class_total_rounds=len(round_results),
                         class_avg_time_per_question=round(class_avg_time_per_question, 1),
                         global_data=global_data)

def generate_personalized_feedback(
        accuracy,
        avg_response_time,
        participation_rate,
        class_avg_accuracy,
        class_avg_response_time,
        class_avg_participation):
    """根据学生表现生成个性化评价（按照新的文案逻辑）"""
    
    # 使用新的评价规则
    comment = generate_comment(accuracy, class_avg_accuracy, participation_rate, avg_response_time, class_avg_response_time)
    
    # 保持原有的结构，但使用新的评价内容
    return {
        'focus_title': "学习评价",
        'focus_feedback': comment,
        'accuracy_title': "",
        'accuracy_feedback': "",
        'speed_title': "",
        'speed_feedback': ""
    }

def generate_comment(accuracy, class_avg, focus, reaction, reaction_avg):
    """生成学习评价内容"""
    comment_parts = []

    # 专注度
    if focus >= 80:
        comment_parts.append("孩子在课堂中始终保持高度专注，积极参与每个环节，学习态度非常认真。")
    elif focus >= 60:
        comment_parts.append("孩子在课堂中能较好地保持专注，大部分时间认真参与，学习状态稳定。")
    else:
        comment_parts.append("孩子在课堂中展现出一定的专注度，说明具备学习意愿，但整体专注力还需进一步加强，才能更好地跟上课堂节奏。")

    # 正确率
    if accuracy > class_avg + 5:
        comment_parts.append("答题正确率高于班级平均，说明对知识点掌握扎实，能够轻松应对课堂内容。")
    elif abs(accuracy - class_avg) <= 5:
        comment_parts.append("答题正确率接近班级平均，说明学习状态稳健，能够很好地跟上课堂节奏。")
    else:
        comment_parts.append("答题正确率低于班级平均，说明本节课难度对孩子有挑战，但也能带来更多成长空间。")

    # 反应时间
    if reaction < reaction_avg - 2:
        comment_parts.append("答题速度快于班级平均，展现出思维敏捷。")
    elif abs(reaction - reaction_avg) <= 2:
        comment_parts.append("答题速度与班级平均接近，思维节奏稳定。")
    else:
        comment_parts.append("答题速度慢于班级平均，体现了认真思考的态度，但需要逐步提升运算速度，减少对计算器的依赖。")

    return " ".join(comment_parts)

# API 路由
@app.route('/start_class', methods=['POST'])
def start_class_legacy():
    """开始课堂（兼容旧版本）"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    if not course_data:
        return jsonify({'error': '课程不存在'}), 400
    
    # 开始课堂
    course_data['is_active'] = True
    course_data['round_active'] = True
    course_data['start_time'] = time.time()
    course_data['current_round'] = 1
    course_data['current_answers'] = {}
    course_data['answer_times'] = {}
    course_data['correct_answer'] = ''
    
    save_data()
    return jsonify({'success': True})

@app.route('/api/start_class', methods=['POST'])
def start_class():
    """开始课堂"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    course_data['is_active'] = True
    course_data['round_active'] = True
    course_data['start_time'] = time.time()
    
    save_data()
    return jsonify({'success': True})

@app.route('/submit_student_answer', methods=['POST'])
def submit_student_answer_legacy():
    """提交学生答案（兼容旧版本）"""
    data = request.get_json()
    student_name = data.get('student_name', '').strip()
    answer = data.get('answer', '').strip()
    
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    if not student_name or not answer:
        return jsonify({'error': '学生姓名和答案不能为空'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    if not course_data:
        return jsonify({'error': '课程不存在'}), 400
    
    # 记录答案
    course_data['current_answers'][student_name] = answer
    course_data['answer_times'][student_name] = time.time()
    
    # 更新学生状态
    if student_name in course_data['students']:
        course_data['students'][student_name]['expression'] = 'submitted'
        course_data['students'][student_name]['last_answer'] = answer
    
    save_data()
    return jsonify({'success': True})

@app.route('/api/submit_student_answer', methods=['POST'])
def submit_student_answer():
    """学生提交答案"""
    data = request.get_json()
    student_name = data.get('student_name', '').strip()
    answer = data.get('answer', '').strip()
    
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    
    if not student_name or not answer:
        return jsonify({'error': '学生姓名和答案不能为空'}), 400
    
    if student_name not in course_data.get('students', {}):
        return jsonify({'error': '学生不存在'}), 400
    
    if not course_data.get('round_active', False):
        return jsonify({'error': '当前没有活跃的答题轮次'}), 400
    
    # 记录答题时间
    current_time = time.time()
    if course_data.get('start_time'):
        answer_time = current_time - course_data['start_time']
    else:
        answer_time = 0
    
    if 'answer_times' not in course_data:
        course_data['answer_times'] = {}
    if 'current_answers' not in course_data:
        course_data['current_answers'] = {}
    
    course_data['answer_times'][student_name] = answer_time
    course_data['current_answers'][student_name] = answer
    
    # 更新学生的答题时间
    if student_name in course_data['students']:
        course_data['students'][student_name]['last_answer_time'] = answer_time
    
    save_data()
    return jsonify({'success': True, 'answer_time': answer_time})

@app.route('/judge_answers', methods=['POST'])
def judge_answers_legacy():
    """评判答案（兼容旧版本）"""
    data = request.get_json()
    correct_answer = data.get('correct_answer', '').strip()
    question_score = data.get('question_score', 1)
    
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    if not correct_answer:
        return jsonify({'error': '正确答案不能为空'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    if not course_data:
        return jsonify({'error': '课程不存在'}), 400
    
    # 评判答案
    course_data['correct_answer'] = correct_answer
    round_result = {
        'round': course_data.get('current_round', 1),
        'correct_answer': correct_answer,
        'question_score': question_score,
        'results': {}
    }
    
    for student_id, student_data in course_data['students'].items():
        student_answer = course_data['current_answers'].get(student_id, '')
        
        # 检查学生是否提交了答案
        if student_answer:  # 学生提交了答案
            is_correct = student_answer.lower() == correct_answer.lower()
            
            if is_correct:
                student_data['score'] += question_score
                student_data['correct_rounds'] += 1
                student_data['expression'] = 'smile'
                student_data['animation'] = 'celebration'
            else:
                student_data['expression'] = 'angry'
                student_data['animation'] = 'none'
            
            student_data['total_rounds'] += 1
            student_data['last_answer'] = student_answer
            
            round_result['results'][student_id] = {
                'answer': student_answer,
                'correct': is_correct,
                'score': student_data['score']
            }
        else:  # 学生未提交答案
            student_data['expression'] = 'embarrassed'  # 未作答状态
            student_data['animation'] = 'none'
            student_data['last_answer'] = ''  # 清空答案
            
            round_result['results'][student_id] = {
                'answer': '',
                'correct': False,
                'score': student_data['score']
            }
    
    # 添加轮次结果
    course_data['round_results'].append(round_result)
    
    # 停止当前轮次
    course_data['round_active'] = False
    
    save_data()
    return jsonify({
        'success': True, 
        'round_result': round_result,
        'students': course_data['students']
    })

@app.route('/api/judge_answers', methods=['POST'])
def judge_answers():
    """评判答案"""
    data = request.get_json()
    correct_answer = data.get('correct_answer', '').strip()
    question_score = data.get('question_score', 1)
    
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    if not correct_answer:
        return jsonify({'error': '正确答案不能为空'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    course_data['correct_answer'] = correct_answer
    
    # 评判每个学生的答案
    round_result = {
        'round': course_data.get('current_round', 1),
        'correct_answer': correct_answer,
        'results': {}
    }
    
    # 为所有学生评判答案（包括未提交答案的学生）
    for student_id, student_data in course_data.get('students', {}).items():
        student_answer = course_data.get('current_answers', {}).get(student_id, '')

        # 检查学生是否提交了答案
        if student_answer:  # 学生提交了答案
            is_correct = student_answer.lower() == correct_answer.lower()

            if is_correct:
                student_data['score'] += question_score
                student_data['correct_rounds'] += 1
                student_data['expression'] = 'smile'
                student_data['animation'] = 'celebration'
            else:
                student_data['expression'] = 'angry'
                student_data['animation'] = 'none'

            student_data['total_rounds'] += 1
            student_data['last_answer'] = student_answer

            round_result['results'][student_id] = {
                'answer': student_answer,
                'correct': is_correct,
                'score': student_data['score']
            }
        else:  # 学生未提交答案
            student_data['expression'] = 'embarrassed'  # 未作答状态
            student_data['animation'] = 'none'
            student_data['last_answer'] = ''  # 清空答案

            round_result['results'][student_id] = {
                'answer': '',
                'correct': False,
                'score': student_data['score']
            }

        student_data['last_answer_time'] = course_data.get('answer_times', {}).get(student_id, 0)

        # 记录提交
        submission = {
            'student_name': student_id,
            'round': course_data.get('current_round', 1),
            'answer': student_answer,
            'is_correct': is_correct if student_answer else False,
            'earned_score': question_score if (student_answer and is_correct) else 0,
            'answer_time': student_data['last_answer_time'],
            'timestamp': datetime.now().isoformat()
        }

        if 'answers' not in student_data:
            student_data['answers'] = []
        student_data['answers'].append(submission)
        
        if 'submissions' not in course_data:
            course_data['submissions'] = []
        course_data['submissions'].append(submission)

    if 'round_results' not in course_data:
        course_data['round_results'] = []
    course_data['round_results'].append(round_result)

    # 重置当前轮次状态
    course_data['round_active'] = False
    course_data['current_answers'] = {}
    course_data['answer_times'] = {}
    course_data['start_time'] = None

    save_data()
    return jsonify({
        'success': True, 
        'round_result': round_result,
        'students': course_data['students']
    })

@app.route('/next_round', methods=['POST'])
def next_round_legacy():
    """下一轮（兼容旧版本）"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    if not course_data:
        return jsonify({'error': '课程不存在'}), 400
    
    # 进入下一轮
    course_data['current_round'] += 1
    course_data['round_active'] = True
    course_data['current_answers'] = {}
    course_data['answer_times'] = {}
    course_data['correct_answer'] = ''
    
    # 重置学生状态
    for student_data in course_data['students'].values():
        student_data['expression'] = 'neutral'
        student_data['animation'] = 'none'
    
    save_data()
    return jsonify({
        'success': True, 
        'current_round': course_data.get('current_round', 1),
        'students': course_data['students'],
        'round': course_data.get('current_round', 1)
    })

@app.route('/api/next_round', methods=['POST'])
def next_round():
    """进入下一轮"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    course_data['current_round'] = course_data.get('current_round', 1) + 1
    course_data['round_active'] = True
    course_data['start_time'] = time.time()
    
    # 重置所有学生表情
    for student in course_data.get('students', {}).values():
        student['expression'] = 'neutral'
        student['animation'] = 'none'
    
    save_data()
    return jsonify({
        'success': True, 
        'current_round': course_data.get('current_round', 1),
        'students': course_data['students'],
        'round': course_data.get('current_round', 1)
    })

@app.route('/get_classroom_data')
def get_classroom_data_legacy():
    """获取课堂数据（兼容旧版本）"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    return jsonify(course_data)

@app.route('/api/get_classroom_data')
def get_classroom_data():
    """获取课堂数据"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    course_data = global_data['courses'].get(current_course_id, {})
    return jsonify(course_data)

@app.route('/reset_classroom', methods=['POST'])
def reset_classroom_legacy():
    """重置课堂（兼容旧版本）"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    global_data['courses'][current_course_id] = {
        'id': current_course_id,
        'students': {},
        'submissions': [],
        'is_active': False,
        'start_time': None,
        'current_round': 1,
        'round_active': False,
        'current_answers': {},
        'answer_times': {},
        'correct_answer': '',
        'round_results': [],
        'created_date': datetime.now().isoformat()
    }
    
    save_data()
    return jsonify({'success': True})

@app.route('/api/reset_classroom', methods=['POST'])
def reset_classroom():
    """重置课堂"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    global_data['courses'][current_course_id] = {
        'id': current_course_id,
        'students': {},
        'submissions': [],
        'is_active': False,
        'start_time': None,
        'current_round': 1,
        'round_active': False,
        'current_answers': {},
        'answer_times': {},
        'correct_answer': '',
        'round_results': [],
        'created_date': datetime.now().isoformat()
    }
    
    save_data()
    return jsonify({'success': True})

@app.route('/api/start_course', methods=['POST'])
def api_start_course():
    """API: 创建并开始新课程"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        course_name = data.get('course_name', '新课程')
        
        if not class_id:
            return jsonify({
                'success': False,
                'message': '班级ID不能为空'
            }), 400
        
        # 获取班级数据
        class_data = global_data['classes'].get(class_id)
        if not class_data:
            return jsonify({
                'success': False,
                'message': '班级不存在'
            }), 400
        
        # 创建新课程
        course_id = str(uuid.uuid4())
        
        # 将班级中的学生复制到课程中
        course_students = {}
        for student_id, student_data in class_data.get('students', {}).items():
            course_students[student_data.get('name', student_id)] = {
                'name': student_data.get('name', student_id),
                'score': 0,
                'total_rounds': 0,
                'correct_rounds': 0,
                'last_answer_time': 0,
                'expression': 'neutral',
                'animation': 'none',
                'avatar_color': student_data.get('avatar_color', '#ff6b6b'),
                'answers': [],
                'last_answer': ''
            }
        
        new_course = {
            'id': course_id,
            'name': course_name,
            'class_id': class_id,
            'students': course_students,
            'submissions': [],
            'is_active': True,
            'start_time': datetime.now().isoformat(),
            'current_round': 1,
            'round_active': False,
            'current_answers': {},
            'answer_times': {},
            'correct_answer': '',
            'round_results': [],
            'created_date': datetime.now().isoformat()
        }
        
        # 保存课程到全局数据
        global_data['courses'][course_id] = new_course
        global_data['current_course'] = course_id
        
        # 将课程添加到班级的课程列表中
        if class_id in global_data['classes']:
            if 'courses' not in global_data['classes'][class_id]:
                global_data['classes'][class_id]['courses'] = []
            
            global_data['classes'][class_id]['courses'].append({
                'id': course_id,
                'name': course_name,
                'start_date': datetime.now().isoformat(),
                'is_active': True
            })
        
        save_data()
        
        return jsonify({
            'success': True,
            'course_id': course_id,
            'message': '课程创建成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建课程失败: {str(e)}'
        }), 500

@app.route('/api/create_demo_data', methods=['POST'])
def create_demo_data():
    """创建演示数据"""
    current_course_id = global_data.get('current_course')
    if not current_course_id:
        return jsonify({'error': '没有当前课程'}), 400
    
    demo_students = ['小明', '小红', '小刚', '小丽', '小华']
    course_data = global_data['courses'].get(current_course_id, {})
    
    # 清空现有数据
    course_data['students'] = {}
    course_data['submissions'] = []
    course_data['round_results'] = []
    
    # 创建演示学生数据
    for student_name in demo_students:
        student_submissions = []
        correct_count = 0
        total_score = 0
        
        for round_num in range(1, 6):
            is_correct = random.choice([True, False])
            answer_time = random.uniform(5, 45)
            earned_score = 1 if is_correct else 0
            
            if is_correct:
                correct_count += 1
            total_score += earned_score
            
            submission = {
                'student_name': student_name,
                'round': round_num,
                'answer': f'答案{round_num}',
                'is_correct': is_correct,
                'earned_score': earned_score,
                'answer_time': answer_time,
                'timestamp': datetime.now().isoformat()
            }
            student_submissions.append(submission)
            course_data['submissions'].append(submission)
        
        course_data['students'][student_name] = {
            'name': student_name,
            'score': total_score,
            'total_rounds': 5,
            'correct_rounds': correct_count,
            'last_answer_time': student_submissions[-1]['answer_time'] if student_submissions else 0,
            'expression': 'neutral',
            'animation': 'none',
            'avatar_color': random.choice(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd']),
            'answers': student_submissions,
            'last_answer': ''
        }
    
    # 创建轮次结果
    for round_num in range(1, 6):
        round_result = {
            'round': round_num,
            'correct_answer': f'正确答案{round_num}',
            'results': {}
        }
        
        for student_name in demo_students:
            student_submission = next((s for s in course_data['submissions'] 
                                     if s['student_name'] == student_name and s['round'] == round_num), None)
            if student_submission:
                round_result['results'][student_name] = {
                    'answer': student_submission['answer'],
                    'is_correct': student_submission['is_correct'],
                    'answer_time': student_submission['answer_time']
                }
        
        course_data['round_results'].append(round_result)
    
    course_data['current_round'] = 6
    course_data['is_active'] = True
    
    save_data()
    return jsonify({'success': True, 'students': list(course_data['students'].keys())})

@app.route('/api/add_student', methods=['POST'])
def add_student():
    """添加学生到班级"""
    try:
        data = request.get_json()
        student_id = str(uuid.uuid4())
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                student = Student(
                    id=student_id,
                    name=data.get('name', ''),
                    class_id=data.get('class_id'),
                    created_date=datetime.utcnow()
                )
                db.session.add(student)
                db.session.commit()
        else:
            # 使用JSON文件
            student_data = {
                'id': student_id,
                'name': data.get('name', ''),
                'class_id': data.get('class_id'),
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # 添加到全局学生数据
            global_data['students'][student_id] = student_data
            
            # 添加到班级的学生列表
            if data.get('class_id') in global_data['classes']:
                global_data['classes'][data.get('class_id')]['students'][student_id] = student_data
            
            save_data()
        
        return jsonify({'success': True, 'student_id': student_id})
        
    except Exception as e:
        print(f"添加学生时发生错误: {e}")
        return jsonify({'error': '添加学生时发生错误', 'details': str(e)}), 500

@app.route('/api/create_class', methods=['POST'])
def create_class():
    """创建新班级"""
    try:
        data = request.get_json()
        class_id = str(uuid.uuid4())
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                class_obj = Class(
                    id=class_id,
                    name=data.get('name', ''),
                    description=data.get('description', ''),
                    is_active=True,
                    created_date=datetime.utcnow()
                )
                db.session.add(class_obj)
                db.session.commit()
        else:
            # 使用JSON文件
            class_data = {
                'id': class_id,
                'name': data.get('name', ''),
                'description': data.get('description', ''),
                'students': {},
                'courses': [],
                'competition_goal_id': None,
                'is_active': True,
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            global_data['classes'][class_id] = class_data
            save_data()
        
        return jsonify({'success': True, 'class_id': class_id})
        
    except Exception as e:
        print(f"创建班级时发生错误: {e}")
        return jsonify({'error': '创建班级时发生错误', 'details': str(e)}), 500

@app.route('/api/create_competition_goal', methods=['POST'])
def create_competition_goal():
    """创建新竞赛目标"""
    try:
        data = request.get_json()
        goal_id = str(uuid.uuid4())
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                goal_obj = CompetitionGoal(
                    id=goal_id,
                    title=data.get('name', ''),
                    description=data.get('description', ''),
                    target_score=100,
                    created_date=datetime.utcnow()
                )
                db.session.add(goal_obj)
                db.session.commit()
        else:
            # 使用JSON文件
            goal_data = {
                'id': goal_id,
                'name': data.get('name', ''),
                'description': data.get('description', ''),
                'goal_date': data.get('goal_date', ''),
                'is_active': True,
                'ended_date': None,
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            global_data['competition_goals'][goal_id] = goal_data
            save_data()
        
        return jsonify({'success': True, 'goal_id': goal_id})
        
    except Exception as e:
        print(f"创建竞赛目标时发生错误: {e}")
        return jsonify({'error': '创建竞赛目标时发生错误', 'details': str(e)}), 500

@app.route('/api/get_competition_goals')
def get_competition_goals():
    """获取所有竞赛目标"""
    try:
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                goals = CompetitionGoal.query.all()
                goals_data = []
                for goal in goals:
                    goals_data.append({
                        'id': goal.id,
                        'name': goal.title,
                        'description': goal.description,
                        'goal_date': goal.created_date.strftime('%Y-%m-%d') if goal.created_date else '',
                        'is_active': True
                    })
                return jsonify({
                    'success': True,
                    'goals': goals_data
                })
        else:
            # 使用JSON文件
            active_goals = []
            for goal in global_data['competition_goals'].values():
                if goal.get('is_active', True):  # 默认为True
                    active_goals.append(goal)
            
            return jsonify({
                'success': True,
                'goals': active_goals
            })
        
    except Exception as e:
        print(f"获取竞赛目标时发生错误: {e}")
        return jsonify({'error': '获取竞赛目标时发生错误', 'details': str(e)}), 500

@app.route('/api/assign_goal_to_class', methods=['POST'])
def assign_goal_to_class():
    """分配竞赛目标到班级"""
    try:
        data = request.get_json()
        goal_id = data.get('goal_id')
        class_id = data.get('class_id')
        
        if not goal_id or not class_id:
            return jsonify({'error': '竞赛目标ID和班级ID不能为空'}), 400
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                class_obj = Class.query.get(class_id)
                if not class_obj:
                    return jsonify({'error': '班级不存在'}), 404
                
                class_obj.competition_goal_id = goal_id
                db.session.commit()
        else:
            # 使用JSON文件
            if goal_id not in global_data['competition_goals']:
                return jsonify({'error': '竞赛目标不存在'}), 404
            
            if class_id not in global_data['classes']:
                return jsonify({'error': '班级不存在'}), 404
            
            # 分配竞赛目标到班级
            global_data['classes'][class_id]['competition_goal_id'] = goal_id
            save_data()
        
        return jsonify({'success': True, 'message': '竞赛目标分配成功'})
        
    except Exception as e:
        print(f"分配竞赛目标时发生错误: {e}")
        return jsonify({'error': '分配竞赛目标时发生错误', 'details': str(e)}), 500

@app.route('/api/end_competition_goal/<goal_id>', methods=['POST'])
def end_competition_goal(goal_id):
    """结束竞赛目标"""
    try:
        if goal_id not in global_data['competition_goals']:
            return jsonify({'error': '竞赛目标不存在'}), 404
        
        goal_data = global_data['competition_goals'][goal_id]
        
        # 标记竞赛目标为已结束
        goal_data['is_active'] = False
        goal_data['ended_date'] = datetime.now().strftime('%Y-%m-%d')
        
        save_data()
        
        return jsonify({'success': True, 'message': '竞赛目标已结束'})
        
    except Exception as e:
        print(f"结束竞赛目标时发生错误: {e}")
        return jsonify({'error': '结束竞赛目标时发生错误', 'details': str(e)}), 500

@app.route('/api/delete_competition_goal/<goal_id>', methods=['DELETE'])
def delete_competition_goal(goal_id):
    """删除竞赛目标（仅限未使用的目标）"""
    try:
        if goal_id not in global_data['competition_goals']:
            return jsonify({'error': '竞赛目标不存在'}), 404
        
        # 检查是否有班级正在使用这个竞赛目标（包括已结束的班级）
        classes_using_goal = [cls for cls in global_data['classes'].values() 
                            if cls.get('competition_goal_id') == goal_id]
        
        if classes_using_goal:
            class_names = [cls['name'] for cls in classes_using_goal]
            return jsonify({
                'error': f'无法删除竞赛目标，以下班级正在使用：{", ".join(class_names)}。建议使用"结束竞赛"功能。'
            }), 400
        
        # 删除竞赛目标
        del global_data['competition_goals'][goal_id]
        save_data()
        
        return jsonify({'success': True, 'message': '竞赛目标已删除'})
        
    except Exception as e:
        print(f"删除竞赛目标时发生错误: {e}")
        return jsonify({'error': '删除竞赛目标时发生错误', 'details': str(e)}), 500

@app.route('/api/test')
def test_api():
    """测试API是否正常工作"""
    return jsonify({'message': 'API正常工作', 'timestamp': datetime.now().isoformat()})

@app.route('/api/end_class/<class_id>', methods=['POST'])
def end_class(class_id):
    """结束班级"""
    try:
        print(f"收到结束班级请求: {class_id}")
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                class_obj = Class.query.get(class_id)
                if not class_obj:
                    print(f"班级 {class_id} 不存在")
                    return jsonify({'error': '班级不存在'}), 404
                
                # 标记班级为已结束
                class_obj.is_active = False
                class_obj.ended_date = datetime.utcnow()
                
                # 结束该班级的所有课程
                courses = Course.query.filter_by(class_id=class_id).all()
                for course in courses:
                    course.is_active = False
                
                db.session.commit()
                print(f"班级 {class_id} 已成功结束")
        else:
            # 使用JSON文件
            print(f"当前班级列表: {list(global_data['classes'].keys())}")
            
            if class_id not in global_data['classes']:
                print(f"班级 {class_id} 不存在")
                return jsonify({'error': '班级不存在'}), 404
            
            class_data = global_data['classes'][class_id]
            
            # 标记班级为已结束
            class_data['is_active'] = False
            class_data['ended_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # 结束该班级的所有课程
            for course_id, course_data in global_data['courses'].items():
                if course_data.get('class_id') == class_id:
                    course_data['is_active'] = False
            
            save_data()
            print(f"班级 {class_id} 已成功结束")
        
        return jsonify({'success': True, 'message': '班级已成功结束'})
        
    except Exception as e:
        print(f"结束班级时发生错误: {e}")
        return jsonify({'error': '结束班级时发生错误', 'details': str(e)}), 500

@app.route('/api/start_course', methods=['POST'])
def start_course():
    """开始课程"""
    try:
        data = request.get_json()
        course_id = str(uuid.uuid4())
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                course = Course(
                    id=course_id,
                    name=data.get('name', ''),
                    class_id=data.get('class_id'),
                    is_active=True,
                    created_date=datetime.utcnow()
                )
                db.session.add(course)
                db.session.commit()
        else:
            # 使用JSON文件
            course_data = {
                'id': course_id,
                'name': data.get('name', ''),
                'class_id': data.get('class_id'),
                'is_active': True,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'students': {},
                'submissions': [],
                'round_results': [],
                'current_round': 1,
                'round_active': False
            }
            
            global_data['courses'][course_id] = course_data
            save_data()
        
        return jsonify({'success': True, 'course_id': course_id})
        
    except Exception as e:
        print(f"开始课程时发生错误: {e}")
        return jsonify({'error': '开始课程时发生错误', 'details': str(e)}), 500

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """提交答案"""
    try:
        data = request.get_json()
        
        if USE_DATABASE:
            # 使用数据库
            with app.app_context():
                # 查找或创建课程轮次
                round_id = f"{data['course_id']}_round_{data['round_number']}"
                round_obj = CourseRound.query.get(round_id)
                
                if not round_obj:
                    round_obj = CourseRound(
                        id=round_id,
                        course_id=data['course_id'],
                        round_number=data['round_number'],
                        question_text=data.get('question', ''),
                        correct_answer=data.get('correct_answer', ''),
                        question_score=data.get('question_score', 1),
                        created_date=datetime.utcnow()
                    )
                    db.session.add(round_obj)
                
                # 创建学生提交记录
                submission_id = f"{data['student_id']}_{round_id}"
                submission = StudentSubmission(
                    id=submission_id,
                    student_id=data['student_id'],
                    round_id=round_id,
                    answer=data['answer'],
                    is_correct=data['answer'] == data['correct_answer'],
                    answer_time=data.get('answer_time', 0.0),
                    submitted_at=datetime.utcnow()
                )
                
                db.session.add(submission)
                db.session.commit()
                
                return jsonify({'success': True, 'is_correct': submission.is_correct})
        else:
            # 使用JSON文件（保持原有逻辑）
            course_id = data.get('course_id')
            student_name = data.get('student_name')
            answer = data.get('answer')
            correct_answer = data.get('correct_answer')
            
            if not course_id or not student_name or not answer:
                return jsonify({'error': '课程ID、学生姓名和答案不能为空'}), 400
            
            course_data = global_data['courses'].get(course_id, {})
            if not course_data:
                return jsonify({'error': '课程不存在'}), 400
            
            # 记录答案
            course_data['current_answers'][student_name] = answer
            
            # 记录答题时间（模拟）
            current_time = time.time()
            if 'start_time' in course_data:
                answer_time = current_time - course_data['start_time']
                course_data['answer_times'][student_name] = answer_time
            
            save_data()
            
            return jsonify({'success': True, 'message': '答案已提交'})
        
    except Exception as e:
        print(f"提交答案时发生错误: {e}")
        return jsonify({'error': '提交答案时发生错误', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)