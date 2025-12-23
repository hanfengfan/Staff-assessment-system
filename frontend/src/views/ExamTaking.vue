<template>
  <div class="exam-container">
    <!-- 考试头部 -->
    <el-card class="exam-header">
      <div class="header-main">
        <div class="exam-title-section">
          <div class="exam-icon">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="exam-info">
            <h1>{{ currentExam?.title }}</h1>
          </div>
        </div>

        <div class="exam-stats">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ examQuestions?.length || 0 }}</div>
              <div class="stat-label">题目总数</div>
            </div>
          </div>

          <div class="stat-divider"></div>

          <div class="stat-item">
            <div class="stat-icon timer-icon">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number timer">{{ formatTime(examTime) }}</div>
              <div class="stat-label">已用时间</div>
            </div>
          </div>
        </div>
      </div>

      <div class="header-footer">
        <div class="progress-section">
          <div class="progress-info">
            <span class="progress-text">答题进度</span>
            <span class="progress-count">{{ answeredCount }}/{{ examQuestions?.length || 0 }}</span>
          </div>
          <div class="progress-bar">
            <el-progress
              :percentage="progressPercentage"
              :stroke-width="6"
              :show-text="false"
            />
          </div>
        </div>

        <div class="exam-actions">
          <el-button size="default" @click="handleExitExam" class="exit-btn">
            <el-icon><Close /></el-icon>
            退出考试
          </el-button>
          <el-button
            type="primary"
            size="default"
            @click="handleSubmitExam"
            :disabled="!allQuestionsAnswered || submitting"
            :title="allQuestionsAnswered ? '提交试卷' : '请回答所有题目后再提交'"
            class="submit-btn"
          >
            <el-icon><Check /></el-icon>
            提交试卷
            <span v-if="!allQuestionsAnswered" class="unanswered-hint">({{ unansweredQuestions.length }} 题未答)</span>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 题目导航 -->
    <el-card class="question-nav">
      <template #header>
        <div class="nav-header">
          <el-icon><List /></el-icon>
          <span>题目导航</span>
          <el-tag type="info" size="small">
            当前进度: {{ currentQuestionIndex + 1 }} / {{ examQuestions?.length || 0 }}
          </el-tag>
        </div>
      </template>
      <div class="nav-grid">
        <div
          v-if="examQuestions && examQuestions.length > 0"
          v-for="(question, index) in examQuestions"
          :key="question?.id || index"
          class="nav-item"
          :class="{
            'current': index === currentQuestionIndex,
            'answered': question?.id && getAnswer(question.id)
          }"
          @click="goToQuestion(index)"
        >
          {{ index + 1 }}
        </div>
        <div v-else class="no-questions">
          没有题目数据
        </div>
      </div>
    </el-card>

    <!-- 题目内容区 -->
    <div class="questions-area">
      <div
        v-for="(question, index) in (examQuestions || [])"
        :key="question?.id || index"
        v-show="index === currentQuestionIndex && question"
        class="question-card"
      >
        <div class="question-header">
          <div class="question-info">
            <span class="question-number">第 {{ index + 1 }} 题</span>
            <el-tag :type="getTypeColor(question.question_type)" class="question-type">
              {{ getTypeText(question.question_type) }}
            </el-tag>
            <el-tag type="warning" class="difficulty-tag">
              难度: {{ question.difficulty }}
            </el-tag>
          </div>
          <div class="question-tags">
            <el-tag
              v-for="tag in question.tags"
              :key="tag.id"
              size="small"
              type="info"
              class="tag-item"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>

        <div class="question-content">
          {{ question.content }}
        </div>

        <!-- 选项区域 -->
        <div class="options-area">
          <!-- 客观题选项 -->
          <ul v-if="question.question_type !== 'subjective' && question.options && question.options.length > 0" class="options-list">
            <li
              v-for="option in question.options"
              :key="option.key"
              class="option-item"
              :class="{ selected: isOptionSelected(question.id, option.key) }"
              @click="handleSelectOption(question.id, option.key)"
            >
              <span class="option-key">{{ option.key }}</span>
              <span class="option-text">{{ option.text }}</span>
            </li>
          </ul>

          <!-- 客观题无选项的提示 -->
          <div v-else-if="question.question_type !== 'subjective'" class="no-options">
            <el-alert
              title="该题目暂无选项"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>

          <!-- 主观题文本输入 -->
          <div v-else class="subjective-answer">
            <el-input
              :model-value="getAnswerForQuestion(question.id)"
              @input="(value) => setAnswerForQuestion(question.id, value)"
              type="textarea"
              :rows="6"
              :placeholder="(question.options && question.options.length > 0 && question.options[0].text) ? question.options[0].text : '请输入你的答案...'"
              maxlength="2000"
              show-word-limit
              class="subjective-textarea"
              @update:model-value="handleSubjectiveInput(question.id)"
            />
            <div class="answer-hint">
              <el-icon><InfoFilled /></el-icon>
              <span>请详细阐述你的观点，答案将自动评分</span>
            </div>
          </div>
        </div>

        <!-- 题目导航按钮 -->
        <div class="question-navigation">
          <el-button
            :disabled="isFirstQuestion"
            @click="prevQuestion"
            size="large"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一题
          </el-button>
          <el-button
            :disabled="isLastQuestion"
            type="primary"
            @click="nextQuestion"
            size="large"
          >
            下一题
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

      </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Clock, List, Check, Close, ArrowLeft, ArrowRight, InfoFilled } from '@element-plus/icons-vue'
