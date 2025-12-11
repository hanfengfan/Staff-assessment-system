<template>
  <div class="dashboard-container">
    <!-- 用户信息卡片 -->
    <div class="user-info-card">
      <div class="user-header">
        <el-avatar size="large" :icon="UserFilled" />
        <div class="user-details">
          <h2>{{ user?.get_full_name || user?.username }}</h2>
          <p class="user-position">{{ user?.position }} · {{ user?.department }}</p>
        </div>
        <el-button type="danger" plain @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          登出
        </el-button>
      </div>
    </div>

    <!-- 管理员用户选择器 -->
    <div class="user-selector" v-if="isAdmin && userList.length > 0">
      <el-card>
        <template #header>
          <el-icon><UserFilled /></el-icon>
          <span>选择用户</span>
        </template>
        <el-select
          v-model="selectedUserId"
          placeholder="选择要查看的用户"
          @change="handleUserChange"
          style="width: 100%"
        >
          <el-option
            v-for="userItem in userList"
            :key="userItem.id"
            :label="`${userItem.job_number} - ${userItem.username}`"
            :value="userItem.id"
          />
        </el-select>
      </el-card>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <el-icon size="32" color="#409EFF">
          <TrendCharts />
        </el-icon>
        <div class="stat-content">
          <div class="stat-value">{{ capabilitySummary?.overall_score || 0 }}</div>
          <div class="stat-label">
            {{ selectedUserId ? '用户综合能力评分' : '综合能力评分' }}
          </div>
        </div>
      </div>

      <div class="stat-card">
        <el-icon size="32" color="#67C23A">
          <Document />
        </el-icon>
        <div class="stat-content">
          <div class="stat-value">{{ capabilitySummary?.total_exams || 0 }}</div>
          <div class="stat-label">考试次数</div>
        </div>
      </div>

      <div class="stat-card">
        <el-icon size="32" color="#E6A23C">
          <Trophy />
        </el-icon>
        <div class="stat-content">
          <div class="stat-value">{{ capabilitySummary?.recent_accuracy?.toFixed(1) || 0 }}%</div>
          <div class="stat-label">最近准确率</div>
        </div>
      </div>

      <div class="stat-card">
        <el-icon size="32" color="#F56C6C">
          <Warning />
        </el-icon>
        <div class="stat-content">
          <div class="stat-value">{{ capabilitySummary?.weak_tags?.length || 0 }}</div>
          <div class="stat-label">待提升技能</div>
        </div>
      </div>
    </div>

    <div class="dashboard-content">
      <!-- 左侧：能力雷达图和统计信息 -->
      <div class="radar-section">
        <el-card class="custom-card">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>能力雷达图</span>
            </div>
          </template>
          <div class="radar-container">
            <div ref="radarChartRef"></div>
          </div>
        </el-card>

        <!-- 新增：能力详情卡片 -->
        <el-card class="custom-card radar-details-card">
          <template #header>
            <div class="card-header">
              <el-icon><Trophy /></el-icon>
              <span>能力详情</span>
            </div>
          </template>
          <div class="ability-details">
            <div class="detail-item">
              <div class="detail-label">最强能力</div>
              <div class="detail-value strong">
                {{ getStrongestAbility() || '暂无数据' }}
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">待提升能力</div>
              <div class="detail-value weak">
                {{ getWeakestAbility() || '暂无数据' }}
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">平均能力值</div>
              <div class="detail-value average">
                {{ getAverageAbility() || 0 }}分
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：操作区域 -->
      <div class="action-section">
        <!-- 开始考试按钮 - 仅普通用户可见 -->
        <el-card class="custom-card" v-if="!isAdmin">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>每日考核</span>
            </div>
          </template>
          <div class="action-buttons">
            <el-button
              type="primary"
              size="large"
              :loading="generatingExam"
              :disabled="generatingExam"
              @click="handleGenerateExam"
              class="start-exam-btn"
            >
              <el-icon><Promotion /></el-icon>
              {{ generatingExam ? '生成试卷中...' : '开始每日考核' }}
            </el-button>
          </div>
        </el-card>

        <!-- 学习建议 -->
        <el-card class="custom-card" v-if="recommendations.length > 0">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>学习建议</span>
            </div>
          </template>
          <div class="recommendations">
            <el-alert
              v-for="(rec, index) in recommendations.slice(0, 3)"
              :key="index"
              :title="`${rec.tag_name} 需要提升 (当前水平: ${rec.current_level.toFixed(1)})`"
              :type="rec.priority === '高' ? 'warning' : 'info'"
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            >
              <template #default>
                <div>建议重点学习 {{ rec.tag_name }} 相关知识</div>
                <div v-if="rec.available_materials > 0">
                  相关培训资料：{{ rec.available_materials }} 份
                </div>
              </template>
            </el-alert>
          </div>
        </el-card>

        <!-- 管理员入口 -->
        <el-card class="admin-card" v-if="isAdmin">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>管理员功能</span>
            </div>
          </template>
          <div class="admin-actions">
            <el-button
              type="primary"
              size="large"
              :loading="generatingExam"
              :disabled="generatingExam"
              @click="handleGenerateExam"
              class="admin-btn start-exam-btn"
            >
              <el-icon><Promotion /></el-icon>
              {{ generatingExam ? '生成试卷中...' : '开始每日考核' }}
            </el-button>
            <el-button
              type="success"
              size="large"
              @click="goToAdminDashboard"
              class="admin-btn"
            >
              <el-icon><Tools /></el-icon>
              进入管理员控制台
            </el-button>
          </div>
        </el-card>

        <!-- 最近考试记录 -->
        <el-card class="custom-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近考试记录</span>
              <el-tag type="info" size="small" v-if="totalExams > 0">
                共 {{ totalExams }} 条记录
              </el-tag>
            </div>
          </template>
          <div v-if="recentExams.length === 0" class="empty-state">
            <el-empty description="暂无考试记录" />
          </div>
          <div v-else>
            <div class="exam-list">
              <div
                v-for="exam in recentExams"
                :key="exam.id"
                class="exam-item"
                @click="handleViewExamResult(exam.id)"
              >
                <div class="exam-info">
                  <div class="exam-title">{{ exam.title }}</div>
                  <div class="exam-meta">
                    <el-tag :type="getStatusType(exam.status)" size="small">
                      {{ getStatusText(exam.status) }}
                    </el-tag>
                    <span class="exam-date">
                      {{ formatDate(exam.created_at) }}
                    </span>
                  </div>
                </div>
                <div class="exam-score" v-if="exam.status === 'completed'">
                  <div class="score-value">{{ exam.score_obtained?.toFixed(1) || 0 }}</div>
                  <div class="score-total">/ {{ exam.total_score || 100 }}</div>
                </div>
              </div>
            </div>

            <!-- 分页组件 -->
            <div class="pagination-container" v-if="examPagination.total > pageSize">
              <el-pagination
                v-model:current-page="examPagination.current"
                :page-size="pageSize"
                :total="examPagination.total"
                layout="prev, pager, next, jumper"
                @current-change="handlePageChange"
                :background="true"
                :hide-on-single-page="true"
              />
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UserFilled,
  SwitchButton,
  TrendCharts,
  Document,
  Promotion,
  Bell,
  Clock,
  Trophy,
  Warning,
  Setting,
  Tools
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getExamList, generateExam } from '@/api/exam'
import { getRadarData, getCapabilitySummary, getRecommendations, getUserList } from '@/api/analysis'
import { getUserInfo } from '@/api/auth'
import * as echarts from 'echarts'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const generatingExam = ref(false)
const radarChartRef = ref()
const radarChart = ref(null)

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)
const recentExams = ref([])
const radarData = ref([])
const capabilitySummary = ref(null)
const recommendations = ref([])
const userList = ref([])
const selectedUserId = ref(null)

