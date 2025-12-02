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

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <el-icon size="32" color="#409EFF">
          <TrendCharts />
        </el-icon>
        <div class="stat-content">
          <div class="stat-value">{{ capabilitySummary?.overall_score || 0 }}</div>
          <div class="stat-label">综合能力评分</div>
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
      <!-- 左侧：能力雷达图 -->
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
      </div>

      <!-- 右侧：操作区域 -->
      <div class="action-section">
        <!-- 开始考试按钮 -->
        <el-card class="custom-card">
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

        <!-- 最近考试记录 -->
        <el-card class="custom-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近考试记录</span>
            </div>
          </template>
          <div v-if="recentExams.length === 0" class="empty-state">
            <el-empty description="暂无考试记录" />
          </div>
          <div v-else class="exam-list">
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
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
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
  Warning
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getExamList } from '@/api/exam'
import { getRadarData, getCapabilitySummary, getRecommendations } from '@/api/analysis'
import * as echarts from 'echarts'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const generatingExam = ref(false)
const radarChartRef = ref()
const radarChart = ref(null)

const user = computed(() => authStore.user)
const recentExams = ref([])
const radarData = ref([])
const capabilitySummary = ref(null)
const recommendations = ref([])

// 获取数据
const fetchDashboardData = async () => {
  loading.value = true

  try {
    const [examsResponse, radarResponse, summaryResponse, recommendationsResponse] = await Promise.all([
      getExamList({ page_size: 5 }),
      getRadarData(),
      getCapabilitySummary(),
      getRecommendations()
    ])

    // 确保数据结构正确，防止 undefined 错误
    recentExams.value = Array.isArray(examsResponse?.results) ? examsResponse.results : []
    radarData.value = Array.isArray(radarResponse) ? radarResponse : []
    capabilitySummary.value = summaryResponse || {}
    recommendations.value = Array.isArray(recommendationsResponse?.recommendations) ? recommendationsResponse.recommendations : []

    // 渲染雷达图
    nextTick(() => {
      renderRadarChart()
    })
  } catch (error) {
    console.error('获取工作台数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')

    // 发生错误时设置默认值，防止页面崩溃
    recentExams.value = []
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
      radius: '65%'
    },
    series: [{
      name: '能力水平',
      type: 'radar',
      data: [{
        value: validRadarData.map(item => item?.score || 0),
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

    // 这里应该调用生成考试API，现在先跳转
    ElMessage.success('正在生成智能试卷...')

    // 模拟延迟
    setTimeout(() => {
      router.push('/exam/generate')
      generatingExam.value = false
    }, 1500)

  } catch (error) {
    // 用户取消了操作
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
onMounted(() => {
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
  padding: 24px;
  max-width: 1600px;
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 24px;
  transition: all 0.3s ease;
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

.dashboard-content {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 28px;
}

@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }
}

.radar-section {
  grid-row: span 1;
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
  height: 450px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
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

/* 移动端适配 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 15px;
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
}
</style>