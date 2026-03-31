"""
Autonomous Threat Response System for AirOne Professional
Implements AI-driven automated threat detection and response capabilities
"""

import asyncio
import threading
import queue
import time
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import socket
import struct
from functools import wraps
import psutil
import GPUtil
import requests
import aiohttp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import ipaddress
from collections import defaultdict, deque
import statistics
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import pipeline
import pandas as pd


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat levels for autonomous response"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class ResponseAction(Enum):
    """Actions that can be taken by the autonomous system"""
    MONITOR = "monitor"
    ALERT = "alert"
    ISOLATE_ENDPOINT = "isolate_endpoint"
    BLOCK_IP = "block_ip"
    BLOCK_PORT = "block_port"
    RESET_CONNECTION = "reset_connection"
    TERMINATE_PROCESS = "terminate_process"
    COLLECT_EVIDENCE = "collect_evidence"
    NOTIFY_SECURITY_TEAM = "notify_security_team"
    SHUTDOWN_SERVICE = "shutdown_service"
    ACTIVATE_INCIDENT_RESPONSE = "activate_incident_response"


class DetectionMethod(Enum):
    """Methods used for threat detection"""
    ANOMALY_DETECTION = "anomaly_detection"
    SIGNATURE_MATCHING = "signature_matching"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    MACHINE_LEARNING = "machine_learning"
    RULE_BASED = "rule_based"
    HEURISTIC_ANALYSIS = "heuristic_analysis"


@dataclass
class ThreatIndicator:
    """Represents a threat indicator"""
    id: str
    indicator_type: str  # ip, domain, hash, url, etc.
    indicator_value: str
    threat_level: ThreatLevel
    confidence_score: float
    detection_method: DetectionMethod
    first_seen: datetime
    last_seen: datetime
    source_feed: str
    tags: List[str]
    description: str


@dataclass
class SecurityEvent:
    """Represents a security event"""
    id: str
    timestamp: datetime
    event_type: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    threat_level: ThreatLevel
    confidence_score: float
    detection_method: DetectionMethod
    description: str
    related_indicators: List[str]
    raw_data: Dict[str, Any]
    status: str  # detected, analyzed, responded, resolved


@dataclass
class ResponseActionItem:
    """Represents a response action to be taken"""
    id: str
    action: ResponseAction
    target: str  # IP, hostname, process ID, etc.
    priority: int  # Lower number = higher priority
    reason: str
    confidence_score: float
    execution_time: datetime
    status: str  # pending, executing, completed, failed


class ThreatIntelligenceManager:
    """Manages threat intelligence for the autonomous system"""
    
    def __init__(self):
        self.threat_indicators = {}
        self.feed_sources = {}
        self.indicator_cache = {}
        self.lock = threading.Lock()
        self.update_interval = 300  # 5 minutes
        self.last_update = datetime.utcnow()
        
        logger.info("Threat intelligence manager initialized")
    
    def add_feed_source(self, source_id: str, source_url: str, update_interval: int = 300):
        """Add a threat intelligence feed source"""
        self.feed_sources[source_id] = {
            'url': source_url,
            'interval': update_interval,
            'last_update': datetime.utcnow(),
            'enabled': True
        }
        logger.info(f"Added threat intelligence feed: {source_id}")
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str,
                           threat_level: ThreatLevel, confidence_score: float,
                           detection_method: DetectionMethod, source_feed: str,
                           tags: List[str] = None, description: str = "") -> str:
        """Add a threat indicator to the system"""
        indicator_id = f"ti_{hashlib.md5(f'{indicator_type}:{indicator_value}'.encode('utf-8')).hexdigest()[:12]}"
        
        with self.lock:
            self.threat_indicators[indicator_id] = ThreatIndicator(
                id=indicator_id,
                indicator_type=indicator_type,
                indicator_value=indicator_value,
                threat_level=threat_level,
                confidence_score=confidence_score,
                detection_method=detection_method,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                source_feed=source_feed,
                tags=tags or [],
                description=description
            )
        
        logger.info(f"Added threat indicator: {indicator_id} - {indicator_type}:{indicator_value}")
        return indicator_id
    
    def get_indicator_by_value(self, indicator_type: str, indicator_value: str) -> Optional[ThreatIndicator]:
        """Get a threat indicator by its value"""
        with self.lock:
            for indicator in self.threat_indicators.values():
                if indicator.indicator_type == indicator_type and indicator.indicator_value == indicator_value:
                    return indicator
        return None
    
    def is_threat_indicated(self, indicator_type: str, indicator_value: str) -> Dict[str, Any]:
        """Check if an indicator is in the threat database"""
        indicator = self.get_indicator_by_value(indicator_type, indicator_value)
        if indicator:
            return {
                'is_threat': True,
                'indicator': indicator,
                'threat_level': indicator.threat_level,
                'confidence_score': indicator.confidence_score,
                'description': indicator.description
            }
        return {'is_threat': False}
    
    def update_threat_intelligence(self):
        """Update threat intelligence from all sources"""
        current_time = datetime.utcnow()
        
        for source_id, source_info in self.feed_sources.items():
            if (current_time - source_info['last_update']).seconds >= source_info['interval']:
                self._fetch_threat_data(source_id, source_info['url'])
                source_info['last_update'] = current_time
    
    def _fetch_threat_data(self, source_id: str, url: str):
        """Fetch threat data from a source"""
        try:
            # In a real implementation, this would fetch from actual threat feeds
            # For demonstration, we'll simulate with mock data
            logger.info(f"Fetching threat data from {source_id}")
            
            # Simulate adding new indicators
            mock_indicators = [
                ("ip", f"192.168.1.{i}", ThreatLevel.HIGH, 0.85, DetectionMethod.SIGNATURE_MATCHING, source_id, ["malware", "c2"], f"Malicious IP {i}")
                for i in range(100, 110)
            ]
            
            for indicator_type, indicator_value, threat_level, confidence, method, feed, tags, desc in mock_indicators:
                self.add_threat_indicator(
                    indicator_type, indicator_value, threat_level, confidence, method, feed, tags, desc
                )
            
            logger.info(f"Updated threat intelligence from {source_id}")
            
        except Exception as e:
            logger.error(f"Error fetching threat data from {source_id}: {e}")


