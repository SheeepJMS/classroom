# Git 提交命令列表

## 当前改动文件列表

本次修复包含以下文件：

### 核心修复文件
1. `app.py` - 添加extra_data字段和自动迁移
2. `templates/classroom.html` - 修复JavaScript错误和ROUND显示

### 文档文件（可选）
3. `FIX_CLASSROOM_DISPLAY_BUG.md` - 第一次修复文档
4. `FIX_ROUND_AND_BINGO_ERROR.md` - ROUND和BINGO错误修复文档
5. `MIGRATE_EXTRA_DATA.md` - 数据库迁移指南
6. `SAFE_MIGRATION_GUIDE.md` - 安全迁移指南
7. `MINIMAL_FIX_PLAN.md` - 最小化修复方案
8. `migrate_add_extra_data.py` - 迁移脚本（可选）

---

## 方案1：只提交核心修复（推荐）

```bash
# 查看当前改动
git status

# 添加核心修复文件
git add app.py
git add templates/classroom.html

# 提交
git commit -m "fix: 修复课堂显示和BINGO错误

- 添加extra_data字段到CourseAttendance模型
- 修复JavaScript语法错误（重复声明）
- 修复ROUND数据显示问题
- 添加数据库字段自动迁移逻辑"

# 推送到远程
git push
```

---

## 方案2：包含所有文档文件

```bash
# 查看当前改动
git status

# 添加所有修改的文件
git add app.py
git add templates/classroom.html
git add FIX_CLASSROOM_DISPLAY_BUG.md
git add FIX_ROUND_AND_BINGO_ERROR.md
git add MIGRATE_EXTRA_DATA.md
git add SAFE_MIGRATION_GUIDE.md
git add MINIMAL_FIX_PLAN.md
git add migrate_add_extra_data.py
git add GIT_COMMANDS.md

# 提交
git commit -m "fix: 修复课堂显示和BINGO错误

- 添加extra_data字段到CourseAttendance模型
- 修复JavaScript语法错误（重复声明）
- 修复ROUND数据显示问题
- 添加数据库字段自动迁移逻辑
- 添加相关文档和迁移脚本"

# 推送到远程
git push
```

---

## 方案3：分步提交（最安全）

```bash
# 第一步：只提交核心代码修复
git add app.py templates/classroom.html
git commit -m "fix: 修复BINGO错误和ROUND显示问题"

# 第二步：推送第一步
git push

# 第三步：如果需要，再提交文档
git add *.md migrate_add_extra_data.py
git commit -m "docs: 添加修复文档和迁移脚本"
git push
```

---

## 一键提交命令（方案1）

```bash
git add app.py templates/classroom.html && git commit -m "fix: 修复课堂显示和BINGO错误 - 添加extra_data字段、修复JS错误和ROUND显示" && git push
```

---

## 检查提交前先查看改动

```bash
# 查看所有改动
git status

# 查看具体改动内容
git diff app.py
git diff templates/classroom.html

# 确认无误后再提交
```

---

## 如果出错需要回滚

```bash
# 取消已添加但未提交的文件
git reset

# 撤销最后一次提交（保留改动）
git reset --soft HEAD~1

# 完全撤销最后一次提交（不保留改动）
git reset --hard HEAD~1
```



