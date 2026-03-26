<template>
  <div class="svn-config">
    <Card title="SVN 配置">
      <!-- 网络状态提示 -->
      <Alert
        v-if="networkStatus === 'offline'"
        message="网络连接已断开"
        description="请检查网络连接后重试"
        type="warning"
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
      
      <!-- 成功提示 -->
      <Alert
        v-if="successMessage"
        :message="successMessage"
        type="success"
        show-icon
        closable
        @close="successMessage = ''"
        style="margin-bottom: 16px"
      />
      
      <Form 
        ref="formRef"
        :model="formState" 
        @finish="handleSubmit"
        :validate-messages="validateMessages"
        layout="vertical"
      >
        <Form.Item 
          label="SVN 根地址" 
          name="rootSvnUrl" 
          :rules="[{ required: true, message: '请输入SVN根地址' }]"
          extra="例如：https://svn.example.com/repos"
        >
          <Input 
            v-model:value="formState.rootSvnUrl" 
            placeholder="请输入SVN根地址"
            :disabled="isSubmitting"
          />
        </Form.Item>
        <Form.Item 
          label="用户名" 
          name="username" 
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <Input 
            v-model:value="formState.username" 
            placeholder="请输入用户名"
            :disabled="isSubmitting"
          />
        </Form.Item>
        <Form.Item 
          label="密码" 
          name="password" 
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <Input.Password 
            v-model:value="formState.password" 
            placeholder="请输入密码"
            :disabled="isSubmitting"
          />
        </Form.Item>
        <Form.Item 
          label="扫描批处理数" 
          name="batchSize" 
          :rules="[
            { required: true, message: '请输入扫描批处理数' },
            { type: 'number', min: 100, max: 1000, message: '批处理数必须在 100-1000 之间' }
          ]"
          extra="建议值：500（数值越大扫描越快，但占用资源越多）"
        >
          <InputNumber 
            v-model:value="formState.batchSize" 
            :min="100" 
            :max="1000"
            :step="100"
            style="width: 100%"
            :disabled="isSubmitting"
          />
        </Form.Item>
        <Form.Item>
          <Button 
            type="primary" 
            html-type="submit" 
            :loading="isSubmitting"
            :disabled="networkStatus === 'offline'"
          >
            保存配置
          </Button>
          <Button 
            style="margin-left: 8px" 
            :loading="isTesting" 
            @click="testConnection"
            :disabled="networkStatus === 'offline' || !isFormValid"
          >
            测试连通性
          </Button>
          <Button 
            style="margin-left: 8px" 
            @click="resetConfig"
            :disabled="isSubmitting"
          >
            重置配置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Button, Card, Form, Input, InputNumber, message, Alert } from 'ant-design-vue'

const formRef = ref(null)
const formState = ref({
  rootSvnUrl: '',
  username: '',
  password: '',
  batchSize: 100
})

const isSubmitting = ref(false)
const isTesting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const networkStatus = ref('online')

// 表单验证提示信息
const validateMessages = {
  required: '${label}不能为空',
  types: {
    number: '${label}必须是数字'
  },
  number: {
    range: '${label}必须在 ${min} 到 ${max} 之间'
  }
}

// 检查表单是否有效（用于控制测试按钮）
const isFormValid = computed(() => {
  return formState.value.rootSvnUrl && 
         formState.value.username && 
         formState.value.password
})

// 加载配置
const loadConfig = async () => {
  try {
    errorMessage.value = ''
    successMessage.value = ''
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    
    const response = await fetch('http://localhost:8001/api/config/get', {
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status !== 'no_config') {
      formState.value = {
        rootSvnUrl: data.root_svn_url,
        username: data.username,
        password: '', // 不直接显示密码
        batchSize: data.batch_size
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    if (error.name === 'AbortError') {
      errorMessage.value = '加载配置超时，请稍后重试'
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage.value = '无法连接到服务器，请检查后端服务是否运行'
    } else {
      errorMessage.value = '加载配置失败: ' + error.message
    }
  }
}

// 保存配置
const handleSubmit = async (values) => {
  try {
    isSubmitting.value = true
    errorMessage.value = ''
    successMessage.value = ''
    
    if (networkStatus.value === 'offline') {
      errorMessage.value = '网络已断开，无法保存配置'
      return
    }
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch('http://localhost:8001/api/config/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        root_svn_url: values.rootSvnUrl,
        username: values.username,
        password: values.password,
        batch_size: values.batchSize
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      successMessage.value = '配置保存成功'
    } else {
      throw new Error(data.message || '保存失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    if (error.name === 'AbortError') {
      errorMessage.value = '保存配置超时，请稍后重试'
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage.value = '无法连接到服务器，请检查后端服务是否运行'
    } else {
      errorMessage.value = '保存配置失败: ' + error.message
    }
    message.error(errorMessage.value)
  } finally {
    isSubmitting.value = false
  }
}

// 测试连通性
const testConnection = async () => {
  try {
    isTesting.value = true
    errorMessage.value = ''
    successMessage.value = ''
    
    if (networkStatus.value === 'offline') {
      errorMessage.value = '网络已断开，无法测试连通性'
      return
    }
    
    // 先验证表单
    const values = await formRef.value.validateFields()
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch(
      `http://localhost:8001/api/config/test?root_svn_url=${encodeURIComponent(values.rootSvnUrl)}&username=${encodeURIComponent(values.username)}&password=${encodeURIComponent(values.password)}`,
      { signal: controller.signal }
    )
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success') {
      successMessage.value = 'SVN 连接测试成功'
    } else {
      throw new Error(data.message || '连接失败')
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    if (error.name === 'AbortError') {
      errorMessage.value = '连接测试超时，请稍后重试'
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage.value = '无法连接到服务器，请检查后端服务是否运行'
    } else {
      errorMessage.value = `连接失败: ${error.message}`
    }
    message.error(errorMessage.value)
  } finally {
    isTesting.value = false
  }
}

// 重置配置
const resetConfig = () => {
  formState.value = {
    rootSvnUrl: '',
    username: '',
    password: '',
    batchSize: 500
  }
  errorMessage.value = ''
  successMessage.value = ''
  formRef.value?.clearValidate()
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

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  networkStatus.value = navigator.onLine ? 'online' : 'offline'
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
.svn-config {
  padding: 20px;
}
</style>
