#!/usr/bin/env python3
"""
学生答题分数累计问题调试工具
用于诊断和修复分数无法累计的问题
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Class, Student, Course, CourseRound, StudentSubmission

class ScoringDebugger:
    def __init__(self):
        """初始化调试器"""
        self.db_url = os.environ.get('DATABASE_URL', 'sqlite:///math_homework.db')
        if self.db_url.startswith('postgres://'):
            self.db_url = self.db_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif self.db_url.startswith('postgresql://'):
            self.db_url = self.db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_database_structure(self):
        """检查数据库结构"""
        self.log("=== 检查数据库结构 ===")
        
        try:
            # 检查表是否存在
            tables = ['classes', 'students', 'courses', 'course_rounds', 'student_submissions']
            for table in tables:
                result = self.session.execute(text(f"""
                    SELECT COUNT(*) FROM {table}
                """))
                count = result.fetchone()[0]
                self.log(f"表 {table}: {count} 条记录")
                
        except Exception as e:
            self.log(f"数据库结构检查失败: {e}", "ERROR")
    
    def analyze_scoring_data(self, class_id=None):
        """分析答题数据"""
        self.log("=== 分析答题数据 ===")
        
        try:
            # 获取所有班级
            if class_id:
                classes_query = f"WHERE id = '{class_id}'"
            else:
                classes_query = ""
                
            result = self.session.execute(text(f"""
                SELECT id, name, created_date 
                FROM classes {classes_query}
                ORDER BY created_date DESC
            """))
            classes = result.fetchall()
            
            for class_row in classes:
                class_id, class_name, created_date = class_row
                self.log(f"\n班级: {class_name} (ID: {class_id})")
                
                # 获取该班级的课程
                courses_result = self.session.execute(text("""
                    SELECT id, name, is_active, created_date
                    FROM courses 
                    WHERE class_id = :class_id
                    ORDER BY created_date DESC
                """), {'class_id': class_id})
                courses = courses_result.fetchall()
                
                self.log(f"  课程数量: {len(courses)}")
                
                for course_row in courses:
                    course_id, course_name, is_active, course_created = course_row
                    self.log(f"    课程: {course_name} (活跃: {is_active})")
                    
                    # 获取该课程的轮次
                    rounds_result = self.session.execute(text("""
                        SELECT id, round_number, question_text, correct_answer, question_score, created_date
                        FROM course_rounds 
                        WHERE course_id = :course_id
                        ORDER BY round_number
                    """), {'course_id': course_id})
                    rounds = rounds_result.fetchall()
                    
                    self.log(f"      轮次数量: {len(rounds)}")
                    
                    # 分析轮次数据
                    round_numbers = [r[1] for r in rounds]
                    if round_numbers:
                        self.log(f"      轮次范围: {min(round_numbers)} - {max(round_numbers)}")
                        self.log(f"      轮次列表: {sorted(round_numbers)}")
                        
                        # 检查是否有重复轮次
                        if len(round_numbers) != len(set(round_numbers)):
                            duplicates = [x for x in round_numbers if round_numbers.count(x) > 1]
                            self.log(f"      ⚠️ 发现重复轮次: {set(duplicates)}", "WARNING")
                    
                    # 获取学生提交记录
                    submissions_result = self.session.execute(text("""
                        SELECT s.name, ss.answer, ss.is_correct, ss.answer_time, ss.submitted_at, cr.round_number
                        FROM student_submissions ss
                        JOIN students s ON ss.student_id = s.id
                        JOIN course_rounds cr ON ss.round_id = cr.id
                        WHERE cr.course_id = :course_id
                        ORDER BY s.name, cr.round_number
                    """), {'course_id': course_id})
                    submissions = submissions_result.fetchall()
                    
                    self.log(f"      提交记录数量: {len(submissions)}")
                    
                    # 按学生分组分析
                    student_data = {}
                    for sub in submissions:
                        student_name = sub[0]
                        if student_name not in student_data:
                            student_data[student_name] = []
                        student_data[student_name].append(sub)
                    
                    for student_name, student_subs in student_data.items():
                        correct_count = sum(1 for sub in student_subs if sub[2])  # is_correct
                        total_count = len(student_subs)
                        rounds_answered = [sub[5] for sub in student_subs]  # round_number
                        
                        self.log(f"        学生 {student_name}:")
                        self.log(f"          答题轮次: {sorted(rounds_answered)}")
                        self.log(f"          总提交: {total_count}, 正确: {correct_count}")
                        self.log(f"          准确率: {correct_count/total_count*100:.1f}%" if total_count > 0 else "          准确率: 0%")
                        
                        # 检查是否有重复轮次提交
                        if len(rounds_answered) != len(set(rounds_answered)):
                            self.log(f"          ⚠️ 发现重复轮次提交: {rounds_answered}", "WARNING")
                
        except Exception as e:
            self.log(f"分析答题数据失败: {e}", "ERROR")
    
    def identify_scoring_issues(self):
        """识别分数累计问题"""
        self.log("=== 识别分数累计问题 ===")
        
        issues = []
        
        try:
            # 检查是否有硬编码轮次问题
            result = self.session.execute(text("""
                SELECT course_id, COUNT(*) as round_count, 
                       COUNT(DISTINCT round_number) as unique_rounds
                FROM course_rounds 
                GROUP BY course_id
                HAVING COUNT(*) > COUNT(DISTINCT round_number)
            """))
            duplicate_rounds = result.fetchall()
            
            if duplicate_rounds:
                issues.append("发现重复轮次记录")
                for course_id, round_count, unique_rounds in duplicate_rounds:
                    self.log(f"  课程 {course_id}: 总轮次 {round_count}, 唯一轮次 {unique_rounds}", "WARNING")
            
            # 检查学生提交记录中的轮次分布
            result = self.session.execute(text("""
                SELECT s.name, c.name as course_name, 
                       COUNT(ss.id) as total_submissions,
                       COUNT(DISTINCT cr.round_number) as unique_rounds,
                       SUM(CASE WHEN ss.is_correct THEN 1 ELSE 0 END) as correct_count
                FROM student_submissions ss
                JOIN students s ON ss.student_id = s.id
                JOIN course_rounds cr ON ss.round_id = cr.id
                JOIN courses c ON cr.course_id = c.id
                GROUP BY s.id, s.name, c.id, c.name
                ORDER BY s.name, c.name
            """))
            student_stats = result.fetchall()
            
            for stat in student_stats:
                student_name, course_name, total_subs, unique_rounds, correct_count = stat
                if total_subs != unique_rounds:
                    issues.append(f"学生 {student_name} 在课程 {course_name} 中有重复轮次提交")
                    self.log(f"  学生 {student_name} ({course_name}): 总提交 {total_subs}, 唯一轮次 {unique_rounds}", "WARNING")
            
            # 检查轮次编号是否连续
            result = self.session.execute(text("""
                SELECT course_id, round_number
                FROM course_rounds
                ORDER BY course_id, round_number
            """))
            rounds = result.fetchall()
            
            current_course = None
            expected_round = 1
            for course_id, round_number in rounds:
                if current_course != course_id:
                    current_course = course_id
                    expected_round = 1
                
                if round_number != expected_round:
                    issues.append(f"课程 {course_id} 轮次编号不连续: 期望 {expected_round}, 实际 {round_number}")
                    self.log(f"  课程 {course_id}: 轮次编号不连续", "WARNING")
                
                expected_round += 1
            
            if not issues:
                self.log("未发现明显的分数累计问题", "SUCCESS")
            else:
                self.log(f"发现 {len(issues)} 个问题:", "ERROR")
                for i, issue in enumerate(issues, 1):
                    self.log(f"  {i}. {issue}", "ERROR")
                    
        except Exception as e:
            self.log(f"识别问题失败: {e}", "ERROR")
        
        return issues
    
    def fix_scoring_issues(self, class_id=None):
        """修复分数累计问题"""
        self.log("=== 修复分数累计问题 ===")
        
        try:
            # 1. 修复重复轮次问题
            self.log("1. 修复重复轮次问题...")
            
            # 获取有重复轮次的课程
            result = self.session.execute(text("""
                SELECT course_id, round_number, COUNT(*) as count
                FROM course_rounds
                GROUP BY course_id, round_number
                HAVING COUNT(*) > 1
            """))
            duplicate_rounds = result.fetchall()
            
            for course_id, round_number, count in duplicate_rounds:
                self.log(f"  修复课程 {course_id} 轮次 {round_number} 的 {count} 个重复记录")
                
                # 保留第一个，删除其他的
                result = self.session.execute(text("""
                    SELECT id FROM course_rounds 
                    WHERE course_id = :course_id AND round_number = :round_number
                    ORDER BY created_date
                """), {'course_id': course_id, 'round_number': round_number})
                round_ids = [row[0] for row in result.fetchall()]
                
                if len(round_ids) > 1:
                    # 删除除第一个之外的所有记录
                    ids_to_delete = round_ids[1:]
                    for round_id in ids_to_delete:
                        # 先删除相关的学生提交记录
                        self.session.execute(text("""
                            DELETE FROM student_submissions WHERE round_id = :round_id
                        """), {'round_id': round_id})
                        
                        # 删除轮次记录
                        self.session.execute(text("""
                            DELETE FROM course_rounds WHERE id = :round_id
                        """), {'round_id': round_id})
            
            # 2. 重新编号轮次
            self.log("2. 重新编号轮次...")
            
            result = self.session.execute(text("""
                SELECT DISTINCT course_id FROM course_rounds ORDER BY course_id
            """))
            courses = [row[0] for row in result.fetchall()]
            
            for course_id in courses:
                self.log(f"  重新编号课程 {course_id} 的轮次")
                
                # 获取该课程的所有轮次，按创建时间排序
                result = self.session.execute(text("""
                    SELECT id, round_number FROM course_rounds 
                    WHERE course_id = :course_id
                    ORDER BY created_date
                """), {'course_id': course_id})
                rounds = result.fetchall()
                
                # 重新编号
                for new_number, (round_id, old_number) in enumerate(rounds, 1):
                    if new_number != old_number:
                        self.log(f"    轮次 {old_number} -> {new_number}")
                        self.session.execute(text("""
                            UPDATE course_rounds 
                            SET round_number = :new_number 
                            WHERE id = :round_id
                        """), {'new_number': new_number, 'round_id': round_id})
            
            # 3. 验证修复结果
            self.log("3. 验证修复结果...")
            self.session.commit()
            
            # 重新分析数据
            self.analyze_scoring_data(class_id)
            
            self.log("修复完成！", "SUCCESS")
            
        except Exception as e:
            self.log(f"修复失败: {e}", "ERROR")
            self.session.rollback()
    
    def generate_debug_report(self, class_id=None):
        """生成调试报告"""
        self.log("=== 生成调试报告 ===")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_url": self.db_url,
            "issues_found": [],
            "recommendations": []
        }
        
        # 检查数据库结构
        self.check_database_structure()
        
        # 分析数据
        self.analyze_scoring_data(class_id)
        
        # 识别问题
        issues = self.identify_scoring_issues()
        report["issues_found"] = issues
        
        # 生成建议
        if issues:
            report["recommendations"] = [
                "运行 fix_scoring_issues() 修复重复轮次问题",
                "检查前端轮次管理逻辑",
                "确保每次答题都创建新的轮次记录",
                "验证学生提交记录的唯一性约束"
            ]
        else:
            report["recommendations"] = [
                "系统运行正常，无需修复",
                "建议定期运行此调试工具监控数据质量"
            ]
        
        # 保存报告
        report_file = f"scoring_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"调试报告已保存到: {report_file}")
        
        return report
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='学生答题分数累计问题调试工具')
    parser.add_argument('--class-id', help='指定班级ID进行分析')
    parser.add_argument('--fix', action='store_true', help='自动修复发现的问题')
    parser.add_argument('--report', action='store_true', help='生成调试报告')
    
    args = parser.parse_args()
    
    debugger = ScoringDebugger()
    
    try:
        if args.report:
            debugger.generate_debug_report(args.class_id)
        else:
            debugger.check_database_structure()
            debugger.analyze_scoring_data(args.class_id)
            debugger.identify_scoring_issues()
            
            if args.fix:
                debugger.fix_scoring_issues(args.class_id)
    
    finally:
        debugger.close()

if __name__ == "__main__":
    main()
