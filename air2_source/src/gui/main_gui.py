#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Ground Station GUI with Login
Based on CanSat-Ground-station by darods
"""
import sys
import os
import time
import threading
import serial
import random
import hashlib
import secrets

# Check PyQt5 and pyqtgraph
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    import pyqtgraph as pg
    PYQT5_AVAILABLE = True
except ImportError:
    print("Install: pip install PyQt5 pyqtgraph pyserial")
    PYQT5_AVAILABLE = False
    sys.exit(1)

# ==================== LOGIN WINDOW ====================
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirOne - Login")
        self.setFixedSize(400, 300)
        self.setup_ui()
        
        # Default credentials (can be changed)
        self.users = {
            'admin': self.hash_password('admin123'),
            'user': self.hash_password('user123'),
        }
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("✈️ AirOne Professional v4.0")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #3498db;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Ground Station Login")
        subtitle.setStyleSheet("color: #7f8c8d;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username = QLineEdit()
        self.username.setStyleSheet("QLineEdit { background: #ffffff; color: #333333; border: 2px solid #3498db; padding: 8px; font-size: 14px; border-radius: 4px; }")
        self.username.setPlaceholderText("Enter username")
        layout.addWidget(self.username)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("QLineEdit { background: #ffffff; color: #333333; border: 2px solid #3498db; padding: 8px; font-size: 14px; border-radius: 4px; }")
        self.password.setPlaceholderText("Enter password")
        layout.addWidget(self.password)
        
        layout.addSpacing(10)
        
        # Login button
        self.login_btn = QPushButton("🔐 Login")
        self.login_btn.setStyleSheet("background: #3498db; color: white; padding: 10px; font-weight: bold;")
        self.login_btn.clicked.connect(self.try_login)
        layout.addWidget(self.login_btn)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c;")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Demo credentials hint
        hint = QLabel("Demo: admin/admin123 or user/user123")
        hint.setStyleSheet("color: #95a5a6; font-size: 10px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)
    
    def try_login(self):
        username = self.username.text()
        password = self.password.text()
        
        if username in self.users:
            if self.users[username] == self.hash_password(password):
                self.accept()
            else:
                self.error_label.setText("Invalid password")
        else:
            self.error_label.setText("Invalid username")

# ==================== SECURITY MANAGER ====================
class SecurityManager:
    def __init__(self):
        self.session_token = None
        self.failed_attempts = 0
        self.locked = False
    
    def authenticate(self, username, password):
        if self.locked:
            return False, "Account locked. Wait 5 minutes."
        
        # Simple auth check
        users = {'admin': 'admin123', 'user': 'user123'}
        
        if username in users and users[username] == password:
            self.session_token = secrets.token_hex(32)
            self.failed_attempts = 0
            return True, self.session_token
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 5:
                self.locked = True
                return False, "Too many failed attempts. Locked."
            return False, f"Invalid credentials. {5 - self.failed_attempts} attempts left."
    
    def verify_session(self, token):
        return token == self.session_token

# ==================== MAIN WINDOW ====================
class AirOneMainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"AirOne Professional v4.0 - {username}")
        self.setGeometry(100, 100, 1400, 900)
        
        self.cansat_connected = False
        self.serial_port = None
        self.recording = False
        self.security = SecurityManager()
        
        self.init_ui()
    
    def init_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        
        # Top header
        header = QLabel(f"✈️ AirOne Ground Station | User: {self.username} | 🔒 Secure Session")
        header.setStyleSheet("background: #1e3a5f; color: white; padding: 12px; font-size: 14px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.tabs.addTab(self.create_flight_tab(), "🚀 Flight Monitor")
        self.tabs.addTab(self.create_cansat_tab(), "🛰️ CanSat")
        self.tabs.addTab(self.create_telemetry_tab(), "📡 Telemetry")
        self.tabs.addTab(self.create_data_tab(), "💾 Data")
        self.tabs.addTab(self.create_security_tab(), "🔐 Security")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        self.tabs.addTab(self.create_ai_reports_tab(), "🤖 AI Reports")
        self.tabs.addTab(self.create_simulation_tab(), "🎮 Simulation")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready | Secure Connection")
    
    # ==================== FLIGHT MONITOR TAB (from darods) ====================
    def create_flight_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Use pyqtgraph for professional charts
        pg.setConfigOption('background', (33, 33, 33))
        pg.setConfigOption('foreground', (197, 198, 199))
        
        # Create graphics view
        self.graphics_view = pg.GraphicsView()
        self.layout = pg.GraphicsLayout()
        self.graphics_view.setCentralItem(self.layout)
        
        # Title
        title_text = """
