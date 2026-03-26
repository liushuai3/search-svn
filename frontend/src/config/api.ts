// API 配置
// 支持通过环境变量配置，优先级：import.meta.env > process.env > 默认值
// 在 .env 文件中设置 VITE_BACKEND_PORT=8001 即可修改端口

const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || 8001
const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST || 'localhost'

export const API_BASE_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`
export const WS_BASE_URL = `ws://${BACKEND_HOST}:${BACKEND_PORT}`

// API 端点
export const API_ENDPOINTS = {
  // 配置相关
  configGet: `${API_BASE_URL}/api/config/get`,
  configSave: `${API_BASE_URL}/api/config/save`,
  configTest: `${API_BASE_URL}/api/config/test`,
  
  // 任务相关
  taskStatus: `${API_BASE_URL}/api/task/status`,
  taskNew: `${API_BASE_URL}/api/task/new`,
  taskResume: `${API_BASE_URL}/api/task/resume`,
  taskPause: `${API_BASE_URL}/api/task/pause`,
  
  // 文件相关
  fileSearch: `${API_BASE_URL}/api/file/search`,
  fileDownload: `${API_BASE_URL}/api/file/download`,
  
  // WebSocket
  wsProgress: `${WS_BASE_URL}/api/ws/progress`,
}
