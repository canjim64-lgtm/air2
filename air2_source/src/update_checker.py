"""
AirOne Professional v4.0 - Update Checker
Check for updates and notify users
"""
# -*- coding: utf-8 -*-

import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

logger = logging.getLogger(__name__)

# Current version
CURRENT_VERSION = {
    'major': 4,
    'minor': 0,
    'patch': 0,
    'build': '20260301',
    'release': 'Ultimate Unified Edition'
}

VERSION_STRING = f"{CURRENT_VERSION['major']}.{CURRENT_VERSION['minor']}.{CURRENT_VERSION['patch']}"


class UpdateChecker:
    """Check for application updates"""
    
    def __init__(self, config_file: str = "config/update_config.json"):
        self.config_file = Path(config_file)
        self.last_check_file = Path("logs/last_update_check.json")
        self.update_available = False
        self.update_info: Optional[Dict[str, Any]] = None
        
        # Create config directory
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load update configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default config
        return {
            'auto_check': True,
            'check_interval_days': 7,
            'notify_prerelease': False,
            'current_version': VERSION_STRING,
            'last_check': None,
            'ignored_versions': []
        }
    
    def _save_config(self):
        """Save update configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save update config: {e}")
    
    def get_current_version(self) -> str:
        """Get current version string"""
        return VERSION_STRING
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get detailed version information"""
        return {
            'version': VERSION_STRING,
            'full_version': f"v{VERSION_STRING} (build {CURRENT_VERSION['build']})",
            'release_name': CURRENT_VERSION['release'],
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'check_date': datetime.now().isoformat()
        }
    
    def check_for_updates(self, force: bool = False) -> bool:
        """
        Check if updates are available
        
        Args:
            force: Force check even if recently checked
            
        Returns:
            True if update available, False otherwise
        """
        # Check if we should check for updates
        if not force and not self._should_check():
            return False
        
        # In a real implementation, this would check a remote server
        # For now, we'll simulate with local version file
        update_info = self._check_local_version()
        
        # Update last check time
        self.config['last_check'] = datetime.now().isoformat()
        self._save_config()
        
        if update_info:
            self.update_available = True
            self.update_info = update_info
            return True
        
        return False
    
    def _should_check(self) -> bool:
        """Check if enough time has passed since last check"""
        if not self.config.get('auto_check', True):
            return False
        
        last_check = self.config.get('last_check')
        if not last_check:
            return True
        
        try:
            last_check_date = datetime.fromisoformat(last_check)
            check_interval = timedelta(days=self.config.get('check_interval_days', 7))
            return datetime.now() > last_check_date + check_interval
        except:
            return True
    
    def _check_local_version(self) -> Optional[Dict[str, Any]]:
        """Check local version file for updates"""
        version_file = Path("VERSION.json")
        
        if not version_file.exists():
            return None
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                remote_version = json.load(f)
            
            # Compare versions
            if self._is_newer(remote_version.get('version', '0.0.0')):
                return {
                    'version': remote_version.get('version'),
                    'release_date': remote_version.get('release_date'),
                    'changes': remote_version.get('changes', []),
                    'download_url': remote_version.get('download_url'),
                    'critical': remote_version.get('critical', False)
                }
        except Exception as e:
            logger.error(f"Error checking local version: {e}")
        
        return None
    
    def _is_newer(self, remote_version: str) -> bool:
        """Check if remote version is newer than current"""
        try:
            # Ignore versions in ignored list
            if remote_version in self.config.get('ignored_versions', []):
                return False
            
            # Simple version comparison
            remote_parts = [int(x) for x in remote_version.split('.')]
            current_parts = [
                CURRENT_VERSION['major'],
                CURRENT_VERSION['minor'],
                CURRENT_VERSION['patch']
            ]
            
            for remote, current in zip(remote_parts, current_parts):
                if remote > current:
                    return True
                elif remote < current:
                    return False
            
            return False
        except:
            return False
    
    def ignore_version(self, version: str):
        """Ignore a specific version"""
        if 'ignored_versions' not in self.config:
            self.config['ignored_versions'] = []
        
        if version not in self.config['ignored_versions']:
            self.config['ignored_versions'].append(version)
            self._save_config()
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get update status information"""
        return {
            'current_version': self.get_version_info(),
            'update_available': self.update_available,
            'update_info': self.update_info,
            'auto_check_enabled': self.config.get('auto_check', True),
            'last_check': self.config.get('last_check'),
            'next_check': self._get_next_check_time()
        }
    
    def _get_next_check_time(self) -> Optional[str]:
        """Get next scheduled check time"""
        last_check = self.config.get('last_check')
        if not last_check:
            return None
        
        try:
            last_check_date = datetime.fromisoformat(last_check)
            next_check = last_check_date + timedelta(days=self.config.get('check_interval_days', 7))
            return next_check.isoformat()
        except:
            return None
    
    def set_auto_check(self, enabled: bool):
        """Enable or disable auto check"""
        self.config['auto_check'] = enabled
        self._save_config()
    
    def set_check_interval(self, days: int):
        """Set check interval in days"""
        self.config['check_interval_days'] = max(1, min(30, days))
        self._save_config()


class ChangelogViewer:
    """View application changelog"""
    
    def __init__(self, changelog_file: str = "CHANGELOG.md"):
        self.changelog_file = Path(changelog_file)
        
    def get_changelog(self) -> str:
        """Get full changelog"""
        if not self.changelog_file.exists():
            return self._get_default_changelog()
        
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return self._get_default_changelog()
    
    def get_latest_changes(self, limit: int = 10) -> List[str]:
        """Get latest changes"""
        changelog = self.get_changelog()
        lines = changelog.split('\n')
        
        changes = []
        for line in lines:
            if line.startswith('- ') or line.startswith('* '):
                changes.append(line[2:])
                if len(changes) >= limit:
                    break
        
        return changes if changes else [
            "Initial release",
            "Core system implementation",
            "GUI and CLI interfaces",
            "Web dashboard",
            "Error handling improvements"
        ]
    
    def _get_default_changelog(self) -> str:
        """Get default changelog"""
        return f"""
