"""Backup Manager - Automated backup scheduling and execution"""
import os, shutil, json, time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

class BackupManager:
    def __init__(self, backup_root: str = './backups'):
        self.backup_root = backup_root
        os.makedirs(backup_root, exist_ok=True)
        self.schedules = []
        self.history = []
    def create_backup(self, source_paths: List[str], name: str = None, compress: bool = True) -> Dict[str, Any]:
        if not name: name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        backup_path = os.path.join(self.backup_root, name)
        os.makedirs(backup_path, exist_ok=True)
        stats = {'files': 0, 'size': 0, 'failed': []}
        for sp in source_paths:
            if os.path.exists(sp):
                dp = os.path.join(backup_path, os.path.basename(sp))
                try:
                    if os.path.isdir(sp):
                        shutil.copytree(sp, dp)
                    else:
                        shutil.copy2(sp, dp)
                    stats['files'] += 1
                    stats['size'] += os.path.getsize(sp)
                except Exception as e: stats['failed'].append((sp, str(e)))
        if compress:
            shutil.make_archive(backup_path, 'zip', backup_path)
            shutil.rmtree(backup_path)
            backup_path += '.zip'
        self.history.append({'name': name, 'time': datetime.now().isoformat(), 'stats': stats})
        return {'name': name, 'path': backup_path, 'stats': stats}
    def restore_backup(self, backup_name: str, target_dir: str) -> bool:
        bp = os.path.join(self.backup_root, backup_name)
        if not os.path.exists(bp): return False
        try:
            if bp.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(bp, 'r') as z:
                    z.extractall(target_dir)
            else:
                shutil.copytree(bp, target_dir, dirs_exist_ok=True)
            return True
        except: return False
    def add_schedule(self, source: List[str], interval_hours: int, retention_days: int):
        self.schedules.append({'source': source, 'interval': interval_hours, 'retention': retention_days})
    def run_scheduled(self):
        for sched in self.schedules:
            self.create_backup(sched['source'])
    def list_backups(self) -> List[Dict[str, Any]]:
        res = []
        for b in os.listdir(self.backup_root):
            bp = os.path.join(self.backup_root, b)
            if os.path.isfile(bp):
                res.append({'name': b, 'size': os.path.getsize(bp), 'modified': os.path.getmtime(bp)})
        return res
    def delete_backup(self, name: str) -> bool:
        bp = os.path.join(self.backup_root, name)
        try:
            if os.path.isdir(bp): shutil.rmtree(bp)
            elif os.path.isfile(bp): os.remove(bp)
            return True
        except: return False
    def get_backup_info(self, name: str) -> Optional[Dict[str, Any]]:
        for h in self.history:
            if h['name'] == name: return h
        return None
