"""
Disaster Recovery and Backup System for AirOne Professional
Implements comprehensive backup, recovery, and disaster recovery capabilities
"""

import os
import shutil
import json
import hashlib
import hmac
import tarfile
import zipfile
import gzip
import lzma
import asyncio
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import boto3
from botocore.exceptions import ClientError
import paramiko
from scp import SCPClient
import subprocess
import psutil
import secrets
import tempfile
import schedule
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import pickle
import zlib
from pathlib import Path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class RecoveryPointObjective(Enum):
    """Recovery Point Objectives"""
    HOUR = "hourly"
    DAY = "daily"
    WEEK = "weekly"
    MONTH = "monthly"


class RecoveryTimeObjective(Enum):
    """Recovery Time Objectives"""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


@dataclass
class BackupJob:
    """Represents a backup job"""
    id: str
    name: str
    source_paths: List[str]
    destination_path: str
    backup_type: BackupType
    compression: str  # 'gzip', 'xz', 'zip', 'none'
    encryption: bool
    retention_days: int
    scheduled_time: Optional[str]  # Cron-like format
    created_at: datetime
    last_run: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class RecoveryPlan:
    """Represents a disaster recovery plan"""
    id: str
    name: str
    description: str
    rpo: RecoveryPointObjective
    rto: RecoveryTimeObjective
    critical_systems: List[str]
    backup_sources: List[str]
    recovery_steps: List[Dict[str, Any]]
    created_at: datetime
    last_tested: Optional[datetime] = None


