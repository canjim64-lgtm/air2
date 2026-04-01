"""
LoRaWAN Module - Full Implementation
Long range wide area network
"""

import numpy as np
import time


class LoRaWANRadio:
    """LoRaWAN radio control"""
    
    def __init__(self):
        self.frequency = 868.0
        self.spreading_factor = 7
        self.bandwidth = 125
        self.tx_power = 14
        self.duty_cycle = 1.0
    
    def set_frequency(self, freq: float):
        if freq in [863.0, 868.0, 869.525, 915.0, 923.0]:
            self.frequency = freq
    
    def set_spreading_factor(self, sf: int):
        if 7 <= sf <= 12:
            self.spreading_factor = sf
    
    def configure(self, freq: float = 868.0, sf: int = 7, bw: int = 125, tx: int = 14):
        self.set_frequency(freq)
        self.set_spreading_factor(sf)
        self.bandwidth = bw
        self.tx_power = tx
    
    def calculate_time_on_air(self, payload_size: int) -> float:
        # Simplified time on air calculation
        symbol_time = (2 ** self.spreading_factor) / self.bandwidth
        n_payload = payload_size + 8
        n_symbols = 8 + max(0, n_payload - (2 * self.spreading_factor - 4))
        return n_symbols * symbol_time
    
    def get_config(self) -> dict:
        return {
            'frequency': self.frequency,
            'spreading_factor': self.spreading_factor,
            'bandwidth': self.bandwidth,
            'tx_power': self.tx_power
        }


class AdaptiveDataRate:
    """ADR for LoRaWAN"""
    
    def __init__(self):
        self.history = []
        self.target_dr = 5
    
    def update(self, snr: float, margin: float):
        self.history.append({'snr': snr, 'margin': margin, 'time': time.time()})
        if len(self.history) > 20:
            self.history = self.history[-20:]
    
    def compute_next_dr(self) -> int:
        if len(self.history) < 5:
            return self.target_dr
        
        avg_snr = np.mean([h['snr'] for h in self.history[-10:]])
        
        if avg_snr > 10:
            return min(12, self.target_dr + 1)
        elif avg_snr < -5:
            return max(0, self.target_dr - 1)
        
        return self.target_dr


class GateWay:
    """LoRaWAN gateway"""
    
    def __init__(self, gateway_id: str):
        self.gateway_id = gateway_id
        self.coordinates = {'lat': 0, 'lon': 0, 'alt': 0}
        self.connected = False
    
    def set_location(self, lat: float, lon: float, alt: float):
        self.coordinates = {'lat': lat, 'lon': lon, 'alt': alt}
    
    def connect(self):
        self.connected = True
    
    def get_status(self) -> dict:
        return {
            'id': self.gateway_id,
            'connected': self.connected,
            'location': self.coordinates
        }


if __name__ == "__main__":
    lora = LoRaWANRadio()
    lora.configure(868.0, 7)
    print(f"ToA: {lora.calculate_time_on_air(50):.2f}s")