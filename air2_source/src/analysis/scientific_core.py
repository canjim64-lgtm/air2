"""
Scientific Analysis Core for AirOne v3.0
Handles data analysis and scientific computations
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


class ScientificAnalysisCore:
    """Core scientific analysis engine for AirOne system"""
    
    def __init__(self):
        self.analysis_methods = {
            'altitude_profile': self.analyze_altitude_profile,
            'temperature_trend': self.analyze_temperature_trend,
            'pressure_altitude': self.analyze_pressure_altitude,
            'battery_consumption': self.analyze_battery_consumption,
            'gps_accuracy': self.analyze_gps_accuracy,
            'signal_strength': self.analyze_signal_strength
        }
        
    def analyze_altitude_profile(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze altitude profile from telemetry data"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        altitudes = [point.get('altitude', 0) for point in telemetry_data if 'altitude' in point]
        
        if not altitudes:
            return {'error': 'No altitude data in telemetry'}
            
        analysis_result = {
            'min_altitude': min(altitudes),
            'max_altitude': max(altitudes),
            'avg_altitude': sum(altitudes) / len(altitudes),
            'total_ascent': 0,
            'total_descent': 0,
            'apogee_time': None
        }
        
        # Calculate ascent/descent
        for i in range(1, len(altitudes)):
            diff = altitudes[i] - altitudes[i-1]
            if diff > 0:
                analysis_result['total_ascent'] += diff
            else:
                analysis_result['total_descent'] += abs(diff)
                
        # Find apogee
        max_alt_idx = altitudes.index(max(altitudes))
        if telemetry_data[max_alt_idx].get('timestamp'):
            analysis_result['apogee_time'] = telemetry_data[max_alt_idx]['timestamp']
            
        return analysis_result
    
    def analyze_temperature_trend(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temperature trends from telemetry data"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        temperatures = [point.get('temperature', 0) for point in telemetry_data if 'temperature' in point]
        
        if not temperatures:
            return {'error': 'No temperature data in telemetry'}
            
        analysis_result = {
            'min_temp': min(temperatures),
            'max_temp': max(temperatures),
            'avg_temp': sum(temperatures) / len(temperatures),
            'temp_variance': np.var(temperatures),
            'temp_std_dev': np.std(temperatures)
        }
        
        return analysis_result
    
    def analyze_pressure_altitude(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pressure and derive altitude from barometric data"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        pressures = [point.get('pressure', 0) for point in telemetry_data if 'pressure' in point]
        
        if not pressures:
            return {'error': 'No pressure data in telemetry'}
            
        # Barometric formula: h = (T0/L) * ((P/P0)^(-(R*L)/(g*M)) - 1)
        # Simplified: altitude ≈ (1 - (P/P0)^(1/5.25588)) * 44330
        P0 = 1013.25  # Standard sea level pressure in hPa
        altitudes = []
        
        for pressure in pressures:
            if pressure > 0:
                altitude = (1 - pow(pressure / P0, 1/5.25588)) * 44330
                altitudes.append(altitude)
        
        analysis_result = {
            'derived_altitudes': altitudes,
            'pressure_range': {'min': min(pressures), 'max': max(pressures)},
            'altitude_range_from_pressure': {
                'min': min(altitudes) if altitudes else 0,
                'max': max(altitudes) if altitudes else 0
            }
        }
        
        return analysis_result
    
    def analyze_battery_consumption(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze battery consumption patterns"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        battery_levels = [point.get('battery_level', 0) for point in telemetry_data if 'battery_level' in point]
        
        if not battery_levels:
            return {'error': 'No battery data in telemetry'}
            
        analysis_result = {
            'initial_level': battery_levels[0] if battery_levels else 0,
            'current_level': battery_levels[-1] if battery_levels else 0,
            'consumed': battery_levels[0] - battery_levels[-1] if len(battery_levels) > 0 else 0,
            'average_consumption_rate': 0,
            'estimated_runtime_remaining': 0
        }
        
        if len(battery_levels) > 1:
            total_consumed = battery_levels[0] - battery_levels[-1]
            
            # Calculate time_span using actual timestamps
            if len(telemetry_data) > 1 and 'timestamp' in telemetry_data[0] and 'timestamp' in telemetry_data[-1]:
                time_span = telemetry_data[-1]['timestamp'] - telemetry_data[0]['timestamp']
            else:
                time_span = len(telemetry_data)  # Fallback to number of points if timestamps not available
            
            analysis_result['average_consumption_rate'] = total_consumed / time_span if time_span > 0 else 0
            
            # Estimate runtime remaining based on current consumption rate
            current_level = battery_levels[-1]
            rate = analysis_result['average_consumption_rate']
            analysis_result['estimated_runtime_remaining'] = current_level / rate if rate > 0 else float('inf')
        
        return analysis_result
    
    def analyze_gps_accuracy(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze GPS accuracy and positioning data"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        positions = [(point.get('latitude', 0), point.get('longitude', 0)) 
                     for point in telemetry_data 
                     if 'latitude' in point and 'longitude' in point]
        
        if len(positions) < 2:
            return {'error': 'Insufficient position data for accuracy analysis'}
            
        # Calculate distances between consecutive points to estimate movement
        distances = []
        for i in range(1, len(positions)):
            lat1, lon1 = positions[i-1]
            lat2, lon2 = positions[i]
            
            # Simple distance calculation (not geodesic for simplicity)
            d_lat = (lat2 - lat1) * 111000  # Approximate meters per degree latitude
            d_lon = (lon2 - lon1) * 111000 * np.cos(np.radians((lat1 + lat2) / 2))
            distance = np.sqrt(d_lat**2 + d_lon**2)
            distances.append(distance)
        
        analysis_result = {
            'total_distance_traveled': sum(distances),
            'avg_step_distance': sum(distances) / len(distances) if distances else 0,
            'max_step_distance': max(distances) if distances else 0,
            'num_position_fixes': len(positions),
            'latitude_variance': np.var([pos[0] for pos in positions]) if positions else 0,
            'longitude_variance': np.var([pos[1] for pos in positions]) if positions else 0,
            'average_position': (np.mean([pos[0] for pos in positions]), np.mean([pos[1] for pos in positions])) if positions else (0,0)
        }
        
        return analysis_result
    
    def analyze_signal_strength(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze signal strength and communication quality"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}
            
        signal_strengths = [point.get('radio_signal_strength', -999) 
                           for point in telemetry_data 
                           if 'radio_signal_strength' in point and point['radio_signal_strength'] != -999]
        
        if not signal_strengths:
            return {'error': 'No signal strength data in telemetry'}
            
        analysis_result = {
            'avg_signal_strength': sum(signal_strengths) / len(signal_strengths),
            'min_signal_strength': min(signal_strengths),
            'max_signal_strength': max(signal_strengths),
            'signal_variance': np.var(signal_strengths),
            'signal_std_dev': np.std(signal_strengths),
            'signal_quality_percentage': len(signal_strengths) / len(telemetry_data) * 100
        }
        
        return analysis_result
    
    def run_analysis(self, analysis_type: str, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a specific type of analysis"""
        if analysis_type not in self.analysis_methods:
            return {'error': f'Unknown analysis type: {analysis_type}'}
            
        return self.analysis_methods[analysis_type](telemetry_data)
    
    def run_comprehensive_analysis(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all available analyses on the telemetry data"""
        results = {}
        
        for analysis_type in self.analysis_methods:
            try:
                results[analysis_type] = self.run_analysis(analysis_type, telemetry_data)
            except Exception as e:
                results[analysis_type] = {'error': f'Analysis failed: {str(e)}'}
        
        return results