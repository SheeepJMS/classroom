#!/usr/bin/env python3
"""
修复Git合并冲突标记
"""

def fix_git_conflicts(file_path):
    """修复文件中的Git合并冲突标记"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    skip_until_end = False
    
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            skip_until_end = True
            continue
        elif line.startswith('======='):
            continue
        elif line.startswith('>>>>>>> '):
            skip_until_end = False
            continue
        elif not skip_until_end:
            fixed_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"已修复 {file_path} 中的Git合并冲突标记")

if __name__ == "__main__":
    fix_git_conflicts('app.py')
