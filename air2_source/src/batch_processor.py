"""
AirOne Professional v4.0 - Batch Processing Utilities
Process multiple files and datasets efficiently
"""
# -*- coding: utf-8 -*-

import os
import json
import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from queue import Queue

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple files in batch"""
    
    def __init__(self, input_dir: str = "data", output_dir: str = "output",
                 max_workers: int = 4, progress_callback: Optional[Callable] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.processed = 0
        self.failed = 0
        self.total = 0
        self.lock = threading.Lock()
    
    def find_files(self, pattern: str = "*.json") -> List[Path]:
        """Find files matching pattern"""
        return sorted(self.input_dir.glob(pattern))
    
    def process_file(self, filepath: Path, process_func: Callable) -> Dict[str, Any]:
        """Process a single file"""
        start_time = time.time()
        
        try:
            # Read input
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.suffix == '.json':
                    data = json.load(f)
                elif filepath.suffix == '.csv':
                    reader = csv.DictReader(f)
                    data = list(reader)
                else:
                    data = f.read()
            
            # Process
            result = process_func(data, filepath)
            
            # Write output
            output_path = self.output_dir / f"processed_{filepath.name}"
            
            if isinstance(result, dict):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str)
            elif isinstance(result, list):
                with open(output_path, 'w', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=result[0].keys() if result else [])
                    writer.writeheader()
                    writer.writerows(result)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))
            
            duration = time.time() - start_time
            
            with self.lock:
                self.processed += 1
            
            return {
                'status': 'success',
                'file': str(filepath),
                'output': str(output_path),
                'duration': duration
            }
            
        except Exception as e:
            with self.lock:
                self.failed += 1
            
            return {
                'status': 'error',
                'file': str(filepath),
                'error': str(e)
            }
    
    def process_batch(self, pattern: str = "*.json",
                     process_func: Optional[Callable] = None) -> Dict[str, Any]:
        """Process batch of files"""
        files = self.find_files(pattern)
        self.total = len(files)
        
        if not files:
            return {'status': 'warning', 'message': 'No files found'}
        
        print(f"\nProcessing {self.total} files with {self.max_workers} workers...")
        
        # Default process function (identity)
        if process_func is None:
            process_func = lambda data, path: data
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_file, f, process_func): f for f in files}
            
            for i, future in enumerate(futures):
                result = future.result()
                results.append(result)
                
                # Progress callback
                if self.progress_callback:
                    self.progress_callback(i + 1, self.total, result)
                else:
                    progress = (i + 1) / self.total * 100
                    print(f"\rProgress: {progress:.1f}% ({i + 1}/{self.total})", end='', flush=True)
        
        total_duration = time.time() - start_time
        print(f"\n\nCompleted in {total_duration:.2f}s")
        print(f"  Processed: {self.processed}")
        print(f"  Failed: {self.failed}")
        
        return {
            'status': 'complete',
            'total_files': self.total,
            'processed': self.processed,
            'failed': self.failed,
            'duration': total_duration,
            'results': results
        }
    
    def process_with_progress_bar(self, pattern: str = "*.json",
                                  process_func: Optional[Callable] = None):
        """Process batch with visual progress bar"""
        def progress_callback(current, total, result):
            progress = current / total * 100
            bar_length = 40
            filled = int(bar_length * current // total)
            bar = '█' * filled + '░' * (bar_length - filled)
            status = '✓' if result['status'] == 'success' else '✗'
            print(f"\r[{bar}] {progress:.1f}% {status}", end='', flush=True)
        
        self.progress_callback = progress_callback
        return self.process_batch(pattern, process_func)


class DataPipeline:
    """Data processing pipeline"""
    
    def __init__(self):
        self.stages: List[Callable] = []
        self.stats = {
            'items_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def add_stage(self, func: Callable, name: str = "") -> 'DataPipeline':
        """Add processing stage"""
        self.stages.append(func)
        return self
    
    def execute(self, data: Any) -> Any:
        """Execute pipeline on data"""
        self.stats['start_time'] = datetime.now()
        result = data
        
        for i, stage in enumerate(self.stages):
            try:
                result = stage(result)
                self.stats['items_processed'] += 1
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Stage {i} failed: {e}")
                raise
        
        self.stats['end_time'] = datetime.now()
        return result
    
    def execute_batch(self, items: List[Any]) -> List[Any]:
        """Execute pipeline on batch of items"""
        results = []
        
        for item in items:
            try:
                result = self.execute(item)
                results.append(result)
            except:
                results.append(None)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        return {
            'items_processed': self.stats['items_processed'],
            'errors': self.stats['errors'],
            'duration_seconds': duration,
            'stages': len(self.stages)
        }


class FileWatcher:
    """Watch directory for file changes"""
    
    def __init__(self, directory: str, callback: Callable, pattern: str = "*.json"):
        self.directory = Path(directory)
        self.callback = callback
        self.pattern = pattern
        self.running = False
        self.known_files = set()
        self.watch_thread = None
    
    def start(self, interval: float = 2.0):
        """Start watching"""
        self.running = True
        self.known_files = set(str(f) for f in self.directory.glob(self.pattern))
        
        self.watch_thread = threading.Thread(target=self._watch_loop, args=(interval,))
        self.watch_thread.daemon = True
        self.watch_thread.start()
        
        print(f"Watching {self.directory} for {self.pattern} files...")
    
    def stop(self):
        """Stop watching"""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=5)
    
    def _watch_loop(self, interval: float):
        """Watch loop"""
        while self.running:
            time.sleep(interval)
            
            current_files = set(str(f) for f in self.directory.glob(self.pattern))
            
            # New files
            new_files = current_files - self.known_files
            for filepath in new_files:
                print(f"\n[NEW] {filepath}")
                self.callback('new', Path(filepath))
            
            # Deleted files
            deleted_files = self.known_files - current_files
            for filepath in deleted_files:
                print(f"\n[DELETED] {filepath}")
                self.callback('deleted', Path(filepath))
            
            self.known_files = current_files


def create_pipeline() -> DataPipeline:
    """Create a data pipeline"""
    return DataPipeline()


def batch_process_files(input_dir: str, output_dir: str,
                       pattern: str = "*.json",
                       process_func: Optional[Callable] = None) -> Dict[str, Any]:
    """Quick batch process files"""
    processor = BatchProcessor(input_dir, output_dir)
    return processor.process_batch(pattern, process_func)


if __name__ == "__main__":
    # Test batch processor
    print("="*70)
    print("  AirOne Professional v4.0 - Batch Processing Test")
    print("="*70)
    print()
    
    # Create test data
    test_dir = Path("data/test_batch")
    test_dir.mkdir(exist_ok=True)
    
    print("Creating test files...")
    for i in range(5):
        test_file = test_dir / f"test_{i}.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({'id': i, 'value': i * 10, 'timestamp': datetime.now().isoformat()}, f)
    
    print(f"Created {5} test files in {test_dir}")
    print()
    
    # Process files
    processor = BatchProcessor(
        input_dir=str(test_dir),
        output_dir="output/test_batch",
        max_workers=2
    )
    
    # Define custom process function
    def add_metadata(data, filepath):
        data['processed'] = True
        data['processed_at'] = datetime.now().isoformat()
        return data
    
    result = processor.process_batch("*.json", add_metadata)
    
    print()
    print("Batch processing completed!")
    print(f"  Status: {result['status']}")
    print(f"  Total: {result['total_files']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed: {result['failed']}")
    
    # Test pipeline
    print()
    print("Testing data pipeline...")
    
    pipeline = create_pipeline()
    pipeline.add_stage(lambda x: x * 2, "Double")
    pipeline.add_stage(lambda x: x + 10, "Add 10")
    pipeline.add_stage(lambda x: {'result': x}, "Wrap")
    
    result = pipeline.execute(5)
    print(f"  Pipeline result: {result}")
    print(f"  Stats: {pipeline.get_stats()}")
    
    print()
    print("="*70)
    print("  Batch Processing Test Complete")
    print("="*70)