// 分页相关数据
const currentPage = ref(1)
const pageSize = ref(5)
const totalExams = ref(0)
const examPagination = ref({
  current: 1,
  pageSize: 5,
  total: 0
})

// 用户选择处理函数
const handleUserChange = async (userId) => {
  selectedUserId.value = userId
  loading.value = true
  try {
    // 重置分页到第一页
    examPagination.value.current = 1

    // 并行获取所有数据
    const [radarResponse, summaryResponse, recommendationsResponse, examData] = await Promise.all([
      getRadarData(userId),
      getCapabilitySummary(userId),
      getRecommendations(),
      fetchExamData(1, pageSize.value)
    ])

    radarData.value = Array.isArray(radarResponse) ? radarResponse : []
    capabilitySummary.value = summaryResponse || {}
    recommendations.value = Array.isArray(recommendationsResponse?.recommendations) ? recommendationsResponse.recommendations : []
    recentExams.value = Array.isArray(examData?.results) ? examData.results : []
    totalExams.value = examData?.count || 0
    examPagination.value = {
      current: 1,
      pageSize: pageSize.value,
      total: examData?.count || 0
    }

    // 渲染雷达图
    nextTick(() => {
      renderRadarChart()
    })
  } catch (error) {
    console.error('获取用户数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')

    radarData.value = []
    capabilitySummary.value = {}
    recommendations.value = []
    recentExams.value = []
    totalExams.value = 0
  } finally {
    loading.value = false
  }
}

