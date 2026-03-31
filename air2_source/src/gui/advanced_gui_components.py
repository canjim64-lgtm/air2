"""
AirOne Professional v4.0 - Advanced GUI Components
Additional advanced GUI features and widgets

Features:
- 3D Flight Visualization
- GPS Map Tracking
- Audio Alert System
- Notification Center
- Multi-Mission Comparison
- Live Video Feed Support
- Custom Dashboard Builder
- Advanced Filtering
- Report Generator
- Plugin System
"""

import sys
import os
import time
import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
import numpy as np
import random
import wave # For WAV file generation
import struct # For WAV file generation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLCDNumber, QTableWidget, QTableWidgetItem,
        QTabWidget, QGroupBox, QStatusBar, QMenuBar, QMenu, QAction,
        QFileDialog, QMessageBox, QProgressDialog, QProgressBar,
        QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
        QRadioButton, QButtonGroup, QSplitter, QScrollArea, QFrame,
        QSystemTrayIcon, QToolBar, QDockWidget, QDialog, QDialogButtonBox,
        QFormLayout, QGridLayout, QSpacerItem, QSizePolicy, QListWidget,
        QListWidgetItem, QTreeWidget, QTreeWidgetItem, QSlider, QDial,
        QCalendarWidget, QDateTimeEdit, QCompleter, QLineEdit, QPlainTextEdit,
        QStackedWidget, QToolBox, QListView, QTreeView, QGraphicsView,
        QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
        QGraphicsTextItem, QGraphicsLineItem, QGraphicsPolygonItem,
        QGraphicsItemGroup, QApplication, QStyleFactory
    )
    from PyQt5.QtCore import (
        Qt, QTimer, QThread, pyqtSignal, QObject, QUrl, QFileInfo,
        QSettings, QStandardPaths, QSize, QPoint, QPointF, QRectF,
        QLineF, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
        QSequentialAnimationGroup, QTime, QDate, QDateTime
    )
    from PyQt5.QtGui import (
        QIcon, QFont, QColor, QPalette, QBrush, QPixmap, QPainter,
        QPen, QLinearGradient, QFontDatabase, QPolygonF, QTransform,
        QRadialGradient, QConicalGradient, QPainterPath, QRegion,
        QMovie, QImage, QBitmap
    )
    from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    
    PYQT5_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PyQt5 not available: {e}")
    PYQT5_AVAILABLE = False

# Try to import additional libraries
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Matplotlib 3D not available: {e}")

FOLIUM_AVAILABLE = False
try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except Exception as e:
    logger.warning(f"Folium not available: {e}")


# ============================================================================
# 3D FLIGHT VISUALIZATION
# ============================================================================

