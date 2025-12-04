import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 如果响应包含token，保存到localStorage
    if (res.token) {
      localStorage.setItem('token', res.token)
    }

    return res
  },
  (error) => {
    console.error('响应错误:', error)

    const response = error.response
    const status = response ? response.status : null

    switch (status) {
      case 400:
        // 对于登录接口，不显示通用错误，让业务逻辑处理
        // 其他接口可以显示通用错误
        if (!error.config.url.includes('/auth/login/')) {
          ElMessage.error('请求参数错误')
        }
        break
      case 401:
        ElMessage.error('未授权，请重新登录')
        localStorage.removeItem('token')
        router.push('/login')
        break
      case 403:
        ElMessage.error('无权限访问')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 500:
        ElMessage.error('服务器内部错误')
        break
      default:
        if (error.message === 'Network Error') {
          ElMessage.error('网络连接失败，请检查网络')
        } else {
          ElMessage.error('请求失败，请稍后重试')
        }
    }

    return Promise.reject(error)
  }
)

export default request