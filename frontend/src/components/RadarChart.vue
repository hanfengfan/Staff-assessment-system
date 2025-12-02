<template>
  <div class="radar-chart-container">
    <div ref="chartRef" class="chart" :style="{ width, height }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface Props {
  data: Array<{ tag: string; score: number }>
  width?: string
  height?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  title: '能力雷达图'
})

const chartRef = ref()
const chart = ref(null)

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || !props.data || props.data.length === 0) return

  // 销毁旧图表
  if (chart.value) {
    chart.value.dispose()
  }

  // 创建新图表
  chart.value = echarts.init(chartRef.value)

  // 准备数据
  const indicators = props.data.map(item => ({
    name: item.tag,
    max: 100,
    min: 0
  }))

  const radarData = props.data.map(item => ({
    value: item.score,
    name: item.tag
  }))

  const option = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        color: '#303133',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}: ${params.value.toFixed(1)}分`
      },
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#409eff',
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      }
    },
    legend: {
      data: ['能力水平'],
      orient: 'vertical',
      right: 20,
      top: 'center',
      textStyle: {
        color: '#606266',
        fontSize: 12
      }
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      center: ['50%', '55%'],
      axisName: {
        color: '#606266',
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(64, 158, 255, 0.1)',
            'rgba(64, 158, 255, 0.05)'
          ]
        }
      }
    },
    series: [
      {
        name: '能力水平',
        type: 'radar',
        data: [radarData],
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        },
        lineStyle: {
          color: '#409eff',
          width: 2
        },
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#409eff',
          borderColor: '#fff',
          borderWidth: 2
        },
        emphasis: {
          areaStyle: {
            color: 'rgba(64, 158, 255, 0.5)'
          },
          lineStyle: {
            color: '#409eff',
            width: 3
          }
        }
      }
    ],
    grid: {
      top: 80,
      bottom: 20
    }
  }

  chart.value.setOption(option)

  // 响应式处理
  const resizeHandler = () => {
    if (chart.value) {
      chart.value.resize()
    }
  }

  window.addEventListener('resize', resizeHandler)
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    renderChart()
  })
}, { deep: true })

// 监听尺寸变化
watch(() => [props.width, props.height], () => {
  nextTick(() => {
    renderChart()
  })
})

// 生命周期
onMounted(() => {
  nextTick(() => {
    renderChart()
  })
})

onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
  }
  window.removeEventListener('resize', () => {})
})

// 暴露方法给父组件
defineExpose({
  resizeChart: () => {
    if (chart.value) {
      chart.value.resize()
    }
  },
  getChart: () => chart.value,
  disposeChart: () => {
    if (chart.value) {
      chart.value.dispose()
      chart.value = null
    }
  }
})
</script>

<style scoped>
.radar-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart {
  width: v-bind(width);
  height: v-bind(height);
}
</style>