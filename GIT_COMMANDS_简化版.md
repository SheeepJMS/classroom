# Git 提交命令（简化版 - 移除隐藏功能）

## 当前改动总结

### 已完成的修改

1. **后端 (app.py)**
   - ✅ 移除了 `CourseAttendance.extra_data` 字段定义
   - ✅ 移除了数据库迁移代码
   - ✅ 移除了 `/api/hide_student` API
   - ✅ 修改了 `get_classroom_data` 返回请假学生数据
   - ✅ 移除了所有 `is_hidden` 相关代码

2. **前端 (templates/classroom.html)**
   - ✅ 添加了请假学生显示区域的HTML结构
   - ✅ 添加了切换请假学生区域的函数
   - ⏳ 还需要移除删除按钮和隐藏学生函数

### 还需要完成的

- 移除前端删除/隐藏学生按钮
- 移除 `deleteStudent` 函数
- 添加显示请假学生的函数
- 移除所有 `is_hidden` 相关代码

---

## Git 提交命令（当前状态）

```bash
# 查看改动
git status

# 添加文件
git add app.py templates/classroom.html

# 提交
git commit -m "fix: 移除隐藏功能，简化请假学生显示方案

- 移除CourseAttendance.extra_data字段定义
- 移除隐藏学生功能和API
- 修改数据获取逻辑，返回活跃和请假学生
- 添加请假学生显示区域（可收起）"

# 推送
git push
```

---

## 注意

⚠️ **代码还未完全完成**，前端还需要：
1. 移除删除按钮
2. 完成请假学生显示函数
3. 清理所有 `is_hidden` 相关代码

**建议**：先运行SQL修复数据库错误，然后再提交代码。



