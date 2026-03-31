"""
AirOne Professional v4.0 - Telemetry Analyzer
Advanced telemetry data analysis and visualization
"""
# -*- coding: utf-8 -*-

import json
import math
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class TelemetryAnalyzer:
    """Analyze telemetry data"""
    
    def __init__(self):
        self.data: List[Dict[str, Any]] = []
        self.statistics: Dict[str, Any] = {}
        self.anomalies: List[Dict[str, Any]] = []
        
    def load_data(self, filepath: str) -> bool:
        """Load telemetry data from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.data = data
            elif isinstance(data, dict) and 'telemetry' in data:
                self.data = data['telemetry']
            else:
                self.data = [data]
            
            logger.info(f"Loaded {len(self.data)} telemetry records")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def load_from_list(self, data: List[Dict[str, Any]]):
        """Load data from list"""
        self.data = data
        return self
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        if not self.data:
            return {'error': 'No data loaded'}
        
        # Numeric fields to analyze
        numeric_fields = ['altitude', 'velocity', 'temperature', 'pressure', 
                         'battery', 'signal_strength', 'latitude', 'longitude']
        
        stats = {
            'record_count': len(self.data),
            'time_range': self._calculate_time_range(),
            'fields': {}
        }
        
        for field in numeric_fields:
            values = [d.get(field) for d in self.data if d.get(field) is not None]
            
            if values:
                stats['fields'][field] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'count': len(values)
                }
        
        # Flight phase analysis
        phases = defaultdict(int)
        for record in self.data:
            phase = record.get('flight_phase', 'UNKNOWN')
            phases[phase] += 1
        
        stats['flight_phases'] = dict(phases)
        
        self.statistics = stats
        return stats
    
    def _calculate_time_range(self) -> Dict[str, Any]:
        """Calculate time range of data"""
        if not self.data:
            return {}
        
        timestamps = []
        for record in self.data:
            ts = record.get('timestamp')
            if ts:
                try:
                    if isinstance(ts, str):
                        timestamps.append(datetime.fromisoformat(ts))
                except:
                    pass
        
        if not timestamps:
            return {}
        
        start = min(timestamps)
        end = max(timestamps)
        duration = (end - start).total_seconds()
        
        return {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'duration_seconds': duration
        }
    
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in telemetry data"""
        if not self.data:
            return []
        
        self.anomalies = []
        
        # Calculate baseline statistics
        fields = ['altitude', 'velocity', 'temperature', 'pressure']
        baselines = {}
        
        for field in fields:
            values = [d.get(field) for d in self.data if d.get(field) is not None]
            if values:
                avg = sum(values) / len(values)
                std = math.sqrt(sum((x - avg) ** 2 for x in values) / len(values))
                baselines[field] = {'avg': avg, 'std': std}
        
        # Detect anomalies
        for i, record in enumerate(self.data):
            for field, baseline in baselines.items():
                value = record.get(field)
                if value is not None and baseline['std'] > 0:
                    z_score = abs(value - baseline['avg']) / baseline['std']
                    
                    if z_score > threshold:
                        anomaly = {
                            'index': i,
                            'field': field,
                            'value': value,
                            'expected': baseline['avg'],
                            'z_score': z_score,
                            'severity': 'high' if z_score > 3 else 'medium',
                            'timestamp': record.get('timestamp')
                        }
                        self.anomalies.append(anomaly)
        
        logger.info(f"Detected {len(self.anomalies)} anomalies")
        return self.anomalies
    
    def analyze_flight_profile(self) -> Dict[str, Any]:
        """Analyze flight profile"""
        if not self.data:
            return {}
        
        altitudes = [d.get('altitude', 0) for d in self.data if d.get('altitude') is not None]
        
        if not altitudes:
            return {}
        
        # Find max altitude and when it occurred
        max_alt = max(altitudes)
        max_alt_index = altitudes.index(max_alt)
        
        # Calculate ascent and descent rates
        ascent_rates = []
        descent_rates = []
        
        for i in range(1, len(self.data)):
            if i < len(altitudes):
                alt_diff = altitudes[i] - altitudes[i-1]
                time_diff = 1  # Assume 1 second between records
                
                if alt_diff > 0:
                    ascent_rates.append(alt_diff / time_diff)
                elif alt_diff < 0:
                    descent_rates.append(abs(alt_diff) / time_diff)
        
        return {
            'max_altitude': max_alt,
            'max_altitude_time': self.data[max_alt_index].get('timestamp') if max_alt_index < len(self.data) else None,
            'avg_ascent_rate': sum(ascent_rates) / len(ascent_rates) if ascent_rates else 0,
            'avg_descent_rate': sum(descent_rates) / len(descent_rates) if descent_rates else 0,
            'flight_duration': len(self.data),
            'apogee_index': max_alt_index
        }
    
    def generate_report(self, format: str = 'json') -> str:
        """Generate analysis report"""
        report = {
            'analysis_date': datetime.now().isoformat(),
            'data_summary': {
                'records': len(self.data),
                'time_range': self.statistics.get('time_range', {})
            },
            'statistics': self.statistics.get('fields', {}),
            'flight_profile': self.analyze_flight_profile(),
            'anomalies': {
                'count': len(self.anomalies),
                'details': self.anomalies[:20]  # First 20 anomalies
            },
            'recommendations': self._generate_recommendations()
        }
        
        if format == 'json':
            return json.dumps(report, indent=2)
        elif format == 'txt':
            return self._format_report_txt(report)
        else:
            return json.dumps(report, indent=2)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for anomalies
        if len(self.anomalies) > 10:
            recommendations.append("High number of anomalies detected - review sensor calibration")
        
        # Check battery
        battery_stats = self.statistics.get('fields', {}).get('battery', {})
        if battery_stats.get('min', 100) < 20:
            recommendations.append("Battery dropped below 20% - consider capacity upgrade")
        
        # Check signal
        signal_stats = self.statistics.get('fields', {}).get('signal_strength', {})
        if signal_stats.get('avg', 0) < -70:
            recommendations.append("Weak average signal - check antenna placement")
        
        if not recommendations:
            recommendations.append("All systems nominal - no issues detected")
        
        return recommendations
    
    def _format_report_txt(self, report: Dict[str, Any]) -> str:
        """Format report as text"""
        lines = [
            "="*70,
            "AirOne Professional v4.0 - Telemetry Analysis Report",
            "="*70,
            "",
            f"Analysis Date: {report['analysis_date']}",
            f"Records Analyzed: {report['data_summary']['records']}",
            "",
            "STATISTICS:",
            "-"*40
        ]
        
        for field, stats in report['statistics'].items():
            lines.append(f"  {field}:")
            lines.append(f"    Min: {stats['min']:.2f}")
            lines.append(f"    Max: {stats['max']:.2f}")
            lines.append(f"    Avg: {stats['avg']:.2f}")
        
        lines.extend([
            "",
            "FLIGHT PROFILE:",
            "-"*40,
            f"  Max Altitude: {report['flight_profile'].get('max_altitude', 0):.2f} m",
            f"  Avg Ascent Rate: {report['flight_profile'].get('avg_ascent_rate', 0):.2f} m/s",
            f"  Avg Descent Rate: {report['flight_profile'].get('avg_descent_rate', 0):.2f} m/s",
            "",
            "ANOMALIES:",
            "-"*40,
            f"  Total Detected: {report['anomalies']['count']}",
            "",
            "RECOMMENDATIONS:",
            "-"*40
        ])
        
        for rec in report['recommendations']:
            lines.append(f"  • {rec}")
        
        lines.extend([
            "",
            "="*70
        ])
        
        return "\n".join(lines)
    
    def export_analysis(self, output_path: str, format: str = 'json'):
        """Export analysis to file"""
        report = self.generate_report(format)
        
        Path(output_path).parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Analysis exported to: {output_path}")
        return output_path


