# 修复 hasattr 错误

## 问题
Jinja2 模板引擎不支持 Python 的 `hasattr()` 函数，导致首页加载失败。

错误信息：
```
jinja2.exceptions.UndefinedError: 'hasattr' is undefined
```

## 解决方案
移除所有 `hasattr()` 调用，直接访问属性。因为后端已经在 `index()` 函数中为所有班级对象添加了 `student_count` 和 `course_count` 属性，所以不需要检查属性是否存在。

### 修改前的代码
```jinja2
{{ class_data.student_count if hasattr(class_data, 'student_count') else (class_data.students|length if class_data.students else 0) }}
{{ class_data.ended_date.strftime('%Y-%m-%d') if class_data.ended_date and hasattr(class_data.ended_date, 'strftime') else (class_data.ended_date if class_data.ended_date else '未知') }}
```

### 修改后的代码
```jinja2
{{ class_data.student_count }}
{{ class_data.ended_date.strftime('%Y-%m-%d') if class_data.ended_date else '未知' }}
```

## 涉及文件
- `templates/homepage.html` - 移除了6处 `hasattr()` 调用

## 验证
```bash
# 检查是否还有 hasattr 调用
grep -n "hasattr" templates/homepage.html

# 应该没有输出
```

## Git 提交指令

```bash
git add templates/homepage.html
git commit -m "fix: 移除Jinja2模板中的hasattr调用

- Jinja2不支持Python的hasattr函数
- 直接访问属性，因为后端已确保属性存在
- 修复首页加载错误"

git push
```



