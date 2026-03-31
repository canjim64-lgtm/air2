"""
Advanced Cybersecurity Mesh Architecture for AirOne Professional
Implements distributed security architecture with adaptive threat response
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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityNodeType(Enum):
    """Types of security nodes in the mesh"""
    FIREWALL = "firewall"
    IDS = "intrusion_detection_system"
    IPS = "intrusion_prevention_system"
    SIEM = "siem"
    EDR = "endpoint_detection_response"
    IAM = "identity_access_management"
    DLP = "data_loss_prevention"
    VULN_SCANNER = "vulnerability_scanner"
    THREAT_INTEL = "threat_intelligence"
    DECEPTION = "deception_platform"


class ThreatSeverity(Enum):
    """Severity levels for threats"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class SecurityPolicyAction(Enum):
    """Actions that can be taken by security policies"""
    ALLOW = "allow"
    BLOCK = "block"
    MONITOR = "monitor"
    ALERT = "alert"
    REDIRECT = "redirect"
    ISOLATE = "isolate"
    TERMINATE = "terminate"


@dataclass
class SecurityEvent:
    """Represents a security event in the mesh"""
    id: str
    timestamp: datetime
    node_id: str
    node_type: SecurityNodeType
    event_type: str
    severity: ThreatSeverity
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    description: str
    confidence_score: float
    related_events: List[str]
    action_taken: SecurityPolicyAction
    status: str  # detected, analyzed, responded, resolved


@dataclass
class SecurityPolicy:
    """Represents a security policy in the mesh"""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]  # Conditions that trigger the policy
    action: SecurityPolicyAction
    priority: int  # Lower number means higher priority
    enabled: bool
    created_at: datetime
    last_updated: datetime
    tags: List[str]


@dataclass
class MeshNode:
    """Represents a node in the cybersecurity mesh"""
    id: str
    node_type: SecurityNodeType
    ip_address: str
    port: int
    location: str
    capabilities: List[str]
    status: str  # active, inactive, maintenance
    last_heartbeat: datetime
    threat_score: float
    connected_nodes: List[str]
    policies: List[str]


class ThreatIntelligenceManager:
    """Manages threat intelligence across the mesh"""
    
    def __init__(self):
        self.threat_indicators = {}
        self.threat_intel_sources = {}
        self.threat_scores = defaultdict(float)
        self.lock = threading.Lock()
        self.update_interval = 300  # 5 minutes
        self.last_update = datetime.utcnow()
        
        logger.info("Threat intelligence manager initialized")
    
    def add_threat_source(self, source_id: str, source_url: str, update_interval: int = 300):
        """Add a threat intelligence source"""
        self.threat_intel_sources[source_id] = {
            'url': source_url,
            'interval': update_interval,
            'last_update': datetime.utcnow(),
            'enabled': True
        }
        logger.info(f"Added threat intelligence source: {source_id}")
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str, 
                           severity: ThreatSeverity, confidence: float,
                           tags: List[str] = None, description: str = "") -> str:
        """Add a threat indicator to the system"""
        indicator_id = f"ti_{hashlib.md5(f'{indicator_type}:{indicator_value}'.encode('utf-8')).hexdigest()[:12]}"
        
        with self.lock:
            self.threat_indicators[indicator_id] = {
                'type': indicator_type,
                'value': indicator_value,
                'severity': severity,
                'confidence': confidence,
                'tags': tags or [],
                'description': description,
                'first_seen': datetime.utcnow(),
                'last_seen': datetime.utcnow(),
                'sources': []
            }
        
        logger.info(f"Added threat indicator: {indicator_id} - {indicator_type}:{indicator_value}")
        return indicator_id
    
    def is_threat_indicated(self, indicator_type: str, indicator_value: str) -> Dict[str, Any]:
        """Check if an indicator is in the threat database"""
        with self.lock:
            for indicator_id, indicator in self.threat_indicators.items():
                if (indicator['type'] == indicator_type and 
                    indicator['value'] == indicator_value):
                    return {
                        'is_threat': True,
                        'indicator_id': indicator_id,
                        'severity': indicator['severity'],
                        'confidence': indicator['confidence'],
                        'description': indicator['description']
                    }
        
        return {'is_threat': False}
    
    def update_threat_intelligence(self):
        """Update threat intelligence from all sources"""
        current_time = datetime.utcnow()
        
        for source_id, source_info in self.threat_intel_sources.items():
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
                ("ip", f"192.168.1.{i}", ThreatSeverity.HIGH, 0.8, ["malware", "c2"]) 
                for i in range(100, 110)
            ]
            
            for indicator_type, indicator_value, severity, confidence, tags in mock_indicators:
                self.add_threat_indicator(
                    indicator_type, indicator_value, severity, confidence, tags
                )
            
            logger.info(f"Updated threat intelligence from {source_id}")
            
        except Exception as e:
            logger.error(f"Error fetching threat data from {source_id}: {e}")
    
    def calculate_threat_score(self, ip_address: str) -> float:
        """Calculate threat score for an IP address"""
        score = 0.0
        
        with self.lock:
            for indicator_id, indicator in self.threat_indicators.items():
                if indicator['type'] == 'ip' and indicator['value'] == ip_address:
                    weight = 1.0 if indicator['severity'] == ThreatSeverity.CRITICAL else 0.8 if indicator['severity'] == ThreatSeverity.HIGH else 0.5
                    score += indicator['confidence'] * weight
        
        # Normalize score to 0-1 range
        return min(1.0, score)


