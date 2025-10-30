# Git 提交指令

## 修复颁奖页面错误

```bash
git add templates/ceremony.html
git add app.py
git commit -m "fix: 修复颁奖页面classroom_data未定义错误 - 改为使用student_scores数据源"
git push
```