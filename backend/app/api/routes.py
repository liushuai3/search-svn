from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.database import SessionLocal, ScanTask, SVNFile
from app.services.svn_scanner import SVNScanner
import asyncio
import json

router = APIRouter()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 全局扫描器实例
scanner_instance = None

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# 配置相关接口
@router.post("/config/save")
def save_config(root_svn_url: str = Form(...), username: str = Form(...), password: str = Form(...), batch_size: int = Form(500), db: Session = Depends(get_db)):
    """保存SVN配置"""
    # 这里可以添加加密逻辑
    config = {
        "root_svn_url": root_svn_url,
        "username": username,
        "password": password,
        "batch_size": batch_size
    }
    # 保存到数据库，创建一个新的任务记录
    new_task = ScanTask(
        root_svn_url=root_svn_url,
        username=username,
        password=password,
        status="未开始",
        batch_size=batch_size
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"status": "success", "config": config, "task_id": new_task.id}

@router.get("/config/get")
def get_config(db: Session = Depends(get_db)):
    """获取配置"""
    # 从数据库获取最新的配置
    latest_task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
    if latest_task:
        return {
            "root_svn_url": latest_task.root_svn_url,
            "username": latest_task.username,
            "password": latest_task.password,
            "batch_size": latest_task.batch_size
        }
    return {"status": "no_config"}

@router.get("/config/test")
def test_connection(root_svn_url: str, username: str, password: str):
    """测试SVN连通性"""
    import subprocess
    try:
        # 彻底清理URL中的反引号和空格
        root_svn_url = root_svn_url.strip('`').strip()
        # 构建SVN命令，使用建议的参数配置
        base_cmd = ["svn", "--non-interactive", "--no-auth-cache", "--trust-server-cert", "--trust-server-cert-failures", "unknown-ca,cn-mismatch,expired,not-yet-valid,other"]
        cmd = base_cmd + ["info", root_svn_url, "--username", username, "--password", password]
        # 完全移除超时限制
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=None)
        if result.returncode == 0:
            return {"status": "success", "message": "连接成功"}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 扫描任务接口
