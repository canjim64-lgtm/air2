"""
AirOne v3 - Hardware Drivers & Interfaces
=========================================

This file contains all hardware driver implementations for the AirOne v3 system,
consolidating multiple hardware interface modules into a single comprehensive
driver system.

This file consolidates:
- src/hardware/drivers.py (Main hardware drivers)
- src/hardware/geiger_driver.py (Radiation detection driver)
- src/hardware/gnss_driver.py (GNSS positioning driver) 
- src/hardware/lora_driver.py (LoRa communication driver)
- src/hardware/rtc_driver.py (Real-time clock driver)
- src/hardware/sensor_driver.py (Generic sensor driver)
- src/hardware/mock_hardware.py (Mock hardware for testing)
- src/hardware/rf_driver.py (RF communication driver)
"""

import logging
import time
import threading
from typing import Optional, Dict, Any, List, Callable, Tuple
from datetime import datetime
import random
import queue
import struct
import json
import os
import sys
from pathlib import Path
import numpy as np
import math
import statistics
import socket
import select
import errno
import platform
import subprocess
import hashlib
import hmac
import secrets
import string
import base64
import zlib
import gzip
import pickle
import asyncio
import concurrent.futures
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import ctypes # For low-level memory/hardware interaction
import mmap # For shared memory
import signal
import atexit
import weakref
import gc
import resource # For system resource monitoring
import psutil # For system process monitoring
import cpuinfo # For CPU information
import pkg_resources # For package introspection
import importlib # For dynamic module loading
import ast # For code analysis, e.g., in dynamic drivers
import dis # For bytecode analysis
import inspect # For runtime inspection of code
import types # For dynamic type creation/manipulation
import copy
import collections
import heapq
import bisect
import itertools
import functools
import operator
import re
import uuid
import urllib.parse # For URL encoding/decoding, potentially in network configs

# Specific hardware/communication related imports that might be used:
import serial
import serial.tools.list_ports

from dataclasses import dataclass, field
from enum import Enum, auto # auto is used in some enums


logger = logging.getLogger(__name__)

# ###########################################################################
# MOCK HARDWARE (from mock_hardware.py) - for testing and simulation
# ###########################################################################

