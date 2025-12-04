import { defineStore } from 'pinia'
import { ref, computed, toRaw } from 'vue'
import { login, logout, getUserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    return Boolean(user.value.is_staff)
  })

  // 初始化用户信息（在store创建时立即执行）
  function initUser() {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser)
        user.value = parsedUser
      } catch (error) {
        console.error('解析用户信息失败:', error)
        localStorage.removeItem('user')
      }
    }
  }

  // 立即初始化用户信息
  initUser()

  // 检查认证状态
  async function checkAuth() {
    if (token.value) {
      try {
        const response = await getUserInfo()
        user.value = response
        // 更新localStorage中的用户信息
        localStorage.setItem('user', JSON.stringify(response))
        return true
      } catch (error) {
        console.error('checkAuth 失败:', error)
        // token失效，清除状态
        clearAuth()
        return false
      }
    }
    return false
  }

  // 登录
  async function loginAction(credentials) {
    try {
      const response = await login(credentials)
      token.value = response.token
      user.value = response.user

      // 保存到localStorage
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))

      return { success: true }
    } catch (error) {
      // 优先显示后端返回的具体错误信息
      if (error.response?.data?.non_field_errors) {
        // Django REST Framework 通常使用 non_field_errors
        return {
          success: false,
          error: error.response.data.non_field_errors[0]
        }
      } else if (error.response?.data?.error) {
        return {
          success: false,
          error: error.response.data.error
        }
      } else if (error.response?.data?.detail) {
        return {
          success: false,
          error: error.response.data.detail
        }
      } else {
        // 只在真正没有具体错误信息时才显示通用错误
        return {
          success: false,
          error: '工号或密码错误'
        }
      }
    }
  }

  // 登出
  async function logoutAction() {
    try {
      await logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 清除认证状态
  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    // 状态
    token,
    user,
    isLoggedIn,
    isAdmin,

    // 方法
    checkAuth,
    loginAction,
    logoutAction,
    clearAuth,
    initUser
  }
})