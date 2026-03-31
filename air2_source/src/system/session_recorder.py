"""
Session Recorder System
Records and manages telemetry recording sessions.
"""

from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional
import time

class SessionRecorder:
    def __init__(self):
        self.active = False
        self.session_id = None
        self.session_name = None
        self.start_time = None
        self.packets_logged = 0
        self.packet_buffer = []
        self.max_buffer_size = 10000 # Max in-memory packets

    def start_session(self, name: str) -> str:
        """Start a new recording session"""
        self.active = True
        self.session_name = name
        self.session_id = f"session_{name}_{int(time.time())}"
        self.start_time = datetime.now()
        self.packets_logged = 0
        self.packet_buffer = []
        return self.session_id

    def stop_session(self) -> Dict[str, Any]:
        """Stop the current recording session"""
        self.active = False
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        else:
            duration = 0
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "duration_seconds": duration,
            "packets_logged": self.packets_logged
        }

    def log_packet(self, packet_data: Dict[str, Any]) -> bool:
        """Log a telemetry packet"""
        if not self.active:
            return False
        
        packet_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "data": packet_data
        }
        
        self.packet_buffer.append(packet_with_timestamp)
        self.packets_logged += 1
        
        # Trim buffer if needed
        if len(self.packet_buffer) > self.max_buffer_size:
            self.packet_buffer = self.packet_buffer[-self.max_buffer_size:]
        
        return True

    def get_packets(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get logged packets"""
        if count:
            return self.packet_buffer[-count:]
        return self.packet_buffer

    def get_status(self) -> Dict[str, Any]:
        """Get current recorder status"""
        return {
            "active": self.active,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "packets_logged": self.packets_logged,
            "buffer_size": len(self.packet_buffer)
        }
