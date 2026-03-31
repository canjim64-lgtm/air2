#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Scheduling System
Enterprise-grade job scheduling with cron-like syntax, dependencies, and monitoring
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pickle


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Job:
    """Represents a scheduled job"""
    id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    schedule: str = None  # Cron-like syntax or interval
    priority: JobPriority = JobPriority.NORMAL
    enabled: bool = True
    max_retries: int = 3
    retry_count: int = 0
    timeout: int = 3600  # seconds
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    dependencies: List[str] = field(default_factory=list)


class Scheduler:
    """Advanced job scheduler"""
    
    def __init__(self):
        self.jobs = {}
        self.job_history = []
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.RLock()
        self.config_dir = Path(__file__).parent.parent / 'config' / 'scheduler'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = 1000
    
    def create_job(self, name: str, function: Callable, schedule: str = None,
                  args: tuple = None, kwargs: dict = None,
                  priority: JobPriority = JobPriority.NORMAL,
                  max_retries: int = 3, timeout: int = 3600,
                  dependencies: List[str] = None) -> Job:
        """Create and register a new job"""
        job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(name.encode('utf-8')).hexdigest()[:8]}"
        
        job = Job(
            id=job_id,
            name=name,
            function=function,
            args=args or (),
            kwargs=kwargs or {},
            schedule=schedule,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            dependencies=dependencies or []
        )
        
        # Calculate next run time
        job.next_run = self._calculate_next_run(schedule)
        
        with self.lock:
            self.jobs[job_id] = job
        
        return job
    
    def _calculate_next_run(self, schedule: str) -> Optional[str]:
        """Calculate next run time from schedule"""
        if not schedule:
            return None
        
        try:
            # Simple interval parsing (e.g., "every 5 minutes", "daily", "hourly")
            schedule_lower = schedule.lower()
            
            if 'minute' in schedule_lower:
                minutes = int(''.join(filter(str.isdigit, schedule)))
                return (datetime.utcnow() + timedelta(minutes=minutes)).isoformat()
            elif 'hour' in schedule_lower:
                hours = int(''.join(filter(str.isdigit, schedule)))
                return (datetime.utcnow() + timedelta(hours=hours)).isoformat()
            elif 'day' in schedule_lower:
                days = int(''.join(filter(str.isdigit, schedule)))
                return (datetime.utcnow() + timedelta(days=days)).isoformat()
            elif schedule_lower == 'daily':
                return (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
            elif schedule_lower == 'hourly':
                return (datetime.utcnow() + timedelta(hours=1)).replace(minute=0, second=0).isoformat()
            else:
                return None
        except:
            return None
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        
        def scheduler_loop():
            while self.running:
                try:
                    self._check_and_run_jobs()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logging.error(f"Scheduler error: {e}")
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logging.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logging.info("Scheduler stopped")
    
    def _check_and_run_jobs(self):
        """Check and run due jobs"""
        with self.lock:
            now = datetime.utcnow()
            
            # Get jobs that are due
            due_jobs = []
            for job in self.jobs.values():
                if not job.enabled or job.status == JobStatus.RUNNING:
                    continue
                
                if job.next_run:
                    next_run = datetime.fromisoformat(job.next_run)
                    if now >= next_run:
                        # Check dependencies
                        deps_satisfied = self._check_dependencies(job)
                        if deps_satisfied:
                            due_jobs.append(job)
            
            # Sort by priority
            due_jobs.sort(key=lambda j: j.priority.value, reverse=True)
            
            # Run due jobs
            for job in due_jobs:
                self._run_job(job)
    
    def _check_dependencies(self, job: Job) -> bool:
        """Check if job dependencies are satisfied"""
        for dep_id in job.dependencies:
            dep_job = self.jobs.get(dep_id)
            if not dep_job or dep_job.status != JobStatus.COMPLETED:
                return False
        return True
    
    def _run_job(self, job: Job):
        """Run a job"""
        job.status = JobStatus.RUNNING
        job.last_run = datetime.utcnow().isoformat()
        
        logging.info(f"Running job: {job.name}")
        
        def run_job_thread():
            try:
                # Execute job function
                result = job.function(*job.args, **job.kwargs)
                
                job.status = JobStatus.COMPLETED
                job.error = None
                job.next_run = self._calculate_next_run(job.schedule)
                
                logging.info(f"Job completed: {job.name}")
                
            except Exception as e:
                job.error = str(e)
                job.retry_count += 1
                
                if job.retry_count < job.max_retries:
                    job.status = JobStatus.PENDING
                    logging.warning(f"Job failed, will retry: {job.name} ({job.retry_count}/{job.max_retries})")
                else:
                    job.status = JobStatus.FAILED
                    logging.error(f"Job failed after {job.max_retries} retries: {job.name}")
            
            # Add to history
            self.job_history.append({
                'job_id': job.id,
                'job_name': job.name,
                'status': job.status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'error': job.error
            })
            
            # Trim history
            if len(self.job_history) > self.max_history:
                self.job_history = self.job_history[-self.max_history:]
        
        # Run job in thread
        thread = threading.Thread(target=run_job_thread, daemon=True)
        thread.start()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def enable_job(self, job_id: str):
        """Enable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
    
    def disable_job(self, job_id: str):
        """Disable a job"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
    
    def cancel_job(self, job_id: str):
        """Cancel a job"""
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.CANCELLED
            self.jobs[job_id].enabled = False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
    
    def get_job_history(self, job_id: str = None, limit: int = 100) -> List[Dict]:
        """Get job history"""
        history = self.job_history.copy()
        
        if job_id:
            history = [h for h in history if h['job_id'] == job_id]
        
        # Sort by timestamp
        history.sort(key=lambda h: h['timestamp'], reverse=True)
        
        return history[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        with self.lock:
            total_jobs = len(self.jobs)
            enabled_jobs = len([j for j in self.jobs.values() if j.enabled])
            running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
            completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
            failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
            
            return {
                'total_jobs': total_jobs,
                'enabled_jobs': enabled_jobs,
                'running_jobs': running_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'history_size': len(self.job_history),
                'scheduler_running': self.running
            }
    
    def save_configuration(self):
        """Save scheduler configuration"""
        config = {
            'jobs': {
                job_id: {
                    'name': job.name,
                    'schedule': job.schedule,
                    'priority': job.priority.value,
                    'enabled': job.enabled,
                    'max_retries': job.max_retries,
                    'timeout': job.timeout,
                    'dependencies': job.dependencies,
                    'metadata': job.metadata
                }
                for job_id, job in self.jobs.items()
            }
        }
        
        config_file = self.config_dir / 'scheduler_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def load_configuration(self):
        """Load scheduler configuration"""
        config_file = self.config_dir / 'scheduler_config.json'
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logging.info(f"Scheduler configuration loaded from: {config_file}")
        except Exception as e:
            logging.error(f"Failed to load scheduler configuration: {e}")


def create_scheduler() -> Scheduler:
    """Create and return scheduler"""
    scheduler = Scheduler()
    scheduler.load_configuration()
    return scheduler


if __name__ == '__main__':
    # Test scheduler
    logging.basicConfig(level=logging.INFO)
    
    scheduler = create_scheduler()
    
    # Create test jobs
    def test_job():
        print(f"Test job executed at {datetime.utcnow().isoformat()}")
        return True
    
    job1 = scheduler.create_job(
        name='Test Job 1',
        function=test_job,
        schedule='every 1 minute',
        priority=JobPriority.NORMAL
    )
    
    job2 = scheduler.create_job(
        name='Test Job 2',
        function=test_job,
        schedule='every 5 minutes',
        priority=JobPriority.HIGH
    )
    
    # Start scheduler
    scheduler.start()
    
    print("Scheduler started")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler stopped")