class BackupManager:
    """Manages backup operations"""
    
    def __init__(self, backup_base_path: str = "./backups", encryption_key: Optional[bytes] = None):
        self.backup_base_path = Path(backup_base_path)
        self.backup_base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.encryption_key)
        self.jobs = {}
        self.job_queue = queue.Queue()
        self.running_jobs = set()
        self.lock = threading.Lock()
        
        # Initialize database for backup records
        self.db_path = self.backup_base_path / "backup_records.db"
        self._init_database()
        
        logger.info(f"Backup manager initialized at {self.backup_base_path}")
    
    def _init_database(self):
        """Initialize the backup records database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_records (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                job_name TEXT NOT NULL,
                source_paths TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                compression TEXT NOT NULL,
                encryption_enabled BOOLEAN NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                checksum TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT NOT NULL,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                rpo TEXT NOT NULL,
                rto TEXT NOT NULL,
                critical_systems TEXT,
                backup_sources TEXT,
                recovery_steps TEXT,
                created_at TEXT NOT NULL,
                last_tested TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Backup database initialized")
    
    def create_backup_job(self, name: str, source_paths: List[str], destination_path: str,
                         backup_type: BackupType = BackupType.FULL,
                         compression: str = "gzip", encryption: bool = True,
                         retention_days: int = 30,
                         scheduled_time: Optional[str] = None) -> str:
        """Create a new backup job"""
        job_id = secrets.token_urlsafe(16)
        
        job = BackupJob(
            id=job_id,
            name=name,
            source_paths=source_paths,
            destination_path=destination_path,
            backup_type=backup_type,
            compression=compression,
            encryption=encryption,
            retention_days=retention_days,
            scheduled_time=scheduled_time,
            created_at=datetime.utcnow()
        )
        
        with self.lock:
            self.jobs[job_id] = job
        
        logger.info(f"Created backup job: {name} (ID: {job_id})")
        return job_id
    
    def start_backup_job(self, job_id: str) -> bool:
        """Start a backup job"""
        if job_id not in self.jobs:
            logger.error(f"Backup job {job_id} not found")
            return False
        
        job = self.jobs[job_id]
        
        # Update job status
        job.status = "running"
        job.last_run = datetime.utcnow()
        
        # Add to queue for processing
        self.job_queue.put(job_id)
        
        # Start backup in a separate thread
        thread = threading.Thread(target=self._execute_backup_job, args=(job_id,), daemon=True)
        thread.start()
        
        logger.info(f"Started backup job: {job.name}")
        return True
    
    def _execute_backup_job(self, job_id: str):
        """Execute a backup job"""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        self.running_jobs.add(job_id)
        
        try:
            # Prepare backup directory
            backup_dir = self.backup_base_path / "jobs" / job_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup archive
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_name = f"backup_{job.name}_{timestamp}"
            
            if job.compression == "gzip":
                archive_path = backup_dir / f"{archive_name}.tar.gz"
                self._create_tar_archive(job.source_paths, archive_path, compress=True)
            elif job.compression == "xz":
                archive_path = backup_dir / f"{archive_name}.tar.xz"
                self._create_tar_archive(job.source_paths, archive_path, compress=True, compression_format="xz")
            elif job.compression == "zip":
                archive_path = backup_dir / f"{archive_name}.zip"
                self._create_zip_archive(job.source_paths, archive_path)
            else:
                archive_path = backup_dir / f"{archive_name}.tar"
                self._create_tar_archive(job.source_paths, archive_path, compress=False)
            
            # Encrypt if required
            if job.encryption:
                encrypted_path = archive_path.with_suffix(archive_path.suffix + ".encrypted")
                self._encrypt_file(archive_path, encrypted_path)
                archive_path = encrypted_path
            
            # Calculate checksum
            checksum = self._calculate_checksum(archive_path)
            
            # Record backup in database
            self._record_backup(job, str(archive_path), checksum, "completed")
            
            job.status = "completed"
            logger.info(f"Backup job {job.name} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            logger.error(f"Backup job {job.name} failed: {str(e)}")
            
            # Record failure in database
            self._record_backup(job, "", "", "failed", str(e))
        
        finally:
            self.running_jobs.discard(job_id)
    
    def _create_tar_archive(self, source_paths: List[str], archive_path: Path, 
                           compress: bool = True, compression_format: str = "gz"):
        """Create a tar archive"""
        mode = "w:" + compression_format if compress else "w"
        
        with tarfile.open(archive_path, mode) as tar:
            for source_path in source_paths:
                source = Path(source_path)
                if source.exists():
                    tar.add(source, arcname=source.name)
    
    def _create_zip_archive(self, source_paths: List[str], archive_path: Path):
        """Create a zip archive"""
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for source_path in source_paths:
                source = Path(source_path)
                if source.is_file():
                    zipf.write(source, source.name)
                elif source.is_dir():
                    for root, dirs, files in os.walk(source):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(source.parent)
                            zipf.write(file_path, arcname)
    
    def _encrypt_file(self, input_path: Path, output_path: Path):
        """Encrypt a file using Fernet encryption"""
        with open(input_path, 'rb') as infile:
            data = infile.read()
        
        encrypted_data = self.fernet.encrypt(data)
        
        with open(output_path, 'wb') as outfile:
            outfile.write(encrypted_data)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _record_backup(self, job: BackupJob, file_path: str, checksum: str, 
                      status: str, error_message: str = ""):
        """Record backup in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO backup_records 
            (id, job_id, job_name, source_paths, destination_path, backup_type, 
             compression, encryption_enabled, file_path, checksum, start_time, 
             end_time, status, error_message, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            secrets.token_urlsafe(16), job.id, job.name, json.dumps(job.source_paths),
            job.destination_path, job.backup_type.value, job.compression,
            job.encryption, file_path, checksum, job.last_run.isoformat(),
            datetime.utcnow().isoformat(), status, error_message,
            os.path.getsize(file_path) if os.path.exists(file_path) else 0
        ))
        
        conn.commit()
        conn.close()
    
    def restore_backup(self, backup_file_path: str, restore_path: str, 
                      decryption_key: Optional[bytes] = None) -> bool:
        """Restore a backup to a specified location"""
        try:
            # Decrypt if necessary
            temp_path = backup_file_path
            if backup_file_path.endswith(".encrypted"):
                temp_path = tempfile.mktemp()
                key = decryption_key or self.encryption_key
                fernet = Fernet(key)
                
                with open(backup_file_path, 'rb') as encrypted_file:
                    encrypted_data = encrypted_file.read()
                
                decrypted_data = fernet.decrypt(encrypted_data)
                
                with open(temp_path, 'wb') as decrypted_file:
                    decrypted_file.write(decrypted_data)
            
            # Extract archive based on format
            if temp_path.endswith('.tar.gz'):
                with tarfile.open(temp_path, 'r:gz') as tar:
                    tar.extractall(path=restore_path)
            elif temp_path.endswith('.tar.xz'):
                with tarfile.open(temp_path, 'r:xz') as tar:
                    tar.extractall(path=restore_path)
            elif temp_path.endswith('.zip'):
                with zipfile.ZipFile(temp_path, 'r') as zipf:
                    zipf.extractall(path=restore_path)
            elif temp_path.endswith('.tar'):
                with tarfile.open(temp_path, 'r:') as tar:
                    tar.extractall(path=restore_path)
            else:
                logger.error(f"Unsupported archive format: {temp_path}")
                return False
            
            # Clean up temp file if created
            if temp_path != backup_file_path:
                os.unlink(temp_path)
            
            logger.info(f"Backup restored successfully to {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {str(e)}")
            return False
    
    def get_backup_history(self, job_id: Optional[str] = None, 
                          days: int = 30) -> List[Dict[str, Any]]:
        """Get backup history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM backup_records 
            WHERE start_time > datetime('now', '-{} days')
        """.format(days)
        
        if job_id:
            query += f" AND job_id = '{job_id}'"
        
        query += " ORDER BY start_time DESC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Convert rows to dictionaries
        records = []
        for row in rows:
            record = dict(zip(columns, row))
            record['source_paths'] = json.loads(record['source_paths'])
            records.append(record)
        
        conn.close()
        return records
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all jobs and their retention policies
        for job_id, job in self.jobs.items():
            cutoff_date = datetime.utcnow() - timedelta(days=job.retention_days)
            
            # Find backups to delete
            cursor.execute("""
                SELECT file_path FROM backup_records 
                WHERE job_id = ? AND start_time < ?
            """, (job_id, cutoff_date.isoformat()))
            
            files_to_delete = cursor.fetchall()
            
            # Delete files and records
            for (file_path,) in files_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        logger.info(f"Deleted old backup: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {file_path}: {e}")
            
            # Remove records from database
            cursor.execute("""
                DELETE FROM backup_records 
                WHERE job_id = ? AND start_time < ?
            """, (job_id, cutoff_date.isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info("Old backups cleanup completed")


class RecoveryManager:
    """Manages disaster recovery operations"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.plans = {}
        self.active_recovery = None
        self.lock = threading.Lock()
    
    def create_recovery_plan(self, name: str, description: str,
                           rpo: RecoveryPointObjective,
                           rto: RecoveryTimeObjective,
                           critical_systems: List[str],
                           backup_sources: List[str],
                           recovery_steps: List[Dict[str, Any]]) -> str:
        """Create a disaster recovery plan"""
        plan_id = secrets.token_urlsafe(16)
        
        plan = RecoveryPlan(
            id=plan_id,
            name=name,
            description=description,
            rpo=rpo,
            rto=rto,
            critical_systems=critical_systems,
            backup_sources=backup_sources,
            recovery_steps=recovery_steps,
            created_at=datetime.utcnow()
        )
        
        with self.lock:
            self.plans[plan_id] = plan
        
        # Also store in database
        self._store_recovery_plan(plan)
        
        logger.info(f"Created recovery plan: {name} (ID: {plan_id})")
        return plan_id
    
    def _store_recovery_plan(self, plan: RecoveryPlan):
        """Store recovery plan in database"""
        conn = sqlite3.connect(self.backup_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO recovery_plans
            (id, name, description, rpo, rto, critical_systems, backup_sources, recovery_steps, created_at, last_tested)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan.id, plan.name, plan.description, plan.rpo.value, plan.rto.value,
            json.dumps(plan.critical_systems), json.dumps(plan.backup_sources),
            json.dumps(plan.recovery_steps), plan.created_at.isoformat(),
            plan.last_tested.isoformat() if plan.last_tested else None
        ))
        
        conn.commit()
        conn.close()
    
    def execute_recovery_plan(self, plan_id: str, target_path: str) -> bool:
        """Execute a disaster recovery plan"""
        if plan_id not in self.plans:
            logger.error(f"Recovery plan {plan_id} not found")
            return False
        
        plan = self.plans[plan_id]
        self.active_recovery = plan_id
        
        try:
            logger.info(f"Starting recovery plan: {plan.name}")
            
            # Execute each recovery step
            for step in plan.recovery_steps:
                step_type = step.get('type')
                step_params = step.get('params', {})
                
                if step_type == 'restore_backup':
                    backup_source = step_params.get('backup_source')
                    restore_path = step_params.get('restore_path', target_path)
                    
                    # Find the most recent backup for this source
                    history = self.backup_manager.get_backup_history(days=7)
                    recent_backup = None
                    for record in history:
                        if backup_source in record['source_paths']:
                            recent_backup = record
                            break
                    
                    if recent_backup:
                        success = self.backup_manager.restore_backup(
                            recent_backup['file_path'], 
                            restore_path
                        )
                        if not success:
                            logger.error(f"Failed to restore backup: {recent_backup['file_path']}")
                            return False
                    else:
                        logger.error(f"No recent backup found for source: {backup_source}")
                        return False
                
                elif step_type == 'run_script':
                    script_path = step_params.get('script_path')
                    self._run_recovery_script(script_path)
                
                elif step_type == 'restart_service':
                    service_name = step_params.get('service_name')
                    self._restart_service(service_name)
                
                # Add more step types as needed
            
            logger.info(f"Recovery plan {plan.name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Recovery plan {plan.name} failed: {str(e)}")
            return False
        
        finally:
            self.active_recovery = None
    
    def _run_recovery_script(self, script_path: str):
        """Run a recovery script"""
        try:
            result = subprocess.run(['python', script_path], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Recovery script failed: {result.stderr}")
            else:
                logger.info(f"Recovery script completed: {result.stdout}")
        except subprocess.TimeoutExpired:
            logger.error("Recovery script timed out")
        except Exception as e:
            logger.error(f"Error running recovery script: {e}")
    
    def _restart_service(self, service_name: str):
        """Restart a system service"""
        try:
            # This is a simplified example - actual implementation would depend on the OS
            if os.name == 'nt':  # Windows
                subprocess.run(['sc', 'start', service_name], check=True)
            else:  # Unix-like
                subprocess.run(['sudo', 'systemctl', 'start', service_name], check=True)
            logger.info(f"Restarted service: {service_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
    
    def test_recovery_plan(self, plan_id: str, test_target: str) -> Dict[str, Any]:
        """Test a recovery plan without affecting production"""
        if plan_id not in self.plans:
            logger.error(f"Recovery plan {plan_id} not found")
            return {"success": False, "error": "Plan not found"}
        
        plan = self.plans[plan_id]
        
        start_time = datetime.utcnow()
        try:
            # Execute test recovery
            success = self.execute_recovery_plan(plan_id, test_target)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Update last tested time
            plan.last_tested = datetime.utcnow()
            self._store_recovery_plan(plan)
            
            return {
                "success": success,
                "duration_seconds": duration,
                "rto_achieved": duration <= self._rto_to_seconds(plan.rto),
                "tested_at": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Recovery plan test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _rto_to_seconds(self, rto: RecoveryTimeObjective) -> int:
        """Convert RTO to seconds"""
        mapping = {
            RecoveryTimeObjective.MINUTES: 60,
            RecoveryTimeObjective.HOURS: 3600,
            RecoveryTimeObjective.DAYS: 86400
        }
        return mapping.get(rto, 3600)  # Default to 1 hour


class CloudBackupManager:
    """Manages cloud-based backups"""
    
    def __init__(self, provider: str = "aws", region: str = "us-east-1", 
                 access_key: str = None, secret_key: str = None):
        self.provider = provider
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = None
        self.bucket_name = None
        
        if provider == "aws":
            self.client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
    
    def configure_bucket(self, bucket_name: str):
        """Configure the cloud storage bucket"""
        self.bucket_name = bucket_name
        
        # Create bucket if it doesn't exist
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            # Bucket doesn't exist, create it
            if self.region == 'us-east-1':
                self.client.create_bucket(Bucket=bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"Created S3 bucket: {bucket_name}")
    
    def upload_backup(self, local_file_path: str, remote_key: str) -> bool:
        """Upload a backup file to cloud storage"""
        try:
            self.client.upload_file(local_file_path, self.bucket_name, remote_key)
            logger.info(f"Uploaded backup to cloud: {remote_key}")
            return True
        except ClientError as e:
            logger.error(f"Cloud upload failed: {e}")
            return False
    
    def download_backup(self, remote_key: str, local_file_path: str) -> bool:
        """Download a backup file from cloud storage"""
        try:
            self.client.download_file(self.bucket_name, remote_key, local_file_path)
            logger.info(f"Downloaded backup from cloud: {remote_key}")
            return True
        except ClientError as e:
            logger.error(f"Cloud download failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups in cloud storage"""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix="backups/")
            backups = []
            
            for obj in response.get('Contents', []):
                backups.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return backups
        except ClientError as e:
            logger.error(f"Failed to list cloud backups: {e}")
            return []


class DisasterRecoverySystem:
    """Main disaster recovery system orchestrator"""
    
    def __init__(self, backup_base_path: str = "./backups"):
        self.backup_manager = BackupManager(backup_base_path)
        self.recovery_manager = RecoveryManager(self.backup_manager)
        self.cloud_manager = None
        self.health_monitor = SystemHealthMonitor()
        self.auto_recovery_enabled = False
        self.recovery_thresholds = {}
        
        logger.info("Disaster recovery system initialized")
    
    def configure_cloud_backup(self, provider: str, region: str, access_key: str, secret_key: str, bucket_name: str):
        """Configure cloud backup storage"""
        self.cloud_manager = CloudBackupManager(provider, region, access_key, secret_key)
        self.cloud_manager.configure_bucket(bucket_name)
        logger.info("Cloud backup configured")
    
    def enable_auto_recovery(self, thresholds: Dict[str, Any]):
        """Enable automatic recovery based on system health"""
        self.auto_recovery_enabled = True
        self.recovery_thresholds = thresholds
        logger.info("Automatic recovery enabled")
    
    def schedule_regular_backups(self):
        """Schedule regular backup jobs"""
        # Example: Schedule daily full backup
        daily_job_id = self.backup_manager.create_backup_job(
            name="daily_full_backup",
            source_paths=["./data", "./config", "./logs"],
            destination_path="./backups/daily",
            backup_type=BackupType.FULL,
            compression="gzip",
            retention_days=30
        )
        
        # Schedule the job (in a real system, you'd use a proper scheduler)
        schedule.every().day.at("02:00").do(
            lambda: self.backup_manager.start_backup_job(daily_job_id)
        )
        
        logger.info("Daily backup scheduled")
    
    def monitor_system_health(self):
        """Monitor system health and trigger recovery if needed"""
        if not self.auto_recovery_enabled:
            return
        
        health_status = self.health_monitor.get_health_status()
        
        # Check if any threshold is crossed
        for component, status in health_status.items():
            if component in self.recovery_thresholds:
                threshold = self.recovery_thresholds[component]
                
                if self._is_below_threshold(status, threshold):
                    logger.warning(f"Health threshold crossed for {component}, initiating recovery...")
                    # Trigger recovery plan here
                    # self.execute_emergency_recovery()
    
    def _is_below_threshold(self, status: Dict[str, Any], threshold: Dict[str, Any]) -> bool:
        """Check if system status is below recovery threshold"""
        # Example implementation - would be more complex in reality
        if 'cpu_usage_percent' in status and 'max_cpu' in threshold:
            if status['cpu_usage_percent'] > threshold['max_cpu']:
                return True
        if 'memory_usage_percent' in status and 'max_memory' in threshold:
            if status['memory_usage_percent'] > threshold['max_memory']:
                return True
        if 'disk_usage_percent' in status and 'max_disk' in threshold:
            if status['disk_usage_percent'] > threshold['max_disk']:
                return True
        
        return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return {
            'backup_jobs': len(self.backup_manager.jobs),
            'running_backups': len(self.backup_manager.running_jobs),
            'recovery_plans': len(self.recovery_manager.plans),
            'active_recovery': self.recovery_manager.active_recovery,
            'cloud_configured': self.cloud_manager is not None,
            'auto_recovery_enabled': self.auto_recovery_enabled,
            'health_status': self.health_monitor.get_health_status()
        }


class SystemHealthMonitor:
    """Monitors system health for disaster recovery triggers"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.check_intervals = {
            'cpu': 5,      # seconds
            'memory': 5,
            'disk': 60,
            'network': 30,
            'processes': 60
        }
        self.last_checks = {}
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start health monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("System health monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check each component based on its interval
                now = time.time()
                
                for component, interval in self.check_intervals.items():
                    last_check = self.last_checks.get(component, 0)
                    if now - last_check >= interval:
                        self.last_checks[component] = now
                        # Perform check for this component
                        self._check_component(component)
                
                time.sleep(1)  # Check every second for interval management
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(5)
    
    def _check_component(self, component: str):
        """Check a specific system component"""
        if component == 'cpu':
            self._check_cpu()
        elif component == 'memory':
            self._check_memory()
        elif component == 'disk':
            self._check_disk()
        elif component == 'network':
            self._check_network()
        elif component == 'processes':
            self._check_processes()
    
    def _check_cpu(self):
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        logger.debug(f"CPU: {cpu_percent}% across {cpu_count} cores")
    
    def _check_memory(self):
        """Check memory usage"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        logger.debug(f"Memory: {memory.percent}% used, Swap: {swap.percent}% used")
    
    def _check_disk(self):
        """Check disk usage"""
        disk_usage = psutil.disk_usage('/')
        
        logger.debug(f"Disk: {disk_usage.percent}% used")
    
    def _check_network(self):
        """Check network status"""
        net_io = psutil.net_io_counters()
        
        logger.debug(f"Network: Sent {net_io.bytes_sent}, Received {net_io.bytes_recv}")
    
    def _check_processes(self):
        """Check process status"""
        processes = len(psutil.pids())
        load_avg = os.getloadavg() if os.name != 'nt' else (0, 0, 0)
        
        logger.debug(f"Processes: {processes}, Load Avg: {load_avg}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            'cpu_usage_percent': psutil.cpu_percent(interval=1),
            'memory_usage_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids()),
            'timestamp': datetime.utcnow().isoformat()
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize disaster recovery system
    dr_system = DisasterRecoverySystem(backup_base_path="./dr_backups")
    
    print("🚨 Disaster Recovery System Initialized...")
    
    # Create a backup job
    job_id = dr_system.backup_manager.create_backup_job(
        name="system_backup",
        source_paths=["./data", "./config"],
        destination_path="./backups",
        backup_type=BackupType.FULL,
        compression="gzip",
        encryption=True,
        retention_days=7
    )
    
    print(f"Created backup job: {job_id}")
    
    # Start the backup job
    dr_system.backup_manager.start_backup_job(job_id)
    
    # Wait for backup to complete
    import time
    time.sleep(5)
    
    # Create a recovery plan
    recovery_steps = [
        {
            'type': 'restore_backup',
            'params': {
                'backup_source': './data',
                'restore_path': './restored_data'
            }
        },
        {
            'type': 'restart_service',
            'params': {
                'service_name': 'airone_service'
            }
        }
    ]
    
    plan_id = dr_system.recovery_manager.create_recovery_plan(
        name="full_system_recovery",
        description="Complete system recovery plan",
        rpo=RecoveryPointObjective.DAY,
        rto=RecoveryTimeObjective.HOURS,
        critical_systems=["database", "web_server", "api"],
        backup_sources=["./data", "./config"],
        recovery_steps=recovery_steps
    )
    
    print(f"Created recovery plan: {plan_id}")
    
    # Test the recovery plan
    test_result = dr_system.recovery_manager.test_recovery_plan(
        plan_id, 
        "./test_recovery"
    )
    
    print(f"Recovery plan test result: {test_result}")
    
    # Get system metrics
    metrics = dr_system.get_system_metrics()
    print(f"System metrics: {json.dumps(metrics, indent=2, default=str)}")
    
    # Get backup history
    history = dr_system.backup_manager.get_backup_history()
    print(f"Backup history: {len(history)} records")
    
    # Cleanup old backups
    dr_system.backup_manager.cleanup_old_backups()
    
    print("\n✅ Disaster recovery system test completed")