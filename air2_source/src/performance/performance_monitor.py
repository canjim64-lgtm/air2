"""
Performance Monitoring Module
Performance metrics and monitoring
"""

import time
import psutil
from typing import Dict


class PerformanceMonitor:
    """Monitor performance"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage"""
        return psutil.cpu_percent()
    
    def get_memory_usage(self) -> Dict:
        """Get memory usage"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'used': mem.used
        }
    
    def get_disk_usage(self) -> Dict:
        """Get disk usage"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    
    def get_network_stats(self) -> Dict:
        """Get network stats"""
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }
    
    def get_uptime(self) -> float:
        """Get uptime"""
        return time.time() - self.start_time
    
    def get_all(self) -> Dict:
        """Get all metrics"""
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_stats(),
            'uptime': self.get_uptime()
        }


# Example
if __name__ == "__main__":
    pm = PerformanceMonitor()
    print(pm.get_cpu_usage())