@router.post("/task/new")
def create_new_task(root_svn_url: str = Form(...), username: str = Form(...), password: str = Form(...), batch_size: int = Form(500), db: Session = Depends(get_db)):
    """新建全新扫描任务"""
    # 清空旧数据（先删除子表，再删除父表）
    try:
        # 使用原生 SQL 删除，避免外键约束问题
        from sqlalchemy import text
        db.execute(text('DELETE FROM svn_file'))
        db.execute(text('DELETE FROM scan_task'))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"清空数据失败: {e}")
        # 如果清空失败，继续创建新任务
    
    # 创建新任务
    new_task = ScanTask(
        root_svn_url=root_svn_url,
        username=username,
        password=password,
        status="未开始",
        batch_size=batch_size
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {"status": "success", "task_id": new_task.id}

@router.post("/task/resume")
async def resume_task(task_id: int, db: Session = Depends(get_db)):
    """断点继续扫描"""
    global scanner_instance
    task = db.query(ScanTask).filter(ScanTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status == "扫描中":
        raise HTTPException(status_code=400, detail="任务已经在扫描中")
    
    # 在一个单独的线程中运行扫描任务
    def run_scan():
        # 在线程中创建新的数据库连接
        thread_db = SessionLocal()
        global scanner_instance
        try:
            # 设置全局manager实例
            from app.services.svn_scanner import SVNScanner
            SVNScanner.set_manager(manager)
            
            scanner_instance = SVNScanner(thread_db)
            scanner_instance.scan(task_id)
        finally:
            thread_db.close()
    
    import threading
    threading.Thread(target=run_scan, daemon=True).start()
    
    return {"status": "success", "message": "扫描任务已启动"}

@router.post("/task/pause")
def pause_task(db: Session = Depends(get_db)):
    """暂停扫描"""
    global scanner_instance
    if scanner_instance:
        scanner_instance.pause()
    
    # 直接更新数据库中的任务状态
    latest_task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
    if latest_task and latest_task.status == "扫描中":
        latest_task.status = "已暂停"
        db.commit()
    
    return {"status": "success", "message": "扫描已暂停"}

@router.get("/task/status")
def get_task_status(db: Session = Depends(get_db)):
    """获取任务状态"""
    latest_task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
    if not latest_task:
        return {"status": "no_task"}
    
    return {
        "task_id": latest_task.id,
        "status": latest_task.status,
        "scanned_count": latest_task.scanned_count,
        "total_count": latest_task.total_count,
        "now_scan_dir": latest_task.now_scan_dir
    }

# WebSocket接口
@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 定期发送任务状态
            db = SessionLocal()
            try:
                # 尝试获取任务状态，处理数据库锁定的情况
                try:
                    latest_task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
                    if latest_task:
                        await websocket.send_json({
                            "task_id": latest_task.id,
                            "status": latest_task.status,
                            "scanned_count": latest_task.scanned_count,
                            "total_count": latest_task.total_count,
                            "now_scan_dir": latest_task.now_scan_dir
                        })
                except Exception as e:
                    # 忽略数据库锁定等错误，继续运行
                    pass
            finally:
                db.close()  # 确保每次都关闭数据库连接
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 搜索接口
@router.get("/file/search")
def search_files(kw: str = "", page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    """全文搜索文件"""
    offset = (page - 1) * page_size
    
    if kw:
        # 使用LIKE进行模糊搜索，支持中文和特殊字符
        # 在关键字两边添加%号，实现模糊搜索
        fuzzy_kw = f"%{kw}%"
        # 使用LIKE进行模糊搜索
        results = db.execute(text('''
            SELECT id, file_name, file_path, svn_url 
            FROM svn_file 
            WHERE file_name LIKE :kw OR file_path LIKE :kw
            LIMIT :page_size OFFSET :offset
        '''), {"kw": fuzzy_kw, "page_size": page_size, "offset": offset}).fetchall()
        
        # 获取总数
        total = db.execute(text('''
            SELECT COUNT(*)
            FROM svn_file 
            WHERE file_name LIKE :kw OR file_path LIKE :kw
        '''), {"kw": fuzzy_kw}).scalar()
    else:
        # 不输入关键字时，查询所有文件
        results = db.execute(text('''
            SELECT id, file_name, file_path, svn_url 
            FROM svn_file 
            LIMIT :page_size OFFSET :offset
        '''), {"page_size": page_size, "offset": offset}).fetchall()
        
        # 获取总数
        total = db.execute(text('''
            SELECT COUNT(*)
            FROM svn_file 
        ''')).scalar()
    
    files = []
    for result in results:
        files.append({
            "id": result[0],
            "file_name": result[1],
            "file_path": result[2],
            "svn_url": result[3]
        })
    
    return {
        "status": "success",
        "total": total,
        "page": page,
        "page_size": page_size,
        "files": files
    }

# 下载接口
@router.get("/file/download")
def download_file(file_url: str, file_name: str, db: Session = Depends(get_db)):
    """下载文件"""
    import os
    import subprocess
    import tempfile
    from fastapi.responses import StreamingResponse
    
    # 从数据库获取最新的SVN配置
    latest_task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
    if not latest_task:
        raise HTTPException(status_code=400, detail="SVN配置不存在")
    
    svn_username = latest_task.username
    svn_password = latest_task.password
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 使用简单的文件名，避免空格和特殊字符问题
        simple_file_name = "download.tmp"
        file_path = os.path.join(temp_dir, simple_file_name)
        
        # 构建SVN命令
        cmd = ["svn", "export", "--force", "--non-interactive"]
        if svn_username:
            cmd.extend(["--username", svn_username])
        if svn_password:
            cmd.extend(["--password", svn_password])
        # 添加SSL证书信任参数
        cmd.extend(["--trust-server-cert", "--trust-server-cert-failures", "unknown-ca,cn-mismatch,expired,not-yet-valid,other"])
        
        # 构建文件路径，确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        cmd.extend([file_url, file_path])
        
        # 执行命令
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"SVN export command executed successfully: {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"SVN export failed: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"下载失败: {e.stderr}")
        
        # 检查文件是否存在
        print(f"Checking if file exists: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path):
            print(f"File size: {os.path.getsize(file_path)}")
            
            # 读取文件内容到内存
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # 编码文件名，确保中文字符能够正确处理
            import urllib.parse
            encoded_file_name = urllib.parse.quote(file_name)
            
            # 返回StreamingResponse
            return StreamingResponse(
                iter([file_content]),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"
                }
            )
        else:
            # 检查临时目录中的文件
            print(f"Files in temp directory: {os.listdir(temp_dir)}")
            raise HTTPException(status_code=500, detail="文件下载失败")
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
