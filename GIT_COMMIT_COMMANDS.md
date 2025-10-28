# Git 提交命令

```bash
git add app.py templates/classroom.html
git commit -m "修复next后按钮显示问题：只有在start后才显示行为按钮"
git push origin main
```

## 修复内容

### 问题
- 点击NEXT后，行为按钮自动显示出来
- 应该只在点击START后才显示按钮

### 解决
- 在 next_round 函数中注释掉自动显示按钮的代码
- 按钮只在 startClass 函数中显示
- 确保 round_active 为 true 时才显示按钮