# AirOne Professional v4.0 - Changelog

## Version {VERSION_STRING} ({CURRENT_VERSION['release']})

### New Features
- Enhanced argument parser with 30+ options
- Modern GUI themes (9 total)
- Interactive launcher with menu system
- Web-based real-time dashboard
- Comprehensive system diagnostics
- Error handling and recovery system
- Quick launch scripts for common scenarios

### Improvements
- UTF-8 encoding support for Windows
- Better error messages and logging
- Improved startup time
- Enhanced configuration system

### Bug Fixes
- Fixed Unicode encoding issues on Windows
- Fixed import error handling
- Fixed diagnostics crash on missing dependencies

### Technical
- Python 3.12 compatibility
- Improved dependency management
- Better module organization
"""


def check_updates() -> Dict[str, Any]:
    """Quick function to check for updates"""
    checker = UpdateChecker()
    checker.check_for_updates()
    return checker.get_update_status()


def get_version() -> str:
    """Get current version string"""
    return VERSION_STRING


def get_changelog() -> str:
    """Get changelog"""
    return ChangelogViewer().get_changelog()


if __name__ == "__main__":
    # Test update checker
    checker = UpdateChecker()
    
    print("="*60)
    print("AirOne Professional v4.0 - Update Checker")
    print("="*60)
    print()
    
    # Show current version
    print("Current Version:")
    version_info = checker.get_version_info()
    for key, value in version_info.items():
        print(f"  {key}: {value}")
    
    print()
    
    # Check for updates
    print("Checking for updates...")
    if checker.check_for_updates(force=True):
        print(f"\n[UPDATE] Update available!")
        print(f"   Version: {checker.update_info['version']}")
        print(f"   Download: {checker.update_info.get('download_url', 'N/A')}")
    else:
        print("\n[OK] You have the latest version")
    
    print()
    print("Update Status:")
    status = checker.get_update_status()
    print(f"  Auto-check: {status['auto_check_enabled']}")
    print(f"  Last check: {status['last_check'] or 'Never'}")
    print(f"  Next check: {status['next_check'] or 'Not scheduled'}")
