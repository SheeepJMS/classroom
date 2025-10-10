#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据脚本
在部署时创建初始数据，确保应用能正常运行
"""

import json
import os
from datetime import datetime

def create_initial_data():
    """创建初始数据结构"""
    initial_data = {
        "classes": {},
        "competition_goals": {},
        "courses": {},
        "students": {},
        "current_course": None
    }
    
    return initial_data

def init_data_if_needed():
    """如果app_data.json不存在，创建初始数据"""
    data_file = 'app_data.json'
    
    if not os.path.exists(data_file):
        print("app_data.json不存在，创建初始数据...")
        initial_data = create_initial_data()
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        
        print("初始数据已创建")
    else:
        print("app_data.json已存在，跳过初始化")

if __name__ == '__main__':
    init_data_if_needed()
