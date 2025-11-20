# Git 更新指令 - 修复历史班级显示问题

## 完整提交指令

### 方式1：分步骤提交（推荐）

```bash
# 1. 查看更改的文件
git status

# 2. 添加修改的文件
git add app.py
git add templates/homepage.html
git add HISTORICAL_CLASSES_FIX.md

# 3. 提交更改
git commit -m "fix: 修复历史班级显示问题

- 添加历史班级和竞赛目标的查询和显示
- 新增 delete_class 和 delete_competition_goal API 端点
- 修复前端模板的过滤逻辑和字段访问
- 修正 endGoal 函数的 API 端点路径"

# 4. 推送到远程仓库
git push
```

### 方式2：一键提交

```bash
git add app.py templates/homepage.html HISTORICAL_CLASSES_FIX.md && git commit -m "fix: 修复历史班级显示问题 - 添加历史记录查询、删除功能和前端修复" && git push
```

## 详细说明

### 本次修改的文件：

1. **app.py** - 主要修改
   - 添加 `inactive_classes` 和 `inactive_goals` 查询
   - 新增 `delete_class()` 和 `delete_competition_goal()` 函数
   - 添加 `classes_json` 数据传递

2. **templates/homepage.html** - 模板修复
   - 修复活跃班级区域的过滤逻辑
   - 添加安全的字段访问检查
   - 修正 `endGoal` 函数的 API 端点

3. **HISTORICAL_CLASSES_FIX.md** - 新增文档
   - 详细记录了问题原因和修复方案

## 如果遇到问题

### 查看当前状态
```bash
git status
```

### 查看具体更改
```bash
git diff app.py
git diff templates/homepage.html
```

### 如果提交后想修改提交信息
```bash
git commit --amend -m "新的提交信息"
git push --force
```

### 如果只想提交部分文件
```bash
# 交互式选择要提交的文件
git add -i
```

## 最佳实践

1. **先查看更改**：`git diff` 确认修改内容
2. **提交前测试**：确保功能正常
3. **提交信息清晰**：描述问题和解决方案
4. **小步提交**：不要一次性提交太多不相关的更改

## 回滚命令（如果需要）

### 撤销未提交的更改
```bash
# 撤销所有未提交的更改
git checkout .

# 撤销特定文件的更改
git checkout app.py
```

### 撤销已提交但未推送的更改
```bash
# 撤销最后一次提交，但保留更改
git reset --soft HEAD~1

# 完全撤销最后一次提交和更改
git reset --hard HEAD~1
```




