"""
Comprehensive Compliance and Audit System for AirOne Professional
Implements regulatory compliance, audit trails, and governance frameworks
"""

import json
import csv
import sqlite3
import hashlib
import hmac
import secrets
import time
import asyncio
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import re
from functools import wraps
import inspect
from pathlib import Path
import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import uuid


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Regulatory compliance frameworks"""
    ISO_27001 = "ISO/IEC 27001"
    SOC_2 = "SOC 2"
    GDPR = "General Data Protection Regulation"
    HIPAA = "Health Insurance Portability and Accountability Act"
    PCI_DSS = "Payment Card Industry Data Security Standard"
    SOX = "Sarbanes-Oxley Act"
    NIST_CSF = "NIST Cybersecurity Framework"
    CCPA = "California Consumer Privacy Act"


class AuditEventType(Enum):
    """Types of audit events"""
    ACCESS = "access"
    MODIFICATION = "modification"
    DELETION = "deletion"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION_CHANGE = "configuration_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    SYSTEM_EVENT = "system_event"
    SECURITY_INCIDENT = "security_incident"


class ComplianceStatus(Enum):
    """Compliance status values"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non-compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPT = "exempt"
    UNDER_REVIEW = "under_review"


@dataclass
class AuditEvent:
    """Represents an auditable event"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    action: str
    resource: str
    source_ip: str
    user_agent: str
    success: bool
    details: Dict[str, Any]
    compliance_frameworks: List[ComplianceFramework]
    session_id: str


@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement"""
    id: str
    framework: ComplianceFramework
    requirement_id: str
    description: str
    category: str
    criticality: str  # critical, high, medium, low
    implementation_status: ComplianceStatus
    evidence_path: str
    last_reviewed: datetime
    next_review_due: datetime
    controls: List[str]


@dataclass
class AuditFinding:
    """Represents an audit finding"""
    id: str
    audit_id: str
    finding_type: str
    severity: str  # critical, high, medium, low
    description: str
    evidence: str
    remediation_required: bool
    remediation_plan: str
    status: str  # open, in_progress, closed
    assigned_to: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


