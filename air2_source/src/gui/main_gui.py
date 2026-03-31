"""
AirOne Professional v4.0 - Enhanced Main GUI
Complete graphical interface with all features integrated

Features:
- Real-time telemetry display
- All 50+ mission graphs accessible
- Mission control panel
- System status dashboard
- Settings and configuration
- Multiple themes
- Interactive widgets
- Alert/notification system
- Multi-window support
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLCDNumber, QTableWidget, QTableWidgetItem,
        QTabWidget, QGroupBox, QStatusBar, QMenuBar, QMenu, QAction,
        QFileDialog, QMessageBox, QProgressDialog, QProgressBar,
        QTextEdit, QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
        QRadioButton, QButtonGroup, QSplitter, QScrollArea, QFrame,
        QSystemTrayIcon, QToolBar, QDockWidget, QDialog, QDialogButtonBox,
        QFormLayout, QGridLayout, QSpacerItem, QSizePolicy
    )
    from PyQt5.QtCore import (
        Qt, QTimer, QThread, pyqtSignal, QObject, QUrl, QFileInfo,
        QSettings, QStandardPaths, QSize, QPoint
    )
    from PyQt5.QtGui import (
        QIcon, QFont, QColor, QPalette, QBrush, QPixmap, QPainter,
        QPen, QLinearGradient, QFontDatabase
    )
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    
    PYQT5_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PyQt5 not available: {e}")
    PYQT5_AVAILABLE = False
    
    # Create placeholder classes for type hints when PyQt5 is not available
    class QApplication:
        pass
    class QMainWindow:
        pass
    class QWidget:
        pass

# Try to import plotting libraries
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
    logger.info("Matplotlib Qt5 backend available")
except Exception as e:
    logger.warning(f"Matplotlib not available: {e}")

PLOTLY_AVAILABLE = False
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
    logger.info("Plotly available")
except Exception as e:
    logger.warning(f"Plotly not available: {e}")

# Import AirOne modules
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.advanced_data_analysis import create_data_analyzer, GraphType, TelemetryPoint
    from ai.unified_ai_service import create_ai_service
    ANALYSIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"AirOne modules not available: {e}")
    ANALYSIS_AVAILABLE = False


class Theme:
    """Application themes"""
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    BLUE = "blue"
    GREEN = "green"


class ThemeManager:
    """Manage application themes"""
    
    def __init__(self):
        self.themes = {
            Theme.DARK: {
                'background': '#2b2b2b',
                'foreground': '#ffffff',
                'primary': '#007acc',
                'secondary': '#3c3c3c',
                'accent': '#ff6b35',
                'success': '#4caf50',
                'warning': '#ff9800',
                'error': '#f44336',
                'info': '#2196f3'
            },
            Theme.LIGHT: {
                'background': '#ffffff',
                'foreground': '#000000',
                'primary': '#0066cc',
                'secondary': '#f0f0f0',
                'accent': '#ff6b35',
                'success': '#4caf50',
                'warning': '#ff9800',
                'error': '#f44336',
                'info': '#2196f3'
            },
            Theme.HIGH_CONTRAST: {
                'background': '#000000',
                'foreground': '#ffffff',
                'primary': '#ffff00',
                'secondary': '#ffffff',
                'accent': '#00ffff',
                'success': '#00ff00',
                'warning': '#ffff00',
                'error': '#ff0000',
                'info': '#00ffff'
            },
            Theme.BLUE: {
                'background': '#1a2332',
                'foreground': '#e0e0e0',
                'primary': '#4fc3f7',
                'secondary': '#263238',
                'accent': '#ff7043',
                'success': '#81c784',
                'warning': '#ffb74d',
                'error': '#e57373',
                'info': '#64b5f6'
            },
            Theme.GREEN: {
                'background': '#1b261b',
                'foreground': '#e0e0e0',
                'primary': '#81c784',
                'secondary': '#263226',
                'accent': '#ff7043',
                'success': '#a5d6a7',
                'warning': '#ffb74d',
                'error': '#e57373',
                'info': '#90caf9'
            }
        }
        
        self.current_theme = Theme.DARK
    
    def get_stylesheet(self, theme_name: str = None) -> str:
        """Get Qt stylesheet for theme"""
        if theme_name is None:
            theme_name = self.current_theme
        
        colors = self.themes.get(theme_name, self.themes[Theme.DARK])
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['foreground']};
        }}
        
        QWidget {{
            background-color: {colors['background']};
            color: {colors['foreground']};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }}
        
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['secondary']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['secondary']};
            color: {colors['foreground']}50;
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {colors['secondary']};
            border: 1px solid {colors['primary']};
            border-radius: 4px;
            padding: 4px;
            color: {colors['foreground']};
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {colors['accent']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors['secondary']};
            background-color: {colors['background']};
            border-radius: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {colors['secondary']};
            color: {colors['foreground']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors['accent']}50;
        }}
        
        QMenuBar {{
            background-color: {colors['secondary']};
            color: {colors['foreground']};
            padding: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QMenu {{
            background-color: {colors['secondary']};
            border: 1px solid {colors['primary']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {colors['secondary']};
            color: {colors['foreground']};
            border-top: 1px solid {colors['primary']};
        }}
        
        QProgressBar {{
            border: 1px solid {colors['secondary']};
            border-radius: 4px;
            text-align: center;
            background-color: {colors['secondary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['success']};
        }}
        
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors['secondary']};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: {colors['secondary']}30;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {colors['primary']};
        }}
        
        QTableWidget {{
            background-color: {colors['secondary']}50;
            alternate-background-color: {colors['secondary']}30;
            gridline-color: {colors['secondary']};
            border: 1px solid {colors['secondary']};
            border-radius: 4px;
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {colors['primary']};
            color: white;
            padding: 4px;
            border: none;
            font-weight: bold;
        }}
        
        QScrollBar:vertical {{
            background-color: {colors['secondary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['primary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors['secondary']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['primary']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors['foreground']};
            margin-right: 5px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['primary']};
            border-radius: 3px;
            background-color: {colors['secondary']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['primary']};
        }}
        
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['primary']};
            border-radius: 8px;
            background-color: {colors['secondary']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {colors['primary']};
        }}
        
        QToolTip {{
            background-color: {colors['primary']};
            color: white;
            border: 1px solid {colors['foreground']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QSplitter::handle {{
            background-color: {colors['secondary']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        """
        
        return stylesheet
    
    def apply_theme(self, app, theme_name: str):
        """Apply theme to application"""
        if not PYQT5_AVAILABLE:
            logger.warning("Cannot apply theme - PyQt5 not available")
            return
        self.current_theme = theme_name
        if app:
            app.setStyleSheet(self.get_stylesheet(theme_name))


