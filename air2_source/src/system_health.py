"""
AirOne Professional v4.0 - System Health Monitor
Real-time system health monitoring and alerting
"""
# -*- coding: utf-8 -*-

import psutil
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from threading import Thread
import hashlib

logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """Monitor system health in real-time"""
    
    def __init__(self, config_file: str = "config/health_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.alerts = []
        self.metrics_history = []
        self.running = False
        self.monitor_thread = None
        
    def _load_config(self) -> Dict:
        """Load health monitoring configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default configuration
        return {
            'thresholds': {
                'cpu_warning': 70,
                'cpu_critical': 90,
                'memory_warning': 75,
                'memory_critical': 95,
                'disk_warning': 80,
                'disk_critical': 95,
                'temperature_warning': 70,
                'temperature_critical': 85
            },
            'monitoring': {
                'interval_seconds': 5,
                'history_size': 1000,
                'enable_alerts': True
            }
        }
    
    def get_cpu_health(self) -> Dict[str, Any]:
        """Get CPU health status"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        status = 'OK'
        if cpu_percent > self.config['thresholds']['cpu_critical']:
            status = 'CRITICAL'
        elif cpu_percent > self.config['thresholds']['cpu_warning']:
            status = 'WARNING'
        
        return {
            'status': status,
            'usage_percent': cpu_percent,
            'cores': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_memory_health(self) -> Dict[str, Any]:
        """Get memory health status"""
        mem = psutil.virtual_memory()
        
        status = 'OK'
        if mem.percent > self.config['thresholds']['memory_critical']:
            status = 'CRITICAL'
        elif mem.percent > self.config['thresholds']['memory_warning']:
            status = 'WARNING'
        
        return {
            'status': status,
            'usage_percent': mem.percent,
            'total_gb': round(mem.total / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2),
            'used_gb': round(mem.used / (1024**3), 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_disk_health(self) -> Dict[str, Any]:
        """Get disk health status"""
        disk = psutil.disk_usage('/')
        
        status = 'OK'
        if disk.percent > self.config['thresholds']['disk_critical']:
            status = 'CRITICAL'
        elif disk.percent > self.config['thresholds']['disk_warning']:
            status = 'WARNING'
        
        return {
            'status': status,
            'usage_percent': disk.percent,
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_network_health(self) -> Dict[str, Any]:
        """Get network health status"""
        net_io = psutil.net_io_counters()
        net_if_addrs = psutil.net_if_addrs()
        
        interfaces = []
        for iface, addrs in net_if_addrs.items():
            interface_info = {
                'name': iface,
                'addresses': []
            }
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    interface_info['addresses'].append({
                        'type': 'IPv4',
                        'address': addr.address
                    })
            interfaces.append(interface_info)
        
        return {
            'status': 'OK',
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'interfaces': interfaces,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_process_health(self, limit: int = 5) -> Dict[str, Any]:
        """Get top processes by resource usage"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage
        top_memory = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:limit]
        top_cpu = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:limit]
        
        return {
            'status': 'OK',
            'top_memory': top_memory,
            'top_cpu': top_cpu,
            'total_processes': len(processes),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        cpu = self.get_cpu_health()
        memory = self.get_memory_health()
        disk = self.get_disk_health()
        network = self.get_network_health()
        
        # Determine overall status
        statuses = [cpu['status'], memory['status'], disk['status']]
        
        if 'CRITICAL' in statuses:
            overall_status = 'CRITICAL'
        elif 'WARNING' in statuses:
            overall_status = 'WARNING'
        else:
            overall_status = 'OK'
        
        return {
            'overall_status': overall_status,
            'cpu': cpu,
            'memory': memory,
            'disk': disk,
            'network': network,
            'process': self.get_process_health(),
            'health_score': self._calculate_health_score(cpu, memory, disk),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_health_score(self, cpu: Dict, memory: Dict, disk: Dict) -> int:
        """Calculate overall health score (0-100)"""
        cpu_score = max(0, 100 - cpu['usage_percent'])
        memory_score = max(0, 100 - memory['usage_percent'])
        disk_score = max(0, 100 - disk['usage_percent'])
        
        return int((cpu_score + memory_score + disk_score) / 3)
    
    def check_alerts(self, health: Dict[str, Any]):
        """Check for alert conditions"""
        if not self.config['monitoring']['enable_alerts']:
            return
        
        components = ['cpu', 'memory', 'disk']
        
        for component in components:
            data = health.get(component, {})
            status = data.get('status', 'OK')
            
            if status in ['WARNING', 'CRITICAL']:
                alert = {
                    'id': hashlib.md5(f"{component}{status}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                    'component': component,
                    'status': status,
                    'usage': data.get('usage_percent', 0),
                    'threshold': self.config['thresholds'].get(f"{component}_{status.lower()}", 0),
                    'timestamp': datetime.now().isoformat(),
                    'message': f"{component.upper()} {status}: {data.get('usage_percent', 0):.1f}% usage"
                }
                
                self.alerts.append(alert)
                logger.warning(alert['message'])
    
    def start_monitoring(self, interval: Optional[float] = None):
        """Start continuous monitoring"""
        if interval is None:
            interval = self.config['monitoring']['interval_seconds']
        
        self.running = True
        
        def monitor_loop():
            while self.running:
                try:
                    health = self.get_overall_health()
                    self.check_alerts(health)
                    
                    # Store in history
                    self.metrics_history.append(health)
                    
                    # Limit history size
                    if len(self.metrics_history) > self.config['monitoring']['history_size']:
                        self.metrics_history = self.metrics_history[-self.config['monitoring']['history_size']:]
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Health monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
        logger.info("All alerts cleared")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        return {
            'generated_at': datetime.now().isoformat(),
            'current_health': self.get_overall_health(),
            'recent_alerts': self.get_alerts(),
            'metrics_summary': self._get_metrics_summary(),
            'recommendations': self._generate_recommendations()
        }
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics_history:
            return {}
        
        cpu_usages = [m['cpu']['usage_percent'] for m in self.metrics_history]
        memory_usages = [m['memory']['usage_percent'] for m in self.metrics_history]
        disk_usages = [m['disk']['usage_percent'] for m in self.metrics_history]
        
        return {
            'cpu': {
                'avg': sum(cpu_usages) / len(cpu_usages),
                'min': min(cpu_usages),
                'max': max(cpu_usages)
            },
            'memory': {
                'avg': sum(memory_usages) / len(memory_usages),
                'min': min(memory_usages),
                'max': max(memory_usages)
            },
            'disk': {
                'avg': sum(disk_usages) / len(disk_usages),
                'min': min(disk_usages),
                'max': max(disk_usages)
            },
            'samples': len(self.metrics_history)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate system health recommendations"""
        recommendations = []
        
        current = self.get_overall_health()
        
        if current['cpu']['usage_percent'] > 80:
            recommendations.append("High CPU usage detected - consider closing unnecessary applications")
        
        if current['memory']['usage_percent'] > 80:
            recommendations.append("High memory usage detected - consider increasing RAM or closing applications")
        
        if current['disk']['usage_percent'] > 80:
            recommendations.append("Low disk space - consider cleaning up files or expanding storage")
        
        if not recommendations:
            recommendations.append("System health is optimal - no action required")
        
        return recommendations
    
    def export_report(self, filename: Optional[str] = None) -> str:
        """Export health report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        filepath = Path("logs") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        report = self.get_health_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Health report exported to: {filepath}")
        return str(filepath)


def get_system_health() -> Dict[str, Any]:
    """Quick function to get system health"""
    monitor = SystemHealthMonitor()
    return monitor.get_overall_health()


def print_health_status():
    """Print system health status to console"""
    monitor = SystemHealthMonitor()
    health = monitor.get_overall_health()
    
    print("="*70)
    print("  AirOne Professional v4.0 - System Health Status")
    print("="*70)
    print()
    print(f"Overall Status: {health['overall_status']}")
    print(f"Health Score: {health['health_score']}/100")
    print()
    print(f"CPU: {health['cpu']['usage_percent']:.1f}% ({health['cpu']['status']})")
    print(f"Memory: {health['memory']['usage_percent']:.1f}% ({health['memory']['status']})")
    print(f"Disk: {health['disk']['usage_percent']:.1f}% ({health['disk']['status']})")
    print()
    print("="*70)


if __name__ == "__main__":
    print_health_status()
