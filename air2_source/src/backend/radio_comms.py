"""
Radio Communication Module - HC-12 433 MHz (SI4463)
"""
import serial
import time
from typing import Optional, Dict, Any

class HC12Radio:
    """HC-12 SI4463 433MHz Radio Module"""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baud: int = 9600):
        self.port = port
        self.baud = baud
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        
        # Radio settings
        self.frequency = 433.0  # MHz
        self.tx_power = 100  # mW
        self.channel = 0
        
    def connect(self) -> bool:
        """Connect to HC-12 module"""
        try:
            self.serial = serial.Serial(
                self.port, 
                self.baud,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from radio"""
        if self.serial:
            self.serial.close()
        self.connected = False
    
    def send(self, data: str) -> bool:
        """Send data string"""
        if not self.connected:
            return False
        try:
            self.serial.write(f"{data}\n".encode())
            return True
        except:
            return False
    
    def receive(self, timeout: float = 1.0) -> Optional[str]:
        """Receive data with timeout"""
        if not self.connected:
            return None
        
        self.serial.timeout = timeout
        try:
            line = self.serial.readline()
            return line.decode('utf-8', errors='ignore').strip()
        except:
            return None
    
    def set_frequency(self, freq_mhz: float):
        """Set operating frequency (433-435 MHz)"""
        self.frequency = freq_mhz
        # Send AT command to set frequency
        self.send(f"AT+FREQ={int(freq_mhz * 1000000)}")
    
    def set_power(self, power_dbm: int):
        """Set transmit power (0-20 dBm)"""
        self.tx_power = power_dbm
        self.send(f"AT+PWR={power_dbm}")
    
    def set_channel(self, channel: int):
        """Set channel (0-100)"""
        self.channel = channel
        self.send(f"AT+CH={channel}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get radio status"""
        return {
            'connected': self.connected,
            'frequency': self.frequency,
            'tx_power': self.tx_power,
            'channel': self.channel
        }
    
    def scan_channels(self) -> Dict[int, bool]:
        """Scan for available channels"""
        channels = {}
        for ch in range(10):
            self.set_channel(ch)
            time.sleep(0.1)
            # Try to detect activity
            channels[ch] = True  # Placeholder
        return channels


def main():
    """Test radio module"""
    radio = HC12Radio('/dev/ttyUSB0', 9600)
    
    if radio.connect():
        print("Radio connected!")
        
        # Send test message
        radio.send("TEST")
        
        # Receive
        msg = radio.receive()
        print(f"Received: {msg}")
        
        radio.disconnect()
    else:
        print("Failed to connect")

if __name__ == "__main__":
    main()