class ComplianceManager:
    """Manages compliance requirements and frameworks"""
    
    def __init__(self, db_path: str = "./compliance.db"):
        self.db_path = db_path
        self.requirements = {}
        self.framework_standards = {}
        self.compliance_status = {}
        self.lock = threading.Lock()
        
        # Initialize database
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_database()
        
        # Load standard frameworks
        self._load_standard_frameworks()
        
        logger.info(f"Compliance manager initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize the compliance database"""
        cursor = self.db_conn.cursor()
        
        # Create compliance requirements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_requirements (
                id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                requirement_id TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                criticality TEXT,
                implementation_status TEXT,
                evidence_path TEXT,
                last_reviewed TEXT,
                next_review_due TEXT,
                controls TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create compliance assessments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_assessments (
                id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                assessment_date TEXT NOT NULL,
                assessor TEXT NOT NULL,
                status TEXT NOT NULL,
                findings_count INTEGER,
                compliant_items INTEGER,
                non_compliant_items INTEGER,
                evidence_path TEXT,
                notes TEXT
            )
        """)
        
        # Create compliance evidence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_evidence (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                evidence_path TEXT NOT NULL,
                description TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requirement_id) REFERENCES compliance_requirements(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_req_framework ON compliance_requirements(framework)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_req_status ON compliance_requirements(implementation_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_framework ON compliance_assessments(framework)")
        
        self.db_conn.commit()
        logger.info("Compliance database initialized")
    
    def _load_standard_frameworks(self):
        """Load standard compliance frameworks"""
        # ISO 27001 controls
        iso_27001_controls = {
            "A.5.1": "Policies for information security",
            "A.5.2": "Information security roles and responsibilities",
            "A.5.3": "Segregation of duties",
            "A.6.1": "Internal organization",
            "A.6.2": "Mobile devices and teleworking",
            "A.7.1": "Prior to employment",
            "A.7.2": "During employment",
            "A.7.3": "Termination and change of employment",
            "A.8.1": "Inventory of assets",
            "A.8.2": "Acceptable use of assets",
            "A.8.3": "Return of assets",
            "A.9.1": "Access control policy",
            "A.9.2": "User access management",
            "A.9.3": "Management of privileged access rights",
            "A.9.4": "Management of secret authentication information of users",
            "A.10.1": "Policy on the use of cryptographic controls",
            "A.11.1": "Secure areas",
            "A.11.2": "Equipment siting and protection",
            "A.12.1": "Controls against malware",
            "A.12.2": "Secure development policy",
            "A.12.3": "System change control procedures",
            "A.12.4": "Technical vulnerability management",
            "A.12.5": "Restrictions on system changes",
            "A.12.6": "Information backup",
            "A.12.7": "Network security management",
            "A.13.1": "Network security controls",
            "A.13.2": "Security of network services",
            "A.14.1": "Security requirements of information systems",
            "A.14.2": "Security in development and support processes",
            "A.14.3": "Test data",
            "A.15.1": "Protecting against malware",
            "A.15.2": "Information systems audit considerations",
            "A.16.1": "Management of information security incidents",
            "A.16.2": "Reporting information security events",
            "A.17.1": "Information security continuity",
            "A.17.2": "Redundancies",
            "A.18.1": "Identification of legal, statutory, regulatory and contractual requirements",
            "A.18.2": "Privacy and protection of personally identifiable information",
            "A.18.3": "Regulatory compliance"
        }
        
        # Add ISO 27001 requirements
        for req_id, description in iso_27001_controls.items():
            self.add_requirement(
                framework=ComplianceFramework.ISO_27001,
                requirement_id=req_id,
                description=description,
                category="Information Security Management",
                criticality="high"
            )
        
        # Add other framework requirements as needed
        logger.info("Standard compliance frameworks loaded")
    
    def add_requirement(self, framework: ComplianceFramework, requirement_id: str,
                       description: str, category: str, criticality: str = "medium",
                       implementation_status: ComplianceStatus = ComplianceStatus.PENDING_REVIEW,
                       evidence_path: str = "") -> str:
        """Add a compliance requirement"""
        req_id = f"{framework.value}_{requirement_id}".replace(" ", "_").replace("/", "_")
        
        requirement = ComplianceRequirement(
            id=req_id,
            framework=framework,
            requirement_id=requirement_id,
            description=description,
            category=category,
            criticality=criticality,
            implementation_status=implementation_status,
            evidence_path=evidence_path,
            last_reviewed=datetime.utcnow(),
            next_review_due=datetime.utcnow() + timedelta(days=365),
            controls=[]
        )
        
        with self.lock:
            self.requirements[req_id] = requirement
        
        # Store in database
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO compliance_requirements
            (id, framework, requirement_id, description, category, criticality, 
             implementation_status, evidence_path, last_reviewed, next_review_due, controls)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            requirement.id, requirement.framework.value, requirement.requirement_id,
            requirement.description, requirement.category, requirement.criticality,
            requirement.implementation_status.value, requirement.evidence_path,
            requirement.last_reviewed.isoformat(), requirement.next_review_due.isoformat(),
            json.dumps(requirement.controls)
        ))
        self.db_conn.commit()
        
        logger.info(f"Added compliance requirement: {req_id}")
        return req_id
    
    def assess_compliance(self, framework: ComplianceFramework, 
                         assessor: str, evidence_path: str = "",
                         notes: str = "") -> Dict[str, Any]:
        """Assess compliance against a framework"""
        # Get all requirements for the framework
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT id, implementation_status FROM compliance_requirements 
            WHERE framework = ?
        """, (framework.value,))
        
        requirements = cursor.fetchall()
        
        compliant_count = 0
        non_compliant_count = 0
        
        for req_id, status in requirements:
            if status == ComplianceStatus.COMPLIANT.value:
                compliant_count += 1
            else:
                non_compliant_count += 1
        
        assessment_id = f"assessment_{framework.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Store assessment
        cursor.execute("""
            INSERT INTO compliance_assessments
            (id, framework, assessment_date, assessor, status, findings_count,
             compliant_items, non_compliant_items, evidence_path, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id, framework.value, datetime.utcnow().isoformat(),
            assessor, 
            ComplianceStatus.COMPLIANT.value if non_compliant_count == 0 else ComplianceStatus.NON_COMPLIANT.value,
            non_compliant_count, compliant_count, non_compliant_count,
            evidence_path, notes
        ))
        self.db_conn.commit()
        
        return {
            'assessment_id': assessment_id,
            'framework': framework.value,
            'assessor': assessor,
            'assessment_date': datetime.utcnow().isoformat(),
            'status': ComplianceStatus.COMPLIANT.value if non_compliant_count == 0 else ComplianceStatus.NON_COMPLIANT.value,
            'total_requirements': len(requirements),
            'compliant_count': compliant_count,
            'non_compliant_count': non_compliant_count,
            'compliance_percentage': (compliant_count / len(requirements)) * 100 if requirements else 0
        }
    
    def get_compliance_status(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Get compliance status for a framework"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT implementation_status, COUNT(*) FROM compliance_requirements 
            WHERE framework = ? GROUP BY implementation_status
        """, (framework.value,))
        
        status_counts = dict(cursor.fetchall())
        
        total = sum(status_counts.values())
        compliant = status_counts.get(ComplianceStatus.COMPLIANT.value, 0)
        
        return {
            'framework': framework.value,
            'total_requirements': total,
            'status_breakdown': status_counts,
            'compliance_percentage': (compliant / total * 100) if total > 0 else 0,
            'last_assessment': self._get_last_assessment(framework)
        }
    
    def _get_last_assessment(self, framework: ComplianceFramework) -> Optional[Dict[str, Any]]:
        """Get the last assessment for a framework"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance_assessments 
            WHERE framework = ? ORDER BY assessment_date DESC LIMIT 1
        """, (framework.value,))
        
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def add_evidence(self, requirement_id: str, evidence_type: str, 
                     evidence_path: str, description: str, created_by: str) -> str:
        """Add compliance evidence for a requirement"""
        evidence_id = f"evidence_{requirement_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO compliance_evidence
            (id, requirement_id, evidence_type, evidence_path, description, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (evidence_id, requirement_id, evidence_type, evidence_path, description, created_by))
        self.db_conn.commit()
        
        logger.info(f"Added compliance evidence: {evidence_id} for requirement {requirement_id}")
        return evidence_id
    
    def generate_compliance_report(self, framework: ComplianceFramework) -> str:
        """Generate a compliance report for a framework"""
        status = self.get_compliance_status(framework)
        
        # Get detailed requirement status
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT requirement_id, description, implementation_status, category, criticality
            FROM compliance_requirements WHERE framework = ?
            ORDER BY category, criticality DESC
        """, (framework.value,))
        
        requirements = cursor.fetchall()
        
        report = f"""
