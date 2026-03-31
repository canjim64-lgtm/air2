"""
DeepSeek AI Telemetry Analytics Module
Advanced AI-powered telemetry analysis with DeepSeek integration
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import queue
import time
import json
import logging
from collections import deque


class AnalysisType(Enum):
    """Types of AI analysis"""
    CORRELATION = "correlation"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"
    ANOMALY = "anomaly"
    CAUSAL = "causal"


@dataclass
class AITelemetryInsight:
    """AI-generated insight from telemetry"""
    insight_type: AnalysisType
    title: str
    description: str
    confidence: float
    evidence: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime


class DeepSeekTelemetryAnalytics:
    """DeepSeek-powered telemetry analytics engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DeepSeekAnalytics")
        
        # Data storage
        self.telemetry_buffer: deque = deque(maxlen=10000)
        self.parameter_cache: Dict[str, List[float]] = {}
        
        # Analysis results cache
        self.insights: List[AITelemetryInsight] = []
        
        # Configuration
        self.confidence_threshold = 0.7
        self.min_data_points = 20
        
        self.logger.info("DeepSeek Telemetry Analytics initialized")
    
    def add_telemetry(self, telemetry: Dict[str, Any]):
        """Add telemetry data"""
        telemetry['ingest_time'] = time.time()
        self.telemetry_buffer.append(telemetry)
        
        # Update parameter cache
        for key, value in telemetry.items():
            if isinstance(value, (int, float)):
                if key not in self.parameter_cache:
                    self.parameter_cache[key] = []
                self.parameter_cache[key].append(value)
    
    def analyze_parameter_correlations(self) -> AITelemetryInsight:
        """Analyze correlations between parameters"""
        
        if len(self.telemetry_buffer) < self.min_data_points:
            return self._create_insufficient_data_insight(AnalysisType.CORRELATION)
        
        # Calculate correlation matrix
        params = list(self.parameter_cache.keys())
        n_params = len(params)
        
        if n_params < 2:
            return self._create_insufficient_data_insight(AnalysisType.CORRELATION)
        
        correlations = []
        
        for i in range(n_params):
            for j in range(i + 1, n_params):
                p1, p2 = params[i], params[j]
                
                if (len(self.parameter_cache[p1]) > 10 and 
                    len(self.parameter_cache[p2]) > 10):
                    
                    min_len = min(len(self.parameter_cache[p1]), 
                                 len(self.parameter_cache[p2]))
                    
                    corr = np.corrcoef(
                        np.array(self.parameter_cache[p1][:min_len]),
                        np.array(self.parameter_cache[p2][:min_len])
                    )[0, 1]
                    
                    if not np.isnan(corr):
                        correlations.append({
                            'params': (p1, p2),
                            'correlation': float(corr),
                            'abs_correlation': abs(corr)
                        })
        
        # Sort by absolute correlation
        correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
        
        # Generate insights
        strong_correlations = [c for c in correlations if c['abs_correlation'] > 0.7]
        
        title = "Parameter Correlation Analysis"
        
        if strong_correlations:
            top = strong_correlations[0]
            description = (
                f"Strong correlation detected between '{top['params'][0]}' "
                f"and '{top['params'][1]}' (r={top['correlation']:.3f}). "
                f"This suggests these parameters may be related or "
                f"one may influence the other."
            )
            
            recommendations = [
                "Investigate the causal relationship between these parameters",
                "Consider using multi-variate analysis models",
                "Monitor both parameters together for anomaly detection"
            ]
        else:
            description = (
                "No strong correlations found between parameters. "
                "Parameters appear to vary independently."
            )
            recommendations = [
                "Continue monitoring for emerging patterns",
                "Consider analyzing time-lagged correlations"
            ]
        
        evidence = {
            'strong_correlations': strong_correlations[:5],
            'total_correlations_analyzed': len(correlations),
            'parameters_analyzed': params
        }
        
        confidence = min(1.0, len(self.telemetry_buffer) / 100)
        
        insight = AITelemetryInsight(
            insight_type=AnalysisType.CORRELATION,
            title=title,
            description=description,
            confidence=confidence,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.insights.append(insight)
        return insight
    
    def detect_anomalies(self) -> AITelemetryInsight:
        """Detect anomalies in telemetry data"""
        
        if len(self.telemetry_buffer) < self.min_data_points:
            return self._create_insufficient_data_insight(AnalysisType.ANOMALY)
        
        anomalies = []
        
        for param, values in self.parameter_cache.items():
            if len(values) < 20:
                continue
            
            values_arr = np.array(values)
            
            # Calculate statistics
            mean = np.mean(values_arr)
            std = np.std(values_arr)
            
            # Find outliers using z-score
            for i, val in enumerate(values_arr):
                z_score = abs((val - mean) / (std + 1e-10))
                
                if z_score > 3.0:
                    anomalies.append({
                        'parameter': param,
                        'value': float(val),
                        'expected_range': (mean - 3*std, mean + 3*std),
                        'z_score': float(z_score),
                        'index': i,
                        'severity': 'high' if z_score > 4 else 'medium'
                    })
        
        # Generate insights
        if anomalies:
            high_severity = [a for a in anomalies if a['severity'] == 'high']
            
            description = (
                f"Detected {len(anomalies)} anomalies across telemetry parameters. "
                f"{len(high_severity)} are classified as high severity."
            )
            
            recommendations = [
                "Investigate high-severity anomalies immediately",
                "Check sensor calibration",
                "Review environmental conditions during anomalies"
            ]
        else:
            description = "No significant anomalies detected in telemetry data."
            recommendations = ["Continue monitoring", "All parameters within normal ranges"]
        
        evidence = {
            'total_anomalies': len(anomalies),
            'anomalies': anomalies[:10],
            'parameters_checked': list(self.parameter_cache.keys())
        }
        
        confidence = min(1.0, len(self.telemetry_buffer) / 50)
        
        insight = AITelemetryInsight(
            insight_type=AnalysisType.ANOMALY,
            title="Anomaly Detection Analysis",
            description=description,
            confidence=confidence,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.insights.append(insight)
        return insight
    
    def forecast_parameter(self, parameter: str, 
                          horizon: int = 10) -> AITelemetryInsight:
        """Forecast future parameter values"""
        
        if parameter not in self.parameter_cache:
            return self._create_insufficient_data_insight(AnalysisType.FORECASTING)
        
        values = self.parameter_cache[parameter]
        
        if len(values) < self.min_data_points:
            return self._create_insufficient_data_insight(AnalysisType.FORECASTING)
        
        values_arr = np.array(values)
        
        # Fit polynomial
        x = np.arange(len(values_arr))
        
        # Try different degrees
        best_degree = 1
        best_score = -np.inf
        
        for degree in [1, 2, 3]:
            if degree >= len(values_arr):
                continue
            try:
                coeffs = np.polyfit(x, values_arr, degree)
                preds = np.polyval(coeffs, x)
                score = 1 - np.sum((values_arr - preds)**2) / (
                    np.var(values_arr) * len(values_arr) + 1e-10
                )
                if score > best_score:
                    best_score = score
                    best_degree = degree
            except:
                continue
        
        # Generate forecast
        coeffs = np.polyfit(x, values_arr, best_degree)
        future_x = np.arange(len(values_arr), len(values_arr) + horizon)
        forecast = np.polyval(coeffs, future_x)
        
        # Calculate confidence
        confidence = min(1.0, max(0.0, best_score))
        
        # Description
        last_value = values_arr[-1]
        predicted_change = forecast[-1] - last_value
        direction = "increase" if predicted_change > 0 else "decrease"
        
        description = (
            f"Forecast for '{parameter}' over next {horizon} time steps. "
            f"Current value: {last_value:.2f}. "
            f"Predicted to {direction} to {forecast[-1]:.2f} "
            f"(change: {predicted_change:.2f})."
        )
        
        recommendations = [
            "Monitor forecast accuracy over time",
            "Update model with new data regularly",
            "Consider external factors not captured in model"
        ]
        
        evidence = {
            'parameter': parameter,
            'forecast': forecast.tolist(),
            'horizon': horizon,
            'last_value': float(last_value),
            'model_degree': best_degree,
            'r_squared': float(best_score)
        }
        
        insight = AITelemetryInsight(
            insight_type=AnalysisType.FORECASTING,
            title=f"Forecast: {parameter}",
            description=description,
            confidence=confidence,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.insights.append(insight)
        return insight
    
    def analyze_trends(self, parameter: str) -> AITelemetryInsight:
        """Analyze trend for a parameter"""
        
        if parameter not in self.parameter_cache:
            return self._create_insufficient_data_insight(AnalysisType.REGRESSION)
        
        values = self.parameter_cache[parameter]
        
        if len(values) < self.min_data_points:
            return self._create_insufficient_data_insight(AnalysisType.REGRESSION)
        
        values_arr = np.array(values)
        
        # Calculate trend using linear regression
        x = np.arange(len(values_arr))
        slope, intercept = np.polyfit(x, values_arr, 1)
        
        # Calculate R-squared
        preds = slope * x + intercept
        ss_res = np.sum((values_arr - preds)**2)
        ss_tot = np.sum((values_arr - np.mean(values_arr))**2)
        r_squared = 1 - ss_res / (ss_tot + 1e-10)
        
        # Determine trend direction
        if abs(slope) < 0.01:
            trend = "stable"
            description = f"'{parameter}' is stable with no significant trend."
        elif slope > 0:
            trend = "increasing"
            description = (
                f"'{parameter}' shows an increasing trend. "
                f"Rate: {slope:.4f} per time step."
            )
        else:
            trend = "decreasing"
            description = (
                f"'{parameter}' shows a decreasing trend. "
                f"Rate: {abs(slope):.4f} per time step."
            )
        
        recommendations = [
            "Continue monitoring trend stability",
            "Investigate causes of trend if concerning",
            "Update models based on new observations"
        ]
        
        evidence = {
            'parameter': parameter,
            'slope': float(slope),
            'r_squared': float(r_squared),
            'trend': trend,
            'data_points': len(values)
        }
        
        confidence = min(1.0, len(values) / 50)
        
        insight = AITelemetryInsight(
            insight_type=AnalysisType.REGRESSION,
            title=f"Trend Analysis: {parameter}",
            description=description,
            confidence=confidence,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.insights.append(insight)
        return insight
    
    def analyze_system_health(self) -> AITelemetryInsight:
        """Analyze overall system health from telemetry"""
        
        if len(self.telemetry_buffer) < self.min_data_points:
            return self._create_insufficient_data_insight(AnalysisType.CLASSIFICATION)
        
        health_indicators = {}
        
        # Check battery
        if 'battery_voltage' in self.parameter_cache:
            voltage = np.mean(self.parameter_cache['battery_voltage'])
            if voltage > 12.0:
                health_indicators['battery'] = 'good'
            elif voltage > 11.0:
                health_indicators['battery'] = 'fair'
            else:
                health_indicators['battery'] = 'low'
        
        # Check signal strength
        if 'rssi' in self.parameter_cache:
            rssi = np.mean(self.parameter_cache['rssi'])
            if rssi > -50:
                health_indicators['signal'] = 'excellent'
            elif rssi > -70:
                health_indicators['signal'] = 'good'
            else:
                health_indicators['signal'] = 'weak'
        
        # Check temperature
        if 'temperature' in self.parameter_cache:
            temp = np.mean(self.parameter_cache['temperature'])
            if 20 <= temp <= 30:
                health_indicators['temperature'] = 'nominal'
            else:
                health_indicators['temperature'] = 'warning'
        
        # Overall health score
        good_count = sum(1 for v in health_indicators.values() 
                        if v in ['good', 'excellent', 'nominal'])
        total_count = len(health_indicators)
        
        if total_count > 0:
            health_score = good_count / total_count
        else:
            health_score = 0.5
        
        # Generate description
        if health_score > 0.8:
            description = "System health is excellent. All parameters nominal."
            status = "nominal"
        elif health_score > 0.5:
            description = "System health is acceptable. Some parameters need attention."
            status = "degraded"
        else:
            description = "System health is concerning. Multiple parameters need attention."
            status = "critical"
        
        recommendations = [
            f"Status: {status}",
            "Review parameter-specific recommendations",
            "Perform system diagnostics if issues persist"
        ]
        
        evidence = {
            'health_indicators': health_indicators,
            'health_score': health_score,
            'status': status
        }
        
        insight = AITelemetryInsight(
            insight_type=AnalysisType.CLASSIFICATION,
            title="System Health Analysis",
            description=description,
            confidence=health_score,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.insights.append(insight)
        return insight
    
    def _create_insufficient_data_insight(self, 
                                          analysis_type: AnalysisType) -> AITelemetryInsight:
        """Create insight for insufficient data"""
        return AITelemetryInsight(
            insight_type=analysis_type,
            title=f"{analysis_type.value.title()} Analysis",
            description="Insufficient data for analysis. Need more telemetry samples.",
            confidence=0.0,
            evidence={'data_points': len(self.telemetry_buffer)},
            recommendations=["Collect more telemetry data"]
        )
    
    def get_comprehensive_report(self) -> str:
        """Generate comprehensive analytics report"""
        
        lines = []
        lines.append("=" * 70)
        lines.append("DEEPSEEK AI TELEMETRY ANALYTICS REPORT")
        lines.append("=" * 70)
        
        lines.append(f"\nData Summary:")
        lines.append(f"  Total telemetry points: {len(self.telemetry_buffer)}")
        lines.append(f"  Parameters tracked: {len(self.parameter_cache)}")
        
        # Run all analyses
        if len(self.telemetry_buffer) >= self.min_data_points:
            lines.append("\n" + "-" * 70)
            
            # Correlations
            corr_insight = self.analyze_parameter_correlations()
            lines.append(f"\n📊 CORRELATION ANALYSIS (confidence: {corr_insight.confidence:.1%})")
            lines.append(f"   {corr_insight.description}")
            
            # Anomalies
            anomaly_insight = self.detect_anomalies()
            lines.append(f"\n⚠️ ANOMALY DETECTION (confidence: {anomaly_insight.confidence:.1%})")
            lines.append(f"   {anomaly_insight.description}")
            
            # System health
            health_insight = self.analyze_system_health()
            lines.append(f"\n🩺 SYSTEM HEALTH (confidence: {health_insight.confidence:.1%})")
            lines.append(f"   {health_insight.description}")
            
            # Trends for key parameters
            for param in ['altitude', 'temperature', 'velocity']:
                if param in self.parameter_cache:
                    trend_insight = self.analyze_trends(param)
                    lines.append(f"\n📈 TREND: {param} (confidence: {trend_insight.confidence:.1%})")
                    lines.append(f"   {trend_insight.description}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


class TelemetryAIOrchestrator:
    """Orchestrate AI analytics for telemetry"""
    
    def __init__(self):
        self.analytics = DeepSeekTelemetryAnalytics()
        self.analysis_interval = 60  # seconds
        self.last_analysis = None
        
    def process(self, telemetry: Dict[str, Any]) -> Optional[str]:
        """Process telemetry through AI analytics"""
        
        # Add to analytics
        self.analytics.add_telemetry(telemetry)
        
        # Periodic analysis
        now = datetime.now()
        if (self.last_analysis is None or 
            (now - self.last_analysis).total_seconds() > self.analysis_interval):
            
            if len(self.analytics.telemetry_buffer) >= 50:
                report = self.analytics.get_comprehensive_report()
                self.last_analysis = now
                return report
        
        return None
    
    def get_insights(self) -> List[AITelemetryInsight]:
        """Get current insights"""
        return self.analytics.insights


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing DeepSeek AI Telemetry Analytics...")
    
    # Create analytics engine
    analytics = DeepSeekTelemetryAnalytics()
    
    # Add sample telemetry data
    print("\n1. Adding telemetry data...")
    for i in range(100):
        telemetry = {
            'altitude': 1000 + i * 0.5 + np.random.randn() * 10,
            'velocity': 50 + i * 0.1 + np.random.randn() * 2,
            'temperature': 25 + np.sin(i * 0.1) * 5 + np.random.randn() * 0.5,
            'pressure': 101325 - i * 10 + np.random.randn() * 100,
            'battery_voltage': 12.5 + np.random.randn() * 0.1,
            'rssi': -60 + np.random.randn() * 5,
            'humidity': 50 + np.random.randn() * 5
        }
        analytics.add_telemetry(telemetry)
    
    print(f"   Added {len(analytics.telemetry_buffer)} telemetry points")
    
    # Run analyses
    print("\n2. Running correlation analysis...")
    corr_insight = analytics.analyze_parameter_correlations()
    print(f"   {corr_insight.description[:100]}...")
    
    print("\n3. Running anomaly detection...")
    anomaly_insight = analytics.detect_anomalies()
    print(f"   {anomaly_insight.description[:100]}...")
    
    print("\n4. Forecasting altitude...")
    forecast_insight = analytics.forecast_parameter('altitude', horizon=10)
    print(f"   {forecast_insight.description[:100]}...")
    
    print("\n5. Analyzing system health...")
    health_insight = analytics.analyze_system_health()
    print(f"   Status: {health_insight.evidence.get('status')}")
    print(f"   Score: {health_insight.evidence.get('health_score', 0):.1%}")
    
    # Generate report
    print("\n6. Generating comprehensive report...")
    report = analytics.get_comprehensive_report()
    print(report[:500] + "...")
    
    print("\n✅ DeepSeek AI Telemetry Analytics test completed!")