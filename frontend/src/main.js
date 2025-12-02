import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 注册 Element Plus 图标
Object.entries(ElementPlusIconsVue).forEach(([key, component]) => {
  app.component(key, component)
})
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  console.error('Vue实例:', vm)
  console.error('错误信息:', info)
}

app.mount('#app')