# Compliance Report: {framework.value}

## Executive Summary
- Total Requirements: {status['total_requirements']}
- Compliance Percentage: {status['compliance_percentage']:.2f}%
- Status: {status['status_breakdown']}

## Detailed Requirements Status
"""
        
        for req_id, desc, status_val, category, criticality in requirements:
            report += f"\n### {req_id} ({criticality.upper()})"
            report += f"\n- Category: {category}"
            report += f"\n- Status: {status_val}"
            report += f"\n- Description: {desc[:100]}..."
        
        # Add last assessment info
        last_assessment = status.get('last_assessment')
        if last_assessment:
            report += f"\n\n## Last Assessment"
            report += f"\n- Date: {last_assessment['assessment_date']}"
            report += f"\n- Assessor: {last_assessment['assessor']}"
            report += f"\n- Status: {last_assessment['status']}"
        
        return report


class AuditManager:
    """Manages audit logging and event tracking"""
    
    def __init__(self, db_path: str = "./audit.db", retention_days: int = 365):
        self.db_path = db_path
        self.retention_days = retention_days
        self.lock = threading.Lock()
        self.event_queue = queue.Queue()
        
        # Initialize database
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_database()
        
        # Start audit processing thread
        self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processing_thread.start()
        
        logger.info(f"Audit manager initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize the audit database"""
        cursor = self.db_conn.cursor()
        
        # Create audit events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                source_ip TEXT,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                details TEXT,
                compliance_frameworks TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create audit findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_findings (
                id TEXT PRIMARY KEY,
                audit_id TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence TEXT,
                remediation_required BOOLEAN,
                remediation_plan TEXT,
                status TEXT NOT NULL,
                assigned_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource)")
        
        self.db_conn.commit()
        logger.info("Audit database initialized")
    
    def log_event(self, event_type: AuditEventType, user_id: str, action: str,
                  resource: str, source_ip: str, user_agent: str, success: bool,
                  details: Dict[str, Any], compliance_frameworks: List[ComplianceFramework],
                  session_id: str = "") -> str:
        """Log an audit event"""
        event_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        
        event = AuditEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource=resource,
            source_ip=source_ip,
            user_agent=user_agent,
            success=success,
            details=details,
            compliance_frameworks=compliance_frameworks,
            session_id=session_id
        )
        
        # Add to processing queue
        self.event_queue.put(event)
        
        logger.debug(f"Audit event queued: {event_id} - {event_type.value}")
        return event_id
    
    def _process_events(self):
        """Process audit events from the queue"""
        while True:
            try:
                event = self.event_queue.get(timeout=1)
                
                # Store in database
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_events
                    (id, timestamp, event_type, user_id, action, resource, 
                     source_ip, user_agent, success, details, compliance_frameworks, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.timestamp.isoformat(), event.event_type.value,
                    event.user_id, event.action, event.resource, event.source_ip,
                    event.user_agent, event.success, json.dumps(event.details),
                    json.dumps([f.value for f in event.compliance_frameworks]),
                    event.session_id
                ))
                self.db_conn.commit()
                
                # Check for compliance violations
                self._check_compliance_violations(event)
                
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audit event: {e}")
    
    def _check_compliance_violations(self, event: AuditEvent):
        """Check if an event violates compliance requirements"""
        # This is where we'd check against compliance rules
        # For example, checking if sensitive data was accessed without proper authorization
        violations = []
        
        # Example: Check for unauthorized access to sensitive resources
        sensitive_resources = ["/api/data/sensitive", "/config/secrets", "/users/personal"]
        if (event.event_type == AuditEventType.ACCESS and 
            any(res in event.resource for res in sensitive_resources) and 
            not event.success):
            violations.append({
                'type': 'unauthorized_access',
                'severity': 'high',
                'description': f'Unauthorized access attempt to sensitive resource: {event.resource}'
            })
        
        # Example: Check for configuration changes
        if (event.event_type == AuditEventType.CONFIGURATION_CHANGE and
            event.action == 'delete'):
            violations.append({
                'type': 'critical_config_change',
                'severity': 'medium',
                'description': f'Deletion of configuration: {event.resource}'
            })
        
        # Log violations as findings
        for violation in violations:
            self._create_finding(
                audit_id=event.id,
                finding_type=violation['type'],
                severity=violation['severity'],
                description=violation['description'],
                evidence=json.dumps(event.details),
                remediation_required=True,
                remediation_plan="Review access controls and implement additional safeguards",
                assigned_to=event.user_id
            )
    
    def _create_finding(self, audit_id: str, finding_type: str, severity: str,
                       description: str, evidence: str, remediation_required: bool,
                       remediation_plan: str, assigned_to: str) -> str:
        """Create an audit finding"""
        finding_id = f"finding_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(6)}"
        
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_findings
            (id, audit_id, finding_type, severity, description, evidence,
             remediation_required, remediation_plan, status, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_id, audit_id, finding_type, severity, description,
            evidence, remediation_required, remediation_plan, 'open', assigned_to
        ))
        self.db_conn.commit()
        
        logger.warning(f"Audit finding created: {finding_id} - {finding_type}")
        return finding_id
    
    def get_audit_events(self, start_date: datetime = None, end_date: datetime = None,
                        user_id: str = None, event_type: AuditEventType = None,
                        limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit events with filters"""
        cursor = self.db_conn.cursor()
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        events = []
        for row in rows:
            event_dict = dict(zip(columns, row))
            event_dict['details'] = json.loads(event_dict['details'])
            event_dict['compliance_frameworks'] = json.loads(event_dict['compliance_frameworks'])
            events.append(event_dict)
        
        return events
    
    def get_audit_findings(self, status: str = None, severity: str = None,
                          assigned_to: str = None) -> List[Dict[str, Any]]:
        """Retrieve audit findings with filters"""
        cursor = self.db_conn.cursor()
        
        query = "SELECT * FROM audit_findings WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        findings = []
        for row in rows:
            finding_dict = dict(zip(columns, row))
            findings.append(finding_dict)
        
        return findings
    
    def generate_audit_report(self, start_date: datetime, end_date: datetime,
                            event_types: List[AuditEventType] = None) -> str:
        """Generate an audit report"""
        # Get event counts by type
        cursor = self.db_conn.cursor()
        
        if event_types:
            type_placeholders = ','.join(['?' for _ in event_types])
            query = f"""
                SELECT event_type, COUNT(*) FROM audit_events 
                WHERE timestamp BETWEEN ? AND ? AND event_type IN ({type_placeholders})
                GROUP BY event_type
            """
            params = [start_date.isoformat(), end_date.isoformat()] + [et.value for et in event_types]
        else:
            query = """
                SELECT event_type, COUNT(*) FROM audit_events 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY event_type
            """
            params = [start_date.isoformat(), end_date.isoformat()]
        
        cursor.execute(query, params)
        event_counts = dict(cursor.fetchall())
        
        # Get top users
        cursor.execute("""
            SELECT user_id, COUNT(*) FROM audit_events 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 10
        """, (start_date.isoformat(), end_date.isoformat()))
        top_users = cursor.fetchall()
        
        # Get findings
        cursor.execute("""
            SELECT severity, COUNT(*) FROM audit_findings 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY severity
        """, (start_date.isoformat(), end_date.isoformat()))
        finding_counts = dict(cursor.fetchall())
        
        report = f"""
# Audit Report
Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}

