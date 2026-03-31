"""
Advanced Threat Intelligence System for AirOne Professional
Implements threat detection, intelligence gathering, and predictive analysis
"""

import asyncio
import time
import json
import sqlite3
import hashlib
import hmac
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import re
import requests
import feedparser
from urllib.parse import urlparse
import whois
import socket
import ipaddress
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import pipeline
import dns.resolver
import dns.reversename
from functools import wraps
import secrets
import pickle
import joblib
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Levels of threat severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats"""
    MALWARE = "malware"
    PHISHING = "phishing"
    DDOS = "ddos"
    RANSOMWARE = "ransomware"
    ADVANCED_PERSISTENT_THREAT = "apt"
    INSIDER_THREAT = "insider_threat"
    ZERO_DAY = "zero_day"
    SOCIAL_ENGINEERING = "social_engineering"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class IntelligenceSource(Enum):
    """Sources of threat intelligence"""
    OPEN_SOURCE = "open_source"
    COMMERCIAL_FEED = "commercial_feed"
    INTERNAL_EVENTS = "internal_events"
    HONEY_POT = "honey_pot"
    VULNERABILITY_DB = "vulnerability_db"
    DARK_WEB = "dark_web"
    SOCIAL_MEDIA = "social_media"
    TECHNICAL_FORUMS = "technical_forums"


@dataclass
class ThreatIndicator:
    """Represents a threat indicator"""
    id: str
    indicator_type: str  # IP, domain, hash, URL, email
    indicator_value: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    source: IntelligenceSource
    confidence_score: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    tags: List[str]
    description: str
    related_indicators: List[str]
    tlp_level: str  # Traffic Light Protocol level


@dataclass
class ThreatIntelligence:
    """Represents gathered threat intelligence"""
    id: str
    threat_id: str
    source: IntelligenceSource
    confidence: float
    severity: ThreatLevel
    description: str
    indicators: List[ThreatIndicator]
    affected_systems: List[str]
    timeline: Dict[str, datetime]
    recommendations: List[str]
    created_at: datetime


@dataclass
class ThreatEvent:
    """Represents a detected threat event"""
    id: str
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    description: str
    confidence_score: float
    related_indicators: List[str]
    status: str  # detected, investigated, mitigated, false_positive
    assigned_to: Optional[str] = None


class ThreatIntelligenceFeed:
    """Manages threat intelligence feeds"""
    
    def __init__(self, feed_url: str, source: IntelligenceSource):
        self.feed_url = feed_url
        self.source = source
        self.last_updated = datetime.utcnow()
        self.indicators = []
        self.lock = threading.Lock()
    
    def update_feed(self) -> bool:
        """Update the threat intelligence feed"""
        try:
            if self.source == IntelligenceSource.OPEN_SOURCE:
                return self._update_open_source_feed()
            elif self.source == IntelligenceSource.COMMERCIAL_FEED:
                return self._update_commercial_feed()
            elif self.source == IntelligenceSource.VULNERABILITY_DB:
                return self._update_vulnerability_db()
            else:
                logger.warning(f"Unsupported feed source: {self.source}")
                return False
        except Exception as e:
            logger.error(f"Error updating feed {self.feed_url}: {e}")
            return False
    
    def _update_open_source_feed(self) -> bool:
        """Update from open source feeds like RSS"""
        try:
            feed = feedparser.parse(self.feed_url)
            new_indicators = []
            
            for entry in feed.entries:
                # Parse threat indicators from feed entry
                # This is a simplified example - real implementation would parse actual threat data
                if 'threat' in entry.title.lower() or 'malware' in entry.title.lower():
                    indicator = ThreatIndicator(
                        id=f"feed_{self.source.value}_{hashlib.md5(entry.title.encode('utf-8')).hexdigest()[:8]}",
                        indicator_type="url",
                        indicator_value=entry.link,
                        threat_type=ThreatType.MALWARE,
                        threat_level=ThreatLevel.HIGH,
                        source=self.source,
                        confidence_score=0.7,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        tags=["open_source", "malware"],
                        description=entry.summary[:200] if len(entry.summary) > 200 else entry.summary,
                        related_indicators=[],
                        tlp_level="amber"
                    )
                    new_indicators.append(indicator)
            
            with self.lock:
                self.indicators.extend(new_indicators)
                self.last_updated = datetime.utcnow()
            
            logger.info(f"Updated open source feed with {len(new_indicators)} new indicators")
            return True
            
        except Exception as e:
            logger.error(f"Error updating open source feed: {e}")
            return False
    
    def _update_commercial_feed(self) -> bool:
        """Update from commercial threat intelligence feed"""
        # In a real implementation, this would connect to commercial TI platforms
        # For now, we'll simulate with mock data
        try:
            # Simulate API call to commercial feed
            # response = requests.get(self.feed_url, headers=headers)
            # data = response.json()
            
            # For demonstration, create mock indicators
            mock_indicators = []
            for i in range(5):
                indicator = ThreatIndicator(
                    id=f"commercial_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    indicator_type="ip",
                    indicator_value=f"192.168.1.{100+i}",
                    threat_type=ThreatType.RANSOMWARE,
                    threat_level=ThreatLevel.CRITICAL,
                    source=self.source,
                    confidence_score=0.9,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    tags=["commercial", "ransomware", "ioc"],
                    description=f"Commercial feed indicator {i}",
                    related_indicators=[],
                    tlp_level="red"
                )
                mock_indicators.append(indicator)
            
            with self.lock:
                self.indicators.extend(mock_indicators)
                self.last_updated = datetime.utcnow()
            
            logger.info(f"Updated commercial feed with {len(mock_indicators)} new indicators")
            return True
            
        except Exception as e:
            logger.error(f"Error updating commercial feed: {e}")
            return False
    
    def _update_vulnerability_db(self) -> bool:
        """Update from vulnerability databases"""
        # In a real implementation, this would connect to CVE databases
        try:
            # For demonstration, create mock vulnerability indicators
            mock_indicators = []
            for i in range(3):
                indicator = ThreatIndicator(
                    id=f"cve_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    indicator_type="cve",
                    indicator_value=f"CVE-2023-{1000+i:04d}",
                    threat_type=ThreatType.ZERO_DAY,
                    threat_level=ThreatLevel.HIGH,
                    source=self.source,
                    confidence_score=0.8,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    tags=["vulnerability", "cve", "exploit"],
                    description=f"Mock CVE indicator {i}",
                    related_indicators=[],
                    tlp_level="green"
                )
                mock_indicators.append(indicator)
            
            with self.lock:
                self.indicators.extend(mock_indicators)
                self.last_updated = datetime.utcnow()
            
            logger.info(f"Updated vulnerability DB with {len(mock_indicators)} new indicators")
            return True
            
        except Exception as e:
            logger.error(f"Error updating vulnerability DB: {e}")
            return False


class ThreatAnalyzer:
    """Analyzes threats and performs intelligence correlation"""
    
    def __init__(self):
        self.indicators = {}
        self.threats = {}
        self.intel_feeds = {}
        self.models = {}
        self.lock = threading.Lock()
        self.scaler = StandardScaler()
        
        # Initialize ML models
        self._initialize_models()
        
        logger.info("Threat analyzer initialized")
    
    def _initialize_models(self):
        """Initialize machine learning models for threat analysis"""
        try:
            # Isolation Forest for anomaly detection
            self.models['anomaly_detector'] = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # DBSCAN for clustering similar threats
            self.models['clusterer'] = DBSCAN(eps=0.5, min_samples=2)
            
            logger.info("ML models initialized for threat analysis")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
    
    def add_intel_feed(self, feed_url: str, source: IntelligenceSource) -> ThreatIntelligenceFeed:
        """Add a threat intelligence feed"""
        feed = ThreatIntelligenceFeed(feed_url, source)
        self.intel_feeds[feed_url] = feed
        logger.info(f"Added threat intelligence feed: {feed_url}")
        return feed
    
    def update_all_feeds(self):
        """Update all threat intelligence feeds"""
        for feed_url, feed in self.intel_feeds.items():
            success = feed.update_feed()
            if success:
                # Add new indicators to our main indicator store
                with self.lock:
                    for indicator in feed.indicators:
                        self.indicators[indicator.id] = indicator
    
    def add_internal_indicator(self, indicator_type: str, indicator_value: str, 
                             threat_type: ThreatType, threat_level: ThreatLevel,
                             confidence_score: float, description: str) -> str:
        """Add an internally discovered threat indicator"""
        indicator_id = f"internal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        indicator = ThreatIndicator(
            id=indicator_id,
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            threat_type=threat_type,
            threat_level=threat_level,
            source=IntelligenceSource.INTERNAL_EVENTS,
            confidence_score=confidence_score,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            tags=["internal", threat_type.value],
            description=description,
            related_indicators=[],
            tlp_level="amber"
        )
        
        with self.lock:
            self.indicators[indicator_id] = indicator
        
        logger.info(f"Added internal indicator: {indicator_id} - {indicator_value}")
        return indicator_id
    
    def analyze_network_traffic(self, traffic_data: List[Dict[str, Any]]) -> List[ThreatEvent]:
        """Analyze network traffic for potential threats"""
        detected_threats = []
        
        for packet in traffic_data:
            threat_event = self._analyze_packet(packet)
            if threat_event:
                detected_threats.append(threat_event)
        
        return detected_threats
    
    def _analyze_packet(self, packet: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Analyze a single network packet for threats"""
        try:
            # Check against known indicators
            source_ip = packet.get('src_ip', '0.0.0.0')
            dest_ip = packet.get('dst_ip', '0.0.0.0')
            dest_port = packet.get('dst_port', 0)
            
            # Check if source IP is in threat indicators
            threat_indicators = [
                ind for ind in self.indicators.values()
                if ind.indicator_type == 'ip' and ind.indicator_value == source_ip
            ]
            
            if threat_indicators:
                highest_confidence = max(ind.confidence_score for ind in threat_indicators)
                highest_level = max(ind.threat_level for ind in threat_indicators)
                
                return ThreatEvent(
                    id=f"threat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                    timestamp=datetime.utcnow(),
                    threat_type=threat_indicators[0].threat_type,
                    threat_level=highest_level,
                    source_ip=source_ip,
                    destination_ip=dest_ip,
                    source_port=packet.get('src_port', 0),
                    destination_port=dest_port,
                    protocol=packet.get('protocol', 'unknown'),
                    description=f"Traffic from known threat IP: {source_ip}",
                    confidence_score=highest_confidence,
                    related_indicators=[ind.id for ind in threat_indicators],
                    status="detected"
                )
            
            # Check for unusual patterns (simplified)
            if dest_port in [445, 139, 3389]:  # SMB, NetBIOS, RDP
                # Check if this is unusual for the source
                if self._is_unusual_connection(source_ip, dest_ip, dest_port):
                    return ThreatEvent(
                        id=f"anomaly_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
                        timestamp=datetime.utcnow(),
                        threat_type=ThreatType.PRIVILEGE_ESCALATION,
                        threat_level=ThreatLevel.MEDIUM,
                        source_ip=source_ip,
                        destination_ip=dest_ip,
                        source_port=packet.get('src_port', 0),
                        destination_port=dest_port,
                        protocol=packet.get('protocol', 'unknown'),
                        description=f"Unusual connection to sensitive port {dest_port} from {source_ip}",
                        confidence_score=0.6,
                        related_indicators=[],
                        status="detected"
                    )
        
        except Exception as e:
            logger.error(f"Error analyzing packet: {e}")
        
        return None
    
    def _is_unusual_connection(self, source_ip: str, dest_ip: str, dest_port: int) -> bool:
        """Check if a connection is unusual based on historical patterns"""
        # This is a simplified check - in reality, this would use ML models
        # to detect anomalies based on historical connection patterns
        sensitive_ports = [445, 139, 3389, 22, 23]  # SMB, NetBIOS, RDP, SSH, Telnet
        return dest_port in sensitive_ports
    
    def correlate_threats(self, events: List[ThreatEvent]) -> List[ThreatIntelligence]:
        """Correlate threat events to identify broader campaigns"""
        if not events:
            return []
        
        # Group events by related indicators and time proximity
        event_groups = defaultdict(list)
        
        for event in events:
            # Group by related indicators
            for indicator_id in event.related_indicators:
                event_groups[indicator_id].append(event)
            
            # If no related indicators, group by source IP
            if not event.related_indicators:
                event_groups[event.source_ip].append(event)
        
        correlated_threats = []
        
        for group_key, group_events in event_groups.items():
            if len(group_events) < 2:  # Only consider groups with multiple events
                continue
            
            # Determine the primary threat type and level
            threat_types = [event.threat_type for event in group_events]
            primary_threat_type = Counter(threat_types).most_common(1)[0][0]
            
            threat_levels = [event.threat_level for event in group_events]
            primary_threat_level = max(threat_levels, key=lambda x: list(ThreatLevel).index(x))
            
            # Calculate overall confidence
            avg_confidence = sum(event.confidence_score for event in group_events) / len(group_events)
            
            # Create correlated threat intelligence
            threat_intel = ThreatIntelligence(
                id=f"campaign_{group_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                threat_id=group_key,
                source=IntelligenceSource.INTERNAL_EVENTS,
                confidence=avg_confidence,
                severity=primary_threat_level,
                description=f"Correlated threat campaign involving {len(group_events)} events",
                indicators=[],
                affected_systems=list(set(event.destination_ip for event in group_events)),
                timeline={
                    'first_event': min(event.timestamp for event in group_events),
                    'last_event': max(event.timestamp for event in group_events)
                },
                recommendations=self._generate_recommendations(group_events),
                created_at=datetime.utcnow()
            )
            
            correlated_threats.append(threat_intel)
        
        return correlated_threats
    
    def _generate_recommendations(self, events: List[ThreatEvent]) -> List[str]:
        """Generate recommendations based on threat events"""
        recommendations = []
        
        # Check for common patterns
        if any(event.threat_type == ThreatType.MALWARE for event in events):
            recommendations.append("Quarantine affected systems and run antivirus scans")
        
        if any(event.threat_type == ThreatType.DDOS for event in events):
            recommendations.append("Implement rate limiting and DDoS protection measures")
        
        if any(event.threat_type == ThreatType.RANSOMWARE for event in events):
            recommendations.append("Isolate affected systems and verify backup integrity")
        
        if any(event.threat_type == ThreatType.PHISHING for event in events):
            recommendations.append("Implement email filtering and user awareness training")
        
        if len(events) > 5:  # Multiple events suggest coordinated attack
            recommendations.append("Review network segmentation and access controls")
        
        if not recommendations:
            recommendations.append("Monitor for similar activity and update threat indicators")
        
        return recommendations
    
    def predict_threat_trends(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict potential threat trends using historical data"""
        # This is a simplified prediction model
        # In a real system, this would use more sophisticated ML techniques
        
        predictions = {
            'period_days': days_ahead,
            'start_date': datetime.utcnow().isoformat(),
            'end_date': (datetime.utcnow() + timedelta(days=days_ahead)).isoformat(),
            'predicted_threat_types': {},
            'confidence': 0.7,  # Overall confidence in predictions
            'trending_threats': [],
            'recommended_actions': []
        }
        
        # Analyze current threat indicators to predict trends
        threat_type_counts = Counter(ind.threat_type for ind in self.indicators.values())
        
        # Predict which threat types might increase
        for threat_type, count in threat_type_counts.most_common(5):
            # Simple prediction: if there are many indicators of this type,
            # it might continue to be prevalent
            if count > 10:  # Arbitrary threshold
                predictions['predicted_threat_types'][threat_type.value] = {
                    'current_prevalence': count,
                    'predicted_increase': True,
                    'confidence': min(0.9, count / 20.0)  # Scale confidence with prevalence
                }
                predictions['trending_threats'].append(threat_type.value)
        
        # Generate recommended actions based on predictions
        if 'malware' in predictions['trending_threats']:
            predictions['recommended_actions'].append("Enhance endpoint protection and malware scanning")
        
        if 'phishing' in predictions['trending_threats']:
            predictions['recommended_actions'].append("Increase phishing awareness training")
        
        if 'ddos' in predictions['trending_threats']:
            predictions['recommended_actions'].append("Prepare DDoS mitigation strategies")
        
        return predictions
    
    def get_threat_intelligence_report(self) -> Dict[str, Any]:
        """Generate a comprehensive threat intelligence report"""
        current_time = datetime.utcnow()
        
        # Count indicators by type
        type_counts = Counter(ind.indicator_type for ind in self.indicators.values())
        
        # Count indicators by threat level
        level_counts = Counter(ind.threat_level for ind in self.indicators.values())
        
        # Count indicators by threat type
        threat_type_counts = Counter(ind.threat_type for ind in self.indicators.values())
        
        # Get most recent indicators
        recent_indicators = sorted(
            self.indicators.values(),
            key=lambda x: x.last_seen,
            reverse=True
        )[:10]
        
        # Get indicators by source
        source_counts = Counter(ind.source for ind in self.indicators.values())
        
        return {
            'report_generated': current_time.isoformat(),
            'total_indicators': len(self.indicators),
            'indicators_by_type': dict(type_counts),
            'indicators_by_level': dict(level_counts),
            'indicators_by_threat_type': dict(threat_type_counts),
            'indicators_by_source': dict(source_counts),
            'most_recent_indicators': [
                {
                    'id': ind.id,
                    'type': ind.indicator_type,
                    'value': ind.indicator_value,
                    'threat_type': ind.threat_type.value,
                    'level': ind.threat_level.value,
                    'confidence': ind.confidence_score,
                    'description': ind.description[:100] + "..." if len(ind.description) > 100 else ind.description
                } for ind in recent_indicators
            ],
            'threat_trends': self.predict_threat_trends(7)
        }


class ThreatHuntingEngine:
    """Advanced threat hunting capabilities"""
    
    def __init__(self, threat_analyzer: ThreatAnalyzer):
        self.analyzer = threat_analyzer
        self.hunting_queries = {}
        self.hunting_results = {}
        self.lock = threading.Lock()
    
    def define_hunting_query(self, query_id: str, name: str, description: str, 
                           query_logic: Callable[[Dict[str, Any]], bool]) -> str:
        """Define a threat hunting query"""
        self.hunting_queries[query_id] = {
            'name': name,
            'description': description,
            'logic': query_logic,
            'created_at': datetime.utcnow()
        }
        logger.info(f"Defined hunting query: {name}")
        return query_id
    
    def execute_hunt(self, query_id: str, data_source: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a threat hunting query"""
        if query_id not in self.hunting_queries:
            raise ValueError(f"Hunting query not found: {query_id}")
        
        query = self.hunting_queries[query_id]
        results = []
        
        for record in data_source:
            try:
                if query['logic'](record):
                    results.append({
                        'query_id': query_id,
                        'record': record,
                        'matched_at': datetime.utcnow().isoformat(),
                        'confidence': self._calculate_hunt_confidence(record)
                    })
            except Exception as e:
                logger.error(f"Error executing hunt query {query_id}: {e}")
        
        # Store results
        hunt_id = f"hunt_{query_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.hunting_results[hunt_id] = {
            'query_id': query_id,
            'results': results,
            'executed_at': datetime.utcnow(),
            'total_matches': len(results)
        }
        
        logger.info(f"Threat hunt completed: {len(results)} matches found")
        return results
    
    def _calculate_hunt_confidence(self, record: Dict[str, Any]) -> float:
        """Calculate confidence score for a hunt result"""
        # Simple confidence calculation based on various factors
        confidence = 0.5  # Base confidence
        
        # Increase confidence for certain indicators
        if record.get('severity', '').lower() in ['high', 'critical']:
            confidence += 0.3
        elif record.get('severity', '').lower() == 'medium':
            confidence += 0.1
        
        # Increase confidence if multiple IoCs present
        ioc_count = len([k for k, v in record.items() if 'ioc' in k.lower() or 'indicator' in k.lower()])
        confidence += min(0.2, ioc_count * 0.05)
        
        return min(1.0, confidence)
    
    def get_hunting_report(self) -> Dict[str, Any]:
        """Generate a threat hunting report"""
        return {
            'total_queries': len(self.hunting_queries),
            'total_hunts_executed': len(self.hunting_results),
            'recent_hunts': [
                {
                    'hunt_id': hunt_id,
                    'query_name': self.hunting_queries[result['query_id']]['name'],
                    'matches_found': result['total_matches'],
                    'executed_at': result['executed_at'].isoformat()
                }
                for hunt_id, result in list(self.hunting_results.items())[-10:]  # Last 10 hunts
            ],
            'active_queries': [
                {
                    'id': qid,
                    'name': query['name'],
                    'description': query['description'][:100] + "..." if len(query['description']) > 100 else query['description']
                }
                for qid, query in self.hunting_queries.items()
            ]
        }