import { useExamStore } from '@/stores/exam'
import { generateExam, startExam, submitExam, getExamDetail } from '@/api/exam'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const examStore = useExamStore()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const submitDialogVisible = ref(false)

// 从 store 获取状态 - 使用 storeToRefs 保持响应性
const { currentExam, examQuestions, currentQuestionIndex, userAnswers, examTime, currentQuestion,
        answeredCount, progressPercentage, isLastQuestion, isFirstQuestion, isGenerating } = storeToRefs(examStore)

// 获取方法（不需要 storeToRefs）
const { saveAnswer, getAnswer, goToQuestion, nextQuestion, prevQuestion, formatTime } = examStore

// 计算未答题目
const unansweredQuestions = computed(() => {
  if (!examQuestions.value || !Array.isArray(examQuestions.value)) return []
  return examQuestions.value
    .map((_, index) => index)
    .filter(index => {
      const question = examQuestions.value[index]
      return question && question.id && !getAnswer(question.id)
    })
})

// 检查是否所有题目都已回答
const allQuestionsAnswered = computed(() => {
  return unansweredQuestions.value.length === 0
})

// 获取特定题目的答案
const getAnswerForQuestion = (questionId) => {
  return (userAnswers.value || {})[questionId] || ''
}

// 设置特定题目的答案（用于主观题）
const setAnswerForQuestion = (questionId, value) => {
  saveAnswer(questionId, value)
}

// 初始化考试
const initExam = async () => {
  loading.value = true

  try {
    console.log('开始初始化考试...')
    let examData

    if (route.params.id === 'generate') {
      if (isGenerating.value) {
        return
      }

      isGenerating.value = true
      // 调用生成考试API（题目数量由后端配置控制）
      const response = await generateExam({
        reason: 'daily_practice'
      })
      examData = response

      const startResponse = await startExam(examData.id)
      examStore.setExam({
        id: examData.id,
        title: examData.title,
        status: startResponse.status,
        time_limit: examData.time_limit,
        started_at: startResponse.started_at,
        question_count: examData.question_count
      })
      examStore.setQuestions(startResponse.questions || [])
      isGenerating.value = false
    } else {
      // 获取已有试卷
      const examId = route.params.id
      const detailResponse = await getExamDetail(examId)
      examData = detailResponse

      // 检查是否已经在该试卷中
      if (examStore.currentExam && examStore.currentExam.id === detailResponse.id) {
        isGenerating.value = false // 重置生成状态
        return
      }

      // 如果试卷未开始，需要开始考试
      if (detailResponse.status === 'not_started') {
        const startResponse = await startExam(examId)
        examStore.setExam(startResponse)
        examStore.setQuestions(startResponse.questions || [])
      } else {
        // 试卷已经开始，直接使用详情数据
        examStore.setExam(detailResponse)
        examStore.setQuestions(detailResponse.questions || [])
      }
    }

    // 开始计时
    examStore.startTimer()
    ElMessage.success('考试已开始，请认真答题')
  } catch (error) {
    console.error('初始化考试失败:', error)
    ElMessage.error('初始化考试失败，请稍后重试')
    router.push('/')
  } finally {
    loading.value = false
  }
}

