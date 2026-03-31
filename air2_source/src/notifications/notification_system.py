#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Notification System
Multi-channel notification system with email, SMS, push notifications, and more
"""

import os
import sys
import json
import smtplib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from enum import Enum
from dataclasses import dataclass
import requests


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    CONSOLE = "console"
    FILE = "file"
    SYSLOG = "syslog"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Represents a notification"""
    id: str
    channel: NotificationChannel
    priority: NotificationPriority
    title: str
    message: str
    recipient: str
    created_at: str
    sent_at: Optional[str] = None
    delivered: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class NotificationManager:
    """Advanced notification management system"""
    
    def __init__(self):
        self.notifications = []
        self.channels = {}
        self.templates = {}
        self.lock = threading.RLock()
        self.config_dir = Path(__file__).parent.parent / 'config' / 'notifications'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Register default channels
        self._register_default_channels()
    
    def _register_default_channels(self):
        """Register default notification channels"""
        
        # Console channel
        def console_handler(notification: Notification) -> bool:
            print(f"\n[{notification.priority.value.upper()}] {notification.title}")
            print(f"{notification.message}\n")
            return True
        
        self.register_channel(NotificationChannel.CONSOLE, console_handler)
        
        # File channel
        def file_handler(notification: Notification) -> bool:
            log_file = Path(__file__).parent.parent / 'logs' / 'notifications.log'
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{notification.created_at} | {notification.priority.value} | {notification.title} | {notification.message}\n")
            return True
        
        self.register_channel(NotificationChannel.FILE, file_handler)
    
    def register_channel(self, channel: NotificationChannel, handler: Callable[[Notification], bool]):
        """Register a notification channel handler"""
        self.channels[channel.value] = handler
    
    def create_template(self, name: str, template: str):
        """Create a notification template"""
        self.templates[name] = template
    
    def send_notification(self, channel: NotificationChannel, priority: NotificationPriority,
                         title: str, message: str, recipient: str, metadata: Dict = None) -> Notification:
        """Send a notification"""
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.notifications)}"
        
        notification = Notification(
            id=notification_id,
            channel=channel,
            priority=priority,
            title=title,
            message=message,
            recipient=recipient,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        # Send notification in background thread
        thread = threading.Thread(target=self._send_notification_async, args=(notification,))
        thread.daemon = True
        thread.start()
        
        with self.lock:
            self.notifications.append(notification)
        
        return notification
    
    def _send_notification_async(self, notification: Notification):
        """Send notification asynchronously"""
        try:
            handler = self.channels.get(notification.channel.value)
            if handler:
                success = handler(notification)
                notification.delivered = success
                notification.sent_at = datetime.utcnow().isoformat()
            else:
                notification.error = f"Unknown channel: {notification.channel}"
        except Exception as e:
            notification.error = str(e)
            logging.error(f"Notification failed: {e}")
    
    def send_email(self, to: str, subject: str, body: str, priority: NotificationPriority = NotificationPriority.NORMAL,
                  smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587,
                  username: str = '', password: str = '') -> Notification:
        """Send email notification"""
        
        def email_handler(notification: Notification) -> bool:
            if not username or not password:
                logging.warning("Email credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = notification.recipient
            msg['Subject'] = notification.title
            msg.attach(MIMEText(notification.message, 'plain'))
            
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
                server.quit()
                return True
            except Exception as e:
                logging.error(f"Email send failed: {e}")
                return False
        
        # Register temporary handler
        self.register_channel('email_temp', email_handler)
        
        notification = self.send_notification(
            NotificationChannel('email_temp'),
            priority,
            subject,
            body,
            to
        )
        
        return notification
    
    def send_webhook(self, url: str, payload: Dict, priority: NotificationPriority = NotificationPriority.NORMAL) -> Notification:
        """Send webhook notification"""
        
        def webhook_handler(notification: Notification) -> bool:
            try:
                response = requests.post(
                    notification.recipient,
                    json=notification.metadata.get('payload', {}),
                    timeout=10
                )
                return response.status_code == 200
            except Exception as e:
                logging.error(f"Webhook send failed: {e}")
                return False
        
        self.register_channel('webhook_temp', webhook_handler)
        
        notification = self.send_notification(
            NotificationChannel('webhook_temp'),
            priority,
            'Webhook Notification',
            f'Webhook to {url}',
            url,
            metadata={'payload': payload}
        )
        
        return notification
    
    def send_slack(self, webhook_url: str, message: str, channel: str = '#general',
                  priority: NotificationPriority = NotificationPriority.NORMAL) -> Notification:
        """Send Slack notification"""
        
        payload = {
            'channel': channel,
            'text': message,
            'username': 'AirOne Professional'
        }
        
        return self.send_webhook(webhook_url, payload, priority)
    
    def send_discord(self, webhook_url: str, message: str, priority: NotificationPriority = NotificationPriority.NORMAL) -> Notification:
        """Send Discord notification"""
        
        payload = {
            'content': message,
            'username': 'AirOne Professional'
        }
        
        return self.send_webhook(webhook_url, payload, priority)
    
    def get_notifications(self, limit: int = 100, channel: NotificationChannel = None,
                         priority: NotificationPriority = None) -> List[Notification]:
        """Get notifications with optional filters"""
        with self.lock:
            notifications = self.notifications.copy()
        
        if channel:
            notifications = [n for n in notifications if n.channel == channel]
        
        if priority:
            notifications = [n for n in notifications if n.priority == priority]
        
        # Sort by creation date
        notifications.sort(key=lambda n: n.created_at, reverse=True)
        
        return notifications[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        with self.lock:
            total = len(self.notifications)
            delivered = len([n for n in self.notifications if n.delivered])
            failed = len([n for n in self.notifications if not n.delivered and n.error])
            
            by_channel = {}
            by_priority = {}
            
            for notification in self.notifications:
                channel = notification.channel.value
                priority = notification.priority.value
                
                by_channel[channel] = by_channel.get(channel, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
            
            return {
                'total': total,
                'delivered': delivered,
                'failed': failed,
                'success_rate': round(delivered / total * 100, 2) if total > 0 else 0,
                'by_channel': by_channel,
                'by_priority': by_priority,
                'channels_registered': len(self.channels),
                'templates': len(self.templates)
            }
    
    def clear_notifications(self, older_than_days: int = 30):
        """Clear old notifications"""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        with self.lock:
            self.notifications = [
                n for n in self.notifications
                if datetime.fromisoformat(n.created_at) > cutoff
            ]


def create_notification_manager() -> NotificationManager:
    """Create and return notification manager"""
    return NotificationManager()


# Import timedelta
from datetime import timedelta


if __name__ == '__main__':
    # Test notification system
    logging.basicConfig(level=logging.INFO)
    
    manager = create_notification_manager()
    
    # Send console notification
    manager.send_notification(
        NotificationChannel.CONSOLE,
        NotificationPriority.INFO,
        'Test Notification',
        'This is a test notification',
        'admin'
    )
    
    # Send high priority notification
    manager.send_notification(
        NotificationChannel.CONSOLE,
        NotificationPriority.HIGH,
        'High Priority Alert',
        'This is a high priority alert',
        'admin'
    )
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"Notification statistics: {stats}")
    
    print("Notification system tests completed")
