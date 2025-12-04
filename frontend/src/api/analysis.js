import request from './request'

// 获取能力雷达图数据
export function getRadarData(userId = null) {
  const params = userId ? { user_id: userId } : {}
  return request({
    url: '/radar/',
    method: 'get',
    params
  })
}

// 获取用户能力总结
export function getCapabilitySummary(userId = null) {
  const params = userId ? { user_id: userId } : {}
  return request({
    url: '/summary/',
    method: 'get',
    params
  })
}

// 获取能力趋势数据
export function getTrendData(days = 30, userId = null) {
  const params = userId ? { days, user_id: userId } : { days }
  return request({
    url: '/trend/',
    method: 'get',
    params
  })
}

// 获取用户列表（管理员专用）
export function getUserList() {
  return request({
    url: '/users/',
    method: 'get'
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