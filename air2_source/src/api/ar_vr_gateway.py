"""
AR/VR Telemetry Gateway for AirOne Professional v4.0
Integrated real-time WebSocket and raw TCP streaming for 3D headsets.
"""
import logging
import json
import threading
import time
import socket
import asyncio
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)

class ARVRGateway:
    def __init__(self, port: int = 8081):
        self.logger = logging.getLogger(f"{__name__}.ARVRGateway")
        self.port = port
        self.clients: Set[Any] = set()
        self.loop = None
        self.is_running = False
        self.use_websockets = False
        self.server_thread = None
        self.logger.info(f"AR/VR Telemetry Gateway Initialized on port {self.port}.")

    def start(self):
        try:
            import websockets
            self.use_websockets = True
            self.server_thread = threading.Thread(target=self._run_websocket_server)
        except ImportError:
            self.logger.warning("websockets module not installed. Using raw TCP streaming.")
            self.server_thread = threading.Thread(target=self._run_raw_tcp_server)
            
        self.server_thread.daemon = True
        self.server_thread.start()

    def _run_websocket_server(self):
        import websockets
        async def handler(ws, path):
            self.clients.add(ws)
            try:
                await ws.wait_closed()
            finally:
                self.clients.remove(ws)
            
        async def serve():
            self.loop = asyncio.get_running_loop()
            async with websockets.serve(handler, "0.0.0.0", self.port):
                self.is_running = True
                await asyncio.Future()

        asyncio.run(serve())

    def _run_raw_tcp_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(5)
        self.is_running = True
        
        while True:
            client, addr = server.accept()
            self.clients.add(client)
            self.logger.info(f"AR/VR Client connected via TCP: {addr}")

    def broadcast_telemetry(self, data: Dict[str, Any]):
        """Broadcasts a telemetry frame specifically formatted for 3D engines."""
        if not self.is_running or not self.clients:
            return
            
        payload = json.dumps({
            "spatial": {
                "x": float(data.get('x', 0.0)),
                "y": float(data.get('y', 0.0)),
                "z": float(data.get('altitude', 0.0))
            },
            "rotation": {
                "pitch": float(data.get('pitch', 0.0)),
                "yaw": float(data.get('yaw', 0.0)),
                "roll": float(data.get('roll', 0.0))
            },
            "environment": {
                "temp": float(data.get('temperature', 0.0)),
                "pressure": float(data.get('pressure', 0.0))
            },
            "timestamp": time.time()
        })
        
        if self.use_websockets and self.loop:
            import websockets
            # Thread-safe broadcast to the event loop
            for ws in list(self.clients):
                self.loop.call_soon_threadsafe(
                    lambda w=ws: asyncio.create_task(self._safe_ws_send(w, payload))
                )
        else:
            disconnected = set()
            for client in list(self.clients):
                try:
                    client.send((payload + "\n").encode('utf-8'))
                except:
                    disconnected.add(client)
            self.clients -= disconnected

    async def _safe_ws_send(self, ws, message):
        try:
            await ws.send(message)
        except:
            if ws in self.clients:
                self.clients.remove(ws)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gateway = ARVRGateway()
    gateway.start()
    while True:
        gateway.broadcast_telemetry({"altitude": 100.0, "pitch": 5.0})
        time.sleep(1)