class MockSerialDevice:
    """Mock serial device for testing"""
    def __init__(self, port: str = "COM1", baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = False
        self.read_buffer = queue.Queue()
        self.write_buffer = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def open(self):
        self.is_open = True
        self.logger.info(f"MockSerialDevice: Opened {self.port} at {self.baudrate} baud")

    def close(self):
        self.is_open = False
        self.logger.info(f"MockSerialDevice: Closed {self.port}")

    def write(self, data: bytes):
        if not self.is_open:
            raise IOError("Serial port not open")
        self.write_buffer.append(data)
        self.logger.debug(f"MockSerialDevice: Wrote {len(data)} bytes")

    def read(self, size: int = 1) -> bytes:
        if not self.is_open:
            raise IOError("Serial port not open")
        try:
            # Simulate receiving data
            if self.read_buffer.empty() and random.random() < 0.1: # 10% chance to generate random data
                self.read_buffer.put(os.urandom(random.randint(1, 10)))
            
            data = self.read_buffer.get(timeout=self.timeout)
            self.logger.debug(f"MockSerialDevice: Read {len(data)} bytes")
            return data
        except queue.Empty:
            return b''

    def readline(self) -> bytes:
        # Simulate reading a line
        data = self.read(random.randint(5, 20))
        if data:
            return data + b'\n'
        return b''

    def in_waiting(self) -> int:
        return self.read_buffer.qsize() * 10 # Estimate bytes

class MockUSBDevice:
    """Mock USB device for testing"""
    def __init__(self, vendor_id: int, product_id: int):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.is_open = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def open(self):
        self.is_open = True
        self.logger.info(f"MockUSBDevice: Opened Vendor:{hex(self.vendor_id)}, Product:{hex(self.product_id)}")

    def close(self):
        self.is_open = False
        self.logger.info(f"MockUSBDevice: Closed Vendor:{hex(self.vendor_id)}, Product:{hex(self.product_id)}")

    def read(self, size: int) -> bytes:
        if not self.is_open:
            raise IOError("USB device not open")
        self.logger.debug(f"MockUSBDevice: Reading {size} bytes")
        return os.urandom(size) # Simulate random data

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise IOError("USB device not open")
        self.logger.debug(f"MockUSBDevice: Wrote {len(data)} bytes")
        return len(data)

# ###########################################################################
# GENERIC SENSOR DRIVER (from sensor_driver.py)
# ###########################################################################

class SensorDriver:
    """Generic sensor driver for various types of sensors"""
    
    def __init__(self, sensor_type: str, interface: 'HardwareInterface', config: Dict[str, Any]):
        self.sensor_type = sensor_type
        self.interface = interface
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}-{sensor_type}")
        self.connected = False
        
        self.calibration_offset = config.get('offset', 0.0)
        self.calibration_scale = config.get('scale', 1.0)
    
    def connect(self) -> bool:
        """Connect to the sensor via the hardware interface"""
        # Assuming interface is already connected to the bus (e.g., I2C, SPI)
        self.logger.info(f"Connecting to {self.sensor_type} sensor...")
        time.sleep(0.1) # Simulate connection delay
        if random.random() < 0.95:
            self.connected = True
            self.logger.info(f"Successfully connected to {self.sensor_type} sensor.")
            return True
        self.logger.error(f"Failed to connect to {self.sensor_type} sensor.")
        return False
    
    def disconnect(self):
        """Disconnect from the sensor"""
        self.connected = False
        self.logger.info(f"Disconnected from {self.sensor_type} sensor.")
    
    def read_data(self) -> Optional[float]:
        """Read data from the sensor"""
        if not self.connected:
            self.logger.warning(f"{self.sensor_type} sensor not connected.")
            return None
        
        # Simulate reading raw data from the interface
        raw_data = self._read_raw_from_interface()
        
        if raw_data is not None:
            processed_data = (raw_data + self.calibration_offset) * self.calibration_scale
            self.logger.debug(f"Read {processed_data:.2f} from {self.sensor_type}")
            return processed_data
        
        return None
    
    def _read_raw_from_interface(self) -> Optional[float]:
        """Simulate reading raw data directly from the hardware interface"""
        # In a real scenario, this would involve I2C, SPI, or ADC reads
        # For simulation, return a random value within expected range
        if self.sensor_type == "BMP280" or self.sensor_type == "BME280":
            return random.uniform(900.0, 1100.0) # Pressure
        elif self.sensor_type == "MPU6050" or self.sensor_type == "MPU9250":
            return random.uniform(-10.0, 10.0) # Acceleration/Gyro
        elif self.sensor_type == "HMC5883L":
            return random.uniform(-50.0, 50.0) # Magnetometer
        elif self.sensor_type == "ADS1115":
            return random.uniform(0.0, 5.0) # ADC voltage
        else:
            return random.uniform(0.0, 100.0) # Generic range

class GNSSDriver:
    """GNSS (GPS) driver for position, velocity, and time"""
    
    def __init__(self, interface: 'HardwareInterface', config: Dict[str, Any]):
        self.interface = interface
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connected = False
        
        self.last_position = (0.0, 0.0, 0.0) # lat, lon, alt
        self.last_velocity = (0.0, 0.0, 0.0) # vx, vy, vz
        self.fix_quality = 0 # 0=no fix, 1=GPS fix, 2=DGPS fix
    
    def connect(self) -> bool:
        """Connect to the GNSS module"""
        self.logger.info("Connecting to GNSS module...")
        time.sleep(0.2)
        if random.random() < 0.9:
            self.connected = True
            self.logger.info("Successfully connected to GNSS module.")
            return True
        self.logger.error("Failed to connect to GNSS module.")
        return False
    
    def disconnect(self):
        """Disconnect from the GNSS module"""
        self.connected = False
        self.logger.info("Disconnected from GNSS module.")
    
    def read_position(self) -> Optional[Tuple[float, float, float]]:
        """Read current position (lat, lon, alt)"""
        if not self.connected:
            self.logger.warning("GNSS module not connected.")
            return None
        
        # Simulate reading NMEA sentences and parsing
        if random.random() < 0.05: # Simulate momentary signal loss
            self.fix_quality = 0
            return None
        
        self.fix_quality = 1 # Simulate GPS fix
        self.last_position = (
            self.last_position[0] + random.uniform(-0.00001, 0.00001),
            self.last_position[1] + random.uniform(-0.00001, 0.00001),
            self.last_position[2] + random.uniform(-0.5, 0.5)
        )
        self.logger.debug(f"GNSS Position: {self.last_position}")
        return self.last_position
    
    def read_velocity(self) -> Optional[Tuple[float, float, float]]:
        """Read current velocity (vx, vy, vz)"""
        if not self.connected or self.fix_quality == 0:
            return None
        
        self.last_velocity = (
            self.last_velocity[0] + random.uniform(-0.1, 0.1),
            self.last_velocity[1] + random.uniform(-0.1, 0.1),
            self.last_velocity[2] + random.uniform(-0.1, 0.1)
        )
        self.logger.debug(f"GNSS Velocity: {self.last_velocity}")
        return self.last_velocity
    
    def get_fix_quality(self) -> int:
        """Get GPS fix quality"""
        return self.fix_quality


