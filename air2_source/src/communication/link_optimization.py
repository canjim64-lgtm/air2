"""
Satellite Link Optimization (SLO) for AirOne Professional v4.0
Predicts optimal baud rate and packet sizing based on real-time RSSI and SNR trends.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LinkOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SLO")
        self.current_baud = 57600
        self.current_packet_size = 128
        self.logger.info("Satellite Link Optimizer (SLO) initialized.")

    def optimize(self, rssi: float, snr: float) -> Dict[str, Any]:
        """Dynamically adjusts link parameters to maximize throughput vs reliability."""
        
        # Link budget analysis
        link_quality = 0.0
        if rssi > -70: link_quality = 1.0
        elif rssi < -110: link_quality = 0.0
        else: link_quality = (rssi + 110) / 40.0
        
        # Slower baud for lower RSSI
        new_baud = 57600
        if rssi < -100: new_baud = 9600
        elif rssi < -90: new_baud = 19200
        elif rssi < -80: new_baud = 38400
        else: new_baud = 115200
        
        # Adaptive packet sizing (larger packets for better SNR)
        new_size = 64
        if snr > 15: new_size = 256
        elif snr > 8: new_size = 128
        
        changed = (new_baud != self.current_baud or new_size != self.current_packet_size)
        self.current_baud = new_baud
        self.current_packet_size = new_size
        
        if changed:
            self.logger.info(f"Link parameters updated: {new_baud} bps, {new_size} bytes/packet.")

        return {
            "baud_rate": new_baud,
            "packet_size": new_size,
            "link_quality_pct": round(link_quality * 100, 1),
            "recommendation": "STABLE" if link_quality > 0.5 else "REDUCE_LOAD"
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    slo = LinkOptimizer()
    print(slo.optimize(rssi=-95, snr=5))
