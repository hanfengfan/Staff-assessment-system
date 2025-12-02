import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useExamStore = defineStore('exam', () => {
  // 状态
  const currentExam = ref(null)
  const examQuestions = ref([])
  const currentQuestionIndex = ref(0)
  const userAnswers = ref({})
  const examTime = ref(0)
  const examTimer = ref(null)
  const isGenerating = ref(false) // 添加：防重复生成标志

  // 开始考试计时
  function startTimer() {
    examTimer.value = setInterval(() => {
      examTime.value++
    }, 1000)
  }

  // 停止考试计时
  function stopTimer() {
    if (examTimer.value) {
      clearInterval(examTimer.value)
      examTimer.value = null
    }
  }

  // 重置考试状态
  function resetExam() {
    currentExam.value = null
    examQuestions.value = []
    currentQuestionIndex.value = 0
    userAnswers.value = {}
    examTime.value = 0
    isGenerating.value = false // 重置防重复生成标志
    stopTimer()
  }

  // 设置当前考试
  function setExam(exam) {
    currentExam.value = exam
  }

  // 设置考试题目
  function setQuestions(questions) {
    examQuestions.value = questions
  }

  // 跳转到指定题目
  function goToQuestion(index) {
    if (index >= 0 && index < examQuestions.value.length) {
      currentQuestionIndex.value = index
    }
  }

  // 下一题
  function nextQuestion() {
    if (currentQuestionIndex.value < examQuestions.value.length - 1) {
      currentQuestionIndex.value++
    }
  }

  // 上一题
  function prevQuestion() {
    if (currentQuestionIndex.value > 0) {
      currentQuestionIndex.value--
    }
  }

  // 保存答案
  function saveAnswer(questionId, answer) {
    userAnswers.value[questionId] = answer
  }

  // 获取答案
  function getAnswer(questionId) {
    return userAnswers.value[questionId] || ''
  }

  // 格式化时间显示
  function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 计算答题进度
  const answeredCount = computed(() => {
    return Object.keys(userAnswers.value).length
  })

  const progressPercentage = computed(() => {
    if (examQuestions.value.length === 0) return 0
    return Math.round((answeredCount.value / examQuestions.value.length) * 100)
  })

  // 当前题目
  const currentQuestion = computed(() => {
    return examQuestions.value[currentQuestionIndex.value] || null
  })

  // 是否最后一题
  const isLastQuestion = computed(() => {
    return currentQuestionIndex.value === examQuestions.value.length - 1
  })

  // 是否第一题
  const isFirstQuestion = computed(() => {
    return currentQuestionIndex.value === 0
  })

  return {
    // 状态
    currentExam,
    examQuestions,
    questions: examQuestions, // 添加 questions 别名以保持兼容性
    currentQuestionIndex,
    userAnswers,
    examTime,
    currentQuestion,
    answeredCount,
    progressPercentage,
    isLastQuestion,
    isFirstQuestion,
    isGenerating, // 添加：防重复生成标志

    // 方法
    startTimer,
    stopTimer,
    resetExam,
    setExam,
    setQuestions,
    goToQuestion,
    nextQuestion,
    prevQuestion,
    saveAnswer,
    getAnswer,
    formatTime
  }
})