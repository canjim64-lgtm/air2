"""
AirOne v4.0 - AI Decision Engine
Intelligent decision-making system powered by AI/ML analysis
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions the engine can make"""
    MISSION_ABORT = "mission_abort"
    MODE_CHANGE = "mode_change"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    ALERT_GENERATION = "alert_generation"
    RESOURCE_ALLOCATION = "resource_allocation"
    MAINTENANCE_SCHEDULE = "maintenance_schedule"
    ANOMALY_RESPONSE = "anomaly_response"
    OPTIMIZATION_SUGGESTION = "optimization_suggestion"


class DecisionPriority(Enum):
    """Decision priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class DecisionStatus(Enum):
    """Decision status"""
    PENDING = "pending"
    EXECUTED = "executed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass
class Decision:
    """Represents an AI-generated decision"""
    decision_id: str
    decision_type: str
    priority: str
    status: str
    description: str
    recommendation: str
    confidence: float
    supporting_evidence: List[str]
    created_at: str
    expires_at: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class DecisionContext:
    """Context for decision making"""
    telemetry_data: Dict[str, Any]
    historical_patterns: Dict[str, Any]
    system_state: Dict[str, Any]
    environmental_factors: Dict[str, Any]
    constraints: Dict[str, Any]
    objectives: List[str]


class AIDecisionEngine:
    """
    AI-powered decision engine for autonomous operations
    
    Analyzes telemetry, system state, and patterns to generate
    intelligent decisions and recommendations
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[Decision] = []
        self.rules: List[Dict] = []
        self.models: Dict[str, Any] = {}
        self.thresholds: Dict[str, Dict] = {}
        
        # Initialize default thresholds
        self._init_default_thresholds()
        
        # Initialize decision rules
        self._init_default_rules()
        
        logger.info("AI Decision Engine initialized")

    def _init_default_thresholds(self):
        """Initialize default thresholds for decision making"""
        self.thresholds = {
            'battery': {
                'critical': 10,
                'warning': 20,
                'low': 30
            },
            'altitude': {
                'max_safe': 10000,
                'warning': 8000,
                'target': 5000
            },
            'velocity': {
                'max_safe': 200,
                'warning': 150,
                'optimal': 50
            },
            'temperature': {
                'max_safe': 80,
                'min_safe': -20,
                'warning_high': 60,
                'warning_low': -10
            },
            'signal_strength': {
                'critical': -90,
                'warning': -70,
                'good': -50
            },
            'anomaly_score': {
                'critical': -0.15,
                'warning': -0.05
            }
        }

    def _init_default_rules(self):
        """Initialize default decision rules"""
        self.rules = [
            {
                'id': 'rule_battery_critical',
                'name': 'Critical Battery Response',
                'condition': self._check_battery_critical,
                'action': self._recommend_battery_response,
                'priority': DecisionPriority.CRITICAL
            },
            {
                'id': 'rule_altitude_exceeded',
                'name': 'Maximum Altitude Exceeded',
                'condition': self._check_altitude_exceeded,
                'action': self._recommend_altitude_response,
                'priority': DecisionPriority.HIGH
            },
            {
                'id': 'rule_anomaly_detected',
                'name': 'Anomaly Response',
                'condition': self._check_anomaly,
                'action': self._recommend_anomaly_response,
                'priority': DecisionPriority.HIGH
            },
            {
                'id': 'rule_signal_loss',
                'name': 'Signal Loss Response',
                'condition': self._check_signal_loss,
                'action': self._recommend_signal_response,
                'priority': DecisionPriority.CRITICAL
            },
            {
                'id': 'rule_temperature_warning',
                'name': 'Temperature Warning',
                'condition': self._check_temperature,
                'action': self._recommend_temperature_response,
                'priority': DecisionPriority.MEDIUM
            },
            {
                'id': 'rule_optimization_opportunity',
                'name': 'Optimization Opportunity',
                'condition': self._check_optimization,
                'action': self._recommend_optimization,
                'priority': DecisionPriority.LOW
            }
        ]

    # ==================== Condition Checkers ====================

    def _check_battery_critical(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check if battery is at critical level"""
        battery = context.telemetry_data.get('battery_level', 100)
        if battery <= self.thresholds['battery']['critical']:
            return True, {'battery_level': battery, 'severity': 'critical'}
        elif battery <= self.thresholds['battery']['warning']:
            return True, {'battery_level': battery, 'severity': 'warning'}
        return False, {}

    def _check_altitude_exceeded(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check if altitude exceeds safe limits"""
        altitude = context.telemetry_data.get('altitude', 0)
        if altitude > self.thresholds['altitude']['max_safe']:
            return True, {'altitude': altitude, 'severity': 'critical'}
        elif altitude > self.thresholds['altitude']['warning']:
            return True, {'altitude': altitude, 'severity': 'warning'}
        return False, {}

    def _check_anomaly(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check if anomaly is detected"""
        anomaly_score = context.telemetry_data.get('anomaly_score', 0)
        if anomaly_score < self.thresholds['anomaly_score']['critical']:
            return True, {'anomaly_score': anomaly_score, 'severity': 'critical'}
        elif anomaly_score < self.thresholds['anomaly_score']['warning']:
            return True, {'anomaly_score': anomaly_score, 'severity': 'warning'}
        return False, {}

    def _check_signal_loss(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check for signal loss"""
        signal = context.telemetry_data.get('radio_signal_strength', -50)
        if signal < self.thresholds['signal_strength']['critical']:
            return True, {'signal_strength': signal, 'severity': 'critical'}
        elif signal < self.thresholds['signal_strength']['warning']:
            return True, {'signal_strength': signal, 'severity': 'warning'}
        return False, {}

    def _check_temperature(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check temperature limits"""
        temp = context.telemetry_data.get('temperature', 20)
        if temp > self.thresholds['temperature']['max_safe'] or temp < self.thresholds['temperature']['min_safe']:
            return True, {'temperature': temp, 'severity': 'critical'}
        elif temp > self.thresholds['temperature']['warning_high'] or temp < self.thresholds['temperature']['warning_low']:
            return True, {'temperature': temp, 'severity': 'warning'}
        return False, {}

    def _check_optimization(self, context: DecisionContext) -> Tuple[bool, Dict]:
        """Check for optimization opportunities"""
        # Analyze patterns for optimization
        velocity = context.telemetry_data.get('velocity', 0)
        battery = context.telemetry_data.get('battery_level', 100)
        
        # Example: Suggest power saving if battery is moderate and velocity is stable
        if 40 < battery < 70 and abs(velocity) < 10:
            return True, {'optimization_type': 'power_saving', 'potential_savings': '10-15%'}
        return False, {}

    # ==================== Action Recommenders ====================

    def _recommend_battery_response(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate battery-related recommendations"""
        severity = condition_data.get('severity', 'warning')
        battery_level = condition_data.get('battery_level', 0)
        
        if severity == 'critical':
            recommendation = "IMMEDIATE ACTION: Initiate emergency recovery procedure. Reduce power consumption to minimum. Deploy recovery parachute if available."
            decision_type = DecisionType.MISSION_ABORT
        else:
            recommendation = "Reduce power consumption. Disable non-essential systems. Consider early recovery if trend continues."
            decision_type = DecisionType.PARAMETER_ADJUSTMENT
        
        return self._create_decision(
            decision_type=decision_type,
            priority=DecisionPriority.CRITICAL if severity == 'critical' else DecisionPriority.HIGH,
            description=f"Battery level at {battery_level}%",
            recommendation=recommendation,
            confidence=0.95 if severity == 'critical' else 0.85,
            supporting_evidence=[
                f"Current battery: {battery_level}%",
                f"Threshold: {self.thresholds['battery']['critical']}%",
                "Historical data shows rapid depletion at this level"
            ]
        )

    def _recommend_altitude_response(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate altitude-related recommendations"""
        altitude = condition_data.get('altitude', 0)
        severity = condition_data.get('severity', 'warning')
        
        if severity == 'critical':
            recommendation = "CRITICAL: Maximum safe altitude exceeded. Initiate controlled descent. Verify parachute deployment system status."
            decision_type = DecisionType.MODE_CHANGE
        else:
            recommendation = "Approaching altitude limit. Monitor closely. Prepare for potential descent initiation."
            decision_type = DecisionType.ALERT_GENERATION
        
        return self._create_decision(
            decision_type=decision_type,
            priority=DecisionPriority.HIGH,
            description=f"Altitude at {altitude}m exceeds safe limits",
            recommendation=recommendation,
            confidence=0.92,
            supporting_evidence=[
                f"Current altitude: {altitude}m",
                f"Maximum safe altitude: {self.thresholds['altitude']['max_safe']}m",
                "Structural integrity may be compromised"
            ]
        )

    def _recommend_anomaly_response(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate anomaly-related recommendations"""
        anomaly_score = condition_data.get('anomaly_score', 0)
        
        recommendation = f"Anomaly detected with score {anomaly_score:.4f}. Recommend detailed system diagnostic. Consider switching to safe mode if anomalies persist."
        
        return self._create_decision(
            decision_type=DecisionType.ANOMALY_RESPONSE,
            priority=DecisionPriority.HIGH,
            description="System anomaly detected",
            recommendation=recommendation,
            confidence=0.88,
            supporting_evidence=[
                f"Anomaly score: {anomaly_score:.4f}",
                "Pattern deviates from normal operational parameters",
                "May indicate sensor malfunction or environmental interference"
            ]
        )

    def _recommend_signal_response(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate signal loss recommendations"""
        signal_strength = condition_data.get('signal_strength', -50)
        
        if signal_strength < self.thresholds['signal_strength']['critical']:
            recommendation = "CRITICAL: Signal strength critically low. Switch to autonomous mode. Initiate return-to-home if GPS available. Store telemetry locally."
            decision_type = DecisionType.MODE_CHANGE
        else:
            recommendation = "Signal strength degrading. Check antenna orientation. Consider repositioning ground station or increasing transmission power."
            decision_type = DecisionType.PARAMETER_ADJUSTMENT
        
        return self._create_decision(
            decision_type=decision_type,
            priority=DecisionPriority.CRITICAL if signal_strength < self.thresholds['signal_strength']['critical'] else DecisionPriority.HIGH,
            description=f"Radio signal strength at {signal_strength}dBm",
            recommendation=recommendation,
            confidence=0.90,
            supporting_evidence=[
                f"Signal strength: {signal_strength}dBm",
                "Communication reliability compromised",
                "May result in telemetry loss"
            ]
        )

    def _recommend_temperature_response(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate temperature-related recommendations"""
        temperature = condition_data.get('temperature', 20)
        
        if temperature > self.thresholds['temperature']['warning_high']:
            recommendation = "High temperature detected. Activate cooling systems if available. Reduce computational load. Monitor for thermal runaway."
        else:
            recommendation = "Low temperature detected. Activate heating systems. Monitor battery performance (reduced capacity expected in cold)."
        
        return self._create_decision(
            decision_type=DecisionType.PARAMETER_ADJUSTMENT,
            priority=DecisionPriority.MEDIUM,
            description=f"Temperature warning: {temperature}°C",
            recommendation=recommendation,
            confidence=0.87,
            supporting_evidence=[
                f"Current temperature: {temperature}°C",
                "Operating outside optimal range",
                "May affect sensor accuracy and battery performance"
            ]
        )

    def _recommend_optimization(self, context: DecisionContext, condition_data: Dict) -> Decision:
        """Generate optimization recommendations"""
        optimization_type = condition_data.get('optimization_type', 'general')
        
        recommendation = "System operating in suboptimal state. Consider enabling power-saving mode. Review task scheduling for efficiency improvements."
        
        return self._create_decision(
            decision_type=DecisionType.OPTIMIZATION_SUGGESTION,
            priority=DecisionPriority.LOW,
            description="Optimization opportunity detected",
            recommendation=recommendation,
            confidence=0.75,
            supporting_evidence=[
                f"Optimization type: {optimization_type}",
                "Current resource utilization below optimal",
                "Potential efficiency gain: 10-15%"
            ]
        )

    # ==================== Core Methods ====================

    def _create_decision(self, decision_type: DecisionType, priority: DecisionPriority,
                        description: str, recommendation: str, confidence: float,
                        supporting_evidence: List[str]) -> Decision:
        """Create a new decision object"""
        decision_id = f"DEC_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        now = datetime.now()
        expires = datetime.now()
        
        # Set expiration based on priority
        if priority == DecisionPriority.CRITICAL:
            expires = expires.replace(minute=expires.minute + 5)  # 5 minutes
        elif priority == DecisionPriority.HIGH:
            expires = expires.replace(minute=expires.minute + 15)  # 15 minutes
        elif priority == DecisionPriority.MEDIUM:
            expires = expires.replace(hour=expires.hour + 1)  # 1 hour
        else:
            expires = expires.replace(hour=expires.hour + 24)  # 24 hours
        
        decision = Decision(
            decision_id=decision_id,
            decision_type=decision_type.value,
            priority=priority.value,
            status=DecisionStatus.PENDING.value,
            description=description,
            recommendation=recommendation,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            created_at=now.isoformat(),
            expires_at=expires.isoformat()
        )
        
        self.decisions[decision_id] = decision
        self.decision_history.append(decision)
        
        return decision

    def analyze_and_decide(self, context: DecisionContext) -> List[Decision]:
        """
        Analyze context and generate decisions
        
        Args:
            context: Decision context with telemetry and system state
            
        Returns:
            List of generated decisions
        """
        decisions = []
        
        for rule in self.rules:
            try:
                triggered, condition_data = rule['condition'](context)
                if triggered:
                    decision = rule['action'](context, condition_data)
                    decisions.append(decision)
                    logger.info(f"Rule '{rule['name']}' triggered. Decision: {decision.decision_id}")
            except Exception as e:
                logger.error(f"Rule evaluation failed for {rule['id']}: {e}")
        
        return decisions

    def process_telemetry(self, telemetry: Dict[str, Any],
                         historical_data: Optional[List[Dict]] = None) -> List[Decision]:
        """
        Process telemetry and generate decisions
        
        Args:
            telemetry: Current telemetry data
            historical_data: Historical telemetry for context
            
        Returns:
            List of decisions
        """
        # Build context
        context = DecisionContext(
            telemetry_data=telemetry,
            historical_patterns=self._analyze_patterns(historical_data) if historical_data else {},
            system_state=self._get_system_state(telemetry),
            environmental_factors={},
            constraints={},
            objectives=['maintain_safety', 'maximize_mission_duration', 'ensure_data_integrity']
        )
        
        return self.analyze_and_decide(context)

    def _analyze_patterns(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze historical patterns"""
        if not historical_data:
            return {}
        
        patterns = {}
        
        # Analyze trends
        if len(historical_data) > 1:
            # Battery trend
            batteries = [d.get('battery_level', 100) for d in historical_data[-10:]]
            if len(batteries) > 1:
                battery_trend = (batteries[-1] - batteries[0]) / len(batteries)
                patterns['battery_trend'] = battery_trend
                patterns['battery_depletion_rate'] = abs(battery_trend)
            
            # Altitude trend
            altitudes = [d.get('altitude', 0) for d in historical_data[-10:]]
            if len(altitudes) > 1:
                patterns['altitude_trend'] = altitudes[-1] - altitudes[0]
        
        return patterns

    def _get_system_state(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Determine system state from telemetry"""
        state = {
            'operational': True,
            'warnings': [],
            'critical_issues': []
        }
        
        # Check various parameters
        if telemetry.get('battery_level', 100) < self.thresholds['battery']['warning']:
            state['warnings'].append('low_battery')
        
        if telemetry.get('altitude', 0) > self.thresholds['altitude']['warning']:
            state['warnings'].append('high_altitude')
        
        if telemetry.get('radio_signal_strength', -50) < self.thresholds['signal_strength']['warning']:
            state['warnings'].append('weak_signal')
        
        return state

    # ==================== Decision Management ====================

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get decision by ID"""
        return self.decisions.get(decision_id)

    def get_pending_decisions(self) -> List[Decision]:
        """Get all pending decisions"""
        return [d for d in self.decisions.values() if d.status == DecisionStatus.PENDING.value]

    def execute_decision(self, decision_id: str) -> bool:
        """Mark decision as executed"""
        if decision_id in self.decisions:
            self.decisions[decision_id].status = DecisionStatus.EXECUTED.value
            logger.info(f"Decision {decision_id} executed")
            return True
        return False

    def reject_decision(self, decision_id: str, reason: str = "") -> bool:
        """Mark decision as rejected"""
        if decision_id in self.decisions:
            self.decisions[decision_id].status = DecisionStatus.REJECTED.value
            self.decisions[decision_id].metadata = {'rejection_reason': reason}
            logger.info(f"Decision {decision_id} rejected: {reason}")
            return True
        return False

    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of all decisions"""
        return {
            'total_decisions': len(self.decisions),
            'pending': len([d for d in self.decisions.values() if d.status == DecisionStatus.PENDING.value]),
            'executed': len([d for d in self.decisions.values() if d.status == DecisionStatus.EXECUTED.value]),
            'rejected': len([d for d in self.decisions.values() if d.status == DecisionStatus.REJECTED.value]),
            'by_priority': {
                'critical': len([d for d in self.decisions.values() if d.priority == DecisionPriority.CRITICAL.value]),
                'high': len([d for d in self.decisions.values() if d.priority == DecisionPriority.HIGH.value]),
                'medium': len([d for d in self.decisions.values() if d.priority == DecisionPriority.MEDIUM.value]),
                'low': len([d for d in self.decisions.values() if d.priority == DecisionPriority.LOW.value])
            }
        }

    def clear_expired_decisions(self) -> int:
        """Clear expired decisions"""
        now = datetime.now()
        expired = [
            d_id for d_id, d in self.decisions.items()
            if d.expires_at and datetime.fromisoformat(d.expires_at) < now
        ]
        
        for d_id in expired:
            if self.decisions[d_id].status == DecisionStatus.PENDING.value:
                self.decisions[d_id].status = DecisionStatus.SUPERSEDED.value
            del self.decisions[d_id]
        
        logger.info(f"Cleared {len(expired)} expired decisions")
        return len(expired)


# Convenience function
def create_decision_engine(config: Optional[Dict] = None) -> AIDecisionEngine:
    """Create and return a Decision Engine instance"""
    return AIDecisionEngine(config)


__all__ = [
    'AIDecisionEngine',
    'create_decision_engine',
    'DecisionType',
    'DecisionPriority',
    'DecisionStatus',
    'Decision',
    'DecisionContext'
]
