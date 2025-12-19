from fastapi import FastAPI, BackgroundTasks, HTTPException

import subprocess
import platform

from indexer import Indexer
from config import settings

app = FastAPI(title="File Indexer API")

indexer = Indexer()

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

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "AI File Search API",
        "version": "1.0.0",
        "status": "running"
}

@app.post("/api/index")
async def start_indexing(directory: str, background_tasks: BackgroundTasks):
    """Start indexing files in the specified directory"""
    if indexing_status["is_indexing"]:
        raise HTTPException(status_code=400, detail="Indexing already in progress")
    
    background_tasks.add_task(index_directory_task, directory)
    return {"message": f"Started indexing directory: {directory}"}

@app.get("/api/index/status")
async def get_indexing_status():
    """Get indexing status"""
    return indexing_status

@app.post("/api/search")
async def search_files(query: str, n_results: int = settings.SEARCH_RESULT_COUNT):
    """Search indexed files for the given query"""
    results = indexer.search(query, n_results)
    return {"query": query, "results": results, "count": len(results)}

@app.post("/api/open-file")
async def open_file(file_path: str):
    """Open a file in the default application"""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        elif system == "Windows":
            subprocess.run(["start", file_path], shell=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", file_path])
        
        return {"message": "File opened", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
