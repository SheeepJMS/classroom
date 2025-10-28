# Git 提交命令

```bash
git add app.py templates/classroom.html templates/class_detail.html
git commit -m "完善界面切换：BINGO前显示行为按钮，BINGO后显示统计数据，next_round切换回按钮"
git push origin main
```

## 所有修复内容总结

### 1. 学生行为记录功能
- 四个行为按钮：Guess（橙色🎲）、Copy（红色📋）、Noisy（紫色🔊）、Distracted（黄色🙈）
- 点击扣2分，不影响准确率
- 记录行为次数并显示在按钮上

### 2. 界面切换逻辑
- **答题阶段（START到BINGO）**：显示四个行为按钮
- **评判阶段（点击BINGO后）**：隐藏按钮，显示四个统计数据（Score, Rounds, Acc, Answer）
- **下一轮（点击Next）**：重新切换回显示行为按钮，为下一轮答题做准备

### 3. 学生请假功能
- 请假按钮和恢复按钮
- 请假学生不参加新课程
- 请假学生自动排到底部
- 显示正确的统计数据

### 4. 准确率和分数计算
- 准确率计算：未作答算作错误
- 扣分不影响准确率
- 正确累加分数和轮次
