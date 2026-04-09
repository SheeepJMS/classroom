# 最小化修复方案

## 当前问题

1. **数据库错误**：`column "extra_data" of relation "course_attendances" does not exist`
   - 这是唯一需要立即修复的问题
   - 其他问题（ROUND显示等）需要先确认是否真的存在

## 修复方案（最小改动）

### 方案1：最简单的SQL脚本（推荐）

只需要在数据库中运行一条SQL命令：

```sql
ALTER TABLE course_attendances ADD COLUMN IF NOT EXISTS extra_data TEXT;
```

### 方案2：暂时不使用 extra_data 字段

如果不想改数据库，可以暂时在代码中忽略这个字段，等确认后再添加。

## 需要您确认的信息

1. **您的数据库环境**：
   - [ ] 本地 SQLite
   - [ ] Render PostgreSQL
   - [ ] 其他

2. **当前问题的优先级**：
   - [ ] 只有 BINGO 错误需要修复
   - [ ] 还有其他问题（请说明）

3. **是否可以运行SQL**：
   - [ ] 可以访问数据库控制台
   - [ ] 只能通过代码修改

## 建议

**最安全的做法**：
1. 先回滚我刚才的代码改动
2. 只运行一条SQL添加字段
3. 确认问题解决后，再考虑其他功能

您希望采用哪种方案？