class ThreatIntelligenceSystem:
    """Main threat intelligence system orchestrator"""
    
    def __init__(self, db_path: str = "./threat_intel.db"):
        self.analyzer = ThreatAnalyzer()
        self.hunting_engine = ThreatHuntingEngine(self.analyzer)
        self.db_path = db_path
        self.monitoring = False
        self.monitoring_thread = None
        
        # Initialize database
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_database()
        
        # Add default intelligence feeds
        self._add_default_feeds()
        
        logger.info("Threat Intelligence System initialized")
    
    def _init_database(self):
        """Initialize the threat intelligence database"""
        cursor = self.db_conn.cursor()
        
        # Create threat indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_indicators (
                id TEXT PRIMARY KEY,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                tags TEXT,
                description TEXT,
                related_indicators TEXT,
                tlp_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create threat events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                destination_ip TEXT NOT NULL,
                source_port INTEGER,
                destination_port INTEGER,
                protocol TEXT,
                description TEXT,
                confidence_score REAL NOT NULL,
                related_indicators TEXT,
                status TEXT NOT NULL,
                assigned_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create threat intelligence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_intelligence (
                id TEXT PRIMARY KEY,
                threat_id TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                affected_systems TEXT,
                timeline TEXT,
                recommendations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_value ON threat_indicators(indicator_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_type ON threat_indicators(indicator_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_level ON threat_indicators(threat_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_timestamp ON threat_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_source_ip ON threat_events(source_ip)")
        
        self.db_conn.commit()
        logger.info("Threat intelligence database initialized")
    
    def _add_default_feeds(self):
        """Add default threat intelligence feeds"""
        # Add some example feeds (these are illustrative - real feeds would have actual URLs)
        default_feeds = [
            ("https://feeds.example.com/malware", IntelligenceSource.OPEN_SOURCE),
            ("https://feeds.example.com/cyber_threats", IntelligenceSource.OPEN_SOURCE),
            ("https://vuln.example.com/api/cves", IntelligenceSource.VULNERABILITY_DB)
        ]
        
        for feed_url, source in default_feeds:
            self.analyzer.add_intel_feed(feed_url, source)
    
    def start_monitoring(self):
        """Start continuous threat monitoring"""
        if self.monitoring:
            logger.warning("Threat monitoring already running")
            return
        
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Threat monitoring started")
    
    def stop_monitoring(self):
        """Stop threat monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Threat monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Update threat intelligence feeds
                self.analyzer.update_all_feeds()
                
                # Perform periodic analysis
                self._perform_periodic_analysis()
                
                # Sleep before next iteration
                time.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _perform_periodic_analysis(self):
        """Perform periodic threat analysis"""
        # This would include:
        # Perform correlation analysis
        self._correlate_threat_events(detected_events)
        
        # Update threat intelligence database
        self._update_threat_database(detected_events)
        
        # Generate threat report
        return self._generate_threat_report(detected_events)
    
    def _correlate_threat_events(self, events: List[Dict[str, Any]]):
        """Correlate threat events to identify patterns"""
        if not events:
            return
        
        # Group events by source IP
        events_by_source = {}
        for event in events:
            source_ip = event.get('source_ip', 'unknown')
            if source_ip not in events_by_source:
                events_by_source[source_ip] = []
            events_by_source[source_ip].append(event)
        
        # Identify coordinated attacks (multiple events from same source)
        for source_ip, source_events in events_by_source.items():
            if len(source_events) > 3:
                logger.warning(f"Potential coordinated attack from {source_ip}: {len(source_events)} events")
    
    def _update_threat_database(self, events: List[Dict[str, Any]]):
        """Update threat intelligence database with new events"""
        cursor = self.db_conn.cursor()
        for event in events:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO threat_events
                    (id, timestamp, threat_type, threat_level, source_ip, destination_ip,
                     source_port, destination_port, protocol, description, confidence_score,
                     related_indicators, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('id', secrets.token_hex(16)),
                    event.get('timestamp', datetime.utcnow().isoformat()),
                    event.get('threat_type', 'unknown'),
                    event.get('threat_level', 'medium'),
                    event.get('source_ip'),
                    event.get('destination_ip'),
                    event.get('source_port'),
                    event.get('destination_port'),
                    event.get('protocol'),
                    event.get('description', ''),
                    event.get('confidence_score', 0.5),
                    json.dumps(event.get('related_indicators', [])),
                    'new'
                ))
            except Exception as e:
                logger.error(f"Failed to store threat event: {e}")
        
        self.db_conn.commit()
    
    def _generate_threat_report(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate threat intelligence report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_events': len(events),
            'events_by_type': self._count_by_field(events, 'threat_type'),
            'events_by_level': self._count_by_field(events, 'threat_level'),
            'top_sources': self._get_top_sources(events, limit=10),
            'recommendations': self._generate_recommendations(events)
        }
    
    def _count_by_field(self, events: List[Dict], field: str) -> Dict[str, int]:
        """Count events by a specific field"""
        counts = {}
        for event in events:
            value = event.get(field, 'unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _get_top_sources(self, events: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top threat sources"""
        source_counts = {}
        for event in events:
            source_ip = event.get('source_ip', 'unknown')
            source_counts[source_ip] = source_counts.get(source_ip, 0) + 1
        
        sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'ip': ip, 'count': count} for ip, count in sorted_sources[:limit]]
    
    def _generate_recommendations(self, events: List[Dict]) -> List[str]:
        """Generate security recommendations based on events"""
        recommendations = []
        
        # Check for high-severity events
        high_severity = sum(1 for e in events if e.get('threat_level') == 'critical')
        if high_severity > 0:
            recommendations.append(f"URGENT: {high_severity} critical threats detected - immediate action required")
        
        # Check for brute force patterns
        auth_events = sum(1 for e in events if e.get('threat_type') == 'brute_force')
        if auth_events > 5:
            recommendations.append("Multiple brute force attempts detected - consider IP blocking")
        
        return recommendations
    
    def analyze_network_traffic(self, traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network traffic for threats"""
        detected_events = self.analyzer.analyze_network_traffic(traffic_data)
        
        # Store events in database
        cursor = self.db_conn.cursor()
        for event in detected_events:
            cursor.execute("""
                INSERT INTO threat_events
                (id, timestamp, threat_type, threat_level, source_ip, destination_ip,
                 source_port, destination_port, protocol, description, confidence_score,
                 related_indicators, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.timestamp.isoformat(), event.threat_type.value,
                event.threat_level.value, event.source_ip, event.destination_ip,
                event.source_port, event.destination_port, event.protocol,
                event.description, event.confidence_score,
                json.dumps(event.related_indicators), event.status
            ))
        self.db_conn.commit()
        
        # Correlate events to find campaigns
        correlated_threats = self.analyzer.correlate_threats(detected_events)
        
        # Store correlated threats
        for threat in correlated_threats:
            cursor.execute("""
                INSERT INTO threat_intelligence
                (id, threat_id, source, confidence, severity, description, 
                 affected_systems, timeline, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                threat.id, threat.threat_id, threat.source.value, threat.confidence,
                threat.severity.value, threat.description,
                json.dumps(threat.affected_systems), json.dumps(threat.timeline),
                json.dumps(threat.recommendations)
            ))
        self.db_conn.commit()
        
        return {
            'events_detected': len(detected_events),
            'campaigns_identified': len(correlated_threats),
            'threats': [event.id for event in detected_events],
            'campaigns': [threat.id for threat in correlated_threats]
        }
    
    def add_internal_indicator(self, indicator_type: str, indicator_value: str,
                             threat_type: ThreatType, threat_level: ThreatLevel,
                             confidence_score: float, description: str) -> str:
        """Add an internally discovered threat indicator"""
        indicator_id = self.analyzer.add_internal_indicator(
            indicator_type, indicator_value, threat_type, threat_level,
            confidence_score, description
        )
        
        # Store in database
        indicator = self.analyzer.indicators[indicator_id]
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO threat_indicators
            (id, indicator_type, indicator_value, threat_type, threat_level,
             source, confidence_score, first_seen, last_seen, tags, description,
             related_indicators, tlp_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            indicator.id, indicator.indicator_type, indicator.indicator_value,
            indicator.threat_type.value, indicator.threat_level.value,
            indicator.source.value, indicator.confidence_score,
            indicator.first_seen.isoformat(), indicator.last_seen.isoformat(),
            json.dumps(indicator.tags), indicator.description,
            json.dumps(indicator.related_indicators), indicator.tlp_level
        ))
        self.db_conn.commit()
        
        return indicator_id
    
    def get_threat_report(self) -> Dict[str, Any]:
        """Get a comprehensive threat report"""
        intel_report = self.analyzer.get_threat_intelligence_report()
        
        # Get recent events from database
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT * FROM threat_events 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC LIMIT 50
        """)
        recent_events = cursor.fetchall()
        
        # Get recent intelligence
        cursor.execute("""
            SELECT * FROM threat_intelligence
            WHERE created_at > datetime('now', '-24 hours')
            ORDER BY created_at DESC LIMIT 20
        """)
        recent_intel = cursor.fetchall()
        
        return {
            **intel_report,
            'recent_events_count': len(recent_events),
            'recent_intelligence_count': len(recent_intel),
            'hunting_report': self.hunting_engine.get_hunting_report()
        }
    
    def define_custom_hunt(self, name: str, description: str, 
                          query_logic: Callable[[Dict[str, Any]], bool]) -> str:
        """Define a custom threat hunting query"""
        query_id = f"hunt_{name.lower().replace(' ', '_')}_{secrets.token_hex(4)}"
        return self.hunting_engine.define_hunting_query(
            query_id, name, description, query_logic
        )
    
    def execute_custom_hunt(self, query_id: str, data_source: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a custom threat hunting query"""
        return self.hunting_engine.execute_hunt(query_id, data_source)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics for the threat intelligence system"""
        cursor = self.db_conn.cursor()
        
        # Count records in each table
        cursor.execute("SELECT COUNT(*) FROM threat_indicators")
        indicator_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM threat_events")
        event_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM threat_intelligence")
        intel_count = cursor.fetchone()[0]
        
        return {
            'total_indicators': indicator_count,
            'total_events': event_count,
            'total_intelligence_reports': intel_count,
            'feeds_monitored': len(self.analyzer.intel_feeds),
            'active_hunting_queries': len(self.hunting_engine.hunting_queries),
            'monitoring_active': self.monitoring
        }


# Example hunting queries
def suspicious_port_scan(record: Dict[str, Any]) -> bool:
    """Hunting query to detect potential port scans"""
    # Look for multiple connections to different ports from same IP
    if record.get('event_type') == 'network_connection':
        dest_ports = record.get('destination_ports', [])
        source_ip = record.get('source_ip')
        if len(dest_ports) > 10 and len(set(dest_ports)) > 8:  # Many different ports
            return True
    return False


def lateral_movement_attempt(record: Dict[str, Any]) -> bool:
    """Hunting query to detect potential lateral movement"""
    # Look for authentication attempts from unusual locations
    if record.get('event_type') == 'authentication':
        source_ip = record.get('source_ip')
        target_host = record.get('target_host')
        time_of_day = record.get('timestamp', '').split('T')[1][:2]  # Hour
        
        # Unusual time or location
        if int(time_of_day) < 6 or int(time_of_day) > 22:  # Night time
            return True
    return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize threat intelligence system
    tis = ThreatIntelligenceSystem()
    
    print("🔍 Advanced Threat Intelligence System Initialized...")
    
    # Start monitoring
    tis.start_monitoring()
    
    # Add some internal indicators
    print("\nAdding internal threat indicators...")
    indicator1 = tis.add_internal_indicator(
        indicator_type="ip",
        indicator_value="10.0.0.100",
        threat_type=ThreatType.MALWARE,
        threat_level=ThreatLevel.HIGH,
        confidence_score=0.85,
        description="Internal system showing signs of compromise"
    )
    print(f"Added indicator: {indicator1}")
    
    indicator2 = tis.add_internal_indicator(
        indicator_type="domain",
        indicator_value="suspicious-domain.com",
        threat_type=ThreatType.PHISHING,
        threat_level=ThreatLevel.MEDIUM,
        confidence_score=0.75,
        description="Domain used in recent phishing campaign"
    )
    print(f"Added indicator: {indicator2}")
    
    # Define custom hunting queries
    print("\nDefining custom hunting queries...")
    hunt1_id = tis.define_custom_hunt(
        "Suspicious Port Scan",
        "Detect potential port scanning activity",
        suspicious_port_scan
    )
    print(f"Defined hunt: {hunt1_id}")
    
    hunt2_id = tis.define_custom_hunt(
        "Lateral Movement",
        "Detect potential lateral movement attempts",
        lateral_movement_attempt
    )
    print(f"Defined hunt: {hunt2_id}")
    
    # Simulate network traffic for analysis
    print("\nAnalyzing simulated network traffic...")
    sample_traffic = [
        {
            'src_ip': '192.168.1.100',  # This matches our first indicator
            'dst_ip': '10.0.0.50',
            'src_port': 12345,
            'dst_port': 445,
            'protocol': 'TCP',
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'src_ip': '8.8.8.8',
            'dst_ip': '10.0.0.60',
            'src_port': 53,
            'dst_port': 80,
            'protocol': 'UDP',
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'src_ip': '10.0.0.100',  # Another connection from compromised host
            'dst_ip': '10.0.0.70',
            'src_port': 45678,
            'dst_port': 3389,
            'protocol': 'TCP',
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    
    analysis_result = tis.analyze_network_traffic(sample_traffic)
    print(f"Analysis completed: {analysis_result['events_detected']} events detected, "
          f"{analysis_result['campaigns_identified']} campaigns identified")
    
    # Execute custom hunts
    print("\nExecuting custom threat hunts...")
    mock_data = [
        {
            'event_type': 'network_connection',
            'source_ip': '192.168.1.50',
            'destination_ports': [22, 23, 25, 80, 443, 445, 139, 3389, 5900, 8080, 9000, 9001]
        },
        {
            'event_type': 'authentication',
            'source_ip': '192.168.1.50',
            'target_host': 'server01',
            'timestamp': '2023-10-15T03:30:00'
        }
    ]
    
    hunt_results1 = tis.execute_custom_hunt(hunt1_id, mock_data)
    print(f"Port scan hunt results: {len(hunt_results1)} matches")
    
    hunt_results2 = tis.execute_custom_hunt(hunt2_id, mock_data)
    print(f"Lateral movement hunt results: {len(hunt_results2)} matches")
    
    # Get threat report
    print("\nGenerating threat report...")
    threat_report = tis.get_threat_report()
    print(f"Threat report generated with {threat_report['total_indicators']} indicators")
    print(f"Recent events: {threat_report['recent_events_count']}")
    print(f"Recent intelligence: {threat_report['recent_intelligence_count']}")
    
    # Get system metrics
    print("\nGetting system metrics...")
    metrics = tis.get_system_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Stop monitoring
    tis.stop_monitoring()
    
    print("\n✅ Advanced Threat Intelligence System Test Completed")