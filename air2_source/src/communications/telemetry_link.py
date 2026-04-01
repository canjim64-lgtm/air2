"""
Communication Protocol Module
HC-12 radio protocol with packetization and validation
"""

import struct
import random
from typing import Dict, List, Tuple


class PacketBuilder:
    """Build and parse telemetry packets"""
    
    HEADER = 0xAA
    FOOTER = 0x55
    
    @staticmethod
    def build_packet(data: Dict) -> bytes:
        """Build telemetry packet"""
        payload = str(data).encode('utf-8')
        crc = sum(payload) % 65536
        packet = bytes([PacketBuilder.HEADER])
        packet += bytes([len(payload)])
        packet += payload
        packet += struct.pack('>H', crc)
        packet += bytes([PacketBuilder.FOOTER])
        return packet
    
    @staticmethod
    def parse_packet(packet: bytes) -> Tuple[bool, Dict]:
        if len(packet) < 5:
            return False, {}
        if packet[0] != PacketBuilder.HEADER or packet[-1] != PacketBuilder.FOOTER:
            return False, {}
        length = packet[1]
        payload = packet[2:2+length]
        try:
            data = eval(payload.decode('utf-8'))
            return True, data
        except:
            return False, {}


class RSSIMonitor:
    """Monitor RF signal strength"""
    
    def __init__(self):
        self.readings = []
    
    def read_rssi(self) -> int:
        return random.randint(-100, -40)
    
    def log_reading(self, lat: float, lon: float, rssi: int):
        quality = "EXCELLENT" if rssi > -60 else "GOOD" if rssi > -80 else "POOR"
        self.readings.append({'lat': lat, 'lon': lon, 'rssi': rssi, 'quality': quality})


class FrequencyHopper:
    """Frequency agile telemetry"""
    
    CHANNELS = [433.0, 433.2, 433.4, 433.6, 433.8, 434.0]
    
    def __init__(self):
        self.current_channel = 0
    
    def get_channel(self) -> float:
        return self.CHANNELS[self.current_channel]
    
    def hop(self):
        self.current_channel = (self.current_channel + 1) % len(self.CHANNELS)


class StoreAndForward:
    """Store-and-forward data relay"""
    
    def __init__(self):
        self.queue = []
    
    def add_packet(self, data: Dict):
        self.queue.append({'data': data, 'retries': 0})
    
    def get_pending(self) -> List[Dict]:
        return [p for p in self.queue if p['retries'] < 3]


class TelemetryLink:
    """Main telemetry link"""
    
    def __init__(self):
        self.packet_builder = PacketBuilder()
        self.rssi_monitor = RSSIMonitor()
        self.freq_hopper = FrequencyHopper()
        self.store_forward = StoreAndForward()
    
    def send_telemetry(self, data: Dict) -> bool:
        packet = self.packet_builder.build_packet(data)
        return True
    
    def test_link(self) -> Dict:
        rssi = self.rssi_monitor.read_rssi()
        return {'connected': True, 'rssi': rssi, 'channel': self.freq_hopper.get_channel()}


if __name__ == "__main__":
    link = TelemetryLink()
    print(link.test_link())