import CryptoJS from 'crypto-js'

// 科大讯飞语音听写配置
const config = {
  host: 'iat-api.xfyun.cn',
  appId: import.meta.env.VITE_XFYUN_APP_ID,
  apiKey: import.meta.env.VITE_XFYUN_API_KEY,
  apiSecret: import.meta.env.VITE_XFYUN_API_SECRET
}

/**
 * 生成WebSocket鉴权URL
 */
export function generateAuthUrl() {
  const host = config.host
  const date = new Date().toUTCString()
  const requestLine = 'GET /v2/iat HTTP/1.1'

  // 签名原始字段
  const signatureOrigin = `host: ${host}\ndate: ${date}\n${requestLine}`

  // HMAC-SHA256签名
  const signatureSha = CryptoJS.HmacSHA256(signatureOrigin, config.apiSecret).toString(CryptoJS.enc.Base64)

  // authorization
  const authorizationOrigin = `api_key="${config.apiKey}", algorithm="hmac-sha256", headers="host date request-line", signature="${signatureSha}"`
  const authorization = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(authorizationOrigin))

  return `wss://${host}/v2/iat?authorization=${encodeURIComponent(authorization)}&date=${encodeURIComponent(date)}&host=${host}`
}

/**
 * 科大讯飞语音识别服务类
 */
export class XfyunSpeechService {
  constructor() {
    this.ws = null
    this.scriptProcessor = null
    this.audioSource = null
    this.pcmBuffer = []
    this.onResult = null
    this.onError = null
    this.onEnd = null
    this.recognitionText = ''
    this.isRecording = false
    this.audioContext = null
    this.stream = null
  }

  /**
   * 启动语音识别
   * @param {Function} onResult - 识别结果回调
   * @param {Function} onError - 错误回调
   * @param {Function} onEnd - 结束回调
   */
  async start(onResult, onError, onEnd) {
    this.onResult = onResult
    this.onError = onError
    this.onEnd = onEnd
    this.recognitionText = ''
    this.pcmBuffer = []

    try {
      // 1. 获取麦克风权限
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // 2. 创建AudioContext用于音频处理
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      })

      // 3. 建立WebSocket连接
      await this.connectWebSocket()

      // 4. 使用ScriptProcessorNode直接采集PCM数据
      this.audioSource = this.audioContext.createMediaStreamSource(this.stream)
      this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1)

      this.scriptProcessor.onaudioprocess = (e) => {
        if (this.isRecording) {
          const inputData = e.inputBuffer.getChannelData(0)
          const pcmData = this.floatTo16BitPCM(inputData)
          this.pcmBuffer.push(pcmData)
        }
      }

      this.audioSource.connect(this.scriptProcessor)
      this.scriptProcessor.connect(this.audioContext.destination)
      this.isRecording = true

      // 定时发送音频数据
      this.sendInterval = setInterval(() => {
        this.sendAudioData()
      }, 40)

    } catch (error) {
      this.onError?.(error.message || '无法访问麦克风')
      this.cleanup()
    }
  }

  /**
   * 建立WebSocket连接
   */
  connectWebSocket() {
    return new Promise((resolve, reject) => {
      const url = generateAuthUrl()
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        // 发送首帧握手数据
        this.sendFirstFrame()
        resolve()
      }

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data)
      }

      this.ws.onerror = (error) => {
        reject(new Error('WebSocket连接失败'))
      }

      this.ws.onclose = () => {
        this.isRecording = false
      }
    })
  }

  /**
   * 发送首帧握手数据
   */
  sendFirstFrame() {
    const data = {
      common: { app_id: config.appId },
      business: {
        language: 'zh_cn',
        domain: 'iat',
        accent: 'mandarin',
        vad_eos: 5000,
        dwa: 'wpgs'  // 开启动态修正
      },
      data: {
        status: 0,
        format: 'audio/L16;rate=16000',
        encoding: 'raw',
        audio: '',
      }
    }
    this.ws.send(JSON.stringify(data))
  }

  /**
   * 发送音频数据
   */
  sendAudioData() {
    if (!this.isRecording || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return
    }

    if (this.pcmBuffer.length === 0) {
      return
    }

    try {
      // 取出所有PCM数据并发送
      const allPcmData = this.pcmBuffer.splice(0, this.pcmBuffer.length)
      const combinedData = this.combinePcmData(allPcmData)

      // 转换为base64
      const base64Audio = this.arrayBufferToBase64(combinedData)

      // 发送数据（分帧发送，每帧1280字节）
      const frameSize = 1280
      for (let i = 0; i < base64Audio.length; i += frameSize) {
        const frame = base64Audio.slice(i, i + frameSize)
        const data = {
          data: {
            status: 1,  // 中间帧
            format: 'audio/L16;rate=16000',
            encoding: 'raw',
            audio: frame
          }
        }
        this.ws.send(JSON.stringify(data))
      }
    } catch (error) {
      console.error('音频数据处理错误:', error)
    }
  }

  /**
   * Float32Array转Int16Array PCM数据
   */
  floatTo16BitPCM(float32Array) {
    const int16Array = new Int16Array(float32Array.length)
    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]))
      int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
    }
    return int16Array.buffer
  }

  /**
   * 合并多个PCM数据块
   */
  combinePcmData(pcmBuffers) {
    const totalLength = pcmBuffers.reduce((sum, buffer) => sum + buffer.byteLength, 0)
    const combined = new Int16Array(totalLength / 2)  // Int16Array每个元素2字节
    let offset = 0

    for (const buffer of pcmBuffers) {
      const int16Array = new Int16Array(buffer)
      combined.set(int16Array, offset)
      offset += int16Array.length
    }

    return combined.buffer
  }

  /**
   * ArrayBuffer转Base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }

  /**
   * 处理服务器返回的消息
   */
  handleMessage(data) {
    try {
      const response = JSON.parse(data)

      if (response.code !== 0) {
        this.onError?.(`识别错误: ${response.message}`)
        return
      }

      if (response.data && response.data.result) {
        const result = response.data.result
        let text = ''

        // 解析识别结果
        if (result.ws) {
          for (const ws of result.ws) {
            if (ws.cw && ws.cw.length > 0) {
              text += ws.cw[0].w
            }
          }
        }

        // 识别结束（status=2 时不再调用 onResult，避免覆盖之前的结果）
        if (response.data.status === 2) {
          this.onEnd?.()
          this.stop()
        } else if (text) {
          this.onResult?.(text)
        }
      }
    } catch (error) {
      console.error('消息解析错误:', error)
    }
  }

  /**
   * 停止录音
   */
  stop() {
    if (!this.isRecording) {
      return
    }

    this.isRecording = false

    // 发送结束帧
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const data = {
        data: {
          status: 2,  // 结束帧
          format: 'audio/L16;rate=16000',
          encoding: 'raw',
          audio: ''
        }
      }
      this.ws.send(JSON.stringify(data))
    }

    this.cleanup()
  }

  /**
   * 清理资源
   */
  cleanup() {
    if (this.sendInterval) {
      clearInterval(this.sendInterval)
      this.sendInterval = null
    }

    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect()
      this.scriptProcessor = null
    }

    if (this.audioSource) {
      this.audioSource.disconnect()
      this.audioSource = null
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }

    this.isRecording = false
    this.pcmBuffer = []
  }
}

/**
 * 创建语音识别服务实例
 */
export function createSpeechService() {
  return new XfyunSpeechService()
}
