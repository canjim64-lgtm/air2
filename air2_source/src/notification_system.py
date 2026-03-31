"""
AirOne Professional v4.0 - Notification System
Desktop notifications and alerts
"""
# -*- coding: utf-8 -*-

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)


class NotificationLevel:
    """Notification severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Notification:
    """Notification object"""
    
    def __init__(self, title: str, message: str, level: str = NotificationLevel.INFO,
                 duration: int = 5, callback: Optional[Callable] = None):
        self.id = f"notif_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.title = title
        self.message = message
        self.level = level
        self.duration = duration
        self.callback = callback
        self.created_at = datetime.now()
        self.dismissed = False
        self.acted_upon = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'level': self.level,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
            'dismissed': self.dismissed
        }
    
    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.title}: {self.message}"


class NotificationManager:
    """Manage system notifications"""
    
    def __init__(self, log_file: str = "logs/notifications.log"):
        self.notifications: List[Notification] = []
        self.subscribers: List[Callable] = []
        self.log_file = Path(log_file)
        self.running = False
        self.notification_thread = None
        
        # Create log directory
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Load persisted notifications
        self._load_notifications()
    
    def subscribe(self, callback: Callable):
        """Subscribe to notifications"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from notifications"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def notify(self, title: str, message: str, level: str = NotificationLevel.INFO,
               duration: int = 5, callback: Optional[Callable] = None) -> Notification:
        """Send notification"""
        notification = Notification(title, message, level, duration, callback)
        
        self.notifications.append(notification)
        self._log_notification(notification)
        self._notify_subscribers(notification)
        
        # Auto-dismiss after duration
        if duration > 0:
            self._schedule_dismissal(notification)
        
        logger.info(f"Notification: {notification}")
        return notification
    
    def info(self, title: str, message: str, **kwargs) -> Notification:
        """Send info notification"""
        return self.notify(title, message, NotificationLevel.INFO, **kwargs)
    
    def success(self, title: str, message: str, **kwargs) -> Notification:
        """Send success notification"""
        return self.notify(title, message, NotificationLevel.SUCCESS, **kwargs)
    
    def warning(self, title: str, message: str, **kwargs) -> Notification:
        """Send warning notification"""
        return self.notify(title, message, NotificationLevel.WARNING, **kwargs)
    
    def error(self, title: str, message: str, **kwargs) -> Notification:
        """Send error notification"""
        return self.notify(title, message, NotificationLevel.ERROR, **kwargs)
    
    def critical(self, title: str, message: str, **kwargs) -> Notification:
        """Send critical notification"""
        return self.notify(title, message, NotificationLevel.CRITICAL, duration=0, **kwargs)
    
    def _notify_subscribers(self, notification: Notification):
        """Notify all subscribers"""
        for callback in self.subscribers:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
    
    def _schedule_dismissal(self, notification: Notification):
        """Schedule notification dismissal"""
        def dismiss():
            time.sleep(notification.duration)
            if not notification.dismissed:
                notification.dismissed = True
                logger.debug(f"Notification auto-dismissed: {notification.id}")
        
        thread = threading.Thread(target=dismiss, daemon=True)
        thread.start()
    
    def _log_notification(self, notification: Notification):
        """Log notification to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_entry = json.dumps(notification.to_dict())
                f.write(log_entry + '\n')
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    def _load_notifications(self):
        """Load persisted notifications"""
        if not self.log_file.exists():
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        notif = Notification(
                            data['title'],
                            data['message'],
                            data['level'],
                            data.get('duration', 5)
                        )
                        notif.id = data['id']
                        notif.created_at = datetime.fromisoformat(data['created_at'])
                        notif.dismissed = data.get('dismissed', False)
                        self.notifications.append(notif)
                    except:
                        continue
        except Exception as e:
            logger.error(f"Failed to load notifications: {e}")
    
    def dismiss(self, notification_id: str):
        """Dismiss a notification"""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.dismissed = True
                logger.debug(f"Notification dismissed: {notification_id}")
                break
    
    def dismiss_all(self):
        """Dismiss all notifications"""
        for notif in self.notifications:
            notif.dismissed = True
        logger.info("All notifications dismissed")
    
    def get_active(self) -> List[Notification]:
        """Get active (non-dismissed) notifications"""
        return [n for n in self.notifications if not n.dismissed]
    
    def get_by_level(self, level: str) -> List[Notification]:
        """Get notifications by level"""
        return [n for n in self.notifications if n.level == level and not n.dismissed]
    
    def get_recent(self, count: int = 10) -> List[Notification]:
        """Get recent notifications"""
        return self.notifications[-count:]
    
    def clear_old(self, hours: int = 24):
        """Clear old notifications"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        self.notifications = [
            n for n in self.notifications
            if n.created_at.timestamp() > cutoff
        ]
        
        logger.info(f"Cleared notifications older than {hours} hours")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        active = self.get_active()
        
        return {
            'total': len(self.notifications),
            'active': len(active),
            'dismissed': len(self.notifications) - len(active),
            'by_level': {
                level: len(self.get_by_level(level))
                for level in [NotificationLevel.INFO, NotificationLevel.SUCCESS,
                             NotificationLevel.WARNING, NotificationLevel.ERROR,
                             NotificationLevel.CRITICAL]
            }
        }


