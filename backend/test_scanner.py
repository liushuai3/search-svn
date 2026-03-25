from app.models.database import SessionLocal, ScanTask
from app.services.svn_scanner import SVNScanner

# 创建数据库会话
db = SessionLocal()

# 检查是否有任务，如果没有，创建一个测试任务
task = db.query(ScanTask).order_by(ScanTask.id.desc()).first()
if not task:
    # 创建一个测试任务
    task = ScanTask(
        root_svn_url="https://172.30.66.136/svn/repo",
        username="liushuai3",
        password="liushuai3",
        status="未开始",
        batch_size=500
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    print(f"Created test task with ID: {task.id}")
else:
    print(f"Found existing task with ID: {task.id}")

# 创建SVNScanner实例并执行扫描
scanner = SVNScanner(db)
print(f"Starting scan for task ID: {task.id}")
scanner.scan(task.id)
print("Scan completed")

# 关闭数据库会话
db.close()