class LoRaDriver:
    """LoRa (Long Range) radio communication driver"""
    
    def __init__(self, interface: 'HardwareInterface', config: Dict[str, Any]):
        self.interface = interface
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connected = False
        
        self.frequency = config.get('frequency', 915e6) # Hz
        self.bandwidth = config.get('bandwidth', 125e3) # Hz
        self.spreading_factor = config.get('spreading_factor', 7)
        self.tx_power = config.get('tx_power', 20) # dBm
        self.node_address = config.get('node_address', 0x01)
    
    def connect(self) -> bool:
        """Connect to the LoRa module"""
        self.logger.info("Connecting to LoRa module...")
        time.sleep(0.1)
        if random.random() < 0.98:
            self.connected = True
            self.logger.info("Successfully connected to LoRa module.")
            return True
        self.logger.error(f"Failed to connect to LoRa module.")
        return False
    
    def disconnect(self):
        """Disconnect from the LoRa module"""
        self.connected = False
        self.logger.info("Disconnected from LoRa module.")
    
    def send_packet(self, data: bytes, destination_address: int = 0xFF) -> bool:
        """Send a LoRa packet"""
        if not self.connected:
            self.logger.warning("LoRa module not connected.")
            return False
        
        # Simulate sending packet over air
        time.sleep(0.05) # Simulate air time
        self.logger.debug(f"LoRa: Sent {len(data)} bytes to {destination_address}")
        
        if random.random() < 0.9: # Simulate packet loss
            return True
        
        self.logger.warning("LoRa: Packet lost during transmission.")
        return False
    
    def receive_packet(self) -> Optional[bytes]:
        """Receive a LoRa packet"""
        if not self.connected:
            return None
        
        # Simulate receiving packet
        if random.random() < 0.1: # 10% chance of receiving a packet
            self.logger.debug("LoRa: Received simulated packet.")
            return os.urandom(random.randint(10, 50))
        
        return None

class GeigerDriver:
    """Geiger counter driver for radiation detection"""
    
    def __init__(self, interface: 'HardwareInterface', config: Dict[str, Any]):
        self.interface = interface
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connected = False
        
        self.sensitivity_cpm_per_uSv = config.get('sensitivity', 3.0) # Counts per minute per microSievert
        self.background_radiation_uSv_per_hr = config.get('background', 0.1) # microSieverts per hour
    
    def connect(self) -> bool:
        """Connect to the Geiger counter"""
        self.logger.info("Connecting to Geiger counter...")
        time.sleep(0.05)
        if random.random() < 0.99:
            self.connected = True
            self.logger.info("Successfully connected to Geiger counter.")
            return True
        self.logger.error("Failed to connect to Geiger counter.")
        return False
    
    def disconnect(self):
        """Disconnect from the Geiger counter"""
        self.connected = False
        self.logger.info("Disconnected from Geiger counter.")
    
    def read_radiation(self, interval_s: float = 1.0) -> Optional[float]:
        """Read current radiation level in microSieverts per hour"""
        if not self.connected:
            self.logger.warning("Geiger counter not connected.")
            return None
        
        # Simulate Geiger counter clicks (Poisson process)
        background_cpm = self.sensitivity_cpm_per_uSv * self.background_radiation_uSv_per_hr / 60.0
        # Add random spike (e.g., cosmic ray)
        spike_cpm = 0.0
        if random.random() < 0.01: # 1% chance of a spike
            spike_cpm = random.uniform(5.0, 20.0)
        
        total_cpm = background_cpm + spike_cpm
        
        # Convert CPM to uSv/hr
        radiation_uSv_per_hr = total_cpm / self.sensitivity_cpm_per_uSv * 60.0
        
        self.logger.debug(f"Geiger: Read {radiation_uSv_per_hr:.2f} uSv/hr")
        return radiation_uSv_per_hr


