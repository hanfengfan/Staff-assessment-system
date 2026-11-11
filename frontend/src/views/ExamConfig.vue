<template>
  <div class="config-page" v-loading="loading">
    <el-card>
      <template #header>
        <div class="header-row">
          <h2>组卷规则</h2>
          <el-button @click="router.push('/admin')">
            <el-icon><ArrowLeft /></el-icon>
            返回管理员控制台
          </el-button>
        </div>
      </template>

      <el-alert
        v-if="!configured"
        type="warning"
        :closable="false"
        show-icon
        title="还没有保存过组卷规则，员工暂时无法生成试卷"
        class="tip"
      />
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="普通员工会先按自己的“所属线路”、再按“岗位级别”筛出可抽的题目，然后按这里的规则抽题；管理员账号不筛选。"
        class="tip"
      />

      <el-form label-width="120px" class="config-form">
        <el-form-item label="题库专业" required>
          <el-checkbox-group v-model="form.bank_subjects" @change="onSubjectsChange">
            <el-checkbox v-for="s in options" :key="s.name" :label="s.name" :value="s.name">
              {{ s.name }}（{{ s.total }} 题）
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="一级目录权重">
          <div v-if="categories.length === 0" class="hint">先选择题库专业</div>
          <div v-else class="weights">
            <div class="hint">可选。权重越大越优先抽取；留空或 0 表示不设权重。优先抽权重高的目录，题不够再从整个题库专业补。</div>
            <div v-for="c in categories" :key="c.name" class="weight-row">
              <span class="weight-name">{{ c.name }}（{{ c.count }} 题）</span>
              <el-input-number v-model="form.category_weights[c.name]" :min="0" :max="100" :step="1" size="small" controls-position="right" />
            </div>
          </div>
        </el-form-item>

        <el-form-item label="各题型数量" required>
          <div class="type-grid">
            <div v-for="t in TYPES" :key="t.key" class="type-item">
              <span>{{ t.label }}</span>
              <el-input-number v-model="form.type_counts[t.key]" :min="0" :max="500" size="small" controls-position="right" />
              <span class="hint">可用 {{ available.types[t.key] || 0 }}</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="总题数">
          <strong>{{ totalCount }}</strong>
          <span class="hint">（各题型数量之和，每题平均分配 100 分）</span>
        </el-form-item>

        <el-form-item label="难度分层比例" required>
          <div class="type-grid">
            <div v-for="lv in LEVELS" :key="lv" class="type-item">
              <span>{{ lv }}</span>
              <el-input-number v-model="form.difficulty_ratio[lv]" :min="0" :max="100" size="small" controls-position="right" />
              <span class="hint">占 {{ ratioPercent(lv) }}% · 可用 {{ available.levels[lv] || 0 }}</span>
            </div>
          </div>
          <div class="hint">按比例分配到每个题型内部，例如 2:5:3。</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存规则</el-button>
          <el-button @click="load">放弃修改</el-button>
          <span v-if="updatedAt" class="hint">上次保存：{{ updatedAt }}</span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getExamConfig, saveExamConfig, getExamConfigOptions } from '@/api/examConfig'

const router = useRouter()

const TYPES = [
  { key: 'single', label: '单选题' },
  { key: 'multiple', label: '多选题' },
  { key: 'true_false', label: '判断题' },
  { key: 'subjective', label: '主观题' }
]
const LEVELS = ['易', '中', '难']

const loading = ref(false)
const saving = ref(false)
const configured = ref(false)
const updatedAt = ref('')
const options = ref([])
const form = reactive({
  bank_subjects: [],
  category_weights: {},
  type_counts: { single: 0, multiple: 0, true_false: 0, subjective: 0 },
  difficulty_ratio: { 易: 0, 中: 0, 难: 0 }
})

const selected = computed(() => options.value.filter(s => form.bank_subjects.includes(s.name)))

// 所选题库专业下的一级目录（同名目录的题量合并）
const categories = computed(() => {
  const merged = {}
  selected.value.forEach(s => s.categories.forEach(c => {
    merged[c.name] = (merged[c.name] || 0) + c.count
  }))
  return Object.entries(merged).map(([name, count]) => ({ name, count }))
})

// 所选题库专业下，各题型、各难度的可用题量
const available = computed(() => {
  const types = {}
  const levels = {}
  selected.value.forEach(s => {
    Object.entries(s.types).forEach(([k, v]) => (types[k] = (types[k] || 0) + v))
    Object.entries(s.levels).forEach(([k, v]) => (levels[k] = (levels[k] || 0) + v))
  })
  return { types, levels }
})

const totalCount = computed(() => TYPES.reduce((sum, t) => sum + (form.type_counts[t.key] || 0), 0))

const ratioPercent = (lv) => {
  const sum = LEVELS.reduce((s, k) => s + (form.difficulty_ratio[k] || 0), 0)
  return sum ? Math.round(((form.difficulty_ratio[lv] || 0) / sum) * 100) : 0
}

// 取消选择某个题库专业后，清掉已不在可选范围内的目录权重
const onSubjectsChange = () => {
  const names = new Set(categories.value.map(c => c.name))
  Object.keys(form.category_weights).forEach(k => {
    if (!names.has(k)) delete form.category_weights[k]
  })
}

const formatTime = (value) => new Date(value).toLocaleString('zh-CN', { hour12: false })

const load = async () => {
  loading.value = true
  try {
    const [opts, cfg] = await Promise.all([getExamConfigOptions(), getExamConfig()])
    options.value = opts
    configured.value = cfg.configured
    updatedAt.value = cfg.updated_at ? formatTime(cfg.updated_at) : ''
    form.bank_subjects = cfg.bank_subjects || []
    form.category_weights = { ...(cfg.category_weights || {}) }
    TYPES.forEach(t => (form.type_counts[t.key] = cfg.type_counts?.[t.key] || 0))
    LEVELS.forEach(lv => (form.difficulty_ratio[lv] = cfg.difficulty_ratio?.[lv] || 0))
  } catch (error) {
    ElMessage.error('获取组卷规则失败')
  } finally {
    loading.value = false
  }
}

const save = async () => {
  saving.value = true
  try {
    // 权重为空或 0 的目录不提交
    const weights = {}
    Object.entries(form.category_weights).forEach(([k, v]) => {
      if (v > 0) weights[k] = v
    })
    const cfg = await saveExamConfig({
      bank_subjects: form.bank_subjects,
      category_weights: weights,
      total_count: totalCount.value,
      type_counts: form.type_counts,
      difficulty_ratio: form.difficulty_ratio
    })
    configured.value = cfg.configured
    updatedAt.value = cfg.updated_at ? formatTime(cfg.updated_at) : ''
    ElMessage.success('组卷规则已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.config-page {
  padding: 24px;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-row h2 {
  margin: 0;
}
.tip {
  margin-bottom: 12px;
}
.config-form {
  margin-top: 16px;
  max-width: 820px;
}
.hint {
  color: #909399;
  font-size: 13px;
  margin-left: 8px;
}
.weights .hint {
  display: block;
  margin: 0 0 8px;
}
.weight-row,
.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.weight-row {
  margin-bottom: 6px;
}
.weight-name {
  width: 260px;
}
.type-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 28px;
}
</style>