class PolicyEngine:
    """Manages security policies across the mesh"""
    
    def __init__(self):
        self.policies = {}
        self.policy_queue = queue.Queue()
        self.active_policies = set()
        self.lock = threading.Lock()
        
        logger.info("Policy engine initialized")
    
    def create_policy(self, name: str, description: str, conditions: Dict[str, Any],
                     action: SecurityPolicyAction, priority: int = 10,
                     tags: List[str] = None) -> str:
        """Create a new security policy"""
        policy_id = f"policy_{hashlib.md5(name.encode('utf-8')).hexdigest()[:12]}"
        
        policy = SecurityPolicy(
            id=policy_id,
            name=name,
            description=description,
            conditions=conditions,
            action=action,
            priority=priority,
            enabled=True,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            tags=tags or []
        )
        
        with self.lock:
            self.policies[policy_id] = policy
            if policy.enabled:
                self.active_policies.add(policy_id)
        
        logger.info(f"Created security policy: {name} (ID: {policy_id})")
        return policy_id
    
    def evaluate_event_against_policies(self, event: SecurityEvent) -> List[SecurityPolicy]:
        """Evaluate an event against all active policies"""
        matching_policies = []
        
        with self.lock:
            for policy_id in self.active_policies:
                policy = self.policies[policy_id]
                
                if self._policy_matches_event(policy, event):
                    matching_policies.append(policy)
        
        # Sort by priority (lower number = higher priority)
        matching_policies.sort(key=lambda p: p.priority)
        return matching_policies
    
    def _policy_matches_event(self, policy: SecurityPolicy, event: SecurityEvent) -> bool:
        """Check if an event matches a policy's conditions"""
        conditions = policy.conditions
        
        # Check IP-based conditions
        if 'source_ip' in conditions:
            if conditions['source_ip'] == event.source_ip:
                return True
        
        if 'destination_ip' in conditions:
            if conditions['destination_ip'] == event.destination_ip:
                return True
        
        # Check port-based conditions
        if 'source_port' in conditions:
            if conditions['source_port'] == event.source_port:
                return True
        
        if 'destination_port' in conditions:
            if conditions['destination_port'] == event.destination_port:
                return True
        
        # Check protocol conditions
        if 'protocol' in conditions:
            if conditions['protocol'] == event.protocol:
                return True
        
        # Check severity conditions
        if 'min_severity' in conditions:
            severity_order = {
                ThreatSeverity.LOW: 0,
                ThreatSeverity.MEDIUM: 1,
                ThreatSeverity.HIGH: 2,
                ThreatSeverity.CRITICAL: 3,
                ThreatSeverity.URGENT: 4
            }
            if severity_order.get(event.severity, 0) >= severity_order.get(conditions['min_severity'], 0):
                return True
        
        # Check tag conditions
        if 'tags' in conditions:
            if any(tag in event.description.lower() for tag in conditions['tags']):
                return True
        
        return False
    
    def update_policy(self, policy_id: str, **updates) -> bool:
        """Update an existing policy"""
        with self.lock:
            if policy_id not in self.policies:
                return False
            
            policy = self.policies[policy_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(policy, field):
                    setattr(policy, field, value)
            
            policy.last_updated = datetime.utcnow()
            
            # Update active policies set
            if policy.enabled:
                self.active_policies.add(policy_id)
            else:
                self.active_policies.discard(policy_id)
        
        logger.info(f"Updated policy: {policy_id}")
        return True


class MeshCommunicator:
    """Handles communication between mesh nodes"""
    
    def __init__(self, node_id: str, mesh_port: int = 8443):
        self.node_id = node_id
        self.mesh_port = mesh_port
        self.nodes = {}
        self.connection_pool = {}
        self.message_queue = queue.Queue()
        self.lock = threading.Lock()
        self.running = False
        
        logger.info(f"Mesh communicator initialized for node {node_id}")
    
    def register_node(self, node_id: str, ip_address: str, port: int, node_type: SecurityNodeType):
        """Register a node in the mesh"""
        node = {
            'id': node_id,
            'ip': ip_address,
            'port': port,
            'type': node_type,
            'last_seen': datetime.utcnow(),
            'status': 'active'
        }
        
        with self.lock:
            self.nodes[node_id] = node
        
        logger.info(f"Registered mesh node: {node_id} at {ip_address}:{port}")
    
    def broadcast_event(self, event: SecurityEvent):
        """Broadcast a security event to all connected nodes"""
        message = {
            'type': 'security_event',
            'event': self._serialize_event(event),
            'sender': self.node_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to all connected nodes
        for node_id, node_info in self.nodes.items():
            if node_info['status'] == 'active':
                self._send_message_to_node(node_id, message)
    
    def _send_message_to_node(self, node_id: str, message: Dict[str, Any]):
        """Send a message to a specific node"""
        # In a real implementation, this would use secure communication channels
        # For now, we'll just log the message
        logger.debug(f"Sending message to {node_id}: {message['type']}")
    
    def _serialize_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """Serialize a security event for transmission"""
        return {
            'id': event.id,
            'timestamp': event.timestamp.isoformat(),
            'node_id': event.node_id,
            'node_type': event.node_type.value,
            'event_type': event.event_type,
            'severity': event.severity.value,
            'source_ip': event.source_ip,
            'destination_ip': event.destination_ip,
            'source_port': event.source_port,
            'destination_port': event.destination_port,
            'protocol': event.protocol,
            'description': event.description,
            'confidence_score': event.confidence_score,
            'related_events': event.related_events,
            'action_taken': event.action_taken.value,
            'status': event.status
        }
    
    def receive_message(self, message: Dict[str, Any]) -> Optional[SecurityEvent]:
        """Receive and process a message from another node"""
        if message['type'] == 'security_event':
            event_data = message['event']
            event = SecurityEvent(
                id=event_data['id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                node_id=event_data['node_id'],
                node_type=SecurityNodeType(event_data['node_type']),
                event_type=event_data['event_type'],
                severity=ThreatSeverity(event_data['severity']),
                source_ip=event_data['source_ip'],
                destination_ip=event_data['destination_ip'],
                source_port=event_data['source_port'],
                destination_port=event_data['destination_port'],
                protocol=event_data['protocol'],
                description=event_data['description'],
                confidence_score=event_data['confidence_score'],
                related_events=event_data['related_events'],
                action_taken=SecurityPolicyAction(event_data['action_taken']),
                status=event_data['status']
            )
            return event
        return None


class AdaptiveResponseEngine:
    """Adaptive response engine for automated threat mitigation"""
    
    def __init__(self, threat_intel_manager: ThreatIntelligenceManager, 
                 policy_engine: PolicyEngine):
        self.threat_intel = threat_intel_manager
        self.policy_engine = policy_engine
        self.response_history = deque(maxlen=1000)
        self.response_strategies = {}
        self.lock = threading.Lock()
        
        # Initialize response strategies
        self._init_response_strategies()
        
        logger.info("Adaptive response engine initialized")
    
    def _init_response_strategies(self):
        """Initialize adaptive response strategies"""
        self.response_strategies = {
            ThreatSeverity.LOW: {
                'action': SecurityPolicyAction.MONITOR,
                'delay': 0,
                'escalation_threshold': 3
            },
            ThreatSeverity.MEDIUM: {
                'action': SecurityPolicyAction.ALERT,
                'delay': 5,
                'escalation_threshold': 2
            },
            ThreatSeverity.HIGH: {
                'action': SecurityPolicyAction.BLOCK,
                'delay': 1,
                'escalation_threshold': 1
            },
            ThreatSeverity.CRITICAL: {
                'action': SecurityPolicyAction.ISOLATE,
                'delay': 0,
                'escalation_threshold': 1
            },
            ThreatSeverity.URGENT: {
                'action': SecurityPolicyAction.TERMINATE,
                'delay': 0,
                'escalation_threshold': 1
            }
        }
    
    def process_event(self, event: SecurityEvent) -> SecurityPolicyAction:
        """Process a security event and determine appropriate response"""
        # Evaluate against policies
        matching_policies = self.policy_engine.evaluate_event_against_policies(event)
        
        # If there are matching policies, use the highest priority one
        if matching_policies:
            primary_policy = matching_policies[0]
            action = primary_policy.action
        else:
            # Use adaptive strategy based on severity
            strategy = self.response_strategies.get(event.severity, 
                                                  self.response_strategies[ThreatSeverity.MEDIUM])
            action = strategy['action']
        
        # Apply adaptive adjustments based on threat intelligence
        if event.source_ip:
            threat_score = self.threat_intel.calculate_threat_score(event.source_ip)
            if threat_score > 0.8:  # High threat score
                # Escalate response
                if action == SecurityPolicyAction.ALERT:
                    action = SecurityPolicyAction.BLOCK
                elif action == SecurityPolicyAction.BLOCK:
                    action = SecurityPolicyAction.ISOLATE
                elif action == SecurityPolicyAction.MONITOR:
                    action = SecurityPolicyAction.ALERT
        
        # Record response
        response_record = {
            'event_id': event.id,
            'timestamp': datetime.utcnow(),
            'original_severity': event.severity,
            'determined_action': action,
            'threat_score': threat_score if event.source_ip else 0
        }
        
        with self.lock:
            self.response_history.append(response_record)
        
        logger.info(f"Processed event {event.id}: {action.value} (threat score: {threat_score:.2f})")
        return action
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get statistics about response actions"""
        with self.lock:
            if not self.response_history:
                return {}
            
            actions = [record['determined_action'] for record in self.response_history]
            action_counts = {}
            for action in actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
            
            threat_scores = [record['threat_score'] for record in self.response_history]
            
            return {
                'total_responses': len(self.response_history),
                'action_distribution': action_counts,
                'avg_threat_score': statistics.mean(threat_scores) if threat_scores else 0,
                'max_threat_score': max(threat_scores) if threat_scores else 0,
                'min_threat_score': min(threat_scores) if threat_scores else 0
            }


class CybersecurityMeshNode:
    """A node in the cybersecurity mesh architecture"""
    
    def __init__(self, node_id: str, node_type: SecurityNodeType, 
                 ip_address: str, port: int, location: str = "local"):
        self.node_id = node_id
        self.node_type = node_type
        self.ip_address = ip_address
        self.port = port
        self.location = location
        self.status = "active"
        self.capabilities = self._get_capabilities_for_type(node_type)
        self.connected_nodes = set()
        self.event_queue = queue.Queue()
        self.threat_intel_manager = ThreatIntelligenceManager()
        self.policy_engine = PolicyEngine()
        self.mesh_communicator = MeshCommunicator(node_id)
        self.response_engine = AdaptiveResponseEngine(
            self.threat_intel_manager, 
            self.policy_engine
        )
        self.running = False
        self.node_thread = None
        self.lock = threading.Lock()
        
        # Initialize with default policies
        self._init_default_policies()
        
        logger.info(f"Cybersecurity mesh node {node_id} initialized")
    
    def _get_capabilities_for_type(self, node_type: SecurityNodeType) -> List[str]:
        """Get capabilities based on node type"""
        capabilities_map = {
            SecurityNodeType.FIREWALL: ["packet_filtering", "stateful_inspection", "nat", "vpn"],
            SecurityNodeType.IDS: ["signature_detection", "anomaly_detection", "behavioral_analysis"],
            SecurityNodeType.IPS: ["signature_detection", "anomaly_detection", "automated_response", "packet_drop"],
            SecurityNodeType.SIEM: ["log_aggregation", "correlation", "alerting", "dashboards"],
            SecurityNodeType.EDR: ["endpoint_monitoring", "threat_hunting", "forensics", "response"],
            SecurityNodeType.IAM: ["authentication", "authorization", "provisioning", "governance"],
            SecurityNodeType.DLP: ["data_discovery", "classification", "monitoring", "prevention"],
            SecurityNodeType.VULN_SCANNER: ["scanning", "assessment", "reporting", "remediation"],
            SecurityNodeType.THREAT_INTEL: ["intelligence_gathering", "analysis", "sharing", "enrichment"],
            SecurityNodeType.DECEPTION: ["decoy_deployment", "trap_activation", "intelligence_collection"]
        }
        return capabilities_map.get(node_type, ["basic_monitoring"])
    
    def _init_default_policies(self):
        """Initialize default security policies"""
        # Block known malicious IPs
        self.policy_engine.create_policy(
            name="Block Known Malicious IPs",
            description="Block traffic from IPs in threat intelligence database",
            conditions={"min_severity": ThreatSeverity.HIGH},
            action=SecurityPolicyAction.BLOCK,
            priority=1
        )
        
        # Alert on high severity events
        self.policy_engine.create_policy(
            name="Alert on High Severity",
            description="Generate alert for high severity events",
            conditions={"min_severity": ThreatSeverity.HIGH},
            action=SecurityPolicyAction.ALERT,
            priority=2
        )
        
        logger.info(f"Initialized default policies for node {self.node_id}")
    
    def start(self):
        """Start the mesh node"""
        self.running = True
        self.node_thread = threading.Thread(target=self._node_main_loop, daemon=True)
        self.node_thread.start()
        logger.info(f"Mesh node {self.node_id} started")
    
    def stop(self):
        """Stop the mesh node"""
        self.running = False
        if self.node_thread:
            self.node_thread.join(timeout=5)
        logger.info(f"Mesh node {self.node_id} stopped")
    
    def _node_main_loop(self):
        """Main loop for the mesh node"""
        while self.running:
            try:
                # Update threat intelligence periodically
                current_time = datetime.utcnow()
                if (current_time - self.threat_intel_manager.last_update).seconds >= self.threat_intel_manager.update_interval:
                    self.threat_intel_manager.update_threat_intelligence()
                
                # Process events from queue
                try:
                    event = self.event_queue.get(timeout=1)
                    self._process_security_event(event)
                except queue.Empty:
                    continue
                
            except Exception as e:
                logger.error(f"Error in mesh node {self.node_id} main loop: {e}")
                time.sleep(1)  # Brief pause before continuing
    
    def _process_security_event(self, event: SecurityEvent):
        """Process a security event"""
        # Determine response action
        action = self.response_engine.process_event(event)
        
        # Update event with action taken
        event.action_taken = action
        event.status = "analyzed"
        
        # Broadcast event to other nodes
        self.mesh_communicator.broadcast_event(event)
        
        # Log the event
        logger.info(f"Node {self.node_id} processed event {event.id}: {action.value}")
    
    def add_security_event(self, event_type: str, severity: ThreatSeverity,
                          source_ip: str, destination_ip: str,
                          source_port: int, destination_port: int,
                          protocol: str, description: str,
                          confidence_score: float = 0.5) -> str:
        """Add a security event to the processing queue"""
        event = SecurityEvent(
            id=f"event_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
            timestamp=datetime.utcnow(),
            node_id=self.node_id,
            node_type=self.node_type,
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            destination_ip=destination_ip,
            source_port=source_port,
            destination_port=destination_port,
            protocol=protocol,
            description=description,
            confidence_score=confidence_score,
            related_events=[],
            action_taken=SecurityPolicyAction.ALERT,  # Will be updated during processing
            status="detected"
        )
        
        self.event_queue.put(event)
        logger.debug(f"Added security event to queue: {event.id}")
        return event.id
    
    def register_mesh_node(self, node_id: str, ip_address: str, port: int, 
                          node_type: SecurityNodeType):
        """Register another node in the mesh"""
        self.mesh_communicator.register_node(node_id, ip_address, port, node_type)
        self.connected_nodes.add(node_id)
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str,
                           severity: ThreatSeverity, confidence: float,
                           tags: List[str] = None, description: str = "") -> str:
        """Add a threat indicator to this node's intelligence database"""
        return self.threat_intel_manager.add_threat_indicator(
            indicator_type, indicator_value, severity, confidence, tags, description
        )
    
    def create_security_policy(self, name: str, description: str, 
                             conditions: Dict[str, Any],
                             action: SecurityPolicyAction, 
                             priority: int = 10,
                             tags: List[str] = None) -> str:
        """Create a security policy on this node"""
        return self.policy_engine.create_policy(
            name, description, conditions, action, priority, tags
        )
    
    def get_node_status(self) -> Dict[str, Any]:
        """Get the status of this node"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'ip_address': self.ip_address,
            'port': self.port,
            'location': self.location,
            'status': self.status,
            'capabilities': self.capabilities,
            'connected_nodes': list(self.connected_nodes),
            'event_queue_size': self.event_queue.qsize(),
            'running': self.running,
            'threat_intel_count': len(self.threat_intel_manager.threat_indicators),
            'policy_count': len(self.policy_engine.policies),
            'response_stats': self.response_engine.get_response_statistics()
        }


class MeshOrchestrator:
    """Orchestrates the entire cybersecurity mesh"""
    
    def __init__(self):
        self.nodes = {}
        self.global_policies = {}
        self.threat_intel_sources = {}
        self.lock = threading.Lock()
        self.orchestrator_thread = None
        self.running = False
        
        logger.info("Mesh orchestrator initialized")
    
    def create_node(self, node_id: str, node_type: SecurityNodeType,
                   ip_address: str, port: int, location: str = "local") -> CybersecurityMeshNode:
        """Create a new mesh node"""
        node = CybersecurityMeshNode(node_id, node_type, ip_address, port, location)
        
        with self.lock:
            self.nodes[node_id] = node
        
        logger.info(f"Created mesh node: {node_id}")
        return node
    
    def start_all_nodes(self):
        """Start all registered nodes"""
        with self.lock:
            for node_id, node in self.nodes.items():
                node.start()
        
        self.running = True
        self.orchestrator_thread = threading.Thread(target=self._orchestration_loop, daemon=True)
        self.orchestrator_thread.start()
        
        logger.info("Started all mesh nodes")
    
    def stop_all_nodes(self):
        """Stop all nodes"""
        self.running = False
        if self.orchestrator_thread:
            self.orchestrator_thread.join(timeout=5)
        
        with self.lock:
            for node_id, node in self.nodes.items():
                node.stop()
        
        logger.info("Stopped all mesh nodes")
    
    def _orchestration_loop(self):
        """Main orchestration loop"""
        while self.running:
            try:
                # Perform health checks on nodes
                self._perform_health_checks()
                
                # Distribute global policies
                self._distribute_global_policies()
                
                # Aggregate threat intelligence
                self._aggregate_threat_intelligence()
                
                # Sleep before next iteration
                time.sleep(30)  # Every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _perform_health_checks(self):
        """Perform health checks on all nodes"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_nodes': len(self.nodes),
            'healthy_nodes': 0,
            'degraded_nodes': 0,
            'offline_nodes': 0,
            'node_status': {}
        }
        
        for node_id, node in self.nodes.items():
            try:
                status = node.get_node_status()
                if status.get('health', 'unknown') == 'healthy':
                    health_status['healthy_nodes'] += 1
                elif status.get('health', 'unknown') == 'degraded':
                    health_status['degraded_nodes'] += 1
                else:
                    health_status['offline_nodes'] += 1
                    
                health_status['node_status'][node_id] = status
            except Exception as e:
                logger.error(f"Health check failed for node {node_id}: {e}")
                health_status['offline_nodes'] += 1
                health_status['node_status'][node_id] = {'health': 'error', 'error': str(e)}
        
        self.mesh_health = health_status
        return health_status

    def _distribute_global_policies(self):
        """Distribute global security policies to all nodes"""
        distribution_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'policies_distributed': len(self.global_policies),
            'nodes_updated': 0,
            'failures': []
        }
        
        for node_id, node in self.nodes.items():
            try:
                for policy_id, policy in self.global_policies.items():
                    node.policy_enforcement_point.enforce_policy(policy)
                distribution_status['nodes_updated'] += 1
            except Exception as e:
                logger.error(f"Failed to distribute policies to node {node_id}: {e}")
                distribution_status['failures'].append({
                    'node_id': node_id,
                    'error': str(e)
                })
        
        logger.info(f"Distributed {distribution_status['policies_distributed']} policies to {distribution_status['nodes_updated']} nodes")
        return distribution_status

    def _aggregate_threat_intelligence(self):
        """Aggregate threat intelligence from all nodes"""
        aggregated_threats = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_threats': 0,
            'critical_threats': 0,
            'high_threats': 0,
            'medium_threats': 0,
            'low_threats': 0,
            'threats_by_node': {},
            'common_threats': []
        }
        
        threat_counts = {}
        
        for node_id, node in self.nodes.items():
            try:
                node_threats = node.threat_intelligence_hub.get_recent_threats(limit=100)
                aggregated_threats['threats_by_node'][node_id] = len(node_threats)
                aggregated_threats['total_threats'] += len(node_threats)
                
                for threat in node_threats:
                    severity = threat.get('severity', 'low')
                    threat_key = threat.get('threat_type', 'unknown')
                    
                    if severity == 'critical':
                        aggregated_threats['critical_threats'] += 1
                    elif severity == 'high':
                        aggregated_threats['high_threats'] += 1
                    elif severity == 'medium':
                        aggregated_threats['medium_threats'] += 1
                    else:
                        aggregated_threats['low_threats'] += 1
                    
                    # Count threat types for common threats analysis
                    threat_counts[threat_key] = threat_counts.get(threat_key, 0) + 1
                    
            except Exception as e:
                logger.error(f"Failed to aggregate threats from node {node_id}: {e}")
        
        # Find common threats (appearing in multiple nodes)
        aggregated_threats['common_threats'] = [
            {'threat_type': k, 'count': v}
            for k, v in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            if v > 1
        ]
        
        self.aggregated_threat_intelligence = aggregated_threats
        return aggregated_threats
    
    def add_threat_intelligence_source(self, source_id: str, source_url: str):
        """Add a global threat intelligence source"""
        for node in self.nodes.values():
            node.threat_intel_manager.add_threat_source(source_id, source_url)
        
        self.threat_intel_sources[source_id] = source_url
        logger.info(f"Added global threat intelligence source: {source_id}")
    
    def get_mesh_topology(self) -> Dict[str, Any]:
        """Get the current mesh topology"""
        topology = {
            'nodes': {},
            'connections': [],
            'global_policies': len(self.global_policies),
            'threat_sources': list(self.threat_intel_sources.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with self.lock:
            for node_id, node in self.nodes.items():
                topology['nodes'][node_id] = node.get_node_status()
                
                # Add connections
                for connected_node in node.connected_nodes:
                    topology['connections'].append({
                        'from': node_id,
                        'to': connected_node,
                        'status': 'active'
                    })
        
        return topology
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get overall security metrics for the mesh"""
        metrics = {
            'total_nodes': len(self.nodes),
            'active_nodes': 0,
            'total_events_processed': 0,
            'threat_indicators': 0,
            'policies': 0,
            'critical_events': 0,
            'high_severity_events': 0,
            'blocked_connections': 0,
            'isolated_endpoints': 0
        }
        
        with self.lock:
            for node in self.nodes.values():
                node_status = node.get_node_status()
                if node_status['running']:
                    metrics['active_nodes'] += 1
                
                # Aggregate metrics from response stats
                response_stats = node_status.get('response_stats', {})
                if 'action_distribution' in response_stats:
                    action_dist = response_stats['action_distribution']
                    metrics['blocked_connections'] += action_dist.get('block', 0)
                    metrics['isolated_endpoints'] += action_dist.get('isolate', 0)
        
        return metrics


# Example usage and testing
if __name__ == "__main__":
    # Initialize the mesh orchestrator
    orchestrator = MeshOrchestrator()
    
    print("🕸️  Advanced Cybersecurity Mesh Architecture Initialized...")
    
    # Create different types of security nodes
    print("\nCreating mesh nodes...")
    
    # Firewall node
    firewall_node = orchestrator.create_node(
        node_id="fw_node_001",
        node_type=SecurityNodeType.FIREWALL,
        ip_address="192.168.1.10",
        port=8443,
        location="perimeter"
    )
    
    # IDS node
    ids_node = orchestrator.create_node(
        node_id="ids_node_001",
        node_type=SecurityNodeType.IDS,
        ip_address="192.168.1.11",
        port=8444,
        location="internal"
    )
    
    # SIEM node
    siem_node = orchestrator.create_node(
        node_id="siem_node_001",
        node_type=SecurityNodeType.SIEM,
        ip_address="192.168.1.12",
        port=8445,
        location="management"
    )
    
    # Connect nodes in the mesh
    firewall_node.register_mesh_node(ids_node.node_id, ids_node.ip_address, ids_node.port, ids_node.node_type)
    firewall_node.register_mesh_node(siem_node.node_id, siem_node.ip_address, siem_node.port, siem_node.node_type)
    ids_node.register_mesh_node(firewall_node.node_id, firewall_node.ip_address, firewall_node.port, firewall_node.node_type)
    ids_node.register_mesh_node(siem_node.node_id, siem_node.ip_address, siem_node.port, siem_node.node_type)
    siem_node.register_mesh_node(firewall_node.node_id, firewall_node.ip_address, firewall_node.port, firewall_node.node_type)
    siem_node.register_mesh_node(ids_node.node_id, ids_node.ip_address, ids_node.port, ids_node.node_type)
    
    print(f"Created {len(orchestrator.nodes)} mesh nodes")
    
    # Add threat intelligence sources
    print("\nAdding threat intelligence sources...")
    orchestrator.add_threat_intelligence_source(
        "feodo_tracker", 
        "https://feodotracker.abuse.ch/downloads/ipblocklist.txt"
    )
    orchestrator.add_threat_intelligence_source(
        "malware_domains", 
        "http://www.malwaredomainlist.com/hostslist/hosts.txt"
    )
    
    # Add threat indicators
    print("\nAdding threat indicators...")
    fw_indicator_id = firewall_node.add_threat_indicator(
        indicator_type="ip",
        indicator_value="103.76.106.200",
        severity=ThreatSeverity.HIGH,
        confidence=0.9,
        tags=["botnet", "c2"],
        description="Known botnet command and control server"
    )
    print(f"Added threat indicator to firewall node: {fw_indicator_id}")
    
    # Create security policies
    print("\nCreating security policies...")
    fw_policy_id = firewall_node.create_security_policy(
        name="Block Botnet IPs",
        description="Block traffic to/from known botnet IPs",
        conditions={"min_severity": ThreatSeverity.HIGH},
        action=SecurityPolicyAction.BLOCK,
        priority=1
    )
    print(f"Created policy on firewall node: {fw_policy_id}")
    
    # Start all nodes
    print("\nStarting mesh nodes...")
    orchestrator.start_all_nodes()
    
    # Simulate security events
    print("\nSimulating security events...")
    
    # Simulate a malicious connection attempt
    event1_id = firewall_node.add_security_event(
        event_type="port_scan",
        severity=ThreatSeverity.HIGH,
        source_ip="103.76.106.200",  # Known bad IP
        destination_ip="192.168.1.100",
        source_port=12345,
        destination_port=22,
        protocol="TCP",
        description="Port scan detected from known botnet IP",
        confidence_score=0.85
    )
    print(f"Added security event: {event1_id}")
    
    # Simulate another event
    event2_id = ids_node.add_security_event(
        event_type="suspicious_traffic",
        severity=ThreatSeverity.MEDIUM,
        source_ip="192.168.1.50",
        destination_ip="192.168.1.100",
        source_port=45678,
        destination_port=80,
        protocol="HTTP",
        description="Suspicious HTTP traffic pattern detected",
        confidence_score=0.65
    )
    print(f"Added security event: {event2_id}")
    
    # Wait for events to be processed
    time.sleep(5)
    
    # Get mesh topology
    print("\nGetting mesh topology...")
    topology = orchestrator.get_mesh_topology()
    print(f"Mesh topology retrieved: {len(topology['nodes'])} nodes, {len(topology['connections'])} connections")
    
    # Get security metrics
    print("\nGetting security metrics...")
    metrics = orchestrator.get_security_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Get individual node status
    print("\nGetting node statuses...")
    for node_id, node in orchestrator.nodes.items():
        status = node.get_node_status()
        print(f"Node {node_id}: {status['status']}, Events processed: {status['event_queue_size']}")
    
    # Stop all nodes
    print("\nStopping mesh nodes...")
    orchestrator.stop_all_nodes()
    
    print("\n✅ Advanced Cybersecurity Mesh Architecture Test Completed")