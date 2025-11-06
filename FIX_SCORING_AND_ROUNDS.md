# 修复轮次累计和分数累计问题

## 问题描述

用户报告了三个主要问题：
1. 第二题提交答案时提示"您已经提交过答案了"
2. BINGO评判时，所有题目都使用第一题的回答
3. round数字和学生累计问题没有改善（轮次不递增，分数不累计）

## 根本原因

### 问题1和2：数据查询错误
之前的代码在检查是否已提交时，以及评判答案时，没有正确区分当前轮次和历史轮次。虽然在查询时使用了 `round_number=course.current_round`，但在某些情况下可能获取到错误的提交记录。

### 问题3：计算逻辑错误
- 历史分数和轮次的计算逻辑不够清晰
- `historical_correct_rounds` 的计算存在重复计算的问题
- 当前轮次的分数和轮次没有正确添加到总分和总轮次中

## 修复方案

### 1. 提交答案检查
在 `submit_student_answer` 函数中，添加了详细的日志输出，确保检查的是当前轮次的提交：
```python
existing = StudentSubmission.query.filter_by(
    student_id=student.id,
    course_id=course.id,
    round_number=course.current_round  # 明确的当前轮次
).first()
```

### 2. 评判答案逻辑
在 `judge_answers` 函数中，修复了以下问题：
- 明确区分历史成绩和当前轮次成绩
- 修复 `historical_correct_rounds` 的计算，使用列表推导式确保每个轮次只计算一次
- 在计算总分和总轮次时，明确区分有没有提交记录的情况

```python
# 历史正确轮次数（同一轮次只算一次）
historical_correct_rounds = len([r for r in historical_rounds if 
    any(sub.is_correct and sub.round_number == r for sub in all_submissions)])

# 判断当前答案
if submission:
    # 判断当前轮次答案是否正确
    is_current_correct = submission.answer.strip().lower() == correct_answer.strip().lower()
    submission.is_correct = is_current_correct
    
    # 计算总分数和轮次
    total_score = historical_score + current_round_score
    total_rounds = len(historical_rounds) + 1
    correct_rounds = historical_correct_rounds + (1 if is_current_correct else 0)
else:
    # 没有提交记录，只统计历史轮次
    total_rounds = len(historical_rounds)
    correct_rounds = historical_correct_rounds
```

### 3. 下一轮逻辑
在 `next_round` 函数中，添加了详细的调试日志，帮助追踪问题：
```python
print(f"👤 学生 {student.name} 有 {len(submissions)} 条提交记录")
for sub in submissions:
    print(f"  轮次 {sub.round_number}: 答案='{sub.answer}' is_correct={sub.is_correct}")
print(f"  → 总分: {total_score}, 总轮次: {total_rounds}, 正确轮次: {correct_rounds}")
```

### 4. 添加调试日志
为了帮助定位问题，在关键位置添加了调试日志：
- 提交答案时：显示当前轮次和答案内容
- 评判答案时：显示评判的轮次、学生答案 vs 正确答案
- 下一轮时：显示每个学生的提交记录和计算结果

## 测试要点

1. **提交答案**：确保每个轮次可以独立提交答案，不会误判为"已经提交过"
2. **评判答案**：确保评判时使用的是当前轮次的答案，而不是历史轮次
3. **分数累计**：确保分数正确累加，包括历史分数和当前轮次分数
4. **轮次累计**：确保轮次数正确递增，每个学生参与的轮次数正确
5. **准确率**：确保准确率正确计算（正确轮次数 / 总轮次数）

## 部署说明

修复后的代码需要重新部署到 Render 平台。请执行：
```bash
git add app.py
git commit -m "修复轮次计算和分数累计逻辑，添加详细调试日志"
git push origin main
```

部署后，可以在 Render 的日志中看到详细的调试信息，帮助定位任何剩余的问题。






