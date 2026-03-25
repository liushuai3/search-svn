import subprocess
import os
from sqlalchemy.orm import Session
from app.models.database import ScanTask, SVNFile
import logging
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局连接管理器
manager = None

class SVNScanner:
    """SVN扫描服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.is_running = False
        self.current_task = None
    
    @staticmethod
    def set_manager(manager_instance):
        """设置全局连接管理器"""
        global manager
        manager = manager_instance
    
    def scan(self, task_id: int):
        """开始扫描任务"""
        try:
            self.is_running = True
            task = self.db.query(ScanTask).filter(ScanTask.id == task_id).first()
            if not task:
                logger.error(f"任务ID {task_id} 不存在")
                return
            
            # 设置当前任务
            self.current_task = task
            
            task.status = "扫描中"
            self.db.commit()
            # 广播状态更新
            self._broadcast_status(task)
            
            # 构建SVN命令，使用建议的参数配置
            base_cmd = ["svn", "--non-interactive", "--no-auth-cache", "--trust-server-cert", "--trust-server-cert-failures", "unknown-ca,cn-mismatch,expired,not-yet-valid,other"]
            
            # 检查是否有上次的扫描目录
            last_scan_dir = task.now_scan_dir
            logger.info(f"上次扫描目录: {last_scan_dir}")
            
            # 构建扫描命令
            if last_scan_dir:
                # 从上次的扫描目录开始扫描
                # 移除末尾的 '/'，确保路径正确
                if last_scan_dir.endswith('/'):
                    last_scan_dir = last_scan_dir[:-1]
                # 构建完整的URL
                scan_url = f"{task.root_svn_url}/{last_scan_dir}"
                # 使用列表传递参数，避免空格问题
                cmd = base_cmd + ["ls", "-R", "--depth", "infinity", scan_url, "--username", task.username, "--password", task.password]
                logger.info(f"从上次扫描目录开始执行SVN扫描命令: svn ls -R --depth infinity {scan_url}")
            else:
                # 从根目录开始扫描
                cmd = base_cmd + ["ls", "-R", "--depth", "infinity", task.root_svn_url, "--username", task.username, "--password", task.password]
                logger.info(f"从根目录开始执行SVN扫描命令: svn ls -R --depth infinity {task.root_svn_url}")
            
            # 执行命令并流式读取输出
            # 在Windows系统上，SVN命令的输出可能是GBK编码，需要特殊处理
            import sys
            if sys.platform == 'win32':
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='gbk',
                    errors='ignore'
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            
            file_batch = []
            scanned_count = 0
            has_files = False
            
            for line in process.stdout:
                if not self.is_running:
                    process.terminate()
                    # 等待进程终止
                    process.wait()
                    # 清空file_batch，避免将未处理的文件添加到数据库
                    file_batch = []
                    task.status = "已暂停"
                    self.db.commit()
                    logger.info("扫描已暂停")
                    return
                
                line = line.strip()
                if not line:
                    continue
                
                # 跳过目录（以/结尾）
                if line.endswith('/'):
                    # 构建完整的目录路径
                    if last_scan_dir:
                        current_dir = f"{last_scan_dir}/{line}"
                    else:
                        current_dir = line
                    # 更新当前扫描目录
                    task.now_scan_dir = current_dir
                    self.db.commit()
                    # 广播状态更新
                    self._broadcast_status(task)
                    continue
                
                # 只有当读取到文件时，才将has_files设置为True
                has_files = True
                
                # 解析文件信息
                if last_scan_dir:
                    # 如果是从上次的扫描目录开始，需要构建完整的路径
                    full_path = f"{last_scan_dir}/{line}"
                    file_name = os.path.basename(line)
                    file_path = os.path.dirname(full_path) if os.path.dirname(full_path) else ''
                    svn_url = f"{task.root_svn_url}/{full_path}"
                else:
                    # 从根目录开始
                    file_name = os.path.basename(line)
                    file_path = os.path.dirname(line) if os.path.dirname(line) else ''
                    svn_url = f"{task.root_svn_url}/{line}"
                
                # 添加到批处理
                file_batch.append(SVNFile(
                    task_id=task.id,
                    file_name=file_name,
                    file_path=file_path,
                    svn_url=svn_url
                ))
                scanned_count += 1
                
                # 达到批处理大小，执行入库
                if len(file_batch) >= task.batch_size:
                    self.db.bulk_save_objects(file_batch)
                    self.db.commit()
                    task.scanned_count += len(file_batch)
                    self.db.commit()
                    logger.info(f"已扫描 {task.scanned_count} 个文件")
                    # 广播状态更新
                    self._broadcast_status(task)
                    file_batch = []
            
            # 处理剩余文件
            if file_batch:
                self.db.bulk_save_objects(file_batch)
                self.db.commit()
                task.scanned_count += len(file_batch)
                self.db.commit()
                # 广播状态更新
                self._broadcast_status(task)
            
            # 检查进程是否正常结束
            process.wait()
            if process.returncode != 0:
                error_output = process.stderr.read()
                logger.error(f"SVN命令执行失败: {error_output}")
                task.status = "失败"
                self.db.commit()
                # 广播状态更新
                self._broadcast_status(task)
                return
            
            # 检查是否有文件被扫描
            if last_scan_dir:
                # 无论当前目录是否有文件，都尝试从父目录继续扫描
                # 这样可以确保所有目录都被扫描
                logger.info(f"当前目录 {last_scan_dir} 扫描完成，尝试从父目录继续扫描")
                parent_dir = os.path.dirname(last_scan_dir)
                if parent_dir:
                    # 更新当前扫描目录为父目录
                    task.now_scan_dir = parent_dir
                    self.db.commit()
                    # 重新开始扫描
                    self.scan(task_id)
                    return
            
            # 扫描完成
            task.status = "已完成"
            task.total_count = task.scanned_count
            self.db.commit()
            # 广播状态更新
            self._broadcast_status(task)
            logger.info(f"扫描完成，共扫描 {task.scanned_count} 个文件")
            
        except Exception as e:
            logger.error(f"扫描过程中发生错误: {str(e)}")
            if task:
                task.status = "失败"
                self.db.commit()
                # 广播状态更新
                self._broadcast_status(task)
        finally:
            self.is_running = False
    
    def pause(self):
        """暂停扫描"""
        self.is_running = False
        logger.info("暂停扫描")
        # 如果有当前任务，更新任务状态到数据库
        if self.current_task:
            try:
                self.current_task.status = "已暂停"
                self.db.commit()
                # 广播状态更新
                self._broadcast_status(self.current_task)
                logger.info("任务状态已更新为已暂停")
            except Exception as e:
                logger.error(f"更新任务状态失败: {str(e)}")
    
    def stop(self):
        """停止扫描"""
        self.is_running = False
        logger.info("停止扫描")
    
    def _broadcast_status(self, task):
        """广播任务状态更新"""
        # 移除异步广播，让WebSocket端点定期轮询任务状态
        pass
