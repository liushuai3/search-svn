from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# 创建SQLite数据库引擎
engine = create_engine('sqlite:///db.sqlite3', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScanTask(Base):
    """扫描任务表"""
    __tablename__ = "scan_task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    root_svn_url = Column(Text, nullable=False)
    username = Column(Text)
    password = Column(Text)
    status = Column(Text, nullable=False)  # 未开始/扫描中/暂停/完成/失败
    now_scan_dir = Column(Text)
    scanned_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    batch_size = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class SVNFile(Base):
    """SVN文件表"""
    __tablename__ = "svn_file"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("scan_task.id"))
    file_name = Column(Text)
    file_path = Column(Text)
    svn_url = Column(Text)
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)

# 创建表结构
Base.metadata.create_all(bind=engine)

# 创建FTS5全文检索表
with engine.connect() as conn:
    conn.execute(text('''
        CREATE VIRTUAL TABLE IF NOT EXISTS svn_file_fts USING fts5(
            file_name,
            file_path,
            svn_url,
            content=svn_file,
            content_rowid=id
        )
    '''))
    conn.execute(text('''
        CREATE TRIGGER IF NOT EXISTS svn_file_fts_insert AFTER INSERT ON svn_file BEGIN
            INSERT INTO svn_file_fts(rowid, file_name, file_path, svn_url) 
            VALUES (new.id, new.file_name, new.file_path, new.svn_url);
        END
    '''))
    conn.execute(text('''
        CREATE TRIGGER IF NOT EXISTS svn_file_fts_delete AFTER DELETE ON svn_file BEGIN
            DELETE FROM svn_file_fts WHERE rowid = old.id;
        END
    '''))
    conn.execute(text('''
        CREATE TRIGGER IF NOT EXISTS svn_file_fts_update AFTER UPDATE ON svn_file BEGIN
            UPDATE svn_file_fts SET 
                file_name = new.file_name,
                file_path = new.file_path,
                svn_url = new.svn_url
            WHERE rowid = new.id;
        END
    '''))
