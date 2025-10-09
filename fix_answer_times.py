#!/usr/bin/env python3
"""
修复答题时间数据的脚本
将绝对时间戳转换为相对答题时间，并确保所有round_results都有正确的answer_time
"""

import json
import time
from datetime import datetime

def fix_answer_times():
    """修复所有课程的答题时间数据"""
    
    # 读取数据文件
    with open('app_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    courses = data.get('courses', {})
    fixed_count = 0
    
    print("开始修复答题时间数据...")
    
    for course_id, course_data in courses.items():
        course_name = course_data.get('name', '未命名课程')
        print(f"\n处理课程: {course_name} (ID: {course_id})")
        
        # 获取课程开始时间
        course_start_time = course_data.get('start_time')
        
        # 处理start_time格式
        if isinstance(course_start_time, str):
            try:
                # 尝试解析ISO格式的日期时间字符串
                dt_object = datetime.fromisoformat(course_start_time)
                course_start_time = dt_object.timestamp()
            except ValueError:
                print(f"警告: 课程 {course_id} 的 start_time 格式不正确: {course_start_time}")
                course_start_time = None
        elif course_start_time is None:
            print(f"警告: 课程 {course_id} 没有 start_time，跳过处理")
            continue
        
        round_results = course_data.get('round_results', [])
        answer_times = course_data.get('answer_times', {})
        
        if not round_results:
            print(f"课程 {course_id} 没有轮次结果，跳过")
            continue
        
        # 遍历每一轮的结果
        for round_idx, round_result in enumerate(round_results):
            results = round_result.get('results', {})
            
            # 为每个学生的结果添加或修复答题时间
            for student_id, student_result in results.items():
                current_answer_time = student_result.get('answer_time')
                
                # 如果已经有answer_time，检查是否是绝对时间戳
                if current_answer_time is not None and current_answer_time > 0:
                    # 检查是否是绝对时间戳（大于某个阈值，比如2020年的时间戳）
                    if current_answer_time > 1577836800:  # 2020-01-01 00:00:00的时间戳
                        # 这是绝对时间戳，转换为相对时间
                        relative_time = current_answer_time - course_start_time
                        if relative_time < 0:
                            relative_time = 0  # 避免负数
                        student_result['answer_time'] = relative_time
                        fixed_count += 1
                        print(f"  轮次 {round_idx + 1} 学生 {student_id}: 绝对时间戳 {current_answer_time:.2f} 转换为相对时间 {relative_time:.2f}秒")
                    else:
                        # 已经是相对时间，不需要修改
                        print(f"  轮次 {round_idx + 1} 学生 {student_id}: 答题时间 {current_answer_time:.2f}秒 (已是相对时间)")
                else:
                    # 没有answer_time，尝试从其他地方获取
                    student_answer_time = answer_times.get(student_id)
                    
                    if student_answer_time is not None:
                        # 检查是否是绝对时间戳
                        if student_answer_time > 1577836800:  # 2020-01-01 00:00:00的时间戳
                            # 这是绝对时间戳，转换为相对时间
                            relative_time = student_answer_time - course_start_time
                            if relative_time < 0:
                                relative_time = 0  # 避免负数
                            student_result['answer_time'] = relative_time
                            fixed_count += 1
                            print(f"  轮次 {round_idx + 1} 学生 {student_id}: 从answer_times获取绝对时间戳 {student_answer_time:.2f} 转换为相对时间 {relative_time:.2f}秒")
                        else:
                            # 已经是相对时间
                            student_result['answer_time'] = student_answer_time
                            fixed_count += 1
                            print(f"  轮次 {round_idx + 1} 学生 {student_id}: 从answer_times获取相对时间 {student_answer_time:.2f}秒")
                    else:
                        # 都没有，设为0
                        student_result['answer_time'] = 0
                        fixed_count += 1
                        print(f"  轮次 {round_idx + 1} 学生 {student_id}: 未找到答题时间，设为0秒")
    
    # 保存修复后的数据
    if fixed_count > 0:
        with open('app_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n修复完成！共修复了 {fixed_count} 个答题时间记录")
    else:
        print("\n没有需要修复的答题时间数据")

if __name__ == "__main__":
    fix_answer_times()