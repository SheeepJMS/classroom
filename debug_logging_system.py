#!/usr/bin/env python3
"""
增强的调试日志系统
用于实时监控学生答题数据流
"""

import logging
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, g
import traceback

class ScoringDebugLogger:
    """分数调试日志记录器"""
    
    def __init__(self, log_file="scoring_debug.log"):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志记录器
        self.logger = logging.getLogger('scoring_debug')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_request(self, endpoint, data=None):
        """记录请求"""
        self.logger.info(f"=== 请求开始: {endpoint} ===")
        self.logger.info(f"请求方法: {request.method}")
        self.logger.info(f"请求URL: {request.url}")
        self.logger.info(f"请求头: {dict(request.headers)}")
        
        if data:
            self.logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def log_response(self, endpoint, response_data):
        """记录响应"""
        self.logger.info(f"=== 响应: {endpoint} ===")
        self.logger.info(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    
    def log_database_operation(self, operation, table, data=None):
        """记录数据库操作"""
        self.logger.debug(f"数据库操作: {operation} 表: {table}")
        if data:
            self.logger.debug(f"操作数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def log_scoring_event(self, event_type, student_name, round_number, details=None):
        """记录分数相关事件"""
        self.logger.info(f"分数事件: {event_type}")
        self.logger.info(f"  学生: {student_name}")
        self.logger.info(f"  轮次: {round_number}")
        if details:
            self.logger.info(f"  详情: {json.dumps(details, ensure_ascii=False, indent=2)}")
    
    def log_error(self, error, context=None):
        """记录错误"""
        self.logger.error(f"错误发生: {str(error)}")
        if context:
            self.logger.error(f"上下文: {context}")
        self.logger.error(f"堆栈跟踪: {traceback.format_exc()}")

# 全局调试日志记录器实例
debug_logger = ScoringDebugLogger()

def debug_log(endpoint_name):
    """调试日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 记录请求开始
                request_data = None
                if request.is_json:
                    request_data = request.get_json()
                
                debug_logger.log_request(endpoint_name, request_data)
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录响应
                if hasattr(result, 'get_json'):
                    response_data = result.get_json()
                else:
                    response_data = str(result)
                
                debug_logger.log_response(endpoint_name, response_data)
                
                return result
                
            except Exception as e:
                debug_logger.log_error(e, f"在 {endpoint_name} 中")
                raise
        
        return wrapper
    return decorator

def log_scoring_flow(student_name, round_number, event_type, details=None):
    """记录分数流程"""
    debug_logger.log_scoring_event(event_type, student_name, round_number, details)

def log_database_query(operation, table, query_data=None):
    """记录数据库查询"""
    debug_logger.log_database_operation(operation, table, query_data)

# 数据库操作监控
class DatabaseMonitor:
    """数据库操作监控器"""
    
    def __init__(self):
        self.operations = []
    
    def log_operation(self, operation_type, table_name, data=None, result=None):
        """记录数据库操作"""
        operation = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'table': table_name,
            'data': data,
            'result': result
        }
        self.operations.append(operation)
        
        # 记录到调试日志
        log_database_query(operation_type, table_name, data)
    
    def get_operations_summary(self):
        """获取操作摘要"""
        summary = {}
        for op in self.operations:
            key = f"{op['type']}_{op['table']}"
            if key not in summary:
                summary[key] = 0
            summary[key] += 1
        return summary
    
    def clear_operations(self):
        """清除操作记录"""
        self.operations.clear()

# 全局数据库监控器
db_monitor = DatabaseMonitor()

# 分数计算验证器
class ScoreValidator:
    """分数计算验证器"""
    
    @staticmethod
    def validate_round_data(course_id, round_number):
        """验证轮次数据"""
        from models import CourseRound, StudentSubmission
        
        # 检查轮次是否存在
        round_obj = CourseRound.query.filter_by(
            course_id=course_id, 
            round_number=round_number
        ).first()
        
        if not round_obj:
            debug_logger.logger.warning(f"轮次不存在: 课程 {course_id}, 轮次 {round_number}")
            return False
        
        # 检查学生提交记录
        submissions = StudentSubmission.query.filter_by(round_id=round_obj.id).all()
        
        debug_logger.logger.info(f"轮次 {round_number} 有 {len(submissions)} 个学生提交")
        
        for submission in submissions:
            student = submission.student_ref
            debug_logger.logger.info(
                f"  学生 {student.name}: 答案={submission.answer}, "
                f"正确={submission.is_correct}, 时间={submission.answer_time}"
            )
        
        return True
    
    @staticmethod
    def calculate_student_total_score(student_id, course_id):
        """计算学生总分数"""
        from models import StudentSubmission, CourseRound
        
        # 获取学生在指定课程中的所有提交记录
        submissions = StudentSubmission.query.join(CourseRound).filter(
            StudentSubmission.student_id == student_id,
            CourseRound.course_id == course_id
        ).all()
        
        total_score = 0
        correct_count = 0
        total_rounds = len(submissions)
        
        for submission in submissions:
            if submission.is_correct:
                # 获取轮次分数
                round_obj = CourseRound.query.get(submission.round_id)
                if round_obj and round_obj.question_score:
                    total_score += round_obj.question_score
                else:
                    total_score += 1  # 默认分数
                correct_count += 1
        
        result = {
            'student_id': student_id,
            'course_id': course_id,
            'total_score': total_score,
            'correct_count': correct_count,
            'total_rounds': total_rounds,
            'accuracy': (correct_count / total_rounds * 100) if total_rounds > 0 else 0
        }
        
        debug_logger.logger.info(f"学生分数计算: {json.dumps(result, ensure_ascii=False)}")
        
        return result
    
    @staticmethod
    def validate_course_rounds(course_id):
        """验证课程轮次"""
        from models import CourseRound
        
        rounds = CourseRound.query.filter_by(course_id=course_id).order_by(
            CourseRound.round_number
        ).all()
        
        debug_logger.logger.info(f"课程 {course_id} 有 {len(rounds)} 个轮次")
        
        issues = []
        expected_round = 1
        
        for round_obj in rounds:
            if round_obj.round_number != expected_round:
                issues.append(f"轮次编号不连续: 期望 {expected_round}, 实际 {round_obj.round_number}")
            
            debug_logger.logger.info(
                f"  轮次 {round_obj.round_number}: "
                f"题目='{round_obj.question_text}', "
                f"答案='{round_obj.correct_answer}', "
                f"分数={round_obj.question_score}"
            )
            
            expected_round += 1
        
        if issues:
            debug_logger.logger.warning(f"发现轮次问题: {issues}")
        
        return len(issues) == 0

# 实时监控器
class RealTimeMonitor:
    """实时监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.events = []
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        debug_logger.logger.info("开始实时监控学生答题数据")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        debug_logger.logger.info("停止实时监控")
    
    def log_event(self, event_type, data):
        """记录事件"""
        if self.monitoring:
            event = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': data
            }
            self.events.append(event)
            
            debug_logger.logger.info(f"监控事件: {event_type}")
            debug_logger.logger.info(f"事件数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def get_events_summary(self):
        """获取事件摘要"""
        summary = {}
        for event in self.events:
            event_type = event['type']
            if event_type not in summary:
                summary[event_type] = 0
            summary[event_type] += 1
        return summary

# 全局实时监控器
realtime_monitor = RealTimeMonitor()

# 调试工具函数
def debug_scoring_system():
    """调试分数系统"""
    debug_logger.logger.info("=== 开始调试分数系统 ===")
    
    try:
        from models import db, Class, Student, Course, CourseRound, StudentSubmission
        
        # 1. 检查数据库连接
        debug_logger.logger.info("1. 检查数据库连接...")
        result = db.session.execute(db.text("SELECT 1"))
        debug_logger.logger.info("数据库连接正常")
        
        # 2. 检查表结构
        debug_logger.logger.info("2. 检查表结构...")
        tables = ['classes', 'students', 'courses', 'course_rounds', 'student_submissions']
        for table in tables:
            try:
                result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                debug_logger.logger.info(f"表 {table}: {count} 条记录")
            except Exception as e:
                debug_logger.logger.error(f"检查表 {table} 失败: {e}")
        
        # 3. 检查活跃课程
        debug_logger.logger.info("3. 检查活跃课程...")
        active_courses = Course.query.filter_by(is_active=True).all()
        debug_logger.logger.info(f"活跃课程数量: {len(active_courses)}")
        
        for course in active_courses:
            debug_logger.logger.info(f"  课程: {course.name} (ID: {course.id})")
            
            # 检查轮次
            rounds = CourseRound.query.filter_by(course_id=course.id).all()
            debug_logger.logger.info(f"    轮次数量: {len(rounds)}")
            
            # 检查学生提交
            submissions = StudentSubmission.query.join(CourseRound).filter(
                CourseRound.course_id == course.id
            ).all()
            debug_logger.logger.info(f"    提交记录数量: {len(submissions)}")
        
        # 4. 验证分数计算
        debug_logger.logger.info("4. 验证分数计算...")
        for course in active_courses:
            ScoreValidator.validate_course_rounds(course.id)
            
            # 获取该课程的学生
            students = Student.query.filter_by(class_id=course.class_id).all()
            for student in students:
                ScoreValidator.calculate_student_total_score(student.id, course.id)
        
        debug_logger.logger.info("=== 分数系统调试完成 ===")
        
    except Exception as e:
        debug_logger.log_error(e, "调试分数系统时")
        raise

def export_debug_data():
    """导出调试数据"""
    debug_logger.logger.info("=== 导出调试数据 ===")
    
    try:
        from models import db, Class, Student, Course, CourseRound, StudentSubmission
        
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'classes': [],
            'courses': [],
            'rounds': [],
            'submissions': [],
            'students': []
        }
        
        # 导出班级数据
        classes = Class.query.all()
        for cls in classes:
            debug_data['classes'].append({
                'id': cls.id,
                'name': cls.name,
                'created_date': cls.created_date.isoformat() if cls.created_date else None
            })
        
        # 导出课程数据
        courses = Course.query.all()
        for course in courses:
            debug_data['courses'].append({
                'id': course.id,
                'name': course.name,
                'class_id': course.class_id,
                'is_active': course.is_active,
                'created_date': course.created_date.isoformat() if course.created_date else None
            })
        
        # 导出轮次数据
        rounds = CourseRound.query.all()
        for round_obj in rounds:
            debug_data['rounds'].append({
                'id': round_obj.id,
                'course_id': round_obj.course_id,
                'round_number': round_obj.round_number,
                'question_text': round_obj.question_text,
                'correct_answer': round_obj.correct_answer,
                'question_score': round_obj.question_score,
                'created_date': round_obj.created_date.isoformat() if round_obj.created_date else None
            })
        
        # 导出学生数据
        students = Student.query.all()
        for student in students:
            debug_data['students'].append({
                'id': student.id,
                'name': student.name,
                'class_id': student.class_id,
                'created_date': student.created_date.isoformat() if student.created_date else None
            })
        
        # 导出提交记录
        submissions = StudentSubmission.query.all()
        for submission in submissions:
            debug_data['submissions'].append({
                'id': submission.id,
                'student_id': submission.student_id,
                'round_id': submission.round_id,
                'answer': submission.answer,
                'is_correct': submission.is_correct,
                'answer_time': submission.answer_time,
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
            })
        
        # 保存到文件
        filename = f"debug_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)
        
        debug_logger.logger.info(f"调试数据已导出到: {filename}")
        
        return filename
        
    except Exception as e:
        debug_logger.log_error(e, "导出调试数据时")
        raise

if __name__ == "__main__":
    # 测试调试系统
    debug_scoring_system()
    export_debug_data()
