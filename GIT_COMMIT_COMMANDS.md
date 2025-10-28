# Git 提交命令

```bash
git add app.py templates/classroom.html templates/class_detail.html
git commit -m "修复数据库：在init_database中手动添加缺失的字段"
git push origin main
```

## 修复内容

### 问题
- `db.create_all()` 不会自动添加新字段到已存在的表
- 数据库表 `student_submissions` 缺少新字段：guess_count, copy_count, noisy_count, distracted_count, penalty_score

### 解决方案
- 修改 `init_database()` 函数
- 使用 SQL 的 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 语句
- 在应用启动时自动添加缺失的字段
- 使用 try-except 确保即使字段已存在也不会报错

### 部署后效果
- 应用启动时会自动检查并添加缺失的字段
- 不会影响现有数据
- 新字段默认值为 0