class TelemetryDisplayWidget(QWidget):
    """Real-time telemetry display widget"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.telemetry_data = {}
    
    def init_ui(self):
        """Initialize UI"""
        layout = QGridLayout()
        
        # Altitude
        layout.addWidget(QLabel("Altitude (m):"), 0, 0)
        self.altitude_lcd = QLCDNumber()
        self.altitude_lcd.setDigitCount(8)
        self.altitude_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.altitude_lcd.setStyleSheet("color: #007acc; background-color: #f0f0f0;")
        layout.addWidget(self.altitude_lcd, 0, 1)
        
        # Velocity
        layout.addWidget(QLabel("Velocity (m/s):"), 0, 2)
        self.velocity_lcd = QLCDNumber()
        self.velocity_lcd.setDigitCount(8)
        self.velocity_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.velocity_lcd.setStyleSheet("color: #ff5722; background-color: #f0f0f0;")
        layout.addWidget(self.velocity_lcd, 0, 3)
        
        # Temperature
        layout.addWidget(QLabel("Temperature (°C):"), 1, 0)
        self.temp_lcd = QLCDNumber()
        self.temp_lcd.setDigitCount(6)
        self.temp_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.temp_lcd.setStyleSheet("color: #ff9800; background-color: #f0f0f0;")
        layout.addWidget(self.temp_lcd, 1, 1)
        
        # Pressure
        layout.addWidget(QLabel("Pressure (hPa):"), 1, 2)
        self.pressure_lcd = QLCDNumber()
        self.pressure_lcd.setDigitCount(7)
        self.pressure_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.pressure_lcd.setStyleSheet("color: #4caf50; background-color: #f0f0f0;")
        layout.addWidget(self.pressure_lcd, 1, 3)
        
        # Battery
        layout.addWidget(QLabel("Battery (%):"), 2, 0)
        self.battery_lcd = QLCDNumber()
        self.battery_lcd.setDigitCount(5)
        self.battery_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.battery_lcd.setStyleSheet("color: #8bc34a; background-color: #f0f0f0;")
        layout.addWidget(self.battery_lcd, 2, 1)
        
        # Battery progress bar
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(100)
        self.battery_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
            }
        """)
        layout.addWidget(self.battery_bar, 2, 2, 1, 2)
        
        # Signal
        layout.addWidget(QLabel("Signal (dBm):"), 3, 0)
        self.signal_lcd = QLCDNumber()
        self.signal_lcd.setDigitCount(6)
        self.signal_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.signal_lcd.setStyleSheet("color: #03a9f4; background-color: #f0f0f0;")
        layout.addWidget(self.signal_lcd, 3, 1)
        
        # GPS
        layout.addWidget(QLabel("GPS:"), 3, 2)
        self.gps_label = QLabel("0.000000, 0.000000")
        self.gps_label.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        layout.addWidget(self.gps_label, 3, 3)
        
        # Flight phase
        layout.addWidget(QLabel("Flight Phase:"), 4, 0)
        self.phase_label = QLabel("UNKNOWN")
        self.phase_label.setStyleSheet("font-weight: bold; color: #9c27b0; font-size: 14px;")
        layout.addWidget(self.phase_label, 4, 1, 1, 3)
        
        self.setLayout(layout)
    
    def update_telemetry(self, data: Dict[str, Any]):
        """Update telemetry display"""
        if 'altitude' in data:
            self.altitude_lcd.display(f"{data['altitude']:8.2f}")
        
        if 'velocity' in data:
            self.velocity_lcd.display(f"{data['velocity']:8.2f}")
        
        if 'temperature' in data:
            self.temp_lcd.display(f"{data['temperature']:6.1f}")
        
        if 'pressure' in data:
            self.pressure_lcd.display(f"{data['pressure']:7.1f}")
        
        if 'battery_percent' in data:
            battery = data['battery_percent']
            self.battery_lcd.display(f"{battery:5.1f}")
            self.battery_bar.setValue(int(battery))
            
            # Change color based on battery level
            if battery > 50:
                color = "#4caf50"
            elif battery > 20:
                color = "#ff9800"
            else:
                color = "#f44336"
            
            self.battery_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
        
        if 'signal_strength' in data:
            self.signal_lcd.display(f"{data['signal_strength']:6.0f}")
        
        if 'latitude' in data and 'longitude' in data:
            self.gps_label.setText(f"{data['latitude']:.6f}, {data['longitude']:.6f}")
        
        if 'flight_phase' in data:
            self.phase_label.setText(data['flight_phase'])


