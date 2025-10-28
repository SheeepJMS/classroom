# Git 提交命令

```bash
git add app.py templates/classroom.html templates/class_detail.html
git commit -m "完善行为按钮UI：横向排列、响应式、点击后显示PUNISHED状态"
git push origin main
```

## 修复内容

### 1. 按钮横向排列
- 使用 `flex-direction: row` 和 `flex: 1` 让四个按钮并排显示
- 设置 `flex-wrap: nowrap` 防止换行
- 缩小内边距和字体大小以适应空间

### 2. 响应式设计
- 添加媒体查询 `@media (max-width: 600px)`
- 小屏幕时隐藏图标和计数：`.btn-icon` 和 `.btn-count`
- 只显示按钮文字

### 3. PUNISHED状态
- 添加 `student-punished` div，点击按钮后显示
- 红色背景，白色文字，显示"PUNISHED"
- 点击按钮后自动隐藏输入框、按钮，显示punished状态

### 4. 统计数据隐藏
- 答题环节统计数据默认隐藏（`display: none !important`）
- 只有BINGO后才显示

### 5. next_round重置
- 进入下一轮时重置punished状态
- 重新显示输入框和行为按钮
