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
            logger.info(f"上次扫描目录: {last_scan_dir}, 已扫描文件数: {task.scanned_count}")
            
            # 始终从根目录开始扫描
            # 如果有上次扫描目录，会在处理时跳过该目录之前的所有内容
            cmd = base_cmd + ["ls", "-R", "--depth", "infinity", task.root_svn_url, "--username", task.username, "--password", task.password]
            logger.info(f"执行SVN扫描命令: svn ls -R --depth infinity {task.root_svn_url}")
            
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
            
            # 如果继续扫描，需要跳过 last_scan_dir 之前的所有内容
            should_process = not (last_scan_dir and task.scanned_count > 0)
            logger.info(f"继续扫描模式: {not should_process}, last_scan_dir: {last_scan_dir}")
            
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
                    current_dir = line
                    
                    # 检查是否应该开始处理
                    if not should_process and last_scan_dir:
                        # 如果当前目录是 last_scan_dir 或其子目录，开始处理
                        if current_dir == last_scan_dir or current_dir.startswith(last_scan_dir + '/'):
                            logger.info(f"找到上次扫描目录，开始处理: {current_dir}")
                            should_process = True
                        else:
                            # 跳过该目录
                            continue
                    
                    # 更新当前扫描目录
                    task.now_scan_dir = current_dir
                    self.db.commit()
                    # 广播状态更新
                    self._broadcast_status(task)
                    continue
                
                # 如果还没有到达上次扫描的目录，跳过
                if not should_process:
                    continue
                
                # 只有当读取到文件时，才将has_files设置为True
                has_files = True
                
                # 解析文件信息
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
            
            logger.info(f"SVN命令执行完成，本次扫描到 {scanned_count} 个文件，has_files={has_files}")
            
            # 检查是否有文件被扫描
            # 注意：不再递归到父目录，因为SVN ls -R 已经递归列出了所有子目录的内容
            # 如果扫描完成，说明当前目录及其子目录都已经扫描完毕
            if last_scan_dir:
                logger.info(f"当前目录 {last_scan_dir} 及其子目录扫描完成")
            
            # 检查是否真的没有扫描到任何文件
            if not has_files and task.scanned_count == 0:
                logger.warning("本次扫描未找到任何文件，可能是SVN仓库为空或权限问题")
            
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
