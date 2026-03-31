"""
Advanced Data Processing Pipeline Module
Complete data processing pipeline with stages, caching, and parallel processing
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
import time
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
import hashlib
import json


class PipelineStageType(Enum):
    """Pipeline stage types"""
    SOURCE = "source"
    FILTER = "filter"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    MAP = "map"
    REDUCE = "reduce"
    OUTPUT = "output"


class CachePolicy(Enum):
    """Cache behavior policies"""
    NO_CACHE = "no_cache"
    LRU = "lru"
    TTL = "ttl"
    PERSISTENT = "persistent"


@dataclass
class PipelineStage:
    """A single pipeline stage"""
    name: str
    stage_type: PipelineStageType
    processor: Callable
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    

@dataclass
class PipelineData:
    """Data container passed through pipeline"""
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    stage_results: Dict[str, Any] = field(default_factory=dict)
    

class ProcessingCache:
    """Cache for pipeline processing results"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300):
        self.max_size = max_size
        self.ttl = ttl
        
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order: deque = deque()
        self.hits = 0
        self.misses = 0
        
    def _generate_key(self, stage_name: str, data: Any) -> str:
        """Generate cache key"""
        # Simple hash based on data representation
        data_str = str(data)[:1000]  # Limit size
        key_str = f"{stage_name}:{data_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, stage_name: str, data: Any) -> Optional[Any]:
        """Get cached result"""
        key = self._generate_key(stage_name, data)
        
        if key in self.cache:
            value, timestamp = self.cache[key]
            
            # Check TTL
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                # Update access order
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                return value
            else:
                # Expired
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def put(self, stage_name: str, data: Any, result: Any):
        """Store result in cache"""
        
        # Check size limit
        if len(self.cache) >= self.max_size:
            # Remove oldest
            oldest_key = self.access_order.popleft()
            if oldest_key in self.cache:
                del self.cache[oldest_key]
        
        key = self._generate_key(stage_name, data)
        self.cache[key] = (result, time.time())
        
        if key not in self.access_order:
            self.access_order.append(key)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / (self.hits + self.misses) if self.hits + self.misses > 0 else 0
        }