// 选择选项
const handleSelectOption = (questionId, optionKey) => {
  const question = examQuestions.value.find(q => q.id === questionId)
  if (!question) return

  let currentAnswer = getAnswer(questionId)

  if (question.question_type === 'single') {
    // 单选题：直接替换答案
    saveAnswer(questionId, optionKey)
  } else if (question.question_type === 'multiple') {
    // 多选题：处理多选
    if (currentAnswer) {
      const answers = currentAnswer.split(',')
      const keyIndex = answers.indexOf(optionKey)

      if (keyIndex > -1) {
        // 取消选择
        answers.splice(keyIndex, 1)
      } else {
        // 添加选择
        answers.push(optionKey)
      }

      saveAnswer(questionId, answers.sort().join(','))
    } else {
      // 首次选择或没有当前答案的情况
      if (!currentAnswer || !currentAnswer.includes(optionKey)) {
        saveAnswer(questionId, optionKey)
      }
    }
  } else if (question.question_type === 'true_false') {
    // 判断题：直接替换答案
    saveAnswer(questionId, optionKey)
  }
}

// 判断选项是否被选中
const isOptionSelected = (questionId, optionKey) => {
  const answer = getAnswer(questionId)
  if (!answer) return false

  const question = examQuestions.value.find(q => q.id === questionId)
  if (question.question_type === 'multiple') {
    return answer.split(',').includes(optionKey)
  } else {
    return answer === optionKey
  }
}

// 处理主观题输入
const handleSubjectiveInput = (questionId) => {
  // 主观题答案已经在v-model中自动更新，这里可以添加额外的处理逻辑
  // 比如自动保存草稿等
}

// 获取题型颜色
const getTypeColor = (type) => {
  const colorMap = {
    'single': 'primary',
    'multiple': 'warning',
    'true_false': 'success',
    'subjective': 'danger'
  }
  return colorMap[type] || 'info'
}

// 获取题型文本
const getTypeText = (type) => {
  const textMap = {
    'single': '单选题',
    'multiple': '多选题',
    'true_false': '判断题',
    'subjective': '主观题'
  }
  return textMap[type] || '未知类型'
}

// 处理退出考试
const handleExitExam = async () => {
  try {
    await ElMessageBox.confirm(
      '确认要退出考试吗？您的答题进度将被保存。',
      '退出确认',
      {
        confirmButtonText: '确认退出',
        cancelButtonText: '继续答题',
        type: 'warning'
      }
    )

    examStore.stopTimer()
    router.push('/')
  } catch (error) {
    // 用户取消了退出操作
  }
}

