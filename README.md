# 烧脑数学课堂管理系统

这是一个智能数学课堂管理系统，提供班级管理、学生报告和竞赛目标跟踪功能。

## 功能特性

### 🏫 班级管理
- 创建和管理班级
- 学生信息管理
- 班级状态跟踪

### 📊 学生报告
- 个性化学习报告
- 学习进度分析
- 竞赛目标跟踪

### 🎯 竞赛目标
- 设置竞赛目标
- 进度跟踪
- 目标分配

## 项目结构

```
math-classroom-app/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖包
├── render.yaml           # Render部署配置
├── .gitignore           # Git忽略文件
├── templates/            # 模板文件
│   ├── base.html
│   ├── homepage.html
│   ├── classroom.html
│   ├── student_report.html
│   └── reports.html
└── static/              # 静态文件
    ├── css/
    └── js/
```

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境变量配置（可选）
```bash
# 如果使用PostgreSQL数据库
export DATABASE_URL="postgresql://username:password@host:port/database"

# 如果使用SQLite（默认）
# 无需配置，会自动创建 math_homework.db
```

### 3. 运行应用
```bash
python app.py
```

### 4. 访问应用
- 系统主页: http://127.0.0.1:5000/
- 学生报告: http://127.0.0.1:5000/reports

## 部署到Render

### 1. 上传代码到GitHub
```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/math-classroom-app.git
git push -u origin main
```

### 2. 在Render中部署
1. 登录 [Render](https://render.com)
2. 点击 "New +" → "Web Service"
3. 连接你的GitHub仓库
4. 使用以下配置:
   - **Name**: math-classroom-app
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. 点击 "Create Web Service"

### 3. 环境变量配置
- `SECRET_KEY`: 自动生成
- `PORT`: 自动设置

## API接口

### 主要页面
- `GET /` - 系统主页
- `GET /class/<class_id>` - 班级详情
- `GET /class/<class_id>/classroom` - 课堂页面
- `GET /reports` - 报告列表
- `GET /generate_student_report/<student_name>` - 生成学生报告

### 班级管理
- `POST /api/create_class` - 创建班级
- `POST /api/delete_class/<class_id>` - 删除班级
- `POST /api/end_class/<class_id>` - 结束班级

### 竞赛目标
- `POST /api/create_competition_goal` - 创建竞赛目标
- `POST /api/assign_goal_to_class` - 分配目标到班级
- `POST /api/delete_competition_goal/<goal_id>` - 删除竞赛目标

## 数据存储

系统使用JSON文件存储数据，包括：
- 班级信息
- 学生数据
- 竞赛目标
- 课程记录

## 技术栈

- **后端**: Flask
- **前端**: Bootstrap, Chart.js
- **部署**: Render
- **数据存储**: JSON文件

## 开发说明

### 添加新功能
1. 在`app.py`中添加新的路由
2. 在`templates/`中添加对应的HTML模板
3. 更新`requirements.txt`添加新的依赖

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

## 许可证

MIT License