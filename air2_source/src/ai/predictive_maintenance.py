"""
AirOne v4.0 - Predictive Maintenance System
Predicts component failures and schedules maintenance proactively
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Aircraft component types"""
    MOTOR = "motor"
    BATTERY = "battery"
    ESC = "esc"
    PROPELLER = "propeller"
    SERVO = "servo"
    GPS = "gps"
    IMU = "imu"
    RADIO = "radio"
    AIRFRAME = "airframe"


class HealthStatus(Enum):
    """Component health status"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"            # 70-89%
    FAIR = "fair"            # 50-69%
    POOR = "poor"            # 25-49%
    CRITICAL = "critical"    # <25%


@dataclass
class ComponentHealth:
    """Component health status"""
    component_id: str
    component_type: str
    health_percentage: float
    status: str
    estimated_remaining_life: float  # hours
    last_maintenance: str
    next_maintenance_due: str
    degradation_rate: float  # % per hour
    failure_probability_24h: float
    warning_indicators: List[str]


@dataclass
class MaintenanceRecommendation:
    """Maintenance recommendation"""
    recommendation_id: str
    priority: str  # urgent, scheduled, optional
    component_id: str
    component_type: str
    recommended_action: str
    reason: str
    estimated_downtime: float  # hours
    parts_required: List[str]
    deadline: str
    confidence: float


@dataclass
class MaintenanceReport:
    """Comprehensive maintenance report"""
    report_id: str
    generated_at: str
    aircraft_id: str
    total_flight_hours: float
    component_health: List[ComponentHealth]
    maintenance_recommendations: List[MaintenanceRecommendation]
    overall_health_score: float
    estimated_maintenance_cost: float
    next_inspection_due: str


class ComponentHealthMonitor:
    """
    Monitor health of individual components
    """

    def __init__(self, component_id: str, component_type: ComponentType,
                 initial_health: float = 1.0):
        self.component_id = component_id
        self.component_type = component_type.value
        self.health = initial_health
        self.health_history: deque = deque(maxlen=1000)
        self.stress_history: deque = deque(maxlen=500)
        self.last_maintenance = datetime.now()
        self.total_operation_time = 0
        
        # Degradation model parameters
        self.base_degradation_rate = self._get_base_degradation_rate()
        self.stress_sensitivity = self._get_stress_sensitivity()
        
        # Warning thresholds
        self.warning_thresholds = self._get_warning_thresholds()

    def _get_base_degradation_rate(self) -> float:
        """Get base degradation rate per hour"""
        rates = {
            ComponentType.MOTOR: 0.001,
            ComponentType.BATTERY: 0.0005,
            ComponentType.ESC: 0.0008,
            ComponentType.PROPELLER: 0.002,
            ComponentType.SERVO: 0.001,
            ComponentType.GPS: 0.0001,
            ComponentType.IMU: 0.0002,
            ComponentType.RADIO: 0.0001,
            ComponentType.AIRFRAME: 0.00005
        }
        return rates.get(ComponentType(self.component_type), 0.001)

    def _get_stress_sensitivity(self) -> float:
        """Get stress sensitivity factor"""
        sensitivities = {
            ComponentType.MOTOR: 1.5,
            ComponentType.BATTERY: 1.3,
            ComponentType.ESC: 1.4,
            ComponentType.PROPELLER: 1.2,
            ComponentType.SERVO: 1.0,
            ComponentType.GPS: 0.5,
            ComponentType.IMU: 0.8,
            ComponentType.RADIO: 0.3,
            ComponentType.AIRFRAME: 2.0
        }
        return sensitivities.get(ComponentType(self.component_type), 1.0)

    def _get_warning_thresholds(self) -> Dict[str, float]:
        """Get warning indicator thresholds"""
        thresholds = {
            ComponentType.MOTOR: {
                'temperature_max': 80,
                'rpm_variance': 500,
                'efficiency_drop': 0.15
            },
            ComponentType.BATTERY: {
                'voltage_sag': 0.5,
                'capacity_drop': 0.2,
                'internal_resistance': 0.1
            },
            ComponentType.PROPELLER: {
                'vibration_level': 0.3,
                'efficiency_drop': 0.1
            }
        }
        return thresholds.get(ComponentType(self.component_type), {})

    def update(self, telemetry: Dict[str, Any], dt: float = 0.1):
        """
        Update component health based on telemetry
        
        Args:
            telemetry: Flight telemetry
            dt: Time step in hours
        """
        self.total_operation_time += dt
        
        # Calculate stress factor
        stress = self._calculate_stress(telemetry)
        self.stress_history.append(stress)
        
        # Calculate degradation
        stress_factor = 1 + (stress - 1) * self.stress_sensitivity
        degradation = self.base_degradation_rate * stress_factor * dt
        
        # Apply degradation
        self.health = max(0, self.health - degradation)
        
        # Record history
        self.health_history.append({
            'timestamp': datetime.now().isoformat(),
            'health': self.health,
            'stress': stress,
            'degradation': degradation
        })
        
        # Check for warning indicators
        self._check_warnings(telemetry)

    def _calculate_stress(self, telemetry: Dict) -> float:
        """Calculate stress factor from telemetry"""
        stress = 1.0
        
        if self.component_type == ComponentType.MOTOR.value:
            # Motor stress from RPM and temperature
            rpm = telemetry.get('motor_rpm', 0)
            temp = telemetry.get('temperature', 25)
            throttle = telemetry.get('throttle', 0)
            
            rpm_stress = rpm / 10000  # Normalized to max RPM
            temp_stress = max(0, (temp - 40) / 40)  # Above 40°C
            throttle_stress = throttle
            
            stress = 1 + 0.5 * rpm_stress + 0.3 * temp_stress + 0.2 * throttle_stress
        
        elif self.component_type == ComponentType.BATTERY.value:
            # Battery stress from current and temperature
            current = telemetry.get('battery_current', 0)
            voltage = telemetry.get('battery_voltage', 16.8)
            temp = telemetry.get('temperature', 25)
            
            current_stress = current / 30  # Normalized to max current
            voltage_stress = max(0, (16.8 - voltage) / 3)  # Below nominal
            temp_stress = max(0, (temp - 30) / 20)
            
            stress = 1 + 0.4 * current_stress + 0.4 * voltage_stress + 0.2 * temp_stress
        
        elif self.component_type == ComponentType.PROPELLER.value:
            # Propeller stress from vibration and RPM
            rpm = telemetry.get('motor_rpm', 0)
            vibration = telemetry.get('vibration', 0)
            
            rpm_stress = rpm / 10000
            vibration_stress = vibration / 10
            
            stress = 1 + 0.6 * rpm_stress + 0.4 * vibration_stress
        
        elif self.component_type == ComponentType.AIRFRAME.value:
            # Airframe stress from G-forces and velocity
            acceleration = telemetry.get('acceleration', 0)
            velocity = telemetry.get('velocity', 0)
            
            g_stress = abs(acceleration) / 9.81  # G-force
            velocity_stress = velocity / 100  # Normalized to max velocity
            
            stress = 1 + 0.7 * g_stress + 0.3 * velocity_stress
        
        return max(1, stress)

    def _check_warnings(self, telemetry: Dict):
        """Check for warning indicators"""
        # Implementation depends on specific thresholds
        pass

    def get_health_status(self) -> ComponentHealth:
        """Get current health status"""
        # Calculate status
        if self.health >= 0.9:
            status = HealthStatus.EXCELLENT
        elif self.health >= 0.7:
            status = HealthStatus.GOOD
        elif self.health >= 0.5:
            status = HealthStatus.FAIR
        elif self.health >= 0.25:
            status = HealthStatus.POOR
        else:
            status = HealthStatus.CRITICAL
        
        # Estimate remaining life
        if self.health_history:
            recent_degradation = np.mean([h['degradation'] for h in list(self.health_history)[-100:]])
            if recent_degradation > 0:
                remaining_life = self.health / (recent_degradation * 3600)  # Convert to hours
            else:
                remaining_life = float('inf')
        else:
            remaining_life = self.health / (self.base_degradation_rate * 3600)
        
        # Calculate failure probability in 24h
        if self.health_history:
            recent_degradation = np.mean([h['degradation'] for h in list(self.health_history)[-100:]])
            failure_prob = 1 - np.exp(-recent_degradation * 3600 * 24 / max(self.health, 0.01))
        else:
            failure_prob = 0.0
        
        # Next maintenance due
        next_maintenance = self.last_maintenance + timedelta(hours=remaining_life * 0.8)
        
        # Warning indicators
        warnings = self._get_warning_indicators()
        
        return ComponentHealth(
            component_id=self.component_id,
            component_type=self.component_type,
            health_percentage=self.health,
            status=status.value,
            estimated_remaining_life=remaining_life,
            last_maintenance=self.last_maintenance.isoformat(),
            next_maintenance_due=next_maintenance.isoformat(),
            degradation_rate=self.base_degradation_rate,
            failure_probability_24h=failure_prob,
            warning_indicators=warnings
        )

    def _get_warning_indicators(self) -> List[str]:
        """Get list of active warning indicators"""
        warnings = []
        
        if self.health < 0.5:
            warnings.append("Health below 50%")
        
        if self.health_history:
            recent_health = [h['health'] for h in list(self.health_history)[-10:]]
            if len(recent_health) >= 10:
                trend = np.polyfit(np.arange(10), recent_health, 1)[0]
                if trend < -0.001:
                    warnings.append("Rapid degradation detected")
        
        return warnings

    def perform_maintenance(self):
        """Reset health after maintenance"""
        self.health = 1.0
        self.last_maintenance = datetime.now()
        self.health_history.clear()
        logger.info(f"Maintenance performed on {self.component_id}")


class PredictiveMaintenanceSystem:
    """
    System-wide predictive maintenance management
    """

    def __init__(self, aircraft_id: str = "aircraft_001"):
        self.aircraft_id = aircraft_id
        self.components: Dict[str, ComponentHealthMonitor] = {}
        self.maintenance_history: List[Dict] = []
        self.total_flight_hours = 0
        
        # Initialize default components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize default aircraft components"""
        default_components = [
            ('motor_main', ComponentType.MOTOR),
            ('motor_backup', ComponentType.MOTOR),
            ('battery_main', ComponentType.BATTERY),
            ('battery_backup', ComponentType.BATTERY),
            ('esc_1', ComponentType.ESC),
            ('esc_2', ComponentType.ESC),
            ('propeller_1', ComponentType.PROPELLER),
            ('propeller_2', ComponentType.PROPELLER),
            ('servo_throttle', ComponentType.SERVO),
            ('servo_elevator', ComponentType.SERVO),
            ('gps_module', ComponentType.GPS),
            ('imu_module', ComponentType.IMU),
            ('radio_tx', ComponentType.RADIO),
            ('airframe_main', ComponentType.AIRFRAME)
        ]
        
        for comp_id, comp_type in default_components:
            self.components[comp_id] = ComponentHealthMonitor(comp_id, comp_type)

    def update(self, telemetry: Dict[str, Any], dt: float = 0.1):
        """
        Update all component health monitors
        
        Args:
            telemetry: Flight telemetry
            dt: Time step in hours
        """
        self.total_flight_hours += dt
        
        for component in self.components.values():
            component.update(telemetry, dt)

    def get_component_health(self, component_id: str) -> Optional[ComponentHealth]:
        """Get health status for specific component"""
        if component_id in self.components:
            return self.components[component_id].get_health_status()
        return None

    def get_all_component_health(self) -> List[ComponentHealth]:
        """Get health status for all components"""
        return [comp.get_health_status() for comp in self.components.values()]

    def get_maintenance_recommendations(self) -> List[MaintenanceRecommendation]:
        """Generate maintenance recommendations"""
        recommendations = []
        now = datetime.now()
        
        for comp_id, component in self.components.items():
            health = component.get_health_status()
            
            # Critical components need urgent attention
            if health.status == HealthStatus.CRITICAL.value:
                recommendations.append(self._create_recommendation(
                    component=health,
                    priority="urgent",
                    action=f"Replace {health.component_type} immediately",
                    reason=f"Health at {health.health_percentage:.1%} - critical failure risk",
                    deadline=now + timedelta(days=1),
                    confidence=0.95
                ))
            
            # Poor health needs scheduled maintenance
            elif health.status == HealthStatus.POOR.value:
                recommendations.append(self._create_recommendation(
                    component=health,
                    priority="scheduled",
                    action=f"Schedule {health.component_type} replacement",
                    reason=f"Health at {health.health_percentage:.1%} - degradation accelerating",
                    deadline=now + timedelta(days=7),
                    confidence=0.85
                ))
            
            # Fair health - plan maintenance
            elif health.status == HealthStatus.FAIR.value:
                recommendations.append(self._create_recommendation(
                    component=health,
                    priority="optional",
                    action=f"Plan {health.component_type} maintenance",
                    reason=f"Health at {health.health_percentage:.1%} - monitor closely",
                    deadline=now + timedelta(days=30),
                    confidence=0.75
                ))
            
            # High failure probability
            elif health.failure_probability_24h > 0.1:
                recommendations.append(self._create_recommendation(
                    component=health,
                    priority="urgent",
                    action=f"Inspect {health.component_type}",
                    reason=f"High failure probability ({health.failure_probability_24h:.1%}) in next 24h",
                    deadline=now + timedelta(hours=12),
                    confidence=0.80
                ))
        
        # Sort by priority
        priority_order = {'urgent': 0, 'scheduled': 1, 'optional': 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
        
        return recommendations

    def _create_recommendation(self, component: ComponentHealth, priority: str,
                               action: str, reason: str, 
                               deadline: datetime, confidence: float) -> MaintenanceRecommendation:
        """Create maintenance recommendation"""
        parts_map = {
            ComponentType.MOTOR.value: ['brushless motor', 'mounting hardware'],
            ComponentType.BATTERY.value: ['LiPo battery', 'balance connector'],
            ComponentType.ESC.value: ['electronic speed controller'],
            ComponentType.PROPELLER.value: ['propeller set', 'prop nuts'],
            ComponentType.SERVO.value: ['servo', 'servo horn'],
            ComponentType.GPS.value: ['GPS module', 'antenna'],
            ComponentType.IMU.value: ['IMU module'],
            ComponentType.RADIO.value: ['radio receiver', 'antenna'],
            ComponentType.AIRFRAME.value: ['airframe parts', 'fasteners']
        }
        
        downtime_map = {
            'urgent': 0.5,
            'scheduled': 1.0,
            'optional': 2.0
        }
        
        return MaintenanceRecommendation(
            recommendation_id=f"maint_{datetime.now().strftime('%Y%m%d%H%M%S')}_{component.component_id}",
            priority=priority,
            component_id=component.component_id,
            component_type=component.component_type,
            recommended_action=action,
            reason=reason,
            estimated_downtime=downtime_map.get(priority, 1.0),
            parts_required=parts_map.get(component.component_type, ['generic parts']),
            deadline=deadline.isoformat(),
            confidence=confidence
        )

    def get_maintenance_report(self) -> MaintenanceReport:
        """Generate comprehensive maintenance report"""
        component_health = self.get_all_component_health()
        recommendations = self.get_maintenance_recommendations()
        
        # Calculate overall health score
        if component_health:
            weights = {
                HealthStatus.EXCELLENT.value: 1.0,
                HealthStatus.GOOD.value: 0.8,
                HealthStatus.FAIR.value: 0.5,
                HealthStatus.POOR.value: 0.25,
                HealthStatus.CRITICAL.value: 0.0
            }
            overall_health = np.mean([
                weights.get(c.status, 0.5) for c in component_health
            ])
        else:
            overall_health = 1.0
        
        # Estimate maintenance cost
        cost_map = {
            ComponentType.MOTOR.value: 50,
            ComponentType.BATTERY.value: 80,
            ComponentType.ESC.value: 30,
            ComponentType.PROPELLER.value: 15,
            ComponentType.SERVO.value: 25,
            ComponentType.GPS.value: 100,
            ComponentType.IMU.value: 150,
            ComponentType.RADIO.value: 50,
            ComponentType.AIRFRAME.value: 200
        }
        
        estimated_cost = sum(
            cost_map.get(r.component_type, 50)
            for r in recommendations if r.priority in ['urgent', 'scheduled']
        )
        
        # Next inspection due
        next_inspection = min(
            [datetime.fromisoformat(c.next_maintenance_due) for c in component_health],
            default=datetime.now() + timedelta(days=30)
        )
        
        return MaintenanceReport(
            report_id=f"maint_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            aircraft_id=self.aircraft_id,
            total_flight_hours=self.total_flight_hours,
            component_health=component_health,
            maintenance_recommendations=recommendations,
            overall_health_score=overall_health,
            estimated_maintenance_cost=estimated_cost,
            next_inspection_due=next_inspection.isoformat()
        )

    def perform_maintenance(self, component_id: str):
        """Perform maintenance on component"""
        if component_id in self.components:
            self.components[component_id].perform_maintenance()
            self.maintenance_history.append({
                'component_id': component_id,
                'timestamp': datetime.now().isoformat(),
                'type': 'maintenance',
                'flight_hours': self.total_flight_hours
            })
            logger.info(f"Maintenance performed on {component_id}")

    def export_report(self, filepath: str) -> bool:
        """Export maintenance report to file"""
        try:
            report = self.get_maintenance_report()
            
            report_dict = {
                'report_id': report.report_id,
                'generated_at': report.generated_at,
                'aircraft_id': report.aircraft_id,
                'total_flight_hours': report.total_flight_hours,
                'overall_health_score': report.overall_health_score,
                'estimated_maintenance_cost': report.estimated_maintenance_cost,
                'next_inspection_due': report.next_inspection_due,
                'component_health': [asdict(c) for c in report.component_health],
                'recommendations': [asdict(r) for r in report.maintenance_recommendations],
                'maintenance_history': self.maintenance_history[-50:]
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2)
            
            logger.info(f"Maintenance report exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False


# Convenience function
def create_predictive_maintenance_system(aircraft_id: str = "aircraft_001") -> PredictiveMaintenanceSystem:
    """Create and return a Predictive Maintenance System instance"""
    return PredictiveMaintenanceSystem(aircraft_id)


__all__ = [
    'PredictiveMaintenanceSystem',
    'create_predictive_maintenance_system',
    'ComponentHealthMonitor',
    'ComponentHealth',
    'MaintenanceRecommendation',
    'MaintenanceReport',
    'ComponentType',
    'HealthStatus'
]
