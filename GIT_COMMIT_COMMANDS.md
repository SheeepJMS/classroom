# Git 提交命令

```bash
git add app.py templates/classroom.html templates/class_detail.html
git commit -m "修复数据库字段不存在错误：添加行为记录字段并初始化数据库"
git push origin main
```

## 修复内容

### 问题
- 数据库报错：column student_submissions.guess_count does not exist
- 原因：新增了数据库字段（guess_count, copy_count, noisy_count, distracted_count, penalty_score），但数据库中没有这些列

### 解决方案
1. 将字段设置为 `nullable=True`，使其兼容已有数据库
2. 在 `init_database()` 函数中调用 `db.create_all()` 来自动创建缺失的字段
3. 确保应用启动时调用 `init_database()`

### 注意事项
- 部署到 Render 后，数据库表会自动更新（添加新字段）
- 如果字段仍然不存在，可能需要手动执行 SQL 添加字段
