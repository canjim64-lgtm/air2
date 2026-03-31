"""
AirOne Professional v4.0 - Enhanced GUI with Advanced Tabs
Complete tabbed interface with all features
"""
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    PYQT5_AVAILABLE = True
except ImportError as e:
    print(f"PyQt5 not available: {e}")
    PYQT5_AVAILABLE = False


if PYQT5_AVAILABLE:
    from gui.modern_gui_components import ModernThemeManager, Theme
    from gui.advanced_widgets import CircularGauge, StatusLED, InfoCard, ProgressBarWidget, AlertBanner
    
    class EnhancedTabbedGUI(QMainWindow):
        """Enhanced GUI with multiple advanced tabs"""
        
        def __init__(self):
            super().__init__()
            
            self.theme_manager = ModernThemeManager()
            self.init_ui()
            self.apply_theme()
            
        def init_ui(self):
            """Initialize UI"""
            self.setWindowTitle("AirOne Professional v4.0 - Enhanced Control Center")
            self.setGeometry(100, 100, 1600, 1000)
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout()
            central_widget.setLayout(main_layout)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabPosition(QTabWidget.North)
            self.tab_widget.setMovable(True)
            
            # Add all tabs
            self._create_dashboard_tab()
            self._create_telemetry_tab()
            self._create_mission_tab()
            self._create_ai_analysis_tab()
            self._create_simulation_tab()
            self._create_digital_twin_tab()
            self._create_deepseek_tab()
            self._create_reports_tab()
            self._create_system_health_tab()
            self._create_api_tab()
            self._create_settings_tab()
            
            main_layout.addWidget(self.tab_widget)
            
            # Create menu bar
            self._create_menu_bar()
            
            # Create status bar
            self._create_status_bar()
            
            # Auto-refresh timer
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._refresh_data)
            self.refresh_timer.start(2000)  # Refresh every 2 seconds
        
        def _create_dashboard_tab(self):
            """Create main dashboard tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Top row: Key metrics
            top_layout = QHBoxLayout()
            
            # Altitude gauge
            alt_gauge = CircularGauge()
            alt_gauge.setTitle("Altitude")
            alt_gauge.setUnit("m")
            alt_gauge.setRange(0, 1000)
            alt_gauge.setValue(523)
            top_layout.addWidget(alt_gauge)
            
            # Velocity gauge
            vel_gauge = CircularGauge()
            vel_gauge.setTitle("Velocity")
            vel_gauge.setUnit("m/s")
            vel_gauge.setRange(-50, 150)
            vel_gauge.setValue(25)
            top_layout.addWidget(vel_gauge)
            
            # Battery gauge
            bat_gauge = CircularGauge()
            bat_gauge.setTitle("Battery")
            bat_gauge.setUnit("%")
            bat_gauge.setRange(0, 100)
            bat_gauge.setValue(95)
            top_layout.addWidget(bat_gauge)
            
            # Signal gauge
            sig_gauge = CircularGauge()
            sig_gauge.setTitle("Signal")
            sig_gauge.setUnit("dBm")
            sig_gauge.setRange(-100, -30)
            sig_gauge.setValue(-65)
            top_layout.addWidget(sig_gauge)
            
            layout.addLayout(top_layout)
            
            # Middle row: Info cards
            cards_layout = QHBoxLayout()
            
            cards_layout.addWidget(InfoCard("Mission State", "ASCENT", "🚀"))
            cards_layout.addWidget(InfoCard("Flight Time", "2m 35s", "⏱️"))
            cards_layout.addWidget(InfoCard("Distance", "1.2 km", "📍"))
            cards_layout.addWidget(InfoCard("Packets", "1,234", "📦"))
            
            layout.addLayout(cards_layout)
            
            # Bottom: Status indicators
            status_layout = QHBoxLayout()
            status_layout.addWidget(QLabel("System Status:"))
            
            cpu_led = StatusLED()
            cpu_led.setColor("#4caf50")
            cpu_led.setState(True)
            status_layout.addWidget(cpu_led)
            status_layout.addWidget(QLabel("CPU"))
            
            mem_led = StatusLED()
            mem_led.setColor("#4caf50")
            mem_led.setState(True)
            status_layout.addWidget(mem_led)
            status_layout.addWidget(QLabel("Memory"))
            
            net_led = StatusLED()
            net_led.setColor("#4caf50")
            net_led.setState(True)
            status_layout.addWidget(net_led)
            status_layout.addWidget(QLabel("Network"))
            
            status_layout.addStretch()
            layout.addLayout(status_layout)
            
            layout.addStretch()
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "📊 Dashboard")
        
        def _create_telemetry_tab(self):
            """Create telemetry tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Telemetry table
            table = QTableWidget()
            table.setColumnCount(8)
            table.setHorizontalHeaderLabels([
                "Time", "Altitude", "Velocity", "Temperature",
                "Pressure", "Battery", "Signal", "Phase"
            ])
            table.horizontalHeader().setStretchLastSection(True)
            
            # Add sample data
            for i in range(20):
                table.insertRow(i)
                table.setItem(i, 0, QTableWidgetItem(f"12:{i:02d}:00"))
                table.setItem(i, 1, QTableWidgetItem(f"{500 + i*2:.1f}"))
                table.setItem(i, 2, QTableWidgetItem(f"{25 + i*0.5:.1f}"))
                table.setItem(i, 3, QTableWidgetItem(f"{22 - i*0.1:.1f}"))
                table.setItem(i, 4, QTableWidgetItem(f"{1013 - i:.1f}"))
                table.setItem(i, 5, QTableWidgetItem(f"{95 - i*0.2:.1f}"))
                table.setItem(i, 6, QTableWidgetItem(f"{-65 + i}"))
                table.setItem(i, 7, QTableWidgetItem("ASCENT"))
            
            layout.addWidget(table)
            
            # Export button
            export_btn = QPushButton("Export Telemetry")
            export_btn.clicked.connect(lambda: QMessageBox.information(self, "Export", "Telemetry exported successfully!"))
            layout.addWidget(export_btn)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "📈 Telemetry")
        
        def _create_mission_tab(self):
            """Create mission control tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Mission status
            status_group = QGroupBox("Mission Status")
            status_layout = QGridLayout()
            
            status_layout.addWidget(QLabel("State:"), 0, 0)
            state_label = QLabel("ASCENT")
            state_label.setStyleSheet("font-weight: bold; color: #4caf50; font-size: 16px;")
            status_layout.addWidget(state_label, 0, 1)
            
            status_layout.addWidget(QLabel("Progress:"), 1, 0)
            progress = ProgressBarWidget()
            progress.setValue(65)
            status_layout.addWidget(progress, 1, 1)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            # Command buttons
            cmd_group = QGroupBox("Commands")
            cmd_layout = QHBoxLayout()
            
            arm_btn = QPushButton("ARM")
            arm_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
            cmd_layout.addWidget(arm_btn)
            
            start_btn = QPushButton("START")
            start_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
            cmd_layout.addWidget(start_btn)
            
            abort_btn = QPushButton("ABORT")
            abort_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            cmd_layout.addWidget(abort_btn)
            
            cmd_group.setLayout(cmd_layout)
            layout.addWidget(cmd_group)
            
            # Event log
            log_group = QGroupBox("Event Log")
            log_layout = QVBoxLayout()
            
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.append("[12:00:00] Mission initialized")
            log_text.append("[12:00:15] Systems armed")
            log_text.append("[12:00:30] Launch detected")
            log_text.append("[12:01:00] Ascent phase started")
            
            log_layout.addWidget(log_text)
            log_group.setLayout(log_layout)
            layout.addWidget(log_group)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🎯 Mission Control")
        
        def _create_ai_analysis_tab(self):
            """Create AI analysis tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # AI Chat
            chat_group = QGroupBox("AI Chat Assistant")
            chat_layout = QVBoxLayout()
            
            chat_display = QTextEdit()
            chat_display.setReadOnly(True)
            chat_display.append("AI: Hello! I'm your AirOne Assistant. How can I help?")
            chat_layout.addWidget(chat_display)
            
            chat_input = QLineEdit()
            chat_input.setPlaceholderText("Type your message...")
            chat_layout.addWidget(chat_input)
            
            send_btn = QPushButton("Send")
            send_btn.clicked.connect(lambda: chat_display.append(f"User: {chat_input.text()}"))
            chat_layout.addWidget(send_btn)
            
            chat_group.setLayout(chat_layout)
            layout.addWidget(chat_group)
            
            # AI Recommendations
            rec_group = QGroupBox("AI Recommendations")
            rec_layout = QVBoxLayout()
            
            rec_list = QListWidget()
            rec_list.addItem("[INFO] High altitude achieved - monitor for apogee")
            rec_list.addItem("[WARNING] Battery at 35%% - consider ending mission")
            rec_list.addItem("[INFO] Signal strength optimal")
            
            rec_layout.addWidget(rec_list)
            rec_group.setLayout(rec_layout)
            layout.addWidget(rec_group)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🤖 AI Analysis")
        
        def _create_simulation_tab(self):
            """Create Simulation tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("🎮 Flight Simulation")
            header.setStyleSheet("font-size: 24px; font-weight: bold;")
            layout.addWidget(header)
            
            # Controls
            control_group = QGroupBox("Controls")
            control_layout = QHBoxLayout()
            
            start_btn = QPushButton("▶ Start")
            start_btn.setStyleSheet("background-color: #00ff88; padding: 8px;")
            control_layout.addWidget(start_btn)
            
            pause_btn = QPushButton("⏸ Pause")
            pause_btn.setStyleSheet("background-color: #ff9800; padding: 8px;")
            control_layout.addWidget(pause_btn)
            
            stop_btn = QPushButton("⏹ Stop")
            stop_btn.setStyleSheet("background-color: #f44336; color: #fff; padding: 8px;")
            control_layout.addWidget(stop_btn)
            
            control_layout.addStretch()
            control_group.setLayout(control_layout)
            layout.addWidget(control_group)
            
            # Display
            sim_display = QTextEdit()
            sim_display.setReadOnly(True)
            sim_display.setStyleSheet("background-color: #1e1e1e; color: #00ff88; font-family: monospace;")
            sim_display.setPlainText("Waiting for simulation...\n\nAltitude: 0 m\nSpeed: 0 m/s")
            layout.addWidget(sim_display)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🎮 Simulation")
        
        def _create_digital_twin_tab(self):
            """Create Digital Twin tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("🔄 Digital Twin Engine")
            header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00bcd4;")
            layout.addWidget(header)
            
            # Twin Status
            status_group = QGroupBox("Twin Status")
            status_layout = QGridLayout()
            
            status_layout.addWidget(QLabel("Sync:"), 0, 0)
            sync_label = QLabel("● Synced")
            sync_label.setStyleSheet("color: #00ff88; font-weight: bold;")
            status_layout.addWidget(sync_label, 0, 1)
            
            status_layout.addWidget(QLabel("Objects:"), 1, 0)
            status_layout.addWidget(QLabel("5 active"), 1, 1)
            
            status_layout.addWidget(QLabel("Update Rate:"), 2, 0)
            status_layout.addWidget(QLabel("10 Hz"), 2, 1)
            
            status_layout.addWidget(QLabel("Latency:"), 3, 0)
            status_layout.addWidget(QLabel("12ms"), 3, 1)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            # Model Selection
            model_group = QGroupBox("Digital Twin Models")
            model_layout = QVBoxLayout()
            
            self.vehicle_cb = QCheckBox("Vehicle Model")
            self.vehicle_cb.setChecked(True)
            model_layout.addWidget(self.vehicle_cb)
            
            self.env_cb = QCheckBox("Environment Model")
            self.env_cb.setChecked(True)
            model_layout.addWidget(self.env_cb)
            
            self.sensor_cb = QCheckBox("Sensor Array Model")
            self.sensor_cb.setChecked(True)
            model_layout.addWidget(self.sensor_cb)
            
            self.power_cb = QCheckBox("Power System Model")
            self.power_cb.setChecked(True)
            model_layout.addWidget(self.power_cb)
            
            self.nav_cb = QCheckBox("Navigation Model")
            self.nav_cb.setChecked(True)
            model_layout.addWidget(self.nav_cb)
            
            model_group.setLayout(model_layout)
            layout.addWidget(model_group)
            
            # AI Features
            ai_group = QGroupBox("AI Enhancements")
            ai_layout = QVBoxLayout()
            
            self.ai_predict_cb = QCheckBox("Trajectory Prediction")
            self.ai_predict_cb.setChecked(True)
            ai_layout.addWidget(self.ai_predict_cb)
            
            self.ai_anomaly_cb = QCheckBox("Anomaly Detection")
            self.ai_anomaly_cb.setChecked(True)
            ai_layout.addWidget(self.ai_anomaly_cb)
            
            self.ai_optimize_cb = QCheckBox("Optimization")
            self.ai_optimize_cb.setChecked(True)
            ai_layout.addWidget(self.ai_optimize_cb)
            
            ai_group.setLayout(ai_layout)
            layout.addWidget(ai_group)
            
            # Real-time Data
            data_group = QGroupBox("Real-time Data Stream")
            data_layout = QVBoxLayout()
            self.twin_data = QTextEdit()
            self.twin_data.setReadOnly(True)
            self.twin_data.setStyleSheet("background-color: #1e1e1e; color: #00bcd4; font-family: monospace; font-size: 12px;")
            self.twin_data.setPlainText("Digital Twin Data Stream:\n\n[12:00:00] Vehicle: Alt=120m, Speed=15m/s\n[12:00:00] Sensors: GPS OK, IMU OK, BARO OK\n[12:00:00] Power: 85%\n[12:00:00] Environment: Wind=5m/s, Temp=22C")
            data_layout.addWidget(self.twin_data)
            data_group.setLayout(data_layout)
            layout.addWidget(data_group)
            
            # Control buttons
            twin_btn_layout = QHBoxLayout()
            sync_btn = QPushButton("🔄 Sync Now")
            sync_btn.setStyleSheet("background-color: #00bcd4; color: #000; padding: 10px;")
            twin_btn_layout.addWidget(sync_btn)
            
            reset_btn = QPushButton("🔄 Reset Twin")
            reset_btn.setStyleSheet("background-color: #ff9800; color: #000; padding: 10px;")
            twin_btn_layout.addWidget(reset_btn)
            
            export_btn = QPushButton("📤 Export")
            export_btn.setStyleSheet("background-color: #9c27b0; color: #fff; padding: 10px;")
            twin_btn_layout.addWidget(export_btn)
            
            twin_btn_layout.addStretch()
            layout.addLayout(twin_btn_layout)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🔄 Digital Twin")
        
        def _create_system_health_tab(self):
            """Create system health tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Health score
            health_group = QGroupBox("Overall Health")
            health_layout = QHBoxLayout()
            
            health_score = QLabel("85/100")
            health_score.setStyleSheet("font-size: 48px; font-weight: bold; color: #4caf50;")
            health_layout.addWidget(health_score)
            
            health_layout.addWidget(QLabel("""
                <div style='font-size: 14px;'>
                    <p>✓ CPU: OK (35%%)</p>
                    <p>✓ Memory: OK (52%%)</p>
                    <p>✓ Disk: OK (45%%)</p>
                    <p>✓ Network: OK</p>
                </div>
            """))
            
            health_group.setLayout(health_layout)
            layout.addWidget(health_group)
            
            # Resource usage
            resource_group = QGroupBox("Resource Usage")
            resource_layout = QVBoxLayout()
            
            cpu_bar = ProgressBarWidget()
            cpu_bar.setValue(35)
            resource_layout.addWidget(QLabel("CPU"))
            resource_layout.addWidget(cpu_bar)
            
            mem_bar = ProgressBarWidget()
            mem_bar.setValue(52)
            resource_layout.addWidget(QLabel("Memory"))
            resource_layout.addWidget(mem_bar)
            
            disk_bar = ProgressBarWidget()
            disk_bar.setValue(45)
            resource_layout.addWidget(QLabel("Disk"))
            resource_layout.addWidget(disk_bar)
            
            resource_group.setLayout(resource_layout)
            layout.addWidget(resource_group)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "💻 System Health")
        
        def _create_api_tab(self):
            """Create API tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # API Status
            status_group = QGroupBox("API Server Status")
            status_layout = QGridLayout()
            
            status_layout.addWidget(QLabel("Server:"), 0, 0)
            server_label = QLabel("● Running")
            server_label.setStyleSheet("color: #00ff88; font-weight: bold;")
            status_layout.addWidget(server_label, 0, 1)
            
            status_layout.addWidget(QLabel("Port:"), 1, 0)
            status_layout.addWidget(QLabel("5001"), 1, 1)
            
            status_layout.addWidget(QLabel("Endpoints:"), 2, 0)
            status_layout.addWidget(QLabel("15 active"), 2, 1)
            
            status_layout.addWidget(QLabel("Requests:"), 3, 0)
            status_layout.addWidget(QLabel("1,234 today"), 3, 1)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)
            
            # Quick Actions
            action_group = QGroupBox("Quick Actions")
            action_layout = QHBoxLayout()
            
            start_api_btn = QPushButton("Start API")
            start_api_btn.setStyleSheet("background-color: #00ff88; color: #000; padding: 8px;")
            action_layout.addWidget(start_api_btn)
            
            stop_api_btn = QPushButton("Stop API")
            stop_api_btn.setStyleSheet("background-color: #f44336; color: #fff; padding: 8px;")
            action_layout.addWidget(stop_api_btn)
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.setStyleSheet("background-color: #2196F3; color: #fff; padding: 8px;")
            action_layout.addWidget(refresh_btn)
            
            action_layout.addStretch()
            action_group.setLayout(action_layout)
            layout.addWidget(action_group)
            
            # API Endpoints
            endpoints_group = QGroupBox("API Endpoints")
            endpoints_layout = QVBoxLayout()
            
            # GET endpoints
            get_label = QLabel("GET Endpoints:")
            get_label.setStyleSheet("font-weight: bold;")
            endpoints_layout.addWidget(get_label)
            
            endpoints_list = QListWidget()
            endpoints_list.addItem("GET  /api/health          - Health check")
            endpoints_list.addItem("GET  /api/status          - System status")
            endpoints_list.addItem("GET  /api/telemetry       - Get telemetry")
            endpoints_list.addItem("GET  /api/missions        - List missions")
            endpoints_list.addItem("GET  /api/users           - Get users")
            endpoints_list.addItem("GET  /api/logs            - Get logs")
            endpoints_list.addItem("GET  /api/config          - Get config")
            endpoints_layout.addWidget(endpoints_list)
            
            # POST endpoints
            post_label = QLabel("POST Endpoints:")
            post_label.setStyleSheet("font-weight: bold;")
            endpoints_layout.addWidget(post_label)
            
            post_list = QListWidget()
            post_list.addItem("POST /api/missions        - Create mission")
            post_list.addItem("POST /api/commands        - Execute command")
            post_list.addItem("POST /api/telemetry       - Post telemetry")
            post_list.addItem("POST /api/export          - Export data")
            endpoints_layout.addWidget(post_list)
            
            endpoints_group.setLayout(endpoints_layout)
            layout.addWidget(endpoints_group)
            
            # API Test
            test_group = QGroupBox("API Test")
            test_layout = QHBoxLayout()
            
            test_layout.addWidget(QLabel("Endpoint:"))
            test_input = QLineEdit()
            test_input.setText("/api/health")
            test_layout.addWidget(test_input)
            
            test_btn = QPushButton("Test")
            test_btn.setStyleSheet("background-color: #9c27b0; color: #fff; padding: 8px;")
            test_layout.addWidget(test_btn)
            
            test_group.setLayout(test_layout)
            layout.addWidget(test_group)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🔌 API Gateway")
        
        def _create_deepseek_tab(self):
            """Create DeepSeek AI tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("🤖 DeepSeek R1 8B INT")
            header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff88;")
            layout.addWidget(header)
            
            # Status
            status_layout = QHBoxLayout()
            status_layout.addWidget(QLabel("Status:"))
            status_label = QLabel("● Ready")
            status_label.setStyleSheet("color: #00ff88; font-weight: bold;")
            status_layout.addWidget(status_label)
            status_layout.addStretch()
            layout.addLayout(status_layout)
            
            # Chat area
            chat_group = QGroupBox("AI Assistant")
            chat_layout = QVBoxLayout()
            
            chat_layout.addWidget(QLabel("Query:"))
            query_input = QTextEdit()
            query_input.setPlaceholderText("Ask DeepSeek anything...")
            query_input.setMaximumHeight(80)
            chat_layout.addWidget(query_input)
            
            chat_layout.addWidget(QLabel("Response:"))
            response_text = QTextEdit()
            response_text.setReadOnly(True)
            response_text.setStyleSheet("background-color: #1e1e1e; color: #00ff88;")
            response_text.setMaximumHeight(150)
            chat_layout.addWidget(response_text)
            
            btn_layout = QHBoxLayout()
            query_btn = QPushButton("Ask DeepSeek")
            query_btn.setStyleSheet("background-color: #00ff88; color: #000; padding: 8px;")
            btn_layout.addWidget(query_btn)
            btn_layout.addStretch()
            chat_layout.addLayout(btn_layout)
            
            chat_group.setLayout(chat_layout)
            layout.addWidget(chat_group)
            
            # Info
            info = QLabel("DeepSeek R1: Advanced AI with reasoning capabilities")
            info.setStyleSheet("color: #888;")
            layout.addWidget(info)
            layout.addStretch()
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "🧠 DeepSeek")
        
        def _create_reports_tab(self):
            """Create Reports tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Header
            header = QLabel("📊 Report Generation")
            header.setStyleSheet("font-size: 24px; font-weight: bold;")
            layout.addWidget(header)
            
            # Report type selection
            type_group = QGroupBox("Report Type")
            type_layout = QVBoxLayout()
            
            self.flight_report_cb = QCheckBox("Flight Report")
            self.flight_report_cb.setChecked(True)
            type_layout.addWidget(self.flight_report_cb)
            
            self.mission_report_cb = QCheckBox("Mission Summary")
            type_layout.addWidget(self.mission_report_cb)
            
            self.health_report_cb = QCheckBox("System Health")
            type_layout.addWidget(self.health_report_cb)
            
            self.security_report_cb = QCheckBox("Security Audit")
            type_layout.addWidget(self.security_report_cb)
            
            self.perf_report_cb = QCheckBox("Performance Analysis")
            type_layout.addWidget(self.perf_report_cb)
            
            type_group.setLayout(type_layout)
            layout.addWidget(type_group)
            
            # Generate button
            gen_btn = QPushButton("Generate Report")
            gen_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 16px;")
            layout.addWidget(gen_btn)
            
            # Export format
            format_layout = QHBoxLayout()
            format_layout.addWidget(QLabel("Export:"))
            format_combo = QComboBox()
            format_combo.addItems(["PDF", "HTML", "CSV", "JSON"])
            format_layout.addWidget(format_combo)
            format_layout.addStretch()
            layout.addLayout(format_layout)
            
            # Preview
            preview_group = QGroupBox("Preview")
            preview_layout = QVBoxLayout()
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlainText("Report preview will appear here...")
            preview_layout.addWidget(preview)
            preview_group.setLayout(preview_layout)
            layout.addWidget(preview_group)
            
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "📋 Reports")
        
        def _create_settings_tab(self):
            """Create settings tab"""
            tab = QWidget()
            layout = QVBoxLayout()
            
            # Theme selection
            theme_group = QGroupBox("Appearance")
            theme_layout = QGridLayout()
            
            theme_layout.addWidget(QLabel("Theme:"), 0, 0)
            theme_combo = QComboBox()
            theme_combo.addItems(["modern_dark", "modern_light", "cyberpunk", "professional", "dark", "light", "blue", "green"])
            theme_layout.addWidget(theme_combo, 0, 1)
            
            theme_group.setLayout(theme_layout)
            layout.addWidget(theme_group)
            
            # Save button
            save_btn = QPushButton("Save Settings")
            save_btn.clicked.connect(lambda: QMessageBox.information(self, "Settings", "Settings saved!"))
            layout.addWidget(save_btn)
            
            layout.addStretch()
            tab.setLayout(layout)
            self.tab_widget.addTab(tab, "⚙️ Settings")
        
        def _create_menu_bar(self):
            """Create menu bar"""
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu("&File")
            
            export_action = QAction("&Export Data", self)
            file_menu.addAction(export_action)
            
            exit_action = QAction("&Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Tools menu
            tools_menu = menubar.addMenu("&Tools")
            
            diagnostics_action = QAction("&System Diagnostics", self)
            tools_menu.addAction(diagnostics_action)
            
            # Help menu
            help_menu = menubar.addMenu("&Help")
            
            about_action = QAction("&About", self)
            about_action.triggered.connect(lambda: QMessageBox.about(self, "About", "AirOne Professional v4.0\nEnhanced GUI with Advanced Tabs"))
            help_menu.addAction(about_action)
        
        def _create_status_bar(self):
            """Create status bar"""
            self.statusBar().showMessage("Ready - All systems operational")
        
        def apply_theme(self):
            """Apply modern theme"""
            self.theme_manager.apply_theme(qApp, "modern_dark")
        
        def _refresh_data(self):
            """Refresh data periodically"""
            # Update status bar
            self.statusBar().showMessage(f"Updated at {QTime.currentTime().toString()}")
    
    def run_enhanced_gui():
        """Run enhanced GUI"""
        if not PYQT5_AVAILABLE:
            print("PyQt5 not available - cannot run GUI")
            return False
        
        app = QApplication(sys.argv)
        window = EnhancedTabbedGUI()
        window.show()
        sys.exit(app.exec_())
    
    if __name__ == "__main__":
        run_enhanced_gui()

else:
    def run_enhanced_gui():
        print("PyQt5 not available - install with: pip install PyQt5")
        return False
    
    if __name__ == "__main__":
        run_enhanced_gui()
