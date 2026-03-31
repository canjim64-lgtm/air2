"""
Over-The-Air (OTA) Firmware Update Manager for AirOne Professional v4.0
Integrated firmware chunking and stateful retransmission logic.
"""
import logging
import hashlib
import os
import math
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class OTAUpdateManager:
    def __init__(self, chunk_size: int = 256):
        self.logger = logging.getLogger(f"{__name__}.OTAUpdateManager")
        self.chunk_size = chunk_size
        self.firmware_path = ""
        self.total_chunks = 0
        self.current_chunk = 0
        self.in_progress = False
        self.firmware_hash = ""
        self.logger.info(f"OTA Manager Ready. Chunk size: {chunk_size}B.")

    def load_firmware(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            self.logger.error(f"Binary not found: {filepath}")
            return False
            
        f_size = os.path.getsize(filepath)
        self.firmware_path = filepath
        self.total_chunks = math.ceil(f_size / self.chunk_size)
        
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192): hasher.update(chunk)
        self.firmware_hash = hasher.hexdigest()
        
        self.logger.info(f"Loaded firmware: {filepath} ({f_size}B). Hash: {self.firmware_hash[:16]}...")
        return True

    def start_update(self) -> Dict[str, Any]:
        if not self.firmware_path: return {"status": "error", "message": "No binary loaded"}
        self.in_progress = True
        self.current_chunk = 0
        return {"status": "started", "total_chunks": self.total_chunks, "hash": self.firmware_hash}

    def get_next_chunk(self) -> Dict[str, Any]:
        if not self.in_progress: return {"status": "idle"}
        if self.current_chunk >= self.total_chunks:
            self.in_progress = False
            return {"status": "complete"}
            
        with open(self.firmware_path, 'rb') as f:
            f.seek(self.current_chunk * self.chunk_size)
            data = f.read(self.chunk_size)
            
        return {
            "status": "transmitting",
            "index": self.current_chunk,
            "data_hex": data.hex(),
            "progress": round((self.current_chunk / self.total_chunks) * 100, 1)
        }

    def handle_ack(self, index: int, success: bool):
        """Standard ARQ (Automatic Repeat Request) logic."""
        if success:
            if index == self.current_chunk:
                self.current_chunk += 1
                self.logger.debug(f"ACK {index} received.")
        else:
            self.logger.warning(f"NACK {index} received. Retrying chunk.")
            # current_chunk remains the same, forcing get_next_chunk to repeat it
