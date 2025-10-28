# Git 提交命令

```bash
git add app.py templates/classroom.html
git commit -m "添加学生行为记录：替换统计数据为四个按钮(guess/copy/noisy/distracted)，每次点击扣2分"
git push origin main
```

## 修复内容

### 1. 数据库模型更新
- 在 `StudentSubmission` 模型中添加了行为记录字段：
  - `guess_count`: 猜题次数（橙色按钮 🎲）
  - `copy_count`: 抄袭次数（红色按钮 📋）
  - `noisy_count`: 吵闹次数（紫色按钮 🔊）
  - `distracted_count`: 分心次数（黄色按钮 🙈）
  - `penalty_score`: 扣分总数

### 2. 前端更新
- 替换了学生卡片底部的统计数据（SCORE, ROUNDS, ACC, ANSWER）为四个行为按钮
- 每个按钮显示对应的图标和计数
- 点击按钮后弹窗确认，然后调用后端API
- 按钮颜色和图标：
  - Guess: 橙色 (#ff9800) 🎲
  - Copy: 红色 (#f44336) 📋
  - Noisy: 紫色 (#9c27b0) 🔊
  - Distracted: 黄色 (#ffeb3b) 🙈

### 3. 后端API
- 添加了 `/api/mark_behavior` 端点
\-\-record 学生行为并扣2分
- 在 `judge_answers` 和 `next_round` 函数的分数计算中减去 `penalty_score`
- 扣分不影响准确率（因为只影响总分，不影响 `is_correct`）

### 4. 功能特点
- ✅ 点击按钮前弹窗确认
- ✅ 每次点击扣2分
- ✅ 不影响准确率（ACC）
- ✅ 记录行为次数（显示在按钮上）
- ✅ 扣分影响总分显示
