"""
AirOne Professional v4.0 - Advanced GUI Widgets
Modern reusable widget components
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import math
from datetime import datetime
from typing import List, Dict, Any, Optional


class CircularGauge(QWidget):
    """Circular gauge widget for displaying values"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(250, 250)
        
        self.value = 0.0
        self.min_value = 0.0
        self.max_value = 100.0
        self.title = ""
        self.unit = ""
        self.colors = {
            'bg': '#2d2d44',
            'arc': '#89b4fa',
            'arc_bg': '#45475a',
            'text': '#cdd6f4',
            'subtext': '#6c7086'
        }
        
    def setValue(self, value: float):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()
        
    def setRange(self, min_val: float, max_val: float):
        self.min_value = min_val
        self.max_value = max_val
        self.update()
        
    def setTitle(self, title: str):
        self.title = title
        self.update()
        
    def setUnit(self, unit: str):
        self.unit = unit
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center and radius
        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 15
        
        # Draw background arc
        pen = QPen(QColor(self.colors['arc_bg']), 12, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            45 * 16, 270 * 16
        )
        
        # Draw value arc
        span = int(((self.value - self.min_value) / (self.max_value - self.min_value)) * 270 * 16)
        pen.setColor(QColor(self.colors['arc']))
        painter.setPen(pen)
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            45 * 16, -span
        )
        
        # Draw value text
        painter.setPen(QColor(self.colors['text']))
        font = QFont('Segoe UI', 24, QFont.Bold)
        painter.setFont(font)
        value_text = f"{self.value:.1f}"
        value_rect = QRect(
            center.x() - 50, center.y() - 20,
            100, 40
        )
        painter.drawText(value_rect, Qt.AlignCenter, value_text)
        
        # Draw unit
        painter.setPen(QColor(self.colors['subtext']))
        font = QFont('Segoe UI', 12)
        painter.setFont(font)
        unit_rect = QRect(
            center.x() - 50, center.y() + 15,
            100, 20
        )
        painter.drawText(unit_rect, Qt.AlignCenter, self.unit)
        
        # Draw title
        if self.title:
            painter.setPen(QColor(self.colors['arc']))
            font = QFont('Segoe UI', 10, QFont.Bold)
            painter.setFont(font)
            title_rect = QRect(
                0, self.height() - 25,
                self.width(), 20
            )
            painter.drawText(title_rect, Qt.AlignCenter, self.title)


