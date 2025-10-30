# 修复历史课程报告数据错误

## 问题描述
学生报告中心里面的报告是好的，但是历史课程里面的报告是错的数据。

## 根本原因
在 `student_report_center` 函数中，计算正确率时使用了错误的方法：
1. **错误计算**：使用 `sum(1 for s in submissions if s.is_correct)` 统计所有正确提交，但一个轮次可能有多次提交
2. **排名计算错误**：使用 `sorted_scores.index(total_score)` 导致相同分数排名错误

## 修复内容

### 1. 修正正确率计算（第917-920行）

**修改前：**
```python
correct_rounds = sum(1 for s in submissions if s.is_correct)
accuracy = (correct_rounds / len(submissions) * 100) if len(submissions) > 0 else 0
```

**修改后：**
```python
# 正确答题的轮次数（去重，只计算每个轮次至少答对一次）
correct_rounds = len(set(s.round_number for s in submissions if s.is_correct))
# 计算准确率：正确轮次 / 参与轮次
accuracy = (correct_rounds / total_rounds * 100) if total_rounds > 0 else 0
```

**说明：**
- 现在正确率 = 正确答题的轮次数 / 参与的轮次数
- 这样避免了多次提交同一题目时重复计数
- 符合其他报告页面的计算逻辑

### 2. 修正排名计算（第961-965行）

**修改前：**
```python
sorted_scores = sorted(student_scores.values(), reverse=True)
try:
    rank = sorted_scores.index(total_score) + 1
except ValueError:
    rank = len(sorted_scores) + 1
```

**修改后：**
```python
# 计算排名 - 正确的方法是统计比当前学生分数高的学生数
# 如果有n个学生分数更高，当前学生排名就是n+1
# 例如：分数 [100, 90, 90, 80]，80分的学生排名是4
higher_count = sum(1 for score in student_scores.values() if score > total_score)
rank = higher_count + 1
```

**说明：**
- 旧方法在相同分数时会产生错误的排名（`index()` 返回第一次出现的索引）
- 新方法通过统计更高分学生数来准确计算排名
- 例如：分数 [100, 90, 90, 80]，80分学生排名为4，而不是 `[80,90,90,100].index(80) + 1 = 1`

## 对比：修复前后

### 修复前的计算逻辑：
```
假设学生在轮次1提交了3次，答对2次
- correct_rounds = 2（错误：计算了所有正确提交）
- accuracy = 2 / 3 * 100 = 66.7%（错误：分母是所有提交次数）

假设班级分数 [100, 90, 90, 80]，当前学生80分
- rank = [80, 90, 90, 100].index(80) + 1 = 1（错误：返回1而不是4）
```

### 修复后的计算逻辑：
```
假设学生在轮次1提交了3次，答对2次
- correct_rounds = 1（正确：轮次1至少答对一次，只算1次）
- accuracy = 1 / 1 * 100 = 100%（正确：基于轮次计算）

假设班级分数 [100, 90, 90, 80]，当前学生80分
- higher_count = 3（正确：有3个学生分数更高）
- rank = 3 + 1 = 4（正确：排名为第4名）
```

## 涉及文件
- `app.py` - student_report_center 函数
  - 第915-920行：正确率计算
  - 第961-965行：排名计算

## 相关函数
其他报告页面使用相同的正确率计算方法：
- `generate_student_report`（第584-586行）✅ 已正确
- `generate_student_report` 的其他部分 ✅ 已正确

## 测试建议
1. 检查学生报告中心的历史课程数据是否正确
2. 验证参与率、正确率、排名计算是否正确
3. 特别测试有多次提交同一题目的情况
4. 测试排名计算在相同分数时的表现

## Git 提交指令

```bash
git add app.py FIX_HISTORICAL_COURSE_REPORTS.md
git commit -m "fix: 修复历史课程报告数据错误

- 修正正确率计算：使用去重的轮次计算而非所有提交
- 修正排名计算：统计更高分学生数而非使用index
- 确保与generate_student_report的计算逻辑一致"

git push
```
