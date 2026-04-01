"""
Networking Module - Full Implementation
Network protocols and communication handling
"""

import socket
import threading
import time
import struct
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import deque
import json


class TCPServer:
    """TCP server for commands"""
    
    def __init__(self, port: int = 5001):
        self.port = port
        self.socket = None
        self.running = False
        self.clients = []
        self.callbacks = []
    
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.listen(5)
        self.running = True
        
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
    
    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                self.clients.append(client)
                
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client, addr),
                    daemon=True
                )
                client_thread.start()
            except:
                break
    
    def _handle_client(self, client, addr):
        while self.running:
            try:
                data = client.recv(1024)
                if not data:
                    break
                
                for callback in self.callbacks:
                    callback(data, addr)
            except:
                break
        
        if client in self.clients:
            self.clients.remove(client)
    
    def on_data(self, callback):
        self.callbacks.append(callback)
    
    def broadcast(self, message: str):
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                pass
    
    def stop(self):
        self.running = False
        for client in self.clients:
            client.close()
        if self.socket:
            self.socket.close()


class UDPBroadcaster:
    """UDP broadcaster for telemetry"""
    
    def __init__(self, port: int = 5000):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    def broadcast(self, data: bytes):
        self.socket.sendto(data, ('<broadcast>', self.port))


class ProtocolHandler:
    """Handle custom protocol"""
    
    HEADER = b'\xAA\x55'
    
    @staticmethod
    def encode(data: Dict) -> bytes:
        """Encode data as protocol packet"""
        json_data = json.dumps(data).encode()
        length = len(json_data)
        
        packet = ProtocolHandler.HEADER
        packet += struct.pack('>H', length)
        packet += json_data
        
        # Add checksum
        checksum = hashlib.md5(packet).digest()[:2]
        packet += checksum
        
        return packet
    
    @staticmethod
    def decode(packet: bytes) -> Optional[Dict]:
        """Decode protocol packet"""
        if len(packet) < 6:
            return None
        
        if packet[:2] != ProtocolHandler.HEADER:
            return None
        
        length = struct.unpack('>H', packet[2:4])[0]
        
        if len(packet) < 4 + length + 2:
            return None
        
        json_data = packet[4:4+length]
        received_checksum = packet[4+length:4+length+2]
        
        # Verify checksum
        calculated = hashlib.md5(packet[:4+length]).digest()[:2]
        if received_checksum != calculated:
            return None
        
        try:
            return json.loads(json_data.decode())
        except:
            return None


class PacketQueue:
    """Priority queue for packets"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.queue = deque()
        self.priorities = {'high': 3, 'normal': 2, 'low': 1}
    
    def push(self, packet: Dict, priority: str = 'normal'):
        priority_value = self.priorities.get(priority, 2)
        
        self.queue.append({
            'packet': packet,
            'priority': priority_value,
            'time': time.time()
        })
        
        # Sort by priority
        sorted_queue = sorted(self.queue, key=lambda x: x['priority'], reverse=True)
        self.queue = deque(sorted_queue)
        
        # Remove old if over max
        while len(self.queue) > self.max_size:
            self.queue.pop()
    
    def pop(self) -> Optional[Dict]:
        if self.queue:
            return self.queue.popleft()['packet']
        return None
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def size(self) -> int:
        return len(self.queue)


class ConnectionPool:
    """Pool of network connections"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = {}
        self.connection_id = 0
    
    def add_connection(self, address: Tuple[str, int]) -> int:
        conn_id = self.connection_id
        self.connection_id += 1
        
        self.connections[conn_id] = {
            'address': address,
            'created': time.time(),
            'last_used': time.time(),
            'active': True
        }
        
        return conn_id
    
    def get_connection(self, conn_id: int) -> Optional[Dict]:
        if conn_id in self.connections:
            self.connections[conn_id]['last_used'] = time.time()
            return self.connections[conn_id]
        return None
    
    def remove_connection(self, conn_id: int):
        if conn_id in self.connections:
            del self.connections[conn_id]
    
    def cleanup_old(self, max_age: float = 300):
        """Remove old inactive connections"""
        current_time = time.time()
        to_remove = []
        
        for conn_id, conn in self.connections.items():
            if current_time - conn['last_used'] > max_age:
                to_remove.append(conn_id)
        
        for conn_id in to_remove:
            self.remove_connection(conn_id)


