-- Render 数据库迁移 SQL 脚本
-- 在 Render 的数据库控制台中运行这些 SQL 语句

-- 1. 添加 status 字段
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'students' 
        AND column_name = 'status'
    ) THEN
        ALTER TABLE students ADD COLUMN status VARCHAR(20) DEFAULT 'active';
        RAISE NOTICE 'status 字段添加成功';
    ELSE
        RAISE NOTICE 'status 字段已存在';
    END IF;
END $$;

-- 2. 添加 graduated_date 字段
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'students' 
        AND column_name = 'graduated_date'
    ) THEN
        ALTER TABLE students ADD COLUMN graduated_date TIMESTAMP;
        RAISE NOTICE 'graduated_date 字段添加成功';
    ELSE
        RAISE NOTICE 'graduated_date 字段已存在';
    END IF;
END $$;

-- 3. 更新现有学生的状态
UPDATE students SET status = 'active' WHERE status IS NULL;

-- 4. 检查结果
SELECT COUNT(*) as total_students, 
       COUNT(CASE WHEN status = 'active' THEN 1 END) as active_students,
       COUNT(CASE WHEN status = 'graduated' THEN 1 END) as graduated_students
FROM students;