// 获取考试数据
const fetchExamData = async (page = 1, pageSize = 5) => {
  try {
    const response = await getExamList({
      page,
      page_size: pageSize,
      user_id: selectedUserId.value
    })

    return response
  } catch (error) {
    console.error('获取考试数据失败:', error)
    return { results: [], count: 0 }
  }
}

// 获取数据
const fetchDashboardData = async () => {
  loading.value = true

  try {
    // 获取考试数据（第一页）
    const examsResponse = await fetchExamData(1, pageSize.value)

    // 根据用户身份获取不同数据
    const promises = [
      Promise.resolve(examsResponse),
      getRadarData(selectedUserId.value),
      getCapabilitySummary(selectedUserId.value),
      getRecommendations()
    ]

    // 只有管理员才获取用户列表
    if (isAdmin.value) {
      promises.push(getUserList().catch(error => {
        console.warn('获取用户列表失败:', error)
        return []
      }))
    } else {
      promises.push(Promise.resolve([]))
    }

    const [examData, radarResponse, summaryResponse, recommendationsResponse, usersResponse] = await Promise.all(promises)

    // 确保数据结构正确，防止 undefined 错误
    recentExams.value = Array.isArray(examData?.results) ? examData.results : []
    totalExams.value = examData?.count || 0
    examPagination.value = {
      current: 1,
      pageSize: pageSize.value,
      total: examData?.count || 0
    }
    radarData.value = Array.isArray(radarResponse) ? radarResponse : []
    capabilitySummary.value = summaryResponse || {}
    recommendations.value = Array.isArray(recommendationsResponse?.recommendations) ? recommendationsResponse.recommendations : []

    // 管理员设置用户列表
    if (isAdmin && usersResponse) {
      userList.value = Array.isArray(usersResponse) ? usersResponse : []
    }

    // 渲染雷达图
    nextTick(() => {
      renderRadarChart()
    })
  } catch (error) {
    console.error('获取工作台数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')

    // 发生错误时设置默认值，防止页面崩溃
    recentExams.value = []
    totalExams.value = 0
    radarData.value = []
    capabilitySummary.value = {}
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

// 渲染能力雷达图
const renderRadarChart = () => {
  if (!radarChartRef.value) return

  // 销毁旧的图表实例
  if (radarChart.value) {
    radarChart.value.dispose()
  }

  // 创建新的图表实例
  radarChart.value = echarts.init(radarChartRef.value)

  // 确保数据存在
  const validRadarData = Array.isArray(radarData.value) && radarData.value.length > 0 ? radarData.value : []

  const option = {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: validRadarData.map(item => ({
        name: item?.tag || '未知',
        max: 100
      })),
      radius: '70%'
    },
    series: [{
      name: '能力水平',
      type: 'radar',
      data: [{
        value: validRadarData.map(item => Math.round(item?.score || 0)),
        name: '个人能力',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.2)'
        },
        lineStyle: {
          color: '#409EFF',
          width: 2
        }
      }]
    }]
  }

  radarChart.value.setOption(option)

  // 响应式调整
  const resizeChart = () => {
    if (radarChart.value) {
      radarChart.value.resize()
    }
  }

  window.addEventListener('resize', resizeChart)
}

// 生成考试
const handleGenerateExam = async () => {
  try {
    await ElMessageBox.confirm(
      '确认开始新的每日考核吗？系统将根据您的能力水平智能生成试卷。',
      '开始考试',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    generatingExam.value = true

    // 调用生成考试API
    const response = await generateExam({
      reason: 'daily_practice',
      question_count: 15
    })

    if (response.id) {
      ElMessage.success('试卷生成成功！正在跳转到考试页面...')

      // 生成成功后跳转到考试页面
      setTimeout(() => {
        router.push(`/exam/${response.id}`)
        generatingExam.value = false
      }, 1000)
    } else {
      throw new Error('生成试卷失败')
    }

  } catch (error) {
    console.error('生成考试失败:', error)
    ElMessage.error(error.response?.data?.error || '生成试卷失败，请稍后重试')
    generatingExam.value = false
  }
}

// 登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确认要退出登录吗？',
      '退出确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await authStore.logoutAction()
    router.push('/login')
    ElMessage.success('已成功登出')
  } catch (error) {
    // 用户取消了操作
  }
}

// 查看考试结果
const handleViewExamResult = (examId) => {
  if (examId) {
    router.push(`/result/${examId}`)
  }
}

