# 铁路车站员工智能评估系统

一个基于 Django REST Framework + Vue 3 的全栈智能评估系统，专为铁路车站员工培训与考核设计。

## 项目简介

本系统采用智能算法实现个性化试卷生成和员工能力评估，帮助车站管理员和员工进行针对性的培训和能力提升。

### 核心特性

- **智能组卷算法**：基于用户薄弱点、基础巩固和新题探索的个性化试卷生成
- **能力画像分析**：动态追踪用户各维度能力水平，生成可视化雷达图
- **多题型支持**：单选、多选、判断、主观题全面覆盖
- **AI 智能评分**：主观题自动评分（集成 DeepSeek API）
- **多维度标签体系**：角色、岗位、应急场景、综合能力分类
- **完整的考试流程**：组卷、开始、答题、提交、查看结果全流程支持

---

## 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Django | 4.2.27 | Web 框架 |
| Django REST Framework | 3.16.1 | RESTful API |
| djangorestframework_simplejwt | 5.5.1 | Token 认证 |
| django-cors-headers | 4.9.0 | 跨域支持 |
| pandas | 2.3.3 | 数据处理 |
| openpyxl | 3.1.5 | Excel 操作 |
| Pillow | 11.3.0 | 图像处理 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.3.8 | 前端框架 |
| Vite | 5.0.0 | 构建工具 |
| Element Plus | 2.4.4 | UI 组件库 |
| ECharts | 5.4.3 | 数据可视化 |
| Pinia | 2.1.7 | 状态管理 |
| Vue Router | 4.2.5 | 路由管理 |
| Axios | 1.6.2 | HTTP 客户端 |

### 部署技术

- Docker + Docker Compose
- Nginx（前端服务）
- GitHub Actions CI/CD

---

## 项目结构

```
Staff-assessment-system/
├── backend/                        # Django 后端
│   ├── config/                     # 项目配置
│   │   ├── settings.py            # Django 设置
│   │   ├── urls.py                # 根路由配置
│   │   └── wsgi.py                # WSGI 配置
│   ├── users/                      # 用户管理模块
│   │   ├── models.py              # 用户模型（扩展 AbstractUser）
│   │   ├── serializers.py         # 用户序列化器
│   │   └── views.py               # 用户视图
│   ├── core/                       # 核心考试模块
│   │   ├── models.py              # 标签、题目、试卷模型
│   │   ├── serializers.py         # 考试相关序列化器
│   │   ├── views.py               # 考试视图
│   │   └── services.py            # 智能组卷算法
│   ├── analysis/                   # 能力分析模块
│   │   ├── models.py              # 能力画像模型
│   │   ├── views.py               # 分析 API
│   │   └── algorithms.py          # 能力更新算法
│   ├── requirements.txt            # Python 依赖
│   ├── Dockerfile                 # Docker 镜像配置
│   └── manage.py                  # Django 管理脚本
│
├── frontend/                       # Vue.js 前端
│   ├── src/
│   │   ├── views/                 # 页面组件
│   │   │   ├── Login.vue         # 登录页
│   │   │   ├── Dashboard.vue     # 个人工作台
│   │   │   ├── ExamTaking.vue    # 答题界面
│   │   │   ├── ExamResult.vue    # 考试结果
│   │   │   └── AdminDashboard.vue # 管理后台
│   │   ├── components/            # 可复用组件
│   │   ├── router/                # 路由配置
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── api/                   # API 服务层
│   │   └── App.vue                # 根组件
│   ├── package.json               # Node.js 依赖
│   ├── vite.config.js            # Vite 配置
│   ├── Dockerfile                # Docker 镜像配置
│   └── nginx.conf                # Nginx 配置
│
├── docker-compose.yml             # Docker 编排配置
├── .github/workflows/             # CI/CD 工作流
└── README.md                      # 项目文档
```

---

## 数据模型

### 用户模型 (User)

扩展 Django AbstractUser，添加以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| job_number | String | 工号 |
| position | String | 岗位 |
| department | String | 部门 |

### 标签 (Tag)

题目分类标签，支持四种类型：

| 类型 | 说明 |
|------|------|
| role | 角色标签（如：值班站长、站务员） |
| position | 岗位标签 |
| emergency | 应急场景标签 |
| comprehensive | 综合能力标签 |

### 题目 (Question)

| 字段 | 类型 | 说明 |
|------|------|------|
| type | String | 题型：single/multiple/true_false/subjective |
| content | Text | 题目内容 |
| options | JSON | 选项（单选、多选、判断题） |
| answer | String | 正确答案 |
| difficulty | Integer | 难度等级 (1-5) |
| tags | ManyToMany | 关联标签 |

### 试卷 (ExamPaper)

| 字段 | 类型 | 说明 |
|------|------|------|
| user | ForeignKey | 所属用户 |
| questions | ManyToMany | 包含题目 |
| status | String | 状态：not_started/in_progress/completed |
| reason | String | 生成原因：daily_practice/error_review/mandatory_assessment |
| time_limit | Integer | 时长（分钟） |

