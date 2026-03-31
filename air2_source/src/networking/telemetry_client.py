
import socket
import threading
import json
import logging
import time
from queue import Queue, Empty
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LiveSocketClient:
    """
    Streams telemetry data to a remote TCP server (e.g., Mission Control dashboard).
    """
    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.queue = Queue()
        self.running = False
        self.socket = None
        self.thread = None
        self.lock = threading.Lock()
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        logger.info(f"Telemetry stream client started ({self.host}:{self.port})")
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self._disconnect()
        
    def send_record(self, record: Any):
        """
        Queue a telemetry record for sending. 
        Accepts dict or object with __dict__.
        """
        try:
            if hasattr(record, '__dict__'):
                data = record.__dict__
            else:
                data = record
            
            # Serialize early to catch errors
            payload = json.dumps(data, default=str).encode('utf-8') + b'\n'
            self.queue.put(payload)
        except Exception as e:
            logger.error(f"Failed to serialize record: {e}")
            
    def _connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            logger.info("Connected to telemetry server")
            return True
        except Exception as e:
            logger.debug(f"Connection failed: {e}")
            return False
            
    def _disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.debug(f"Socket close error: {e}")
            self.socket = None
            
    def _worker(self):
        while self.running:
            # Maintain connection
            if not self.socket:
                if not self._connect():
                    time.sleep(2.0)
                    continue
            
            # Send loop
            try:
                # Get batch of messages
                msg = self.queue.get(timeout=0.5)
                self.socket.sendall(msg)
                
                # Drain queue if we can (to reduce latency)
                while not self.queue.empty():
                    try:
                        msg = self.queue.get_nowait()
                        self.socket.sendall(msg)
                    except Empty:
                        break

            except Empty:
                # No data to send, continue waiting
                continue
            except (ConnectionError, socket.timeout, BrokenPipeError) as e:
                logger.warning(f"Connection lost: {e}")
                self._disconnect()
            except Exception as e:
                logger.error(f"Stream error: {e}")
                self._disconnect()
