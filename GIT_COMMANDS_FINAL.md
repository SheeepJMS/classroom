# Git 提交命令（可直接复制粘贴）

## ⚠️ 重要提示

在提交代码之前，请先运行 SQL 修复数据库：

```sql
ALTER TABLE course_attendances ADD COLUMN IF NOT EXISTS extra_data TEXT;
```

---

## Git 提交命令列表

### 方案1：只提交核心修复文件（推荐）

```bash
git add app.py templates/classroom.html
git commit -m "fix: 修复数据库字段缺失和课堂显示问题

- 添加extra_data字段到CourseAttendance模型
- 添加数据库字段自动迁移逻辑
- 修复JavaScript语法错误（重复声明）
- 修复ROUND数据显示问题
- 修复进入班级页面的数据库错误"
git push
```

---

### 方案2：一键提交（一行命令）

```bash
git add app.py templates/classroom.html && git commit -m "fix: 修复数据库字段缺失和课堂显示问题" && git push
```

---

### 方案3：分步提交（最安全）

```bash
# 第一步：查看改动
git status

# 第二步：查看具体改动内容
git diff app.py
git diff templates/classroom.html

# 第三步：添加文件
git add app.py templates/classroom.html

# 第四步：提交
git commit -m "fix: 修复数据库字段缺失和课堂显示问题"

# 第五步：推送
git push
```

---

## 如果提交后发现问题需要回滚

```bash
# 撤销最后一次提交（保留改动）
git reset --soft HEAD~1

# 完全撤销最后一次提交（不保留改动，谨慎使用）
git reset --hard HEAD~1
```

---

## 提交前检查清单

- [ ] 已在数据库中运行 SQL 添加 `extra_data` 字段
- [ ] 已测试进入班级页面不再报错
- [ ] 已测试 BINGO 功能正常工作
- [ ] 已确认 ROUND 数据显示正常



