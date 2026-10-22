<template>
  <div class="staff-page">
    <el-card>
      <template #header>
        <div class="header-row">
          <h2>人员管理</h2>
          <div>
            <el-button @click="router.push('/admin')">
              <el-icon><ArrowLeft /></el-icon>
              返回管理员控制台
            </el-button>
            <el-button type="primary" @click="openCreate">新增员工</el-button>
          </div>
        </div>
      </template>

      <el-form :model="filter" inline @submit.prevent="search">
        <el-form-item label="搜索">
          <el-input v-model="filter.search" placeholder="姓名或工号" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item v-for="dim in dimensions" :key="dim.key" :label="dim.label">
          <el-select v-model="filter[dim.key]" clearable placeholder="全部" style="width: 150px">
            <el-option
              v-for="opt in dim.options"
              :key="opt.value"
              :label="`${opt.value} (${opt.count})`"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.is_active" clearable placeholder="全部" style="width: 110px">
            <el-option label="启用" value="true" />
            <el-option label="停用" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="job_number" label="工号" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="position" label="岗位" min-width="120" />
        <el-table-column prop="station" label="所属车站" min-width="120" />
        <el-table-column prop="zone" label="所属站区" min-width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170">
          <template #default="{ row }">{{ row.last_login ? formatTime(row.last_login) : '从未登录' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="toggleActive(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        @current-change="fetchList"
        @size-change="search"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑员工' : '新增员工'" width="480px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="姓名" prop="name"><el-input v-model="form.name" maxlength="50" /></el-form-item>
        <el-form-item label="工号" prop="job_number">
          <el-input v-model="form.job_number" maxlength="20" />
        </el-form-item>
        <el-form-item v-for="dim in dimensions" :key="dim.key" :label="dim.label" :prop="dim.key">
          <el-select
            v-model="form[dim.key]"
            filterable
            allow-create
            default-first-option
            clearable
            placeholder="选择或直接输入新值"
            style="width: 100%"
          >
            <el-option v-for="opt in dim.options" :key="opt.value" :label="opt.value" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="editingId ? '重置密码' : '初始密码'" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="new-password"
            :placeholder="editingId ? '不修改请留空' : '至少 6 位'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getStaffList, createStaff, updateStaff, deleteStaff, getStaffDimensions } from '@/api/staff'

const router = useRouter()

// 岗位 / 车站 / 站区是后续统计分析的维度，与后端 users/dimensions.py 保持一致
const DIMENSION_DEFS = [
  { key: 'position', label: '岗位' },
  { key: 'station', label: '所属车站' },
  { key: 'zone', label: '所属站区' }
]

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dimensionData = ref([])
const pagination = reactive({ page: 1, size: 20, total: 0 })
const filter = reactive({ search: '', position: '', station: '', zone: '', is_active: '' })

const dimensions = computed(() =>
  DIMENSION_DEFS.map(def => ({
    ...def,
    options: dimensionData.value.find(d => d.key === def.key)?.options || []
  }))
)

const formatTime = (value) => new Date(value).toLocaleString('zh-CN', { hour12: false })

const fetchDimensions = async () => {
  try {
    dimensionData.value = await getStaffDimensions()
  } catch (error) {
    ElMessage.error('获取岗位/车站/站区选项失败')
  }
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.size }
    Object.entries(filter).forEach(([k, v]) => {
      if (v) params[k] = v
    })
    const res = await getStaffList(params)
    list.value = res.results
    pagination.total = res.count
  } catch (error) {
    ElMessage.error('获取员工列表失败')
  } finally {
    loading.value = false
  }
}

const search = () => {
  pagination.page = 1
  fetchList()
}

const resetFilter = () => {
  Object.keys(filter).forEach(k => (filter[k] = ''))
  search()
}

// 新增 / 编辑
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const emptyForm = () => ({ name: '', job_number: '', position: '', station: '', zone: '', password: '' })
const form = reactive(emptyForm())

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  job_number: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  position: [{ required: true, message: '请选择或输入岗位', trigger: 'change' }],
  password: [
    {
      validator: (_rule, value, callback) => {
        if (!editingId.value && !value) return callback(new Error('请设置初始密码'))
        if (value && value.length < 6) return callback(new Error('密码至少 6 位'))
        callback()
      },
      trigger: 'blur'
    }
  ]
}

const resetForm = () => {
  Object.assign(form, emptyForm())
  editingId.value = null
  formRef.value?.clearValidate()
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  Object.assign(form, emptyForm(), {
    name: row.name,
    job_number: row.job_number,
    position: row.position,
    station: row.station,
    zone: row.zone
  })
  dialogVisible.value = true
}

// 后端校验错误形如 { job_number: ['...'] }，转成一条提示
const errorText = (error) => {
  const data = error.response?.data
  if (data && typeof data === 'object') {
    return Object.values(data).flat().join('；')
  }
  return '保存失败'
}

const save = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.password) delete payload.password
    if (editingId.value) {
      await updateStaff(editingId.value, payload)
    } else {
      await createStaff(payload)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await Promise.all([fetchList(), fetchDimensions()])
  } catch (error) {
    ElMessage.error(errorText(error))
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row) => {
  const action = row.is_active ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(
      row.is_active ? `停用后「${row.name}」将无法登录，已登录的状态也会失效。` : `确定启用「${row.name}」吗？`,
      `${action}确认`,
      { type: 'warning' }
    )
    await updateStaff(row.id, { is_active: !row.is_active })
    ElMessage.success(`已${action}`)
    fetchList()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(`${action}失败`)
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `删除「${row.name}（${row.job_number}）」会同时删除其全部考试记录和能力画像，且无法恢复。只是不想让其登录的话，请使用「停用」。`,
      '删除确认',
      { type: 'error', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deleteStaff(row.id)
    ElMessage.success('已删除')
    if (list.value.length === 1 && pagination.page > 1) pagination.page -= 1
    await Promise.all([fetchList(), fetchDimensions()])
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchDimensions()
  fetchList()
})
</script>

<style scoped>
.staff-page {
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
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
