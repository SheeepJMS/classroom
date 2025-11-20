# 页面结构修正说明

## ✅ 修正内容

### 页面流程调整

#### 修正前（错误）：
- `/classroom/<class_id>` → 直接显示答题页面

#### 修正后（正确）：
1. **首页** `/` - 显示所有班级
2. **进入班级** `/classroom/<class_id>` - 班级管理页面
   - 显示学生列表
   - 显示课程列表
   - 添加学生
   - 新建课程
   - 绑定竞赛目标
3. **新建课程后** → 跳转到 `/course/<course_id>` 
4. **课程答题页面** `/course/<course_id>` - 答题界面
   - 调整分数
   - 点击START开始
   - 学生答题
   - 点击BINGO评判
   - 点击Next进入下一轮

### 路由变更

| 路由 | 功能 | 模板 |
|------|------|------|
| `/` | 首页，显示班级列表 | homepage.html |
| `/classroom/<class_id>` | 班级管理 | class_detail.html |
| `/course/<course_id>` | 课程答题 | classroom.html |

### API变更

#### 创建课程API
```python
@app.route('/api/create_course', methods=['POST'])
def create_course():
    # ... 创建课程逻辑 ...
    return jsonify({
        'success': True, 
        'course_id': course_id,
        'redirect_url': f'/course/{course_id}'
    })
```

前端应该在收到这个响应后跳转到 `redirect_url`。

## 🎯 正确的使用流程

1. **创建班级**
   - 首页点击"创建新班级"
   - 输入班级名称

2. **进入班级**
   - 点击"进入班级"
   - 看到班级管理页面

3. **添加学生**
   - 在班级管理页面添加学生
   - 请假的学生不会显示在答题页面

4. **创建课程**
   - 点击"创建课程"按钮
   - 输入课程名称
   - 自动跳转到课程答题页面

5. **开始答题**
   - 调整分数（可选）
   - 点击START
   - 学生答题
   - 评判答案
   - 进入下一轮

## 📝 注意事项

1. `/classroom/<class_id>` 现在是班级管理页面，不再是答题页面
2. `/course/<course_id>` 才是真正的答题页面
3. 必须先创建课程才能进入答题页面
4. 班级管理页面会显示该班级的所有历史课程

## 🔄 前端需要调整

如果前端代码有硬编码的路径，需要更新：
- 从首页进入班级：`/classroom/<class_id>`
- 从班级进入课程：`/course/<course_id>`

**现在页面结构正确了！** ✅







