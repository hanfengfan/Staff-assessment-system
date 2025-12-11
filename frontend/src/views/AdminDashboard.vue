<template>
  <div class="admin-dashboard">
    <el-card class="page-header">
      <template #header>
        <div class="header-content">
          <h2>管理员控制台</h2>
          <div class="header-actions">
            <el-button @click="goToDashboard">
              <el-icon><ArrowLeft /></el-icon>
              返回主控制台
            </el-button>
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
          </div>
        </div>
      </template>
    </el-card>

    <!-- 用户统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalUsers }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.activeUsers }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalExams }}</div>
            <div class="stat-label">总考试次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.avgScore }}</div>
            <div class="stat-label">平均得分</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 考试记录管理 -->
    <el-card class="exam-section">
      <template #header>
        <div class="section-header">
          <h3>考试记录管理</h3>
          <div class="header-actions">
            <el-button size="small" @click="showExamFilter = !showExamFilter">
              <el-icon><Filter /></el-icon>
              筛选
            </el-button>
            <el-button size="small" type="danger" @click="clearSelectedExams" :disabled="selectedExams.length === 0">
              <el-icon><Delete /></el-icon>
              删除选中 ({{ selectedExams.length }})
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选面板 -->
      <div v-show="showExamFilter" class="filter-panel">
        <el-form :model="examFilter" inline>
          <el-form-item label="用户">
            <el-select
              v-model="examFilter.userId"
              placeholder="选择用户"
              clearable
              filterable
              style="width: 220px"
              v-loading="userList.length === 0"
              element-loading-text="加载用户列表中..."
            >
              <el-option
                v-for="user in userList"
                :key="user.id"
                :label="`${user.username || user.get_full_name} (${user.job_number || '无工号'})`"
                :value="user.id"
              >
                <span style="float: left">{{ user.username || user.get_full_name || '未知用户' }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ user.job_number || '无工号' }}</span>
              </el-option>
              <template v-if="userList.length === 0" #empty>
                <div style="padding: 14px 0;">
                  <span>{{ userList.length === 0 && !loading ? '暂无用户数据' : '加载中...' }}</span>
                </div>
              </template>
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="examFilter.status"
              placeholder="选择状态"
              clearable
              :popper-append-to-body="false"
              style="width: 150px"
            >
              <el-option label="已完成" value="completed" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="未开始" value="not_started" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="filterExams">应用筛选</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 考试记录表格 -->
      <el-table
        :data="examList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="username" label="用户" width="150" />
        <el-table-column prop="job_number" label="工号" width="120" />
        <el-table-column prop="title" label="试卷标题" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="得分/总分" width="120">
          <template #default="{ row }">
            {{ row.score_obtained !== null ? `${row.score_obtained}/${row.total_score}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewExamDetail(row.id)">详情</el-button>
            <el-button size="small" type="danger" @click="deleteExam(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getExamList, deleteExam as deleteExamAPI, getExamStats } from '@/api/exam'
import { getUserList } from '@/api/analysis'

const router = useRouter()
const loading = ref(false)
const showExamFilter = ref(false)
const userList = ref([])
const examList = ref([])
const selectedExams = ref([])

// 统计数据
const stats = reactive({
  totalUsers: 0,
  activeUsers: 0,
  totalExams: 0,
  avgScore: 0
})

// 筛选条件
const examFilter = reactive({
  userId: null,
  status: null
})

// 分页
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await getExamStats()
    // 映射 API 响应字段到前端统计对象
    stats.totalUsers = response.total_users || 0
    stats.activeUsers = response.active_users || 0
    stats.totalExams = response.total_exams || 0
    stats.avgScore = response.avg_score || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

// 获取用户列表
const fetchUserList = async () => {
  try {
    const response = await getUserList()
    console.log('用户列表响应:', response)
    // 处理可能的响应结构
    if (response && response.results) {
      userList.value = response.results
    } else if (Array.isArray(response)) {
      userList.value = response
    } else {
      userList.value = []
      console.warn('用户列表数据格式异常:', response)
    }
    console.log('处理后的用户列表:', userList.value)
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
    userList.value = []
  }
}

// 获取考试列表
const fetchExamList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.size
    }

    // 应用筛选条件
    if (examFilter.userId) {
      params.user_id = examFilter.userId
    }
    if (examFilter.status) {
      params.status = examFilter.status
    }

    const response = await getExamList(params)
    examList.value = response.results || []
    pagination.total = response.count || 0
  } catch (error) {
    console.error('获取考试列表失败:', error)
    ElMessage.error('获取考试列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await Promise.all([
    fetchStats(),
    fetchUserList(),
    fetchExamList()
  ])
}

// 筛选考试
const filterExams = () => {
  pagination.current = 1
  fetchExamList()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedExams.value = selection
}

// 清除选中的考试
const clearSelectedExams = async () => {
  if (selectedExams.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedExams.value.length} 条考试记录吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 批量删除
    const deletePromises = selectedExams.value.map(exam => deleteExamAPI(exam.id))
    await Promise.all(deletePromises)

    ElMessage.success('删除成功')
    selectedExams.value = []
    await refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除考试记录失败:', error)
      ElMessage.error('删除考试记录失败')
    }
  }
}

// 查看考试详情
const viewExamDetail = (examId) => {
  router.push(`/result/${examId}`)
}

// 删除单条考试记录
const deleteExam = async (examId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条考试记录吗？此操作不可恢复！',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteExamAPI(examId)
    ElMessage.success('删除成功')
    await refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除考试记录失败:', error)
      ElMessage.error('删除考试记录失败')
    }
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  fetchExamList()
}

const handleCurrentChange = (current) => {
  pagination.current = current
  fetchExamList()
}

// 工具函数
const getStatusType = (status) => {
  const typeMap = {
    completed: 'success',
    in_progress: 'warning',
    not_started: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    completed: '已完成',
    in_progress: '进行中',
    not_started: '未开始'
  }
  return textMap[status] || '未知'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 返回主控制台
const goToDashboard = () => {
  router.push('/')
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.admin-dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px 0;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.exam-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-panel {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

/* 优化筛选面板中的表单项 */
.filter-panel .el-form-item {
  margin-bottom: 0;
}

/* 优化下拉选项的样式 */
.filter-panel .el-select-dropdown {
  max-width: 300px;
}

.filter-panel .el-select-dropdown__item {
  height: 40px;
  line-height: 40px;
  padding: 0 20px;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .admin-dashboard {
    padding: 12px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .stats-section {
    margin-bottom: 16px;
  }

  .section-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .el-button {
    flex: 1;
  }
}
</style>