class RealTimeAnalyzer:
    """Real-time telemetry analysis"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_window: List[Dict[str, Any]] = []
        self.running_stats: Dict[str, Any] = {}
    
    def add_reading(self, reading: Dict[str, Any]):
        """Add new telemetry reading"""
        self.data_window.append(reading)
        
        # Maintain window size
        if len(self.data_window) > self.window_size:
            self.data_window.pop(0)
        
        # Update running statistics
        self._update_stats()
    
    def _update_stats(self):
        """Update running statistics"""
        if not self.data_window:
            return
        
        # Calculate running averages
        fields = ['altitude', 'velocity', 'temperature', 'pressure', 'battery']
        
        for field in fields:
            values = [d.get(field) for d in self.data_window if d.get(field) is not None]
            if values:
                self.running_stats[f'{field}_avg'] = sum(values) / len(values)
                self.running_stats[f'{field}_min'] = min(values)
                self.running_stats[f'{field}_max'] = max(values)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            'window_size': len(self.data_window),
            'stats': self.running_stats,
            'latest': self.data_window[-1] if self.data_window else None
        }
    
    def is_anomalous(self, field: str, threshold: float = 2.0) -> bool:
        """Check if current reading is anomalous"""
        if not self.data_window or field not in self.running_stats:
            return False
        
        current = self.data_window[-1].get(field)
        if current is None:
            return False
        
        avg = self.running_stats.get(f'{field}_avg', current)
        
        # Simple anomaly detection
        deviation = abs(current - avg)
        expected_range = abs(self.running_stats.get(f'{field}_max', avg) - 
                           self.running_stats.get(f'{field}_min', avg))
        
        if expected_range > 0:
            return deviation > (expected_range * threshold)
        
        return False


def analyze_telemetry(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Quick telemetry analysis"""
    analyzer = TelemetryAnalyzer()
    analyzer.load_from_list(data)
    stats = analyzer.calculate_statistics()
    anomalies = analyzer.detect_anomalies()
    
    return {
        'statistics': stats,
        'anomalies': anomalies,
        'flight_profile': analyzer.analyze_flight_profile(),
        'report': analyzer.generate_report()
    }


