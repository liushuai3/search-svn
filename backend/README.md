# SVN文件搜索系统 - 后端

## 项目介绍

SVN文件搜索系统后端是一个基于FastAPI框架的Web服务，负责处理SVN配置管理、文件扫描、文件搜索和文件下载等核心功能。

## 功能特点

- **SVN配置管理**：支持保存和获取SVN配置，测试SVN连接
- **文件扫描**：支持从SVN仓库扫描文件，支持断点续扫、暂停和继续功能
- **实时进度**：通过WebSocket实时推送扫描进度和日志
- **文件搜索**：支持全文搜索和分页查询
- **文件下载**：支持直接下载文件

## 技术栈

- Python 3.10+
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- SQLite 3.40.0 (使用FTS5进行全文搜索)
- WebSocket (实时通信)

## 目录结构

```
backend/
├── app/
│   ├── api/          # API路由定义
│   │   └── routes.py # 路由实现
│   ├── models/       # 数据库模型
│   │   └── database.py # 数据库配置和模型定义
│   └── services/     # 业务逻辑
│       └── svn_scanner.py # SVN扫描服务
├── main.py           # 应用入口
├── requirements.txt  # 依赖声明
└── db.sqlite3        # 数据库文件
```

## 核心模块

### API层
- **配置管理**：处理SVN配置的保存、获取和测试
- **任务管理**：处理扫描任务的创建、暂停和继续
- **WebSocket**：处理实时扫描进度和日志
- **文件管理**：处理文件搜索和下载

### 服务层
- **SVNScanner**：负责扫描SVN仓库，支持断点续扫和暂停功能

### 数据层
- **ScanTask**：扫描任务模型，存储任务状态和配置
- **SVNFile**：文件模型，存储文件信息
- **FTS5虚拟表**：用于全文搜索

## 安装步骤

1. **安装Python**
   - 下载并安装Python 3.10+：[Python官网](https://www.python.org/downloads/)

2. **安装SVN命令行客户端**
   - 下载并安装TortoiseSVN：[TortoiseSVN官网](https://tortoisesvn.net/downloads.html)
   - 确保SVN命令已添加到系统PATH环境变量

3. **安装项目依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 运行服务

### 开发模式
```bash
python main.py
# 服务默认运行在 http://0.0.0.0:8001
```

### 生产模式
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## API接口

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 保存配置 | POST | /api/config/save | 保存SVN配置 |
| 获取配置 | GET | /api/config/get | 获取SVN配置 |
| 测试连接 | GET | /api/config/test | 测试SVN连接 |
| 新建任务 | POST | /api/task/new | 创建新的扫描任务 |
| 继续任务 | POST | /api/task/resume | 继续扫描任务 |
| 暂停任务 | POST | /api/task/pause | 暂停扫描任务 |
| 获取任务状态 | GET | /api/task/status | 获取任务状态 |
| WebSocket | WebSocket | /api/ws/progress | 实时获取扫描进度 |
| 搜索文件 | GET | /api/file/search | 搜索文件 |
| 下载文件 | GET | /api/file/download | 下载文件 |

## 注意事项

- 确保SVN命令行客户端已安装并添加到系统PATH环境变量
- 首次扫描可能需要较长时间，具体时间取决于SVN仓库大小
- 扫描过程中可以暂停和继续，支持断点续扫
- 数据库文件默认存储为`db.sqlite3`，位于项目根目录

## 常见问题

### SVN命令未找到
- 症状：扫描任务失败，提示 "svn: command not found"
- 解决方案：安装SVN命令行客户端，并将其添加到系统PATH环境变量

### 端口被占用
- 症状：启动服务失败，提示 "Address already in use"
- 解决方案：修改端口配置，或关闭占用端口的进程

### 数据库连接失败
- 症状：启动服务失败，提示数据库连接错误
- 解决方案：确保SQLite数据库文件有写入权限