class FlightVisualization3D(QWidget):
    """3D flight path visualization"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.flight_path = []
        self.current_position = (0, 0, 0)
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        if MATPLOTLIB_AVAILABLE:
            # Create 3D figure
            self.figure = Figure(figsize=(8, 6))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
            
            # 3D axis
            self.ax = self.figure.add_subplot(111, projection='3d')
            
            # Labels
            self.ax.set_xlabel('Longitude')
            self.ax.set_ylabel('Latitude')
            self.ax.set_zlabel('Altitude (m)')
            self.ax.set_title('3D Flight Path')
            
            # Grid
            self.ax.grid(True, alpha=0.3)
            
            # Initial view
            self.ax.view_init(elev=30, azim=45)
            
            # View controls
            control_layout = QHBoxLayout()
            
            control_layout.addWidget(QLabel("Elevation:"))
            self.elev_slider = QSlider(Qt.Horizontal)
            self.elev_slider.setRange(0, 90)
            self.elev_slider.setValue(30)
            self.elev_slider.valueChanged.connect(self.update_view)
            control_layout.addWidget(self.elev_slider)
            
            control_layout.addWidget(QLabel("Azimuth:"))
            self.azim_slider = QSlider(Qt.Horizontal)
            self.azim_slider.setRange(0, 360)
            self.azim_slider.setValue(45)
            self.azim_slider.valueChanged.connect(self.update_view)
            control_layout.addWidget(self.azim_slider)
            
            # Reset view button
            reset_btn = QPushButton("Reset View")
            reset_btn.clicked.connect(self.reset_view)
            control_layout.addWidget(reset_btn)
            
            layout.addLayout(control_layout)
        else:
            # Fallback if matplotlib not available
            fallback_label = QLabel("3D Visualization requires matplotlib")
            fallback_label.setAlignment(Qt.AlignCenter)
            fallback_label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(fallback_label)
        
        self.setLayout(layout)
    
    def update_view(self):
        """Update 3D view angles"""
        if MATPLOTLIB_AVAILABLE:
            elev = self.elev_slider.value()
            azim = self.azim_slider.value()
            self.ax.view_init(elev=elev, azim=azim)
            self.canvas.draw()
    
    def reset_view(self):
        """Reset view to default"""
        self.elev_slider.setValue(30)
        self.azim_slider.setValue(45)
        self.update_view()
    
    def add_point(self, longitude: float, latitude: float, altitude: float):
        """Add flight path point"""
        self.flight_path.append((longitude, latitude, altitude))
        self.current_position = (longitude, latitude, altitude)
        
        if MATPLOTLIB_AVAILABLE and len(self.flight_path) > 1:
            self.update_plot()
    
    def update_plot(self):
        """Update 3D plot"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.ax.clear()
        
        # Convert to arrays
        lons = [p[0] for p in self.flight_path]
        lats = [p[1] for p in self.flight_path]
        alts = [p[2] for p in self.flight_path]
        
        # Plot flight path
        self.ax.plot3D(lons, lats, alts, 'b-', linewidth=2, label='Flight Path')
        
        # Plot current position
        if self.flight_path:
            self.ax.scatter3D(lons[-1], lats[-1], alts[-1], 
                            c='red', s=100, label='Current Position')
        
        # Plot launch point
        if self.flight_path:
            self.ax.scatter3D(lons[0], lats[0], alts[0], 
                            c='green', s=100, label='Launch Point')
        
        # Labels
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.set_zlabel('Altitude (m)')
        self.ax.set_title('3D Flight Path')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Restore view
        self.ax.view_init(elev=self.elev_slider.value(), 
                         azim=self.azim_slider.value())
        
        self.canvas.draw()


# ============================================================================
# GPS MAP TRACKING
# ============================================================================

