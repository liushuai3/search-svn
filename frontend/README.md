# SVN文件搜索系统 - 前端

## 项目介绍

SVN文件搜索系统前端是一个基于Vue3框架的单页应用，负责提供用户界面，与后端API交互，实现SVN配置管理、文件扫描和文件搜索等功能。

## 功能特点

- **SVN配置**：提供直观的表单界面，用于配置SVN仓库地址、用户名、密码，并测试连接
- **文件扫描**：实时显示扫描进度和日志，支持暂停和继续扫描任务
- **文件搜索**：提供搜索输入框和结果表格，支持全文搜索和分页查询
- **文件操作**：支持下载文件和复制SVN链接
- **响应式设计**：适配不同屏幕尺寸

## 技术栈

- Vue3 3.3.8
- Ant Design Vue 4.0.0
- Vite 5.0.0
- JavaScript/TypeScript

## 目录结构

```
frontend/
├── src/
│   ├── views/           # 页面组件
│   │   ├── SVNConfig.vue    # SVN配置页面
│   │   ├── FileScan.vue     # 文件扫描页面
│   │   └── FileSearch.vue   # 文件搜索页面
│   ├── App.vue          # 应用主组件
│   ├── main.js          # 应用入口
│   └── style.css        # 全局样式
├── public/              # 静态资源
│   ├── favicon.svg      # 网站图标
│   └── icons.svg        # 图标资源
├── package.json         # 依赖声明
├── index.html           # HTML模板
└── vite.config.ts       # Vite配置
```

## 核心页面

### SVN配置页面 (SVNConfig.vue)
- 提供表单用于输入SVN仓库地址、用户名、密码
- 提供测试连接按钮，验证SVN配置是否正确
- 提供批处理大小配置

### 文件扫描页面 (FileScan.vue)
- 显示扫描任务状态和进度
- 提供开始、暂停、继续按钮
- 实时显示扫描日志
- 支持断点续扫

### 文件搜索页面 (FileSearch.vue)
- 提供搜索输入框，支持全文搜索
- 显示搜索结果表格，包含文件名、路径和操作按钮
- 支持下载文件和复制SVN链接
- 支持分页查询

## 安装步骤

1. **安装Node.js**
   - 下载并安装Node.js 18+：[Node.js官网](https://nodejs.org/en/download/)

2. **安装项目依赖**
   ```bash
   npm install
   ```

## 运行项目

### 开发模式
```bash
npm run dev
# 前端默认运行在 http://localhost:5173
```

### 生产构建
```bash
npm run build
# 构建产物将生成在 dist 目录
```

### 生产部署
```bash
# 安装静态文件服务器
npm install -g serve

# 启动静态文件服务器
serve -s dist
```

## 配置说明

### API地址配置
- 默认API地址：`http://localhost:8001/api`
- 修改方法：修改前端代码中的API请求地址

### WebSocket地址配置
- 默认WebSocket地址：`ws://localhost:8001/api/ws/progress`
- 修改方法：修改前端代码中的WebSocket连接地址

## 注意事项

- 确保后端服务已启动，且API地址配置正确
- 首次扫描可能需要较长时间，具体时间取决于SVN仓库大小
- 扫描过程中可以暂停和继续，支持断点续扫
- 搜索功能支持空关键字查询，可查询所有文件

## 常见问题

### API请求失败
- 症状：前端无法连接到后端API
- 解决方案：确保后端服务已启动，且API地址配置正确

### WebSocket连接失败
- 症状：扫描进度无法实时更新
- 解决方案：确保后端WebSocket服务已启动，且WebSocket地址配置正确

### 构建失败
- 症状：`npm run build` 命令失败
- 解决方案：检查依赖是否安装正确，或尝试删除 `node_modules` 目录后重新安装

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
