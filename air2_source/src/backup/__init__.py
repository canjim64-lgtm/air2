"""
Backup and Recovery Module
===========================
Provides automated backup, versioning, and disaster recovery.
"""
__version__ = "4.0.0"
from .backup_manager import BackupManager
from .restore import RestoreManager
from .versioning import VersionManager
__all__ = ['BackupManager', 'RestoreManager', 'VersionManager']