class NetworkDiagnostics:
    """Network diagnostics and testing"""
    
    def __init__(self):
        self.ping_history = deque(maxlen=100)
        self.bandwidth_history = deque(maxlen=100)
    
    def ping(self, host: str, port: int, timeout: float = 1.0) -> Dict:
        """Ping a host"""
        start = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            
            latency = (time.time() - start) * 1000  # ms
            
            self.ping_history.append(latency)
            
            return {
                'success': True,
                'latency_ms': latency,
                'host': host,
                'port': port
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'host': host,
                'port': port
            }
    
    def measure_bandwidth(self, host: str, port: int, 
                         duration: float = 1.0) -> Dict:
        """Measure bandwidth"""
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            # Send data
            data = b'x' * 100000
            start = time.time()
            sent = 0
            
            while time.time() - start < duration:
                sock.send(data)
                sent += len(data)
            
            sock.close()
            
            bandwidth = sent / duration / 1024  # KB/s
            
            self.bandwidth_history.append(bandwidth)
            
            return {
                'bandwidth_kbps': bandwidth,
                'bytes_sent': sent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """Get network statistics"""
        
        if self.ping_history:
            ping_arr = np.array(self.ping_history)
            avg_ping = np.mean(ping_arr)
            min_ping = np.min(ping_arr)
            max_ping = np.max(ping_arr)
        else:
            avg_ping = min_ping = max_ping = 0
        
        if self.bandwidth_history:
            bw_arr = np.array(self.bandwidth_history)
            avg_bw = np.mean(bw_arr)
        else:
            avg_bw = 0
        
        return {
            'ping': {'avg': avg_ping, 'min': min_ping, 'max': max_ping, 'samples': len(self.ping_history)},
            'bandwidth': {'avg_kbps': avg_bw, 'samples': len(self.bandwidth_history)}
        }


class DataLink:
    """Data link layer implementation"""
    
    def __init__(self):
        self.seq_num = 0
        self.ack_num = 0
        self.window_size = 10
        self.unacked = {}
        self.retry_count = 3
        self.timeout = 2.0
    
    def send_frame(self, data: bytes, sock: socket.socket, 
                   addr: Tuple[str, int]) -> bool:
        """Send frame with reliability"""
        
        frame = self._create_frame(data)
        
        try:
            sock.sendto(frame, addr)
            
            self.unacked[self.seq_num] = {
                'data': data,
                'time': time.time(),
                'retries': 0
            }
            
            self.seq_num += 1
            return True
        except:
            return False
    
    def _create_frame(self, data: bytes) -> bytes:
        """Create frame with header and checksum"""
        
        header = struct.pack('>HH', self.seq_num, self.ack_num)
        checksum = hashlib.md5(data).digest()[:4]
        
        return header + checksum + data
    
    def receive_frame(self, frame: bytes) -> Optional[bytes]:
        """Receive and verify frame"""
        
        if len(frame) < 10:
            return None
        
        seq, ack = struct.unpack('>HH', frame[:4])
        checksum = frame[4:8]
        data = frame[8:]
        
        # Verify checksum
        calculated = hashlib.md5(data).digest()[:4]
        if checksum != calculated:
            return None
        
        self.ack_num = seq
        return data


# Example
if __name__ == "__main__":
    # Test protocol
    data = {'altitude': 100, 'temperature': 25}
    encoded = ProtocolHandler.encode(data)
    print(f"Encoded: {len(encoded)} bytes")
    
    decoded = ProtocolHandler.decode(encoded)
    print(f"Decoded: {decoded}")
    
    # Test diagnostics
    diag = NetworkDiagnostics()
    # result = diag.ping('localhost', 5000)
    # print(f"Ping: {result}")