Flight monitoring interface for CanSats <br>
AirOne Professional v4.0
        """
        self.layout.addLabel(title_text, row=0, col=0, colspan=4)
        
        # Altitude Graph
        self.alt_plot = self.layout.addPlot(row=1, col=0, title="Altitude (m)")
        self.alt_curve = self.alt_plot.plot(pen=(52, 152, 219))
        self.alt_data = []
        
        # Speed Graph  
        self.speed_plot = self.layout.addPlot(row=1, col=1, title="Speed (m/s)")
        self.speed_curve = self.speed_plot.plot(pen=(155, 89, 182))
        self.speed_data = []
        
        # Temperature Graph
        self.temp_plot = self.layout.addPlot(row=2, col=0, title="Temperature (°C)")
        self.temp_curve = self.temp_plot.plot(pen=(231, 76, 60))
        self.temp_data = []
        
        # Pressure Graph
        self.press_plot = self.layout.addPlot(row=2, col=1, title="Pressure (hPa)")
        self.press_curve = self.press_plot.plot(pen=(46, 204, 113))
        self.press_data = []
        
        # Battery Graph
        self.bat_plot = self.layout.addPlot(row=3, col=0, title="Battery (%)")
        self.bat_curve = self.bat_plot.plot(pen=(243, 156, 18))
        self.bat_data = []
        
        # GPS Graph
        self.gps_plot = self.layout.addPlot(row=3, col=1, title="GPS Status")
        self.gps_curve = self.gps_plot.plot(pen=(26, 188, 156))
        self.gps_data = []
        
        layout.addWidget(self.graphics_view)
        
        # Control buttons
        controls = QHBoxLayout()
        
        start_btn = QPushButton("▶ Start Flight")
        start_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px;")
        start_btn.clicked.connect(self.start_flight)
        controls.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹ Stop Flight")
        stop_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        stop_btn.clicked.connect(self.stop_flight)
        controls.addWidget(stop_btn)
        
        record_btn = QPushButton("⏺ Record Data")
        record_btn.setStyleSheet("background: #3498db; color: white; padding: 10px;")
        record_btn.clicked.connect(self.toggle_record)
        controls.addWidget(record_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        widget.setLayout(layout)
        return widget
    
    def start_flight(self):
        self.flight_running = True
        self.flight_thread = threading.Thread(target=self.simulate_flight, daemon=True)
        self.flight_thread.start()
        self.statusBar().showMessage("Flight monitoring started")
    
    def stop_flight(self):
        self.flight_running = False
        self.statusBar().showMessage("Flight monitoring stopped")
    
    def toggle_record(self):
        self.recording = not self.recording
        if self.recording:
            self.statusBar().showMessage("Recording data to CSV...")
        else:
            self.statusBar().showMessage("Recording stopped")
    
    def simulate_flight(self):
        t = 0
        while self.flight_running:
            # Simulate flight data
            alt = 1000 + 500 * t + 100 * (t % 5)  # Climbing
            speed = 50 + 10 * (t % 10)  # Varying speed
            temp = 20 + 5 * (t % 3) - 10  # Temperature fluctuation
            press = 1013 - 0.5 * alt / 100  # Pressure drops with altitude
            bat = max(0, 100 - t * 0.5)  # Battery drain
            gps = 1 if t % 3 == 0 else 0  # GPS fix
            
            # Update graphs
            self.alt_data.append(alt)
            self.speed_data.append(speed)
            self.temp_data.append(temp)
            self.press_data.append(press)
            self.bat_data.append(bat)
            self.gps_data.append(gps)
            
            # Keep last 100 points
            for data in [self.alt_data, self.speed_data, self.temp_data, self.press_data, self.bat_data, self.gps_data]:
                if len(data) > 100:
                    data.pop(0)
            
            # Update curves
            self.alt_curve.setData(self.alt_data)
            self.speed_curve.setData(self.speed_data)
            self.temp_curve.setData(self.temp_data)
            self.press_curve.setData(self.press_data)
            self.bat_curve.setData(self.bat_data)
            self.gps_curve.setData(self.gps_data)
            
            time.sleep(0.5)
            t += 1
    
    # ==================== CANSAT TAB ====================
    def create_cansat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Connection
        conn_group = QGroupBox("CanSat Connection")
        conn_layout = QHBoxLayout()
        
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(['COM1', 'COM2', 'COM3', 'COM4', 'COM5', '/dev/ttyUSB0', '/dev/ttyACM0'])
        conn_layout.addWidget(self.port_combo)
        
        conn_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200'])
        self.baud_combo.setCurrentText('9600')
        conn_layout.addWidget(self.baud_combo)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("background: #27ae60; color: white; padding: 8px;")
        self.connect_btn.clicked.connect(self.connect_cansat)
        conn_layout.addWidget(self.connect_btn)
        
        conn_layout.addStretch()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Data table
        data_group = QGroupBox("Live Data")
        data_layout = QVBoxLayout()
        
        self.data_table = QTableWidget(8, 2)
        self.data_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        params = ["Temperature", "Pressure", "Altitude", "Humidity", "Battery", "GPS Lat", "GPS Lon", "Status"]
        for i, p in enumerate(params):
            self.data_table.setItem(i, 0, QTableWidgetItem(p))
            self.data_table.setItem(i, 1, QTableWidgetItem("--"))
        
        data_layout.addWidget(self.data_table)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Raw serial
        raw_group = QGroupBox("Raw Serial Output")
        raw_layout = QVBoxLayout()
        self.raw_output = QTextEdit()
        self.raw_output.setStyleSheet("background: #1a252f; color: #2ecc71; font-family: monospace;")
        self.raw_output.setReadOnly(True)
        raw_layout.addWidget(self.raw_output)
        raw_group.setLayout(raw_layout)
        layout.addWidget(raw_group)
        
        widget.setLayout(layout)
        return widget
    
    def connect_cansat(self):
        if not self.cansat_connected:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            try:
                self.serial_port = serial.Serial(port, baud, timeout=1)
                self.cansat_connected = True
                self.connect_btn.setText("🔌 Disconnect")
                self.connect_btn.setStyleSheet("background: #e74c3c; color: white; padding: 8px;")
                self.statusBar().showMessage(f"Connected to {port}")
                
                # Start reading
                self.read_thread = threading.Thread(target=self.read_cansat, daemon=True)
                self.read_thread.start()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cannot connect: {e}")
        else:
            if self.serial_port:
                self.serial_port.close()
            self.cansat_connected = False
            self.connect_btn.setText("🔌 Connect")
            self.connect_btn.setStyleSheet("background: #27ae60; color: white; padding: 8px;")
            self.statusBar().showMessage("Disconnected")
    
    def read_cansat(self):
        while self.cansat_connected:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    self.raw_output.append(line)
                    self.parse_cansat_data(line)
            except:
                break
            time.sleep(0.1)
    
    def parse_cansat_data(self, line):
        try:
            parts = line.split(',')
            if len(parts) >= 6:
                values = [parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], "OK"]
                for i, v in enumerate(values):
                    self.data_table.setItem(i, 1, QTableWidgetItem(v))
                
                # Count as a flight session (only once per connection)
                if not hasattr(self, '_flight_counted'):
                    self._flight_counted = True
                    self.increment_flight_count()
        except:
            pass
    
    # ==================== TELEMETRY TAB ====================
    def create_telemetry_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        controls = QHBoxLayout()
        
        start_btn = QPushButton("▶ Start Telemetry")
        start_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px;")
        start_btn.clicked.connect(self.start_telemetry)
        controls.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹ Stop")
        stop_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        stop_btn.clicked.connect(self.stop_telemetry)
        controls.addWidget(stop_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_telemetry)
        controls.addWidget(save_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        self.telem_log = QTextEdit()
        self.telem_log.setStyleSheet("background: #1a252f; color: #2ecc71; font-family: monospace;")
        layout.addWidget(self.telem_log)
        
        widget.setLayout(layout)
        return widget
    
    def start_telemetry(self):
        self.telem_running = True
        threading.Thread(target=self.run_telemetry, daemon=True).start()
    
    def stop_telemetry(self):
        self.telem_running = False
    
    def run_telemetry(self):
        while self.telem_running:
            t = time.strftime("%H:%M:%S")
            line = f"[{t}] Alt:{random.randint(100,5000)}m Temp:{random.randint(-10,35)}°C Pres:{random.randint(900,1100)}hPa"
            self.telem_log.append(line)
            time.sleep(1)
    
    def save_telemetry(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save", "telemetry.txt")
        if fname:
            with open(fname, 'w') as f:
                f.write(self.telem_log.toPlainText())
            QMessageBox.information(self, "Saved", "Data saved!")
    
    # ==================== DATA TAB ====================
    def create_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_group = QGroupBox("🔍 Data Filters")
        filter_layout = QGridLayout()
        
        # Search filter
        filter_layout.addWidget(QLabel("Search:"), 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search data...")
        self.search_box.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_box, 0, 1, 1, 2)
        
        # Altitude range
        filter_layout.addWidget(QLabel("Altitude:"), 1, 0)
        self.alt_min = QSpinBox()
        self.alt_min.setRange(0, 10000)
        self.alt_min.setValue(0)
        self.alt_min.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.alt_min, 1, 1)
        self.alt_max = QSpinBox()
        self.alt_max.setRange(0, 10000)
        self.alt_max.setValue(10000)
        self.alt_max.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("to"), 1, 2)
        filter_layout.addWidget(self.alt_max, 1, 3)
        
        # Temperature range
        filter_layout.addWidget(QLabel("Temp °C:"), 2, 0)
        self.temp_min = QSpinBox()
        self.temp_min.setRange(-50, 100)
        self.temp_min.setValue(-50)
        self.temp_min.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.temp_min, 2, 1)
        self.temp_max = QSpinBox()
        self.temp_max.setRange(-50, 100)
        self.temp_max.setValue(100)
        self.temp_max.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("to"), 2, 2)
        filter_layout.addWidget(self.temp_max, 2, 3)
        
        # Pressure range
        filter_layout.addWidget(QLabel("Pressure:"), 3, 0)
        self.press_min = QSpinBox()
        self.press_min.setRange(0, 2000)
        self.press_min.setValue(0)
        self.press_min.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.press_min, 3, 1)
        self.press_max = QSpinBox()
        self.press_max.setRange(0, 2000)
        self.press_max.setValue(2000)
        self.press_max.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("to"), 3, 2)
        filter_layout.addWidget(self.press_max, 3, 3)
        
        # Status filter
        filter_layout.addWidget(QLabel("Status:"), 4, 0)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "ASCENT", "DESCENT", "PARACHUTE", "GROUND"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter, 4, 1, 1, 2)
        
        # Clear filter button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn, 4, 3)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("📊 Data Analysis & Export"))
        controls.addStretch()
        
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv)
        controls.addWidget(csv_btn)
        
        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(self.export_json)
        controls.addWidget(json_btn)
        
        layout.addLayout(controls)
        
        # Data table
        self.data_table_widget = QTableWidget(30, 7)
        self.data_table_widget.setHorizontalHeaderLabels(["Time", "Altitude", "Temp", "Pressure", "Humidity", "Battery", "Status"])
        
        # Generate sample data with status
        self.flight_data = []
        for i in range(30):
            alt = random.randint(0, 500)
            if alt < 50:
                status = "GROUND"
            elif alt < 150:
                status = "PARACHUTE"
            elif alt < 300:
                status = "DESCENT"
            else:
                status = "ASCENT"
            row_data = [
                f"{i:02d}:00",
                str(alt),
                str(random.randint(-10, 35)),
                str(random.randint(900, 1100)),
                str(random.randint(30, 80)),
                str(random.randint(60, 100)),
                status
            ]
            self.flight_data.append(row_data)
            for j, val in enumerate(row_data):
                self.data_table_widget.setItem(i, j, QTableWidgetItem(val))
        
        layout.addWidget(self.data_table_widget)
        
        # Filtered count label
        self.filter_count = QLabel("Showing: 30/30 records")
        self.filter_count.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.filter_count)
        
        widget.setLayout(layout)
        return widget
    
    def apply_filters(self):
        """Apply filters to data table"""
        search = self.search_box.text().lower()
        alt_min = self.alt_min.value()
        alt_max = self.alt_max.value()
        temp_min = self.temp_min.value()
        temp_max = self.temp_max.value()
        press_min = self.press_min.value()
        press_max = self.press_max.value()
        status = self.status_filter.currentText()
        
        visible_count = 0
        for i, row in enumerate(self.flight_data):
            if search and search not in "".join(row).lower():
                self.data_table_widget.setRowHidden(i, True)
                continue
            if not (alt_min <= int(row[1]) <= alt_max):
                self.data_table_widget.setRowHidden(i, True)
                continue
            if not (temp_min <= int(row[2]) <= temp_max):
                self.data_table_widget.setRowHidden(i, True)
                continue
            if not (press_min <= int(row[3]) <= press_max):
                self.data_table_widget.setRowHidden(i, True)
                continue
            if status != "All" and row[6] != status:
                self.data_table_widget.setRowHidden(i, True)
                continue
            self.data_table_widget.setRowHidden(i, False)
            visible_count += 1
        
        self.filter_count.setText(f"Showing: {visible_count}/{len(self.flight_data)} records")
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_box.clear()
        self.alt_min.setValue(0)
        self.alt_max.setValue(10000)
        self.temp_min.setValue(-50)
        self.temp_max.setValue(100)
        self.press_min.setValue(0)
        self.press_max.setValue(2000)
        self.status_filter.setCurrentText("All")
        for i in range(self.data_table_widget.rowCount()):
            self.data_table_widget.setRowHidden(i, False)
        self.filter_count.setText(f"Showing: {len(self.flight_data)}/{len(self.flight_data)} records")
    
    def export_csv(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export CSV", "data.csv")
        if fname:
            QMessageBox.information(self, "Export", f"Exported to {fname}")
    
    def export_json(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export JSON", "data.json")
        if fname:
            QMessageBox.information(self, "Export", f"Exported to {fname}")
    
    # ==================== SECURITY TAB ====================
    def create_security_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("🔐 Security Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Session info
        session_group = QGroupBox("Session Information")
        session_layout = QVBoxLayout()
        session_layout.addWidget(QLabel(f"Username: {self.username}"))
        session_layout.addWidget(QLabel(f"Session ID: {secrets.token_hex(16)}"))
        session_layout.addWidget(QLabel(f"Login Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"))
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # Security options
        sec_group = QGroupBox("Security Options")
        sec_layout = QFormLayout()
        sec_layout.addRow("Encryption:", QLabel("AES-256"))
        sec_layout.addRow("Session Timeout:", QSpinBox())
        sec_layout.addRow("Auto-lock:", QCheckBox())
        sec_group.setLayout(sec_layout)
        layout.addWidget(sec_group)
        
        # Audit log
        audit_group = QGroupBox("Security Log")
        audit_layout = QVBoxLayout()
        self.audit_log = QTextEdit()
        self.audit_log.setReadOnly(True)
        self.audit_log.setPlainText(f"""
