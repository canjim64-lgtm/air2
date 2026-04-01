"""
Parts List & Hardware Management
Complete CanSat hardware inventory and configuration
"""

PARTS_LIST = {
    "Main Controller & Storage": [
        {"name": "ESP32-WROVER-E", "qty": 1, "role": "Main microcontroller"},
        {"name": "Catalex MicroSD Card Adapter (SPI)", "qty": 1, "role": "SD card interface"},
        {"name": "MicroSD Card 32GB Class 10", "qty": 1, "role": "Data storage"},
    ],
    "Power System": [
        {"name": "2S Li-ion/LiPo Battery 7.4V, 850-1200mAh", "qty": 1, "role": "Primary power"},
        {"name": "2S BMS Board with balancing (5-10A)", "qty": 1, "role": "Battery management"},
        {"name": "MP1584EN Mini-360 Buck Converter", "qty": 1, "role": "3.3V regulator"},
        {"name": "Schottky Diode SS34", "qty": 1, "role": "Reverse protection"},
        {"name": "Ferrite Bead 1206", "qty": 1, "role": "EMI suppression"},
        {"name": "Resettable Fuse (PTC 0.5-1A)", "qty": 1, "role": "Overcurrent protection"},
        {"name": "Master SPDT Slide Switch", "qty": 1, "role": "Power switch"},
        {"name": "22µF Polymer Capacitor", "qty": 1, "role": "Power filtering"},
        {"name": "47µF Polymer Capacitor", "qty": 1, "role": "Power filtering"},
        {"name": "10µF Ceramic Capacitor", "qty": 1, "role": "Power filtering"},
        {"name": "0.1µF Ceramic Capacitors", "qty": 10, "role": "Decoupling"},
    ],
    "Communications & Positioning": [
        {"name": "HC-12 433MHz Radio Module (SI4463)", "qty": 1, "role": "Telemetry downlink"},
        {"name": "433MHz Helical Whip Antenna (SMA-M)", "qty": 1, "role": "RF antenna"},
        {"name": "U.FL to SMA Pigtail RG178", "qty": 1, "role": "Antenna cable"},
        {"name": "u-blox NEO-M8N GNSS Module + Patch Antenna", "qty": 1, "role": "GPS positioning"},
        {"name": "DS3231 RTC Module + CR2032 Battery", "qty": 1, "role": "Real-time clock"},
    ],
    "Environmental & Gas Sensors": [
        {"name": "Adafruit BME688 Environmental Sensor (I2C)", "qty": 1, "role": "Temp/Humidity/Pressure/VOC"},
        {"name": "BMP388 Barometric Sensor", "qty": 1, "role": "High-precision pressure"},
        {"name": "MiCS-6814 3-in-1 Gas Sensor", "qty": 1, "role": "NH3/NO2/CO detection"},
        {"name": "Sensirion SGP30 (TVOC + eCO2)", "qty": 1, "role": "Air quality"},
        {"name": "VEML6070 UV-A Sensor", "qty": 1, "role": "UV-A measurement"},
        {"name": "GUVA-S12SD UV-B/C Sensor", "qty": 1, "role": "UV-B/C measurement"},
        {"name": "TSL2591 Light Sensor", "qty": 1, "role": "Light intensity"},
        {"name": "VL53L1X Time-of-Flight Sensor", "qty": 1, "role": "Ground distance"},
        {"name": "DFRobot SEN0463 Geiger Counter (M4011)", "qty": 1, "role": "Radiation detection"},
        {"name": "Adafruit MMC5603 3-Axis Magnetometer", "qty": 1, "role": "Magnetic field"},
    ],
    "Indicators & Interfaces": [
        {"name": "TXS0108E 8-bit Level Shifter", "qty": 1, "role": "Voltage level conversion"},
        {"name": "RGB LEDs 3mm + 220Ω resistors", "qty": 3, "role": "Status indicators"},
        {"name": "Piezo Buzzer 3.3V", "qty": 1, "role": "Audio feedback"},
    ],
    "Connectors & Accessories": [
        {"name": "JST-PH 2-pin Connector Pairs", "qty": 3, "role": "Power connections"},
        {"name": "JST-PH 3-pin Connector Pairs", "qty": 5, "role": "Sensor connections"},
    ]
}


class HardwareManager:
    """Manage hardware configuration and status"""
    
    def __init__(self):
        self.parts = PARTS_LIST
        self.status = {}
    
    def get_parts_list(self) -> dict:
        """Get complete parts list"""
        return self.parts
    
    def get_total_components(self) -> int:
        """Count total components"""
        total = 0
        for category, items in self.parts.items():
            for item in items:
                total += item.get('qty', 1)
        return total
    
    def check_missing(self, installed: dict) -> list:
        """Check missing components"""
        missing = []
        for category, items in self.parts.items():
            for item in items:
                if category not in installed or item['name'] not in installed[category]:
                    missing.append(item['name'])
        return missing


# Example
if __name__ == "__main__":
    hm = HardwareManager()
    print(f"Total components: {hm.get_total_components()}")