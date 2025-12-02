<template>
  <div class="login-container">
    <div class="login-form">
      <div class="login-title">
        <el-icon size="40" color="#409EFF">
          <User />
        </el-icon>
        <h2>轨道交通站务人员智能考核系统</h2>
      </div>

      <div class="login-subtitle">
        请使用您的工号和密码登录
      </div>

      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        @submit.prevent="handleLogin"
        size="large"
      >
        <el-form-item prop="job_number">
          <el-input
            v-model="loginForm.job_number"
            placeholder="工号"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            size="large"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 演示账号信息 -->
      <el-divider content-position="left">
        <span style="color: #909399; font-size: 12px;">演示账号</span>
      </el-divider>

      <div class="demo-accounts">
        <div class="account-item">
          <strong>管理员:</strong> admin / admin123
          <small>(或工号: ADMIN001)</small>
        </div>
        <div class="account-item">
          <strong>值班站长:</strong> zhangsan / password123
          <small>(或工号: ST001)</small>
        </div>
        <div class="account-item">
          <strong>站务员:</strong> lisi / password123
          <small>(或工号: ST002)</small>
        </div>
        <div class="account-item">
          <strong>客运值班员:</strong> wangwu / password123
          <small>(或工号: ST003)</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const formRef = ref()

const loginForm = reactive({
  job_number: '',
  password: ''
})

// 表单验证规则
const rules = {
  job_number: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { min: 3, max: 20, message: '工号长度应在3-20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度应在6-128个字符之间', trigger: 'blur' }
  ]
}

// 登录处理
const handleLogin = async () => {
  console.log('登录处理开始')
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true
    console.log('表单验证通过，登录数据:', loginForm)

    const result = await authStore.loginAction(loginForm)
    console.log('登录结果:', result)

    if (result.success) {
      ElMessage.success('登录成功')
      console.log('登录成功，准备跳转')

      // 检查是否有重定向地址
      const redirect = route.query.redirect || '/'
      console.log('跳转到:', redirect)

      // 使用 nextTick 确保DOM更新后再跳转
      await nextTick()
      router.push(redirect)
    } else {
      console.error('登录失败:', result.error)
      ElMessage.error(result.error)
    }
  } catch (error) {
    console.error('登录异常:', error)
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 页面加载时检查登录状态
onMounted(() => {
  console.log('Login组件mounted，当前登录状态:', authStore.isLoggedIn)

  // 如果已经登录，重定向到工作台
  if (authStore.isLoggedIn) {
    router.push('/')
  }

  // 自动填充演示账号（开发环境）
  if (import.meta.env.DEV) {
    loginForm.job_number = 'admin'
    loginForm.password = 'admin123'
  }
})
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  position: relative;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.3;
}

.login-form {
  background: rgba(255, 255, 255, 0.98);
  padding: 48px;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  width: 440px;
  max-width: 90%;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.login-form:hover {
  transform: translateY(-2px);
  box-shadow: 0 25px 70px rgba(0, 0, 0, 0.2);
}

.login-title {
  text-align: center;
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.login-title h2 {
  margin: 0;
  color: #303133;
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  text-align: center;
  margin-bottom: 36px;
  color: #606266;
  font-size: 15px;
  line-height: 1.5;
}

.demo-accounts {
  margin-top: 28px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.account-item {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.5;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.account-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
  transform: translateX(2px);
}

.account-item strong {
  color: #303133;
  min-width: 100px;
  display: inline-block;
  font-weight: 600;
}

:deep(.el-form-item__content) {
  line-height: normal;
}

:deep(.el-input) {
  margin-bottom: 8px;
}

:deep(.el-input__wrapper) {
  height: 52px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
  border-color: #409eff;
}

:deep(.el-button) {
  height: 52px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

@media (max-width: 480px) {
  .login-form {
    padding: 30px 20px;
    width: 95%;
  }

  .login-title h2 {
    font-size: 18px;
  }

  .login-subtitle {
    font-size: 13px;
  }
}
</style>