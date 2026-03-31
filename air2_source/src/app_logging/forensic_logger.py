"""
Forensic Logger
Cryptographic log signing, tamper detection, and incident export
"""

import json
import logging
import hashlib
import hmac
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import zipfile
import io
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        if isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        return super(NumpyEncoder, self).default(obj)

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    module: str
    message: str
    context: Dict[str, Any]
    sequence: int
    hash_chain: str  # Hash of previous entry

class ForensicLogger:
    """
    Cryptographically signed logging with tamper detection.
    Supports timeline reconstruction and incident export.
    """
    
    def __init__(self, log_dir: Optional[Path] = None, secret_key: Optional[str] = None):
        self.log_dir = log_dir or Path.home() / ".airone" / "forensic_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Secret key for HMAC signing
        self.secret_key = secret_key or "airone_forensic_key_CHANGE_IN_PRODUCTION"
        
        # Current log file
        self.current_log_file = self.log_dir / f"forensic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Hash chain state
        self.last_hash = "0" * 64  # Genesis hash
        self.sequence_number = 0
        
        # Log buffer
        self.log_buffer: List[LogEntry] = []
        
        logger.info(f"ForensicLogger initialized: {self.current_log_file}")
    
    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC-SHA256 signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _compute_entry_hash(self, entry: LogEntry) -> str:
        """Compute hash of log entry for chain"""
        entry_data = f"{entry.timestamp}|{entry.level}|{entry.module}|{entry.message}|{entry.sequence}|{entry.hash_chain}"
        return hashlib.sha256(entry_data.encode('utf-8')).hexdigest()
    
    def log(self, level: str, module: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Log an entry with cryptographic signing.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            module: Module name
            message: Log message
            context: Additional context data
        """
        # Create entry
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            module=module,
            message=message,
            context=context or {},
            sequence=self.sequence_number,
            hash_chain=self.last_hash
        )
        
        # Compute hash for next entry
        current_hash = self._compute_entry_hash(entry)
        
        # Sign entry
        entry_dict = asdict(entry)
        entry_dict['signature'] = self._compute_hmac(json.dumps(entry_dict, sort_keys=True, cls=NumpyEncoder))
        entry_dict['current_hash'] = current_hash
        
        # Write to file (append-only)
        try:
            with open(self.current_log_file, 'a') as f:
                f.write(json.dumps(entry_dict, cls=NumpyEncoder) + '\n')
        except Exception as e:
            logger.error(f"Failed to write forensic log: {e}")
        
        # Update state
        self.last_hash = current_hash
        self.sequence_number += 1
        self.log_buffer.append(entry)
    
    def verify_integrity(self, log_file: Optional[Path] = None) -> bool:
        """
        Verify integrity of log file using hash chain.
        
        Args:
            log_file: Path to log file (default: current log)
        
        Returns:
            True if integrity verified
        """
        log_file = log_file or self.current_log_file
        
        if not log_file.exists():
            logger.error(f"Log file not found: {log_file}")
            return False
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            expected_hash = "0" * 64  # Genesis hash
            
            for i, line in enumerate(lines):
                entry_dict = json.loads(line)
                
                # Verify sequence
                if entry_dict['sequence'] != i:
                    logger.error(f"Sequence mismatch at line {i}: expected {i}, got {entry_dict['sequence']}")
                    return False
                
                # Verify hash chain
                if entry_dict['hash_chain'] != expected_hash:
                    logger.error(f"Hash chain broken at line {i}")
                    return False
                
                # Verify signature
                entry_copy = entry_dict.copy()
                signature = entry_copy.pop('signature')
                current_hash = entry_copy.pop('current_hash')
                
                expected_signature = self._compute_hmac(json.dumps(entry_copy, sort_keys=True, cls=NumpyEncoder))
                if signature != expected_signature:
                    logger.error(f"Signature mismatch at line {i}")
                    return False
                
                # Update expected hash
                expected_hash = current_hash
            
            logger.info(f"✅ Log integrity verified: {log_file} ({len(lines)} entries)")
            return True
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def reconstruct_timeline(self, start_time: Optional[str] = None, 
                           end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Reconstruct timeline of events.
        
        Args:
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
        
        Returns:
            List of log entries in chronological order
        """
        timeline = []
        
        # Read all log files
        for log_file in sorted(self.log_dir.glob("forensic_*.log")):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        
                        # Filter by time range
                        if start_time and entry['timestamp'] < start_time:
                            continue
                        if end_time and entry['timestamp'] > end_time:
                            continue
                        
                        timeline.append(entry)
            except Exception as e:
                logger.error(f"Failed to read {log_file}: {e}")
        
        # Sort by timestamp
        timeline.sort(key=lambda e: e['timestamp'])
        
        return timeline
    
    def export_incident_bundle(self, incident_id: str, 
                              start_time: str, 
                              end_time: str,
                              output_path: Optional[Path] = None) -> Path:
        """
        Export incident bundle as ZIP file.
        
        Args:
            incident_id: Incident identifier
            start_time: Start of incident window
            end_time: End of incident window
            output_path: Output ZIP path
        
        Returns:
            Path to created ZIP file
        """
        output_path = output_path or self.log_dir / f"incident_{incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Reconstruct timeline
        timeline = self.reconstruct_timeline(start_time, end_time)
        
        # Create ZIP bundle
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add timeline
            timeline_json = json.dumps(timeline, indent=2)
            zf.writestr('timeline.json', timeline_json)
            
            # Add metadata
            metadata = {
                'incident_id': incident_id,
                'start_time': start_time,
                'end_time': end_time,
                'export_time': datetime.now().isoformat(),
                'total_entries': len(timeline)
            }
            zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # Add all relevant log files
            for log_file in self.log_dir.glob("forensic_*.log"):
                zf.write(log_file, arcname=f"logs/{log_file.name}")
        
        logger.info(f"Incident bundle exported: {output_path} ({len(timeline)} entries)")
        return output_path


if __name__ == "__main__":
    # Test forensic logger
    logging.basicConfig(level=logging.INFO)
    
    fl = ForensicLogger()
    
    # Log some events
    fl.log("INFO", "system", "System started", {"version": "3.0.0"})
    fl.log("WARNING", "sensor", "Sensor drift detected", {"sensor": "temperature", "drift": 0.5})
    fl.log("ERROR", "communication", "Packet loss", {"lost_packets": 5})
    fl.log("CRITICAL", "security", "Authentication failure", {"attempts": 3})
    
    # Verify integrity
    is_valid = fl.verify_integrity()
    print(f"Log integrity: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # Reconstruct timeline
    timeline = fl.reconstruct_timeline()
    print(f"\nTimeline ({len(timeline)} entries):")
    for entry in timeline:
        print(f"  [{entry['level']}] {entry['module']}: {entry['message']}")
    
    # Export incident bundle
    bundle_path = fl.export_incident_bundle(
        incident_id="TEST001",
        start_time=timeline[0]['timestamp'],
        end_time=timeline[-1]['timestamp']
    )
    print(f"\nIncident bundle: {bundle_path}")
