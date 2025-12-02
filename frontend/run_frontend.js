#!/usr/bin/env node
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

// ES模块中获取 __dirname
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

console.log('='.repeat(60))
console.log('轨道交通站务人员AI智能考核系统 - 前端启动脚本')
console.log('='.repeat(60))

// 检查 package.json 是否存在
if (!fs.existsSync(path.join(__dirname, 'package.json'))) {
  console.error('❌ 错误: package.json 文件不存在')
  console.error('请确保在项目根目录下运行此脚本')
  process.exit(1)
}

// 检查 node_modules 是否存在
if (!fs.existsSync(path.join(__dirname, 'node_modules'))) {
  console.log('📦 正在安装依赖包...')

  const npmInstall = spawn('npm', ['install'], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname
  })

  npmInstall.on('close', (code) => {
    if (code === 0) {
      console.log('✅ 依赖包安装完成')
      startDevServer()
    } else {
      console.error('❌ 依赖包安装失败')
      process.exit(1)
    }
  })
} else {
  console.log('✅ 依赖包已安装')
  startDevServer()
}

function startDevServer() {
  console.log('\n🚀 启动开发服务器...')
  console.log('📍 本地地址: http://localhost:5173')
  console.log('🔗 后端API: http://localhost:8000/api')
  console.log('🌐 完整地址: http://localhost:5173')
  console.log('\n⚡ 功能特性:')
  console.log('  • Vue 3 + Composition API')
  console.log('  • Element Plus UI 组件库')
  console.log('  • ECharts 数据可视化')
  console.log('  • Vite 快速构建')
  console.log('  • 热更新支持')
  console.log('  • 响应式设计')
  console.log('\n📱 访问地址:')
  console.log('  • 桌面端: http://localhost:5173')
  console.log('  • 手机端: http://<你的IP>:5173')
  console.log('\n🔐 默认账号:')
  console.log('  • 管理员: admin / admin123')
  console.log('  • 值班站长: ST001 / password123')
  console.log('  • 站务员: ST002 / password123')
  console.log('  • 客运值班员: ST003 / password123')
  console.log('\n📝 使用说明:')
  console.log('  • 确保后端服务正在运行 (python manage.py runserver)')
  console.log('  • 确保后端数据已初始化 (python manage.py init_sample_data)')
  console.log('  • 使用 Ctrl+C 停止服务器')
  console.log('  • 代码修改后会自动热更新')
  console.log('\n' + '='.repeat(60))

  const devServer = spawn('npm', ['run', 'dev'], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname
  })

  devServer.on('close', (code) => {
    console.log(`\n🛑 开发服务器已停止 (退出码: ${code})`)
  })

  // 处理 Ctrl+C
  process.on('SIGINT', () => {
    console.log('\n\n🛑 正在停止开发服务器...')
    devServer.kill('SIGINT')
  })
}