class RFDriver:
    """Generic RF communication driver (e.g., for XBee, generic transceivers)"""
    
    def __init__(self, interface: 'HardwareInterface', config: Dict[str, Any]):
        self.interface = interface
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connected = False
        
        self.channel = config.get('channel', 0)
        self.power_level = config.get('power_level', 10) # dBm
        self.address = config.get('address', '0000')
    
    def connect(self) -> bool:
        """Connect to the RF module"""
        self.logger.info("Connecting to RF module...")
        time.sleep(0.05)
        if random.random() < 0.97:
            self.connected = True
            self.logger.info("Successfully connected to RF module.")
            return True
        self.logger.error(f"Failed to connect to RF module.")
        return False
    
    def disconnect(self):
        """Disconnect from the RF module"""
        self.connected = False
        self.logger.info("Disconnected from RF module.")
    
    def send_data(self, data: bytes, destination_address: str = 'FFFF') -> bool:
        """Send data over RF"""
        if not self.connected:
            self.logger.warning("RF module not connected.")
            return False
        
        time.sleep(0.02) # Simulate air time
        self.logger.debug(f"RF: Sent {len(data)} bytes to {destination_address}")
        
        if random.random() < 0.95: # Simulate packet loss
            return True
        
        self.logger.warning("RF: Packet lost during transmission.")
        return False
    
    def receive_data(self) -> Optional[bytes]:
        """Receive data over RF"""
        if not self.connected:
            return None
        
        if random.random() < 0.15: # 15% chance of receiving a packet
            self.logger.debug("RF: Received simulated data.")
            return os.urandom(random.randint(20, 100))
        
        return None

# ###########################################################################
# REAL-TIME CLOCK DRIVER (from rtc_driver.py)
# ###########################################################################

class RTCDriver:
    """Real-time clock driver"""
    
    def __init__(self):
        self.initialized = False
        self.last_sync = None
        self.drift_compensation = 0.0
        
    def initialize(self):
        """Initialize the RTC driver"""
        self.initialized = True
        self.last_sync = datetime.now()
        return True
    
    def get_time(self):
        """Get current time from RTC"""
        return datetime.now()
    
    def set_time(self, new_time):
        """Set RTC time"""
        self.last_sync = new_time
        return True
    
    def sync(self):
        """Synchronize RTC with system time"""
        self.last_sync = datetime.now()
        return True
    
    def get_status(self):
        """Get RTC status"""
        return {
            "initialized": self.initialized,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "drift_compensation": self.drift_compensation
        }

# ###########################################################################
# HARDWARE INTERFACE MANAGER (from drivers.py)
# ###########################################################################

