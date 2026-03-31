"""
Real-Time Data Streaming Module
High-performance streaming and processing for telemetry data
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
import time
import logging
from collections import deque
from circular_buffer import CircularBuffer


class StreamType(Enum):
    """Stream types"""
    TELEMETRY = "telemetry"
    SDR = "sdr"
    SENSOR = "sensor"
    EVENT = "event"


class StreamStatus(Enum):
    """Stream status"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class DataPacket:
    """Data packet for streaming"""
    stream_id: str
    timestamp: float
    data: Any
    sequence: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircularBuffer:
    """Fixed-size circular buffer for streaming"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.tail = 0
        self.count = 0
        self.lock = threading.Lock()
    
    def put(self, item: Any):
        """Add item to buffer"""
        with self.lock:
            self.buffer[self.tail] = item
            self.tail = (self.tail + 1) % self.capacity
            
            if self.count < self.capacity:
                self.count += 1
            else:
                self.head = (self.head + 1) % self.capacity
    
    def get(self) -> Optional[Any]:
        """Get item from buffer"""
        with self.lock:
            if self.count == 0:
                return None
            
            item = self.buffer[self.head]
            self.head = (self.head + 1) % self.capacity
            self.count -= 1
            
            return item
    
    def get_all(self) -> List[Any]:
        """Get all items"""
        with self.lock:
            if self.count == 0:
                return []
            
            items = []
            idx = self.head
            
            for _ in range(self.count):
                items.append(self.buffer[idx])
                idx = (idx + 1) % self.capacity
            
            return items
    
    def __len__(self):
        return self.count


class StreamSource:
    """Base class for stream sources"""
    
    def __init__(self, stream_id: str, stream_type: StreamType):
        self.stream_id = stream_id
        self.stream_type = stream_type
        self.status = StreamStatus.IDLE
        self.listeners: List[Callable] = []
        
        self.packet_count = 0
        self.error_count = 0
        
    def add_listener(self, callback: Callable):
        """Add data listener"""
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def notify_listeners(self, packet: DataPacket):
        """Notify all listeners"""
        for listener in self.listeners:
            try:
                listener(packet)
            except Exception as e:
                logging.error(f"Listener error: {e}")
                self.error_count += 1
    
    def start(self):
        """Start streaming"""
        self.status = StreamStatus.CONNECTED
        
    def stop(self):
        """Stop streaming"""
        self.status = StreamStatus.IDLE


class TelemetryStreamSource(StreamSource):
    """Telemetry data stream source"""
    
    def __init__(self, stream_id: str = "telemetry"):
        super().__init__(stream_id, StreamType.TELEMETRY)
        
        self.rate = 1.0  # Hz
        self.active = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start telemetry stream"""
        super().start()
        self.active = True
        
        self.thread = threading.Thread(target=self._generate_data, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop telemetry stream"""
        self.active = False
        super().stop()
        
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _generate_data(self):
        """Generate simulated telemetry data"""
        while self.active:
            # Generate telemetry packet
            packet = DataPacket(
                stream_id=self.stream_id,
                timestamp=time.time(),
                data={
                    'altitude': np.random.uniform(1000, 5000),
                    'velocity': np.random.uniform(0, 100),
                    'temperature': np.random.uniform(20, 30),
                    'pressure': np.random.uniform(90000, 110000),
                    'battery_voltage': np.random.uniform(11, 13)
                },
                sequence=self.packet_count
            )
            
            self.packet_count += 1
            self.notify_listeners(packet)
            
            time.sleep(1.0 / self.rate)


class SDRStreamSource(StreamSource):
    """SDR data stream source"""
    
    def __init__(self, stream_id: str = "sdr", sample_rate: float = 2.4e6):
        super().__init__(stream_id, StreamType.SDR)
        
        self.sample_rate = sample_rate
        self.buffer_size = 1024
        self.active = False
        
    def start(self):
        """Start SDR stream"""
        super().start()
        self.active = True
        
        self.thread = threading.Thread(target=self._generate_samples, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop SDR stream"""
        self.active = False
        super().stop()
        
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _generate_samples(self):
        """Generate SDR samples"""
        while self.active:
            # Generate IQ samples
            i = np.random.randn(self.buffer_size)
            q = np.random.randn(self.buffer_size)
            
            packet = DataPacket(
                stream_id=self.stream_id,
                timestamp=time.time(),
                data={'i': i, 'q': q},
                sequence=self.packet_count,
                metadata={'sample_rate': self.sample_rate}
            )
            
            self.packet_count += 1
            self.notify_listeners(packet)
            
            time.sleep(self.buffer_size / self.sample_rate)


class StreamProcessor:
    """Process streaming data"""
    
    def __init__(self):
        self.processors: Dict[str, Callable] = {}
        self.output_queues: Dict[str, queue.Queue] = {}
        
    def register_processor(self, stream_id: str, processor: Callable,
                          output_queue: Optional[queue.Queue] = None):
        """Register processor for stream"""
        self.processors[stream_id] = processor
        
        if output_queue:
            self.output_queues[stream_id] = output_queue
    
    def process_packet(self, packet: DataPacket) -> Optional[Any]:
        """Process single packet"""
        
        if packet.stream_id in self.processors:
            processor = self.processors[packet.stream_id]
            result = processor(packet.data, packet)
            
            if packet.stream_id in self.output_queues:
                self.output_queues[packet.stream_id].put(result)
            
            return result
        
        return None
    
    def process_batch(self, packets: List[DataPacket]) -> List[Any]:
        """Process batch of packets"""
        
        results = []
        
        for packet in packets:
            result = self.process_packet(packet)
            if result:
                results.append(result)
        
        return results


class StreamAggregator:
    """Aggregate data from multiple streams"""
    
    def __init__(self, window_size: float = 1.0):
        self.window_size = window_size
        self.streams: Dict[str, CircularBuffer] = {}
        self.lock = threading.Lock()
        
        self.aggregators: Dict[str, Callable] = {}
        
    def add_stream(self, stream_id: str):
        """Add stream to aggregator"""
        with self.lock:
            self.streams[stream_id] = CircularBuffer(capacity=int(self.window_size * 100))
    
    def add_stream_packet(self, stream_id: str, packet: DataPacket):
        """Add packet to stream buffer"""
        with self.lock:
            if stream_id not in self.streams:
                self.add_stream(stream_id)
            
            self.streams[stream_id].put(packet)
    
    def get_aggregated(self, stream_id: str) -> Dict[str, Any]:
        """Get aggregated data for stream"""
        
        with self.lock:
            if stream_id not in self.streams:
                return {}
            
            packets = self.streams[stream_id].get_all()
            
            if not packets:
                return {}
            
            # Aggregate based on stream type
            if stream_id == 'telemetry':
                return self._aggregate_telemetry(packets)
            elif stream_id == 'sdr':
                return self._aggregate_sdr(packets)
            
            return {'count': len(packets)}
    
    def _aggregate_telemetry(self, packets: List[DataPacket]) -> Dict[str, Any]:
        """Aggregate telemetry data"""
        
        # Extract data
        altitudes = [p.data.get('altitude', 0) for p in packets]
        velocities = [p.data.get('velocity', 0) for p in packets]
        temps = [p.data.get('temperature', 0) for p in packets]
        
        return {
            'count': len(packets),
            'altitude': {
                'mean': np.mean(altitudes),
                'std': np.std(altitudes),
                'min': np.min(altitudes),
                'max': np.max(altitudes)
            },
            'velocity': {
                'mean': np.mean(velocities),
                'std': np.std(velocities)
            },
            'temperature': {
                'mean': np.mean(temps),
                'std': np.std(temps)
            }
        }
    
    def _aggregate_sdr(self, packets: List[DataPacket]) -> Dict[str, Any]:
        """Aggregate SDR data"""
        
        i_vals = []
        q_vals = []
        
        for p in packets:
            i_vals.extend(p.data.get('i', []))
            q_vals.extend(p.data.get('q', []))
        
        i_arr = np.array(i_vals)
        q_arr = np.array(q_vals)
        
        complex_signal = i_arr + 1j * q_arr
        
        return {
            'count': len(packets),
            'power': float(np.mean(np.abs(complex_signal)**2)),
            'samples': len(i_vals)
        }


class StreamBuffer:
    """Buffer for managing stream data"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffers: Dict[str, CircularBuffer] = {}
        
    def add_stream(self, stream_id: str):
        """Add stream buffer"""
        self.buffers[stream_id] = CircularBuffer(self.max_size)
    
    def push(self, stream_id: str, data: Any):
        """Push data to stream buffer"""
        
        if stream_id not in self.buffers:
            self.add_stream(stream_id)
        
        self.buffers[stream_id].put(data)
    
    def get_latest(self, stream_id: str, n: int = 1) -> List[Any]:
        """Get latest n items"""
        
        if stream_id not in self.buffers:
            return []
        
        items = self.buffers[stream_id].get_all()
        return items[-n:] if len(items) >= n else items
    
    def get_range(self, stream_id: str, 
                  start_time: float, end_time: float) -> List[Any]:
        """Get items in time range"""
        
        if stream_id not in self.buffers:
            return []
        
        items = self.buffers[stream_id].get_all()
        
        return [p for p in items 
                if start_time <= p.timestamp <= end_time]


class RealTimeProcessor:
    """Real-time processing system"""
    
    def __init__(self):
        self.sources: Dict[str, StreamSource] = {}
        self.processor = StreamProcessor()
        self.aggregator = StreamAggregator()
        self.buffer = StreamBuffer()
        
        self.running = False
        
        # Statistics
        self.total_processed = 0
        self.total_errors = 0
        
    def add_source(self, source: StreamSource):
        """Add stream source"""
        self.sources[source.stream_id] = source
        self.aggregator.add_stream(source.stream_id)
        self.buffer.add_stream(source.stream_id)
        
        # Add listener
        def on_data(packet):
            self.processor.process_packet(packet)
            self.aggregator.add_stream_packet(packet.stream_id, packet)
            self.buffer.push(packet.stream_id, packet)
            self.total_processed += 1
        
        source.add_listener(on_data)
    
    def register_processor(self, stream_id: str, processor: Callable):
        """Register processor for stream"""
        self.processor.register_processor(stream_id, processor)
    
    def start(self):
        """Start all streams"""
        self.running = True
        
        for source in self.sources.values():
            source.start()
            
        logging.info(f"Started {len(self.sources)} streams")
    
    def stop(self):
        """Stop all streams"""
        self.running = False
        
        for source in self.sources.values():
            source.stop()
            
        logging.info("Stopped all streams")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        
        stream_stats = {}
        
        for stream_id, buffer in self.buffer.buffers.items():
            stream_stats[stream_id] = {
                'buffer_size': len(buffer),
                'packets': buffer.count
            }
        
        # Aggregated data
        aggregated = {}
        for stream_id in self.sources.keys():
            agg = self.aggregator.get_aggregated(stream_id)
            if agg:
                aggregated[stream_id] = agg
        
        return {
            'total_processed': self.total_processed,
            'total_errors': self.total_errors,
            'active_streams': len(self.sources),
            'stream_stats': stream_stats,
            'aggregated': aggregated
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Real-Time Data Streaming...")
    
    # Test Stream Source
    print("\n1. Testing Telemetry Stream Source...")
    source = TelemetryStreamSource("telemetry")
    source.rate = 10  # 10 Hz
    
    received = []
    source.add_listener(lambda p: received.append(p))
    
    source.start()
    time.sleep(0.5)
    source.stop()
    
    print(f"   Received {len(received)} packets")
    
    # Test Processor
    print("\n2. Testing Stream Processor...")
    processor = StreamProcessor()
    
    def process_fn(data, packet):
        return {'processed': True, 'value': data.get('altitude', 0) * 2}
    
    processor.register_processor('telemetry', process_fn)
    
    # Test Aggregator
    print("\n3. Testing Stream Aggregator...")
    aggregator = StreamAggregator(window_size=1.0)
    
    for i in range(10):
        packet = DataPacket(
            stream_id='telemetry',
            timestamp=time.time(),
            data={'altitude': 1000 + i * 10},
            sequence=i
        )
        aggregator.add_stream_packet('telemetry', packet)
    
    agg_result = aggregator.get_aggregated('telemetry')
    print(f"   Aggregated: {agg_result.get('count', 0)} packets")
    
    # Test Complete System
    print("\n4. Testing Complete Real-Time Processor...")
    rt_processor = RealTimeProcessor()
    
    tel_source = TelemetryStreamSource('telemetry')
    rt_processor.add_source(tel_source)
    
    # Register processor
    rt_processor.register_processor('telemetry', 
                                   lambda d, p: {'altitude': d.get('altitude', 0)})
    
    rt_processor.start()
    time.sleep(1.0)
    rt_processor.stop()
    
    stats = rt_processor.get_statistics()
    print(f"   Processed: {stats['total_processed']} packets")
    print(f"   Streams: {stats['active_streams']}")
    
    print("\n✅ Real-Time Data Streaming test completed!")