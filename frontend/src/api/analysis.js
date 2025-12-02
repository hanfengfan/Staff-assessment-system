import request from './request'

// 获取能力雷达图数据
export function getRadarData() {
  return request({
    url: '/radar/',
    method: 'get'
  })
}

// 获取用户能力总结
export function getCapabilitySummary() {
  return request({
    url: '/summary/',
    method: 'get'
  })
}

// 获取能力趋势数据
export function getTrendData(days = 30) {
  return request({
    url: '/trend/',
    method: 'get',
    params: { days }
  })
}

// 获取学习建议
export function getRecommendations() {
  return request({
    url: '/recommendations/',
    method: 'get'
  })
}

// 获取能力画像列表
export function getCapabilityProfiles() {
  return request({
    url: '/capability-profiles/',
    method: 'get'
  })
}