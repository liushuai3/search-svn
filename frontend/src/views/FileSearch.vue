<template>
  <div class="file-search">
    <Card title="文件搜索" class="search-card">
      <div class="search-form">
        <Input
          v-model:value="searchKeyword"
          placeholder="请输入搜索关键字（为空时查询所有文件）"
          style="width: 300px"
          @keyup.enter="handleSearch"
          :disabled="networkStatus === 'offline'"
        />
        <Button 
          type="primary" 
          @click="handleSearch" 
          :loading="loading"
          :disabled="networkStatus === 'offline'"
          style="margin-left: 8px"
        >
          搜索
        </Button>
      </div>
      
      <!-- 网络离线提示 -->
      <Alert
        v-if="networkStatus === 'offline'"
        message="网络连接已断开"
        description="请检查网络连接后重试"
        type="warning"
        show-icon
        style="margin-top: 16px"
      />
      
      <!-- 错误提示 -->
      <Alert
        v-else-if="errorMessage"
        :message="errorMessage"
        type="error"
        show-icon
        closable
        @close="errorMessage = ''"
        style="margin-top: 16px"
      />
      
      <!-- 骨架屏 -->
      <div v-if="loading && searchResults.length === 0" class="table-container">
        <Skeleton active :paragraph="{ rows: 10 }" />
      </div>
      
      <!-- 表格内容 -->
      <div v-else-if="searchResults.length > 0" class="table-wrapper">
        <Table
          :data-source="searchResults"
          :columns="columns"
          :pagination="false"
          :loading="loading && searchResults.length > 0"
          :scroll="{ y: 'calc(100vh - 320px)' }"
          size="middle"
        >
          <template #action="{ record }">
            <Button type="link" @click="copySvnUrl(record.svn_url)">复制链接</Button>
            <Button type="link" @click="downloadFile(record.svn_url, record.file_name)">下载文件</Button>
          </template>
        </Table>
        <!-- 分页固定在底部 -->
        <div class="pagination-wrapper">
          <Pagination
            v-model:current="pagination.current"
            v-model:pageSize="pagination.pageSize"
            :total="pagination.total"
            :page-size-options="pagination.pageSizeOptions"
            show-size-changer
            show-quick-jumper
            :show-total="total => `共 ${total} 条`"
            @change="handlePageChange"
            @showSizeChange="handleSizeChange"
          />
        </div>
      </div>
      
      <!-- 空状态 -->
      <Empty
        v-else-if="!loading && hasSearched"
        :description="searchKeyword ? '未找到匹配的文件' : '暂无文件数据'"
        style="margin-top: 40px"
      >
        <template #extra>
          <Button v-if="searchKeyword" @click="clearSearch">清除搜索</Button>
          <Button v-else type="primary" @click="goToScan">前往扫描</Button>
        </template>
      </Empty>
      
      <!-- 初始提示 -->
      <Empty
        v-else-if="!loading && !hasSearched"
        description="请输入关键字开始搜索"
        style="margin-top: 40px"
      />
    </Card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Button, Card, Input, Table, Pagination, message, Skeleton, Empty, Alert } from 'ant-design-vue'
import { API_ENDPOINTS } from '../config/api'

const searchKeyword = ref('')
const searchResults = ref([])
const loading = ref(false)
const hasSearched = ref(false)
const errorMessage = ref('')
const networkStatus = ref('online')

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  pageSizeOptions: ['10', '20', '50', '100']
})

// 页码变化
const handlePageChange = (page, pageSize) => {
  pagination.current = page
  if (pageSize !== pagination.pageSize) {
    pagination.pageSize = pageSize
  }
  handleSearch()
}

// 分页大小变化
const handleSizeChange = (current, size) => {
  pagination.current = 1 // 切换分页大小时重置到第一页
  pagination.pageSize = size
  handleSearch()
}

const columns = [
  {
    title: '文件名',
    dataIndex: 'file_name',
    key: 'file_name'
  },
  {
    title: '路径',
    dataIndex: 'file_path',
    key: 'file_path'
  },
  {
    title: 'SVN链接',
    dataIndex: 'svn_url',
    key: 'svn_url',
    ellipsis: true
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' }
  }
]

// 处理搜索
const handleSearch = async () => {
  loading.value = true
  errorMessage.value = ''
  hasSearched.value = true
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30秒超时
    
    const response = await fetch(
      `${API_ENDPOINTS.fileSearch}?kw=${encodeURIComponent(searchKeyword.value)}&page=${pagination.current}&page_size=${pagination.pageSize}`
      { signal: controller.signal }
    )
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      searchResults.value = data.files
      pagination.total = data.total
    } else {
      throw new Error(data.message || '搜索失败')
    }
  } catch (error) {
    console.error('搜索失败:', error)
    if (error.name === 'AbortError') {
      // 请求被取消（可能是组件切换），不显示错误
      return
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage.value = '无法连接到服务器，请检查后端服务是否运行'
    } else {
      errorMessage.value = `搜索失败: ${error.message}`
    }
    message.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

// 清除搜索
const clearSearch = () => {
  searchKeyword.value = ''
  hasSearched.value = false
  searchResults.value = []
  pagination.total = 0
  pagination.current = 1
  errorMessage.value = ''
}

// 前往扫描页面
const goToScan = () => {
  // 触发自定义事件通知父组件切换菜单
  window.dispatchEvent(new CustomEvent('changeMenu', { detail: 'scan' }))
}

// 监听网络状态
const handleOnline = () => {
  networkStatus.value = 'online'
  message.success('网络已恢复')
}

const handleOffline = () => {
  networkStatus.value = 'offline'
  message.warning('网络已断开')
}

onMounted(() => {
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  networkStatus.value = navigator.onLine ? 'online' : 'offline'
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

// 复制SVN链接
const copySvnUrl = (url) => {
  if (!url) {
    message.error('链接为空')
    return
  }
  navigator.clipboard.writeText(url).then(() => {
    message.success('链接已复制')
  }).catch(() => {
    message.error('复制失败')
  })
}

// 下载文件
const downloadFile = async (svnUrl, fileName) => {
  if (!svnUrl) {
    message.error('链接为空')
    return
  }
  
  if (networkStatus.value === 'offline') {
    message.error('网络已断开，无法下载')
    return
  }
  
  try {
    message.loading('正在准备下载...', 1)
    // 调用后端的下载接口，在新窗口中打开
    window.open(
      `${API_ENDPOINTS.fileDownload}?file_url=${encodeURIComponent(svnUrl)}&file_name=${encodeURIComponent(fileName)}`
      '_blank',
      'noopener,noreferrer'
    )
    message.success('开始下载文件')
  } catch (error) {
    message.error('下载失败: ' + error.message)
  }
}
</script>

<style scoped>
.file-search {
  padding: 20px;
  height: 100%;
  overflow: hidden;
}

.search-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-card :deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-form {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.table-wrapper :deep(.ant-table-wrapper) {
  flex: 1;
  overflow: hidden;
}

.table-wrapper :deep(.ant-table) {
  height: 100%;
}

.table-wrapper :deep(.ant-table-container) {
  height: 100%;
}

.table-wrapper :deep(.ant-table-body) {
  overflow-y: auto !important;
}

.pagination-wrapper {
  flex-shrink: 0;
  padding: 16px 0 0 0;
  text-align: right;
  border-top: 1px solid #f0f0f0;
  margin-top: auto;
}

.table-container {
  flex: 1;
  padding: 20px 0;
}
</style>
