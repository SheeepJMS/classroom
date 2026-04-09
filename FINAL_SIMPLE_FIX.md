# 最终简化修复方案

## 您的需求

> "如果隐藏起来那么麻烦，那就在页面下方建一个框，把请假学生挪进去，并且可收起。这样好弄吗？需要修改数据库吗"

## 回答

✅ **很好弄！不需要修改数据库！**

## 方案说明

1. **移除复杂的隐藏功能** - 不再需要 `extra_data` 字段
2. **使用简单的请假学生** - 使用已有的 `status='absent'` 字段
3. **在页面下方显示请假学生** - 可收起的区域

## 需要修改的地方

### 后端 (app.py)
1. ✅ 移除 `CourseAttendance.extra_data` 字段定义
2. ✅ 移除所有 `extra_data` 相关代码
3. ✅ 移除 `/api/hide_student` API
4. ✅ 修改 `get_classroom_data` 返回请假学生数据

### 前端 (templates/classroom.html)
1. 移除删除/隐藏学生按钮
2. 移除 `deleteStudent` 函数
3. 添加请假学生显示区域
4. 添加显示请假学生的函数

## Git 提交命令

修复完成后，运行：

```bash
git add app.py templates/classroom.html
git commit -m "fix: 简化请假学生显示 - 移除隐藏功能，改用页面下方可收起区域"
git push
```

## 优势

- ✅ 不需要修改数据库
- ✅ 使用已有的 `status` 字段
- ✅ 逻辑更简单清晰
- ✅ 不需要 `extra_data` 字段



