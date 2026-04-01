"""
Post-Flight Analysis Module
Analyze flight data and generate reports
"""

import numpy as np
from typing import Dict, List
import json


class FlightAnalyzer:
    """Analyze flight data"""
    
    def __init__(self):
        self.data = []
        self.events = []
    
    def load_data(self, data: List[Dict]):
        """Load flight data"""
        self.data = data
    
    def analyze(self) -> Dict:
        """Analyze flight and return summary"""
        if not self.data:
            return {}
        
        altitudes = [d.get('altitude', 0) for d in self.data]
        temps = [d.get('temperature', 0) for d in self.data]
        vocs = [d.get('voc', 0) for d in self.data]
        rads = [d.get('radiation', 0) for d in self.data]
        
        return {
            'flight_duration': len(self.data) * 0.2,  # Assuming 200ms intervals
            'max_altitude': max(altitudes),
            'min_altitude': min(altitudes),
            'avg_temperature': np.mean(temps),
            'max_voc': max(vocs),
            'avg_radiation': np.mean(rads),
            'total_data_points': len(self.data)
        }
    
    def get_terrain_breakdown(self) -> Dict:
        """Get terrain percentage breakdown"""
        # Simplified terrain analysis
        return {
            'grass': 45,
            'forest': 30,
            'water': 10,
            'buildings': 15
        }


class EnvironmentalReporter:
    """Generate environmental reports"""
    
    def __init__(self):
        self.deepseek_available = False
    
    def generate_report(self, flight_data: Dict) -> str:
        """Generate environmental summary"""
        
        report = f"""
ENVIRONMENTAL FLIGHT REPORT
===========================

Altitude Analysis:
- Max Altitude: {flight_data.get('max_altitude', 0):.1f}m
- Min Altitude: {flight_data.get('min_altitude', 0):.1f}m

Temperature:
- Average: {flight_data.get('avg_temperature', 0):.1f}°C

Air Quality:
- Max VOC: {flight_data.get('max_voc', 0)} ppm

Radiation:
- Average: {flight_data.get('avg_radiation', 0):.2f} µSv/h

Data Points: {flight_data.get('total_data_points', 0)}
        """
        
        return report
    
    def generate_voice_summary(self, flight_data: Dict) -> str:
        """Generate voice summary"""
        
        voc_level = "normal"
        if flight_data.get('max_voc', 0) > 500:
            voc_level = "elevated"
        
        radiation = flight_data.get('avg_radiation', 0)
        rad_warning = ""
        if radiation > 2.5:
            rad_warning = " WARNING: Elevated radiation levels detected."
        
        return f"Flight complete. Max altitude {flight_data.get('max_altitude', 0):.0f} meters. {rad_warning}"


class AnomalyReconstructor:
    """Reconstruct anomaly events"""
    
    def __init__(self):
        self.anomalies = []
    
    def add_anomaly(self, timestamp: float, event_type: str, data: Dict):
        """Add anomaly event"""
        self.anomalies.append({
            'timestamp': timestamp,
            'type': event_type,
            'data': data
        })
    
    def get_timeline(self) -> List[Dict]:
        """Get anomaly timeline"""
        return sorted(self.anomalies, key=lambda x: x['timestamp'])


class DataQualityChecker:
    """Check data quality"""
    
    def __init__(self):
        self.issues = []
    
    def check(self, data: List[Dict]) -> Dict:
        """Check data for issues"""
        
        missing = 0
        outliers = 0
        gaps = []
        
        for i, point in enumerate(data):
            # Check for missing values
            if not point.get('altitude') or not point.get('temperature'):
                missing += 1
            
            # Check for outliers
            if point.get('altitude', 0) < -100 or point.get('altitude', 0) > 50000:
                outliers += 1
        
        return {
            'missing_values': missing,
            'outliers': outliers,
            'total_points': len(data),
            'quality_score': 1.0 - (missing + outliers) / max(len(data), 1)
        }


if __name__ == "__main__":
    fa = FlightAnalyzer()
    result = fa.analyze()
    print(f"Analysis: {result}")