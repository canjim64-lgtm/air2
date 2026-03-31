"""Version Manager - Version control for backups"""
import os, json, hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

class VersionManager:
    def __init__(self, version_root: str = './versions'): self.version_root = version_root; os.makedirs(version_root, exist_ok=True)
    def save_version(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path): return {'success': False}
        vdir = os.path.join(self.version_root, os.path.basename(file_path))
        os.makedirs(vdir, exist_ok=True)
        ver = len(os.listdir(vdir)) + 1
        vpath = os.path.join(vdir, f'v{ver}')
        import shutil; shutil.copy2(file_path, vpath)
        meta = {'version': ver, 'time': datetime.now().isoformat(), 'size': os.path.getsize(file_path)}
        if metadata: meta.update(metadata)
        with open(vpath + '.json', 'w') as f: json.dump(meta, f)
        return {'success': True, 'version': ver, 'path': vpath}
    def list_versions(self, file_name: str) -> List[Dict[str, Any]]:
        vdir = os.path.join(self.version_root, file_name)
        if not os.path.exists(vdir): return []
        res = []
        for f in sorted(os.listdir(vdir)):
            if f.endswith('.json'):
                with open(os.path.join(vdir, f)) as fp: res.append(json.load(fp))
        return res
    def restore_version(self, file_name: str, version: int, target: str) -> bool:
        vdir = os.path.join(self.version_root, file_name); vpath = os.path.join(vdir, f'v{version}')
        if not os.path.exists(vpath): return False
        import shutil; shutil.copy2(vpath, target); return True
    def get_latest(self, file_name: str) -> Optional[str]:
        vs = self.list_versions(file_name); return vs[-1]['path'] if vs else None
    def delete_old_versions(self, file_name: str, keep: int = 5) -> int:
        vs = self.list_versions(file_name)
        deleted = 0
        for v in vs[:-keep]:
            fp = os.path.join(self.version_root, file_name, f'v{v["version"]}')
            if os.path.exists(fp): os.remove(fp); deleted += 1
        return deleted
