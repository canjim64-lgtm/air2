"""
Version Control Module
Version control for telemetry data
"""

import hashlib
import time
from typing import Dict, List


class Version:
    """Version info"""
    
    def __init__(self, version_id: str, data: dict):
        self.version_id = version_id
        self.timestamp = time.time()
        self.data = data
        self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Compute checksum"""
        data_str = str(self.data)
        return hashlib.md5(data_str.encode()).hexdigest()


class VersionControl:
    """Version control"""
    
    def __init__(self):
        self.versions = {}
    
    def commit(self, name: str, data: dict) -> str:
        """Commit version"""
        version_id = f"{name}_{int(time.time() * 1000)}"
        version = Version(version_id, data)
        self.versions[version_id] = version
        return version_id
    
    def get_version(self, version_id: str) -> Version:
        """Get version"""
        return self.versions.get(version_id)
    
    def list_versions(self, name: str) -> List[str]:
        """List versions"""
        return [v for v in self.versions if v.startswith(name)]
    
    def rollback(self, version_id: str) -> dict:
        """Rollback to version"""
        version = self.get_version(version_id)
        return version.data if version else {}


# Example
if __name__ == "__main__":
    vc = VersionControl()
    vc.commit("data", {"value": 42})
    print(vc.list_versions("data"))