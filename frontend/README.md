# 轨道交通站务人员AI智能考核系统 - 前端

## 项目概述

基于 Vue 3 + Vite + Element Plus + ECharts 开发的现代化Web应用，用于轨道交通站务人员的在线考核和能力评估。

## 技术栈

- **前端框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **数据可视化**: ECharts 5.x
- **HTTP客户端**: Axios
- **状态管理**: Pinia
- **路由管理**: Vue Router 4
- **开发语言**: JavaScript + Vue SFC

## 功能特性

### 1. 用户认证
- 🔐 用户登录/登出
- 📱 响应式设计
- 🛡️ Token认证机制
- 🔄 自动状态同步

### 2. 个人工作台
- 📊 能力雷达图可视化
- 📈 个人能力数据分析
- 🎯 个性化学习建议
- 📋 考试历史记录
- 🚀 一键开始智能考核

### 3. 在线考试
- 📝 智能组卷算法
- ⏱️ 考试计时功能
- 🔄 题目导航系统
- ✅ 实时答题进度
- 💾 自动保存答案

### 4. 答题体验
- 🎨 现代化UI设计
- 📱 移动端适配
- ⚡ 流畅的交互动画
- 🎯 清晰的题目展示
- 🔢 多种题型支持

### 5. 结果分析
- 📊 详细的得分分析
- 📈 能力表现统计
- ❌ 错题解析展示
- 💡 学习建议推荐
- 📥 结果分享功能

## 项目结构

```
frontend/
├── public/                     # 静态资源
│   └── favicon.ico
├── src/
│   ├── api/                # API接口封装
│   │   ├── request.js      # Axios拦截器配置
│   │   ├── auth.js         # 认证相关API
│   │   ├── exam.js         # 考试相关API
│   │   └── analysis.js     # 数据分析API
│   ├── components/           # 公共组件
│   │   └── RadarChart.vue  # 能力雷达图组件
│   ├── router/              # 路由配置
│   │   └── index.js       # 路由守卫和配置
│   ├── stores/              # Pinia状态管理
│   │   ├── auth.js         # 用户认证状态
│   │   └── exam.js         # 考试状态管理
│   ├── views/               # 页面组件
│   │   ├── Login.vue       # 登录页面
│   │   ├── Dashboard.vue   # 个人工作台
│   │   ├── ExamTaking.vue  # 答题界面
│   │   └── ExamResult.vue  # 考试结果
│   ├── App.vue             # 根组件
│   ├── main.js             # 应用入口
│   └── style.css           # 全局样式
├── index.html              # HTML模板
├── vite.config.js          # Vite配置
├── package.json            # 依赖配置
└── README.md               # 项目说明
```

## 核心算法实现

### 1. 智能答题导航
```javascript
// 题目导航算法
const goToQuestion = (index) => {
  if (index >= 0 && index < questions.length) {
    currentQuestionIndex.value = index
  }
}

// 答题进度计算
const progressPercentage = computed(() => {
  if (questions.length === 0) return 0
  return Math.round((answeredCount / questions.length) * 100)
})
```

### 2. 答案处理机制
```javascript
// 支持多种题型
const handleSelectOption = (questionId, optionKey) => {
  const question = questions.find(q => q.id === questionId)

  switch (question.question_type) {
    case 'single':
      // 单选题：直接替换答案
      saveAnswer(questionId, optionKey)
      break
    case 'multiple':
      // 多选题：处理多选逻辑
      handleMultipleChoice(questionId, optionKey)
      break
    case 'true_false':
      // 判断题：直接替换答案
      saveAnswer(questionId, optionKey)
      break
  }
}
```

### 3. 考试计时系统
```javascript
// 精确计时器
const startTimer = () => {
  examTimer.value = setInterval(() => {
    examTime.value++
  }, 1000)
}

// 格式化时间显示
const formatTime = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
```

## 响应式设计

