#!/usr/bin/env python3
"""
Render数据库调试工具
专门用于调试Render平台上的PostgreSQL数据库连接和操作问题
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
import json

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RenderDatabaseDebugger:
    """Render数据库调试器"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.db = SQLAlchemy()
        self.setup_app()
        self.setup_routes()
    
    def setup_app(self):
        """设置Flask应用"""
        # 获取数据库URL
        self.database_url = os.environ.get('DATABASE_URL')
        logger.info(f"原始DATABASE_URL: {self.database_url}")
        
        if not self.database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return
        
        # 转换数据库URL格式
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql+pg8000://', 1)
            logger.info("已转换postgres://为postgresql+pg8000://")
        elif self.database_url.startswith('postgresql://'):
            self.database_url = self.database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
            logger.info("已转换postgresql://为postgresql+pg8000://")
        
        logger.info(f"最终DATABASE_URL: {self.database_url}")
        
        # 配置Flask应用
        self.app.config['SQLALCHEMY_DATABASE_URI'] = self.database_url
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-secret-key')
        
        # 初始化数据库
        self.db.init_app(self.app)
        
        logger.info("Flask应用和数据库初始化完成")
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            """调试主页"""
            return render_template('render_debug.html')
        
        @self.app.route('/debug/connection')
        def debug_connection():
            """测试数据库连接"""
            try:
                logger.info("开始测试数据库连接...")
                
                with self.app.app_context():
                    # 测试基本连接
                    result = self.db.session.execute(text("SELECT 1 as test"))
                    test_value = result.fetchone()[0]
                    
                    if test_value == 1:
                        logger.info("数据库连接测试成功")
                        return jsonify({
                            'success': True,
                            'message': '数据库连接正常',
                            'test_value': test_value,
                            'database_url': self.database_url[:50] + '...' if len(self.database_url) > 50 else self.database_url
                        })
                    else:
                        logger.error(f"数据库连接测试失败，返回值: {test_value}")
                        return jsonify({
                            'success': False,
                            'message': f'数据库连接测试失败，返回值: {test_value}'
                        })
                        
            except Exception as e:
                logger.error(f"数据库连接测试异常: {str(e)}")
                logger.error(f"异常详情: {traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'message': f'数据库连接异常: {str(e)}',
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })
        
        @self.app.route('/debug/tables')
        def debug_tables():
            """检查数据库表结构"""
            try:
                logger.info("开始检查数据库表结构...")
                
                with self.app.app_context():
                    # 获取所有表
                    result = self.db.session.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """))
                    tables = [row[0] for row in result.fetchall()]
                    
                    logger.info(f"找到 {len(tables)} 个表: {tables}")
                    
                    # 检查每个表的结构
                    table_info = {}
                    for table in tables:
                        # 获取表结构
                        columns_result = self.db.session.execute(text("""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns
                            WHERE table_name = :table_name
                            ORDER BY ordinal_position
                        """), {'table_name': table})
                        
                        columns = []
                        for col in columns_result.fetchall():
                            columns.append({
                                'name': col[0],
                                'type': col[1],
                                'nullable': col[2],
                                'default': col[3]
                            })
                        
                        # 获取表记录数
                        count_result = self.db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        record_count = count_result.fetchone()[0]
                        
                        table_info[table] = {
                            'columns': columns,
                            'record_count': record_count
                        }
                    
                    return jsonify({
                        'success': True,
                        'tables': tables,
                        'table_info': table_info
                    })
                    
            except Exception as e:
                logger.error(f"检查表结构异常: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'检查表结构异常: {str(e)}',
                    'error_type': type(e).__name__
                })
        
        @self.app.route('/debug/data')
        def debug_data():
            """检查数据内容"""
            try:
                logger.info("开始检查数据内容...")
                
                with self.app.app_context():
                    data_info = {}
                    
                    # 检查各个表的数据
                    tables_to_check = ['classes', 'students', 'courses', 'course_rounds', 'student_submissions']
                    
                    for table in tables_to_check:
                        try:
                            # 检查表是否存在
                            exists_result = self.db.session.execute(text("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public' 
                                    AND table_name = :table_name
                                )
                            """), {'table_name': table})
                            
                            if exists_result.fetchone()[0]:
                                # 获取记录数
                                count_result = self.db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                                count = count_result.fetchone()[0]
                                
                                # 获取最新记录
                                if count > 0:
                                    latest_result = self.db.session.execute(text(f"""
                                        SELECT * FROM {table} 
                                        ORDER BY created_date DESC 
                                        LIMIT 3
                                    """))
                                    latest_records = []
                                    for row in latest_result.fetchall():
                                        latest_records.append(dict(row._mapping))
                                else:
                                    latest_records = []
                                
                                data_info[table] = {
                                    'exists': True,
                                    'count': count,
                                    'latest_records': latest_records
                                }
                            else:
                                data_info[table] = {
                                    'exists': False,
                                    'count': 0,
                                    'latest_records': []
                                }
                                
                        except Exception as e:
                            data_info[table] = {
                                'exists': False,
                                'error': str(e)
                            }
                    
                    return jsonify({
                        'success': True,
                        'data_info': data_info
                    })
                    
            except Exception as e:
                logger.error(f"检查数据内容异常: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'检查数据内容异常: {str(e)}',
                    'error_type': type(e).__name__
                })
        
        @self.app.route('/debug/test_operations')
        def debug_test_operations():
            """测试数据库操作"""
            try:
                logger.info("开始测试数据库操作...")
                
                with self.app.app_context():
                    test_results = []
                    
                    # 测试1: 创建测试表
                    try:
                        self.db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS debug_test (
                                id SERIAL PRIMARY KEY,
                                test_data VARCHAR(100),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        self.db.session.commit()
                        test_results.append({'test': '创建测试表', 'result': '成功'})
                    except Exception as e:
                        test_results.append({'test': '创建测试表', 'result': f'失败: {str(e)}'})
                    
                    # 测试2: 插入测试数据
                    try:
                        self.db.session.execute(text("""
                            INSERT INTO debug_test (test_data) 
                            VALUES (:test_data)
                        """), {'test_data': f'测试数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}'})
                        self.db.session.commit()
                        test_results.append({'test': '插入测试数据', 'result': '成功'})
                    except Exception as e:
                        test_results.append({'test': '插入测试数据', 'result': f'失败: {str(e)}'})
                    
                    # 测试3: 查询测试数据
                    try:
                        result = self.db.session.execute(text("SELECT COUNT(*) FROM debug_test"))
                        count = result.fetchone()[0]
                        test_results.append({'test': '查询测试数据', 'result': f'成功，记录数: {count}'})
                    except Exception as e:
                        test_results.append({'test': '查询测试数据', 'result': f'失败: {str(e)}'})
                    
                    # 测试4: 删除测试表
                    try:
                        self.db.session.execute(text("DROP TABLE IF EXISTS debug_test"))
                        self.db.session.commit()
                        test_results.append({'test': '删除测试表', 'result': '成功'})
                    except Exception as e:
                        test_results.append({'test': '删除测试表', 'result': f'失败: {str(e)}'})
                    
                    return jsonify({
                        'success': True,
                        'test_results': test_results
                    })
                    
            except Exception as e:
                logger.error(f"测试数据库操作异常: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'测试数据库操作异常: {str(e)}',
                    'error_type': type(e).__name__
                })
        
        @self.app.route('/debug/environment')
        def debug_environment():
            """检查环境变量"""
            try:
                logger.info("开始检查环境变量...")
                
                env_vars = {
                    'DATABASE_URL': os.environ.get('DATABASE_URL', '未设置'),
                    'SECRET_KEY': os.environ.get('SECRET_KEY', '未设置'),
                    'USE_DATABASE': os.environ.get('USE_DATABASE', '未设置'),
                    'PYTHON_VERSION': os.environ.get('PYTHON_VERSION', '未设置'),
                    'RENDER': os.environ.get('RENDER', '未设置'),
                    'RENDER_SERVICE_NAME': os.environ.get('RENDER_SERVICE_NAME', '未设置'),
                    'RENDER_SERVICE_TYPE': os.environ.get('RENDER_SERVICE_TYPE', '未设置'),
                }
                
                # 检查是否在Render环境
                is_render = os.environ.get('RENDER') is not None
                
                return jsonify({
                    'success': True,
                    'is_render': is_render,
                    'environment_variables': env_vars,
                    'python_version': sys.version,
                    'working_directory': os.getcwd(),
                    'files_in_directory': os.listdir('.')
                })
                
            except Exception as e:
                logger.error(f"检查环境变量异常: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'检查环境变量异常: {str(e)}',
                    'error_type': type(e).__name__
                })
        
        @self.app.route('/debug/fix_database')
        def debug_fix_database():
            """修复数据库问题"""
            try:
                logger.info("开始修复数据库问题...")
                
                with self.app.app_context():
                    fix_results = []
                    
                    # 修复1: 确保所有表存在
                    try:
                        from models import Class, Student, Course, CourseRound, StudentSubmission, CompetitionGoal
                        self.db.create_all()
                        fix_results.append({'fix': '创建所有表', 'result': '成功'})
                    except Exception as e:
                        fix_results.append({'fix': '创建所有表', 'result': f'失败: {str(e)}'})
                    
                    # 修复2: 添加缺失的字段
                    try:
                        # 检查并添加status字段
                        self.db.session.execute(text("""
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
                        """))
                        
                        # 检查并添加graduated_date字段
                        self.db.session.execute(text("""
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
                        """))
                        
                        # 检查并添加goal_date字段
                        self.db.session.execute(text("""
                            DO $$ 
                            BEGIN
                                IF NOT EXISTS (
                                    SELECT 1 FROM information_schema.columns 
                                    WHERE table_schema = 'public' 
                                    AND table_name = 'competition_goals' 
                                    AND column_name = 'goal_date'
                                ) THEN
                                    ALTER TABLE competition_goals ADD COLUMN goal_date DATE;
                                END IF;
                            END $$;
                        """))
                        
                        self.db.session.commit()
                        fix_results.append({'fix': '添加缺失字段', 'result': '成功'})
                    except Exception as e:
                        fix_results.append({'fix': '添加缺失字段', 'result': f'失败: {str(e)}'})
                    
                    # 修复3: 更新现有数据
                    try:
                        # 更新学生状态
                        self.db.session.execute(text("UPDATE students SET status = 'active' WHERE status IS NULL"))
                        
                        # 更新竞赛目标日期
                        self.db.session.execute(text("""
                            UPDATE competition_goals 
                            SET goal_date = created_date::date + INTERVAL '77 days' 
                            WHERE goal_date IS NULL
                        """))
                        
                        self.db.session.commit()
                        fix_results.append({'fix': '更新现有数据', 'result': '成功'})
                    except Exception as e:
                        fix_results.append({'fix': '更新现有数据', 'result': f'失败: {str(e)}'})
                    
                    return jsonify({
                        'success': True,
                        'fix_results': fix_results
                    })
                    
            except Exception as e:
                logger.error(f"修复数据库异常: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'修复数据库异常: {str(e)}',
                    'error_type': type(e).__name__
                })
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """运行调试服务器"""
        logger.info(f"启动Render数据库调试服务器: {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函数"""
    debugger = RenderDatabaseDebugger()
    
    # 获取端口
    port = int(os.environ.get('PORT', 5000))
    
    # 运行调试服务器
    debugger.run(port=port, debug=False)

if __name__ == "__main__":
    main()