class StatusLED(QWidget):
    """LED status indicator widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.color = QColor('#45475a')
        self.blinking = False
        self.on = False
        
    def setColor(self, color):
        if isinstance(color, str):
            color = QColor(color)
        self.color = color
        self.update()
        
    def setState(self, on: bool):
        self.on = on
        self.update()
        
    def setBlinking(self, blinking: bool):
        self.blinking = blinking
        if blinking:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._toggle)
            self.timer.start(500)
        else:
            if hasattr(self, 'timer'):
                self.timer.stop()
                
    def _toggle(self):
        self.on = not self.on
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.on:
            # Glow effect
            gradient = QRadialGradient(
                self.width() / 2, self.height() / 2,
                self.width() / 2
            )
            gradient.setColorAt(0, self.color.lighter(150))
            gradient.setColorAt(0.5, self.color)
            gradient.setColorAt(1, self.color.darker(150))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        else:
            painter.setBrush(QColor(self.color.darker(200)))
            painter.setPen(QColor(self.color.darker(150)))
            painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)


class DataPlotWidget(QWidget):
    """Real-time data plotting widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        
        self.data_points: List[float] = []
        self.max_points = 100
        self.line_color = QColor('#89b4fa')
        self.fill_color = QColor(137, 180, 250, 50)
        self.grid_color = QColor(69, 71, 90, 100)
        
    def addData(self, value: float):
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
        
    def clear(self):
        self.data_points = []
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.data_points:
            return
            
        # Draw grid
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
        for i in range(5):
            y = int(self.height() / 5 * i)
            painter.drawLine(0, y, self.width(), y)
        
        # Draw data line
        path = QPainterPath()
        step_x = self.width() / (self.max_points - 1)
        
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Start path
        start_x = 0
        start_y = self.height() - 10
        path.moveTo(start_x, start_y)
        
        for i, value in enumerate(self.data_points):
            x = i * step_x
            normalized = (value - min_val) / range_val
            y = self.height() - 10 - (normalized * (self.height() - 20))
            
            if i == 0:
                path.lineTo(x, y)
            else:
                path.quadTo(
                    (x + (i - 1) * step_x) / 2,
                    self.height() - 10 - ((self.data_points[i-1] - min_val) / range_val * (self.height() - 20)),
                    x, y
                )
        
        # Complete path for fill
        path.lineTo(self.width() - step_x, self.height() - 10)
        path.closeSubpath()
        
        # Fill
        painter.fillPath(path, self.fill_color)
        
        # Draw line
        painter.setPen(QPen(self.line_color, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)


class InfoCard(QFrame):
    """Modern info card widget"""
    
    def __init__(self, title: str = "", value: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setFixedHeight(100)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Icon
        if icon:
            self.icon_label = QLabel(icon)
            self.icon_label.setStyleSheet("""
                font-size: 32px;
                padding: 10px;
            """)
            layout.addWidget(self.icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #6c7086;
            font-size: 12px;
            font-weight: 500;
        """)
        content_layout.addWidget(self.title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            color: #89b4fa;
            font-size: 28px;
            font-weight: 700;
        """)
        content_layout.addWidget(self.value_label)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
    def setValue(self, value: str):
        self.value_label.setText(value)
        
    def setTitleColor(self, color: str):
        self.title_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")
        
    def setValueColor(self, color: str):
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")


class ProgressBarWidget(QWidget):
    """Modern progress bar with percentage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.colors = {
            'bg': '#45475a',
            'fill_start': '#89b4fa',
            'fill_end': '#a6e3a1',
            'text': '#cdd6f4'
        }
        
    def setValue(self, value: float):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()
        
    def setRange(self, min_val: float, max_val: float):
        self.min_value = min_val
        self.max_value = max_val
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setBrush(QColor(self.colors['bg']))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 5, self.width(), 20, 10, 10)
        
        # Draw fill
        fill_width = int((self.value / (self.max_value - self.min_value)) * (self.width() - 10))
        if fill_width > 0:
            gradient = QLinearGradient(5, 5, fill_width + 5, 5)
            gradient.setColorAt(0, QColor(self.colors['fill_start']))
            gradient.setColorAt(1, QColor(self.colors['fill_end']))
            painter.setBrush(gradient)
            painter.drawRoundedRect(5, 5, fill_width - 5, 20, 10, 10)
        
        # Draw percentage text
        percentage = int((self.value / (self.max_value - self.min_value)) * 100)
        painter.setPen(QColor(self.colors['text']))
        font = QFont('Segoe UI', 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{percentage}%")


class AlertBanner(QWidget):
    """Collapsible alert banner"""
    
    def __init__(self, message: str, alert_type: str = "info", parent=None):
        super().__init__(parent)
        
        colors = {
            'info': ('#89b4fa', 'rgba(137, 180, 250, 0.1)'),
            'success': ('#a6e3a1', 'rgba(166, 227, 161, 0.1)'),
            'warning': ('#fab387', 'rgba(250, 179, 135, 0.1)'),
            'error': ('#f38ba8', 'rgba(243, 139, 168, 0.1)')
        }
        
        icons = {
            'info': '[i]',
            'success': '[OK]',
            'warning': '[!]',
            'error': '[X]'
        }
        
        self.color = colors.get(alert_type, colors['info'])[0]
        bg_color = colors.get(alert_type, colors['info'])[1]
        icon = icons.get(alert_type, '[i]')
        
        self.setStyleSheet(f"""
            background-color: {bg_color};
            border-left: 4px solid {self.color};
            border-radius: 8px;
            padding: 12px;
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet(f"color: {self.color}; font-weight: 500; font-size: 13px;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.color};
                font-size: 20px;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.color}30;
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class TelemetryRow(QWidget):
    """Single telemetry data row"""
    
    def __init__(self, label: str, value: str = "", unit: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Label
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet("""
            color: #a6adc8;
            font-size: 13px;
            min-width: 120px;
        """)
        layout.addWidget(self.label_widget)
        
        # Value
        self.value_widget = QLabel(value)
        self.value_widget.setStyleSheet("""
            color: #89b4fa;
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(self.value_widget)
        
        # Unit
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("""
                color: #6c7086;
                font-size: 12px;
                margin-left: 5px;
            """)
            layout.addWidget(unit_label)
        
        layout.addStretch()
        
    def setValue(self, value: str):
        self.value_widget.setText(value)
        
    def setWarning(self, warning: bool = True):
        if warning:
            self.value_widget.setStyleSheet("""
                color: #fab387;
                font-size: 16px;
                font-weight: 600;
            """)
        else:
            self.value_widget.setStyleSheet("""
                color: #89b4fa;
                font-size: 16px;
                font-weight: 600;
            """)


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with menu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create icon
        self.setIcon(self.create_icon())
        self.setToolTip("AirOne Professional v4.0")
        
        # Create menu
        menu = QMenu()
        
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.on_show)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        status_action = QAction("System Status: Online", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.on_quit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        # Double-click to show
        self.activated.connect(self.on_activated)
        
    def create_icon(self):
        """Create tray icon"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        gradient = QRadialGradient(32, 32, 32)
        gradient.setColorAt(0, QColor('#89b4fa'))
        gradient.setColorAt(1, QColor('#1e66f5'))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 64, 64)
        
        # Draw rocket
        painter.setPen(QPen(Qt.white, 3))
        painter.drawLine(32, 20, 32, 44)
        painter.drawLine(32, 20, 24, 32)
        painter.drawLine(32, 20, 40, 32)
        
        return QIcon(pixmap)
        
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.on_show()
            
    def on_show(self):
        if self.parent():
            self.parent().show()
            self.parent().activateWindow()
            
    def on_quit(self):
        QApplication.quit()


def create_info_card(title: str, value: str, icon: str = "") -> InfoCard:
    """Helper to create info card"""
    return InfoCard(title, value, icon)


def create_gauge(title: str = "", unit: str = "", 
                 min_val: float = 0, max_val: float = 100) -> CircularGauge:
    """Helper to create circular gauge"""
    gauge = CircularGauge()
    gauge.setTitle(title)
    gauge.setUnit(unit)
    gauge.setRange(min_val, max_val)
    return gauge
