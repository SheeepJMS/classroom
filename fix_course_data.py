#!/usr/bin/env python3
"""
修复课程数据和答题时间的脚本
"""

import json
import time
from datetime import datetime

def fix_course_data():
    """修复课程数据和答题时间"""
    
    # 读取数据文件
    with open('app_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("开始修复课程数据...")
    
    # 获取当前课程ID
    current_course_id = data.get('current_course')
    print(f"当前课程ID: {current_course_id}")
    
    if current_course_id and current_course_id in data.get('courses', {}):
        course_data = data['courses'][current_course_id]
        print(f"当前课程名称: '{course_data.get('name', '')}'")
        
        # 如果课程名称为空，设置一个默认名称
        if not course_data.get('name', '').strip():
            new_name = input("请输入正确的课程名称: ").strip()
            if new_name:
                course_data['name'] = new_name
                print(f"课程名称已更新为: '{new_name}'")
            else:
                course_data['name'] = "数学课堂"
                print("使用默认名称: '数学课堂'")
        
        # 修复答题时间
        course_start_time = course_data.get('start_time')
        
        # 处理start_time格式
        if isinstance(course_start_time, str):
            try:
                dt_object = datetime.fromisoformat(course_start_time)
                course_start_time = dt_object.timestamp()
            except ValueError:
                print(f"警告: 课程的 start_time 格式不正确: {course_start_time}")
                course_start_time = None
        
        if course_start_time and course_start_time > 0:
            round_results = course_data.get('round_results', [])
            fixed_count = 0
            
            for round_idx, round_result in enumerate(round_results):
                results = round_result.get('results', {})
                
                for student_id, student_result in results.items():
                    current_answer_time = student_result.get('answer_time')
                    
                    # 如果answer_time是绝对时间戳，转换为相对时间
                    if current_answer_time and current_answer_time > 1577836800:  # 2020年的时间戳
                        relative_time = current_answer_time - course_start_time
                        if relative_time < 0:
                            relative_time = 0
                        student_result['answer_time'] = relative_time
                        fixed_count += 1
                        print(f"  轮次 {round_idx + 1} 学生 {student_id}: 答题时间从 {current_answer_time:.2f} 转换为 {relative_time:.2f}秒")
            
            print(f"修复了 {fixed_count} 个答题时间记录")
        else:
            print("警告: 课程没有有效的start_time，无法修复答题时间")
    
    # 保存修复后的数据
    with open('app_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("修复完成！")

if __name__ == "__main__":
    fix_course_data()
