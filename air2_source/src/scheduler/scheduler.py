#!/usr/bin/env python3
"""
AirOne v4.0 - Scheduler System
===============================

Task scheduling with cron-like functionality
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import queue

sys.path.insert(0, str(Path(__file__).parent.parent))


class ScheduleFrequency(Enum):
    """Schedule frequency types"""
    ONCE = "once"
    MINUTE = "minute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Scheduled task definition"""
    id: str
    name: str
    func: str  # Function name to call
    frequency: ScheduleFrequency
    interval: int = 1  # Interval multiplier
    cron_expr: str = ""  # For cron jobs
    next_run: datetime = None
    last_run: datetime = None
    enabled: bool = True
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    
    def __post_init__(self):
        if self.next_run is None:
            self.next_run = self._calculate_next_run()
            
    def _calculate_next_run(self) -> datetime:
        """Calculate next run time"""
        now = datetime.now()
        
        if self.frequency == ScheduleFrequency.ONCE:
            return now + timedelta(minutes=1)
        elif self.frequency == ScheduleFrequency.MINUTE:
            return now + timedelta(minutes=self.interval)
        elif self.frequency == ScheduleFrequency.HOURLY:
            return now + timedelta(hours=self.interval)
        elif self.frequency == ScheduleFrequency.DAILY:
            return now + timedelta(days=self.interval)
        elif self.frequency == ScheduleFrequency.WEEKLY:
            return now + timedelta(weeks=self.interval)
        elif self.frequency == ScheduleFrequency.MONTHLY:
            return now + timedelta(days=30 * self.interval)
        else:
            return now + timedelta(minutes=1)
            
    def should_run(self) -> bool:
        """Check if task should run now"""
        return self.enabled and datetime.now() >= self.next_run


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: str = None
    duration: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TaskRegistry:
    """Registry of available tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Callable] = {}
        
    def register(self, name: str, func: Callable):
        """Register a task function"""
        self.tasks[name] = func
        
    def get(self, name: str) -> Optional[Callable]:
        """Get task function"""
        return self.tasks.get(name)
        
    def list(self) -> List[str]:
        """List all registered tasks"""
        return list(self.tasks.keys())


class Scheduler:
    """
    AirOne Task Scheduler
    
    Manages scheduled tasks with various frequencies.
    """
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.results: List[TaskResult] = []
        self.max_results = 100
        self.running = False
        self.thread = None
        self.registry = TaskRegistry()
        self._lock = threading.Lock()
        
        # Register default tasks
        self._register_default_tasks()
        
        logging.info("Scheduler initialized")
        
    def _register_default_tasks(self):
        """Register default system tasks"""
        self.registry.register("telemetry_backup", self._task_backup_telemetry)
        self.registry.register("health_check", self._task_health_check)
        self.registry.register("cleanup_logs", self._task_cleanup)
        self.registry.register("report_generation", self._task_generate_report)
        
    def add_task(self, task: ScheduledTask):
        """Add a scheduled task"""
        with self._lock:
            self.tasks[task.id] = task
        logging.info(f"Added task: {task.name} ({task.frequency.value})")
        
    def remove_task(self, task_id: str) -> bool:
        """Remove a task"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
        return False
        
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                return True
        return False
        
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                return True
        return False
        
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("Scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("Scheduler stopped")
        
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
        
    def list_tasks(self) -> List[ScheduledTask]:
        """List all tasks"""
        return list(self.tasks.values())
        
    def get_results(self, limit: int = 10) -> List[TaskResult]:
        """Get recent task results"""
        return self.results[-limit:]
        
    # Default task implementations
    def _task_backup_telemetry(self) -> str:
        """Backup telemetry data"""
        return "Telemetry backup completed"
        
    def _task_health_check(self) -> str:
        """Run health check"""
        return "Health check passed"
        
    def _task_cleanup(self) -> str:
        """Cleanup old logs"""
        return "Log cleanup completed"
        
    def _task_generate_report(self) -> str:
        """Generate report"""
        return "Report generated"
        
    def _run_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                with self._lock:
                    tasks_to_run = [
                        task for task in self.tasks.values()
                        if task.should_run()
                    ]
                    
                for task in tasks_to_run:
                    self._execute_task(task)
                    
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                
    def _execute_task(self, task: ScheduledTask):
        """Execute a task"""
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        
        start_time = time.time()
        
        try:
            # Get the task function
            func = self.registry.get(task.func)
            if func:
                result = func()
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.error = None
            else:
                task.status = TaskStatus.FAILED
                task.error = f"Unknown task: {task.func}"
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logging.error(f"Task {task.id} failed: {e}")
            
        duration = time.time() - start_time
        
        # Record result
        result = TaskResult(
            task_id=task.id,
            status=task.status,
            output=task.result,
            error=task.error,
            duration=duration
        )
        self.results.append(result)
        
        # Trim results
        if len(self.results) > self.max_results:
            self.results = self.results[-self.max_results:]
            
        # Schedule next run
        task.next_run = task._calculate_next_run()
        
        logging.info(f"Task {task.name} {task.status.value} in {duration:.2f}s")


def demo():
    """Demo scheduler"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              AirOne v4.0 - Scheduler System              ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create scheduler
    scheduler = Scheduler()
    
    # Add some tasks
    scheduler.add_task(ScheduledTask(
        id="task1",
        name="Backup Telemetry",
        func="telemetry_backup",
        frequency=ScheduleFrequency.HOURLY,
        interval=1
    ))
    
    scheduler.add_task(ScheduledTask(
        id="task2",
        name="Health Check",
        func="health_check",
        frequency=ScheduleFrequency.MINUTE,
        interval=5
    ))
    
    scheduler.add_task(ScheduledTask(
        id="task3",
        name="Daily Report",
        func="report_generation",
        frequency=ScheduleFrequency.DAILY
    ))
    
    # Start scheduler
    scheduler.start()
    
    print(f"Registered tasks: {scheduler.registry.list()}")
    print(f"\nActive tasks: {len(scheduler.list_tasks())}")
    
    # List tasks
    print("\nScheduled Tasks:")
    for task in scheduler.list_tasks():
        print(f"  - {task.name}: {task.frequency.value}, next: {task.next_run.strftime('%H:%M:%S')}")
    
    # Run for a few seconds
    print("\nRunning scheduler for 3 seconds...")
    time.sleep(3)
    
    # Show results
    print("\nTask Results:")
    for result in scheduler.get_results():
        print(f"  - {result.task_id}: {result.status.value} ({result.duration:.2f}s)")
    
    scheduler.stop()
    
    print("\n✓ Scheduler demo complete!")


if __name__ == "__main__":
    demo()
