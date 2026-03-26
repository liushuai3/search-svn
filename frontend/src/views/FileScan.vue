<template>
  <div class="file-scan">
    <Card title="文件扫描">
      <!-- 网络状态提示 -->
      <Alert
        v-if="networkStatus === 'offline'"
        message="网络连接已断开"
        description="扫描功能需要网络连接，请检查网络后重试"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />
      
      <!-- WebSocket 连接状态 -->
      <Alert
        v-else-if="wsStatus === 'disconnected' && taskStatus.status === '扫描中'"
        message="实时连接已断开"
        description="正在尝试重新连接..."
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      
      <!-- 错误提示 -->
      <Alert
        v-if="errorMessage"
        :message="errorMessage"
        type="error"
        show-icon
        closable
        @close="errorMessage = ''"
        style="margin-bottom: 16px"
      />
      
      <!-- 无任务状态 -->
      <Empty
        v-if="taskStatus.status === 'no_task' && !loading"
        description="暂无扫描任务"
        style="margin: 40px 0"
      >
        <template #extra>
          <Button type="primary" @click="startNewScan">创建新任务</Button>
        </template>
      </Empty>
      
      <div v-else-if="taskStatus.status !== 'no_task'" class="task-status">
        <div class="status-info">
          <p><strong>状态：</strong>
            <Tag :color="statusColor">{{ taskStatus.status }}</Tag>
          </p>
          <p><strong>已扫描：</strong>{{ taskStatus.scanned_count }} 条</p>
          <p v-if="taskStatus.now_scan_dir"><strong>当前目录：</strong>{{ taskStatus.now_scan_dir }}</p>
        </div>
        
        <!-- 扫描日志 -->
        <div class="log-container" v-if="logs.length > 0">
          <h4>扫描日志</h4>
          <div class="log-content" ref="logContent" role="log" aria-live="polite" aria-atomic="false">
            <div v-for="(log, index) in logs" :key="index" class="log-item">{{ log }}</div>
          </div>
        </div>
        
        <!-- 空日志提示 -->
        <Empty
          v-else-if="taskStatus.status === '未开始'"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
          description="点击开始扫描以查看日志"
          style="margin: 20px 0"
        />
      </div>
      
      <div class="buttons" style="margin-top: 20px">
        <Button 
          type="primary" 
          :loading="loading && actionType === 'new'" 
          @click="startNewScan" 
          :disabled="taskStatus.status === '扫描中' || networkStatus === 'offline'"
        >
          开始全新扫描
        </Button>
        <Button 
          style="margin-left: 8px" 
          :loading="loading && actionType === 'resume'" 
          @click="resumeScan" 
          :disabled="taskStatus.status === '扫描中' || taskStatus.status === 'no_task' || networkStatus === 'offline'"
        >
          继续扫描
        </Button>
        <Button 
          style="margin-left: 8px" 
          :loading="loading && actionType === 'pause'" 
          @click="pauseScan" 
          :disabled="taskStatus.status !== '扫描中'"
        >
          暂停扫描
        </Button>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { Button, Card, Progress, message, Alert, Empty, Tag } from 'ant-design-vue'
import { API_ENDPOINTS } from '../config/api'

const taskStatus = ref({ status: 'no_task' })
const logs = ref([])
const logContent = ref(null)
const ws = ref(null)
const loading = ref(false)
const actionType = ref('') // 'new', 'resume', 'pause'
const errorMessage = ref('')
const wsStatus = ref('connecting') // 'connecting', 'connected', 'disconnected'
const networkStatus = ref('online')
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 5

// 计算进度百分比
const progressPercent = ref(0)
const progressFormat = (percent) => {
  return `${percent}%`
}

// 进度条状态
const progressStatus = computed(() => {
  if (taskStatus.value.status === '已完成') return 'success'
  if (taskStatus.value.status === '失败') return 'exception'
  if (taskStatus.value.status === '已暂停') return 'normal'
  return 'active'
})

// 状态标签颜色
const statusColor = computed(() => {
  const colors = {
    '未开始': 'default',
    '扫描中': 'processing',
    '已暂停': 'warning',
    '已完成': 'success',
    '失败': 'error'
  }
  return colors[taskStatus.value.status] || 'default'
})

// 加载任务状态
const loadTaskStatus = async () => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    
    const response = await fetch(API_ENDPOINTS.taskStatus, {
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const data = await response.json()
    taskStatus.value = data
    if (data.total_count > 0) {
      progressPercent.value = Math.round((data.scanned_count / data.total_count) * 100)
    }
    errorMessage.value = ''
  } catch (error) {
    console.error('加载任务状态失败:', error)
    if (error.name !== 'AbortError') {
      errorMessage.value = '无法获取任务状态，请检查后端服务'
    }
  }
}

