<template>
  <div class="svn-config">
    <Card title="SVN 配置">
      <Form :model="formState" @finish="handleSubmit">
        <Form.Item label="SVN 根地址" name="rootSvnUrl" :rules="[{ required: true, message: '请输入SVN根地址' }]">
          <Input v-model:value="formState.rootSvnUrl" placeholder="例如：https://svn.example.com/repos" />
        </Form.Item>
        <Form.Item label="用户名" name="username" :rules="[{ required: true, message: '请输入用户名' }]">
          <Input v-model:value="formState.username" />
        </Form.Item>
        <Form.Item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
          <Input.Password v-model:value="formState.password" />
        </Form.Item>
        <Form.Item label="扫描批处理数" name="batchSize" :rules="[{ required: true, message: '请输入扫描批处理数' }]">
          <InputNumber v-model:value="formState.batchSize" min="100" max="1000" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" html-type="submit">保存配置</Button>
          <Button style="margin-left: 8px" :loading="loading" @click="testConnection">测试连通性</Button>
          <Button style="margin-left: 8px" @click="resetConfig">重置配置</Button>
        </Form.Item>
      </Form>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Button, Card, Form, Input, InputNumber, message } from 'ant-design-vue'

const form = ref(null);
const formState = ref({
  rootSvnUrl: '',
  username: '',
  password: '',
  batchSize: 500
})

const loading = ref(false);

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/config/get')
    console.log('加载配置响应:', response)
    const data = await response.json()
    console.log('加载配置数据:', data)
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
    message.error('加载配置失败: ' + error.message)
  }
}

// 保存配置
const handleSubmit = async (values) => {
  try {
    console.log('保存配置参数:', values)
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
      })
    })
    console.log('保存配置响应:', response)
    const data = await response.json()
    console.log('保存配置数据:', data)
    if (data.status === 'success') {
      message.success('配置保存成功')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败: ' + error.message)
  }
}

// 测试连通性
const testConnection = async () => {
  try {
    loading.value = true
    console.log('测试连通性参数:', formState.value)
    const response = await fetch(`http://localhost:8001/api/config/test?root_svn_url=${encodeURIComponent(formState.value.rootSvnUrl)}&username=${encodeURIComponent(formState.value.username)}&password=${encodeURIComponent(formState.value.password)}`)
    console.log('测试连通性响应:', response)
    const data = await response.json()
    console.log('测试连通性数据:', data)
    if (data.status === 'success') {
      message.success('连接成功')
    } else {
      message.error(`连接失败: ${data.message}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    message.error('测试连接失败: ' + error.message)
  } finally {
    loading.value = false
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
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.svn-config {
  padding: 20px;
}
</style>