## Event Summary
"""
        
        for event_type, count in event_counts.items():
            report += f"- {event_type}: {count}\n"
        
        report += f"\n## Top Users by Activity\n"
        for user_id, count in top_users:
            report += f"- {user_id}: {count} events\n"
        
        report += f"\n## Audit Findings\n"
        for severity, count in finding_counts.items():
            report += f"- {severity}: {count}\n"
        
        return report
    
    def cleanup_old_events(self):
        """Remove old audit events based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        cursor = self.db_conn.cursor()
        cursor.execute("""
            DELETE FROM audit_events WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        self.db_conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old audit events")


class GovernanceManager:
    """Manages governance policies and controls"""
    
    def __init__(self, compliance_manager: ComplianceManager, audit_manager: AuditManager):
        self.compliance_manager = compliance_manager
        self.audit_manager = audit_manager
        self.policies = {}
        self.controls = {}
        self.risk_assessments = {}
        self.lock = threading.Lock()
    
    def create_policy(self, policy_id: str, name: str, description: str,
                     framework: ComplianceFramework, requirements: List[str],
                     effective_date: datetime, review_frequency: int = 365) -> str:
        """Create a governance policy"""
        policy = {
            'id': policy_id,
            'name': name,
            'description': description,
            'framework': framework.value,
            'requirements': requirements,
            'effective_date': effective_date.isoformat(),
            'review_frequency_days': review_frequency,
            'next_review_date': (effective_date + timedelta(days=review_frequency)).isoformat(),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat()
        }
        
        with self.lock:
            self.policies[policy_id] = policy
        
        logger.info(f"Created governance policy: {policy_id}")
        return policy_id
    
    def create_control(self, control_id: str, name: str, description: str,
                      control_type: str, framework: ComplianceFramework,
                      policy_ids: List[str], implementation_guide: str) -> str:
        """Create a governance control"""
        control = {
            'id': control_id,
            'name': name,
            'description': description,
            'type': control_type,
            'framework': framework.value,
            'policies': policy_ids,
            'implementation_guide': implementation_guide,
            'status': 'implemented',
            'created_at': datetime.utcnow().isoformat()
        }
        
        with self.lock:
            self.controls[control_id] = control
        
        # Link control to requirements in compliance manager
        for req_id in policy_ids:  # Assuming policy IDs map to requirement IDs
            req = self.compliance_manager.requirements.get(req_id)
            if req:
                req.controls.append(control_id)
        
        logger.info(f"Created governance control: {control_id}")
        return control_id
    
    def conduct_risk_assessment(self, assessment_id: str, scope: str,
                               risk_factors: List[Dict[str, Any]],
                               methodology: str = "qualitative") -> Dict[str, Any]:
        """Conduct a risk assessment"""
        total_risk_score = 0
        risks = []
        
        for factor in risk_factors:
            likelihood = factor.get('likelihood', 0.5)  # 0-1 scale
            impact = factor.get('impact', 0.5)  # 0-1 scale
            risk_score = likelihood * impact
            
            risks.append({
                **factor,
                'risk_score': risk_score,
                'level': self._determine_risk_level(risk_score)
            })
            
            total_risk_score += risk_score
        
        assessment = {
            'id': assessment_id,
            'scope': scope,
            'methodology': methodology,
            'risks': risks,
            'total_risk_score': total_risk_score,
            'risk_level': self._determine_risk_level(total_risk_score / len(risks) if risks else 0),
            'recommendations': self._generate_recommendations(risks),
            'created_at': datetime.utcnow().isoformat()
        }
        
        with self.lock:
            self.risk_assessments[assessment_id] = assessment
        
        logger.info(f"Completed risk assessment: {assessment_id}")
        return assessment
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def _generate_recommendations(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on risks"""
        recommendations = []
        
        high_risks = [r for r in risks if r['risk_level'] in ['critical', 'high']]
        if high_risks:
            recommendations.append("Implement immediate mitigations for high-risk factors")
        
        medium_risks = [r for r in risks if r['risk_level'] == 'medium']
        if medium_risks:
            recommendations.append("Plan medium-term risk reduction initiatives")
        
        if not high_risks and not medium_risks:
            recommendations.append("Current risk posture is acceptable")
        
        return recommendations
    
    def get_governance_metrics(self) -> Dict[str, Any]:
        """Get governance-related metrics"""
        return {
            'total_policies': len(self.policies),
            'total_controls': len(self.controls),
            'total_risk_assessments': len(self.risk_assessments),
            'compliance_status': {
                framework.value: self.compliance_manager.get_compliance_status(framework)
                for framework in ComplianceFramework
            },
            'recent_audit_events': len(self.audit_manager.get_audit_events(
                start_date=datetime.utcnow() - timedelta(days=7), limit=100
            ))
        }


class ComplianceAndAuditSystem:
    """Main system that orchestrates compliance and audit functions"""
    
    def __init__(self, db_path: str = "./compliance_audit.db"):
        self.compliance_manager = ComplianceManager(db_path.replace(".db", "_compliance.db"))
        self.audit_manager = AuditManager(db_path.replace(".db", "_audit.db"))
        self.governance_manager = GovernanceManager(self.compliance_manager, self.audit_manager)
        
        logger.info("Compliance and Audit System initialized")
    
    def log_user_activity(self, user_id: str, action: str, resource: str,
                         success: bool, details: Dict[str, Any] = None) -> str:
        """Log user activity for audit and compliance"""
        if details is None:
            details = {}
        
        return self.audit_manager.log_event(
            event_type=AuditEventType.ACCESS if 'access' in action.lower() else AuditEventType.MODIFICATION,
            user_id=user_id,
            action=action,
            resource=resource,
            source_ip=details.get('source_ip', '127.0.0.1'),
            user_agent=details.get('user_agent', 'Unknown'),
            success=success,
            details=details,
            compliance_frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.GDPR],
            session_id=details.get('session_id', '')
        )
    
    def assess_framework_compliance(self, framework: ComplianceFramework, 
                                   assessor: str) -> Dict[str, Any]:
        """Assess compliance against a specific framework"""
        return self.compliance_manager.assess_compliance(framework, assessor)
    
    def generate_comprehensive_report(self, start_date: datetime, end_date: datetime) -> str:
        """Generate a comprehensive compliance and audit report"""
        compliance_report = self.compliance_manager.generate_compliance_report(ComplianceFramework.ISO_27001)
        audit_report = self.audit_manager.generate_audit_report(start_date, end_date)
        governance_metrics = self.governance_manager.get_governance_metrics()
        
        full_report = f"""
# Comprehensive Compliance and Audit Report
Generated: {datetime.utcnow().isoformat()}

## Compliance Status
{compliance_report}

## Audit Summary
{audit_report}

## Governance Metrics
{json.dumps(governance_metrics, indent=2)}

## Recommendations
1. Address any non-compliant requirements identified in the compliance assessment
2. Review and resolve open audit findings
3. Update governance policies as needed
4. Conduct regular risk assessments
        """
        
        return full_report
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        return {
            'compliance_metrics': self.compliance_manager.get_compliance_status(ComplianceFramework.ISO_27001),
            'audit_metrics': {
                'recent_events_count': len(self.audit_manager.get_audit_events(
                    start_date=datetime.utcnow() - timedelta(days=1), limit=10000
                )),
                'open_findings_count': len(self.audit_manager.get_audit_findings(status='open')),
                'total_events_count': self._get_total_audit_events()
            },
            'governance_metrics': self.governance_manager.get_governance_metrics()
        }
    
    def _get_total_audit_events(self) -> int:
        """Get total count of audit events"""
        cursor = self.audit_manager.db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_events")
        return cursor.fetchone()[0]