### 断点配置
- **桌面端**: >= 1024px
- **平板端**: 768px - 1023px
- **移动端**: < 768px

### 适配特性
- ✅ 流式布局适配
- ✅ 弹性间距调整
- ✅ 字体大小优化
- ✅ 触摸操作优化
- ✅ 移动端导航优化

## 性能优化

### 1. 组件懒加载
```javascript
// 路由懒加载
const Dashboard = () => import('@/views/Dashboard.vue')
const ExamTaking = () => import('@/views/ExamTaking.vue')
```

### 2. 状态管理优化
- Pinia模块化设计
- 计算属性缓存
- 按需状态订阅
- 内存泄漏防护

### 3. 构建优化
- Vite快速构建
- 自动代码分割
- 资源压缩优化
- 浏览器缓存策略

## 开发指南

### 1. 环境准备
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 2. 开发环境配置
- **开发地址**: http://localhost:3000
- **API代理**: /api -> http://127.0.0.1:8000
- **热更新**: 支持组件热重载
- **开发工具**: Vue DevTools

### 3. 代码规范
- ✅ Vue 3 Composition API
- ✅ 标签化模板
- ✅ TypeScript支持(可选)
- ✅ ESLint代码检查
- ✅ Prettier代码格式化

## API集成

### 1. 请求拦截
```javascript
// 统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    switch (status) {
      case 401:
        router.push('/login')
        break
      // ... 其他错误处理
    }
  }
)
```

### 2. 状态同步
```javascript
// Token认证
const token = localStorage.getItem('token')
if (token) {
  request.defaults.headers['Authorization'] = `Token ${token}`
}

// 用户状态持久化
const checkAuth = async () => {
  if (token.value) {
    try {
      const response = await getUserInfo()
      user.value = response
      return true
    } catch (error) {
      clearAuth()
      return false
    }
  }
  return false
}
```

## 浏览器支持

### 现代浏览器
- ✅ Chrome >= 88
- ✅ Firefox >= 78
- ✅ Safari >= 14
- ✅ Edge >= 88

### ES6+ 特性支持
- ✅ ES Modules
- ✅ Async/Await
- ✅ Promise API
- ✅ Proxy 对象
- ✅ 展开运算符

## 部署说明

### 1. 构建生产版本
```bash
# 构建
npm run build

# 预览构建结果
npm run preview
```

### 2. 部署配置
- **静态资源**: Nginx 静态文件服务
- **API代理**: 后端接口反向代理
- **HTTPS支持**: SSL证书配置
- **缓存策略**: 浏览器缓存优化

### 3. 性能监控
- 📊 首屏加载时间
- ⚡ 资源加载优化
- 📱 移动端性能监控
- 🔧 错误日志收集

## 扩展计划

### 1. 功能增强
- [ ] 离线答题支持
- [ ] 实时消息通知
- [ ] 多语言国际化
- [ ] 主题切换功能
- [ ] 数据导出功能

### 2. 性能优化
- [ ] 虚拟滚动优化
- [ ] 图片懒加载
- [ ] Service Worker缓存
- [ ] CDN资源加速

### 3. 用户体验
- [ ] 键盘快捷键
- [ ] 拖拽排序功能
- [ ] 语音答题支持
- [ ] 无障碍访问优化

## 技术特点

### 1. 现代化架构
- Vue 3 Composition API
- 模块化组件设计
- 统一状态管理
- 标准化API接口

### 2. 优秀的用户体验
- 响应式设计
- 流畅的动画效果
- 直观的交互反馈
- 完善的错误处理

### 3. 高性能表现
- 懒加载优化
- 资源压缩
- 代码分割
- 缓存策略

### 4. 开发友好
- 热更新支持
- TypeScript类型提示
- 丰富的组件库
- 清晰的文档说明

这个前端项目与后端API完美集成，提供了现代化的用户体验和强大的功能特性，为轨道交通站务人员的智能考核提供了优秀的Web界面。