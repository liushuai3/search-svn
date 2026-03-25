# SVN文件搜索系统

## 项目介绍

SVN文件搜索系统是一个专门用于在SVN仓库中快速查找和管理文件的工具。它支持从SVN仓库扫描文件，建立索引，并提供高效的全文搜索功能，帮助开发人员和项目管理人员快速定位所需文件。

## 功能特点

- **SVN配置管理**：支持配置SVN仓库地址、用户名、密码，并测试连接
- **文件扫描**：支持从SVN仓库扫描文件，支持断点续扫、暂停和继续功能
- **实时进度**：通过WebSocket实时显示扫描进度和日志
- **全文搜索**：使用SQLite FTS5进行高效的全文搜索
- **文件下载**：支持直接下载文件和复制SVN链接
- **空关键字查询**：支持空关键字查询所有文件
- **分页查询**：支持分页查询，提高性能

## 技术栈

### 后端
- Python 3.10+
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- SQLite 3.40.0 (使用FTS5进行全文搜索)
- WebSocket (实时通信)

### 前端
- Vue3 3.3.8
- Ant Design Vue 4.0.0
- Vite 5.0.0

## 目录结构

```
search-svn/
├── backend/               # 后端代码
│   ├── app/              # 应用代码
│   │   ├── api/          # API路由
│   │   ├── models/       # 数据库模型
│   │   └── services/     # 业务逻辑
│   ├── main.py           # 应用入口
│   ├── requirements.txt  # 依赖声明
│   └── db.sqlite3        # 数据库文件
├── frontend/              # 前端代码
│   ├── src/              # 源代码
│   │   ├── views/        # 页面组件
│   │   ├── App.vue       # 应用主组件
│   │   └── main.js       # 应用入口
│   ├── package.json      # 依赖声明
│   └── index.html        # HTML模板
├── 需求文档.md            # 需求文档
├── 设计文档.md            # 设计文档
├── 部署文档.md            # 部署文档
└── README.md             # 项目说明
```

## 安装步骤

### 1. 安装环境依赖

#### 后端依赖
- Python 3.10+：[Python官网下载](https://www.python.org/downloads/)
- SVN命令行客户端：[TortoiseSVN官网下载](https://tortoisesvn.net/downloads.html)

#### 前端依赖
- Node.js 18+：[Node.js官网下载](https://nodejs.org/en/download/)

### 2. 安装项目依赖

#### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

## 运行项目

### 1. 启动后端服务
```bash
cd backend
python main.py
# 服务默认运行在 http://0.0.0.0:8001
```

### 2. 启动前端服务
```bash
cd frontend
npm run dev
# 前端默认运行在 http://localhost:5173
```

## 使用说明

1. **配置SVN**：在"SVN配置"页面填写SVN仓库地址、用户名、密码，并测试连接
2. **扫描文件**：在"文件扫描"页面点击"开始扫描"按钮，开始扫描SVN仓库文件
3. **搜索文件**：在"文件搜索"页面输入关键字进行搜索，支持全文搜索
4. **下载文件**：在搜索结果中点击"下载"按钮下载文件，或点击"复制链接"复制SVN链接

## 注意事项

- 确保SVN命令行客户端已安装并添加到系统PATH环境变量
- 确保后端服务和前端服务都已启动
- 首次扫描可能需要较长时间，具体时间取决于SVN仓库大小
- 扫描过程中可以暂停和继续，支持断点续扫

## 常见问题

### 后端问题
- **SVN命令未找到**：安装SVN命令行客户端，并将其添加到系统PATH环境变量
- **端口被占用**：修改端口配置，或关闭占用端口的进程

### 前端问题
- **API请求失败**：确保后端服务已启动，且API地址配置正确
- **WebSocket连接失败**：确保后端WebSocket服务已启动，且WebSocket地址配置正确

## 文档

- [需求文档](需求文档.md)：详细描述系统的功能需求、技术要求和验收标准
- [设计文档](设计文档.md)：详细描述系统的架构设计、模块设计和数据库设计
- [部署文档](部署文档.md)：详细描述系统的部署步骤、环境要求和配置说明

## 许可证

本项目采用MIT许可证。
