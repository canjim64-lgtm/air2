"""
Communication Manager Module for AirOne Professional
Manages communication sessions and connections
"""

import time
import threading
import queue
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
import json
import random # Needed for simulated network behavior

from .protocol import CommunicationPacket, ProtocolHandler, create_protocol_handler


logger = logging.getLogger(__name__)

class SimulatedNetworkInterface:
    """Simulates a network connection (TCP/UDP socket or serial port)."""
    def __init__(self, host: str, port: int, connection_type: str = "tcp"):
        self.host = host
        self.port = port
        self.connection_type = connection_type
        self.is_connected = False
        self.data_buffer = queue.Queue(maxsize=100) # Simulate incoming data buffer
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self, timeout: float = 5.0) -> bool:
        self.logger.info(f"Simulating {self.connection_type} connection to {self.host}:{self.port}...")
        time.sleep(random.uniform(0.1, 0.5)) # Simulate connection latency
        if random.random() < 0.9: # 90% success rate
            self.is_connected = True
            self.logger.info("Simulated connection successful.")
            return True
        self.logger.warning("Simulated connection failed.")
        return False

    def disconnect(self) -> bool:
        if self.is_connected:
            self.logger.info(f"Simulating disconnection from {self.host}:{self.port}.")
            self.is_connected = False
            # Clear any pending data
            while not self.data_buffer.empty():
                self.data_buffer.get_nowait()
            return True
        return False

    def send_data(self, data: bytes) -> bool:
        if not self.is_connected:
            self.logger.warning("Attempted to send data while disconnected.")
            return False
        self.logger.debug(f"Simulating sending {len(data)} bytes to {self.host}:{self.port}.")
        time.sleep(random.uniform(0.001, 0.01)) # Simulate transmission delay
        
        # Simulate data being received by the other end (e.g., echo back or internal processing)
        # For simplicity, we'll just log it. In a real sim, it might go to another buffer.
        return True

    def receive_data(self) -> Optional[bytes]:
        if not self.is_connected:
            return None
        try:
            # Simulate some data always being available if connected, for testing loops
            if random.random() < 0.5 and self.data_buffer.empty(): # Simulate external incoming data
                 simulated_incoming = b"simulated_data_" + os.urandom(random.randint(10, 50))
                 self.data_buffer.put_nowait(simulated_incoming)

            data = self.data_buffer.get(timeout=0.1) # Non-blocking for loop performance
            self.logger.debug(f"Simulating receiving {len(data)} bytes from {self.host}:{self.port}.")
            return data
        except queue.Empty:
            return None
        except Exception as e:
            self.logger.error(f"Simulated receive error: {e}")
            return None


class ConnectionManager:
    """Manages network connections"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.network_interfaces: Dict[str, SimulatedNetworkInterface] = {}
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def connect(self, host: str, port: int, connection_type: str = "tcp", timeout: float = 5.0) -> bool:
        """Establish a connection"""
        connection_id = f"{host}:{port}:{connection_type}"
        
        if connection_id in self.network_interfaces and self.network_interfaces[connection_id].is_connected:
            self.logger.info(f"Already connected to {host}:{port}.")
            return True

        interface = SimulatedNetworkInterface(host, port, connection_type)
        if interface.connect(timeout):
            self.network_interfaces[connection_id] = interface
            self.connections[connection_id] = {
                'host': host,
                'port': port,
                'connected_at': datetime.now(),
                'last_activity': datetime.now(),
                'status': 'connected',
                'connection_type': connection_type
            }
            self.logger.info(f"Connected to {host}:{port} ({connection_type}).")
            return True
        self.logger.warning(f"Failed to connect to {host}:{port} ({connection_type}).")
        return False
    
    def disconnect(self, host: str, port: int, connection_type: str = "tcp") -> bool:
        """Close a connection"""
        connection_id = f"{host}:{port}:{connection_type}"
        
        if connection_id in self.network_interfaces:
            if self.network_interfaces[connection_id].disconnect():
                del self.network_interfaces[connection_id]
                if connection_id in self.connections:
                    del self.connections[connection_id]
                self.logger.info(f"Disconnected from {host}:{port} ({connection_type}).")
                return True
        return False
    
    def send_data(self, host: str, port: int, connection_type: str, data: bytes) -> bool:
        """Send raw data through a connection"""
        connection_id = f"{host}:{port}:{connection_type}"
        interface = self.network_interfaces.get(connection_id)
        if interface and interface.is_connected:
            return interface.send_data(data)
        self.logger.warning(f"No active connection to {host}:{port} to send data.")
        return False

    def receive_data(self, host: str, port: int, connection_type: str) -> Optional[bytes]:
        """Receive raw data from a connection"""
        connection_id = f"{host}:{port}:{connection_type}"
        interface = self.network_interfaces.get(connection_id)
        if interface and interface.is_connected:
            return interface.receive_data()
        return None

    def get_connection_status(self, host: str, port: int, connection_type: str = "tcp") -> Dict[str, Any]:
        """Get status of a connection"""
        connection_id = f"{host}:{port}:{connection_type}"
        status = self.connections.get(connection_id, {'status': 'not_connected'})
        status['is_connected_interface'] = self.network_interfaces[connection_id].is_connected if connection_id in self.network_interfaces else False
        return status
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all active connections"""
        return list(self.connections.values())


