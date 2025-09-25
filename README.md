# Math Homework App - 数学作业与课堂系统

这是一个集成了数学作业处理和智能课堂管理功能的Flask应用。

## 功能特性

### 🏠 作业系统
- 文件上传处理
- 演示文稿管理
- 作业批改功能

### 🎓 课堂系统
- 实时学生管理
- 互动答题系统
- 学习报告生成
- PDF报告下载

## 项目结构

```
math-homework-app/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖包
├── classroom/            # 课堂模块
│   ├── __init__.py
│   ├── routes.py         # 课堂路由
│   └── models.py         # 数据库模型
├── templates/            # 模板文件
│   ├── base.html
│   ├── homework_index.html
│   ├── classroom.html
│   ├── student_report.html
│   ├── student_report_print.html
│   └── reports.html
├── static/              # 静态文件
│   ├── css/
│   └── js/
└── uploads/             # 上传文件目录
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
- 作业系统主页: http://127.0.0.1:5000/
- 课堂系统: http://127.0.0.1:5000/classroom/

## 部署到Render

### 1. 上传代码到GitHub
```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/math-homework-app.git
git push -u origin main
```

### 2. 在Render中部署
1. 打开Render → 找到你的math-homework-app → 进入Settings
2. 在Connect部分，绑定你刚刚上传的GitHub仓库
3. 设置启动命令:
   ```
   nginx
   gunicorn app:app
   ```
4. 配置环境变量（如果需要）:
   - `DATABASE_URL`: 你的数据库连接URL
5. 点击Deploy latest commit

### 3. 数据库配置
- 如果你已经有math-homework-db数据库，在Render的Dashboard → math-homework-db → Connections里能看到DATABASE_URL
- 把这个URL配置成环境变量(DATABASE_URL)
- 应用会自动连接到数据库并创建必要的表

## API接口

### 作业系统
- `GET /` - 作业系统主页
- `POST /upload` - 文件上传
- `POST /process` - 处理演示文稿
- `GET /download/<filename>` - 下载文件

### 课堂系统
- `GET /classroom/` - 课堂主页
- `POST /classroom/start_class` - 开始课堂
- `POST /classroom/add_student` - 添加学生
- `POST /classroom/submit_student_answer` - 学生提交答案
- `POST /classroom/judge_answers` - 评判答案
- `POST /classroom/next_round` - 进入下一轮
- `GET /classroom/get_classroom_data` - 获取课堂数据
- `POST /classroom/reset_classroom` - 重置课堂
- `POST /classroom/create_demo_data` - 创建演示数据
- `GET /classroom/generate_student_report/<student_name>` - 生成学生报告
- `GET /classroom/generate_student_pdf/<student_name>` - 下载PDF报告
- `GET /classroom/reports` - 报告列表

## 数据库模型

### Student（学生）
- id: 主键
- name: 学生姓名
- score: 得分
- total_rounds: 总轮次
- correct_rounds: 正确轮次
- last_answer_time: 最后答题时间
- expression: 表情状态
- animation: 动画状态
- avatar_color: 头像颜色

### Submission（提交记录）
- id: 主键
- student_id: 学生ID
- student_name: 学生姓名
- round_number: 轮次
- answer: 答案
- is_correct: 是否正确
- earned_score: 得分
- answer_time: 答题时间

### ClassroomSession（课堂会话）
- id: 主键
- session_name: 会话名称
- is_active: 是否活跃
- current_round: 当前轮次
- round_active: 轮次是否活跃
- correct_answer: 正确答案

### RoundResult（轮次结果）
- id: 主键
- session_id: 会话ID
- round_number: 轮次
- correct_answer: 正确答案

## 技术栈

- **后端**: Flask, SQLAlchemy
- **数据库**: PostgreSQL / SQLite
- **前端**: Bootstrap, Chart.js
- **PDF生成**: ReportLab
- **部署**: Render

## 开发说明

### 添加新功能
1. 在`classroom/routes.py`中添加新的路由
2. 在`classroom/models.py`中添加新的数据模型
3. 在`templates/`中添加对应的HTML模板
4. 更新`requirements.txt`添加新的依赖

### 数据库迁移
```bash
# 在应用上下文中运行
from classroom.models import db
db.create_all()
```

## 许可证

MIT License