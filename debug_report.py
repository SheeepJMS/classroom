#!/usr/bin/env python3
"""
调试报告数据的脚本
"""

import json

def debug_report_data():
    """调试报告数据"""
    
    # 读取数据文件
    with open('app_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取当前课程
    current_course_id = data.get('current_course')
    print(f"当前课程ID: {current_course_id}")
    
    if current_course_id and current_course_id in data.get('courses', {}):
        course_data = data['courses'][current_course_id]
        print(f"课程名称: {course_data.get('name', '')}")
        
        # 查看学生数据
        students = course_data.get('students', {})
        print(f"\n学生列表: {list(students.keys())}")
        
        for student_id, student_data in students.items():
            print(f"\n学生 {student_id}:")
            print(f"  名称: {student_data.get('name', '')}")
            print(f"  最后答题时间: {student_data.get('last_answer_time', 0)}")
        
        # 查看round_results
        round_results = course_data.get('round_results', [])
        print(f"\n轮次结果数量: {len(round_results)}")
        
        for i, round_result in enumerate(round_results):
            print(f"\n轮次 {i + 1}:")
            results = round_result.get('results', {})
            for student_id, result in results.items():
                answer_time = result.get('answer_time', 0)
                print(f"  学生 {student_id}: 答题时间 {answer_time}秒")

if __name__ == "__main__":
    debug_report_data()