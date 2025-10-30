# 部署修复说明

## 问题
应用启动失败，返回404错误，之后又是数据库表不存在的500错误。

## 原因
1. `app.py` 缺少首页路由（`/`）
2. 数据库表在应用启动时没有被创建（`create_tables()`只在`if __name__ == "__main__"`中执行，在Render环境中不会执行）

## 解决方案
已修复以下问题：

### 1. 添加首页路由
```python
@app.route('/')
def index():
    """首页"""
    # 渲染homepage.html模板
```

### 2. 添加课堂路由
```python
@app.route('/classroom/<class_id>')
def classroom(class_id):
    """课堂页面"""
    # 渲染classroom.html模板
```

### 3. 添加班级模型
```python
class SimpleClass(db.Model):
    __tablename__ = 'simple_classes'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 4. 修复数据库初始化（重要！）
**核心问题**：在Render环境中，`if __name__ == "__main__"`块不会执行，导致表没有被创建。

**解决方案**：在模块级别直接调用初始化函数
```python
def init_database():
    """初始化数据库表"""
    with app.app_context():
        db.create_all()
        # 创建默认班级

# 在所有模型定义之后立即调用
init_database()
```

### 5. 修复数据库配置
- 添加了对DATABASE_URL缺失的处理
- 当DATABASE_URL未设置时，默认// 使用SQLite数据库

### 6. 初始化默认班级
- 应用启动时自动创建一个"默认班级"

## 部署步骤

### 方法1: 使用Render Dashboard
1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 找到您的 `math-classroom-app` 服务
3. 点击 "Manual Deploy" -> "Deploy latest commit"
4. 等待部署完成

### 方法2: 推送代码到GitHub
```bash
git add app.py
git commit -m "修复启动问题：添加首页路由"
git push origin main
```

Render会自动检测到新提交并开始部署。

## 验证部署
部署完成后，访问：
```
https://classroom-p1f7.onrender.com
```

应该能看到主页，而不是404错误。

## 预期结果
- ✅ 首页正常显示
- ✅ 可以看到班级列表
- ✅ 可以进入课堂页面
- ✅ API接口正常工作

## 故障排查
如果仍然有问题，请检查：

1. **数据库连接**
   - 确认 `DATABASE_URL` 环境变量已正确设置
   - 检查数据库服务是否运行

2. **日志信息**
   - 在Render Dashboard查看应用日志
   - 查找错误信息

3. **环境变量**
   - `DATABASE_URL` - 数据库连接字符串
   - `SECRET_KEY` - Flask会话密钥
   - `USE_DATABASE` - 应设置为 "true"