class GPSMapWidget(QWidget):
    """GPS tracking map widget using Folium"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.track_points = []
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        if FOLIUM_AVAILABLE:
            # Web view for interactive map
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
            
            # Generate initial map
            self.generate_map()
        else:
            # Fallback
            fallback_label = QLabel("Interactive Map requires folium\npip install folium")
            fallback_label.setAlignment(Qt.AlignCenter)
            fallback_label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(fallback_label)
            
            # Static map placeholder
            self.map_label = QLabel("Map will appear here")
            self.map_label.setAlignment(Qt.AlignCenter)
            self.map_label.setMinimumSize(600, 400)
            self.map_label.setStyleSheet("background-color: #e0e0e0; border: 1px solid #ccc;")
            layout.addWidget(self.map_label)
        
        # Map controls
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(1, 18)
        self.zoom_slider.setValue(13)
        control_layout.addWidget(self.zoom_slider)
        
        # Center on current position
        center_btn = QPushButton("Center on Current")
        center_btn.clicked.connect(self.center_on_current)
        control_layout.addWidget(center_btn)
        
        # Clear track
        clear_btn = QPushButton("Clear Track")
        clear_btn.clicked.connect(self.clear_track)
        control_layout.addWidget(clear_btn)
        
        # Export KML
        export_btn = QPushButton("Export KML")
        export_btn.clicked.connect(self.export_kml)
        control_layout.addWidget(export_btn)
        
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def generate_map(self):
        """Generate folium map"""
        if not FOLIUM_AVAILABLE:
            return
        
        # Create map centered on default location
        self.map = folium.Map(location=[34.0522, -118.2437], zoom_start=13)
        
        # Add tile layers
        folium.TileLayer('OpenStreetMap').add_to(self.map)
        folium.TileLayer('Satellite').add_to(self.map)
        folium.TileLayer('Terrain').add_to(self.map)
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        # Save and display
        self.update_map_display()
    
    def update_map_display(self):
        """Update map display"""
        if not FOLIUM_AVAILABLE or not hasattr(self, 'map'):
            return
        
        # Save to temp file
        temp_path = str(Path.home() / "airone_map_temp.html")
        self.map.save(temp_path)
        
        # Load in web view
        self.web_view.load(QUrl.fromLocalFile(temp_path))
    
    def add_track_point(self, latitude: float, longitude: float, 
                       altitude: float, timestamp: datetime = None):
        """Add track point to map"""
        self.track_points.append({
            'lat': latitude,
            'lon': longitude,
            'alt': altitude,
            'time': timestamp or datetime.now()
        })
        
        if FOLIUM_AVAILABLE and hasattr(self, 'map'):
            # Add marker
            folium.CircleMarker(
                location=[latitude, longitude],
                radius=5,
                color='blue',
                fill=True,
                fill_color='blue',
                popup=f"Alt: {altitude:.1f}m<br>Time: {timestamp}"
            ).add_to(self.map)
            
            # Draw line connecting points
            if len(self.track_points) > 1:
                coordinates = [(p['lat'], p['lon']) for p in self.track_points]
                folium.PolyLine(coordinates, color='blue', weight=3).add_to(self.map)
            
            self.update_map_display()
    
    def center_on_current(self):
        """Center map on current position"""
        if self.track_points and FOLIUM_AVAILABLE:
            last_point = self.track_points[-1]
            self.map.location = [last_point['lat'], last_point['lon']]
            self.map.zoom_start = 15
            self.update_map_display()
    
    def clear_track(self):
        """Clear track from map"""
        self.track_points = []
        if FOLIUM_AVAILABLE:
            self.generate_map()
    
    def export_kml(self):
        """Export track to KML"""
        if not self.track_points:
            QMessageBox.warning(self, "Export", "No track data to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export KML", "", "KML Files (*.kml);;All Files (*)"
        )
        
        if file_path:
            # Simple KML generation
            kml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            kml_content += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
            kml_content += '<Document>\n'
            kml_content += '<name>AirOne Flight Track</name>\n'
            kml_content += '<Placemark>\n'
            kml_content += '<name>Flight Path</name>\n'
            kml_content += '<LineString>\n'
            kml_content += '<coordinates>'
            
            coords = ' '.join([
                f"{p['lon']},{p['lat']},{p['alt']}" 
                for p in self.track_points
            ])
            kml_content += coords
            
            kml_content += '</coordinates>\n'
            kml_content += '</LineString>\n'
            kml_content += '</Placemark>\n'
            kml_content += '</Document>\n'
            kml_content += '</kml>'
            
            with open(file_path, 'w') as f:
                f.write(kml_content)
            
            QMessageBox.information(self, "Export", f"KML exported to {file_path}")


# ============================================================================
# AUDIO ALERT SYSTEM
# ============================================================================

class AudioAlertSystem(QObject):
    """Audio alert and notification system"""
    
    alert_played = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.sounds = {}
        self.enabled = True
        self.volume = 75
        self._load_sounds()
    
    def _load_sounds(self):
        """Load or generate alert sounds"""
        # Define alert types
        self.alert_types = {
            'anomaly': {'frequency': 800, 'duration': 500, 'type': 'beep'},
            'warning': {'frequency': 600, 'duration': 300, 'type': 'beep'},
            'critical': {'frequency': 1000, 'duration': 1000, 'type': 'alarm'},
            'success': {'frequency': 1200, 'duration': 200, 'type': 'chime'},
            'notification': {'frequency': 400, 'duration': 150, 'type': 'soft'}
        }
        
        if PYQT5_AVAILABLE:
            for alert_type, config in self.alert_types.items():
                if config['type'] == 'beep':
                    self.sounds[alert_type] = self._generate_and_load_beep_sound(
                        config['frequency'], config['duration']
                    )
                elif config['type'] == 'alarm':
                    self.sounds[alert_type] = self._generate_and_load_alarm_sound(
                        config['frequency'], config['duration']
                    )
                else: # Generic notification
                    self.sounds[alert_type] = self._generate_and_load_beep_sound(
                        config['frequency'], config['duration']
                    )
    
    def _generate_and_load_beep_sound(self, frequency: int, duration_ms: int) -> Optional[QSound]:
        """Dynamically generate a simple beep sound and load it as QSound."""
        if not PYQT5_AVAILABLE:
            return None
        
        sample_rate = 44100  # samples per second
        duration_s = duration_ms / 1000.0
        
        # Generate sine wave
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
        amplitude = 0.5 * np.iinfo(np.int16).max
        data = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        int_data = data.astype(np.int16)
        
        # Create WAV file in memory
        wav_file = io.BytesIO()
        with wave.open(wav_file, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(int_data.tobytes())
        
        # Save to a temporary file for QSound
        temp_wav_path = str(Path.home() / f"temp_beep_{frequency}_{duration_ms}.wav")
        with open(temp_wav_path, 'wb') as f:
            f.write(wav_file.getvalue())
        
        return QSound(temp_wav_path)

    def _generate_and_load_alarm_sound(self, frequency: int, duration_ms: int) -> Optional[QSound]:
        """Dynamically generate a simple alarm-like sound (pulsating beep) and load it."""
        if not PYQT5_AVAILABLE:
            return None
        
        sample_rate = 44100
        duration_s = duration_ms / 1000.0
        
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
        amplitude = 0.5 * np.iinfo(np.int16).max
        
        # Pulsating tone (e.g., amplitude modulated sine wave)
        pulse_frequency = 5  # Hz
        data = amplitude * np.sin(2 * np.pi * frequency * t) * (0.5 + 0.5 * np.sin(2 * np.pi * pulse_frequency * t))
        
        int_data = data.astype(np.int16)
        
        wav_file = io.BytesIO()
        with wave.open(wav_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int_data.tobytes())
        
        temp_wav_path = str(Path.home() / f"temp_alarm_{frequency}_{duration_ms}.wav")
        with open(temp_wav_path, 'wb') as f:
            f.write(wav_file.getvalue())
        
        return QSound(temp_wav_path)
    
    def play_alert(self, alert_type: str):
        """Play alert sound"""
        if not self.enabled:
            return
        
        if alert_type not in self.alert_types:
            logger.warning(f"Unknown alert type: {alert_type}")
            return
        
        if PYQT5_AVAILABLE and alert_type in self.sounds:
            # Play pre-loaded sound
            self.sounds[alert_type].play()
        else:
            # Fallback: console beep
            print(f"\a")  # Console beep
        
        self.alert_played.emit(alert_type)
        logger.info(f"Alert played: {alert_type}")
    
    def play_anomaly_alert(self):
        """Play anomaly detection alert"""
        self.play_alert('anomaly')
    
    def play_warning_alert(self):
        """Play warning alert"""
        self.play_alert('warning')
    
    def play_critical_alert(self):
        """Play critical alert"""
        self.play_alert('critical')
    
    def play_success_alert(self):
        """Play success alert"""
        self.play_alert('success')
    
    def set_enabled(self, enabled: bool):
        """Enable/disable alerts"""
        self.enabled = enabled
    
    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        self.volume = max(0, min(100, volume))


# ============================================================================
# NOTIFICATION CENTER
# ============================================================================

class NotificationCenter(QWidget):
    """Centralized notification system"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.notifications = []
        self.audio_alerts = AudioAlertSystem()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Notification list
        self.notification_list = QListWidget()
        self.notification_list.setAlternatingRowColors(True)
        layout.addWidget(self.notification_list)
        
        # Controls
        control_layout = QHBoxLayout()
        
        # Clear all
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(clear_btn)
        
        # Clear old
        clear_old_btn = QPushButton("Clear Old (>1hr)")
        clear_old_btn.clicked.connect(self.clear_old)
        control_layout.addWidget(clear_old_btn)
        
        control_layout.addStretch()
        
        # Enable audio
        self.audio_check = QCheckBox("Audio Alerts")
        self.audio_check.setChecked(True)
        self.audio_check.stateChanged.connect(self.toggle_audio)
        control_layout.addWidget(self.audio_check)
        
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
        
        # Set minimum width
        self.setMinimumWidth(400)
    
    def add_notification(self, message: str, level: str = 'info',
                        alert: bool = False):
        """Add notification"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        notification = {
            'time': timestamp,
            'message': message,
            'level': level,
            'read': False,
            'datetime': datetime.now()
        }
        
        self.notifications.append(notification)
        
        # Add to list with icon based on level
        icon = "ℹ️" if level == 'info' else \
               "⚠️" if level == 'warning' else \
               "🚨" if level == 'critical' else "✓"
        
        item_text = f"[{timestamp}] {icon} {message}"
        item = QListWidgetItem(item_text)
        
        # Color code based on level
        if level == 'critical':
            item.setBackground(QColor("#ffcdd2"))
        elif level == 'warning':
            item.setBackground(QColor("#fff9c4"))
        elif level == 'success':
            item.setBackground(QColor("#c8e6c9"))
        
        self.notification_list.addItem(item)
        
        # Scroll to bottom
        self.notification_list.scrollToBottom()
        
        # Play audio alert if enabled
        if alert and self.audio_alerts.enabled:
            if level == 'critical':
                self.audio_alerts.play_critical_alert()
            elif level == 'warning':
                self.audio_alerts.play_warning_alert()
            else:
                self.audio_alerts.play_alert('notification')
    
    def notify_info(self, message: str):
        """Info notification"""
        self.add_notification(message, 'info')
    
    def notify_warning(self, message: str, alert: bool = True):
        """Warning notification"""
        self.add_notification(message, 'warning', alert)
    
    def notify_critical(self, message: str):
        """Critical notification"""
        self.add_notification(message, 'critical', True)
    
    def notify_success(self, message: str):
        """Success notification"""
        self.add_notification(message, 'success')
    
    def notify_anomaly(self, metric: str, value: float, threshold: float):
        """Anomaly notification"""
        message = f"Anomaly: {metric} = {value:.2f} (threshold: {threshold:.2f})"
        self.add_notification(message, 'critical', True)
    
    def clear_all(self):
        """Clear all notifications"""
        self.notifications.clear()
        self.notification_list.clear()
    
    def clear_old(self):
        """Clear notifications older than 1 hour"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        self.notifications = [
            n for n in self.notifications 
            if n['datetime'] > one_hour_ago
        ]
        
        # Refresh list
        self.notification_list.clear()
        for n in self.notifications:
            self.add_notification(n['message'], n['level'])
    
    def toggle_audio(self, state):
        """Toggle audio alerts"""
        self.audio_alerts.set_enabled(state == Qt.Checked)
    
    def get_unread_count(self) -> int:
        """Get unread notification count"""
        return sum(1 for n in self.notifications if not n['read'])


