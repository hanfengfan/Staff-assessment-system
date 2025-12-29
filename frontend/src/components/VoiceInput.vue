<template>
  <div class="voice-input-wrapper">
    <el-button
      :type="isRecording ? 'danger' : 'primary'"
      :icon="Microphone"
      @click="toggleRecording"
      :disabled="disabled || isRecording"
      :loading="isRecording"
    >
      {{ isRecording ? `录音中... ${recordingTime}s` : '语音输入' }}
    </el-button>
    <el-button
      v-if="isRecording"
      type="danger"
      @click="stopRecording"
      :icon="Close"
    >
      停止
    </el-button>
    <div v-if="interimText" class="interim-text">
      {{ interimText }}
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { Microphone, Close } from '@element-plus/icons-vue'
import { createSpeechService } from '@/utils/XfyunService'
import { ElMessage } from 'element-plus'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['result', 'error'])

const isRecording = ref(false)
const recordingTime = ref(0)
const interimText = ref('')
let speechService = null
let timer = null

const toggleRecording = async () => {
  if (isRecording.value) {
    return
  }

  try {
    interimText.value = ''
    recordingTime.value = 0
    isRecording.value = true

    // 创建语音服务实例
    speechService = createSpeechService()

    // 启动识别
    await speechService.start(
      // onResult - 识别结果回调
      (text) => {
        interimText.value = text
      },
      // onError - 错误回调
      (error) => {
        ElMessage.error(error)
        emit('error', error)
        resetState()
      },
      // onEnd - 结束回调（服务器自动结束）
      () => {
        if (interimText.value) {
          emit('result', interimText.value)
        }
        resetState()
      }
    )

    // 启动计时器
    timer = setInterval(() => {
      recordingTime.value++
      // 60秒自动停止
      if (recordingTime.value >= 60) {
        ElMessage.warning('录音时长已达60秒，自动停止')
        stopRecording()
      }
    }, 1000)

  } catch (error) {
    ElMessage.error('启动语音识别失败: ' + error.message)
    emit('error', error.message)
    resetState()
  }
}

const stopRecording = () => {
  // 发送结果并重置状态（手动停止时，服务器可能无法响应）
  if (interimText.value) {
    emit('result', interimText.value)
  }
  resetState()
  if (speechService) {
    speechService.stop()
    speechService = null
  }
}

const resetState = () => {
  isRecording.value = false
  recordingTime.value = 0
  interimText.value = ''
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onUnmounted(() => {
  resetState()
  if (speechService) {
    speechService.cleanup()
    speechService = null
  }
})
</script>

<style scoped>
.voice-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.interim-text {
  flex: 1;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #91caff;
  border-radius: 6px;
  color: #0052cc;
  font-size: 14px;
  line-height: 1.5;
  min-height: 38px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.voice-input-wrapper :deep(.el-button) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.voice-input-wrapper :deep(.el-button .el-icon) {
  margin: 0;
}

.voice-input-wrapper :deep(.el-button.is-loading) {
  position: relative;
}

.voice-input-wrapper :deep(.el-button.is-loading::before) {
  margin-right: 8px;
}
</style>