if __name__ == "__main__":
    # Test telemetry analyzer
    print("="*70)
    print("  AirOne Professional v4.0 - Telemetry Analyzer Test")
    print("="*70)
    print()
    
    # Create test data
    import random
    
    test_data = []
    base_time = datetime.now()
    
    for i in range(100):
        timestamp = (base_time.timestamp() + i) 
        altitude = 500 * math.sin(math.pi * i / 50) + random.uniform(-10, 10)
        
        test_data.append({
            'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
            'altitude': max(0, altitude),
            'velocity': random.uniform(10, 30),
            'temperature': 25 - (altitude / 100) + random.uniform(-2, 2),
            'pressure': 1013.25 - (altitude / 10) + random.uniform(-5, 5),
            'battery': 100 - (i / 100) * 20,
            'signal_strength': random.randint(-80, -40),
            'flight_phase': 'ASCENT' if i < 50 else 'DESCENT'
        })
    
    print(f"Generated {len(test_data)} test records")
    print()
    
    # Analyze
    analyzer = TelemetryAnalyzer()
    analyzer.load_from_list(test_data)
    
    print("Calculating statistics...")
    stats = analyzer.calculate_statistics()
    print(f"  Records: {stats['record_count']}")
    print(f"  Fields analyzed: {len(stats['fields'])}")
    
    print()
    print("Detecting anomalies...")
    anomalies = analyzer.detect_anomalies()
    print(f"  Anomalies found: {len(anomalies)}")
    
    print()
    print("Analyzing flight profile...")
    profile = analyzer.analyze_flight_profile()
    print(f"  Max altitude: {profile.get('max_altitude', 0):.2f} m")
    print(f"  Avg ascent rate: {profile.get('avg_ascent_rate', 0):.2f} m/s")
    
    print()
    print("Generating report...")
    report = analyzer.generate_report('txt')
    print(report)
    
    print()
    print("="*70)
    print("  Telemetry Analyzer Test Complete")
    print("="*70)
