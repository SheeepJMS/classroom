# 历史班级显示问题修复

## 问题描述
点击"结束班级"显示成功消息后，班级没有出现在"历史班级"区域。

## 根本原因
1. **后端缺少查询历史班级**：`index()` 路由只查询了活跃班级（`is_active=True`），没有查询历史班级（`is_active=False`）
2. **模板变量未传递**：前端模板 `homepage.html` 期望 `inactive_classes` 变量，但后端没有传递
3. **缺少 API 端点**：模板中引用了 `deleteClass` 和 `deleteGoal` 函数，但对应的 API 端点不存在
4. **模板过滤逻辑错误**：活跃班级区域错误地检查 `ended_date` 字段

## 修复内容

### 1. 更新 `app.py` 中的 `index()` 路由
```python
# 获取所有活跃班级
classes = Class.query.filter_by(is_active=True).order_by(Class.created_date.desc()).all()

# 获取所有非活跃班级（历史班级）
inactive_classes = Class.query.filter_by(is_active=False).order_by(Class.ended_date.desc()).all()

# 获取所有活跃竞赛目标
goals = CompetitionGoal.query.filter_by(is_active=True).order_by(CompetitionGoal.created_date.desc()).all()

# 获取所有非活跃竞赛目标
inactive_goals = CompetitionGoal.query.filter_by(is_active=False).order_by(CompetitionGoal.created_date.desc()).all()

# 为每个班级添加统计数据
for class_obj in classes:
    class_obj.student_count = len(class_obj.students)
    class_obj.course_count = len(class_obj.courses)

# 为历史班级添加统计数据
for class_obj in inactive_classes:
    class_obj.student_count = len(class_obj.students)
    class_obj.course_count = len(class_obj.courses)

# 构建classes_json用于前端JavaScript
classes_json = {class_obj.id: {'id': class_obj.id, 'name': class_obj.name} for class_obj in classes}

return render_template('homepage.html',
                     classes=classes,
                     inactive_classes=inactive_classes,
                     competition_goals=goals,
                     inactive_competition_goals=inactive_goals,
                     total_students=total_students,
                     classes_json=classes_json)
```

### 2. 添加 `delete_class` API 端点
```python
@app.route('/api/delete_class/<class_id>', methods=['POST'])
def delete_class(class_id):
    """删除班级"""
    try:
        class_obj = Class.query.filter_by(id=class_id).first()
        if not class_obj:
            return jsonify({'success': False, 'message': '班级不存在'}), 404
        
        db.session.delete(class_obj)
        db.session.commit()
        
        print(f"✅ 班级已删除: {class_obj.name}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 删除班级失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除班级失败: {str(e)}'}), 500
```

### 3. 添加 `delete_competition_goal` API 端点
```python
@app.route('/api/delete_competition_goal/<goal_id>', methods=['DELETE'])
def delete_competition_goal(goal_id):
    """删除竞赛目标"""
    try:
        goal = CompetitionGoal.query.filter_by(id=goal_id).first()
        if not goal:
            return jsonify({'success': False, 'message': '竞赛目标不存在'}), 404
        
        db.session.delete(goal)
        db.session.commit()
        
        print(f"✅ 竞赛目标已删除: {goal.title}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 删除竞赛目标失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除竞赛目标失败: {str(e)}'}), 500
```

### 4. 修复 `homepage.html` 模板

#### 4.1 修正活跃班级区域的显示逻辑
- 移除了错误的 `{% if not class_data.ended_date %}` 过滤条件
- 添加了安全的字段访问检查（使用 `hasattr`）

#### 4.2 修正历史班级区域的显示逻辑
- 添加了安全的字段访问检查
- 正确处理 `ended_date` 的格式化显示

#### 4.3 修正 `endGoal` 函数
```javascript
// 从错误的端点修复为正确的端点
fetch(`/api/end_goal/${goalId}`, {  // 之前是 `/api/end_competition_goal/${goalId}`
    method: 'POST'
})
```

## 测试步骤

1. **测试结束班级功能**
   - 创建一个新班级
   - 点击"结束班级"按钮
   - 确认班级从"班级管理"区域消失
   - 确认班级出现在"历史班级"区域

2. **测试删除功能**
   - 在历史班级区域点击"删除"按钮
   - 确认班级被删除

3. **测试竞赛目标结束功能**
   - 创建一个竞赛目标
   - 点击"结束竞赛"按钮
   - 确认目标出现在历史竞赛目标区域

## 数据库查询说明

系统使用 `is_active` 字段区分活跃和历史的记录：
- **活跃班级**：`is_active = True`
- **历史班级**：`is_active = False`（且 `ended_date` 不为空）
- **活跃竞赛目标**：`is_active = True`
- **历史竞赛目标**：`is_active = False`

## 相关文件
- `app.py` - 主要应用文件和路由
- `templates/homepage.html` - 首页模板
- `models.py` - 数据库模型定义

## 注意事项
1. 历史班级和历史竞赛目标按结束时间降序排列
2. 删除操作不可撤销，请谨慎操作
3. 班级关系（学生、课程）使用级联删除，删除班级会同时删除相关数据