// 处理提交考试
const handleSubmitExam = async () => {
  // 防止重复提交
  if (submitting.value) {
    return
  }

  submitting.value = true

  try {
    // 深度安全检查：缓存考试信息
    const examInfo = examStore.currentExam

    if (!examInfo || !examInfo.id) {
      ElMessage.error('考试信息无效')
      return
    }

    // 构建答案数据
    const answers = {}
    examQuestions.value.forEach(question => {
      const answer = examStore.getAnswer(question.id)
      if (answer) {
        // 对于多选题，答案可能是逗号分隔的字符串，需要转换为数组
        if (question.question_type === 'multiple_choice' && answer.includes(',')) {
          answers[question.id] = answer.split(',').map(a => a.trim())
        } else {
          answers[question.id] = answer
        }
      }
    })

    // 调用提交 API
    await submitExam(examInfo.id, { answers })

    ElMessage.success('试卷提交成功！')
    examStore.stopTimer()
    router.push(`/result/${examInfo.id}`)
  } catch (error) {
    console.error('提交试卷失败:', error)
    let errorMessage = '提交试卷失败，请稍后重试'

    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.error) {
        errorMessage = errorData.error
      } else if (errorData.detail) {
        errorMessage = errorData.detail
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

// 确认提交
const confirmSubmit = async () => {
  // 第一时间防止重复提交
  if (submitting.value) {
    return
  }

  submitting.value = true

  try {
    // 深度安全检查：缓存考试信息
    const examInfo = examStore.currentExam
    const examId = examStore.currentExam?.id
    const examStatus = examStore.currentExam?.status

    // 全面的安全验证
    if (!examInfo || !examId || !examStatus) {
      ElMessage.error('考试信息无效，请重新开始考试')
      router.push('/')
      return
    }

    if (examStatus === 'completed') {
      ElMessage.warning('该试卷已经提交过了')
      router.push('/')
      return
    }

    // 构建答案数据
    const answers = {}
    examQuestions.value.forEach(question => {
      const answer = examStore.getAnswer(question.id)
      if (answer) {
        // 对于多选题，答案可能是逗号分隔的字符串，需要转换为数组
        if (question.question_type === 'multiple_choice' && answer.includes(',')) {
          answers[question.id] = answer.split(',').map(a => a.trim())
        } else {
          answers[question.id] = answer
        }
      }
    })

    // 检查答题完整性
    const answeredQuestions = Object.keys(answers)
    const unansweredCount = examQuestions.value.length - answeredQuestions.length

    if (unansweredCount > 0) {
      const confirmUnfinished = await ElMessageBox.confirm(
        `您还有 <strong>${unansweredCount}</strong> 道题目未回答，<br/>确定要提交吗？`,
        '确认提交',
        {
          confirmButtonText: '确定提交',
          cancelButtonText: '继续答题',
          type: 'warning',
          dangerouslyUseHTML: true,
          centerDialog: true,
          customClass: 'submit-confirm-dialog'
        }
      )

      if (!confirmUnfinished) {
        return
      }
    }

    // 提交前最后验证
    if (!examStore.currentExam?.id) {
      ElMessage.error('考试信息已失效，请重新开始')
      router.push('/')
      return
    }

    // 保存当前考试ID，防止被resetExam清除
    const currentExamId = examStore.currentExam?.id

    if (!currentExamId) {
      ElMessage.error('考试信息已失效，请重新开始')
      router.push('/')
      return
    }

    // 执行提交
    const result = await submitExam(currentExamId, { answers })

    // 立即跳转，避免状态问题
    ElMessage.success('试卷提交成功！正在跳转...')

    // 同步进行跳转，避免状态冲突
    setTimeout(() => {
      examStore.stopTimer()
      examStore.resetExam()
      router.push(`/result/${currentExamId}`)
    }, 100)

  } catch (error) {
    console.error('提交试卷失败:', error)

    // 精确的错误处理
    let errorMessage = '提交试卷失败，请稍后重试'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
    submitDialogVisible.value = false
  }
}

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    examStore.resetExam()
    initExam()
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  // initExam()
})

onUnmounted(() => {
  examStore.stopTimer()
})
</script>

<style scoped>
.exam-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 30px;
  min-height: 100vh;
  background: #f8f9fb;
}

.unanswered-hint {
  font-size: 12px;
  color: #f56c6c;
  margin-left: 4px;
}

.exam-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  margin-bottom: 0;
  padding: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  border: none;
}

.header-main {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 32px 40px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.exam-title-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.exam-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.exam-info h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.exam-stats {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-left: 60px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.timer-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 2px;
}

.stat-number.timer {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  letter-spacing: 1px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

.header-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 40px;
  background: rgba(255, 255, 255, 0.05);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.progress-section {
  flex: 1;
  margin-right: 40px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.9;
}

.progress-count {
  font-size: 14px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
}

.exam-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 160px;
  align-items: stretch;
  justify-content: center;
}

.exam-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 160px;
  align-items: stretch;
  justify-content: center;
}

