#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main GUI (PyQt5)
Multiple tabs: CanSat, Telemetry, Dashboard, Data Analysis, Serial Console, Settings
"""
import sys
import os
import time
import threading
import serial
import random

# Check PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtChart import *
    PYQT5_AVAILABLE = True
except ImportError:
    print("PyQt5 not installed. Run: pip install PyQt5")
    PYQT5_AVAILABLE = False

if not PYQT5_AVAILABLE:
    sys.exit(1)

class AirOneGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirOne Professional v4.0")
        self.setGeometry(100, 100, 1400, 900)
        self.cansat_connected = False
        self.serial_port = None
        self.telemetry_data = []
        self.init_ui()
    
    def init_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        
        # Top header
        header = QLabel("✈️ AirOne Professional v4.0 - CanSat Ground Station")
        header.setStyleSheet("background: #1e3a5f; color: white; padding: 15px; font-size: 18px; font-weight: bold;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 10px; }")
        
        # Create tabs
        self.tabs.addTab(self.create_dashboard_tab(), "📊 Dashboard")
        self.tabs.addTab(self.create_cansat_tab(), "🛰️ CanSat")
        self.tabs.addTab(self.create_telemetry_tab(), "📡 Telemetry")
        self.tabs.addTab(self.create_console_tab(), "💻 Console")
        self.tabs.addTab(self.create_data_tab(), "📈 Data")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        self.tabs.addTab(self.create_about_tab(), "ℹ️ About")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready - Connect CanSat to begin")
    
    # ==================== DASHBOARD TAB ====================
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Status cards row
        row1 = QHBoxLayout()
        
        # Flight status card
        status_card = self.make_card("Flight Status", "READY", "#2ecc71")
        row1.addWidget(status_card)
        
        # Altitude card
        self.alt_card = self.make_card("Altitude", "0 m", "#3498db")
        row1.addWidget(self.alt_card)
        
        # Speed card
        self.speed_card = self.make_card("Speed", "0 m/s", "#9b59b6")
        row1.addWidget(self.speed_card)
        
        # Battery card
        self.bat_card = self.make_card("Battery", "100%", "#f39c12")
        row1.addWidget(self.bat_card)
        
        layout.addLayout(row1)
        
        # Charts row
        row2 = QHBoxLayout()
        
        # Altitude chart
        self.alt_chart = self.create_chart("Altitude (m)", "Time", "Altitude")
        row2.addWidget(self.alt_chart)
        
        # Temperature chart  
        self.temp_chart = self.create_chart("Temperature (°C)", "Time", "Temp")
        row2.addWidget(self.temp_chart)
        
        layout.addLayout(row2)
        
        # Bottom row
        row3 = QHBoxLayout()
        
        # Pressure
        self.press_card = self.make_card("Pressure", "1013 hPa", "#e74c3c")
        row3.addWidget(self.press_card)
        
        # GPS
        self.gps_card = self.make_card("GPS", "Searching...", "#1abc9c")
        row3.addWidget(self.gps_card)
        
        # Humidity
        self.hum_card = self.make_card("Humidity", "50%", "#34495e")
        row3.addWidget(self.hum_card)
        
        layout.addLayout(row3)
        
        widget.setLayout(layout)
        return widget
    
    def make_card(self, title, value, color):
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                background: #2c3e50;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 20px;
                font-weight: bold;
            }}
            QLabel {{
                color: {color};
                font-size: 24px;
            }}
        """)
        layout = QVBoxLayout()
        label = QLabel(value)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        card.setLayout(layout)
        return card
    
    def create_chart(self, title, xlabel, ylabel):
        group = QGroupBox(title)
        group.setStyleSheet("background: #2c3e50; border-radius: 5px;")
        layout = QVBoxLayout()
        
        # Simple chart using QLabel for now
        chart = QLabel(f"[{ylabel} vs {xlabel} Graph]")
        chart.setStyleSheet("background: #34495e; color: #ecf0f1; padding: 50px;")
        chart.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart)
        
        group.setLayout(layout)
        return group
    
    # ==================== CANSAT TAB ====================
    def create_cansat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Connection controls
        conn_group = QGroupBox("Serial Connection")
        conn_layout = QHBoxLayout()
        
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 
                                  '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1'])
        conn_layout.addWidget(self.port_combo)
        
        conn_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baud_combo.setCurrentText('9600')
        conn_layout.addWidget(self.baud_combo)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("background: #27ae60; color: white; padding: 8px;")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        
        conn_layout.addStretch()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Live data display
        data_group = QGroupBox("Live CanSat Data")
        data_layout = QVBoxLayout()
        
        # Data table
        self.data_table = QTableWidget(10, 2)
        self.data_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.data_table.setStyleSheet("background: #2c3e50; color: #ecf0f1;")
        
        params = ["Temperature", "Pressure", "Altitude", "Humidity", "Battery", 
                  "GPS Lat", "GPS Lon", "Speed", "Heading", "Timestamp"]
        for i, param in enumerate(params):
            self.data_table.setItem(i, 0, QTableWidgetItem(param))
            self.data_table.setItem(i, 1, QTableWidgetItem("--"))
        
        data_layout.addWidget(self.data_table)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Raw data display
        raw_group = QGroupBox("Raw Data Stream")
        raw_layout = QVBoxLayout()
        self.raw_text = QTextEdit()
        self.raw_text.setStyleSheet("background: #1a252f; color: #2ecc71; font-family: monospace;")
        self.raw_text.setReadOnly(True)
        raw_layout.addWidget(self.raw_text)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.raw_text.clear())
        raw_layout.addWidget(clear_btn)
        
        raw_group.setLayout(raw_layout)
        layout.addWidget(raw_group)
        
        widget.setLayout(layout)
        return widget
    
    def toggle_connection(self):
        if not self.cansat_connected:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.connect_serial(port, baud)
        else:
            self.disconnect_serial()
    
    def connect_serial(self, port, baud):
        try:
            # Try to open serial - will work if device connected
            self.serial_port = serial.Serial(port, baud, timeout=1)
            self.cansat_connected = True
            self.connect_btn.setText("🔌 Disconnect")
            self.connect_btn.setStyleSheet("background: #e74c3c; color: white; padding: 8px;")
            self.statusBar().showMessage(f"Connected to {port}")
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Could not connect to {port}:\n{e}")
    
    def disconnect_serial(self):
        if self.serial_port:
            self.serial_port.close()
        self.cansat_connected = False
        self.connect_btn.setText("🔌 Connect")
        self.connect_btn.setStyleSheet("background: #27ae60; color: white; padding: 8px;")
        self.statusBar().showMessage("Disconnected")
    
    def read_serial(self):
        while self.cansat_connected:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    self.parse_cansat_data(line)
            except:
                break
            time.sleep(0.1)
    
    def parse_cansat_data(self, line):
        # Format: T,P,A,H,B,Lat,Lon,S,Time
        self.raw_text.append(line)
        
        try:
            parts = line.split(',')
            if len(parts) >= 6:
                data = {
                    'temperature': parts[0] if len(parts) > 0 else '--',
                    'pressure': parts[1] if len(parts) > 1 else '--',
                    'altitude': parts[2] if len(parts) > 2 else '--',
                    'humidity': parts[3] if len(parts) > 3 else '--',
                    'battery': parts[4] if len(parts) > 4 else '--',
                    'lat': parts[5] if len(parts) > 5 else '--',
                }
                
                # Update table
                for i, key in enumerate(['temperature', 'pressure', 'altitude', 'humidity', 'battery']):
                    self.data_table.setItem(i, 1, QTableWidgetItem(data[key]))
        except:
            pass
    
    # ==================== TELEMETRY TAB ====================
    def create_telemetry_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        self.start_telem_btn = QPushButton("▶ Start Telemetry")
        self.start_telem_btn.setStyleSheet("background: #27ae60; color: white; padding: 10px;")
        self.start_telem_btn.clicked.connect(self.start_telemetry)
        controls.addWidget(self.start_telem_btn)
        
        self.stop_telem_btn = QPushButton("⏹ Stop")
        self.stop_telem_btn.setStyleSheet("background: #e74c3c; color: white; padding: 10px;")
        self.stop_telem_btn.clicked.connect(self.stop_telemetry)
        self.stop_telem_btn.setEnabled(False)
        controls.addWidget(self.stop_telem_btn)
        
        controls.addStretch()
        
        save_btn = QPushButton("💾 Save Data")
        save_btn.clicked.connect(self.save_telemetry)
        controls.addWidget(save_btn)
        
        layout.addLayout(controls)
        
        # Telemetry log
        self.telem_log = QTextEdit()
        self.telem_log.setStyleSheet("background: #1a252f; color: #2ecc71; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.telem_log)
        
        widget.setLayout(layout)
        return widget
    
    def start_telemetry(self):
        self.telemetry_running = True
        self.start_telem_btn.setEnabled(False)
        self.stop_telem_btn.setEnabled(True)
        self.telem_thread = threading.Thread(target=self.simulate_telemetry, daemon=True)
        self.telem_thread.start()
    
    def stop_telemetry(self):
        self.telemetry_running = False
        self.start_telem_btn.setEnabled(True)
        self.stop_telem_btn.setEnabled(False)
    
    def simulate_telemetry(self):
        # Simulate telemetry data if no CanSat connected
        import random
        while self.telemetry_running:
            t = time.strftime("%H:%M:%S")
            alt = random.randint(100, 10000)
            temp = random.randint(-20, 40)
            pres = random.randint(800, 1200)
            hum = random.randint(20, 80)
            bat = random.randint(50, 100)
            line = f"[{t}] Alt:{alt}m Temp:{temp}°C Pres:{pres}hPa Hum:{hum}% Bat:{bat}%"
            self.telem_log.append(line)
            time.sleep(1)
    
    def save_telemetry(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Telemetry", "telemetry.txt")
        if fname:
            with open(fname, 'w') as f:
                f.write(self.telem_log.toPlainText())
            QMessageBox.information(self, "Saved", f"Data saved to {fname}")
    
    # ==================== CONSOLE TAB ====================
    def create_console_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Command input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Command:"))
        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet("background: #2c3e50; color: white; padding: 8px;")
        self.cmd_input.returnPressed.connect(self.run_command)
        input_layout.addWidget(self.cmd_input)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.run_command)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setStyleSheet("background: #1a252f; color: #2ecc71; font-family: monospace;")
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)
        
        # Help text
        help_text = QLabel("Commands: connect, disconnect, status, read, monitor, calibrate, clear, help")
        help_text.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(help_text)
        
        widget.setLayout(layout)
        return widget
    
    def run_command(self):
        cmd = self.cmd_input.text().strip()
        self.console_output.append(f"> {cmd}")
        
        if cmd == 'help':
            self.console_output.append("Available commands: connect, disconnect, status, read, monitor, calibrate, clear, help")
        elif cmd == 'status':
            self.console_output.append(f"CanSat Connected: {self.cansat_connected}")
            if self.cansat_connected:
                self.console_output.append(f"Port: {self.port_combo.currentText()}")
        elif cmd == 'clear':
            self.console_output.clear()
        else:
            self.console_output.append(f"Unknown command: {cmd}")
        
        self.cmd_input.clear()
    
    # ==================== DATA TAB ====================
    def create_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Export controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Data Analysis & Export"))
        controls.addStretch()
        
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(lambda: QMessageBox.info(self, "Export", "CSV export feature"))
        controls.addWidget(csv_btn)
        
        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(lambda: QMessageBox.info(self, "Export", "JSON export feature"))
        controls.addWidget(json_btn)
        
        layout.addLayout(controls)
        
        # Data table
        self.data_analysis_table = QTableWidget(20, 6)
        self.data_analysis_table.setHorizontalHeaderLabels(["Time", "Altitude", "Temp", "Pressure", "Humidity", "Battery"])
        self.data_analysis_table.setStyleSheet("background: #2c3e50; color: #ecf0f1;")
        
        # Fill with sample data
        for i in range(20):
            self.data_analysis_table.setItem(i, 0, QTableWidgetItem(f"{i:02d}:00"))
            self.data_analysis_table.setItem(i, 1, QTableWidgetItem(str(random.randint(100, 5000))))
            self.data_analysis_table.setItem(i, 2, QTableWidgetItem(str(random.randint(-10, 35))))
            self.data_analysis_table.setItem(i, 3, QTableWidgetItem(str(random.randint(900, 1100))))
            self.data_analysis_table.setItem(i, 4, QTableWidgetItem(str(random.randint(30, 80))))
            self.data_analysis_table.setItem(i, 5, QTableWidgetItem(str(random.randint(60, 100))))
        
        layout.addWidget(self.data_analysis_table)
        
        widget.setLayout(layout)
        return widget
    
    # ==================== SETTINGS TAB ====================
    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # General settings
        gen_group = QGroupBox("General")
        gen_layout = QFormLayout()
        gen_layout.addRow("Theme:", QComboBox())
        gen_layout.addRow("Language:", QComboBox())
        gen_layout.addRow("Data Directory:", QLineEdit())
        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)
        
        # Serial settings
        serial_group = QGroupBox("Serial Port Defaults")
        serial_layout = QFormLayout()
        serial_layout.addRow("Default Port:", QComboBox())
        serial_layout.addRow("Default Baud:", QComboBox())
        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)
        
        # Data settings
        data_group = QGroupBox("Data Recording")
        data_layout = QFormLayout()
        data_layout.addRow("Auto-save:", QCheckBox())
        data_layout.addRow("Interval (sec):", QSpinBox())
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    # ==================== ABOUT TAB ====================
    def create_about_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("✈️ AirOne Professional v4.0")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("""
A comprehensive Ground Station GUI for CanSat and telemetry applications.

Features:
• Real-time CanSat communication
• Telemetry data visualization
• Serial console
• Data export (CSV, JSON)
• Multiple visualization modes

Version: 4.0
© 2024 AirOne
        """)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = AirOneGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()