class HardwareDrivers:
    """Hardware driver manager for AirOne Professional"""
    
    def __init__(self):
        self.drivers = {}
        self.connected_devices = {}
        self.driver_status = {}
        self.supported_hardware = self._get_supported_hardware()
        
    def _get_supported_hardware(self) -> Dict[str, List[str]]:
        """Get list of supported hardware"""
        return {
            'serial_ports': ['USB Serial', 'FTDI', 'Prolific', 'Silicon Labs CP210x', 'Standard UART'],
            'usb_devices': ['USB Telemetry Receiver', 'USB GPS', 'USB Radio', 'USB Sensor Hub'],
            'sdr_devices': ['RTL-SDR', 'HackRF One', 'BladeRF', 'USRP', 'LimeSDR', 'PlutoSDR', 'Airspy'],
            'gps_modules': ['u-blox GPS', 'NEO-6M', 'NEO-7M', 'NEO-8M', 'ZED-F9P'],
            'radio_modules': ['XBee', 'LoRa', 'RFM69', 'CC1101', 'Si4432'],
            'sensors': ['BMP280', 'BME280', 'MPU6050', 'MPU9250', 'HMC5883L', 'ADS1115'],
            'cameras': ['USB Camera', 'Raspberry Pi Camera', 'IP Camera', 'Webcam'],
            'data_loggers': ['SD Card Logger', 'USB Data Logger', 'Network Logger']
        }
    
    def scan_for_hardware(self) -> Dict[str, Any]:
        """Scan for connected hardware"""
        scan_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'devices_found': [],
            'drivers_loaded': [],
            'errors': []
        }
        
        # Scan serial ports
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                scan_results['devices_found'].append({
                    'type': 'serial',
                    'name': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'status': 'available'
                })
        except ImportError:
            scan_results['errors'].append('pyserial not installed - cannot scan serial ports')
        except Exception as e:
            scan_results['errors'].append(f'Serial port scan error: {str(e)}')
        
        # Scan USB devices
        try:
            import usb.core
            devices = usb.core.find(find_all=True)
            for device in devices:
                try:
                    scan_results['devices_found'].append({
                        'type': 'usb',
                        'name': usb.util.get_string(device, device.iProduct) if device.iProduct else f'USB Device {device.idVendor}:{device.idProduct}',
                        'vendor_id': hex(device.idVendor),
                        'product_id': hex(device.idProduct),
                        'status': 'available'
                    })
                except:
                    scan_results['devices_found'].append({
                        'type': 'usb',
                        'name': f'USB Device {device.idVendor}:{device.idProduct}',
                        'vendor_id': hex(device.idVendor),
                        'product_id': hex(device.idProduct),
                        'status': 'available'
                    })
        except ImportError:
            scan_results['errors'].append('pyusb not installed - cannot scan USB devices')
        except Exception as e:
            scan_results['errors'].append(f'USB scan error: {str(e)}')
        
        # Check for SDR devices
        try:
            import rtlsdr
            sdr = rtlsdr.RtlSdr()
            scan_results['devices_found'].append({
                'type': 'sdr',
                'name': 'RTL-SDR',
                'status': 'available'
            })
            sdr.close()
        except Exception as e:
            # SDR not available or rtlsdr not installed
            scan_results['errors'].append(f'SDR scan failed: {e}')

        self.driver_status['last_scan'] = scan_results
        return scan_results
    
    def install_driver(self, device_type: str, device_name: str) -> bool:
        """Install driver for a specific device"""
        try:
            if device_type == 'serial':
                return self._install_serial_driver(device_name)
            elif device_type == 'usb':
                return self._install_usb_driver(device_name)
            elif device_type == 'sdr':
                return self._install_sdr_driver(device_name)
            elif device_type == 'gps':
                return self._install_gps_driver(device_name)
            elif device_type == 'radio':
                return self._install_radio_driver(device_name)
            elif device_type == 'sensor':
                return self._install_sensor_driver(device_name)
            else:
                return False
        except Exception as e:
            self.driver_status['last_error'] = str(e)
            return False
    
    def _install_serial_driver(self, device_name: str) -> bool:
        """Install serial port driver"""
        try:
            import serial
            self.drivers[device_name] = {
                'type': 'serial',
                'module': serial,
                'status': 'loaded',
                'loaded_at': datetime.utcnow().isoformat()
            }
            return True
        except ImportError:
            return False
    
    def _install_usb_driver(self, device_name: str) -> bool:
        """Install USB driver"""
        try:
            import usb.core
            import usb.util
            self.drivers[device_name] = {
                'type': 'usb',
                'module': usb.core,
                'util': usb.util,
                'status': 'loaded',
                'loaded_at': datetime.utcnow().isoformat()
            }
            return True
        except ImportError:
            return False
    
    def _install_sdr_driver(self, device_name: str) -> bool:
        """Install SDR driver"""
        try:
            if 'rtl' in device_name.lower():
                import rtlsdr
                self.drivers[device_name] = {
                    'type': 'sdr',
                    'module': rtlsdr,
                    'status': 'loaded',
                    'loaded_at': datetime.utcnow().isoformat()
                }
                return True
            return False
        except ImportError:
            return False
    
    def _install_gps_driver(self, device_name: str) -> bool:
        """Install GPS driver"""
        try:
            import gps3
            self.drivers[device_name] = {
                'type': 'gps',
                'module': gps3,
                'status': 'loaded',
                'loaded_at': datetime.utcnow().isoformat()
            }
            return True
        except ImportError:
            try:
                import pynmea2
                self.drivers[device_name] = {
                    'type': 'gps',
                    'module': pynmea2,
                    'status': 'loaded',
                    'loaded_at': datetime.utcnow().isoformat()
                }
                return True
            except ImportError:
                return False
    
    def _install_radio_driver(self, device_name: str) -> bool:
        """Install radio module driver"""
        try:
            if 'xbee' in device_name.lower():
                import digi.xbee
                self.drivers[device_name] = {
                    'type': 'radio',
                    'module': digi.xbee,
                    'status': 'loaded',
                    'loaded_at': datetime.utcnow().isoformat()
                }
                return True
            return False
        except ImportError:
            return False
    
    def _install_sensor_driver(self, device_name: str) -> bool:
        """Install sensor driver"""
        try:
            if 'bmp' in device_name.lower() or 'bme' in device_name.lower():
                import smbus2
                self.drivers[device_name] = {
                    'type': 'sensor',
                    'module': smbus2,
                    'status': 'loaded',
                    'loaded_at': datetime.utcnow().isoformat()
                }
                return True
            return False
        except ImportError:
            return False
    
    def get_driver_status(self) -> Dict[str, Any]:
        """Get status of all drivers"""
        return {
            'drivers_loaded': len(self.drivers),
            'drivers': self.drivers,
            'connected_devices': self.connected_devices,
            'last_scan': self.driver_status.get('last_scan', None),
            'supported_hardware': self.supported_hardware
        }
    
    def unload_driver(self, device_name: str) -> bool:
        """Unload a driver"""
        if device_name in self.drivers:
            del self.drivers[device_name]
            return True
        return False
    
    def unload_all_drivers(self):
        """Unload all drivers"""
        self.drivers.clear()
        self.connected_devices.clear()


