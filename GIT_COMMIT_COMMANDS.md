# Git 提交命令

```bash
git add app.py templates/classroom.html
git commit -m "简化行为按钮：点击后该题得分为0，不再扣分"
git push origin main
```

## 修复内容

### 简化逻辑
- **移除扣分逻辑**：不再使用 penalty_score 扣2分
- **直接设为错题**：点击任何行为按钮后，`is_correct = False`
- **该题得分为0**：在评判时不会加分，也不会计入正确轮次

### 修改
1. **后端 (`mark_behavior`)**：
   - 移除 `submission.penalty_score += 2`
   - 添加 `submission.is_correct = False`
   - 提示信息改为"该题得分为0"

2. **前端提示**：
   - 将"将扣2分"改为"该题得分为0"
   - 移除扣分相关的UI更新

3. **分数计算**：
   - 移除所有 penalty_score 处理
   - 只依据 is_correct 判断
