# Git 提交命令

```bash
git add app.py templates/classroom.html templates/class_detail.html
git commit -m "修复模板语法错误：简化hasattr表达式"
git push origin main
```

## 修复内容

### 问题
- 错误：`'hasattr' is undefined`
- 原因：在 Jinja2 模板中使用了复杂的 `hasattr` 嵌套表达式

### 解决方案
- 将复杂的 `hasattr` 嵌套表达式改为使用 `getattr(student, 'field', default_value)` 
- 使用 Jinja2 的 `{% set %}` 设置变量，简化表达式
- 将过长的三元表达式拆分成多行，更易读

### 修改的表达式
- 从：`{{ student.total_score if hasattr(student, 'total_score') else 0 }}`
- 改为：`{{ getattr(student, 'total_score', 0) }}`

- 将复杂的 ATTENDANCE 计算拆分成变量定义