### 能力画像 (CapabilityProfile)

| 字段 | 类型 | 说明 |
|------|------|------|
| user | ForeignKey | 所属用户 |
| tag | ForeignKey | 关联标签 |
| score | Float | 能力得分 (0-100) |

---

## API 接口文档

### 认证接口 `/api/auth/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login/` | 用户登录，返回 JWT Token |
| POST | `/logout/` | 用户登出 |
| GET | `/profile/` | 获取当前用户信息 |

### 考试接口 `/api/exam/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/generate/` | 智能生成试卷 |
| GET | `/` | 获取用户考试列表 |
| GET | `/{id}/` | 获取试卷详情 |
| POST | `/{id}/start/` | 开始考试 |
| POST | `/{id}/submit/` | 提交答案 |
| DELETE | `/{id}/delete/` | 删除试卷 |

### 能力分析接口 `/api/analysis/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/radar/` | 获取雷达图数据 |
| GET | `/summary/` | 获取能力概要 |
| GET | `/trend/` | 获取趋势分析 |
| GET | `/recommendations/` | 获取学习建议 |

### 题目管理接口 `/api/questions/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 获取题目列表 |
| POST | `/` | 创建题目 |
| GET | `/{id}/` | 获取题目详情 |
| PUT | `/{id}/` | 更新题目 |
| DELETE | `/{id}/` | 删除题目 |

---

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose（可选）

### 方法一：Docker 部署（推荐）

1. **克隆项目**

```bash
git clone https://github.com/yourusername/Staff-assessment-system.git
cd Staff-assessment-system
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **访问应用**

- 前端：http://localhost:8082
- 后端 API：http://localhost:8081/api

### 方法二：本地开发

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3001

---

## 智能算法说明

### 智能组卷算法

系统根据用户能力画像，按照以下比例生成个性化试卷：

1. **薄弱点强化 (50%)**：优先选择用户能力得分较低的标签对应题目
2. **新题探索 (50%)**：随机选择新题目，拓展知识面

### 能力更新算法

每次考试后，系统使用加权移动平均算法更新用户能力：

```
new_score = (old_score × 0.7) + (current_accuracy × 100 × 0.3)
```

- 权重 0.7：保留历史能力水平
- 权重 0.3：融入最新表现

### 24小时排重机制

用户在 24 小时内已做过的题目不会再次出现，确保练习新鲜度。

---

## 默认账号

系统预置以下测试账号（密码均为 `123456`）：

| 用户名 | 角色 | 说明 |
|--------|------|------|
| admin | 管理员 | 系统管理员 |
| 值班站长 | 站务人员 | 值班站长角色 |
| 站务员 | 站务人员 | 普通站务员 |
| 客运值班员 | 站务人员 | 客运值班员角色 |

---

## 配置说明

### 后端配置 (backend/config/settings.py)

```python
# CORS 配置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://localhost:8082",
]

# AI 评分配置
DEEPSEEK_API_KEY = "your_api_key"  # DeepSeek API Key
```

### 前端配置 (frontend/vite.config.js)

```javascript
server: {
  port: 3001,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

---

## 生产部署

### 使用 GitHub Actions 自动部署

项目已配置 GitHub Actions 工作流，代码推送到 main 分支后自动部署：

1. 配置服务器 SSH 密钥到 GitHub Secrets
2. 配置以下环境变量：
   - `SSH_HOST`: 服务器地址
   - `SSH_USERNAME`: SSH 用户名
   - `SSH_PRIVATE_KEY`: SSH 私钥
   - `DEPLOY_PATH`: 部署路径

3. 推送代码触发自动部署：

```bash
git add .
git commit -m "deploy"
git push origin main
```

### 手动部署

```bash
# 服务器上拉取代码
git pull origin main

# 重建并启动容器
docker-compose down
docker-compose up -d --build
```

---

## 功能截图

### 登录界面
- 用户名密码登录
- Token 认证机制

### 个人工作台
- 能力雷达图可视化
- 最近考试记录
- 快速开始考试入口

### 答题界面
- 题目导航
- 实时计时
- 答案自动保存

### 考试结果
- 得分统计
- 错题解析
- 能力变化趋势

---

## 常见问题

### Q: 如何修改默认账号密码？

A: 使用 Django 管理命令修改密码：

```bash
python manage.py changepassword <username>
```

### Q: 如何导入题目？

A: 可以通过 Django Admin 后台手动添加，或使用 API 批量导入题目数据。

### Q: 如何配置 AI 评分？

A: 在 `settings.py` 中配置 DeepSeek API Key，系统将对主观题进行自动评分。

### Q: 数据库如何迁移到生产环境？

A: 修改 `settings.py` 中的数据库配置，改用 PostgreSQL 或 MySQL：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 开发计划

- [ ] 支持批量导入题目（Excel/CSV）
- [ ] 增加考试统计分析功能
- [ ] 支持自定义组卷策略
- [ ] 增加学习报告导出功能
- [ ] 支持移动端适配

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。
