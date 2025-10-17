#!/usr/bin/env python3
"""
在 Render 上运行的数据库迁移脚本
通过 Flask 应用来执行数据库迁移
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# 创建 Flask 应用
app = Flask(__name__)

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+pg8000://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

@app.route('/migrate')
def migrate():
    """执行数据库迁移"""
    try:
        with app.app_context():
            # 检查并添加 status 字段
            try:
                db.engine.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'status'
                        ) THEN
                            ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active';
                        END IF;
                    END $$;
                """)
                print("status 字段检查/添加完成")
            except Exception as e:
                print(f"status 字段处理: {e}")
            
            # 检查并添加 graduated_date 字段
            try:
                db.engine.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'graduated_date'
                        ) THEN
                            ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP;
                        END IF;
                    END $$;
                """)
                print("graduated_date 字段检查/添加完成")
            except Exception as e:
                print(f"graduated_date 字段处理: {e}")
            
            # 更新现有学生状态
            try:
                result = db.engine.execute("UPDATE students SET status = 'active' WHERE status IS NULL")
                print(f"更新了 {result.rowcount} 个学生的状态")
            except Exception as e:
                print(f"更新学生状态: {e}")
            
            # 检查结果
            try:
                result = db.engine.execute("""
                    SELECT COUNT(*) as total_students, 
                           COUNT(CASE WHEN status = 'active' THEN 1 END) as active_students,
                           COUNT(CASE WHEN status = 'graduated' THEN 1 END) as graduated_students
                    FROM students
                """)
                stats = result.fetchone()
                print(f"迁移完成 - 总学生: {stats[0]}, 活跃: {stats[1]}, 已毕业: {stats[2]}")
            except Exception as e:
                print(f"检查结果: {e}")
        
        return jsonify({
            'success': True,
            'message': '数据库迁移完成',
            'stats': {
                'total_students': stats[0] if 'stats' in locals() else 0,
                'active_students': stats[1] if 'stats' in locals() else 0,
                'graduated_students': stats[2] if 'stats' in locals() else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'迁移失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("数据库迁移脚本已准备就绪")
    print("访问 /migrate 端点来执行迁移")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
