#!/usr/bin/env python3
"""
测试轮次更新修复的脚本
"""

import requests
import json

# 测试配置
BASE_URL = "https://classroom-p1f7.onrender.com"  # 替换为您的实际URL
CLASS_ID = "aa47de8e-b927-4233-99ad-c45176ca48da"  # 替换为您的班级ID

def test_get_classroom_data():
    """测试获取课堂数据"""
    print("=== 测试获取课堂数据 ===")
    
    headers = {
        'X-Class-ID': CLASS_ID
    }
    
    try:
        response = requests.get(f"{BASE_URL}/get_classroom_data", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            print(f"当前轮次: {data['current_round']}")
            print(f"学生数量: {len(data['students'])}")
            
            # 显示前几个学生的数据
            for i, (name, student_data) in enumerate(data['students'].items()):
                if i < 3:  # 只显示前3个学生
                    print(f"  {name}: 得分={student_data['score']}, 轮次={student_data['total_rounds']}, 正确={student_data['correct_rounds']}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_next_round():
    """测试下一轮功能"""
    print("\n=== 测试下一轮功能 ===")
    
    headers = {
        'X-Class-ID': CLASS_ID,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/next_round", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data['success']}")
            print(f"新轮次: {data['round']}")
            print(f"消息: {data['message']}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("开始测试轮次更新修复...")
    test_get_classroom_data()
    test_next_round()
    print("\n测试完成！")


