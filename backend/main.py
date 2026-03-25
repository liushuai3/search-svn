from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.models.database import SessionLocal, ScanTask

app = FastAPI(title="SVN File Search API", description="SVN文件搜索系统API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")

# 启动时检查异常任务
@app.on_event("startup")
async def startup_event():
    """服务启动时检查异常任务"""
    db = SessionLocal()
    try:
        # 查找状态为"扫描中"的任务，可能是异常中断的
        scanning_tasks = db.query(ScanTask).filter(ScanTask.status == "扫描中").all()
        for task in scanning_tasks:
            # 将异常中断的任务标记为"已暂停"
            task.status = "已暂停"
            db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    """根路径"""
    return {"message": "SVN File Search API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