class PipelineExecutor:
    """Execute pipeline stages"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def execute_stage(self, stage: PipelineStage, 
                     data: PipelineData) -> PipelineData:
        """Execute single stage"""
        
        if not stage.enabled:
            return data
        
        try:
            result = stage.processor(data.data, data)
            
            # Create new data container
            new_data = PipelineData(
                data=result,
                metadata=data.metadata.copy(),
                stage_results=data.stage_results.copy()
            )
            new_data.stage_results[stage.name] = result
            
            return new_data
            
        except Exception as e:
            logging.error(f"Stage {stage.name} error: {e}")
            raise
    
    def execute_parallel(self, stages: List[PipelineStage],
                         data: PipelineData) -> PipelineData:
        """Execute stages in parallel (for independent stages)"""
        
        futures = []
        
        for stage in stages:
            if stage.enabled:
                future = self.executor.submit(
                    self.execute_stage, stage, data
                )
                futures.append(future)
        
        # Wait for all
        results = [f.result() for f in futures]
        
        # Merge results
        if results:
            final = results[-1]
            for r in results[:-1]:
                final.stage_results.update(r.stage_results)
            return final
        
        return data


class DataPipeline:
    """Complete data processing pipeline"""
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.stages: List[PipelineStage] = []
        
        self.cache = ProcessingCache()
        self.executor = PipelineExecutor()
        
        # Metrics
        self.processed_count = 0
        self.error_count = 0
        self.total_time = 0.0
        
        # State
        self.running = False
        self.input_queue: queue.Queue = queue.Queue()
        self.output_queue: queue.Queue = queue.Queue()
        
    def add_stage(self, name: str, stage_type: PipelineStageType,
                  processor: Callable, config: Optional[Dict] = None):
        """Add pipeline stage"""
        
        stage = PipelineStage(
            name=name,
            stage_type=stage_type,
            processor=processor,
            config=config or {}
        )
        
        self.stages.append(stage)
        return self
    
    def add_source(self, name: str, source_fn: Callable):
        """Add data source"""
        return self.add_stage(name, PipelineStageType.SOURCE, source_fn)
    
    def add_filter(self, name: str, filter_fn: Callable):
        """Add filter stage"""
        return self.add_stage(name, PipelineStageType.FILTER, filter_fn)
    
    def add_transform(self, name: str, transform_fn: Callable):
        """Add transform stage"""
        return self.add_stage(name, PipelineStageType.TRANSFORM, transform_fn)
    
    def add_aggregate(self, name: str, aggregate_fn: Callable):
        """Add aggregation stage"""
        return self.add_stage(name, PipelineStageType.AGGREGATE, aggregate_fn)
    
    def add_output(self, name: str, output_fn: Callable):
        """Add output stage"""
        return self.add_stage(name, PipelineStageType.OUTPUT, output_fn)
    
    def process(self, data: Any, use_cache: bool = True) -> PipelineData:
        """Process data through pipeline"""
        
        start_time = time.time()
        
        # Create data container
        pipeline_data = PipelineData(
            data=data,
            metadata={'pipeline': self.name}
        )
        
        try:
            # Execute each stage
            for stage in self.stages:
                # Check cache
                if use_cache and stage.stage_type in [PipelineStageType.FILTER, PipelineStageType.TRANSFORM]:
                    cached = self.cache.get(stage.name, pipeline_data.data)
                    if cached is not None:
                        pipeline_data.data = cached
                        continue
                
                # Execute stage
                pipeline_data = self.executor.execute_stage(stage, pipeline_data)
                
                # Cache result
                if use_cache:
                    self.cache.put(stage.name, data, pipeline_data.data)
            
            self.processed_count += 1
            
        except Exception as e:
            self.error_count += 1
            logging.error(f"Pipeline error: {e}")
            raise
        
        finally:
            self.total_time += time.time() - start_time
        
        return pipeline_data
    
    def start_async(self):
        """Start async processing"""
        self.running = True
        
        def process_loop():
            while self.running:
                try:
                    data = self.input_queue.get(timeout=1)
                    result = self.process(data)
                    self.output_queue.put(result)
                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"Async error: {e}")
        
        thread = threading.Thread(target=process_loop, daemon=True)
        thread.start()
    
    def stop_async(self):
        """Stop async processing"""
        self.running = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            'name': self.name,
            'stages': len(self.stages),
            'processed': self.processed_count,
            'errors': self.error_count,
            'total_time': self.total_time,
            'avg_time': self.total_time / max(self.processed_count, 1),
            'cache': self.cache.get_stats()
        }


# Pipeline stage functions
def filter_outliers(data: Any, ctx: PipelineData) -> np.ndarray:
    """Filter outliers from data"""
    if isinstance(data, np.ndarray):
        mean = np.mean(data)
        std = np.std(data)
        return data[np.abs(data - mean) < 3 * std]
    return data


def normalize_data(data: Any, ctx: PipelineData) -> np.ndarray:
    """Normalize data"""
    if isinstance(data, np.ndarray):
        return (data - np.mean(data)) / (np.std(data) + 1e-10)
    return data


def extract_features(data: Any, ctx: PipelineData) -> Dict[str, float]:
    """Extract statistical features"""
    if isinstance(data, np.ndarray):
        return {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'median': float(np.median(data)),
            'skewness': float(((data - np.mean(data))**3).mean() / (np.std(data)**3 + 1e-10))
        }
    return {}


def downsample_data(data: Any, ctx: PipelineData) -> np.ndarray:
    """Downsample data"""
    if isinstance(data, np.ndarray):
        factor = ctx.config.get('factor', 10)
        return data[::factor]
    return data


def smooth_data(data: Any, ctx: PipelineData) -> np.ndarray:
    """Apply smoothing"""
    if isinstance(data, np.ndarray):
        window = ctx.config.get('window', 5)
        return np.convolve(data, np.ones(window)/window, mode='same')
    return data


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Data Processing Pipeline...")
    
    # Create pipeline
    print("\n1. Creating Pipeline...")
    pipeline = DataPipeline("telemetry_pipeline")
    
    pipeline.add_source("generate", lambda d: np.random.randn(1000))
    pipeline.add_filter("outliers", filter_outliers)
    pipeline.add_transform("normalize", normalize_data)
    pipeline.add_transform("smooth", smooth_data)
    pipeline.add_transform("downsample", downsample_data)
    pipeline.add_aggregate("features", extract_features)
    
    # Process data
    print("\n2. Processing Data...")
    result = pipeline.process(None)
    
    print(f"   Processed: {len(result.data)} samples")
    print(f"   Features: {result.stage_results.get('features', {})}")
    
    # Get statistics
    print("\n3. Pipeline Statistics...")
    stats = pipeline.get_statistics()
    print(f"   Processed: {stats['processed']}")
    print(f"   Avg time: {stats['avg_time']:.4f}s")
    print(f"   Cache stats: {stats['cache']}")
    
    # Test async
    print("\n4. Testing Async Processing...")
    pipeline2 = DataPipeline("async_pipeline")
    pipeline2.add_source("source", lambda d: np.random.randn(100))
    pipeline2.add_transform("transform", normalize_data)
    
    pipeline2.start_async()
    
    for i in range(10):
        pipeline2.input_queue.put(np.random.randn(100))
    
    time.sleep(1)
    pipeline2.stop_async()
    
    print(f"   Output queue size: {pipeline2.output_queue.qsize()}")
    
    print("\n✅ Data Processing Pipeline test completed!")