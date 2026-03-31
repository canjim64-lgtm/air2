"""
Advanced Signal Processing & Visualization
- RSSI heat mapping for RF signal analysis
- Luminous efficiency index
- Virtual horizon via magnetometer
- Gas sensor fusion ratio analysis
- 3D volumetric visualization data generation
- Circular buffer for dual-path data persistence
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import struct
import json


# ============================================================================
# 1. RSSI HEAT-MAPPING (RF Signal Analysis)
# ============================================================================

class RSSIHeatMapper:
    """
    Maps HC-12 RSSI against GPS coordinates for RF shadow detection.
    """
    
    def __init__(self, grid_resolution: float = 10):  # meters
        self.grid_resolution = grid_resolution
        self.data_points = deque(maxlen=1000)
        
        # Grid storage
        self.rssi_grid = {}  # (ix, iy) -> [rssi values]
        self.count_grid = {}  # (ix, iy) -> count
        
    def add_reading(self, timestamp: float, latitude: float, longitude: float,
                   rssi: float, snr: float = 0):
        """Add RSSI measurement with position."""
        self.data_points.append({
            'timestamp': timestamp,
            'latitude': latitude,
            'longitude': longitude,
            'rssi': rssi,
            'snr': snr
        })
        
        # Grid indices
        ix = int(latitude * 10000) % 1000
        iy = int(longitude * 10000) % 1000
        
        if (ix, iy) not in self.rssi_grid:
            self.rssi_grid[(ix, iy)] = []
            self.count_grid[(ix, iy)] = 0
            
        self.rssi_grid[(ix, iy)].append(rssi)
        self.count_grid[(ix, iy)] += 1
        
    def get_signal_map(self) -> Dict:
        """Get signal strength map for visualization."""
        # Calculate average RSSI for each grid cell
        grid_data = []
        
        for (ix, iy), values in self.rssi_grid.items():
            avg_rssi = np.mean(values)
            count = self.count_grid[(ix, iy)]
            
            # Convert grid index to approximate position
            lat = ix / 10000
            lon = iy / 10000
            
            grid_data.append({
                'lat': lat,
                'lon': lon,
                'avg_rssi': float(avg_rssi),
                'count': count,
                'signal_quality': self._classify_signal(avg_rssi)
            })
            
        # Find worst areas (RF shadows)
        weak_signals = [d for d in grid_data if d['avg_rssi'] < -80]
        
        return {
            'grid_points': grid_data,
            'total_measurements': len(self.data_points),
            'rf_shadow_points': weak_signals,
            'avg_rssi': float(np.mean([d['avg_rssi'] for d in grid_data])) if grid_data else 0,
            'worst_rssi': float(min(d['avg_rssi'] for d in grid_data)) if grid_data else 0
        }
        
    def _classify_signal(self, rssi: float) -> str:
        """Classify signal strength."""
        if rssi > -50:
            return 'EXCELLENT'
        elif rssi > -65:
            return 'GOOD'
        elif rssi > -80:
            return 'FAIR'
        elif rssi > -90:
            return 'POOR'
        else:
            return 'CRITICAL'
            
    def get_rf_shadow_report(self) -> Dict:
        """Generate RF shadow analysis report."""
        heat_data = self.get_signal_map()
        
        if not heat_data['rf_shadow_points']:
            return {
                'status': 'No RF shadows detected',
                'recommendation': 'Signal coverage appears adequate'
            }
            
        # Find cluster of weak signals
        shadows = heat_data['rf_shadow_points']
        
        return {
            'status': f'{len(shadows)} potential RF shadow(s) detected',
            'shadow_locations': [{'lat': s['lat'], 'lon': s['lon'], 'rssi': s['avg_rssi']} for s in shadows[:5]],
            'recommendation': 'Consider repositioning ground station or adding relay'
        }


# ============================================================================
# 2. LUMINOUS EFFICIENCY INDEX
# ============================================================================

class LuminousEfficiencyIndex:
    """
    Calculates UV-to-Visible ratio for aerosol detection.
    Spikes indicate cleared haze/smog layers.
    """
    
    def __init__(self):
        self.uv_a_history = deque(maxlen=100)
        self.uv_b_history = deque(maxlen=100)
        self.visible_history = deque(maxlen=100)
        self.lux_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        
    def add_reading(self, timestamp: float, uv_a: float, uv_b: float,
                   visible: float, lux: float):
        """Add light sensor reading."""
        self.timestamp_history.append(timestamp)
        self.uv_a_history.append(uv_a)
        self.uv_b_history.append(uv_b)
        self.visible_history.append(visible)
        self.lux_history.append(lux)
        
    def calculate_efficiency_ratio(self) -> Dict:
        """Calculate UV-to-Visible ratio."""
        if len(self.uv_a_history) < 10:
            return {'status': 'Insufficient data'}
            
        uv_a = np.array(list(self.uv_a_history))
        uv_b = np.array(list(self.uv_b_history))
        visible = np.array(list(self.visible_history))
        lux = np.array(list(self.lux_history))
        
        # Calculate total UV
        total_uv = uv_a + uv_b
        
        # UV-to-Visible ratio
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = total_uv / (visible + 1)
            ratio = np.nan_to_num(ratio, nan=0, posinf=0)
            
        current_ratio = ratio[-1]
        avg_ratio = np.mean(ratio[-20:])
        std_ratio = np.std(ratio[-20:])
        
        # Detect ratio spikes
        ratio_spike = current_ratio > avg_ratio + 2 * std_ratio if std_ratio > 0 else False
        
        # Check if visible light didn't increase (isolated UV spike = cleared aerosol)
        visible_change = (visible[-1] - visible[-10]) / (visible[-10] + 1) if len(visible) >= 10 else 0
        
        aerosol_cleared = ratio_spike and abs(visible_change) < 0.2
        
        return {
            'current_ratio': float(current_ratio),
            'average_ratio': float(avg_ratio),
            'ratio_std': float(std_ratio),
            'ratio_spike_detected': bool(ratio_spike),
            'visible_light_change': float(visible_change),
            'aerosol_cleared': aerosol_cleared,
            'interpretation': self._interpret_ratio(current_ratio, avg_ratio, aerosol_cleared)
        }
        
    def _interpret_ratio(self, current: float, average: float, cleared: bool) -> str:
        """Interpret ratio findings."""
        if cleared:
            return "AEROSOL LAYER CLEARED - UV/Visible ratio spike without visible increase indicates haze/smog cleared"
        elif current > average * 1.5:
            return "Elevated UV ratio - possible thinning of atmospheric particles"
        elif current < average * 0.5:
            return "Low UV ratio - dense aerosol layer may be present"
        else:
            return "UV/Visible ratio within normal range"


# ============================================================================
# 3. VIRTUAL HORIZON (Tilt-Compensated Compass)
# ============================================================================

class VirtualHorizon:
    """
    Uses magnetometer and accelerometer for tilt-compensated heading.
    Displays pitch and roll without gyroscope.
    """
    
    def __init__(self):
        self.mag_x_history = deque(maxlen=50)
        self.mag_y_history = deque(maxlen=50)
        self.mag_z_history = deque(maxlen=50)
        self.acc_x_history = deque(maxlen=50)
        self.acc_y_history = deque(maxlen=50)
        self.acc_z_history = deque(maxlen=50)
        
        # Calibration offsets (set during calibration)
        self.mag_offset = (0, 0, 0)
        self.mag_scale = (1, 1, 1)
        
    def calibrate(self, mag_data: List[Tuple[float, float, float]]):
        """
        Perform simple magnetometer calibration.
        Calibrate with figure-8 motion.
        """
        if len(mag_data) < 100:
            return
            
        mag_array = np.array(mag_data)
        
        # Calculate offset (center)
        self.mag_offset = (
            np.mean(mag_array[:, 0]),
            np.mean(mag_array[:, 1]),
            np.mean(mag_array[:, 2])
        )
        
        # Calculate scale (based on min/max range)
        ranges = np.ptp(mag_array, axis=0)
        avg_range = np.mean(ranges)
        self.mag_scale = (avg_range / (ranges[0] + 1e-6),
                         avg_range / (ranges[1] + 1e-6),
                         avg_range / (ranges[2] + 1e-6))
        
    def add_reading(self, mag_x: float, mag_y: float, mag_z: float,
                   acc_x: float, acc_y: float, acc_z: float):
        """Add sensor reading."""
        self.mag_x_history.append(mag_x)
        self.mag_y_history.append(mag_y)
        self.mag_z_history.append(mag_z)
        self.acc_x_history.append(acc_x)
        self.acc_y_history.append(acc_y)
        self.acc_z_history.append(acc_z)
        
    def calculate_orientation(self) -> Dict:
        """Calculate tilt-compensated heading and orientation."""
        if len(self.mag_x_history) < 5:
            return {'status': 'Insufficient data'}
            
        # Get current values
        mag_x = list(self.mag_x_history)[-1]
        mag_y = list(self.mag_y_history)[-1]
        mag_z = list(self.mag_z_history)[-1]
        
        acc_x = list(self.acc_x_history)[-1]
        acc_y = list(self.acc_y_history)[-1]
        acc_z = list(self.acc_z_history)[-1]
        
        # Apply calibration
        mag_x = (mag_x - self.mag_offset[0]) * self.mag_scale[0]
        mag_y = (mag_y - self.mag_offset[1]) * self.mag_scale[1]
        mag_z = (mag_z - self.mag_offset[2]) * self.mag_scale[2]
        
        # Calculate pitch and roll from accelerometer
        pitch = np.degrees(np.arctan2(-acc_x, np.sqrt(acc_y**2 + acc_z**2)))
        roll = np.degrees(np.arctan2(acc_y, acc_z))
        
        # Tilt-compensated heading calculation
        # Normalize accelerometer for tilt compensation
        acc_norm = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        
        if acc_norm > 0:
            # Tilt compensation formulas
            roll_rad = np.radians(roll)
            pitch_rad = np.radians(pitch)
            
            # Rotate magnetometer readings to horizontal plane
            mag_x_comp = mag_x * np.cos(pitch_rad) + mag_z * np.sin(pitch_rad)
            mag_y_comp = mag_x * np.sin(roll_rad) * np.sin(pitch_rad) + mag_y * np.cos(roll_rad) - mag_z * np.sin(roll_rad) * np.cos(pitch_rad)
            
            # Calculate heading
            heading = np.degrees(np.arctan2(-mag_y_comp, mag_x_comp))
            heading = (heading + 360) % 360
            
            # Cardinal direction
            cardinal = self._get_cardinal(heading)
            
            return {
                'heading_deg': float(heading),
                'heading_cardinal': cardinal,
                'pitch_deg': float(pitch),
                'roll_deg': float(roll),
                'tilt_compensated': True
            }
            
        return {
            'heading_deg': 0,
            'heading_cardinal': 'N',
            'pitch_deg': 0,
            'roll_deg': 0,
            'tilt_compensated': False
        }
        
    def _get_cardinal(self, heading: float) -> str:
        """Convert heading to cardinal direction."""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(heading / 22.5) % 16
        return directions[index]
        
    def get_horizon_visualization(self) -> Dict:
        """Get data for 3D virtual horizon display."""
        orientation = self.calculate_orientation()
        
        # Calculate horizon line angle
        horizon_angle = orientation['roll_deg']
        
        return {
            'heading': orientation['heading_deg'],
            'cardinal': orientation['heading_cardinal'],
            'pitch': orientation['pitch_deg'],
            'roll': orientation['roll_deg'],
            'horizon_angle': horizon_angle,
            'attitude_text': f"{orientation['heading_cardinal']} {orientation['pitch_deg']:.1f}°/{orientation['roll_deg']:.1f}°"
        }


# ============================================================================
# 4. GAS SENSOR FUSION RATIO ANALYZER
# ============================================================================

class GasRatioAnalyzer:
    """
    Analyzes gas sensor ratios to identify pollution sources.
    Different sources have distinct chemical signatures.
    """
    
    # Known ratio profiles for pollution sources
    RATIO_PROFILES = {
        'diesel_vehicle': {
            'no2_co_ratio': (0.01, 0.05),
            'nh3_co_ratio': (0.001, 0.01),
            'voc_co_ratio': (0.5, 1.5)
        },
        'gasoline_vehicle': {
            'no2_co_ratio': (0.02, 0.08),
            'nh3_co_ratio': (0.002, 0.02),
            'voc_co_ratio': (0.8, 2.0)
        },
        'wood_smoke': {
            'no2_co_ratio': (0.001, 0.01),
            'nh3_co_ratio': (0.01, 0.05),
            'voc_co_ratio': (0.3, 0.8)
        },
        'industrial': {
            'no2_co_ratio': (0.05, 0.20),
            'nh3_co_ratio': (0.005, 0.03),
            'voc_co_ratio': (2.0, 5.0)
        },
        'agricultural': {
            'no2_co_ratio': (0.001, 0.005),
            'nh3_co_ratio': (0.1, 0.5),
            'voc_co_ratio': (0.2, 0.6)
        }
    }
    
    def __init__(self):
        self.reading_history = deque(maxlen=100)
        
    def add_reading(self, timestamp: float, co: float, no2: float,
                   nh3: float, voc: float):
        """Add gas sensor reading."""
        self.reading_history.append({
            'timestamp': timestamp,
            'co': co,
            'no2': no2,
            'nh3': nh3,
            'voc': voc
        })
        
    def calculate_ratios(self) -> Dict:
        """Calculate gas concentration ratios."""
        if len(self.reading_history) < 5:
            return {'status': 'Insufficient data'}
            
        recent = list(self.reading_history)[-10:]
        
        avg_co = np.mean([r['co'] for r in recent])
        avg_no2 = np.mean([r['no2'] for r in recent])
        avg_nh3 = np.mean([r['nh3'] for r in recent])
        avg_voc = np.mean([r['voc'] for r in recent])
        
        # Calculate ratios
        no2_co_ratio = avg_no2 / (avg_co + 0.01)  # Add small value to avoid div/0
        nh3_co_ratio = avg_nh3 / (avg_co + 0.01)
        voc_co_ratio = avg_voc / (avg_co + 0.01)
        
        return {
            'no2_co_ratio': float(no2_co_ratio),
            'nh3_co_ratio': float(nh3_co_ratio),
            'voc_co_ratio': float(voc_co_ratio),
            'avg_values': {
                'co': float(avg_co),
                'no2': float(avg_no2),
                'nh3': float(avg_nh3),
                'voc': float(avg_voc)
            }
        }
        
    def identify_source(self) -> Dict:
        """Identify pollution source based on ratios."""
        ratios = self.calculate_ratios()
        
        if 'status' in ratios:
            return ratios
            
        scores = {}
        
        for source_name, profile in self.RATIO_PROFILES.items():
            score = 0
            count = 0
            
            # Check each ratio against profile
            if 'no2_co_ratio' in profile:
                low, high = profile['no2_co_ratio']
                if low <= ratios['no2_co_ratio'] <= high:
                    score += 1
                count += 1
                
            if 'nh3_co_ratio' in profile:
                low, high = profile['nh3_co_ratio']
                if low <= ratios['nh3_co_ratio'] <= high:
                    score += 1
                count += 1
                
            if 'voc_co_ratio' in profile:
                low, high = profile['voc_co_ratio']
                if low <= ratios['voc_co_ratio'] <= high:
                    score += 1
                count += 1
                
            scores[source_name] = score / count if count > 0 else 0
            
        # Find best match
        best_source = max(scores, key=scores.get)
        best_score = scores[best_source]
        
        if best_score > 0.5:
            confidence = 'HIGH'
        elif best_score > 0.3:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
            best_source = 'unknown'
            
        return {
            'detected_source': best_source,
            'confidence': confidence,
            'match_scores': scores,
            'ratios': {
                'no2/co': ratios['no2_co_ratio'],
                'nh3/co': ratios['nh3_co_ratio'],
                'voc/co': ratios['voc_co_ratio']
            }
        }


# ============================================================================
# 5. 3D VOLUMETRIC VISUALIZATION DATA
# ============================================================================

class VolumetricVisualizer:
    """
    Generates 3D point cloud data for atmospheric visualization.
    Compatible with PyVista/Three.js.
    """
    
    def __init__(self, resolution: float = 10):  # meters per voxel
        self.resolution = resolution
        self.data_points = deque(maxlen=1000)
        
    def add_reading(self, latitude: float, longitude: float, altitude: float,
                   voc: float, radiation: float, temperature: float, uv_index: float):
        """Add atmospheric reading for 3D mapping."""
        self.data_points.append({
            'lat': latitude,
            'lon': longitude,
            'alt': altitude,
            'voc': voc,
            'radiation': radiation,
            'temp': temperature,
            'uv': uv_index
        })
        
    def generate_pyvista_data(self) -> Dict:
        """Generate PyVista-compatible point cloud."""
        points = []
        colors = []
        
        for d in self.data_points:
            # Convert to local coordinates
            x = (d['lon'] - self.data_points[0]['lon']) * 111320
            y = (d['lat'] - self.data_points[0]['lat']) * 111320
            z = d['alt']
            
            points.append([x, y, z])
            
            # Color based on VOC (green=good, red=high)
            voc_norm = min(1, d['voc'] / 500)
            if voc_norm < 0.3:
                color = [0, 255, 0]  # Green
            elif voc_norm < 0.6:
                color = [255, 255, 0]  # Yellow
            else:
                color = [255, 0, 0]  # Red
                
            colors.append(color)
            
        return {
            'type': 'point_cloud',
            'points': np.array(points).tolist(),
            'colors': colors,
            'point_count': len(points)
        }
        
    def generate_threejs_data(self) -> Dict:
        """Generate Three.js-compatible data."""
        vertices = []
        colors = []
        indices = []
        
        # Group by altitude layers
        layers = {}
        for d in self.data_points:
            layer_z = int(d['alt'] / self.resolution) * self.resolution
            if layer_z not in layers:
                layers[layer_z] = []
            layers[layer_z].append(d)
            
        # Generate mesh for each layer
        idx = 0
        for layer_z, points in sorted(layers.items()):
            if len(points) < 4:
                continue
                
            # Create Delaunay triangulation for each layer
            positions = []
            for p in points:
                x = (p['lon'] - self.data_points[0]['lon']) * 111320
                y = (p['lat'] - self.data_points[0]['lat']) * 111320
                positions.append((x, y))
                
            # Simple grid mesh
            for i, p in enumerate(points):
                x = (p['lon'] - self.data_points[0]['lon']) * 111320
                y = (p['lat'] - self.data_points[0]['lat']) * 111320
                z = layer_z
                
                vertices.extend([x, y, z])
                
                # Color based on VOC
                voc_norm = min(1, p['voc'] / 500)
                if voc_norm < 0.3:
                    colors.extend([0, 1, 0])
                elif voc_norm < 0.6:
                    colors.extend([1, 1, 0])
                else:
                    colors.extend([1, 0, 0])
                    
                if i > 0 and i % 2 == 0:
                    indices.extend([idx-2, idx-1, idx])
                    
                idx += 1
                
        return {
            'vertices': vertices,
            'colors': colors,
            'indices': indices,
            'layer_count': len(layers),
            'bounds': {
                'min_alt': min(d['alt'] for d in self.data_points),
                'max_alt': max(d['alt'] for d in self.data_points)
            }
        }


# ============================================================================
# 6. CIRCULAR BUFFER FOR DATA PERSISTENCE
# ============================================================================

class DualPathCircularBuffer:
    """
    Dual-path data persistence: raw hex packets + parsed CSV.
    Enables replay after GUI crash with zero data loss.
    """
    
    def __init__(self, buffer_size_mb: int = 100):
        self.buffer_size_bytes = buffer_size_mb * 1024 * 1024
        
        # Binary storage for raw packets
        self.binary_buffer = bytearray()
        
        # Text buffer for parsed data
        self.csv_lines = []
        
        # Index for replay
        self.packet_index = 0
        
    def add_packet(self, timestamp: float, packet_type: str, data: bytes, parsed_values: Dict):
        """
        Add a packet to both buffers.
        
        Args:
            timestamp: Packet timestamp
            packet_type: Type identifier
            data: Raw packet bytes
            parsed_values: Parsed dictionary values
        """
        # Pack into binary format
        # Format: timestamp(8) + type(1) + length(2) + data(n) + checksum(2)
        packet_bytes = struct.pack('<dBH', timestamp, ord(packet_type[0]) if packet_type else 0, len(data))
        packet_bytes += data
        
        # Add checksum
        checksum = sum(data) & 0xFFFF
        packet_bytes += struct.pack('<H', checksum)
        
        self.binary_buffer.extend(packet_bytes)
        
        # Add CSV line
        csv_line = f"{timestamp},{packet_type},{data.hex()}"
        for key, value in parsed_values.items():
            csv_line += f",{key}={value}"
        self.csv_lines.append(csv_line)
        
        # Trim buffers if too large
        self._trim_buffers()
        
    def _trim_buffers(self):
        """Trim buffers to max size."""
        # Trim binary buffer
        while len(self.binary_buffer) > self.buffer_size_bytes and len(self.binary_buffer) > 0:
            # Find first complete packet and remove
            if len(self.binary_buffer) >= 11:  # min packet size
                # Read timestamp to find start
                try:
                    timestamp, ptype, length = struct.unpack('<dBH', bytes(self.binary_buffer[:11]))
                    packet_size = 11 + length + 2  # header + data + checksum
                    self.binary_buffer = self.binary_buffer[packet_size:]
                except:
                    self.binary_buffer = self.binary_buffer[11:]
            else:
                break
                
        # Trim CSV
        while len('\n'.join(self.csv_lines).encode()) > self.buffer_size_bytes and self.csv_lines:
            self.csv_lines.pop(0)
            
    def get_replay_data(self) -> Dict:
        """Get data for replay."""
        return {
            'total_packets': len(self.csv_lines),
            'binary_size_bytes': len(self.binary_buffer),
            'csv_size_bytes': len('\n'.join(self.csv_lines).encode()),
            'earliest_timestamp': self.csv_lines[0].split(',')[0] if self.csv_lines else None,
            'latest_timestamp': self.csv_lines[-1].split(',')[0] if self.csv_lines else None
        }
        
    def replay_from_binary(self) -> List[Dict]:
        """Replay all packets from binary buffer."""
        packets = []
        offset = 0
        
        while offset + 11 <= len(self.binary_buffer):
            try:
                timestamp, ptype, length = struct.unpack('<dBH', bytes(self.binary_buffer[offset:offset+11]))
                
                if offset + 11 + length + 2 > len(self.binary_buffer):
                    break
                    
                data = bytes(self.binary_buffer[offset+11:offset+11+length])
                stored_checksum = struct.unpack('<H', bytes(self.binary_buffer[offset+11+length:offset+11+length+2]))[0]
                
                # Verify checksum
                calculated_checksum = sum(data) & 0xFFFF
                
                packets.append({
                    'timestamp': timestamp,
                    'type': chr(ptype),
                    'data': data,
                    'valid': calculated_checksum == stored_checksum
                })
                
                offset += 11 + length + 2
                
            except Exception as e:
                print(f"Replay error: {e}")
                break
                
        return packets
        
    def export_csv(self, filename: str):
        """Export parsed data to CSV file."""
        header = "timestamp,packet_type,raw_data"
        
        with open(filename, 'w') as f:
            f.write(header + '\n')
            f.write('\n'.join(self.csv_lines))


# ============================================================================
# UNIFIED ADVANCED SIGNAL PROCESSOR
# ============================================================================

class AdvancedSignalProcessor:
    """
    Complete advanced signal processing system.
    """
    
    def __init__(self):
        self.rssi_mapper = RSSIHeatMapper()
        self.luminous_index = LuminousEfficiencyIndex()
        self.virtual_horizon = VirtualHorizon()
        self.gas_ratio = GasRatioAnalyzer()
        self.volumetric = VolumetricVisualizer()
        self.dual_buffer = DualPathCircularBuffer()
        
    def process_all(self, data: Dict) -> Dict:
        """Process all sensor data."""
        timestamp = data.get('timestamp', 0)
        
        # RSSI mapping
        if all(k in data for k in ['latitude', 'longitude', 'rssi']):
            self.rssi_mapper.add_reading(
                timestamp, data['latitude'], data['longitude'],
                data['rssi'], data.get('snr', 0)
            )
            
        # Luminous efficiency
        if all(k in data for k in ['uv_a', 'visible', 'lux']):
            self.luminous_index.add_reading(
                timestamp,
                data.get('uv_a', 0),
                data.get('uv_b', 0),
                data.get('visible', 0),
                data['lux']
            )
            
        # Virtual horizon
        if all(k in data for k in ['mag_x', 'acc_x']):
            self.virtual_horizon.add_reading(
                data['mag_x'], data['mag_y'], data['mag_z'],
                data['acc_x'], data['acc_y'], data['acc_z']
            )
            
        # Gas ratio analysis
        if all(k in data for k in ['co', 'no2']):
            self.gas_ratio.add_reading(
                timestamp,
                data.get('co', 0),
                data.get('no2', 0),
                data.get('nh3', 0),
                data.get('voc', 0)
            )
            
        # Volumetric data
        if all(k in data for k in ['latitude', 'longitude', 'altitude', 'voc']):
            self.volumetric.add_reading(
                data['latitude'], data['longitude'], data['altitude'],
                data.get('voc', 0), data.get('radiation', 0),
                data.get('temperature', 20), data.get('uv_index', 0)
            )
            
        return self.get_report()
        
    def get_report(self) -> Dict:
        """Get comprehensive signal processing report."""
        return {
            'rssi_heatmap': self.rssi_mapper.get_signal_map(),
            'rf_shadow_report': self.rssi_mapper.get_rf_shadow_report(),
            'luminous_efficiency': self.luminous_index.calculate_efficiency_ratio(),
            'virtual_horizon': self.virtual_horizon.get_horizon_visualization(),
            'gas_source_identification': self.gas_ratio.identify_source(),
            'volumetric_3d': self.volumetric.generate_pyvista_data(),
            'buffer_status': self.dual_buffer.get_replay_data()
        }


def create_advanced_processor() -> AdvancedSignalProcessor:
    """Factory function."""
    return AdvancedSignalProcessor()


if __name__ == "__main__":
    print("=" * 60)
    print("Advanced Signal Processing System")
    print("=" * 60)
    
    processor = create_advanced_processor()
    
    print("\nSimulating advanced signal processing...")
    
    for i in range(100):
        data = {
            'timestamp': i * 2,
            'latitude': 37.7749 + i * 0.00001,
            'longitude': -122.4194 + i * 0.00001,
            'altitude': 1000 - i * 10,
            'rssi': -65 + np.random.normal(0, 5),
            'snr': 15 + np.random.normal(0, 3),
            'uv_a': 50 + np.random.normal(10, 5),
            'uv_b': 20 + np.random.normal(5, 2),
            'visible': 10000 - i * 100,
            'lux': 10000 - i * 100,
            'mag_x': 25 + np.random.normal(0, 2),
            'mag_y': -10 + np.random.normal(0, 2),
            'mag_z': 35 + np.random.normal(0, 2),
            'acc_x': 0.5 + np.random.normal(0, 0.1),
            'acc_y': 0.1 + np.random.normal(0, 0.1),
            'acc_z': 9.8 + np.random.normal(0, 0.1),
            'co': 2 + np.random.normal(1, 0.5),
            'no2': 10 + np.random.normal(5, 2),
            'nh3': 5 + np.random.normal(2, 1),
            'voc': 200 + np.random.normal(100, 30),
            'radiation': 0.5 + 0.002 * i,
            'temperature': 20 - i * 0.015,
            'uv_index': 5 + np.random.normal(1, 0.5)
        }
        
        processor.process_all(data)
        
        if i % 25 == 0:
            report = processor.get_report()
            print(f"\n--- t={i*2}s ---")
            print(f"RSSI Map: {len(report['rssi_heatmap']['grid_points'])} points")
            print(f"Signal: {report['luminous_efficiency'].get('interpretation', 'N/A')}")
            horizon = report['virtual_horizon']
            print(f"Virtual Horizon: {horizon.get('heading', 0):.1f}° {horizon.get('cardinal', 'N')}")
            print(f"Gas Source: {report['gas_source_identification'].get('detected_source', 'Unknown')}")
            
    print("\n" + "=" * 60)
    print("Advanced Signal Processor Ready!")
    print("=" * 60)