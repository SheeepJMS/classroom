# 最终 Git 提交命令

## 本次修复包含两个部分

### 1. 移除隐藏功能（之前的修复）
- 移除 `CourseAttendance.extra_data` 字段
- 移除隐藏学生功能和 API
- 添加请假学生显示区域

### 2. 数据库连接修复（本次修复）
- 添加数据库连接池配置
- 添加数据库连接重试装饰器
- 应用到 `class_management` 路由

---

## Git 提交命令

```bash
# 查看所有改动
git status

# 添加所有修改的文件
git add app.py templates/classroom.html

# 提交（包含两个修复）
git commit -m "fix: 移除隐藏功能并修复数据库连接问题

1. 移除隐藏功能，改用请假学生显示方案
   - 移除CourseAttendance.extra_data字段定义
   - 移除隐藏学生功能和API (/api/hide_student)
   - 修复删除按钮导致的404错误
   - 添加请假学生显示区域（页面下方，可收起）
   - 移除所有is_hidden相关代码

2. 添加数据库连接池配置和重试机制
   - 添加SQLALCHEMY_ENGINE_OPTIONS配置（pool_pre_ping等）
   - 添加数据库连接重试装饰器（最多3次重试）
   - 应用到class_management路由
   - 提高数据库连接稳定性和性能"

# 推送
git push
```

---

## 预期效果

修复后应该：
- ✅ 不会再出现"隐藏学生时发生错误"的提示
- ✅ 删除按钮已移除，不会再触发404错误
- ✅ 请假学生显示在页面下方的可收起区域
- ✅ 减少数据库连接超时错误
- ✅ 自动重连失效的连接
- ✅ 提高页面加载速度

