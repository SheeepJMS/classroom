# 修复 ROUND 数据显示和 BINGO 错误问题

## 问题描述

1. **ROUND 没有数据** - ROUND 显示为空
2. **BINGO 错误** - 点击 BINGO 按钮时报错：`'CourseAttendance' object has no attribute 'extra_data'`

## 问题原因

### 问题1：ROUND 没有数据
- `classroomData.current_round` 没有被正确初始化
- 当 API 返回的数据中没有 `current_round` 或值为 `null/undefined` 时，前端没有设置默认值
- `updateRoundStatus()` 函数没有处理 `current_round` 为 `undefined` 的情况

### 问题2：BINGO 错误
- `CourseAttendance` 模型缺少 `extra_data` 字段
- 代码中多处访问 `attendance.extra_data` 但模型定义中没有这个字段
- 导致访问不存在的属性时抛出 `AttributeError`

## 修复内容

### 1. 添加 `extra_data` 字段到 `CourseAttendance` 模型
- **文件**：`app.py`
- **修复**：在 `CourseAttendance` 模型类中添加 `extra_data = db.Column(db.Text)` 字段
- **用途**：用于存储 JSON 格式的额外数据，如学生隐藏状态等

### 2. 修复 ROUND 数据显示
- **文件**：`templates/classroom.html`
- **修复1**：在数据加载成功后，确保 `current_round` 被正确初始化
- **修复2**：在错误处理的 catch 块中也初始化 `current_round`
- **修复3**：改进 `updateRoundStatus()` 函数，处理 `current_round` 为 `undefined/null` 的情况
- **修复4**：从后端模板变量初始化 `current_round` 作为后备方案

### 3. 改进错误处理
- **文件**：`templates/classroom.html`
- **修复**：在 catch 块中完整初始化所有必要的数据结构

## 修改的文件

1. `app.py` - 添加 `extra_data` 字段到 `CourseAttendance` 模型
2. `templates/classroom.html` - 修复 ROUND 数据显示和初始化逻辑

## 技术细节

### 模型字段添加
```python
class CourseAttendance(db.Model):
    """课程出勤模型"""
    __tablename__ = 'course_attendances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), nullable=False)
    is_absent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 新增字段
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据，如隐藏状态等
```

### ROUND 数据初始化
```javascript
// 确保 current_round 被正确初始化
if (!classroomData.current_round && classroomData.current_round !== 0) {
    {% if course %}
    classroomData.current_round = {{ course.current_round if course.current_round else 1 }};
    {% else %}
    classroomData.current_round = 1;
    {% endif %}
    console.log('初始化 current_round 为:', classroomData.current_round);
}
```

### updateRoundStatus 函数改进
```javascript
function updateRoundStatus() {
    try {
        const roundNumber = document.getElementById('roundNumber');
        
        // 确保 current_round 有值
        if (!classroomData.current_round && classroomData.current_round !== 0) {
            {% if course %}
            classroomData.current_round = {{ course.current_round if course.current_round else 1 }};
            {% else %}
            classroomData.current_round = 1;
            {% endif %}
            console.log('updateRoundStatus - 初始化 current_round 为:', classroomData.current_round);
        }
        
        if (roundNumber) {
            const roundValue = classroomData.current_round || 1;
            roundNumber.textContent = roundValue;
        }
        // ...
    } catch (error) {
        console.error('updateRoundStatus错误:', error);
    }
}
```

## 数据库迁移说明

由于添加了新字段 `extra_data` 到 `CourseAttendance` 表，如果数据库已经存在旧数据：

1. **新创建的记录**：会自动包含 `extra_data` 字段（默认值为 `NULL`）
2. **旧记录**：`extra_data` 字段会被设置为 `NULL`，不会影响现有功能
3. **代码兼容性**：所有访问 `extra_data` 的地方都已经做了安全检查：
   ```python
   if attendance and attendance.extra_data:
       try:
           extra_data = json.loads(attendance.extra_data)
           # 处理数据
       except:
           pass
   ```

## Git 提交指令

```bash
# 添加修改的文件
git add app.py
git add templates/classroom.html
git add FIX_ROUND_AND_BINGO_ERROR.md

# 提交更改
git commit -m "fix: 修复ROUND数据显示和BINGO错误问题

- 添加extra_data字段到CourseAttendance模型
- 修复ROUND数据显示为空的问题
- 改进current_round初始化逻辑
- 增强错误处理和默认值设置"

# 推送到远程仓库
git push
```

## 验证清单

- [x] 添加了 `extra_data` 字段到 `CourseAttendance` 模型
- [x] 修复了 ROUND 数据显示问题
- [x] 改进了 `current_round` 初始化逻辑
- [x] 增强了错误处理
- [x] 所有访问 `extra_data` 的地方都有安全检查

## 测试建议

1. **测试 ROUND 显示**：
   - 刷新页面，检查 ROUND 是否正常显示（应该显示当前轮次数）
   - 测试新创建的课堂，ROUND 应该显示为 1
   
2. **测试 BINGO 功能**：
   - 开始答题后，输入正确答案
   - 点击 BINGO 按钮，确认不再出现错误
   - 检查学生答案评判是否正常

3. **测试数据初始化**：
   - 在控制台检查 `classroomData.current_round` 是否正确初始化
   - 检查是否有相关的错误日志

## 注意事项

1. **数据库迁移**：如果数据库表已经存在，新字段会自动添加，但可能需要重启应用
2. **向后兼容**：所有 `extra_data` 的访问都已经做了安全检查，不会影响旧数据
3. **默认值**：`current_round` 的默认值为 1，如果没有从服务器获取到值