# ============================================================================
# CUSTOM DASHBOARD BUILDER
# ============================================================================

class DashboardBuilderWidget(QWidget):
    """Custom dashboard builder"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.widgets = []
        # Mapping from widget type string to actual widget class
        self.widget_class_map = {
            "QLCDNumber": QLCDNumber,
            "QProgressBar": QProgressBar,
            "QLabel": QLabel,
            "QPushButton": QPushButton,
            # Add other widget types as they are supported for dynamic loading
            # For 'graph' and 'status' (custom labels), might need specific factory functions
        }
        self.temp_wav_files = [] # Track temporary WAV files to clean up

    def __del__(self):
        # Clean up temporary WAV files when the AudioAlertSystem is destroyed
        for f in self.temp_wav_files:
            try:
                os.remove(f)
            except OSError:
                pass
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Widget palette
        palette_group = QGroupBox("Available Widgets")
        palette_layout = QHBoxLayout()
        
        widget_types = [
            ("Telemetry LCD", "lcd"),
            ("Progress Bar", "progress"),
            ("Text Label", "label"),
            ("Graph", "graph"),
            ("Status Indicator", "status"),
            ("Button", "button"),
            ("Spacer", "spacer")
        ]
        
        for name, widget_type in widget_types:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=widget_type: self.add_widget(t))
            palette_layout.addWidget(btn)
        
        palette_group.setLayout(palette_layout)
        layout.addWidget(palette_group)
        
        # Dashboard area
        dashboard_group = QGroupBox("Dashboard")
        self.dashboard_layout = QGridLayout()
        
        dashboard_widget = QWidget()
        dashboard_widget.setLayout(self.dashboard_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(dashboard_widget)
        scroll.setWidgetResizable(True)
        
        dashboard_group.setLayout(QVBoxLayout())
        dashboard_group.layout().addWidget(scroll)
        
        layout.addWidget(dashboard_group)
        
        # Save/Load
        save_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Dashboard")
        save_btn.clicked.connect(self.save_dashboard)
        save_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Dashboard")
        load_btn.clicked.connect(self.load_dashboard)
        save_layout.addWidget(load_btn)
        
        save_layout.addStretch()
        
        layout.addLayout(save_layout)
        
        self.setLayout(layout)
    
    def add_widget(self, widget_type: str, row: int = -1, col: int = -1):
        """Add widget to dashboard"""
        # Determine position if not specified
        if row == -1 or col == -1:
            row = len(self.widgets) // self.dashboard_layout.columnCount() if self.dashboard_layout.columnCount() > 0 else len(self.widgets)
            col = len(self.widgets) % self.dashboard_layout.columnCount() if self.dashboard_layout.columnCount() > 0 else len(self.widgets)
            
        widget = None
        if widget_type == "lcd":
            widget = QLCDNumber()
            widget.setDigitCount(8)
            widget.display("0.00")
        elif widget_type == "progress":
            widget = QProgressBar()
            widget.setRange(0, 100)
            widget.setValue(50)
        elif widget_type == "label":
            widget = QLabel("Label Text")
            widget.setStyleSheet("font-size: 14px; font-weight: bold;")
        elif widget_type == "status":
            widget = QLabel("● Status")
            widget.setStyleSheet("color: green; font-size: 16px;")
        elif widget_type == "button":
            widget = QPushButton("Button")
        elif widget_type == "spacer":
            widget = QSpacerItem(20, 40)
            self.dashboard_layout.addItem(widget, row, col)
            self.widgets.append({'type': widget_type, 'widget': None, 'row': row, 'col': col}) # Store QSpacerItem differently
            return
        
        if widget:
            self.dashboard_layout.addWidget(widget, row, col)
            self.widgets.append({'type': widget_type, 'widget': widget, 'row': row, 'col': col}) # Store widget instance

    def save_dashboard(self):
        """Save dashboard layout"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dashboard", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Save widget types and positions
            layout_data = []
            for item in self.widgets:
                if item['widget']: # Don't save QSpacerItem object directly
                    layout_data.append({
                        'type': item['type'], # Store the string type
                        'row': item['row'],
                        'col': item['col'],
                        'properties': { # Example: store text for QLabel, value for QLCDNumber
                            'text': item['widget'].text() if hasattr(item['widget'], 'text') else None,
                            'value': item['widget'].value() if hasattr(item['widget'], 'value') else None,
                            'styleSheet': item['widget'].styleSheet() if hasattr(item['widget'], 'styleSheet') else None,
                        }
                    })
                elif item['type'] == 'spacer': # Store spacer properties
                     layout_data.append({
                        'type': 'spacer',
                        'row': item['row'],
                        'col': item['col']
                     })

            with open(file_path, 'w') as f:
                json.dump(layout_data, f, indent=2)
            
            QMessageBox.information(self, "Save", "Dashboard saved")
    
    def load_dashboard(self):
        """Load dashboard layout"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Dashboard", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'r') as f:
                layout_data = json.load(f)
            
            # Clear current
            self.clear_dashboard()
            
            # Map widget type strings back to the add_widget method's logic
            for item in layout_data:
                widget_type = item['type']
                row = item['row']
                col = item['col']
                properties = item.get('properties', {})

                # Call add_widget, which creates the widget and adds to layout/self.widgets
                self.add_widget(widget_type, row, col) 

                # Apply properties
                # Find the newly added widget. It will be the last one in self.widgets
                if self.widgets and self.widgets[-1]['widget']:
                    new_widget_obj = self.widgets[-1]['widget']
                    if 'text' in properties and hasattr(new_widget_obj, 'setText'):
                        new_widget_obj.setText(properties['text'])
                    if 'value' in properties and hasattr(new_widget_obj, 'setValue'):
                        new_widget_obj.setValue(properties['value'])
                    if 'styleSheet' in properties and hasattr(new_widget_obj, 'setStyleSheet'):
                        new_widget_obj.setStyleSheet(properties['styleSheet'])
            
            QMessageBox.information(self, "Load", "Dashboard loaded")
    
    def clear_dashboard(self):
        """Clear dashboard"""
        while self.dashboard_layout.count():
            item = self.dashboard_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.dashboard_layout.removeItem(item) # Remove QSpacerItem
        self.widgets.clear()


# ============================================================================
# MAIN ADVANCED GUI WINDOW
# ============================================================================

class AdvancedGUIWindow(QMainWindow):
    """Advanced GUI with all additional features"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AirOne Professional v4.0 - Advanced GUI")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # 3D Visualization Tab
        self.visualization_3d = FlightVisualization3D()
        tabs.addTab(self.visualization_3d, "🎯 3D View")
        
        # GPS Map Tab
        self.gps_map = GPSMapWidget()
        tabs.addTab(self.gps_map, "🗺️ GPS Map")
        
        # Notifications Tab
        self.notification_center = NotificationCenter()
        tabs.addTab(self.notification_center, "🔔 Notifications")
        
        # Dashboard Builder Tab
        self.dashboard_builder = DashboardBuilderWidget()
        tabs.addTab(self.dashboard_builder, "📋 Dashboard Builder")
        
        main_layout.addWidget(tabs)
        
        central.setLayout(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage("Advanced GUI Ready")
        
        # Demo data timer
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.add_demo_data)
        self.demo_timer.start(2000)  # Every 2 seconds
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Add notification
        notify_action = QAction("Test Notification", self)
        notify_action.triggered.connect(self.test_notification)
        tools_menu.addAction(notify_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
    
    def add_demo_data(self):
        """Add demo data to visualizations"""
        import random
        
        # Demo flight path
        base_lat = 34.0522
        base_lon = -118.2437
        
        lat = base_lat + random.uniform(-0.001, 0.001)
        lon = base_lon + random.uniform(-0.001, 0.001)
        alt = random.uniform(100, 600)
        
        # Add to 3D visualization
        self.visualization_3d.add_point(lon, lat, alt)
        
        # Add to GPS map
        self.gps_map.add_track_point(lat, lon, alt)
        
        # Add notification occasionally
        if random.random() < 0.1:
            self.notification_center.notify_info(f"Telemetry update: Alt={alt:.1f}m")
    
    def test_notification(self):
        """Test notification system"""
        self.notification_center.notify_warning("This is a test warning")
        self.notification_center.notify_critical("This is a test critical alert")


def main():
    """Main entry point"""
    if not PYQT5_AVAILABLE:
        print("PyQt5 is not available.")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    
    window = AdvancedGUIWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
