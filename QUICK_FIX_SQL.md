# 快速修复 SQL 命令

## 问题
错误：`column course_attendances.extra_data does not exist`

## 最快解决方案：直接在数据库运行 SQL

### 如果您可以访问数据库控制台（推荐）

**在 Render PostgreSQL 数据库控制台运行：**

```sql
ALTER TABLE course_attendances ADD COLUMN IF NOT EXISTS extra_data TEXT;
```

运行后，刷新页面即可。

### 验证字段是否添加成功

```sql
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'course_attendances' 
  AND column_name = 'extra_data';
```

---

## Git 提交命令

完成修复后，运行以下命令：

```bash
git add app.py templates/classroom.html
git commit -m "fix: 修复数据库字段缺失错误 - 添加extra_data字段支持"
git push
```