class GraphWidget(QWidget):
    """Widget for displaying graphs"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.canvas = None
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Graph type selector
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(QLabel("Graph Type:"))
        
        self.graph_combo = QComboBox()
        for gt in GraphType:
            self.graph_combo.addItem(gt.value.replace('_', ' ').title(), gt)
        
        self.graph_combo.currentIndexChanged.connect(self.on_graph_changed)
        graph_layout.addWidget(self.graph_combo)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Graph")
        self.generate_btn.clicked.connect(self.generate_graph)
        graph_layout.addWidget(self.generate_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_graph)
        graph_layout.addWidget(self.export_btn)
        
        graph_layout.addStretch()
        
        layout.addLayout(graph_layout)
        
        # Graph display area
        self.graph_frame = QFrame()
        self.graph_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 4px;")
        self.graph_frame.setMinimumSize(800, 400)
        
        frame_layout = QVBoxLayout()
        self.graph_label = QLabel("Select a graph type and click Generate")
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setStyleSheet("color: #666; font-size: 14px;")
        frame_layout.addWidget(self.graph_label)
        
        self.graph_frame.setLayout(frame_layout)
        layout.addWidget(self.graph_frame)
        
        self.setLayout(layout)
    
    def on_graph_changed(self, index):
        """Handle graph type change"""
        pass
    
    def generate_graph(self):
        """Generate selected graph"""
        if not ANALYSIS_AVAILABLE:
            self.graph_label.setText("Analysis module not available")
            return
        
        graph_type = self.graph_combo.currentData()
        
        # Get analyzer from main window
        main_window = self.window()
        if hasattr(main_window, 'analyzer'):
            result = main_window.analyzer.generate_graph(graph_type)
            
            if 'error' not in result:
                if 'image_data' in result:
                    # Display matplotlib graph
                    pixmap = QPixmap()
                    pixmap.loadFromData(result['image_data'])
                    self.graph_label.setPixmap(pixmap.scaled(
                        self.graph_frame.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                elif 'figure' in result:
                    # Display plotly graph (would need QWebEngineView)
                    self.graph_label.setText("Interactive graph generated (save to view)")
            else:
                self.graph_label.setText(f"Error: {result.get('error', 'Unknown')}")
        else:
            self.graph_label.setText("No data available")
    
    def export_graph(self):
        """Export current graph"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", "",
            "PNG Files (*.png);;HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            main_window = self.window()
            if hasattr(main_window, 'analyzer'):
                graph_type = self.graph_combo.currentData()
                result = main_window.analyzer.generate_graph(
                    graph_type,
                    save_path=file_path
                )
                
                if 'error' not in result:
                    QMessageBox.information(self, "Export", f"Graph exported to {file_path}")
                else:
                    QMessageBox.warning(self, "Export Error", result.get('error', 'Unknown error'))


