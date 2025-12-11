<template>
  <div class="result-container">
    <div v-if="loading" class="loading-container">
      <el-card class="result-card">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 20px;" />
            <el-skeleton-item variant="text" style="width: 40%; margin-bottom: 40px;" />
            <el-skeleton-item variant="rect" style="width: 100%; height: 400px; margin-bottom: 20px;" />
            <el-skeleton-item variant="button" style="width: 120px; height: 40px;" />
          </template>
        </el-skeleton>
      </el-card>
    </div>

    <div v-else-if="examResult" class="result-content">
      <!-- 考试结果概览 -->
      <el-card class="result-overview">
        <div class="overview-header">
          <div class="score-display">
            <div class="score-circle">
              <div class="score-value">{{ scorePercentage }}%</div>
              <div class="score-label">得分率</div>
            </div>
            <div class="score-details">
              <div class="score-item">
                <span class="label">得分</span>
                <span class="value obtained">{{ examResult.score_obtained?.toFixed(1) || 0 }}</span>
              </div>
              <div class="score-divider">/</div>
              <div class="score-item">
                <span class="label">总分</span>
                <span class="value total">{{ examResult.total_score || 100 }}</span>
              </div>
            </div>
          </div>

          <div class="exam-info">
            <h3>{{ examData?.title }}</h3>
            <div class="info-grid">
              <div class="info-item">
                <el-icon><Clock /></el-icon>
                <span>答题时间: {{ formatDuration(examData?.duration || 0) }}</span>
              </div>
              <div class="info-item">
                <el-icon><Document /></el-icon>
                <span>题目数量: {{ examData?.question_count || 0 }} 题</span>
              </div>
              <div class="info-item">
                <el-icon><TrendCharts /></el-icon>
                <span>准确率: {{ scorePercentage }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 能力表现分析 -->
      <el-card class="result-analysis">
        <template #header>
          <div class="card-header">
            <el-icon><TrendCharts /></el-icon>
            <span>能力表现分析</span>
          </div>
        </template>
        <div class="tag-performance">
          <div
            v-for="tag in tagPerformance"
            :key="tag.tag_name"
            class="performance-item"
          >
            <div class="tag-header">
              <el-tag :type="getPerformanceType(tag.accuracy)" size="large">
                {{ tag.tag_name }}
              </el-tag>
              <span class="accuracy">准确率: {{ tag.accuracy?.toFixed(1) }}%</span>
            </div>
            <div class="tag-stats">
              <div class="stats-row">
                <span class="label">正确数:</span>
                <span class="value correct">{{ tag.correct_count }}</span>
              </div>
              <div class="stats-row">
                <span class="label">总题数:</span>
                <span class="value total">{{ tag.total_count }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 错题解析 -->
      <el-card class="wrong-answers">
        <template #header>
          <div class="card-header">
            <el-icon><Close /></el-icon>
            <span>错题解析</span>
            <el-badge :value="wrongAnswers.length" type="danger" v-if="wrongAnswers.length > 0" />
          </div>
        </template>
        <div v-if="wrongAnswers.length === 0" class="no-wrong-answers">
          <el-result
            icon="success"
            title="恭喜！全部答对"
            sub-title="您在本次考试中表现优秀，继续保持！"
          />
        </div>
        <div v-else class="wrong-list">
          <div
            v-for="(item, index) in wrongAnswers"
            :key="item.question_id"
            class="wrong-item"
          >
            <div class="wrong-header">
              <span class="question-number">第 {{ item.question_index + 1 }} 题</span>
              <el-tag type="danger" size="small">答错</el-tag>
            </div>
            <div class="question-content">
              {{ item.question_content }}
            </div>
            <div class="answer-comparison">
              <div class="your-answer">
                <span class="answer-label">您的答案:</span>
                <el-tag type="danger">{{ formatAnswer(item.your_answer, item.question_type) }}</el-tag>
              </div>
              <div class="correct-answer">
                <span class="answer-label">正确答案:</span>
                <el-tag type="success">{{ formatAnswer(item.correct_answer, item.question_type) }}</el-tag>
              </div>
            </div>
            <div v-if="item.explanation" class="answer-explanation">
              <el-alert
                type="info"
                :closable="false"
                show-icon
              >
                <template #title>解析</template>
                <div>{{ item.explanation }}</div>
              </el-alert>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="handleGoToDashboard">
          <el-icon><HomeFilled /></el-icon>
          {{ isAdmin ? '返回管理员控制台' : '返回工作台' }}
        </el-button>
        <el-button size="large" @click="handleViewAnalysis">
          <el-icon><TrendCharts /></el-icon>
          查看能力分析
        </el-button>
      </div>
    </div>

    <div v-else class="error-state">
      <el-result
        icon="warning"
        title="无法获取考试结果"
        sub-title="请稍后重试或联系管理员"
      >
        <template #extra>
          <el-button type="primary" @click="handleGoToDashboard">
            {{ isAdmin ? '返回管理员控制台' : '返回工作台' }}
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, toRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, Document, TrendCharts, Close, HomeFilled } from '@element-plus/icons-vue'
import { getExamDetail } from '@/api/exam'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 判断是否为管理员
const isAdmin = computed(() => {
  const rawUser = toRaw(authStore.user)
  return Boolean(rawUser?.is_staff)
})

// 响应式数据
const loading = ref(true)
const examData = ref(null)
const examResult = ref(null)

// 计算得分率
const scorePercentage = computed(() => {
  if (!examResult.value) return 0
  const { score_obtained, total_score } = examResult.value
  if (!total_score || total_score === 0) return 0
  return Math.round((score_obtained / total_score) * 100)
})

// 计算标签表现数据
const tagPerformance = computed(() => {
  if (!examResult.value?.exam_records) return []

  const tagMap = new Map()

  examResult.value.exam_records.forEach(record => {
    if (!record.question.tags) return

    record.question.tags.forEach(tag => {
      if (!tagMap.has(tag.name)) {
        tagMap.set(tag.name, {
          tag_name: tag.name,
          correct_count: 0,
          total_count: 0,
          accuracy: 0
        })
      }

      const tagData = tagMap.get(tag.name)
      tagData.total_count++
      if (record.is_correct) {
        tagData.correct_count++
      }
    })
  })

  // 计算准确率并转换为数组
  return Array.from(tagMap.values()).map(tag => ({
    ...tag,
    accuracy: tag.total_count > 0 ? Math.round(((tag.correct_count / tag.total_count) * 1000) / 10) : 0
  }))
})

// 计算错题列表
const wrongAnswers = computed(() => {
  if (!examResult.value?.exam_records) return []

  const wrong = []
  let questionIndex = 0

  examResult.value.exam_records.forEach(record => {
    if (record.is_correct) {
      questionIndex++
    } else {
      wrong.push({
        question_id: record.question.id,
        question_index: questionIndex,
        question_content: record.question.content,
        your_answer: record.user_answer,
        correct_answer: record.question.correct_answer,
        question_type: record.question.question_type,
        explanation: record.question.explanation || '需要加强相关知识学习。',
        accuracy: 0
      })
      questionIndex++
    }
  })

  return wrong
})

// 获取考试结果
const fetchExamResult = async () => {
  loading.value = true

  try {
    const examId = route.params.id

    // 安全检查：确保examId有效
    if (!examId || examId === 'undefined' || examId === null || examId === 'null') {
      console.error('无效的考试ID:', examId)
      console.error('当前路由参数:', route.params)
      console.error('当前完整路径:', route.fullPath)
      router.push('/')
      return
    }

  
    // 权限通过，继续获取详情
    const response = await getExamDetail(examId)

    if (response.status === 'completed') {
      // 使用返回的结果数据
      examData.value = response
      examResult.value = response
    } else {
      // 考试未完成，跳转到答题页面
      router.replace(`/exam/${examId}`)
      return
    }
  } catch (error) {
    console.error('获取考试结果失败:', error)
    ElMessage.error('获取考试结果失败')
  } finally {
    loading.value = false
  }
}

// 获取表现类型
const getPerformanceType = (accuracy) => {
  if (accuracy >= 80) return 'success'
  if (accuracy >= 60) return 'warning'
  return 'danger'
}

// 格式化答案显示
const formatAnswer = (answer, questionType) => {
  if (!answer) return '未作答'
  if (questionType === 'multiple') {
    return answer.split(',').join(', ')
  }
  return answer
}

// 格式化考试时长
const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 返回工作台/管理员控制台
const handleGoToDashboard = () => {
  if (isAdmin.value) {
    router.push('/admin')
  } else {
    router.push('/')
  }
}

// 查看能力分析
const handleViewAnalysis = () => {
  // 这里可以跳转到详细的能力分析页面
  router.push('/')
  ElMessage.info('正在开发详细能力分析功能...')
}

// 生命周期
onMounted(() => {
  fetchExamResult()
})
</script>

<style scoped>
.result-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 30px;
  min-height: 100vh;
  background: #f8f9fb;
}

