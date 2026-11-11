import request from './request'

// 当前生效的组卷规则
export function getExamConfig() {
  return request({ url: '/exam-config/', method: 'get' })
}

// 保存组卷规则
export function saveExamConfig(data) {
  return request({ url: '/exam-config/', method: 'put', data })
}

// 题库专业、一级目录及各题型/难度的题量
export function getExamConfigOptions() {
  return request({ url: '/exam-config/options/', method: 'get' })
}
