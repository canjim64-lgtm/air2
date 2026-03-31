"""
Distributed Computing Module
Distributed processing for telemetry data
"""

import numpy as np
from typing import Dict, List, Any
import threading
import queue
import time
import logging


class Worker:
    """Worker node"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.busy = False
        self.task_queue = queue.Queue()
    
    def submit_task(self, task: Dict):
        """Submit task to worker"""
        self.task_queue.put(task)
    
    def process(self):
        """Process tasks"""
        while True:
            try:
                task = self.task_queue.get(timeout=1)
                self.busy = True
                
                # Process task
                result = self._execute_task(task)
                
                self.busy = False
                task['callback'](result)
                
            except queue.Empty:
                pass
    
    def _execute_task(self, task: Dict) -> Any:
        """Execute task"""
        task_type = task.get('type')
        
        if task_type == 'compute':
            return task['function'](*task.get('args', []), **task.get('kwargs', {}))
        
        return None


class DistributedCluster:
    """Distributed computing cluster"""
    
    def __init__(self):
        self.workers = {}
        self.task_queue = queue.Queue()
    
    def add_worker(self, worker_id: str):
        """Add worker"""
        worker = Worker(worker_id)
        self.workers[worker_id] = worker
        
        thread = threading.Thread(target=worker.process, daemon=True)
        thread.start()
    
    def submit_task(self, task: Dict, callback=None):
        """Submit task to cluster"""
        task['callback'] = callback or (lambda x: None)
        
        # Find least busy worker
        min_load = float('inf')
        chosen = None
        
        for worker_id, worker in self.workers.items():
            if not worker.busy:
                chosen = worker_id
                break
        
        if chosen:
            self.workers[chosen].submit_task(task)
        else:
            self.task_queue.put(task)
    
    def map_reduce(self, data: List, map_func, reduce_func) -> Any:
        """MapReduce"""
        # Map phase
        results = []
        for item in data:
            result = map_func(item)
            results.append(result)
        
        # Reduce phase
        return reduce_func(results)


class DataPartition:
    """Data partitioning"""
    
    @staticmethod
    def partition_round_robin(data: List, num_partitions: int) -> List[List]:
        """Round robin partition"""
        partitions = [[] for _ in range(num_partitions)]
        
        for i, item in enumerate(data):
            partitions[i % num_partitions].append(item)
        
        return partitions
    
    @staticmethod
    def partition_by_key(data: List[Dict], key: str) -> Dict[Any, List]:
        """Partition by key"""
        partitions = {}
        
        for item in data:
            partition_key = item.get(key)
            if partition_key not in partitions:
                partitions[partition_key] = []
            partitions[partition_key].append(item)
        
        return partitions


class LoadBalancer:
    """Load balancer"""
    
    def __init__(self):
        self.workers = {}
        self.current_index = 0
    
    def add_worker(self, worker_id: str, capacity: float = 1.0):
        """Add worker"""
        self.workers[worker_id] = capacity
    
    def get_worker(self) -> str:
        """Get next worker (least connections)"""
        # Round robin
        worker_ids = list(self.workers.keys())
        worker = worker_ids[self.current_index % len(worker_ids)]
        self.current_index += 1
        return worker


# Example
if __name__ == "__main__":
    print("Testing Distributed Computing...")
    
    cluster = DistributedCluster()
    cluster.add_worker("worker1")
    cluster.add_worker("worker2")
    
    def square(x): return x ** 2
    def sum_all(x): return sum(x)
    
    result = cluster.map_reduce([1,2,3,4,5], square, sum_all)
    print(f"Result: {result}")