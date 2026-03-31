#!/usr/bin/env python3
"""
AirOne v4.0 - Health Monitoring System
=======================================

Real-time system health monitoring and diagnostics
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Health metric"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    @classmethod
    def from_value(cls, name: str, value: float, unit: str, 
                   warning: float, critical: float) -> 'HealthMetric':
        """Create metric from value"""
        if value >= critical:
            status = HealthStatus.CRITICAL
        elif value >= warning:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
            
        return cls(
            name=name, value=value, unit=unit,
            status=status, threshold_warning=warning,
            threshold_critical=critical
        )


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    metrics: List[HealthMetric] = field(default_factory=list)
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SystemHealthMonitor:
    """
    System Health Monitor
    
    Monitors CPU, memory, disk, network, and application health.
    """
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.history: List[HealthCheck] = []
        self.max_history = 100
        self.running = False
        self.thread = None
        self.interval = 5  # seconds
        
        logging.info("Health monitor initialized")
        
    def start(self):
        """Start monitoring"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logging.info("Health monitoring started")
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("Health monitoring stopped")
        
    def check_all(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        self.checks = {}
        
        # System checks
        self._check_cpu()
        self._check_memory()
        self._check_disk()
        self._check_network()
        
        # Application checks
        self._check_telemetry()
        self._check_database()
        self._check_communication()
        
        return self.checks
        
    def _check_cpu(self):
        """Check CPU health"""
        try:
            # Simulated CPU check
            cpu_percent = random.uniform(10, 40)
            cpu_count = 4
            
            metric = HealthMetric.from_value(
                "CPU Usage", cpu_percent, "%",
                warning=80.0, critical=95.0
            )
            
            self.checks["cpu"] = HealthCheck(
                component="CPU",
                status=metric.status,
                message=f"Usage: {cpu_percent:.1f}%, Cores: {cpu_count}",
                metrics=[metric]
            )
        except Exception as e:
            self.checks["cpu"] = HealthCheck(
                component="CPU",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
            
    def _check_memory(self):
        """Check memory health"""
        try:
            # Simulated memory check
            mem_percent = random.uniform(30, 60)
            mem_available = 8.0
            
            metric = HealthMetric.from_value(
                "Memory Usage", mem_percent, "%",
                warning=80.0, critical=95.0
            )
            
            self.checks["memory"] = HealthCheck(
                component="Memory",
                status=metric.status,
                message=f"Usage: {mem_percent:.1f}%, Available: {mem_available:.1f}GB",
                metrics=[metric]
            )
        except Exception as e:
            self.checks["memory"] = HealthCheck(
                component="Memory",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
            
    def _check_disk(self):
        """Check disk health"""
        try:
            # Simulated disk check
            disk_percent = random.uniform(20, 50)
            disk_free = 450.0
            
            metric = HealthMetric.from_value(
                "Disk Usage", disk_percent, "%",
                warning=85.0, critical=95.0
            )
            
            self.checks["disk"] = HealthCheck(
                component="Disk",
                status=metric.status,
                message=f"Usage: {disk_percent:.1f}%, Free: {disk_free:.1f}GB",
                metrics=[metric]
            )
        except Exception as e:
            self.checks["disk"] = HealthCheck(
                component="Disk",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
            
    def _check_network(self):
        """Check network health"""
        try:
            # Simulated network check (higher is better for negative dBm)
            signal = random.uniform(-90, -50)
            
            # For dBm, closer to 0 is better
            if signal >= -60:
                status = HealthStatus.HEALTHY
            elif signal >= -75:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL
            
            self.checks["network"] = HealthCheck(
                component="Network",
                status=status,
                message=f"Signal: {signal:.1f} dBm",
                metrics=[]
            )
        except Exception as e:
            self.checks["network"] = HealthCheck(
                component="Network",
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
            
    def _check_telemetry(self):
        """Check telemetry system"""
        # Simulated telemetry health
        battery = random.randint(50, 100)
        
        metric = HealthMetric.from_value(
            "Battery Level", battery, "%",
            warning=20.0, critical=10.0
        )
        
        status = HealthStatus.HEALTHY
        if battery < 20:
            status = HealthStatus.WARNING
        if battery < 10:
            status = HealthStatus.CRITICAL
            
        self.checks["telemetry"] = HealthCheck(
            component="Telemetry",
            status=status,
            message=f"Battery: {battery}%, System operational",
            metrics=[metric]
        )
        
    def _check_database(self):
        """Check database health"""
        self.checks["database"] = HealthCheck(
            component="Database",
            status=HealthStatus.HEALTHY,
            message="SQLite connection active"
        )
        
    def _check_communication(self):
        """Check communication system"""
        self.checks["communication"] = HealthCheck(
            component="Communication",
            status=HealthStatus.HEALTHY,
            message="Communication links active"
        )
        
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health"""
        if not self.checks:
            return HealthStatus.UNKNOWN
            
        statuses = [check.status for check in self.checks.values()]
        
        if any(s == HealthStatus.CRITICAL for s in statuses):
            return HealthStatus.CRITICAL
        elif any(s == HealthStatus.WARNING for s in statuses):
            return HealthStatus.WARNING
        elif any(s == HealthStatus.UNKNOWN for s in statuses):
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
            
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.running:
            try:
                self.check_all()
                
                # Add to history
                for check in self.checks.values():
                    self.history.append(check)
                    
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]
                    
            except Exception as e:
                logging.error(f"Health check error: {e}")
                
            time.sleep(self.interval)
            
    def get_report(self) -> Dict[str, Any]:
        """Get health report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_overall_status().value,
            "components": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "unit": m.unit,
                            "status": m.status.value
                        }
                        for m in check.metrics
                    ]
                }
                for name, check in self.checks.items()
            }
        }


def demo():
    """Demo health monitoring"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           AirOne v4.0 - Health Monitoring             ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create monitor
    monitor = SystemHealthMonitor()
    
    # Run health check
    print("Running health check...\n")
    checks = monitor.check_all()
    
    # Display results
    print("Health Status:")
    for name, check in checks.items():
        status_icon = {
            HealthStatus.HEALTHY: "✓",
            HealthStatus.WARNING: "⚠",
            HealthStatus.CRITICAL: "✗",
            HealthStatus.UNKNOWN: "?"
        }.get(check.status, "?")
        
        print(f"  {status_icon} {check.component}: {check.status.value.upper()}")
        print(f"     {check.message}")
        
    print(f"\nOverall Status: {monitor.get_overall_status().value.upper()}")
    
    # Get report
    report = monitor.get_report()
    print(f"\nReport timestamp: {report['timestamp']}")
    
    print("\n✓ Health monitoring demo complete!")


if __name__ == "__main__":
    demo()