class AnomalyDetector:
    """Detects anomalies in network traffic and system behavior"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = [
            'connection_count', 'data_volume', 'error_rate', 'latency', 
            'port_diversity', 'time_variance', 'protocol_anomaly'
        ]
        self.training_data = []
        self.is_trained = False
        self.lock = threading.Lock()
        
        logger.info("Anomaly detector initialized")
    
    def extract_features(self, event: SecurityEvent) -> np.ndarray:
        """Extract features from a security event for anomaly detection"""
        features = np.array([
            1,  # connection_count (simplified)
            len(event.description),  # data_volume proxy
            0.1 if 'error' in event.description.lower() else 0.0,  # error_rate
            abs(event.destination_port - 80),  # latency proxy
            len(set([event.source_port, event.destination_port])),  # port_diversity
            event.timestamp.second / 60,  # time_variance
            1 if event.protocol not in ['TCP', 'UDP', 'ICMP'] else 0  # protocol_anomaly
        ]).reshape(1, -1)
        
        return features
    
    def train_model(self, training_events: List[SecurityEvent]):
        """Train the anomaly detection model"""
        with self.lock:
            if not training_events:
                return
            
            # Extract features from training events
            feature_matrix = []
            for event in training_events:
                features = self.extract_features(event)
                feature_matrix.append(features.flatten())
            
            if feature_matrix:
                X = np.array(feature_matrix)
                X_scaled = self.scaler.fit_transform(X)
                self.model.fit(X_scaled)
                self.is_trained = True
                logger.info(f"Anomaly detection model trained with {len(training_events)} events")
    
    def detect_anomaly(self, event: SecurityEvent) -> Dict[str, Any]:
        """Detect if an event is anomalous"""
        if not self.is_trained:
            # If not trained, use simple heuristics
            return {
                'is_anomaly': event.confidence_score > 0.7,
                'anomaly_score': event.confidence_score,
                'confidence': 0.5
            }
        
        with self.lock:
            features = self.extract_features(event)
            features_scaled = self.scaler.transform(features)
            
            # Predict anomaly
            anomaly_prediction = self.model.predict(features_scaled)[0]
            anomaly_score = self.model.score_samples(features_scaled)[0]
            
            # Convert to probability-like score
            # IsolationForest returns negative scores, more negative = more anomalous
            normalized_score = (anomaly_score + 1) / 2  # Normalize to 0-1 range
            is_anomaly = anomaly_prediction == -1  # -1 indicates anomaly
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': anomaly_score,
                'normalized_score': normalized_score,
                'confidence': abs(normalized_score - 0.5) * 2  # Higher confidence for more extreme scores
            }


class BehavioralAnalyzer:
    """Analyzes behavior patterns to detect threats"""
    
    def __init__(self):
        self.user_profiles = defaultdict(dict)
        self.system_profiles = defaultdict(dict)
        self.anomaly_threshold = 2.0  # Standard deviations
        self.profile_window = timedelta(hours=24)
        self.lock = threading.Lock()
        
        logger.info("Behavioral analyzer initialized")
    
    def update_user_profile(self, user_id: str, activity: Dict[str, Any]):
        """Update a user's behavioral profile"""
        with self.lock:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    'activities': deque(maxlen=1000),
                    'login_times': [],
                    'locations': set(),
                    'devices': set(),
                    'resources_accessed': set(),
                    'created_at': datetime.utcnow()
                }
            
            profile = self.user_profiles[user_id]
            profile['activities'].append({
                'timestamp': datetime.utcnow(),
                'activity': activity,
                'resource': activity.get('resource'),
                'location': activity.get('location'),
                'device': activity.get('device')
            })
            
            # Update profile data
            if 'timestamp' in activity:
                profile['login_times'].append(activity['timestamp'])
            
            if 'location' in activity:
                profile['locations'].add(activity['location'])
            
            if 'device' in activity:
                profile['devices'].add(activity['device'])
            
            if 'resource' in activity:
                profile['resources_accessed'].add(activity['resource'])
    
    def analyze_behavior(self, user_id: str, current_activity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if current activity is anomalous for a user"""
        with self.lock:
            if user_id not in self.user_profiles:
                # New user - low confidence in anomaly detection
                return {
                    'is_anomalous': False,
                    'confidence': 0.3,
                    'reasons': ['new_user'],
                    'baseline_compared': {}
                }
            
            profile = self.user_profiles[user_id]
            current_time = datetime.utcnow()
            
            # Check for anomalous login time
            time_anomaly = False
            reasons = []
            
            if 'timestamp' in current_activity:
                current_hour = current_activity['timestamp'].hour
                # Get typical login hours for this user
                if profile['login_times']:
                    typical_hours = [dt.hour for dt in profile['login_times']]
                    avg_hour = statistics.mean(typical_hours) if typical_hours else 12
                    hour_std = statistics.stdev(typical_hours) if len(typical_hours) > 1 else 2
                    
                    if abs(current_hour - avg_hour) > (2 * hour_std if hour_std > 0 else 4):
                        time_anomaly = True
                        reasons.append('unusual_login_time')
            
            # Check for anomalous location
            location_anomaly = False
            if 'location' in current_activity:
                current_location = current_activity['location']
                if current_location not in profile['locations']:
                    location_anomaly = True
                    reasons.append('new_location')
            
            # Check for anomalous device
            device_anomaly = False
            if 'device' in current_activity:
                current_device = current_activity['device']
                if current_device not in profile['devices']:
                    device_anomaly = True
                    reasons.append('new_device')
            
            # Calculate overall anomaly score
            anomaly_count = sum([time_anomaly, location_anomaly, device_anomaly])
            confidence = min(0.9, anomaly_count * 0.3 + 0.1)  # Base confidence
            
            return {
                'is_anomalous': anomaly_count > 0,
                'confidence': confidence,
                'reasons': reasons,
                'baseline_compared': {
                    'typical_hours': list(set([dt.hour for dt in profile['login_times']])) if profile['login_times'] else [],
                    'known_locations': list(profile['locations']),
                    'known_devices': list(profile['devices'])
                }
            }


class MachineLearningDetector:
    """Advanced ML-based threat detection"""
    
    def __init__(self):
        self.classifiers = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'logistic_regression': LogisticRegression(random_state=42)
        }
        self.scalers = {name: StandardScaler() for name in self.classifiers.keys()}
        self.is_trained = {name: False for name in self.classifiers.keys()}
        self.feature_names = [
            'src_port', 'dst_port', 'protocol_encoded', 'data_size', 
            'connection_duration', 'error_count', 'retry_count'
        ]
        self.lock = threading.Lock()
        
        logger.info("Machine learning detector initialized")
    
    def extract_ml_features(self, event: SecurityEvent) -> np.ndarray:
        """Extract features for ML classification"""
        # Encode protocol
        protocol_map = {'TCP': 0, 'UDP': 1, 'ICMP': 2, 'HTTP': 3, 'HTTPS': 4}
        protocol_encoded = protocol_map.get(event.protocol, 5)  # Unknown protocol
        
        features = np.array([
            event.source_port,
            event.destination_port,
            protocol_encoded,
            len(event.description),  # Proxy for data size
            1,  # Connection duration (simplified)
            0,  # Error count (simplified)
            0   # Retry count (simplified)
        ]).reshape(1, -1)
        
        return features
    
    def train_classifier(self, classifier_name: str, training_events: List[SecurityEvent], labels: List[int]):
        """Train a specific classifier"""
        if classifier_name not in self.classifiers:
            raise ValueError(f"Unknown classifier: {classifier_name}")
        
        with self.lock:
            if not training_events or len(training_events) != len(labels):
                return
            
            # Extract features
            X = []
            for event in training_events:
                features = self.extract_ml_features(event)
                X.append(features.flatten())
            
            if X:
                X = np.array(X)
                y = np.array(labels)
                
                # Scale features
                X_scaled = self.scalers[classifier_name].fit_transform(X)
                
                # Train classifier
                self.classifiers[classifier_name].fit(X_scaled, y)
                self.is_trained[classifier_name] = True
                
                logger.info(f"Trained {classifier_name} classifier with {len(training_events)} events")
    
    def predict_threat(self, event: SecurityEvent) -> Dict[str, Any]:
        """Predict threat probability using trained classifiers"""
        results = {}
        
        with self.lock:
            for name, classifier in self.classifiers.items():
                if self.is_trained[name]:
                    try:
                        features = self.extract_ml_features(event)
                        features_scaled = self.scalers[name].transform(features)
                        
                        # Get prediction probabilities
                        proba = classifier.predict_proba(features_scaled)[0]
                        threat_probability = proba[1] if len(proba) > 1 else 0  # Probability of positive class
                        
                        results[name] = {
                            'probability': threat_probability,
                            'prediction': int(threat_probability > 0.5),
                            'confidence': 0.8  # Model confidence
                        }
                    except Exception as e:
                        logger.error(f"Error predicting with {name}: {e}")
                        results[name] = {
                            'probability': 0.0,
                            'prediction': 0,
                            'confidence': 0.0,
                            'error': str(e)
                        }
                else:
                    results[name] = {
                        'probability': 0.0,
                        'prediction': 0,
                        'confidence': 0.0,
                        'error': 'model_not_trained'
                    }
        
        # Aggregate results
        if results:
            avg_probability = statistics.mean([r['probability'] for r in results.values() if 'error' not in r])
            max_confidence = max([r['confidence'] for r in results.values() if 'error' not in r], default=0)
            
            return {
                'is_threat': avg_probability > 0.5,
                'threat_probability': avg_probability,
                'confidence': max_confidence,
                'individual_predictions': results
            }
        else:
            return {
                'is_threat': False,
                'threat_probability': 0.0,
                'confidence': 0.0,
                'individual_predictions': {}
            }


class ResponseOrchestrator:
    """Orchestrates automated threat responses"""
    
    def __init__(self):
        self.action_queue = queue.PriorityQueue()
        self.executed_actions = deque(maxlen=1000)
        self.response_rules = {}
        self.lock = threading.Lock()
        self.executor_thread = None
        self.running = False
        
        # Initialize response rules
        self._init_response_rules()
        
        logger.info("Response orchestrator initialized")
    
    def _init_response_rules(self):
        """Initialize default response rules"""
        self.response_rules = {
            ThreatLevel.LOW: {
                'default_action': ResponseAction.MONITOR,
                'escalation_threshold': 3,
                'time_window': timedelta(minutes=30)
            },
            ThreatLevel.MEDIUM: {
                'default_action': ResponseAction.ALERT,
                'escalation_threshold': 2,
                'time_window': timedelta(minutes=15)
            },
            ThreatLevel.HIGH: {
                'default_action': ResponseAction.BLOCK_IP,
                'escalation_threshold': 1,
                'time_window': timedelta(minutes=5)
            },
            ThreatLevel.CRITICAL: {
                'default_action': ResponseAction.ISOLATE_ENDPOINT,
                'escalation_threshold': 1,
                'time_window': timedelta(minutes=1)
            },
            ThreatLevel.URGENT: {
                'default_action': ResponseAction.SHUTDOWN_SERVICE,
                'escalation_threshold': 1,
                'time_window': timedelta(seconds=30)
            }
        }
    
    def start_executor(self):
        """Start the response executor thread"""
        if self.running:
            return
        
        self.running = True
        self.executor_thread = threading.Thread(target=self._execute_actions, daemon=True)
        self.executor_thread.start()
        logger.info("Response executor started")
    
    def stop_executor(self):
        """Stop the response executor thread"""
        self.running = False
        if self.executor_thread:
            self.executor_thread.join(timeout=5)
        logger.info("Response executor stopped")
    
    def _execute_actions(self):
        """Execute actions from the queue"""
        while self.running:
            try:
                # Get action with timeout
                priority, action_item = self.action_queue.get(timeout=1)
                
                # Execute the action
                success = self._execute_single_action(action_item)
                
                # Record execution
                execution_record = {
                    'action_id': action_item.id,
                    'action_type': action_item.action.value,
                    'target': action_item.target,
                    'success': success,
                    'executed_at': datetime.utcnow(),
                    'reason': action_item.reason
                }
                
                with self.lock:
                    self.executed_actions.append(execution_record)
                
                self.action_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error executing action: {e}")
    
    def _execute_single_action(self, action_item: ResponseActionItem) -> bool:
        """Execute a single response action"""
        try:
            logger.info(f"Executing action: {action_item.action.value} on {action_item.target}")
            
            # In a real system, these would interface with actual security controls
            # For simulation, we'll just log the action
            if action_item.action == ResponseAction.BLOCK_IP:
                self._block_ip(action_item.target)
            elif action_item.action == ResponseAction.ISOLATE_ENDPOINT:
                self._isolate_endpoint(action_item.target)
            elif action_item.action == ResponseAction.TERMINATE_PROCESS:
                self._terminate_process(action_item.target)
            elif action_item.action == ResponseAction.RESET_CONNECTION:
                self._reset_connection(action_item.target)
            elif action_item.action == ResponseAction.SHUTDOWN_SERVICE:
                self._shutdown_service(action_item.target)
            elif action_item.action == ResponseAction.COLLECT_EVIDENCE:
                self._collect_evidence(action_item.target)
            elif action_item.action == ResponseAction.NOTIFY_SECURITY_TEAM:
                self._notify_security_team(action_item.reason)
            elif action_item.action == ResponseAction.ACTIVATE_INCIDENT_RESPONSE:
                self._activate_incident_response()
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing action {action_item.action.value}: {e}")
            return False
    
    def _block_ip(self, ip_address: str):
        """Block an IP address (simulation)"""
        logger.info(f"BLOCKING IP: {ip_address}")
        # In real system: add to firewall block list
    
    def _isolate_endpoint(self, endpoint_id: str):
        """Isolate an endpoint (simulation)"""
        logger.info(f"ISOLATING endpoint: {endpoint_id}")
        # In real system: quarantine endpoint from network
    
    def _terminate_process(self, process_id: str):
        """Terminate a process (simulation)"""
        logger.info(f"TERMINATING process: {process_id}")
        # In real system: kill process
    
    def _reset_connection(self, connection_info: str):
        """Reset a network connection (simulation)"""
        logger.info(f"RESETTING connection: {connection_info}")
        # In real system: reset TCP connection
    
    def _shutdown_service(self, service_name: str):
        """Shutdown a service (simulation)"""
        logger.info(f"SHUTTING DOWN service: {service_name}")
        # In real system: stop service
    
    def _collect_evidence(self, target: str):
        """Collect evidence from target (simulation)"""
        logger.info(f"COLLECTING EVIDENCE from: {target}")
        # In real system: gather forensics data
    
    def _notify_security_team(self, reason: str):
        """Notify security team (simulation)"""
        logger.info(f"NOTIFYING security team: {reason}")
        # In real system: send alert to SOC
    
    def _activate_incident_response(self):
        """Activate incident response procedure (simulation)"""
        logger.info("ACTIVATING INCIDENT RESPONSE PROCEDURE")
        # In real system: trigger IR playbook
    
    def schedule_response_action(self, action: ResponseAction, target: str, 
                               priority: int, reason: str, 
                               confidence_score: float) -> str:
        """Schedule a response action for execution"""
        action_id = f"action_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        action_item = ResponseActionItem(
            id=action_id,
            action=action,
            target=target,
            priority=priority,
            reason=reason,
            confidence_score=confidence_score,
            execution_time=datetime.utcnow(),
            status="pending"
        )
        
        # Add to queue with priority (lower number = higher priority)
        self.action_queue.put((priority, action_item))
        
        logger.info(f"Scheduled action: {action.value} on {target} (priority: {priority})")
        return action_id
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get statistics about executed responses"""
        with self.lock:
            if not self.executed_actions:
                return {}
            
            total_actions = len(self.executed_actions)
            successful_actions = sum(1 for action in self.executed_actions if action['success'])
            failed_actions = total_actions - successful_actions
            
            action_types = [action['action_type'] for action in self.executed_actions]
            action_type_counts = {}
            for action_type in action_types:
                action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
            
            return {
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'failed_actions': failed_actions,
                'success_rate': successful_actions / total_actions if total_actions > 0 else 0,
                'action_type_distribution': action_type_counts,
                'recent_actions': list(self.executed_actions)[-10:]  # Last 10 actions
            }


class AutonomousThreatResponseSystem:
    """Main autonomous threat response system"""
    
    def __init__(self):
        self.threat_intel = ThreatIntelligenceManager()
        self.anomaly_detector = AnomalyDetector()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.ml_detector = MachineLearningDetector()
        self.response_orchestrator = ResponseOrchestrator()
        
        self.security_events = deque(maxlen=10000)
        self.active_threats = {}
        self.response_history = deque(maxlen=5000)
        self.system_metrics = {}
        self.lock = threading.Lock()
        self.running = False
        self.monitoring_thread = None
        
        # Initialize with default threat feeds
        self._init_default_feeds()
        
        logger.info("Autonomous Threat Response System initialized")
    
    def _init_default_feeds(self):
        """Initialize default threat intelligence feeds"""
        self.threat_intel.add_feed_source(
            "abuse_ch_ssl", 
            "https://sslbl.abuse.ch/blacklist/sslipblacklist.csv"
        )
        self.threat_intel.add_feed_source(
            "feodo_tracker", 
            "https://feodotracker.abuse.ch/downloads/ipblocklist.txt"
        )
        self.threat_intel.add_feed_source(
            "malware_domains", 
            "http://www.malwaredomainlist.com/hostslist/hosts.txt"
        )
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.running:
            logger.warning("Autonomous threat response system already running")
            return
        
        self.running = True
        self.response_orchestrator.start_executor()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Autonomous threat response system started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        self.response_orchestrator.stop_executor()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Autonomous threat response system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Update threat intelligence
                self.threat_intel.update_threat_intelligence()
                
                # Process any queued events
                # In a real system, this would continuously monitor for new events
                # For this simulation, we'll just sleep
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def process_security_event(self, event: SecurityEvent) -> List[ResponseActionItem]:
        """Process a security event and determine appropriate responses"""
        start_time = datetime.utcnow()
        
        # Add event to history
        with self.lock:
            self.security_events.append(event)
        
        # Analyze the event using multiple detection methods
        analysis_results = self._analyze_event(event)
        
        # Determine appropriate responses based on analysis
        response_actions = self._determine_responses(event, analysis_results)
        
        # Schedule responses for execution
        scheduled_actions = []
        for action in response_actions:
            action_id = self.response_orchestrator.schedule_response_action(
                action.action,
                action.target,
                action.priority,
                action.reason,
                action.confidence_score
            )
            scheduled_actions.append(action)
        
        # Record the analysis and response decision
        response_record = {
            'event_id': event.id,
            'analysis_results': analysis_results,
            'scheduled_actions': [a.id for a in scheduled_actions],
            'decision_time': datetime.utcnow(),
            'processing_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
        }
        
        with self.lock:
            self.response_history.append(response_record)
        
        logger.info(f"Processed event {event.id}: {len(scheduled_actions)} actions scheduled")
        return scheduled_actions
    
    def _analyze_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """Analyze an event using multiple detection methods"""
        analysis = {
            'timestamp': datetime.utcnow(),
            'event_id': event.id,
            'threat_indicators': self.threat_intel.is_threat_indicated('ip', event.source_ip),
            'anomaly_detection': self.anomaly_detector.detect_anomaly(event),
            'behavioral_analysis': {'is_anomalous': False, 'confidence': 0.0},
            'ml_prediction': self.ml_detector.predict_threat(event),
            'combined_risk_score': 0.0,
            'recommended_threat_level': event.threat_level
        }
        
        # Calculate combined risk score
        scores = []
        weights = []
        
        # Threat indicator score
        if analysis['threat_indicators']['is_threat']:
            scores.append(analysis['threat_indicators']['indicator'].confidence_score)
            weights.append(0.4)
        
        # Anomaly score
        scores.append(analysis['anomaly_detection']['normalized_score'])
        weights.append(0.3)
        
        # ML prediction score
        scores.append(analysis['ml_prediction']['threat_probability'])
        weights.append(0.3)
        
        if scores and weights:
            analysis['combined_risk_score'] = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine recommended threat level based on combined score
        if analysis['combined_risk_score'] > 0.8:
            analysis['recommended_threat_level'] = ThreatLevel.CRITICAL
        elif analysis['combined_risk_score'] > 0.6:
            analysis['recommended_threat_level'] = ThreatLevel.HIGH
        elif analysis['combined_risk_score'] > 0.4:
            analysis['recommended_threat_level'] = ThreatLevel.MEDIUM
        else:
            analysis['recommended_threat_level'] = ThreatLevel.LOW
        
        return analysis
    
    def _determine_responses(self, event: SecurityEvent, analysis: Dict[str, Any]) -> List[ResponseActionItem]:
        """Determine appropriate responses based on analysis"""
        responses = []
        
        # Get response rule for the determined threat level
        threat_level = analysis['recommended_threat_level']
        rule = self.response_orchestrator.response_rules.get(threat_level, 
                                                           self.response_orchestrator.response_rules[ThreatLevel.MEDIUM])
        
        # Determine action based on threat level
        action = rule['default_action']
        
        # Adjust action based on additional factors
        if analysis['threat_indicators']['is_threat']:
            if analysis['threat_indicators']['indicator'].threat_level in [ThreatLevel.CRITICAL, ThreatLevel.URGENT]:
                action = ResponseAction.ISOLATE_ENDPOINT
        elif analysis['anomaly_detection']['is_anomaly']:
            if analysis['anomaly_detection']['normalized_score'] > 0.9:
                action = ResponseAction.ALERT
        elif analysis['ml_prediction']['is_threat']:
            if analysis['ml_prediction']['threat_probability'] > 0.9:
                action = ResponseAction.BLOCK_IP
        
        # Create response action
        response_action = ResponseActionItem(
            id=f"resp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
            action=action,
            target=event.source_ip,
            priority=self._get_priority_for_action(action),
            reason=f"Auto-response to {threat_level.value} threat (score: {analysis['combined_risk_score']:.2f})",
            confidence_score=analysis['combined_risk_score'],
            execution_time=datetime.utcnow(),
            status="pending"
        )
        
        responses.append(response_action)
        
        # Add secondary actions based on threat type
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.URGENT]:
            # Collect evidence
            evidence_action = ResponseActionItem(
                id=f"ev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                action=ResponseAction.COLLECT_EVIDENCE,
                target=event.source_ip,
                priority=5,  # High priority
                reason="Evidence collection for high-severity threat",
                confidence_score=analysis['combined_risk_score'],
                execution_time=datetime.utcnow(),
                status="pending"
            )
            responses.append(evidence_action)
        
        if threat_level == ThreatLevel.URGENT:
            # Notify security team
            notify_action = ResponseActionItem(
                id=f"ntf_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                action=ResponseAction.NOTIFY_SECURITY_TEAM,
                target="security_team",
                priority=1,  # Highest priority
                reason="URGENT threat detected requiring immediate attention",
                confidence_score=analysis['combined_risk_score'],
                execution_time=datetime.utcnow(),
                status="pending"
            )
            responses.append(notify_action)
        
        return responses
    
    def _get_priority_for_action(self, action: ResponseAction) -> int:
        """Get priority for a response action"""
        priority_map = {
            ResponseAction.URGENT: 1,
            ResponseAction.SHUTDOWN_SERVICE: 2,
            ResponseAction.ISOLATE_ENDPOINT: 3,
            ResponseAction.BLOCK_IP: 4,
            ResponseAction.TERMINATE_PROCESS: 5,
            ResponseAction.RESET_CONNECTION: 6,
            ResponseAction.COLLECT_EVIDENCE: 7,
            ResponseAction.NOTIFY_SECURITY_TEAM: 8,
            ResponseAction.ALERT: 9,
            ResponseAction.MONITOR: 10
        }
        return priority_map.get(action, 5)  # Default to medium priority
    
    def add_security_event(self, event_type: str, source_ip: str, destination_ip: str,
                          source_port: int, destination_port: int, protocol: str,
                          threat_level: ThreatLevel, description: str,
                          confidence_score: float = 0.5) -> str:
        """Add a security event for processing"""
        event = SecurityEvent(
            id=f"evt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            source_ip=source_ip,
            destination_ip=destination_ip,
            source_port=source_port,
            destination_port=destination_port,
            protocol=protocol,
            threat_level=threat_level,
            confidence_score=confidence_score,
            detection_method=DetectionMethod.MACHINE_LEARNING,  # Default
            description=description,
            related_indicators=[],
            raw_data={},
            status="detected"
        )
        
        # Process the event
        response_actions = self.process_security_event(event)
        
        logger.info(f"Added and processed security event: {event.id} with {len(response_actions)} responses")
        return event.id
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of the autonomous response system"""
        with self.lock:
            return {
                'active_events': len(self.security_events),
                'active_threats': len(self.active_threats),
                'response_history_count': len(self.response_history),
                'threat_intel_count': len(self.threat_intel.threat_indicators),
                'running': self.running,
                'response_stats': self.response_orchestrator.get_response_statistics(),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_threat_intelligence(self) -> List[ThreatIndicator]:
        """Get current threat intelligence"""
        return list(self.threat_intel.threat_indicators.values())
    
    def get_recent_events(self, limit: int = 50) -> List[SecurityEvent]:
        """Get recent security events"""
        with self.lock:
            return list(self.security_events)[-limit:]
    
    def get_response_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get response history"""
        with self.lock:
            return list(self.response_history)[-limit:]
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str,
                           threat_level: ThreatLevel, confidence_score: float,
                           detection_method: DetectionMethod, source_feed: str,
                           tags: List[str] = None, description: str = "") -> str:
        """Add a threat indicator to the system"""
        return self.threat_intel.add_threat_indicator(
            indicator_type, indicator_value, threat_level, confidence_score,
            detection_method, source_feed, tags, description
        )