class CommunicationManager:
    """Manages all communication for AirOne system"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.protocol_handlers: Dict[str, ProtocolHandler] = {}
        self.message_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.running = False
        self.connected = False # Refers to global communication status
        self.last_activity: Optional[datetime] = None
        self.statistics = {
            'packets_sent': 0,
            'packets_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'errors': 0
        }
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def initialize(self) -> bool:
        """Initialize communication manager"""
        self.running = True
        
        # Create default protocol handlers
        for protocol_type in ['telemetry', 'command', 'default']:
            self.protocol_handlers[protocol_type] = create_protocol_handler(protocol_type)
            self.protocol_handlers[protocol_type].initialize()
        
        self.logger.info("Communication manager initialized")
        return True
    
    def start(self):
        """Start communication manager"""
        if self.running:
            self.logger.warning("Communication manager already running.")
            return
        
        self.running = True
        self.connection_manager.running = True # Indicate ConnectionManager is also active
        self._start_background_threads()
        self.logger.info("Communication manager started.")
    
    def stop(self):
        """Stop communication manager"""
        if not self.running:
            self.logger.warning("Communication manager not running.")
            return
        
        self.running = False
        self.connected = False
        self.connection_manager.running = False # Indicate ConnectionManager is also inactive
        
        # Disconnect all active connections
        for conn_id in list(self.connection_manager.connections.keys()):
            host, port_str, conn_type = conn_id.split(':')
            self.connection_manager.disconnect(host, int(port_str), conn_type)

        self.logger.info("Communication manager stopped.")
    
    def _start_background_threads(self):
        """Start background processing threads"""
        def process_queue():
            while self.running:
                try:
                    message = self.message_queue.get(timeout=1)
                    self._process_message(message)
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    self.statistics['errors'] += 1

        def receive_loop():
            while self.running:
                # Iterate over all active connections to receive data
                for conn_id, conn_info in list(self.connection_manager.connections.items()):
                    host, port_str, conn_type = conn_id.split(':')
                    data = self.connection_manager.receive_data(host, int(port_str), conn_type)
                    if data:
                        # Attempt to decode and queue the received data as a message
                        try:
                            # Assume 'default' protocol for incoming raw bytes.
                            # In a real system, you might inspect data to determine protocol.
                            packet = self.receive_packet(data, packet_type='default') 
                            if packet:
                                self.queue_message({'type': packet.packet_type, 'data': packet.to_dict()})
                        except Exception as e:
                            self.logger.error(f"Error decoding or queuing received raw data: {e}")
                time.sleep(0.01) # Small delay to prevent busy-waiting

        thread_queue = threading.Thread(target=process_queue, daemon=True)
        thread_queue.start()
        self.background_threads.append(thread_queue)

        thread_receive = threading.Thread(target=receive_loop, daemon=True)
        thread_receive.start()
        self.background_threads.append(thread_receive)

    def _process_message(self, message: Dict[str, Any]):
        """Process a message from the queue"""
        self.last_activity = datetime.now()
        message_type = message.get('type', 'unknown')

        if message_type in self.protocol_handlers:
            handler = self.protocol_handlers[message_type]
            try:
                # ProtocolHandler.process is the general method for handling messages
                handler.process(message.get('data', {}))
            except Exception as e:
                self.logger.error(f"Error processing {message_type} message: {e}")
                self.statistics['errors'] += 1
        else:
            self.logger.warning(f"No handler for message type: {message_type}")
    
    def send_packet(self, packet: CommunicationPacket, host: str, port: int, connection_type: str = "tcp") -> bool:
        """Send a communication packet over a specific connection."""
        if not self.running:
            self.logger.warning("Communication manager not running.")
            return False
        
        try:
            handler = self.protocol_handlers.get(packet.packet_type, self.protocol_handlers['default'])
            encoded = handler.encode(packet.to_dict())
            
            if self.connection_manager.send_data(host, port, connection_type, encoded):
                self.statistics['packets_sent'] += 1
                self.statistics['bytes_sent'] += len(encoded)
                self.last_activity = datetime.now()
                self.logger.debug(f"Packet {packet.packet_id} sent via {host}:{port}.")
                return True
            else:
                self.logger.warning(f"Failed to send packet {packet.packet_id} - connection not active.")
                self.statistics['errors'] += 1
                return False
            
        except Exception as e:
            self.logger.error(f"Error sending packet {packet.packet_id}: {e}")
            self.statistics['errors'] += 1
            return False
    
    def receive_packet(self, raw_data: bytes, packet_type: str = 'default') -> Optional[CommunicationPacket]:
        """Decode raw data into a CommunicationPacket."""
        if not self.running:
            return None
        
        try:
            handler = self.protocol_handlers.get(packet_type, self.protocol_handlers['default'])
            packet_dict = handler.decode(raw_data)
            
            # Check if decoding was successful and data is valid
            if packet_dict and 'packet_id' in packet_dict:
                packet = CommunicationPacket.from_dict(packet_dict)
                self.statistics['packets_received'] += 1
                self.statistics['bytes_received'] += len(raw_data)
                self.last_activity = datetime.now()
                return packet
            else:
                self.logger.warning("Received data could not be decoded into a valid CommunicationPacket.")
                self.statistics['errors'] += 1
                return None
            
        except Exception as e:
            self.logger.error(f"Error decoding received data: {e}")
            self.statistics['errors'] += 1
            return None
    
    def queue_message(self, message: Dict[str, Any]):
        """Add a message to the processing queue"""
        try:
            self.message_queue.put_nowait(message)
        except queue.Full:
            self.logger.warning("Message queue full, dropping message.")
            self.statistics['errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get communication manager status"""
        return {
            'running': self.running,
            'global_connected': self.connected, # Indicates if any connection is active
            'active_sessions': len(self.sessions),
            'protocol_handlers': list(self.protocol_handlers.keys()),
            'message_queue_size': self.message_queue.qsize(),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'statistics': self.statistics,
            'network_connections': self.connection_manager.get_all_connections()
        }
    
    def create_session(self, session_name: str, config: Dict[str, Any] = None) -> str:
        """Create a new communication session"""
        session_id = f"session_{session_name}_{int(time.time())}"
        
        self.sessions[session_id] = {
            'name': session_name,
            'config': config or {},
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'packets_exchanged': 0
        }
        
        self.logger.info(f"Created session: {session_id}.")
        return session_id
    
    def close_session(self, session_id: str) -> bool:
        """Close a communication session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Closed session: {session_id}.")
            return True
        self.logger.warning(f"Session {session_id} not found.")
        return False


def create_communication_manager(connection_manager: Optional[ConnectionManager] = None) -> CommunicationManager:
    """Factory function to create communication manager"""
    if connection_manager is None:
        connection_manager = ConnectionManager() # Create default if not provided
    return CommunicationManager(connection_manager)

