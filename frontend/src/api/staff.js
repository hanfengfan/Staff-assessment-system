import request from './request'

// 员工列表，params: page, page_size, search, position, station, zone, is_active
export function getStaffList(params) {
  return request({ url: '/staff/', method: 'get', params })
}

export function createStaff(data) {
  return request({ url: '/staff/', method: 'post', data })
}

export function updateStaff(id, data) {
  return request({ url: `/staff/${id}/`, method: 'patch', data })
}

export function deleteStaff(id) {
  return request({ url: `/staff/${id}/`, method: 'delete' })
}

// 岗位/车站/站区各维度的可选值及人数
export function getStaffDimensions() {
  return request({ url: '/staff/dimensions/', method: 'get' })
}
