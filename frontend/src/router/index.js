import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由组件懒加载
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const ExamTaking = () => import('@/views/ExamTaking.vue')
const ExamResult = () => import('@/views/ExamResult.vue')

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '个人工作台',
      requiresAuth: true
    }
  },
  {
    path: '/exam/:id',
    name: 'ExamTaking',
    component: ExamTaking,
    meta: {
      title: '在线考试',
      requiresAuth: true
    }
  },
  {
    path: '/result/:id',
    name: 'ExamResult',
    component: ExamResult,
    meta: {
      title: '考试结果',
      requiresAuth: true
    }
  },
    {
    // 404页面
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 轨道交通站务人员AI智能考核系统`
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      // 未登录，重定向到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      // 已登录，检查token是否有效
      const isValid = await authStore.checkAuth()
      if (isValid) {
        next()
      } else {
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
      }
    }
  } else {
    // 不需要认证的页面
    if (to.name === 'Login' && authStore.isLoggedIn) {
      // 已登录用户访问登录页，重定向到工作台
      next('/')
    } else {
      next()
    }
  }
})

export default router