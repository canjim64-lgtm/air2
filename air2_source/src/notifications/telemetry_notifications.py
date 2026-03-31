"""
Notification Module
Notification and alerting system
"""

from typing import Dict, List, Callable
import time


class Notification:
    """Notification"""
    
    def __init__(self, level: str, message: str, source: str = ""):
        self.timestamp = time.time()
        self.level = level
        self.message = message
        self.source = source


class NotificationManager:
    """Manage notifications"""
    
    def __init__(self):
        self.notifications = []
        self.handlers = []
    
    def add_handler(self, handler: Callable):
        """Add handler"""
        self.handlers.append(handler)
    
    def send(self, level: str, message: str, source: str = ""):
        """Send notification"""
        notif = Notification(level, message, source)
        self.notifications.append(notif)
        
        for handler in self.handlers:
            handler(notif)
    
    def get_notifications(self, level: str = None) -> List[Notification]:
        """Get notifications"""
        if level:
            return [n for n in self.notifications if n.level == level]
        return self.notifications


# Example
if __name__ == "__main__":
    nm = NotificationManager()
    nm.send("warning", "High temperature", "sensor1")
    print(f"Count: {len(nm.get_notifications())}")