"""
Performance Optimization Module for AirOne Professional System
Implements caching, resource management, async processing, and performance monitoring
"""

import asyncio
import time
import threading
import queue
import functools
import cProfile
import pstats
from io import StringIO
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import gc
import psutil
import tracemalloc
from functools import lru_cache
import weakref
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from abc import ABC, abstractmethod
import redis
import pickle
import hashlib
import secrets
from datetime import datetime, timedelta
import asyncio
import aioredis
import asyncpg
import uvloop


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be optimized"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    DATABASE = "database"


@dataclass
class ResourceUsage:
    """Resource usage metrics"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    io_read_bytes: int
    io_write_bytes: int
    network_sent_bytes: int
    network_recv_bytes: int
    timestamp: datetime


class CacheStrategy(Enum):
    """Different caching strategies"""
    LRU = "lru"
    TTL = "ttl"
    LFU = "lfu"
    FIFO = "fifo"


class PerformanceOptimizer:
    """Main performance optimization class"""
    
    def __init__(self, enable_profiling: bool = False, enable_caching: bool = True):
        self.enable_profiling = enable_profiling
        self.enable_caching = enable_caching
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.resource_monitor = ResourceMonitor()
        self.task_scheduler = TaskScheduler()
        self.profiler = cProfile.Profile() if enable_profiling else None
        self.metrics = {}
        self.optimization_strategies = []
        self.running = False
        
        # Initialize async event loop
        try:
            uvloop.install()
        except ImportError:
            logger.warning("uvloop not available, using default asyncio event loop")
        
        logger.info("Performance optimizer initialized")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.running = True
        self.resource_monitor.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        self.resource_monitor.stop()
        logger.info("Performance monitoring stopped")
    
    def cache_result(self, ttl_seconds: int = 300, max_size: int = 1000):
        """Decorator to cache function results"""
        def decorator(func):
            if self.enable_caching:
                # Use LRU cache with size limit
                cached_func = lru_cache(maxsize=max_size)(func)
                
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    # Add TTL logic if needed
                    return cached_func(*args, **kwargs)
                
                return wrapper
            else:
                return func
        return decorator
    
    def async_execute(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """Execute a function asynchronously"""
        return self.task_scheduler.schedule_async(func, *args, **kwargs)
    
    def parallel_execute(self, func: Callable, data: List[Any], max_workers: int = None) -> List[Any]:
        """Execute a function in parallel on multiple data items"""
        return self.task_scheduler.execute_parallel(func, data, max_workers)
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function"""
        if not self.enable_profiling:
            return func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.profiler.enable()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                self.profiler.disable()
        return wrapper
    
    def get_performance_report(self) -> str:
        """Get a performance report"""
        if not self.enable_profiling:
            return "Profiling not enabled"
        
        s = StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        return s.getvalue()
    
    def optimize_memory(self):
        """Run memory optimization routines"""
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Memory optimization: Collected {collected} objects")
        
        # Start tracing memory allocations
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
        logger.info(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
    
    def add_optimization_strategy(self, strategy: Callable):
        """Add a custom optimization strategy"""
        self.optimization_strategies.append(strategy)
    
    def run_optimization_strategies(self):
        """Run all registered optimization strategies"""
        for strategy in self.optimization_strategies:
            try:
                strategy()
            except Exception as e:
                logger.error(f"Optimization strategy failed: {e}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'resource_usage': self.resource_monitor.get_current_usage(),
            'cache_stats': self.get_cache_stats(),
            'task_stats': self.task_scheduler.get_stats(),
            'memory_usage_mb': psutil.virtual_memory().used / (1024*1024),
            'cpu_count': psutil.cpu_count(),
            'disk_usage_percent': psutil.disk_usage('/').percent
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }


class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.running = False
        self.monitor_thread = None
        self.history = []
        self.max_history = 1000
        self.process = psutil.Process()
        self.stats_lock = threading.Lock()
        self.current_usage = ResourceUsage(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_mb=0.0,
            io_read_bytes=0,
            io_write_bytes=0,
            network_sent_bytes=0,
            network_recv_bytes=0,
            timestamp=datetime.utcnow()
        )
    
    def start(self):
        """Start monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current resource usage
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                memory_percent = self.process.memory_percent()
                
                # Get I/O stats
                io_counters = self.process.io_counters()
                io_read_bytes = io_counters.read_bytes
                io_write_bytes = io_counters.write_bytes
                
                # Get network stats
                net_io = psutil.net_io_counters()
                network_sent = net_io.bytes_sent
                network_recv = net_io.bytes_recv
                
                # Update current usage
                current_usage = ResourceUsage(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_mb=memory_mb,
                    io_read_bytes=io_read_bytes,
                    io_write_bytes=io_write_bytes,
                    network_sent_bytes=network_sent,
                    network_recv_bytes=network_recv,
                    timestamp=datetime.utcnow()
                )
                
                with self.stats_lock:
                    self.current_usage = current_usage
                    
                    # Add to history
                    self.history.append(current_usage)
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(self.interval)
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        with self.stats_lock:
            return self.current_usage
    
    def get_usage_history(self, minutes: int = 5) -> List[ResourceUsage]:
        """Get resource usage history for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        with self.stats_lock:
            return [usage for usage in self.history if usage.timestamp >= cutoff_time]
    
    def get_average_usage(self, minutes: int = 5) -> Dict[str, float]:
        """Get average resource usage over the last N minutes"""
        history = self.get_usage_history(minutes)
        if not history:
            return {}
        
        avg_cpu = sum(u.cpu_percent for u in history) / len(history)
        avg_memory_mb = sum(u.memory_mb for u in history) / len(history)
        avg_memory_percent = sum(u.memory_percent for u in history) / len(history)
        
        return {
            'avg_cpu_percent': avg_cpu,
            'avg_memory_mb': avg_memory_mb,
            'avg_memory_percent': avg_memory_percent,
            'sample_count': len(history)
        }


class TaskScheduler:
    """Manages task scheduling and execution"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers//2)
        self.async_queue = asyncio.Queue()
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_execution_time': 0.0,
            'total_execution_time': 0.0
        }
        self.stats_lock = threading.Lock()
    
    async def schedule_async(self, func: Callable, *args, **kwargs):
        """Schedule a function for async execution"""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.thread_pool, func, *args)
            
            execution_time = time.time() - start_time
            
            with self.stats_lock:
                self.stats['tasks_completed'] += 1
                self.stats['total_execution_time'] += execution_time
                self.stats['avg_execution_time'] = self.stats['total_execution_time'] / self.stats['tasks_completed']
            
            return result
        except Exception as e:
            with self.stats_lock:
                self.stats['tasks_failed'] += 1
            logger.error(f"Async task failed: {e}")
            raise
    
    def execute_parallel(self, func: Callable, data: List[Any], max_workers: int = None) -> List[Any]:
        """Execute a function in parallel on multiple data items"""
        max_workers = max_workers or self.max_workers
        start_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(func, data))
            
            execution_time = time.time() - start_time
            
            with self.stats_lock:
                self.stats['tasks_completed'] += len(data)
                self.stats['total_execution_time'] += execution_time
                self.stats['avg_execution_time'] = self.stats['total_execution_time'] / self.stats['tasks_completed']
            
            return results
        except Exception as e:
            with self.stats_lock:
                self.stats['tasks_failed'] += len(data)
            logger.error(f"Parallel execution failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        with self.stats_lock:
            return self.stats.copy()


class AsyncCache:
    """Asynchronous cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.cache = {}
        self.lock = threading.Lock()
        self.cleanup_timer = None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in the cache with optional TTL"""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl if ttl > 0 else None
        
        with self.lock:
            self.cache[key] = {
                'value': value,
                'expiry': expiry
            }
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            
            # Check if expired
            if item['expiry'] and time.time() > item['expiry']:
                del self.cache[key]
                return None
            
            return item['value']
    
    def delete(self, key: str):
        """Delete a key from the cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear_expired(self):
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        with self.lock:
            for key, item in self.cache.items():
                if item['expiry'] and current_time > item['expiry']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        return len(expired_keys)
    
    def get_size(self) -> int:
        """Get the current cache size"""
        with self.lock:
            return len(self.cache)


class DatabaseConnectionPool:
    """Optimized database connection pool"""
    
    def __init__(self, db_url: str, min_connections: int = 2, max_connections: int = 10):
        self.db_url = db_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.available_connections = queue.Queue(maxsize=max_connections)
        self.active_connections = set()
        self.lock = threading.Lock()
        self.initialize_pool()
    
    def initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            self.available_connections.put(conn)
    
    def _create_connection(self):
        """Create a new database connection"""
        # Using simulated connection for connection pooling
        self.logger.debug("Creating simulated database connection")
        return {"connection_id": secrets.token_urlsafe(8), "connected": True}
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            # Try to get an available connection
            conn = self.available_connections.get_nowait()
        except queue.Empty:
            # If none available, create a new one if we're under the limit
            with self.lock:
                if len(self.active_connections) < self.max_connections:
                    conn = self._create_connection()
                else:
                    # Wait for an available connection
                    conn = self.available_connections.get()
        
        self.active_connections.add(conn)
        return conn
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.active_connections.discard(conn)
        try:
            self.available_connections.put_nowait(conn)
        except queue.Full:
            # Pool is full, close the connection
            self._close_connection(conn)
    
    def _close_connection(self, conn):
        """Close a database connection"""
        conn["connected"] = False
    
    def get_stats(self) -> Dict[str, int]:
        """Get connection pool statistics"""
        return {
            "available": self.available_connections.qsize(),
            "active": len(self.active_connections),
            "max": self.max_connections
        }


class PerformanceMonitor:
    """Monitors and reports performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.histograms = {}
        self.counters = {}
        self.gauges = {}
        self.lock = threading.Lock()
    
    def start_timer(self, name: str):
        """Start a timer for a specific operation"""
        self.start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a timer and return elapsed time"""
        if name in self.start_times:
            elapsed = time.time() - self.start_times[name]
            del self.start_times[name]
            
            # Update histogram
            if name not in self.histograms:
                self.histograms[name] = []
            self.histograms[name].append(elapsed)
            
            return elapsed
        return 0.0
    
    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter"""
        with self.lock:
            if name not in self.counters:
                self.counters[name] = 0
            self.counters[name] += amount
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value"""
        with self.lock:
            self.gauges[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        with self.lock:
            metrics = {
                "histograms": {},
                "counters": self.counters.copy(),
                "gauges": self.gauges.copy()
            }
            
            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    metrics["histograms"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": sorted(values)[len(values)//2] if values else 0,
                        "p95": sorted(values)[int(0.95 * len(values))] if values else 0,
                        "p99": sorted(values)[int(0.99 * len(values))] if values else 0
                    }
            
            return metrics


class OptimizedDataProcessor:
    """Optimized data processing with batching and parallelization"""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batch(self, data_batch: List[Any], processor_func: Callable) -> List[Any]:
        """Process a batch of data"""
        return [processor_func(item) for item in data_batch]
    
    def process_large_dataset(self, dataset: List[Any], processor_func: Callable) -> List[Any]:
        """Process a large dataset efficiently"""
        results = []
        
        # Split dataset into batches
        for i in range(0, len(dataset), self.batch_size):
            batch = dataset[i:i + self.batch_size]
            
            # Process batch in parallel
            batch_results = self.executor.submit(
                self.process_batch, batch, processor_func
            ).result()
            
            results.extend(batch_results)
        
        return results
    
    def close(self):
        """Close the processor and cleanup resources"""
        self.executor.shutdown(wait=True)


# Example usage and testing
async def main():
    # Initialize performance optimizer
    optimizer = PerformanceOptimizer(enable_profiling=True, enable_caching=True)
    optimizer.start_monitoring()
    
    print("⚡ Performance Optimization System Started...")
    
    # Example: Cache a function
    @optimizer.cache_result(ttl_seconds=60, max_size=100)
    def expensive_calculation(n: int) -> int:
        """Simulate an expensive calculation"""
        time.sleep(0.1)  # Simulate work
        return n * n
    
    # Test caching
    print("Testing cached function...")
    start_time = time.time()
    for i in range(5):
        result = expensive_calculation(i)
        print(f"Result {i}: {result}")
    first_run_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(5):  # These should be cached
        result = expensive_calculation(i)
        print(f"Cached Result {i}: {result}")
    cached_run_time = time.time() - start_time
    
    print(f"First run time: {first_run_time:.2f}s")
    print(f"Cached run time: {cached_run_time:.2f}s")
    print(f"Speedup: {first_run_time/cached_run_time:.2f}x" if cached_run_time > 0 else "N/A")
    
    # Example: Async execution
    async def async_task(x: int) -> int:
        await asyncio.sleep(0.1)  # Simulate async work
        return x * 2
    
    print("\nTesting async execution...")
    start_time = time.time()
    tasks = [async_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    print(f"Async results: {results}")
    print(f"Async execution time: {async_time:.2f}s")
    
    # Example: Parallel execution
    def cpu_intensive_task(x: int) -> int:
        # Simulate CPU-intensive work
        result = 0
        for i in range(x * 1000):
            result += i
        return result
    
    print("\nTesting parallel execution...")
    start_time = time.time()
    data = list(range(1, 6))
    parallel_results = optimizer.parallel_execute(cpu_intensive_task, data, max_workers=4)
    parallel_time = time.time() - start_time
    print(f"Parallel results: {parallel_results}")
    print(f"Parallel execution time: {parallel_time:.2f}s")
    
    # Example: Memory optimization
    print("\nRunning memory optimization...")
    optimizer.optimize_memory()
    
    # Example: Get system metrics
    print("\nGetting system metrics...")
    metrics = optimizer.get_system_metrics()
    print(f"CPU Percent: {metrics['resource_usage'].cpu_percent}%")
    print(f"Memory Used: {metrics['resource_usage'].memory_mb:.2f} MB")
    print(f"Cache Size: {metrics['cache_stats']['cache_size']}")
    
    # Stop monitoring
    optimizer.stop_monitoring()
    
    # Get performance report if profiling was enabled
    if optimizer.enable_profiling:
        print("\n📊 Performance Report:")
        print(optimizer.get_performance_report())
    
    print("\n✅ Performance optimization system test completed")


if __name__ == "__main__":
    asyncio.run(main())