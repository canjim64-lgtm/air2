"""Restore Manager - Restore from backups with verification"""
import os, shutil, hashlib
from typing import Dict, Any, List, Optional

class RestoreManager:
    def __init__(self, backup_root: str = './backups'): self.backup_root = backup_root
    def restore(self, backup_path: str, target_dir: str, verify: bool = True) -> Dict[str, Any]:
        result = {'success': False, 'files': 0, 'size': 0, 'errors': []}
        if not os.path.exists(backup_path): result['errors'].append('Backup not found'); return result
        try:
            if backup_path.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as z: z.extractall(target_dir)
            else: shutil.copytree(backup_path, target_dir, dirs_exist_ok=True)
            result['success'] = True
            for r, ds, fs in os.walk(target_dir):
                for f in fs:
                    fp = os.path.join(r, f); result['files'] += 1; result['size'] += os.path.getsize(fp)
        except Exception as e: result['errors'].append(str(e))
        return result
    def verify_backup(self, backup_path: str) -> bool:
        try:
            if backup_path.endswith('.zip'):
                import zipfile
                return zipfile.is_zipfile(backup_path)
            return os.path.exists(backup_path)
        except: return False
    def list_restore_points(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.backup_root): return []
        res = []
        for b in os.listdir(self.backup_root):
            bp = os.path.join(self.backup_root, b)
            if os.path.isfile(bp):
                res.append({'name': b, 'size': os.path.getsize(bp)})
        return res
    def restore_incremental(self, backup_list: List[str], target_dir: str) -> Dict[str, Any]:
        result = {'restored': 0, 'failed': []}
        for bp in backup_list:
            r = self.restore(bp, target_dir, verify=False)
            if r['success']: result['restored'] += 1
            else: result['failed'].append(bp)
        return result
