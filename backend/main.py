from fastapi import FastAPI, BackgroundTasks, HTTPException

from indexer import FileIndexer
from config import settings

app = FastAPI(title="File Indexer API")

indexer = FileIndexer()

indexing_status = {
    "is_indexing": False,
    "current_file": "",
    "progress": 0,
    "total": 0,
    "last_result": None
}

def progress_callback(file_path: str, current: int, total: int):
    """Update indexing progress"""
    indexing_status["current_file"] = file_path
    indexing_status["progress"] = current
    indexing_status["total"] = total

def index_directory_task(directory: str):
    """Background task for indexing"""
    indexing_status["is_indexing"] = True
    indexing_status["progress"] = 0
    indexing_status["current_file"] = ""
    
    try:
        result = indexer.index_directory(directory)
        indexing_status["last_result"] = result
    except Exception as e:
        indexing_status["last_result"] = {"error": str(e)}
    finally:
        indexing_status["is_indexing"] = False