// 开始全新扫描
const startNewScan = async () => {
  try {
    loading.value = true
    actionType.value = 'new'
    errorMessage.value = ''
    
    if (networkStatus.value === 'offline') {
      message.error('网络已断开，无法开始扫描')
      return
    }
    
    // 获取配置
    const configResponse = await fetch(API_ENDPOINTS.configGet)
    if (!configResponse.ok) {
      throw new Error('无法连接到服务器')
    }
    
    const config = await configResponse.json()
    if (config.status === 'no_config') {
      message.error('请先配置SVN信息')
      // 触发菜单切换事件
      window.dispatchEvent(new CustomEvent('changeMenu', { detail: 'config' }))
      return
    }
    
    // 清空旧日志
    logs.value = []
    
    // 创建新任务
    const response = await fetch(API_ENDPOINTS.taskNew, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        root_svn_url: config.root_svn_url,
        username: config.username,
        password: config.password,
        batch_size: config.batch_size
      })
    })
    
    if (!response.ok) {
      throw new Error(`创建任务失败: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描任务已创建')
      // 启动扫描
      await resumeScan(data.task_id)
    } else {
      throw new Error(data.message || '创建任务失败')
    }
  } catch (error) {
    console.error('开始扫描失败:', error)
    errorMessage.value = `开始扫描失败: ${error.message}`
    message.error(errorMessage.value)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// 继续扫描
const resumeScan = async (taskId) => {
  try {
    loading.value = true
    actionType.value = 'resume'
    errorMessage.value = ''
    
    if (networkStatus.value === 'offline') {
      message.error('网络已断开，无法继续扫描')
      return
    }
    
    // 检查taskId是否是事件对象，如果是，则使用taskStatus.value.task_id
    let id = taskId
    if (typeof taskId === 'object' && taskId.type && taskId.target) {
      id = taskStatus.value.task_id
    }
    id = id || taskStatus.value.task_id
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch(`${API_ENDPOINTS.taskResume}?task_id=${id}`, {
      method: 'POST',
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`启动失败: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描任务已启动')
      loadTaskStatus()
    } else {
      throw new Error(data.message || '启动失败')
    }
  } catch (error) {
    console.error('继续扫描失败:', error)
    errorMessage.value = `继续扫描失败: ${error.message}`
    message.error(errorMessage.value)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// 暂停扫描
const pauseScan = async () => {
  try {
    loading.value = true
    actionType.value = 'pause'
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    
    const response = await fetch(API_ENDPOINTS.taskPause, {
      method: 'POST',
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`暂停失败: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描已暂停')
      loadTaskStatus()
    } else {
      throw new Error(data.message || '暂停失败')
    }
  } catch (error) {
    console.error('暂停扫描失败:', error)
    errorMessage.value = `暂停扫描失败: ${error.message}`
    message.error(errorMessage.value)
  } finally {
    loading.value = false
    actionType.value = ''
  }
}

// 连接WebSocket
const connectWebSocket = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }
  
  wsStatus.value = 'connecting'
  
  try {
    ws.value = new WebSocket(API_ENDPOINTS.wsProgress)
    
    ws.value.onopen = () => {
      wsStatus.value = 'connected'
      reconnectAttempts.value = 0
      console.log('WebSocket 已连接')
    }
    
    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        taskStatus.value = data
        if (data.total_count > 0) {
          progressPercent.value = Math.round((data.scanned_count / data.total_count) * 100)
        }
        // 只有在扫描中时才添加日志
        if (data.status === '扫描中' && data.scanned_count > 0) {
          // 避免重复日志
          const lastLog = logs.value[logs.value.length - 1]
          const newLog = `${new Date().toLocaleString()} - 已扫描 ${data.scanned_count} 个文件`
          if (!lastLog || !lastLog.includes(`${data.scanned_count} 个文件`)) {
            logs.value.push(newLog)
            // 限制日志数量，避免内存溢出
            if (logs.value.length > 1000) {
              logs.value = logs.value.slice(-500)
            }
            // 保持日志滚动到底部
            nextTick(() => {
              setTimeout(() => {
                if (logContent.value) {
                  logContent.value.scrollTop = logContent.value.scrollHeight
                }
              }, 50)
            })
          }
        }
      } catch (e) {
        console.error('解析 WebSocket 消息失败:', e)
      }
    }
    
    ws.value.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      wsStatus.value = 'disconnected'
    }
    
    ws.value.onclose = () => {
      wsStatus.value = 'disconnected'
      // 限制重连次数
      if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++
        const delay = Math.min(3000 * reconnectAttempts.value, 30000) // 指数退避，最大30秒
        console.log(`WebSocket 断开，${delay}ms 后重连 (尝试 ${reconnectAttempts.value}/${maxReconnectAttempts})`)
        setTimeout(connectWebSocket, delay)
      } else {
        console.log('WebSocket 重连次数已达上限')
        errorMessage.value = '实时连接已断开，请刷新页面重试'
      }
    }
  } catch (error) {
    console.error('创建 WebSocket 连接失败:', error)
    wsStatus.value = 'disconnected'
  }
}

// 监听网络状态
const handleOnline = () => {
  networkStatus.value = 'online'
  message.success('网络已恢复')
  // 重新连接 WebSocket
  if (wsStatus.value === 'disconnected') {
    reconnectAttempts.value = 0
    connectWebSocket()
  }
}

const handleOffline = () => {
  networkStatus.value = 'offline'
  message.warning('网络已断开')
}

// 组件挂载时
onMounted(() => {
  loadTaskStatus()
  connectWebSocket()
  
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  networkStatus.value = navigator.onLine ? 'online' : 'offline'
})

// 组件卸载时
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
.file-scan {
  padding: 20px;
}

.status-info {
  margin-bottom: 20px;
}

.log-container {
  margin-top: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 10px;
}

.log-container h4 {
  margin: 0 0 10px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.log-content {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
  height: 250px;
  overflow-y: auto;
}

.log-item {
  padding: 2px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.buttons {
  margin-top: 20px;
}
</style>