.loading-container {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-card {
  width: 100%;
  max-width: 900px;
}

.result-overview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  transition: all 0.3s ease;
  padding: 40px;
}

.result-overview:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.2);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 30px;
}

.score-display {
  text-align: center;
}

.score-circle {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid rgba(255, 255, 255, 0.3);
}

.score-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.score-label {
  font-size: 14px;
  opacity: 0.9;
}

.score-details {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 20px;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-item .label {
  font-size: 14px;
  opacity: 0.8;
  margin-bottom: 5px;
}

.score-item .value {
  font-size: 28px;
  font-weight: bold;
}

.score-item .value.obtained {
  color: #ffeb3b;
}

.score-item .value.total {
  color: rgba(255, 255, 255, 0.8);
}

.score-divider {
  font-size: 24px;
  opacity: 0.6;
}

.exam-info {
  flex: 1;
  min-width: 300px;
}

.exam-info h3 {
  margin: 0 0 20px 0;
  font-size: 24px;
  color: #fff;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.result-analysis {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.tag-performance {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 25px;
}

.performance-item {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.performance-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.tag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.accuracy {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.tag-stats {
  display: flex;
  justify-content: space-between;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stats-row .label {
  font-size: 14px;
  color: #909399;
}

.stats-row .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stats-row .value.correct {
  color: #67c23a;
}

.stats-row .value.total {
  color: #409eff;
}

.wrong-answers {
  margin-bottom: 20px;
}

.no-wrong-answers {
  text-align: center;
  padding: 40px 0;
}

.wrong-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wrong-item {
  background: #fef0f0;
  border: 1px solid #fcd3d3;
  border-radius: 8px;
  padding: 20px;
}

.wrong-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.question-number {
  font-weight: 600;
  color: #303133;
}

.question-content {
  font-size: 16px;
  line-height: 1.6;
  color: #303133;
  margin-bottom: 15px;
  padding: 15px;
  background: #fff;
  border-radius: 6px;
  border-left: 4px solid #f56c6c;
}

.answer-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.your-answer,
.correct-answer {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.answer-label {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.answer-explanation {
  margin-top: 15px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 20px;
}

.error-state {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 平板端适配 */
@media (max-width: 1024px) {
  .result-container {
    padding: 30px;
  }

  .tag-performance {
    grid-template-columns: repeat(2, 1fr);
  }

  .overview-header {
    gap: 30px;
  }

  .score-circle {
    width: 160px;
    height: 160px;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .result-container {
    padding: 20px;
  }

  .overview-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .score-circle {
    width: 120px;
    height: 120px;
  }

  .score-value {
    font-size: 28px;
  }

  .score-item .value {
    font-size: 24px;
  }

  .exam-info h3 {
    font-size: 20px;
  }

  .tag-performance {
    grid-template-columns: 1fr;
  }

  .answer-comparison {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 15px;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .result-overview {
    padding: 30px 20px;
  }

  .wrong-item {
    padding: 15px;
  }

  .performance-item {
    padding: 20px;
  }
}
</style>