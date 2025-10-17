#!/usr/bin/env python3
"""
直接在 Render 上运行数据库迁移
"""

import os
import psycopg2
from urllib.parse import urlparse

def migrate_database():
    """执行数据库迁移"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("错误: 未找到 DATABASE_URL 环境变量")
        return False
    
    # 解析数据库URL
    url = urlparse(DATABASE_URL)
    
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # 移除开头的 '/'
            user=url.username,
            password=url.password
        )
        
        cur = conn.cursor()
        
        # 检查并添加 status 字段
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'students' 
                AND column_name = 'status'
            );
        """)
        
        if not cur.fetchone()[0]:
            print("添加 status 字段...")
            cur.execute("ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
            print("status 字段添加成功")
        else:
            print("status 字段已存在")
        
        # 检查并添加 graduated_date 字段
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'students' 
                AND column_name = 'graduated_date'
            );
        """)
        
        if not cur.fetchone()[0]:
            print("添加 graduated_date 字段...")
            cur.execute("ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP")
            print("graduated_date 字段添加成功")
        else:
            print("graduated_date 字段已存在")
        
        # 更新现有学生状态
        cur.execute("UPDATE students SET status = 'active' WHERE status IS NULL")
        updated_count = cur.rowcount
        print(f"更新了 {updated_count} 个学生的状态")
        
        # 提交更改
        conn.commit()
        
        # 检查结果
        cur.execute("""
            SELECT COUNT(*) as total_students, 
                   COUNT(CASE WHEN status = 'active' THEN 1 END) as active_students,
                   COUNT(CASE WHEN status = 'graduated' THEN 1 END) as graduated_students
            FROM students
        """)
        
        stats = cur.fetchone()
        print(f"迁移完成 - 总学生: {stats[0]}, 活跃: {stats[1]}, 已毕业: {stats[2]}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == '__main__':
    print("开始数据库迁移...")
    success = migrate_database()
    if success:
        print("迁移成功完成！")
    else:
        print("迁移失败！")
