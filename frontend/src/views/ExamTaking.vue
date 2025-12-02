<template>
  <div class="exam-container">
    <!-- 考试头部 -->
    <el-card class="exam-header">
      <div class="header-content">
        <div class="exam-info">
          <h2>{{ currentExam?.title }}</h2>
          <div class="exam-meta">
            <el-tag type="primary" size="large">
              <el-icon><Document /></el-icon>
              共 {{ questions?.length || 0 }} 题
            </el-tag>
            <el-tag type="success" size="large">
              <el-icon><Clock /></el-icon>
              <span class="timer">{{ formatTime(examTime) }}</span>
            </el-tag>
          </div>
        </div>
        <div class="exam-actions">
          <el-button type="primary" size="large" @click="handleSubmitExam">
            <el-icon><Check /></el-icon>
            提交试卷
          </el-button>
          <el-button size="large" @click="handleExitExam">
            <el-icon><Close /></el-icon>
            退出考试
          </el-button>
        </div>
      </div>
      <div class="progress-bar">
        <el-progress
          :percentage="progressPercentage"
          :stroke-width="8"
          :show-text="true"
          :format="(percentage) => `答题进度: ${answeredCount}/${questions?.length || 0}`"
        />
      </div>
    </el-card>

    <!-- 题目导航 -->
    <el-card class="question-nav">
      <template #header>
        <div class="nav-header">
          <el-icon><List /></el-icon>
          <span>题目导航</span>
          <el-tag type="info" size="small">
            当前进度: {{ currentQuestionIndex + 1 }} / {{ questions?.length || 0 }}
          </el-tag>
        </div>
      </template>
      <div class="nav-grid">
        <div
          v-for="(question, index) in (questions || [])"
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
      </div>
    </el-card>

    <!-- 题目内容区 -->
    <div class="questions-area">
      <div
        v-for="(question, index) in (questions || [])"
        :key="question?.id || index"
        v-show="index === currentQuestionIndex"
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
          <ul class="options-list">
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

    <!-- 提交确认对话框 -->
    <el-dialog
      v-model="submitDialogVisible"
      title="提交确认"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="submit-confirm">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        >
          确认要提交试卷吗？提交后将无法修改答案。
        </el-alert>

        <div class="submit-stats">
          <p><strong>答题进度:</strong> {{ answeredCount }} / {{ questions?.length || 0 }} ({{ Math.round(progressPercentage) }}%)</p>
          <p v-if="unansweredQuestions.length > 0" class="unanswered-warning">
            <strong>未答题目:</strong>
            <el-tag
              v-for="index in unansweredQuestions"
              :key="index"
              size="small"
              type="danger"
              style="margin-left: 4px;"
            >
              {{ index + 1 }}
            </el-tag>
          </p>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="submitDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="confirmSubmit"
            :loading="submitting"
            :disabled="submitting"
          >
            确认提交
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Clock, List, Check, Close, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
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
const { currentExam, questions, currentQuestionIndex, userAnswers, examTime, currentQuestion,
        answeredCount, progressPercentage, isLastQuestion, isFirstQuestion, isGenerating } = storeToRefs(examStore)

// 获取方法（不需要 storeToRefs）
const { saveAnswer, getAnswer, goToQuestion, nextQuestion, prevQuestion, formatTime } = examStore

// 计算未答题目
const unansweredQuestions = computed(() => {
  if (!questions.value || !Array.isArray(questions.value)) return []
  return questions.value
    .map((_, index) => index)
    .filter(index => {
      const question = questions.value[index]
      return question && question.id && !getAnswer(question.id)
    })
})

