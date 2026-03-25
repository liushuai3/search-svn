<template>
  <div class="file-scan">
    <Card title="文件扫描">
      <div v-if="taskStatus.status !== 'no_task'" class="task-status">
        <Progress 
          :percent="progressPercent" 
          status="active" 
          :format="progressFormat" 
          style="margin-bottom: 20px" 
        />
        <div class="status-info">
          <p>状态：{{ taskStatus.status }}</p>
          <p>已扫描：{{ taskStatus.scanned_count }} / {{ taskStatus.total_count || '未知' }}</p>
          <p>当前目录：{{ taskStatus.now_scan_dir || '未开始' }}</p>
        </div>
        <div class="log-container">
          <h4>扫描日志</h4>
          <div class="log-content" ref="logContent">
            <div v-for="(log, index) in logs" :key="index">{{ log }}</div>
          </div>
        </div>
      </div>
      <div class="buttons" style="margin-top: 20px">
        <Button type="primary" :loading="loading" @click="startNewScan" :disabled="taskStatus.status === '扫描中'">开始全新扫描</Button>
        <Button style="margin-left: 8px" :loading="loading" @click="resumeScan" :disabled="taskStatus.status === '扫描中' || taskStatus.status === 'no_task'">继续扫描</Button>
        <Button style="margin-left: 8px" :loading="loading" @click="pauseScan" :disabled="taskStatus.status !== '扫描中'">暂停扫描</Button>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Button, Card, Progress, message } from 'ant-design-vue'

const taskStatus = ref({ status: 'no_task' })
const logs = ref([])
const logContent = ref(null)
const ws = ref(null)
const loading = ref(false)

// 计算进度百分比
const progressPercent = ref(0)
const progressFormat = (percent) => {
  return `${percent}%`
}

// 加载任务状态
const loadTaskStatus = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/task/status')
    const data = await response.json()
    taskStatus.value = data
    if (data.total_count > 0) {
      progressPercent.value = Math.round((data.scanned_count / data.total_count) * 100)
    }
  } catch (error) {
    console.error('加载任务状态失败:', error)
  }
}

// 开始全新扫描
const startNewScan = async () => {
  try {
    loading.value = true
    // 获取配置
    const configResponse = await fetch('http://localhost:8001/api/config/get')
    const config = await configResponse.json()
    if (config.status === 'no_config') {
      message.error('请先配置SVN信息')
      return
    }
    
    // 创建新任务
    const response = await fetch('http://localhost:8001/api/task/new', {
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
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描任务已创建')
      // 启动扫描
      await resumeScan(data.task_id)
    }
  } catch (error) {
    console.error('开始扫描失败:', error)
    message.error('开始扫描失败')
  } finally {
    loading.value = false
  }
}

// 继续扫描
const resumeScan = async (taskId) => {
  try {
    // 检查taskId是否是事件对象，如果是，则使用taskStatus.value.task_id
    let id = taskId
    if (typeof taskId === 'object' && taskId.type && taskId.target) {
      id = taskStatus.value.task_id
    }
    id = id || taskStatus.value.task_id
    const response = await fetch(`http://localhost:8001/api/task/resume?task_id=${id}`, {
      method: 'POST'
    })
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描任务已启动')
      loadTaskStatus()
    }
  } catch (error) {
    console.error('继续扫描失败:', error)
    message.error('继续扫描失败')
  }
}

// 暂停扫描
const pauseScan = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/task/pause', {
      method: 'POST'
    })
    const data = await response.json()
    if (data.status === 'success') {
      message.success('扫描已暂停')
      loadTaskStatus()
    }
  } catch (error) {
    console.error('暂停扫描失败:', error)
    message.error('暂停扫描失败')
  }
}

// 连接WebSocket
const connectWebSocket = () => {
  ws.value = new WebSocket('ws://localhost:8001/api/ws/progress')
  
  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    taskStatus.value = data
    if (data.total_count > 0) {
      progressPercent.value = Math.round((data.scanned_count / data.total_count) * 100)
    }
    // 只有在扫描中时才添加日志
    if (data.status === '扫描中') {
      // 添加日志
      logs.value.push(`${new Date().toLocaleString()} - 已扫描 ${data.scanned_count} 个文件`)
      // 保持日志滚动到底部
      nextTick(() => {
        if (logContent.value) {
          logContent.value.scrollTop = logContent.value.scrollHeight
        }
      })
    }
  }
  
  ws.value.onclose = () => {
    // 重连
    setTimeout(connectWebSocket, 3000)
  }
}

// 组件挂载时
onMounted(() => {
  loadTaskStatus()
  connectWebSocket()
})

// 组件卸载时
onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
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
  height: 300px;
  overflow: auto;
}

.log-content {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
}

.buttons {
  margin-top: 20px;
}
</style>
