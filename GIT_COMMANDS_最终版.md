# Git 提交命令（最终版 - 修复隐藏失败错误）

## 修复内容

### 问题
- ❌ 点击删除按钮时报错：`/api/hide_student` 404 错误
- ❌ 隐藏学生功能已经移除，但前端还在调用

### 解决方案
✅ **移除隐藏功能，改用简单的请假学生显示方案**

### 修改内容

1. **后端 (app.py)**
   - ✅ 移除了 `CourseAttendance.extra_data` 字段定义
   - ✅ 移除了数据库迁移代码
   - ✅ 移除了 `/api/hide_student` API
   - ✅ 修改了 `get_classroom_data` 同时返回活跃和请假学生
   - ✅ 移除了所有 `is_hidden` 相关代码

2. **前端 (templates/classroom.html)**
   - ✅ 移除了删除/隐藏学生按钮
   - ✅ 移除了 `deleteStudent()` 函数
   - ✅ 移除了所有 `is_hidden` 相关代码
   - ✅ 添加了请假学生显示区域（可收起）
   - ✅ 添加了 `updateAbsentStudentsDisplay()` 函数
   - ✅ 添加了 `toggleAbsentStudents()` 函数

---

## Git 提交命令

```bash
# 查看改动
git status

# 添加文件
git add app.py templates/classroom.html

# 提交
git commit -m "fix: 移除隐藏功能，改用请假学生显示方案

- 移除CourseAttendance.extra_data字段定义
- 移除隐藏学生功能和API (/api/hide_student)
- 修复删除按钮导致的404错误
- 修改数据获取逻辑，返回活跃和请假学生
- 添加请假学生显示区域（页面下方，可收起）
- 移除所有is_hidden相关代码"

# 推送
git push
```

---

## 功能说明

### 新功能
- **请假学生区域**：在页面下方显示所有 `status='absent'` 的学生
- **可收起/展开**：点击标题栏可以收起或展开请假学生区域
- **不参与答题**：请假学生只显示，不参与课堂数据计算

### 优势
- ✅ 不需要修改数据库
- ✅ 使用已有的 `status` 字段
- ✅ 逻辑更简单清晰
- ✅ 不会再出现404错误

---

## 验证

修复后应该：
- ✅ 不会再有"隐藏学生时发生错误"的提示
- ✅ 删除按钮已移除，不会再触发错误
- ✅ 请假学生显示在页面下方的可收起区域
- ✅ 活跃学生正常显示在上方，参与答题



