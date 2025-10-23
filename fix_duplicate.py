#!/usr/bin/env python3
"""
删除重复的generate_report函数
"""

def fix_duplicate_functions(file_path):
    """删除重复的generate_report函数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到第一个generate_report函数的位置
    first_start = -1
    first_end = -1
    second_start = -1
    
    for i, line in enumerate(lines):
        if line.strip() == "@app.route('/reports/<course_id>')":
            if first_start == -1:
                first_start = i
            else:
                second_start = i
                break
    
    # 找到第一个函数的结束位置（下一个@app.route）
    for i in range(first_start + 1, len(lines)):
        if lines[i].strip().startswith('@app.route'):
            first_end = i
            break
    
    if first_start != -1 and first_end != -1 and second_start != -1:
        # 删除第一个函数
        new_lines = lines[:first_start] + lines[first_end:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"已删除重复的generate_report函数 (行 {first_start+1}-{first_end})")
    else:
        print("未找到重复的函数")

if __name__ == "__main__":
    fix_duplicate_functions('app.py')
