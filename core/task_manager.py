import threading
import queue
import uuid
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class ScanTask:
    id: str
    name: str
    target: str  # File or directory path
    status: TaskStatus
    progress: float  # 0.0 to 1.0
    files_processed: int
    total_files: int
    results: Dict[str, Any]
    error_message: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]
    thread: Optional[threading.Thread]
    cancel_flag: threading.Event
    
    def __init__(self, target: str, name: Optional[str] = None):
        self.id = str(uuid.uuid4())[:8]
        self.target = target
        self.name = name or f"Scan {Path(target).name}"
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.files_processed = 0
        self.total_files = 0
        self.results = {}
        self.error_message = None
        self.start_time = None
        self.end_time = None
        self.thread = None
        self.cancel_flag = threading.Event()
    
    def get_elapsed_time(self) -> float:
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'target': self.target,
            'status': self.status.value,
            'progress': self.progress,
            'files_processed': self.files_processed,
            'total_files': self.total_files,
            'elapsed_time': self.get_elapsed_time(),
            'abbreviations_found': len(self.results),
            'error': self.error_message
        }

class TaskManager:
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, ScanTask] = {}
        self.task_queue: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
        self._running = True
        self._worker_thread = None
    
    def start(self):
        if not self._worker_thread or not self._worker_thread.is_alive():
            self._running = True
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
    
    def stop(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
    
    def create_task(self, target: str, name: Optional[str] = None, 
                   scan_callback: Optional[Callable] = None) -> str:
        task = ScanTask(target, name)
        
        with self.lock:
            self.tasks[task.id] = task
        
        # Queue the task with its callback
        self.task_queue.put((task.id, scan_callback))
        
        return task.id
    
    def cancel_task(self, task_id: str) -> bool:
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                task.cancel_flag.set()
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScanTask]:
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScanTask]:
        with self.lock:
            return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[ScanTask]:
        with self.lock:
            return [t for t in self.tasks.values() 
                   if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]]
    
    def get_running_count(self) -> int:
        with self.lock:
            return sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
    
    def remove_task(self, task_id: str) -> bool:
        with self.lock:
            task = self.tasks.get(task_id)
            if task and task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                del self.tasks[task_id]
                return True
        return False
    
    def clear_completed(self):
        with self.lock:
            completed = [tid for tid, task in self.tasks.items() 
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR]]
            for tid in completed:
                del self.tasks[tid]
    
    def _worker_loop(self):
        while self._running:
            try:
                # Check if we can start a new task
                if self.get_running_count() >= self.max_concurrent:
                    time.sleep(0.1)
                    continue
                
                # Get next task from queue (non-blocking)
                try:
                    task_id, callback = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                with self.lock:
                    task = self.tasks.get(task_id)
                    if not task or task.status != TaskStatus.PENDING:
                        continue
                    
                    # Start the task
                    task.status = TaskStatus.RUNNING
                    task.start_time = time.time()
                
                # Run the scan in a separate thread
                if callback:
                    thread = threading.Thread(
                        target=self._run_task,
                        args=(task_id, callback),
                        daemon=True
                    )
                    task.thread = thread
                    thread.start()
                
            except Exception as e:
                print(f"Worker loop error: {e}")
                time.sleep(0.5)
    
    def _run_task(self, task_id: str, callback: Callable):
        task = self.get_task(task_id)
        if not task:
            return
        
        try:
            # Call the scan callback with the task
            if callback:
                callback(task)
            
            # Mark as completed if not cancelled
            with self.lock:
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.COMPLETED
                    task.end_time = time.time()
        
        except Exception as e:
            with self.lock:
                task.status = TaskStatus.ERROR
                task.error_message = str(e)
                task.end_time = time.time()
    
    def update_task_progress(self, task_id: str, files_processed: int, 
                            total_files: int, results: Optional[Dict] = None):
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                task.files_processed = files_processed
                task.total_files = total_files
                task.progress = files_processed / total_files if total_files > 0 else 0.0
                if results:
                    task.results = results
