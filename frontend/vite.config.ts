import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')
  
  // 优先级：process.env > .env 文件 > 默认值
  const frontendPort = parseInt(
    process.env.FRONTEND_PORT || 
    env.FRONTEND_PORT || 
    '5173'
  )
  
  return {
    plugins: [vue()],
    server: {
      port: frontendPort,
      host: true
    }
  }
})
