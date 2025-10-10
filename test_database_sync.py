#!/usr/bin/env python3
"""
测试数据库同步问题
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append('/opt/render/project/src')

# 设置环境变量
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')
os.environ['USE_DATABASE'] = 'true'

from app import app, global_data, USE_DATABASE
from models import db, Course, Student, Class

def test_database_sync():
    """测试数据库同步问题"""
    print("=== 测试数据库同步 ===")
    print(f"USE_DATABASE: {USE_DATABASE}")
    
    with app.app_context():
        try:
            # 测试数据库连接
            print("1. 测试数据库连接...")
            db.session.execute("SELECT 1").fetchone()
            print("   ✅ 数据库连接正常")
            
            # 查找活跃课程
            print("2. 查找活跃课程...")
            active_courses = Course.query.filter_by(is_active=True).all()
            print(f"   找到 {len(active_courses)} 个活跃课程")
            
            for course in active_courses:
                print(f"   课程ID: {course.id}, 名称: {course.name}")
                
                # 查找该课程的学生
                students = Student.query.filter_by(class_id=course.class_id).all()
                print(f"   学生数量: {len(students)}")
                
                for student in students:
                    print(f"     学生: {student.name}")
                
                # 检查全局数据
                course_id_str = str(course.id)
                if course_id_str in global_data['courses']:
                    global_course_data = global_data['courses'][course_id_str]
                    print(f"   全局数据中有该课程")
                    print(f"   全局学生数据: {list(global_course_data.get('students', {}).keys())}")
                    print(f"   全局轮次: {global_course_data.get('current_round', 1)}")
                    print(f"   全局轮次结果: {len(global_course_data.get('round_results', []))}")
                else:
                    print(f"   ❌ 全局数据中没有该课程")
            
            # 检查全局数据结构
            print("3. 检查全局数据结构...")
            print(f"   全局课程数量: {len(global_data['courses'])}")
            print(f"   全局课程ID: {list(global_data['courses'].keys())}")
            
            # 测试数据保存
            print("4. 测试数据保存...")
            global_data['test_timestamp'] = datetime.now().isoformat()
            from app import save_data
            save_data()
            print("   ✅ 数据保存成功")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_database_sync()
