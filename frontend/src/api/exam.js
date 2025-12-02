import request from './request'

// 生成智能试卷
export function generateExam(data) {
  return request({
    url: '/exam/generate/',
    method: 'post',
    data
  })
}

// 获取试卷列表
export function getExamList(params = {}) {
  return request({
    url: '/exam/',
    method: 'get',
    params
  })
}

// 获取试卷详情
export function getExamDetail(id) {
  return request({
    url: `/exam/${id}/`,
    method: 'get'
  })
}

// 开始考试
export function startExam(id) {
  return request({
    url: `/exam/${id}/start/`,
    method: 'post'
  })
}

// 提交考试
export function submitExam(id, data) {
  return request({
    url: `/exam/${id}/submit/`,
    method: 'post',
    data
  })
}