.exam-actions :deep(.el-button) {
  width: 100% !important;
  height: 44px !important;
  font-size: 14px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 16px !important;
  text-align: center !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.exam-actions :deep(.el-button:not(.is-primary)) {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #303133 !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

.exam-actions :deep(.el-button:not(.is-primary):hover) {
  background: #ffffff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
}

.exam-actions :deep(.el-button.is-primary) {
  background: #ffffff !important;
  color: #667eea !important;
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
}

.exam-actions :deep(.el-button.is-primary:hover:not(:disabled)) {
  background: #f8f9fa !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3) !important;
}

.exam-actions :deep(.el-button:disabled) {
  background: rgba(255, 255, 255, 0.3) !important;
  color: rgba(255, 255, 255, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  transform: none !important;
  box-shadow: none !important;
}

.exam-actions :deep(.el-button .el-button__content) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  gap: 6px !important;
}

.exam-actions :deep(.el-button .el-icon) {
  margin: 0 !important;
  flex-shrink: 0 !important;
  font-size: 16px !important;
}

.exam-actions :deep(.el-button span:not(.el-icon)) {
  margin: 0 !important;
  padding: 0 !important;
}

/* 进度条样式覆盖 */
.progress-section :deep(.el-progress-bar__outer) {
  background-color: rgba(255, 255, 255, 0.2) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

.progress-section :deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #ffffff 0%, rgba(255, 255, 255, 0.9) 100%) !important;
  border-radius: 10px !important;
  transition: width 0.6s ease !important;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3) !important;
}

.question-nav {
  margin-bottom: 0;
  padding: 30px 40px;
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #303133;
  font-size: 16px;
  padding: 16px 0;
}

.nav-grid {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  gap: 15px;
  padding: 20px 0;
  justify-content: flex-start;
  align-items: flex-start;
  align-content: flex-start;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

.nav-item {
  width: 50px;
  height: 50px;
  display: flex !important;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  margin: 0;
}

.nav-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.nav-item.current {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.nav-item.answered:not(.current) {
  background: #f0f9ff;
  border-color: #67c23a;
  color: #67c23a;
}

.no-questions {
  width: 100%;
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 16px;
}

.questions-area {
  flex: 1;
}

.question-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  margin: 0 40px;
}

.question-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.question-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.question-number {
  background: #409eff;
  color: #fff;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: bold;
}

.question-type,
.difficulty-tag,
.tag-item {
  margin-left: 8px;
}

.question-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.question-content {
  font-size: 20px;
  line-height: 1.8;
  color: #303133;
  margin-bottom: 28px;
  padding: 24px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border-left: 5px solid #409eff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.options-area {
  margin-bottom: 35px;
}

.options-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  margin: 16px 0;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.option-item:hover {
  border-color: #409eff;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f4ff 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.2);
}

.option-item.selected {
  border-color: #409eff;
  background: linear-gradient(135deg, #409eff 0%, #3291ff 100%);
  color: #fff;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.option-item.selected:hover {
  background: linear-gradient(135deg, #3291ff 0%, #2680eb 100%);
  transform: translateY(-2px);
}

.option-key {
  background: linear-gradient(135deg, #f1f3f4 0%, #e8eaed 100%);
  color: #5f6368;
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: bold;
  margin-right: 20px;
  min-width: 36px;
  text-align: center;
  font-size: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.option-item.selected .option-key {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.option-text {
  flex: 1;
  font-size: 18px;
  line-height: 1.6;
  color: #303133;
}

.question-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.submit-confirm {
  line-height: 1.6;
}

.submit-stats p {
  margin: 10px 0;
  line-height: 1.8;
}

.unanswered-warning {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.dialog-footer {
  text-align: right;
  margin-top: 20px;
}

/* 平板端适配 */
@media (max-width: 1024px) {
  .exam-container {
    padding: 30px;
  }

  .question-card {
    margin: 0 20px;
    padding: 30px;
  }

  .nav-item {
    width: 45px;
    height: 45px;
    font-size: 13px;
  }

  .nav-grid {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 12px;
  }

  .exam-actions {
    min-width: 120px;
  }

  .exit-btn,
  .submit-btn {
    width: 120px;
    height: 48px;
  }

  .question-nav {
    padding: 20px;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .exam-container {
    padding: 20px;
  }

  .exam-header {
    padding: 20px;
  }

  .header-content {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }

  .exam-info h2 {
    font-size: 20px;
    text-align: center;
  }

  .exam-meta {
    justify-content: center;
  }

  .exam-actions {
    flex-direction: column;
    align-items: center;
    min-width: auto;
  }

  .exit-btn,
  .submit-btn {
    width: 200px;
    height: 45px;
  }

  .question-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .question-content {
    font-size: 16px;
    padding: 15px;
  }

  .option-item {
    padding: 12px 15px;
  }

  .option-text {
    font-size: 15px;
  }

  .nav-grid {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 10px;
    justify-content: center;
  }

  .nav-item {
    width: 40px;
    height: 40px;
    font-size: 12px;
  }

  .question-navigation {
    flex-direction: column;
    gap: 15px;
  }

  .question-card {
    margin: 0;
    padding: 20px;
  }

  .question-nav {
    padding: 15px;
  }

  .exam-header {
    padding: 20px;
  }
}

.subjective-answer {
  width: 100%;

  .subjective-textarea {
    margin-bottom: 10px;

    :deep(.el-textarea__inner) {
      font-size: 16px;
      line-height: 1.6;
      resize: vertical;
    }
  }

  .answer-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #909399;

    .el-icon {
      font-size: 16px;
    }
  }
}

.no-options {
  padding: 20px;
  text-align: center;
}
</style>