class DeviceInterface:
    """Generic device interface for hardware communication"""
    
    def __init__(self, driver_manager: HardwareDrivers):
        self.driver_manager = driver_manager
        self.connected = False
        self.device = None
        
    def connect(self, device_type: str, device_name: str, **kwargs) -> bool:
        """Connect to a device"""
        try:
            if device_type == 'serial':
                return self._connect_serial(device_name, **kwargs)
            elif device_type == 'usb':
                return self._connect_usb(device_name, **kwargs)
            elif device_type == 'sdr':
                return self._connect_sdr(device_name, **kwargs)
            elif device_type == 'gps':
                return self._connect_gps(device_name, **kwargs)
            else:
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def _connect_serial(self, device_name: str, baudrate: int = 9600, timeout: int = 1) -> bool:
        """Connect to serial device"""
        try:
            import serial
            self.device = serial.Serial(device_name, baudrate=baudrate, timeout=timeout)
            self.connected = True
            return True
        except Exception as e:
            print(f"Serial connection error: {e}")
            return False
    
    def _connect_usb(self, device_name: str, **kwargs) -> bool:
        """Connect to USB device"""
        try:
            import usb.core
            import usb.util
            
            # Parse device name to get vendor and product ID
            if ':' in device_name:
                parts = device_name.split(':')
                vendor_id = int(parts[0], 16)
                product_id = int(parts[1], 16)
                self.device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
            else:
                self.device = usb.core.find(custom_match=lambda d: True)
            
            if self.device is not None:
                self.connected = True
                return True
            return False
        except Exception as e:
            print(f"USB connection error: {e}")
            return False
    
    def _connect_sdr(self, device_name: str, **kwargs) -> bool:
        """Connect to SDR device"""
        try:
            import rtlsdr
            self.device = rtlsdr.RtlSdr()
            self.connected = True
            return True
        except Exception as e:
            print(f"SDR connection error: {e}")
            return False
    
    def _connect_gps(self, device_name: str, **kwargs) -> bool:
        """Connect to GPS device"""
        try:
            return self._connect_serial(device_name, **kwargs)
        except Exception as e:
            print(f"GPS connection error: {e}")
            return False
    
    def read(self, size: int = 1) -> Any:
        """Read data from device"""
        if not self.connected or self.device is None:
            return None
        
        try:
            if hasattr(self.device, 'read'):
                return self.device.read(size)
            elif hasattr(self.device, 'readline'):
                return self.device.readline()
            else:
                return None
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def write(self, data: Any) -> bool:
        """Write data to device"""
        if not self.connected or self.device is None:
            return False
        
        try:
            if hasattr(self.device, 'write'):
                self.device.write(data)
                return True
            else:
                return False
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        if self.device is not None:
            try:
                if hasattr(self.device, 'close'):
                    self.device.close()
            except Exception as e:
                self.logger.debug(f"Device close error: {e}")
            self.device = None
        self.connected = False


def initialize_drivers() -> HardwareDrivers:
    """Initialize hardware drivers"""
    return HardwareDrivers()


def create_device_interface(driver_manager: HardwareDrivers) -> DeviceInterface:
    """Create device interface"""
    return DeviceInterface(driver_manager)