# Example usage and testing
if __name__ == "__main__":
    # Initialize the autonomous threat response system
    atr_system = AutonomousThreatResponseSystem()
    
    print("🤖 Autonomous Threat Response System Initialized...")
    
    # Start monitoring
    atr_system.start_monitoring()
    
    # Add some threat indicators
    print("\nAdding threat indicators...")
    indicator1 = atr_system.add_threat_indicator(
        indicator_type="ip",
        indicator_value="103.76.106.200",
        threat_level=ThreatLevel.HIGH,
        confidence_score=0.9,
        detection_method=DetectionMethod.SIGNATURE_MATCHING,
        source_feed="feodo_tracker",
        tags=["botnet", "c2"],
        description="Known botnet command and control server"
    )
    print(f"Added threat indicator: {indicator1}")
    
    indicator2 = atr_system.add_threat_indicator(
        indicator_type="ip",
        indicator_value="185.132.189.10",
        threat_level=ThreatLevel.CRITICAL,
        confidence_score=0.95,
        detection_method=DetectionMethod.SIGNATURE_MATCHING,
        source_feed="abuse_ch_ssl",
        tags=["malware", "ssl"],
        description="Malware distribution server with suspicious SSL certificate"
    )
    print(f"Added threat indicator: {indicator2}")
    
    # Simulate security events
    print("\nSimulating security events...")
    
    # Event 1: Connection from known malicious IP
    event1_id = atr_system.add_security_event(
        event_type="port_scan",
        source_ip="103.76.106.200",  # Known bad IP
        destination_ip="192.168.1.100",
        source_port=12345,
        destination_port=22,
        protocol="TCP",
        threat_level=ThreatLevel.HIGH,
        description="Port scan detected from known botnet IP",
        confidence_score=0.85
    )
    print(f"Added security event: {event1_id}")
    
    # Event 2: Suspicious internal traffic
    event2_id = atr_system.add_security_event(
        event_type="unusual_traffic",
        source_ip="192.168.1.50",
        destination_ip="192.168.1.1",
        source_port=45678,
        destination_port=445,
        protocol="TCP",
        threat_level=ThreatLevel.MEDIUM,
        description="Unusual SMB traffic from workstation to domain controller",
        confidence_score=0.6
    )
    print(f"Added security event: {event2_id}")
    
    # Event 3: High-volume DDoS attack
    event3_id = atr_system.add_security_event(
        event_type="ddos_attack",
        source_ip="185.132.189.10",  # Another known bad IP
        destination_ip="192.168.1.200",
        source_port=80,
        destination_port=80,
        protocol="HTTP",
        threat_level=ThreatLevel.CRITICAL,
        description="High-volume HTTP DDoS attack detected",
        confidence_score=0.92
    )
    print(f"Added security event: {event3_id}")
    
    # Wait for events to be processed
    time.sleep(5)
    
    # Get system status
    print("\nGetting system status...")
    status = atr_system.get_system_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Get recent events
    print("\nGetting recent events...")
    recent_events = atr_system.get_recent_events(limit=5)
    print(f"Retrieved {len(recent_events)} recent events")
    
    # Get response history
    print("\nGetting response history...")
    response_history = atr_system.get_response_history(limit=5)
    print(f"Retrieved {len(response_history)} response records")
    
    # Get threat intelligence
    print("\nGetting threat intelligence...")
    threat_intel = atr_system.get_threat_intelligence()
    print(f"Threat intelligence database contains {len(threat_intel)} indicators")
    
    # Get response statistics
    print("\nGetting response statistics...")
    response_stats = status.get('response_stats', {})
    print(json.dumps(response_stats, indent=2, default=str))
    
    # Stop monitoring
    atr_system.stop_monitoring()
    
    print("\n✅ Autonomous Threat Response System Test Completed")