#!/usr/bin/env python3
"""
Render数据库修复脚本
专门用于修复Render平台上的PostgreSQL数据库问题
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import traceback

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 数据库配置
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    # 转换数据库URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        logger.info("已转换postgres://为postgresql+pg8000://")
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        logger.info("已转换postgresql://为postgresql+pg8000://")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fix-secret-key')
    
    return app

def fix_database():
    """修复数据库"""
    logger.info("=== 开始修复Render数据库 ===")
    
    app = create_app()
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 1. 测试数据库连接
            logger.info("1. 测试数据库连接...")
            try:
                result = db.session.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                if test_value == 1:
                    logger.info("✅ 数据库连接正常")
                else:
                    logger.error(f"❌ 数据库连接测试失败，返回值: {test_value}")
                    return False
            except Exception as e:
                logger.error(f"❌ 数据库连接失败: {str(e)}")
                return False
            
            # 2. 创建所有表
            logger.info("2. 创建所有表...")
            try:
                from models import Class, Student, Course, CourseRound, StudentSubmission, CompetitionGoal
                db.create_all()
                logger.info("✅ 所有表创建成功")
            except Exception as e:
                logger.error(f"❌ 创建表失败: {str(e)}")
                return False
            
            # 3. 添加缺失的字段
            logger.info("3. 添加缺失的字段...")
            try:
                # 添加status字段到students表
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'status'
                        ) THEN
                            ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active';
                            RAISE NOTICE 'Added status column to students table';
                        END IF;
                    END $$;
                """))
                
                # 添加graduated_date字段到students表
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'students' 
                            AND column_name = 'graduated_date'
                        ) THEN
                            ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP;
                            RAISE NOTICE 'Added graduated_date column to students table';
                        END IF;
                    END $$;
                """))
                
                # 添加goal_date字段到competition_goals表
                db.session.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'competition_goals' 
                            AND column_name = 'goal_date'
                        ) THEN
                            ALTER TABLE competition_goals ADD COLUMN goal_date DATE;
                            RAISE NOTICE 'Added goal_date column to competition_goals table';
                        END IF;
                    END $$;
                """))
                
                db.session.commit()
                logger.info("✅ 缺失字段添加成功")
            except Exception as e:
                logger.error(f"❌ 添加字段失败: {str(e)}")
                db.session.rollback()
                return False
            
            # 4. 更新现有数据
            logger.info("4. 更新现有数据...")
            try:
                # 更新学生状态
                result = db.session.execute(text("UPDATE students SET status = 'active' WHERE status IS NULL"))
                logger.info(f"✅ 更新了 {result.rowcount} 个学生的状态")
                
                # 更新竞赛目标日期
                result = db.session.execute(text("""
                    UPDATE competition_goals 
                    SET goal_date = created_date::date + INTERVAL '77 days' 
                    WHERE goal_date IS NULL
                """))
                logger.info(f"✅ 更新了 {result.rowcount} 个竞赛目标的日期")
                
                db.session.commit()
                logger.info("✅ 现有数据更新成功")
            except Exception as e:
                logger.error(f"❌ 更新数据失败: {str(e)}")
                db.session.rollback()
                return False
            
            # 5. 验证修复结果
            logger.info("5. 验证修复结果...")
            try:
                # 检查表结构
                tables = ['classes', 'students', 'courses', 'course_rounds', 'student_submissions', 'competition_goals']
                for table in tables:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    logger.info(f"✅ 表 {table}: {count} 条记录")
                
                # 检查字段
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'students' 
                    AND column_name IN ('status', 'graduated_date')
                """))
                columns = [row[0] for row in result.fetchall()]
                logger.info(f"✅ students表字段: {columns}")
                
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'competition_goals' 
                    AND column_name = 'goal_date'
                """))
                columns = [row[0] for row in result.fetchall()]
                logger.info(f"✅ competition_goals表字段: {columns}")
                
                logger.info("✅ 修复结果验证成功")
            except Exception as e:
                logger.error(f"❌ 验证修复结果失败: {str(e)}")
                return False
            
            logger.info("=== Render数据库修复完成 ===")
            return True
            
    except Exception as e:
        logger.error(f"❌ 修复过程中发生异常: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False

def check_database_status():
    """检查数据库状态"""
    logger.info("=== 检查Render数据库状态 ===")
    
    app = create_app()
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 检查连接
            result = db.session.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            logger.info(f"✅ 数据库连接正常，测试值: {test_value}")
            
            # 检查表
            tables = ['classes', 'students', 'courses', 'course_rounds', 'student_submissions', 'competition_goals']
            for table in tables:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    logger.info(f"✅ 表 {table}: {count} 条记录")
                except Exception as e:
                    logger.error(f"❌ 表 {table} 检查失败: {str(e)}")
            
            # 检查字段
            result = db.session.execute(text("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name IN ('students', 'competition_goals')
                ORDER BY table_name, ordinal_position
            """))
            
            logger.info("✅ 表字段信息:")
            for row in result.fetchall():
                logger.info(f"  {row[0]}.{row[1]} ({row[2]}) - 可空: {row[3]}")
            
            logger.info("=== 数据库状态检查完成 ===")
            return True
            
    except Exception as e:
        logger.error(f"❌ 检查数据库状态失败: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Render数据库修复工具')
    parser.add_argument('--check', action='store_true', help='只检查数据库状态，不进行修复')
    parser.add_argument('--fix', action='store_true', help='修复数据库问题')
    
    args = parser.parse_args()
    
    if args.check:
        success = check_database_status()
    elif args.fix:
        success = fix_database()
    else:
        # 默认先检查，再修复
        logger.info("默认模式：先检查状态，再修复问题")
        check_success = check_database_status()
        if check_success:
            success = fix_database()
        else:
            success = False
    
    if success:
        logger.info("🎉 操作成功完成")
        sys.exit(0)
    else:
        logger.error("💥 操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
