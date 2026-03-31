"""
Diagnostics Service
Provides comprehensive system diagnostics and health checks.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class DiagnosticsService:
    def __init__(self, ml_engine=None, power_monitor=None, hardware_manager=None):
        self.ml_engine = ml_engine
        self.power_monitor = power_monitor
        self.hardware_manager = hardware_manager # This will likely be from src/hardware/hardware_interface.py
        self.last_diagnostic_time: Optional[datetime] = None
        self.diagnostic_history: List[Dict[str, Any]] = []
        self.max_history_length = 50

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics"""
        self.last_diagnostic_time = datetime.now()
        
        diagnostics = {
            "timestamp": self.last_diagnostic_time.isoformat(),
            "status": "ok",
            "components": {},
            "issues": []
        }
        
        # Check ML engine
        if self.ml_engine:
            try:
                # Assuming ml_engine has a get_system_status method
                ml_status = self.ml_engine.get_system_status()
                diagnostics["components"]["ml_engine"] = ml_status
                if ml_status.get("status") == "degraded" or ml_status.get("errors", 0) > 0:
                    diagnostics["issues"].append("ML engine reported issues")
            except Exception as e:
                diagnostics["components"]["ml_engine"] = {"status": "error", "error": str(e)}
                diagnostics["issues"].append(f"ML engine diagnostic failed: {e}")
        else:
            diagnostics["components"]["ml_engine"] = {"status": "unavailable"}

        # Check power monitor
        if self.power_monitor:
            try:
                power_status = self.power_monitor.get_status()
                diagnostics["components"]["power"] = power_status
                if power_status.get("warnings"):
                    diagnostics["issues"].extend([w["message"] for w in power_status["warnings"][-3:]])
            except Exception as e:
                diagnostics["components"]["power"] = {"status": "error", "error": str(e)}
                diagnostics["issues"].append(f"Power monitor diagnostic failed: {e}")
        else:
            diagnostics["components"]["power"] = {"status": "unavailable"}
        
        # Check hardware manager
        if self.hardware_manager:
            try:
                # Assuming hardware_manager has a get_status method
                hw_status = self.hardware_manager.get_status()
                diagnostics["components"]["hardware"] = hw_status
                if hw_status.get("status") == "faulty" or hw_status.get("errors", 0) > 0:
                     diagnostics["issues"].append("Hardware reported issues")
            except Exception as e:
                diagnostics["components"]["hardware"] = {"status": "error", "error": str(e)}
                diagnostics["issues"].append(f"Hardware manager diagnostic failed: {e}")
        else:
            diagnostics["components"]["hardware"] = {"status": "unavailable", "note": "Hardware manager not provided"}
        
        # Overall status
        if diagnostics["issues"]:
            diagnostics["status"] = "degraded"
        
        self.diagnostic_history.append(diagnostics)
        self.diagnostic_history = self.diagnostic_history[-self.max_history_length:] # Keep history limited
        
        return diagnostics

    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run a full system diagnostic"""
        return self.get_diagnostics()

    def get_diagnostic_history(self) -> List[Dict[str, Any]]:
        """Get recent diagnostic history"""
        return self.diagnostic_history
