"""Cloud Sync - Real-time sync service"""
import time, threading, os
from typing import List, Callable

class CloudSync:
    def __init__(self, storage, watch_paths: List[str], remote_base: str):
        self.storage = storage
        self.watch_paths = watch_paths
        self.remote_base = remote_base
        self._running = False
        self._thread = None
        self.callbacks = []
        self.last_sync = {}
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
    def stop(self):
        self._running = False
        if self._thread: self._thread.join()
    def _sync_loop(self):
        while self._running:
            for p in self.watch_paths: self._sync_path(p)
            time.sleep(5)
    def _sync_path(self, local_path):
        if not os.path.exists(local_path): return
        for r, ds, fs in os.walk(local_path):
            for f in fs:
                fp = os.path.join(r, f); m = os.path.getmtime(fp)
                if self.last_sync.get(fp, 0) < m:
                    rp = f'{self.remote_base}/{os.path.relpath(fp, local_path)}'
                    if self.storage.upload_file(fp, rp):
                        self.last_sync[fp] = m
                        for cb in self.callbacks: cb('upload', fp, rp)
    def add_cb(self, cb: Callable): self.callbacks.append(cb)
    def force_sync(self):
        for p in self.watch_paths: self._sync_path(p)