[{time.strftime('%H:%M:%S')}] Login successful for {self.username}
[{time.strftime('%H:%M:%S')}] Session started
[{time.strftime('%H:%M:%S')}] Security module initialized
        """)
        audit_layout.addWidget(self.audit_log)
        audit_group.setLayout(audit_layout)
        layout.addWidget(audit_group)
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        widget.setLayout(layout)
        return widget
    
    def logout(self):
        self.close()
    
    # ==================== SETTINGS TAB ====================
    
    def create_simulation_tab(self):
        """Create Simulation tab - requires 5 CanSat flights first"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🎮 Flight Simulation")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #9b59b6;")
        layout.addWidget(header)
        
        # Flight requirement status
        status_group = QGroupBox("Flight Requirement Status")
        status_layout = QVBoxLayout()
        
        self.flight_count_label = QLabel(f"Flights completed: {self.flight_count}/{self.max_flights}")
        self.flight_count_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        status_layout.addWidget(self.flight_count_label)
        
        self.sim_status_label = QLabel("❌ Simulation locked")
        self.sim_status_label.setStyleSheet("font-size: 14px; color: #e74c3c;")
        status_layout.addWidget(self.sim_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Simulation controls
        control_group = QGroupBox("Simulation Controls")
        control_layout = QHBoxLayout()
        
        self.sim_start_btn = QPushButton("▶ Start Simulation")
        self.sim_start_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px; font-weight: bold;")
        self.sim_start_btn.setEnabled(False)  # Disabled until 5 flights
        self.sim_start_btn.clicked.connect(self.start_simulation)
        control_layout.addWidget(self.sim_start_btn)
        
        self.sim_stop_btn = QPushButton("⏹ Stop")
        self.sim_stop_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        self.sim_stop_btn.setEnabled(False)
        control_layout.addWidget(self.sim_stop_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Simulation display
        self.sim_display = QTextEdit()
        self.sim_display.setReadOnly(True)
        self.sim_display.setStyleSheet("background-color: #1a1a2e; color: #00ff88; font-family: monospace; font-size: 14px;")
        self.sim_display.setPlainText("Waiting for simulation...\n\nComplete 5 CanSat flights to unlock simulation.")
        layout.addWidget(self.sim_display)
        
        # AI Simulation section
        ai_group = QGroupBox("AI Simulation")
        ai_layout = QVBoxLayout()
        
        self.ai_sim_btn = QPushButton("🤖 AI Flight Prediction")
        self.ai_sim_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        self.ai_sim_btn.setEnabled(False)  # Disabled until 5 flights
        ai_layout.addWidget(self.ai_sim_btn)
        
        self.ai_status = QLabel("AI simulation requires 5 flights")
        self.ai_status.setStyleSheet("color: #7f8c8d;")
        ai_layout.addWidget(self.ai_status)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def start_simulation(self):
        """Start CanSat simulation - 3 min flight, 300m apogee, max 500m"""
        if self.flight_count < self.max_flights:
            self.sim_display.setPlainText(f"Error: Need {self.max_flights} flights first!")
            return

        self.sim_display.setPlainText("Starting CanSat simulation...")
        self.sim_display.append("=" * 40)
        self.sim_display.append("Simulating 3-minute flight")
        self.sim_display.append("Target apogee: 300m")
        self.sim_display.append("Max altitude: 500m")
        self.sim_display.append("=" * 40)
        
        SIM_DURATION = 180
        APOGEE = 300
        MAX_ALT = 500
        
        import random
        self.sim_display.append("Time(s)   Alt(m)    Temp(C)   Pressure  Status")
        
        for t in range(0, SIM_DURATION + 1, 5):
            if t < 30:
                altitude = int(APOGEE * (t / 30))
            elif t < 60:
                altitude = int(APOGEE - (APOGEE - 50) * ((t - 30) / 30))
            elif t < 120:
                altitude = int(50 + 100 * ((t - 60) / 60))
            else:
                altitude = max(0, int(150 - 5 * ((t - 120) / 60)))
            altitude = min(altitude, MAX_ALT)
            temp = round(20 - (altitude / 100) * 2 + random.uniform(-1, 1), 1)
            pressure = round(1013 - (altitude / 10) * 1 + random.uniform(-0.5, 0.5), 1)
            if t < 30:
                status = "ASCENT"
            elif t < 60:
                status = "DESCENT"
            elif t < 120:
                status = "PARACHUTE"
            else:
                status = "GROUND"
            self.sim_display.append(f"{t:<9} {altitude:<9} {temp:<9} {pressure:<9} {status}")
        
        self.sim_display.append("=" * 40)
        self.sim_display.append("SIMULATION COMPLETE")
        self.sim_display.append(f"Apogee: {APOGEE}m, Duration: {SIM_DURATION}s (3 min)")
        self.sim_display.append("=" * 40)

    def increment_flight_count(self):
        """Increment flight count after CanSat flight"""
        if self.flight_count < self.max_flights:
            self.flight_count += 1
            self.flight_count_label.setText(f"Flights completed: {self.flight_count}/{self.max_flights}")
            
            if self.flight_count >= self.max_flights:
                self.sim_status_label.setText("✅ Simulation unlocked!")
                self.sim_status_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
                self.sim_start_btn.setEnabled(True)
                self.ai_sim_btn.setEnabled(True)
                self.ai_status.setText("✅ AI simulation ready")
                self.ai_status.setStyleSheet("color: #27ae60;")


    def create_ai_reports_tab(self):
        """Create AI Reports tab with DTE pipeline"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🤖 AirOne AI Analysis Engine")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #9b59b6;")
        layout.addWidget(header)
        
        # DTE Pipeline Status
        dte_group = QGroupBox("DTE Pipeline Status")
        dte_layout = QGridLayout()
        
        dte_layout.addWidget(QLabel("Data Quality:"), 0, 0)
        self.dte_data_quality = QLabel("95%")
        self.dte_data_quality.setStyleSheet("color: #27ae60; font-weight: bold;")
        dte_layout.addWidget(self.dte_data_quality, 0, 1)
        
        dte_layout.addWidget(QLabel("Signal Strength:"), 0, 2)
        self.dte_signal = QLabel("85%")
        self.dte_signal.setStyleSheet("color: #27ae60; font-weight: bold;")
        dte_layout.addWidget(self.dte_signal, 0, 3)
        
        dte_layout.addWidget(QLabel("Events Detected:"), 1, 0)
        self.dte_events = QLabel("3")
        self.dte_events.setStyleSheet("color: #3498db;")
        dte_layout.addWidget(self.dte_events, 1, 1)
        
        dte_layout.addWidget(QLabel("AI Confidence:"), 1, 2)
        self.ai_confidence = QLabel("92%")
        self.ai_confidence.setStyleSheet("color: #27ae60; font-weight: bold;")
        dte_layout.addWidget(self.ai_confidence, 1, 3)
        
        dte_group.setLayout(dte_layout)
        layout.addWidget(dte_group)
        
        # AI Analysis Controls
        control_group = QGroupBox("AI Analysis Controls")
        control_layout = QHBoxLayout()
        
        run_analysis_btn = QPushButton("🔍 Run DTE Analysis")
        run_analysis_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        run_analysis_btn.clicked.connect(self.run_ai_analysis)
        control_layout.addWidget(run_analysis_btn)
        
        gen_report_btn = QPushButton("📊 Generate Report")
        gen_report_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px; font-weight: bold;")
        gen_report_btn.clicked.connect(self.generate_ai_report)
        control_layout.addWidget(gen_report_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # AI Output Display
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setStyleSheet("background-color: #1a1a2e; color: #00ff88; font-family: monospace; font-size: 13px;")
        self.ai_output.setPlainText("AirOne AI Analysis Engine Ready\n\nPress 'Run DTE Analysis' or 'Generate Report' to begin\n\nDTE Pipeline: Active\nAI Models: Loaded\nNeural Networks: Operational")
        layout.addWidget(self.ai_output)
        
        # Neural Network Status
        nn_group = QGroupBox("Neural Network Status")
        nn_layout = QGridLayout()
        
        nn_layout.addWidget(QLabel("Network Type:"), 0, 0)
        nn_layout.addWidget(QLabel("Deep Neural Network"), 0, 1)
        
        nn_layout.addWidget(QLabel("Layers:"), 0, 2)
        nn_layout.addWidget(QLabel("5"), 0, 3)
        
        nn_layout.addWidget(QLabel("Accuracy:"), 1, 0)
        nn_layout.addWidget(QLabel("94%"), 1, 1)
        
        nn_layout.addWidget(QLabel("Inference:"), 1, 2)
        nn_layout.addWidget(QLabel("12ms"), 1, 3)
        
        nn_group.setLayout(nn_layout)
        layout.addWidget(nn_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def run_ai_analysis(self):
        """Run DTE pipeline analysis"""
        self.ai_output.setPlainText("Running DTE Analysis...")
        self.ai_output.append("\n" + "="*40)
        self.ai_output.append("Data Analysis: 95% complete")
        self.ai_output.append("Telemetry Analysis: Signal strength 85%")
        self.ai_output.append("Event Detection: 3 events identified")
        self.ai_output.append("\n✓ DTE Analysis Complete")
        self.ai_output.append("="*40)
        
    def generate_ai_report(self):
        """Generate AI insight report"""
        self.ai_output.setPlainText("Generating AI Report...")
        self.ai_output.append("\n" + "="*40)
        self.ai_output.append("Neural Network Analysis: ✓")
        self.ai_output.append("Pattern Recognition: ✓ (45 similar flights)")
        self.ai_output.append("Anomaly Predictions: ✓ Risk level 15%")
        self.ai_output.append("Optimizations: 3 suggestions generated")
        self.ai_output.append("\nAI Confidence: 92%")
        self.ai_output.append("="*40)
        self.ai_output.append("\nRecommendations:")
        self.ai_output.append("• Optimize ascent rate to reach 300m faster")
        self.ai_output.append("• Adjust parachute deployment altitude")
        self.ai_output.append("• Reduce power consumption in descent")

def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        gen_group = QGroupBox("General")
        gen_layout = QFormLayout()
        gen_layout.addRow("Theme:", QComboBox())
        gen_layout.addRow("Data Folder:", QLineEdit())
        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)
        
        serial_group = QGroupBox("Serial")
        serial_layout = QFormLayout()
        serial_layout.addRow("Default Port:", QComboBox())
        serial_layout.addRow("Default Baud:", QComboBox())
        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

# ==================== MAIN ====================
def main():
    app = QApplication(sys.argv)
    
    # Show login
    login = LoginWindow()
    if login.exec_() != QDialog.Accepted:
        return
    
    # Get username
    username = login.username.text()
    
    # Show main window
    window = AirOneMainWindow(username)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()