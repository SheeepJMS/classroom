# Git 提交命令

```bash
git add app.py templates/classroom.html
git commit -m "修复准确率计算（未作答算作错误）和领奖页面跳转（使用course_id）"
git push origin main
```

## 修复内容

1. **准确率计算修复**：
   - 修改了 `judge_answers` 和 `next_round` 函数的逻辑
   - `total_rounds` 现在使用课程总轮次数，而不是学生参与的轮次数
   - 未作答的轮次算作错误（计入总轮次，但不计入正确轮次）
   - 例如：答对1题、答错1题、未作答1题，准确率 = 1/3 = 33%

2. **领奖页面修复**：
   - 修复了 `endClass` 函数使用 `class_obj.id` 而不是 `course_id` 的问题
   - 现在正确跳转到 `/ceremony/<course_id>` 页面

