#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Database and Data Management System
Complete database abstraction with support for multiple database backends
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import hashlib


class DatabaseManager:
    """Advanced database management system"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = Path(__file__).parent.parent / 'data' / 'database'
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / 'airone.db'
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._connect()
        self._initialize_tables()
    
    def _connect(self):
        """Connect to database"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        logging.info(f"Database connected: {self.db_path}")
    
    def _initialize_tables(self):
        """Initialize database tables"""
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT,
                created_at TEXT,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Telemetry data table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                altitude REAL,
                velocity REAL,
                temperature REAL,
                pressure REAL,
                battery_level REAL,
                signal_strength REAL,
                latitude REAL,
                longitude REAL,
                status TEXT,
                mode TEXT
            )
        ''')
        
        # Events table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT,
                source TEXT,
                message TEXT,
                data TEXT,
                acknowledged INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        # Configuration table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                type TEXT,
                updated_at TEXT,
                updated_by TEXT
            )
        ''')
        
        # Audit log table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT
            )
        ''')
        
        # Sessions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        self.connection.commit()
        logging.info("Database tables initialized")
    
    # User operations
    def create_user(self, username: str, password_hash: str, role: str, permissions: List[str] = None) -> int:
        """Create a new user"""
        self.cursor.execute('''
            INSERT INTO users (username, password_hash, role, permissions, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, role, json.dumps(permissions or []), datetime.utcnow().isoformat()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Update user information"""
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [username]
        self.cursor.execute(f'UPDATE users SET {set_clause} WHERE username = ?', values)
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        self.cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    # Telemetry operations
    def store_telemetry(self, data: Dict[str, Any]) -> int:
        """Store telemetry data"""
        self.cursor.execute('''
            INSERT INTO telemetry (timestamp, altitude, velocity, temperature, pressure,
                                  battery_level, signal_strength, latitude, longitude, status, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', datetime.utcnow().isoformat()),
            data.get('altitude'),
            data.get('velocity'),
            data.get('temperature'),
            data.get('pressure'),
            data.get('battery_level'),
            data.get('signal_strength'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('status'),
            data.get('mode')
        ))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_telemetry(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get telemetry data"""
        self.cursor.execute('''
            SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_telemetry_by_time(self, start_time: str, end_time: str) -> List[Dict]:
        """Get telemetry data within time range"""
        self.cursor.execute('''
            SELECT * FROM telemetry WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp
        ''', (start_time, end_time))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Event operations
    def create_event(self, event_type: str, severity: str, source: str, message: str, data: Dict = None) -> int:
        """Create a new event"""
        self.cursor.execute('''
            INSERT INTO events (timestamp, event_type, severity, source, message, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.utcnow().isoformat(), event_type, severity, source, message, json.dumps(data or {})))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_events(self, limit: int = 100, unacknowledged_only: bool = False) -> List[Dict]:
        """Get events"""
        query = 'SELECT * FROM events ORDER BY timestamp DESC LIMIT ?'
        if unacknowledged_only:
            query = 'SELECT * FROM events WHERE acknowledged = 0 ORDER BY timestamp DESC LIMIT ?'
        self.cursor.execute(query, (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def acknowledge_event(self, event_id: int) -> bool:
        """Acknowledge an event"""
        self.cursor.execute('UPDATE events SET acknowledged = 1 WHERE id = ?', (event_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def resolve_event(self, event_id: int) -> bool:
        """Resolve an event"""
        self.cursor.execute('UPDATE events SET resolved = 1 WHERE id = ?', (event_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    # Configuration operations
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        self.cursor.execute('SELECT value, type FROM configuration WHERE key = ?', (key,))
        row = self.cursor.fetchone()
        if row:
            value = row['value']
            type_ = row['type']
            if type_ == 'int':
                return int(value)
            elif type_ == 'float':
                return float(value)
            elif type_ == 'bool':
                return value.lower() == 'true'
            elif type_ == 'json':
                return json.loads(value)
            return value
        return default
    
    def set_config(self, key: str, value: Any, type_: str = None, updated_by: str = None) -> bool:
        """Set configuration value"""
        if type_ is None:
            if isinstance(value, bool):
                type_ = 'bool'
            elif isinstance(value, int):
                type_ = 'int'
            elif isinstance(value, float):
                type_ = 'float'
            elif isinstance(value, (dict, list)):
                type_ = 'json'
                value = json.dumps(value)
            else:
                type_ = 'str'
                value = str(value)
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO configuration (key, value, type, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (key, value, type_, datetime.utcnow().isoformat(), updated_by))
        self.connection.commit()
        return True
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values"""
        self.cursor.execute('SELECT key, value, type FROM configuration')
        config = {}
        for row in self.cursor.fetchall():
            value = row['value']
            type_ = row['type']
            if type_ == 'int':
                config[row['key']] = int(value)
            elif type_ == 'float':
                config[row['key']] = float(value)
            elif type_ == 'bool':
                config[row['key']] = value.lower() == 'true'
            elif type_ == 'json':
                config[row['key']] = json.loads(value)
            else:
                config[row['key']] = value
        return config
    
    # Audit log operations
    def log_audit(self, user: str, action: str, resource: str = None, details: str = None, ip_address: str = None) -> int:
        """Log an audit entry"""
        self.cursor.execute('''
            INSERT INTO audit_log (timestamp, user, action, resource, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.utcnow().isoformat(), user, action, resource, details, ip_address))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_audit_log(self, limit: int = 100, user: str = None) -> List[Dict]:
        """Get audit log entries"""
        if user:
            self.cursor.execute('SELECT * FROM audit_log WHERE user = ? ORDER BY timestamp DESC LIMIT ?', (user, limit))
        else:
            self.cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Session operations
    def create_session(self, user_id: int, token: str, expires_hours: int = 24) -> int:
        """Create a new session"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        self.cursor.execute('''
            INSERT INTO sessions (user_id, token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, token, datetime.utcnow().isoformat(), expires_at.isoformat()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_session(self, token: str) -> Optional[Dict]:
        """Get session by token"""
        self.cursor.execute('''
            SELECT * FROM sessions WHERE token = ? AND is_active = 1 AND expires_at > ?
        ''', (token, datetime.utcnow().isoformat()))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        self.cursor.execute('UPDATE sessions SET is_active = 0 WHERE token = ?', (token,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def cleanup_sessions(self) -> int:
        """Clean up expired sessions"""
        self.cursor.execute('''
            UPDATE sessions SET is_active = 0 WHERE expires_at < ?
        ''', (datetime.utcnow().isoformat(),))
        self.connection.commit()
        return self.cursor.rowcount
    
    # Database utilities
    def backup(self, backup_path: str = None) -> str:
        """Backup database"""
        if backup_path is None:
            backup_dir = Path(__file__).parent.parent / 'backups' / 'database'
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f'airone_backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.db'
        
        backup_conn = sqlite3.connect(backup_path)
        self.connection.backup(backup_conn)
        backup_conn.close()
        
        logging.info(f"Database backed up to: {backup_path}")
        return str(backup_path)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute custom query"""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            return [dict(row) for row in self.cursor.fetchall()]
        
        self.connection.commit()
        return []
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")


# Import timedelta for session expiry
from datetime import timedelta


def create_database(db_path: str = None) -> DatabaseManager:
    """Create and return database manager"""
    return DatabaseManager(db_path)


if __name__ == '__main__':
    # Test database
    logging.basicConfig(level=logging.INFO)
    
    db = create_database()
    
    # Test user creation
    user_id = db.create_user('test_user', hashlib.sha256('password'.encode('utf-8')).hexdigest(), 'operator', ['read', 'write'])
    print(f"Created user with ID: {user_id}")
    
    # Test telemetry storage
    db.store_telemetry({
        'altitude': 500.0,
        'velocity': 50.0,
        'temperature': 25.0,
        'pressure': 1013.25,
        'battery_level': 95.0,
        'status': 'nominal'
    })
    
    # Test configuration
    db.set_config('test_key', 'test_value')
    print(f"Config value: {db.get_config('test_key')}")
    
    # Test audit logging
    db.log_audit('test_user', 'TEST_ACTION', 'test_resource', 'Test details')
    
    print("Database tests completed")
    db.close()