# Decorator for automatic compliance logging
def auditable(event_type: AuditEventType = AuditEventType.ACCESS, 
              compliance_frameworks: List[ComplianceFramework] = None):
    """Decorator to automatically log function calls for compliance and audit"""
    if compliance_frameworks is None:
        compliance_frameworks = [ComplianceFramework.ISO_27001]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the audit manager from the instance (assuming it's available)
            instance = args[0] if args else None
            audit_manager = getattr(instance, 'audit_manager', None) if instance else None
            
            if audit_manager:
                # Create audit event details
                func_name = func.__name__
                func_args = str(args[1:]) if len(args) > 1 else ""  # Exclude self
                func_kwargs = str(kwargs)
                
                # Log the event
                audit_manager.log_event(
                    event_type=event_type,
                    user_id=kwargs.get('user_id', 'system'),
                    action=f"function_call_{func_name}",
                    resource=f"{func.__module__}.{func.__qualname__}",
                    source_ip=kwargs.get('source_ip', '127.0.0.1'),
                    user_agent=kwargs.get('user_agent', 'Unknown'),
                    success=True,  # This will be updated if an exception occurs
                    details={
                        'function_args': func_args,
                        'function_kwargs': func_kwargs,
                        'module': func.__module__,
                        'class': args[0].__class__.__name__ if args else 'N/A'
                    },
                    compliance_frameworks=compliance_frameworks,
                    session_id=kwargs.get('session_id', '')
                )
            
            # Execute the original function
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Log failure if needed
                if audit_manager:
                    audit_manager.log_event(
                        event_type=event_type,
                        user_id=kwargs.get('user_id', 'system'),
                        action=f"function_call_{func_name}_failed",
                        resource=f"{func.__module__}.{func.__qualname__}",
                        source_ip=kwargs.get('source_ip', '127.0.0.1'),
                        user_agent=kwargs.get('user_agent', 'Unknown'),
                        success=False,
                        details={
                            'function_args': func_args,
                            'function_kwargs': func_kwargs,
                            'exception': str(e),
                            'traceback': str(e.__traceback__) if e.__traceback__ else None
                        },
                        compliance_frameworks=compliance_frameworks,
                        session_id=kwargs.get('session_id', '')
                    )
                raise
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    # Initialize the compliance and audit system
    cas = ComplianceAndAuditSystem()
    
    print("🏛️  Compliance and Audit System Initialized...")
    
    # Add a custom requirement
    req_id = cas.compliance_manager.add_requirement(
        framework=ComplianceFramework.GDPR,
        requirement_id="ARTICLE_5",
        description="Personal data shall be processed lawfully, fairly and in a transparent manner",
        category="Data Protection",
        criticality="critical"
    )
    print(f"Added GDPR requirement: {req_id}")
    
    # Log some user activities
    print("\nLogging user activities...")
    event1 = cas.log_user_activity(
        user_id="user_alice",
        action="access_data",
        resource="/api/users/profile",
        success=True,
        details={"source_ip": "192.168.1.100", "session_id": "sess_abc123"}
    )
    print(f"Logged event: {event1}")
    
    event2 = cas.log_user_activity(
        user_id="user_bob",
        action="modify_config",
        resource="/admin/settings",
        success=False,
        details={"source_ip": "192.168.1.101", "error": "insufficient_permissions"}
    )
    print(f"Logged event: {event2}")
    
    # Assess compliance
    print("\nAssessing ISO 27001 compliance...")
    assessment = cas.assess_framework_compliance(ComplianceFramework.ISO_27001, "auditor_jane")
    print(f"Assessment result: {assessment['status']} - {assessment['compliance_percentage']:.2f}% compliant")
    
    # Create a governance policy
    print("\nCreating governance policy...")
    policy_id = cas.governance_manager.create_policy(
        policy_id="data_retention_policy",
        name="Data Retention Policy",
        description="Policy for retaining user data according to regulations",
        framework=ComplianceFramework.GDPR,
        requirements=["ARTICLE_5", "ARTICLE_17"],  # Right to erasure
        effective_date=datetime.utcnow()
    )
    print(f"Created policy: {policy_id}")
    
    # Create a governance control
    control_id = cas.governance_manager.create_control(
        control_id="data_encryption_control",
        name="Data Encryption Control",
        description="Ensure all personal data is encrypted at rest",
        control_type="technical",
        framework=ComplianceFramework.ISO_27001,
        policy_ids=["data_retention_policy"],
        implementation_guide="Use AES-256 encryption for all stored data"
    )
    print(f"Created control: {control_id}")
    
    # Conduct a risk assessment
    print("\nConducting risk assessment...")
    risk_assessment = cas.governance_manager.conduct_risk_assessment(
        assessment_id="ra_q1_2026",
        scope="User data processing",
        risk_factors=[
            {
                "factor": "unauthorized_access",
                "likelihood": 0.3,
                "impact": 0.8,
                "mitigation": "access_controls"
            },
            {
                "factor": "data_breach",
                "likelihood": 0.1,
                "impact": 0.9,
                "mitigation": "encryption"
            }
        ]
    )
    print(f"Risk assessment completed with score: {risk_assessment['total_risk_score']:.2f}")
    
    # Get recent audit events
    print("\nRetrieving recent audit events...")
    recent_events = cas.audit_manager.get_audit_events(
        start_date=datetime.utcnow() - timedelta(hours=1),
        limit=10
    )
    print(f"Retrieved {len(recent_events)} recent events")
    
    # Get system metrics
    print("\nGetting system metrics...")
    metrics = cas.get_system_metrics()
    print(f"Total audit events: {metrics['audit_metrics']['total_events_count']}")
    print(f"Compliance percentage: {metrics['compliance_metrics']['compliance_percentage']:.2f}%")
    
    # Generate a comprehensive report
    print("\nGenerating comprehensive report...")
    report = cas.generate_comprehensive_report(
        start_date=datetime.utcnow() - timedelta(days=7),
        end_date=datetime.utcnow()
    )
    print(f"Report generated, length: {len(report)} characters")
    
    # Cleanup old events (though none should be old in this test)
    cas.audit_manager.cleanup_old_events()
    
    print("\n✅ Compliance and Audit System Test Completed")