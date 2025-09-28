# 新的课堂管理系统 - 数据结构设计

# 全局数据结构
global_data = {
    # 班级管理
    'classes': {
        # 'class_id': {
        #     'id': 'class_id',
        #     'name': '班级名称',
        #     'description': '班级描述',
        #     'created_date': '2025-09-26',
        #     'competition_goal_id': 'goal_id',  # 关联的竞赛目标
        #     'students': {},  # 长期学员
        #     'courses': [],   # 历史课程记录
        #     'active_course': None  # 当前活跃课程
        # }
    },
    
    # 竞赛目标管理
    'competition_goals': {
        # 'goal_id': {
        #     'id': 'goal_id',
        #     'name': '目标名称',
        #     'description': '目标描述',
        #     'start_date': '2025-09-26',
        #     'end_date': '2025-12-31',
        #     'total_weeks': 12,
        #     'lessons_per_week': 1,
        #     'created_date': '2025-09-26'
        # }
    },
    
    # 学生管理（全局）
    'students': {
        # 'student_id': {
        #     'id': 'student_id',
        #     'name': '学生姓名',
        #     'avatar_color': '#ff6b6b',
        #     'created_date': '2025-09-26',
        #     'total_score': 0,  # 所有课程累计分数
        #     'total_rounds': 0,  # 所有课程累计轮次
        #     'total_correct_rounds': 0,  # 所有课程累计正确轮次
        #     'class_memberships': ['class_id1', 'class_id2']  # 所属班级
        # }
    }
}

# 课程数据结构
course_data_template = {
    'id': 'course_id',
    'name': '课程名称',
    'class_id': 'class_id',
    'start_date': '2025-09-26',
    'end_date': None,  # 课程结束时设置
    'is_active': True,
    'current_round': 1,
    'round_active': False,
    'start_time': None,
    'current_answers': {},
    'answer_times': {},
    'correct_answer': '',
    'round_results': [],
    'submissions': [],
    'students': {}  # 本课程的学生数据
}

# 学生课程数据结构
student_course_data_template = {
    'student_id': 'student_id',
    'course_id': 'course_id',
    'score': 0,  # 本课程分数
    'total_rounds': 0,  # 本课程轮次
    'correct_rounds': 0,  # 本课程正确轮次
    'expression': 'neutral',
    'animation': 'none',
    'last_answer': '',
    'last_answer_time': 0,
    'answers': []  # 本课程答题记录
}

