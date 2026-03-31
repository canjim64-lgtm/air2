"""
Scheduler Module
Task scheduling and cron-like functionality
"""

import time
import threading
from typing import Callable, Dict


class Task:
    """Scheduled task"""
    
    def __init__(self, name: str, func: Callable, interval: int):
        self.name = name
        self.func = func
        self.interval = interval
        self.last_run = 0


class Scheduler:
    """Task scheduler"""
    
    def __init__(self):
        self.tasks = []
        self.running = False
    
    def add_task(self, name: str, func: Callable, interval: int):
        """Add task"""
        self.tasks.append(Task(name, func, interval))
    
    def start(self):
        """Start scheduler"""
        self.running = True
        while self.running:
            for task in self.tasks:
                if time.time() - task.last_run >= task.interval:
                    task.func()
                    task.last_run = time.time()
            time.sleep(1)
    
    def stop(self):
        """Stop scheduler"""
        self.running = False


# Example
if __name__ == "__main__":
    sched = Scheduler()
    sched.add_task("test", lambda: print("Running"), 5)
    print("Scheduler ready")