// 初始化考试
const initExam = async () => {
  loading.value = true

  try {
    let examData

    if (route.params.id === 'generate') {
      // 生成新试卷 - 添加防重复检查
      if (isGenerating.value || examStore.currentExam) {
        console.log('考试正在生成中，跳过重复生成')
        return
      }

      isGenerating.value = true // 设置生成标志
      const response = await generateExam({
        reason: 'daily_practice',
        question_count: 15
      })
      examData = response

      // 开始考试
      await startExam(examData.paper_id)

      // 获取题目详情
      const detailResponse = await getExamDetail(examData.paper_id)
      console.log('生成的试卷数据:', detailResponse)
      console.log('题目数量:', detailResponse.questions?.length || 0)
      examStore.setExam(detailResponse)
      examStore.setQuestions(detailResponse.questions || [])

      isGenerating.value = false // 清除生成标志
    } else {
      // 获取已有试卷
      const examId = route.params.id
      const detailResponse = await getExamDetail(examId)
      examData = detailResponse

      // 检查是否已经在该试卷中
      if (examStore.currentExam && examStore.currentExam.id === detailResponse.id) {
        console.log('试卷已经加载，跳过重复初始化')
        isGenerating.value = false // 重置生成状态
        return
      }

      // 如果试卷未开始，需要开始考试
      if (detailResponse.status === 'not_started') {
        await startExam(examId)
      }

      examStore.setExam(detailResponse)
      examStore.setQuestions(detailResponse.questions || [])
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
    isGenerating.value = false // 确保重置生成状态
  }
}

// 选择选项
const handleSelectOption = (questionId, optionKey) => {
  const question = questions.value.find(q => q.id === questionId)
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
      // 首次选择
      saveAnswer(questionId, optionKey)
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

  const question = questions.value.find(q => q.id === questionId)
  if (question.question_type === 'multiple') {
    return answer.split(',').includes(optionKey)
  } else {
    return answer === optionKey
  }
}

// 获取题型颜色
const getTypeColor = (type) => {
  const colorMap = {
    'single': 'primary',
    'multiple': 'warning',
    'true_false': 'success'
  }
  return colorMap[type] || 'info'
}

// 获取题型文本
const getTypeText = (type) => {
  const textMap = {
    'single': '单选题',
    'multiple': '多选题',
    'true_false': '判断题'
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
const handleSubmitExam = () => {
  // 防止重复提交
  if (submitting.value) {
    console.log('试卷正在提交中，跳过重复操作')
    return
  }
  submitDialogVisible.value = true
}

// 确认提交
const confirmSubmit = async () => {
  // 第一时间防止重复提交
  if (submitting.value) {
    console.log('试卷正在提交中，跳过重复操作')
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
    questions.value.forEach(question => {
      const answer = examStore.getAnswer(question.id)
      if (answer) {
        answers[question.id] = answer
      }
    })

    // 检查答题完整性
    const answeredQuestions = Object.keys(answers)
    const unansweredCount = questions.value.length - answeredQuestions.length

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
    console.log('开始提交考试，ID:', currentExamId)
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

    // 无论成功失败，都要确保界面状态正确
    console.log('提交操作完成，submitting:', submitting.value)
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
  // 防止重复初始化
  if (isGenerating.value) {
    console.log('考试正在生成中，跳过初始化')
    return
  }
  initExam()
})

onUnmounted(() => {
  examStore.stopTimer()
})
</script>

<style scoped>
.exam-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  background: #f8f9fb;
}

.exam-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.exam-info h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: bold;
}

.exam-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.timer {
  font-family: 'Courier New', monospace;
  font-weight: bold;
}

.exam-actions {
  display: flex;
  gap: 12px;
}

.question-nav {
  margin-bottom: 24px;
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
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: 12px;
  padding: 20px 0;
}

.nav-item {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.nav-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.nav-item.current {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
  transform: scale(1.1);
}

.nav-item.answered:not(.current) {
  background: #f0f9ff;
  border-color: #67c23a;
  color: #67c23a;
}

.questions-area {
  flex: 1;
}

.question-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
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

/* 移动端适配 */
@media (max-width: 768px) {
  .exam-container {
    padding: 10px;
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
    justify-content: center;
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
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
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

  .question-navigation {
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>