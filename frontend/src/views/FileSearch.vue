<template>
  <div class="file-search">
    <Card title="文件搜索">
      <div class="search-form">
        <Input
          v-model:value="searchKeyword"
          placeholder="请输入搜索关键字（为空时查询所有文件）"
          style="width: 300px"
          @keyup.enter="handleSearch"
        >
          <template #addonAfter>
            <Button type="primary" @click="handleSearch">搜索</Button>
          </template>
        </Input>
      </div>
      <Table
        :data-source="searchResults"
        :columns="columns"
        :pagination="pagination"
        :loading="loading"
        style="margin-top: 20px"
      >
        <template #action="{ record }">
          <Button type="link" @click="copySvnUrl(record.svn_url)">复制链接</Button>
          <Button type="link" @click="downloadFile(record.svn_url, record.file_name)">下载文件</Button>
        </template>
      </Table>
    </Card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Button, Card, Input, Table, message } from 'ant-design-vue'

const searchKeyword = ref('')
const searchResults = ref([])
const loading = ref(false)
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  onChange: (page) => {
    pagination.current = page
    handleSearch()
  }
})

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
  try {
    const response = await fetch(`http://localhost:8001/api/file/search?kw=${encodeURIComponent(searchKeyword.value)}&page=${pagination.current}&page_size=${pagination.pageSize}`)
    const data = await response.json()
    if (data.status === 'success') {
      searchResults.value = data.files
      pagination.total = data.total
    }
  } catch (error) {
    console.error('搜索失败:', error)
    message.error('搜索失败')
  } finally {
    loading.value = false
  }
}

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
const downloadFile = (svnUrl, fileName) => {
  if (!svnUrl) {
    message.error('链接为空')
    return
  }
  // 调用后端的下载接口，在新窗口中打开
  window.open(`http://localhost:8001/api/file/download?file_url=${encodeURIComponent(svnUrl)}&file_name=${encodeURIComponent(fileName)}`, '_blank', 'noopener,noreferrer')
  message.success('开始下载文件')
}
</script>

<style scoped>
.file-search {
  padding: 20px;
}

.search-form {
  margin-bottom: 20px;
}
</style>
