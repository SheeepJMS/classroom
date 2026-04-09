# 可直接复制粘贴的命令

## 🔴 第一步：修复数据库（必须先做！）

### 在 Render 数据库控制台运行：

```sql
ALTER TABLE course_attendances ADD COLUMN IF NOT EXISTS extra_data TEXT;
```

**如何操作：**
1. 登录 Render 控制台
2. 找到您的 PostgreSQL 数据库服务
3. 点击 "Connect" 或 "Database Shell"
4. 粘贴上面的 SQL 命令并执行
5. 刷新您的应用页面

---

## ✅ 第二步：Git 提交（修复完成后）

### 复制粘贴以下命令：

```bash
git add app.py templates/classroom.html
git commit -m "fix: 修复数据库字段缺失和课堂显示问题"
git push
```

---

## 如果上面命令出错，分步执行：

```bash
# 查看改动
git status

# 添加文件
git add app.py
git add templates/classroom.html

# 提交
git commit -m "fix: 修复数据库字段缺失和课堂显示问题"

# 推送
git push
```

---

## 说明

本次修复包含：
1. ✅ 添加 `extra_data` 字段到 `CourseAttendance` 模型
2. ✅ 添加数据库字段自动迁移逻辑（应用启动时自动检查）
3. ✅ 修复 JavaScript 语法错误
4. ✅ 修复 ROUND 数据显示问题

---

## 验证修复

运行 SQL 后，刷新页面应该：
- ✅ 可以正常进入班级页面
- ✅ BINGO 功能正常工作
- ✅ ROUND 数据显示正常