// 处理分页变化
const handlePageChange = async (page) => {
  loading.value = true
  try {
    const examData = await fetchExamData(page, pageSize.value)
    recentExams.value = Array.isArray(examData?.results) ? examData.results : []
    examPagination.value.current = page
  } catch (error) {
    console.error('获取分页数据失败:', error)
    ElMessage.error('获取分页数据失败')
  } finally {
    loading.value = false
  }
}

// 进入管理员控制台
const goToAdminDashboard = async () => {
  router.push('/admin')
}

// 能力详情相关方法
const getStrongestAbility = () => {
  if (!radarData.value || radarData.value.length === 0) return null
  const strongest = radarData.value.reduce((prev, current) =>
    (prev.score || 0) > (current.score || 0) ? prev : current
  )
  return `${strongest.tag} (${Math.round(strongest.score || 0)}分)`
}

const getWeakestAbility = () => {
  if (!radarData.value || radarData.value.length === 0) return null
  const weakest = radarData.value.reduce((prev, current) =>
    (prev.score || 0) < (current.score || 0) ? prev : current
  )
  return `${weakest.tag} (${Math.round(weakest.score || 0)}分)`
}

const getAverageAbility = () => {
  if (!radarData.value || radarData.value.length === 0) return 0
  const total = radarData.value.reduce((sum, item) => sum + (item.score || 0), 0)
  return Math.round(total / radarData.value.length)
}

// 工具函数
const getStatusType = (status) => {
  const statusMap = {
    'not_started': 'info',
    'in_progress': 'warning',
    'completed': 'success'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'not_started': '未开始',
    'in_progress': '进行中',
    'completed': '已完成'
  }
  return statusMap[status] || '未知'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''

  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生命周期
onMounted(async () => {
  // 确保用户信息是最新的
  await authStore.checkAuth()
  fetchDashboardData()
})

// 组件销毁时清理
onUnmounted(() => {
  if (radarChart.value) {
    radarChart.value.dispose()
  }
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.dashboard-container {
  padding: 40px;
  max-width: 1800px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.user-info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 30px;
  border-radius: 12px;
  margin-bottom: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.user-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-details h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.user-position {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
  margin-bottom: 40px;
}

.stat-card {
  background: #fff;
  padding: 35px 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 24px;
  transition: all 0.3s ease;
  min-height: 120px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.user-selector {
  margin-bottom: 24px;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 40px;
  width: 100%;
}

@media (max-width: 1024px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

.radar-section {
  grid-row: span 1;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.radar-details-card {
  height: fit-content;
}

.ability-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.detail-value {
  font-size: 16px;
  font-weight: bold;
  padding: 4px 12px;
  border-radius: 6px;
}

.detail-value.strong {
  color: #67c23a;
  background: #f0f9ff;
}

.detail-value.weak {
  color: #e6a23c;
  background: #fdf6ec;
}

.detail-value.average {
  color: #409eff;
  background: #ecf5ff;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.radar-container {
  width: 100%;
  height: 500px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff;
  border-radius: 4px;
  padding: 0px;
}

.radar-container > div {
  width: 100% !important;
  height: 100% !important;
}

.action-buttons {
  display: flex;
  justify-content: center;
}

.start-exam-btn {
  width: 100%;
  height: 60px;
  font-size: 18px;
  font-weight: bold;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.start-exam-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.admin-card {
  border: 2px solid #f0f0f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.admin-card:hover {
  border-color: #409eff;
  box-shadow: 0 8px 30px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.admin-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.admin-btn {
  width: 100%;
  height: 60px;
  font-size: 18px;
  font-weight: bold;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-sizing: border-box;
  margin: 0;
  padding: 0 20px;
}

.admin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.recommendations {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exam-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exam-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.exam-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.exam-info {
  flex: 1;
}

.exam-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.exam-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exam-date {
  color: #909399;
  font-size: 12px;
}

.exam-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-weight: bold;
}

.score-value {
  font-size: 24px;
  color: #409EFF;
}

.score-total {
  font-size: 14px;
  color: #909399;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  margin-top: 20px;
}

/* 平板端适配 */
@media (max-width: 1024px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 20px;
  }

  .user-info-card {
    padding: 20px;
  }

  .user-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .stats-cards {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .stat-card {
    padding: 20px;
  }

  .stat-value {
    font-size: 28px;
  }

  .start-exam-btn {
    height: 50px;
    font-size: 16px;
  }

  .dashboard-content {
    gap: 20px;
  }

  .radar-container {
    height: 350px;
    padding: 10px;
  }
}
</style>