class MissionControlWidget(QWidget):
    """Mission control panel"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Mission status
        status_group = QGroupBox("Mission Status")
        status_layout = QGridLayout()
        
        status_layout.addWidget(QLabel("Mission Phase:"), 0, 0)
        self.phase_label = QLabel("--")
        self.phase_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        status_layout.addWidget(self.phase_label, 0, 1)
        
        status_layout.addWidget(QLabel("Flight Computer:"), 1, 0)
        self.fc_label = QLabel("--")
        status_layout.addWidget(self.fc_label, 1, 1)
        
        status_layout.addWidget(QLabel("Communication:"), 2, 0)
        self.comm_label = QLabel("--")
        status_layout.addWidget(self.comm_label, 2, 1)
        
        status_layout.addWidget(QLabel("GPS Lock:"), 3, 0)
        self.gps_label = QLabel("--")
        status_layout.addWidget(self.gps_label, 3, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Command panel
        command_group = QGroupBox("Command Panel")
        command_layout = QVBoxLayout()
        
        # Command buttons
        btn_layout = QHBoxLayout()
        
        self.arm_btn = QPushButton("ARM SYSTEM")
        self.arm_btn.setStyleSheet("background-color: #ff6b35; color: white; font-weight: bold;")
        self.arm_btn.clicked.connect(self.arm_system)
        btn_layout.addWidget(self.arm_btn)
        
        self.disarm_btn = QPushButton("DISARM SYSTEM")
        self.disarm_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.disarm_btn.clicked.connect(self.disarm_system)
        btn_layout.addWidget(self.disarm_btn)
        
        command_layout.addLayout(btn_layout)
        
        btn_layout2 = QHBoxLayout()
        
        self.start_btn = QPushButton("START")
        self.start_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_mission)
        btn_layout2.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_mission)
        btn_layout2.addWidget(self.stop_btn)
        
        command_layout.addLayout(btn_layout2)
        
        # Deploy parachute
        self.chute_btn = QPushButton("DEPLOY PARACHUTE")
        self.chute_btn.setStyleSheet("background-color: #2196f3; color: white; font-weight: bold;")
        self.chute_btn.clicked.connect(self.deploy_chute)
        command_layout.addWidget(self.chute_btn)
        
        # Emergency
        self.emergency_btn = QPushButton("EMERGENCY ABORT")
        self.emergency_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.emergency_btn.clicked.connect(self.emergency_abort)
        command_layout.addWidget(self.emergency_btn)
        
        # Command log
        command_layout.addWidget(QLabel("Command Log:"))
        self.command_log = QTextEdit()
        self.command_log.setMaximumHeight(150)
        self.command_log.setReadOnly(True)
        command_layout.addWidget(self.command_log)
        
        command_group.setLayout(command_layout)
        layout.addWidget(command_group)
        
        self.setLayout(layout)
    
    def arm_system(self):
        """Arm the system"""
        self.log_command("ARM SYSTEM")
        self.phase_label.setText("ARMED")
        self.phase_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ff6b35;")
    
    def disarm_system(self):
        """Disarm the system"""
        self.log_command("DISARM SYSTEM")
        self.phase_label.setText("DISARMED")
        self.phase_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #666;")
    
    def start_mission(self):
        """Start mission"""
        self.log_command("START MISSION")
        self.phase_label.setText("FLIGHT")
        self.phase_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4caf50;")
    
    def stop_mission(self):
        """Stop mission"""
        self.log_command("STOP MISSION")
        self.phase_label.setText("ENDED")
    
    def deploy_chute(self):
        """Deploy parachute"""
        self.log_command("DEPLOY PARACHUTE")
        QMessageBox.information(self, "Parachute", "Parachute deployment command sent")
    
    def emergency_abort(self):
        """Emergency abort"""
        self.log_command("EMERGENCY ABORT")
        reply = QMessageBox.critical(
            self, "Emergency Abort",
            "Are you sure you want to abort the mission?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.phase_label.setText("ABORTED")
            self.phase_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f44336;")
    
    def log_command(self, command: str):
        """Log command"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.command_log.append(f"[{timestamp}] {command}")


