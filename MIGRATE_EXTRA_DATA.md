# 数据库迁移指南 - 添加 extra_data 字段

## 问题描述

错误信息：`column "extra_data" of relation "course_attendances" does not exist`

这是因为我们添加了 `extra_data` 字段到 `CourseAttendance` 模型，但数据库表中还没有这个字段。

## 解决方案

### 方案1：自动迁移（推荐）

应用程序已经更新，会在启动时自动检查并添加缺失的字段。只需：

1. **重启应用程序**
   - 在 Render 上，点击 "Manual Deploy" 或等待自动部署
   - 应用程序启动时会自动添加 `extra_data` 字段

### 方案2：手动运行迁移脚本

如果自动迁移不起作用，可以手动运行迁移脚本：

```bash
python migrate_add_extra_data.py
```

### 方案3：在 Render 数据库控制台直接运行 SQL

1. 登录 Render 控制台
2. 进入数据库服务
3. 打开数据库控制台（Database Shell）
4. 运行以下 SQL：

```sql
-- 检查字段是否已存在
SELECT EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'course_attendances' 
    AND column_name = 'extra_data'
);

-- 如果返回 false，运行以下 SQL 添加字段
ALTER TABLE course_attendances ADD COLUMN extra_data TEXT;
```

或者使用 PostgreSQL 的 DO 块（更安全）：

```sql
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'course_attendances' 
        AND column_name = 'extra_data'
    ) THEN
        ALTER TABLE course_attendances ADD COLUMN extra_data TEXT;
        RAISE NOTICE 'extra_data 字段添加成功';
    ELSE
        RAISE NOTICE 'extra_data 字段已存在';
    END IF;
END $$;
```

## 验证迁移是否成功

运行以下 SQL 查询验证字段是否已添加：

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'course_attendances'
  AND column_name = 'extra_data';
```

如果查询返回结果，说明字段已成功添加。

## 如果迁移失败

如果遇到权限问题或其他错误：

1. **检查数据库连接**：确保应用可以连接到数据库
2. **检查表是否存在**：运行 `SELECT * FROM course_attendances LIMIT 1;` 确认表存在
3. **检查权限**：确保数据库用户有 ALTER TABLE 权限
4. **查看日志**：检查应用启动日志中的迁移信息

## 注意事项

- `extra_data` 字段允许为 `NULL`，不会影响现有数据
- 现有记录的 `extra_data` 字段值将为 `NULL`
- 所有访问 `extra_data` 的代码都已经做了安全检查，不会因为 `NULL` 值而出错



