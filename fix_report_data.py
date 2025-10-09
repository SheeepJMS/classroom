#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复报告数据问题
解决学生名称错误和学习参与记录相同的问题
"""

import json
import os
from datetime import datetime

def fix_report_data():
    """修复报告数据问题"""
    print("开始修复报告数据问题...")
    
    # 读取数据文件
    with open('app_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取当前课程
    current_course_id = data.get('current_course')
    if not current_course_id:
        print("没有找到当前课程")
        return
    
    print(f"当前课程ID: {current_course_id}")
    
    # 获取课程数据
    course_data = data['courses'].get(current_course_id, {})
    if not course_data:
        print("没有找到课程数据")
        return
    
    print(f"课程名称: {course_data.get('name', '未知')}")
    print(f"班级ID: {course_data.get('class_id', '未知')}")
    
    # 检查学生数据
    students = course_data.get('students', {})
    print(f"学生数量: {len(students)}")
    print("学生列表:")
    for student_key, student_data in students.items():
        print(f"  - {student_key}: {student_data.get('name', '未知')}")
    
    # 检查round_results
    round_results = course_data.get('round_results', [])
    print(f"轮次结果数量: {len(round_results)}")
    
    # 检查每个轮次的学生数据
    for i, round_result in enumerate(round_results):
        print(f"第{i+1}轮结果:")
        results = round_result.get('results', {})
        for student_key, result in results.items():
            print(f"  - {student_key}: 答案={result.get('answer', '无')}, 正确={result.get('correct', False)}, 时间={result.get('answer_time', 0)}")
    
    # 检查是否有演示数据残留
    demo_students = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', '小明', '小红', '小刚', '小丽', '小华']
    found_demo_students = []
    
    for student_key, student_data in students.items():
        student_name = student_data.get('name', '')
        if student_name in demo_students:
            found_demo_students.append(student_name)
    
    if found_demo_students:
        print(f"发现演示学生: {found_demo_students}")
        print("这些可能是残留的演示数据")
    
    # 检查round_results中的学生名称
    all_students_in_rounds = set()
    for round_result in round_results:
        results = round_result.get('results', {})
        all_students_in_rounds.update(results.keys())
    
    print(f"轮次结果中的学生: {list(all_students_in_rounds)}")
    
    # 检查数据一致性
    course_students = set(students.keys())
    round_students = all_students_in_rounds
    
    if course_students != round_students:
        print("⚠️  警告：课程学生与轮次结果中的学生不一致！")
        print(f"课程学生: {course_students}")
        print(f"轮次学生: {round_students}")
        
        # 修复不一致的数据
        print("开始修复数据不一致问题...")
        
        # 移除轮次结果中不存在的学生
        for round_result in round_results:
            results = round_result.get('results', {})
            students_to_remove = []
            for student_key in results.keys():
                if student_key not in course_students:
                    students_to_remove.append(student_key)
            
            for student_key in students_to_remove:
                del results[student_key]
                print(f"  移除不存在的学生: {student_key}")
    
    # 保存修复后的数据
    with open('app_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("数据修复完成！")
    
    # 显示修复后的状态
    print("\n修复后的状态:")
    print(f"课程学生: {list(course_students)}")
    
    all_students_in_rounds_after = set()
    for round_result in round_results:
        results = round_result.get('results', {})
        all_students_in_rounds_after.update(results.keys())
    
    print(f"轮次学生: {list(all_students_in_rounds_after)}")
    
    if course_students == all_students_in_rounds_after:
        print("✅ 数据一致性已修复")
    else:
        print("❌ 数据仍然不一致，需要进一步检查")

if __name__ == '__main__':
    fix_report_data()