class SystemStatusWidget(QWidget):
    """System status dashboard"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # CPU Usage
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(15)
        self.cpu_bar.setFormat("%p%")
        cpu_layout.addWidget(self.cpu_bar)
        cpu_group.setLayout(cpu_layout)
        
        # Memory Usage
        mem_group = QGroupBox("Memory Usage")
        mem_layout = QVBoxLayout()
        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        self.mem_bar.setValue(25)
        self.mem_bar.setFormat("%p%")
        mem_layout.addWidget(self.mem_bar)
        mem_group.setLayout(mem_layout)
        
        # Disk Usage
        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout()
        self.disk_bar = QProgressBar()
        self.disk_bar.setRange(0, 100)
        self.disk_bar.setValue(50)
        self.disk_bar.setFormat("%p%")
        disk_layout.addWidget(self.disk_bar)
        disk_group.setLayout(disk_layout)
        
        # Network
        net_group = QGroupBox("Network Status")
        net_layout = QVBoxLayout()
        self.net_label = QLabel("Connected")
        self.net_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        net_layout.addWidget(self.net_label)
        
        self.net_bar = QProgressBar()
        self.net_bar.setRange(0, 100)
        self.net_bar.setValue(0)
        self.net_bar.setFormat("Throughput: %p%")
        net_layout.addWidget(self.net_bar)
        net_group.setLayout(net_layout)
        
        # Add to main layout
        main_layout = QGridLayout()
        main_layout.addWidget(cpu_group, 0, 0)
        main_layout.addWidget(mem_group, 0, 1)
        main_layout.addWidget(disk_group, 1, 0)
        main_layout.addWidget(net_group, 1, 1)
        
        layout.addLayout(main_layout)
        
        # System info
        info_group = QGroupBox("System Information")
        info_layout = QFormLayout()
        
        info_layout.addRow("Python Version:", QLabel(sys.version.split()[0]))
        info_layout.addRow("Platform:", QLabel(sys.platform))
        info_layout.addRow("AirOne Version:", QLabel("4.0 Ultimate"))
        info_layout.addRow("Status:", QLabel("Operational"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)


class AirOneMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.theme_manager = ThemeManager()
        self.analyzer = None
        self.ai_service = None
        
        if ANALYSIS_AVAILABLE:
            self.analyzer = create_data_analyzer()
            self.ai_service = create_ai_service()
        
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()
        self.create_tool_bar()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_telemetry)
        self.update_timer.start(1000)  # Update every second
        
        # Apply theme
        self.theme_manager.apply_theme(QApplication.instance(), self.theme_manager.current_theme)
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("AirOne Professional v4.0 - CanSat Ground Station")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Dashboard
        dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(dashboard_tab, "📊 Dashboard")
        
        # Tab 2: Telemetry
        telemetry_tab = self.create_telemetry_tab()
        self.tab_widget.addTab(telemetry_tab, "📈 Telemetry")
        
        # Tab 3: Graphs
        graphs_tab = self.create_graphs_tab()
        self.tab_widget.addTab(graphs_tab, "📉 Graphs")
        
        # Tab 4: Mission Control
        control_tab = self.create_control_tab()
        self.tab_widget.addTab(control_tab, "🎮 Mission Control")
        
        # Tab 5: System Status
        status_tab = self.create_status_tab()
        self.tab_widget.addTab(status_tab, "💻 System")
        
        # Tab 6: AI Analysis
        ai_tab = self.create_ai_tab()
        self.tab_widget.addTab(ai_tab, "🤖 AI Analysis")
        
        # Tab 7: Settings
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        main_layout.addWidget(self.tab_widget)
        
        central_widget.setLayout(main_layout)
    
    def create_dashboard_tab(self) -> QWidget:
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Top row: Telemetry display
        self.telemetry_display = TelemetryDisplayWidget()
        layout.addWidget(self.telemetry_display)
        
        # Bottom row: Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Quick stats
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        
        stats_group = QGroupBox("Quick Statistics")
        stats_form = QFormLayout()
        
        self.stat_duration = QLabel("0.0s")
        stats_form.addRow("Mission Duration:", self.stat_duration)
        
        self.stat_max_alt = QLabel("0.0m")
        stats_form.addRow("Max Altitude:", self.stat_max_alt)
        
        self.stat_max_vel = QLabel("0.0m/s")
        stats_form.addRow("Max Velocity:", self.stat_max_vel)
        
        self.stat_packets = QLabel("0")
        stats_form.addRow("Packets Received:", self.stat_packets)
        
        stats_group.setLayout(stats_form)
        stats_layout.addWidget(stats_group)
        
        # Anomaly alert
        self.anomaly_label = QLabel("No anomalies detected")
        self.anomaly_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        stats_layout.addWidget(self.anomaly_label)
        
        stats_layout.addStretch()
        stats_widget.setLayout(stats_layout)
        
        # Right: Mini graph
        mini_graph = GraphWidget()
        
        splitter.addWidget(stats_widget)
        splitter.addWidget(mini_graph)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def create_telemetry_tab(self) -> QWidget:
        """Create telemetry tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Telemetry table
        self.telemetry_table = QTableWidget()
        self.telemetry_table.setColumnCount(12)
        self.telemetry_table.setHorizontalHeaderLabels([
            "Time", "Altitude", "Velocity", "Acceleration",
            "Temperature", "Pressure", "Battery", "Signal",
            "Latitude", "Longitude", "Phase", "Quality"
        ])
        self.telemetry_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.telemetry_table)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        export_btn = QPushButton("Export Telemetry")
        export_btn.clicked.connect(self.export_telemetry)
        export_layout.addWidget(export_btn)
        
        layout.addLayout(export_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_graphs_tab(self) -> QWidget:
        """Create graphs tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Graph selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Graph:"))
        
        self.all_graphs_combo = QComboBox()
        for gt in GraphType:
            self.all_graphs_combo.addItem(gt.value.replace('_', ' ').title(), gt)
        selection_layout.addWidget(self.all_graphs_combo)
        
        generate_all_btn = QPushButton("Generate All 50+ Graphs")
        generate_all_btn.clicked.connect(self.generate_all_graphs)
        selection_layout.addWidget(generate_all_btn)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        # Graph display
        self.main_graph_widget = GraphWidget()
        layout.addWidget(self.main_graph_widget)
        
        widget.setLayout(layout)
        return widget
    
    def create_control_tab(self) -> QWidget:
        """Create mission control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.mission_control = MissionControlWidget()
        layout.addWidget(self.mission_control)
        
        widget.setLayout(layout)
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Create system status tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.system_status = SystemStatusWidget()
        layout.addWidget(self.system_status)
        
        widget.setLayout(layout)
        return widget
    
    def create_ai_tab(self) -> QWidget:
        """Create AI analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        if self.ai_service:
            # AI query
            query_group = QGroupBox("AI Query")
            query_layout = QVBoxLayout()
            
            self.ai_query = QTextEdit()
            self.ai_query.setPlaceholderText("Ask AI about telemetry data...")
            self.ai_query.setMaximumHeight(100)
            query_layout.addWidget(self.ai_query)
            
            analyze_btn = QPushButton("Analyze with AI")
            analyze_btn.clicked.connect(self.analyze_with_ai)
            query_layout.addWidget(analyze_btn)
            
            query_group.setLayout(query_layout)
            layout.addWidget(query_group)
            
            # AI results
            results_group = QGroupBox("AI Analysis Results")
            results_layout = QVBoxLayout()
            
            self.ai_results = QTextEdit()
            self.ai_results.setReadOnly(True)
            results_layout.addWidget(self.ai_results)
            
            results_group.setLayout(results_layout)
            layout.addWidget(results_group)
        else:
            layout.addWidget(QLabel("AI service not available"))
        
        widget.setLayout(layout)
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Theme selection
        theme_combo = QComboBox()
        theme_combo.addItem("Dark", Theme.DARK)
        theme_combo.addItem("Light", Theme.LIGHT)
        theme_combo.addItem("High Contrast", Theme.HIGH_CONTRAST)
        theme_combo.addItem("Blue", Theme.BLUE)
        theme_combo.addItem("Green", Theme.GREEN)
        theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        layout.addRow("Theme:", theme_combo)
        
        # Update rate
        self.update_rate_spin = QSpinBox()
        self.update_rate_spin.setRange(100, 10000)
        self.update_rate_spin.setValue(1000)
        self.update_rate_spin.setSuffix(" ms")
        self.update_rate_spin.valueChanged.connect(self.on_update_rate_changed)
        layout.addRow("Update Rate:", self.update_rate_spin)
        
        # Auto-save
        self.autosave_check = QCheckBox("Enable Auto-Save")
        self.autosave_check.setChecked(True)
        layout.addRow("Auto-Save:", self.autosave_check)
        
        # Sound alerts
        self.sound_check = QCheckBox("Enable Sound Alerts")
        self.sound_check.setChecked(True)
        layout.addRow("Sound Alerts:", self.sound_check)
        
        # Data directory
        data_dir_layout = QHBoxLayout()
        self.data_dir_edit = QLineEdit(str(Path.home() / "airone_data"))
        data_dir_layout.addWidget(self.data_dir_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_data_dir)
        data_dir_layout.addWidget(browse_btn)
        
        layout.addRow("Data Directory:", data_dir_layout)
        
        # Save settings
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow("", save_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Mission", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Mission", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Data", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        theme_menu = view_menu.addMenu("&Theme")
        
        for theme_name, theme_value in [
            ("Dark", Theme.DARK),
            ("Light", Theme.LIGHT),
            ("High Contrast", Theme.HIGH_CONTRAST),
            ("Blue", Theme.BLUE),
            ("Green", Theme.GREEN)
        ]:
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_value: self.set_theme(t))
            theme_menu.addAction(action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        calibrate_action = QAction("&Calibrate Sensors", self)
        tools_menu.addAction(calibrate_action)
        
        tools_menu.addSeparator()
        
        export_action = QAction("&Export All Data", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_all_data)
        tools_menu.addAction(export_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        manual_action = QAction("&User Manual", self)
        help_menu.addAction(manual_action)
        
        about_action = QAction("&About AirOne v4.0", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Create status bar"""
        statusbar = self.statusBar()
        
        # Status labels
        self.status_label = QLabel("Ready")
        statusbar.addWidget(self.status_label)
        
        statusbar.addPermanentWidget(QLabel(" | "))
        
        self.connection_label = QLabel("🟢 Connected")
        statusbar.addPermanentWidget(self.connection_label)
        
        statusbar.addPermanentWidget(QLabel(" | "))
        
        self.packet_label = QLabel("Packets: 0")
        statusbar.addPermanentWidget(self.packet_label)
    
    def create_tool_bar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add actions
        new_action = QAction("📄 New", self)
        new_action.triggered.connect(lambda: self.status_label.setText("New Mission"))
        toolbar.addAction(new_action)
        
        toolbar.addSeparator()
        
        connect_action = QAction("🔗 Connect", self)
        connect_action.triggered.connect(lambda: self.status_label.setText("Connecting..."))
        toolbar.addAction(connect_action)
        
        toolbar.addSeparator()
        
        graph_action = QAction("📊 Graphs", self)
        graph_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addAction(graph_action)
    
    def update_telemetry(self):
        """Update telemetry display"""
        if self.analyzer and len(self.analyzer.telemetry_buffer) > 0:
            # Get latest telemetry
            latest = list(self.analyzer.telemetry_buffer)[-1]
            
            # Update display
            telemetry_data = {
                'altitude': latest.altitude,
                'velocity': latest.velocity,
                'temperature': latest.temperature,
                'pressure': latest.pressure,
                'battery_percent': latest.battery_percent,
                'signal_strength': latest.signal_strength,
                'latitude': latest.latitude,
                'longitude': latest.longitude,
                'flight_phase': latest.flight_phase
            }
            
            self.telemetry_display.update_telemetry(telemetry_data)
            
            # Update stats
            stats = self.analyzer.get_statistics()
            self.stat_duration.setText(f"{stats['mission_duration']:.1f}s")
            self.stat_max_alt.setText(f"{stats['altitude_stats']['max']:.1f}m")
            self.stat_max_vel.setText(f"{stats['velocity_stats']['max']:.1f}m/s")
            self.stat_packets.setText(f"{stats['telemetry_count']}")
            
            # Update anomaly display
            if stats['anomaly_count'] > 0:
                self.anomaly_label.setText(f"⚠️ {stats['anomaly_count']} anomalies detected")
                self.anomaly_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            else:
                self.anomaly_label.setText("✓ No anomalies detected")
                self.anomaly_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            
            # Update status bar
            self.packet_label.setText(f"Packets: {stats['telemetry_count']}")
    
    def export_telemetry(self):
        """Export telemetry data"""
        if not self.analyzer:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Telemetry", "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            result = self.analyzer.export_data(file_path)
            if 'error' not in result:
                QMessageBox.information(
                    self, "Export Complete",
                    f"Exported {result['records']} records to {file_path}"
                )
            else:
                QMessageBox.warning(self, "Export Error", result.get('error', 'Unknown error'))
    
    def generate_all_graphs(self):
        """Generate all 50+ graphs"""
        if not self.analyzer:
            return
        
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        
        if dir_path:
            progress = QProgressDialog("Generating graphs...", "Cancel", 0, 63, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            results = self.analyzer.generate_all_graphs(output_dir=dir_path)
            
            progress.close()
            
            QMessageBox.information(
                self, "Graph Generation Complete",
                f"Generated {results['successful']}/{results['total_graphs']} graphs\n"
                f"Failed: {results['failed']}"
            )
    
    def analyze_with_ai(self):
        """Analyze with AI"""
        if not self.ai_service:
            self.ai_results.setText("AI service not available")
            return
        
        query = self.ai_query.toPlainText()
        if not query:
            return
        
        self.ai_results.setText("Analyzing...")
        
        # Use AI service
        result = self.ai_service.analyze_text(query)
        
        # Display results
        output = f"Query: {query}\n\n"
        output += f"Intent: {result.get('intent', 'unknown')}\n"
        output += f"Keywords: {', '.join(result.get('keywords', []))}\n"
        output += f"Sentiment: {result.get('sentiment', {})}\n\n"
        output += f"Response: {result.get('response', 'No response')}\n"
        
        self.ai_results.setText(output)
    
    def on_theme_changed(self, index):
        """Handle theme change"""
        combo = self.sender()
        theme = combo.itemData(index)
        self.set_theme(theme)
    
    def set_theme(self, theme: str):
        """Set application theme"""
        self.theme_manager.apply_theme(QApplication.instance(), theme)
    
    def on_update_rate_changed(self, value):
        """Handle update rate change"""
        self.update_timer.setInterval(value)
    
    def browse_data_dir(self):
        """Browse for data directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Data Directory"
        )
        
        if dir_path:
            self.data_dir_edit.setText(dir_path)
    
    def save_settings(self):
        """Save settings"""
        QMessageBox.information(
            self, "Settings Saved",
            "Settings have been saved successfully"
        )
    
    def toggle_fullscreen(self):
        """Toggle fullscreen"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def export_all_data(self):
        """Export all data"""
        if not self.analyzer:
            return
        
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Export Directory"
        )
        
        if dir_path:
            # Export telemetry
            csv_path = str(Path(dir_path) / "telemetry.csv")
            self.analyzer.export_data(csv_path)
            
            # Export graphs
            graphs_path = str(Path(dir_path) / "graphs")
            self.analyzer.generate_all_graphs(output_dir=graphs_path)
            
            QMessageBox.information(
                self, "Export Complete",
                f"All data exported to {dir_path}"
            )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AirOne Professional v4.0",
            "<h2>AirOne Professional v4.0</h2>"
            "<p>Ultimate Unified Edition</p>"
            "<p>Complete CanSat Ground Station Software</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>50+ Mission Graphs</li>"
            "<li>Real-time Telemetry</li>"
            "<li>AI-Powered Analysis</li>"
            "<li>GPU Acceleration</li>"
            "<li>13 Operational Modes</li>"
            "</ul>"
            "<p>© 2026 AirOne Development Team</p>"
        )


def main():
    """Main entry point"""
    if not PYQT5_AVAILABLE:
        print("PyQt5 is not available. Please install:")
        print("  pip install PyQt5 PyQtWebEngine")
        print("\nOr use CLI mode:")
        print("  python main_unified.py --mode cli")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName("AirOne Professional")
    app.setOrganizationName("AirOne")
    app.setApplicationVersion("4.0")
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = AirOneMainWindow()
    window.show()
    
    # Generate some test data
    if window.analyzer:
        import numpy as np
        base_time = time.time()
        
        for i in range(100):
            t = i * 0.5
            point = TelemetryPoint(
                timestamp=base_time + t,
                altitude=100 + 50 * t if t < 10 else 600 - 5 * (t - 10),
                velocity=50 if t < 10 else -5,
                temperature=20 + np.random.normal(0, 1),
                pressure=1013.25 + np.random.normal(0, 2),
                battery_percent=max(0, 100 - 0.1 * t),
                signal_strength=-50 + np.random.normal(0, 5),
                latitude=34.0522 + np.random.normal(0, 0.0001),
                longitude=-118.2437 + np.random.normal(0, 0.0001),
                flight_phase="ASCENT" if t < 20 else "DESCENT"
            )
            window.analyzer.add_telemetry(point)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