class AlertSystem:
    """System alert management"""
    
    def __init__(self, notification_manager: Optional[NotificationManager] = None):
        self.notifier = notification_manager or NotificationManager()
        self.alert_rules: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
    
    def add_rule(self, condition: Callable, alert_title: str, alert_message: str,
                 level: str = NotificationLevel.WARNING) -> str:
        """Add alert rule"""
        rule_id = f"rule_{len(self.alert_rules)}"
        
        self.alert_rules.append({
            'id': rule_id,
            'condition': condition,
            'title': alert_title,
            'message': alert_message,
            'level': level,
            'enabled': True
        })
        
        return rule_id
    
    def check_rules(self):
        """Check all alert rules"""
        for rule in self.alert_rules:
            if not rule['enabled']:
                continue
            
            try:
                if rule['condition']():
                    alert = {
                        'rule_id': rule['id'],
                        'title': rule['title'],
                        'message': rule['message'],
                        'level': rule['level'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.alert_history.append(alert)
                    self.notifier.notify(
                        rule['title'],
                        rule['message'],
                        rule['level']
                    )
            except Exception as e:
                logger.error(f"Alert rule check failed: {e}")
    
    def start_monitoring(self, interval: float = 5.0):
        """Start continuous monitoring"""
        def monitor_loop():
            while True:
                self.check_rules()
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
        logger.info(f"Alert monitoring started (interval: {interval}s)")
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history[-limit:]


# Global notification manager
_global_notifier: Optional[NotificationManager] = None


def get_notifier() -> NotificationManager:
    """Get global notification manager"""
    global _global_notifier
    if _global_notifier is None:
        _global_notifier = NotificationManager()
    return _global_notifier


def notify(title: str, message: str, level: str = "info") -> Notification:
    """Quick notification"""
    return get_notifier().notify(title, message, level)


def notify_info(title: str, message: str) -> Notification:
    """Info notification"""
    return get_notifier().info(title, message)


def notify_success(title: str, message: str) -> Notification:
    """Success notification"""
    return get_notifier().success(title, message)


def notify_warning(title: str, message: str) -> Notification:
    """Warning notification"""
    return get_notifier().warning(title, message)


def notify_error(title: str, message: str) -> Notification:
    """Error notification"""
    return get_notifier().error(title, message)


if __name__ == "__main__":
    # Test notification system
    print("="*70)
    print("  AirOne Professional v4.0 - Notification System Test")
    print("="*70)
    print()
    
    notifier = NotificationManager()
    
    # Test different notification types
    print("Sending test notifications...")
    print()
    
    notifier.info("System Start", "AirOne Professional v4.0 initialized")
    time.sleep(0.5)
    
    notifier.success("Connection", "Telemetry link established")
    time.sleep(0.5)
    
    notifier.warning("Battery", "Battery level below 50%")
    time.sleep(0.5)
    
    notifier.error("Sensor", "GPS signal lost")
    time.sleep(0.5)
    
    notifier.critical("Emergency", "Critical system failure detected!")
    
    print()
    print("Notifications sent!")
    print()
    
    # Show stats
    stats = notifier.get_stats()
    print("Notification Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Active: {stats['active']}")
    print(f"  Dismissed: {stats['dismissed']}")
    print()
    
    # Test alert system
    print("Testing alert system...")
    
    alert_system = AlertSystem(notifier)
    
    # Add test rules
    counter = [0]
    
    def test_condition():
        counter[0] += 1
        return counter[0] % 3 == 0
    
    alert_system.add_rule(
        test_condition,
        "Test Alert",
        "This is a test alert triggered by condition",
        NotificationLevel.WARNING
    )
    
    # Check rules
    for i in range(5):
        alert_system.check_rules()
        time.sleep(0.1)
    
    print()
    print("Alert History:")
    for alert in alert_system.get_alert_history():
        print(f"  [{alert['level']}] {alert['title']}")
    
    print()
    print("="*70)
    print("  Notification System Test Complete")
    print("="*70)
