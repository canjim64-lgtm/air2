
"""
AirOne Professional v4.0 - GUI Widgets
Custom widgets for the graphical user interface
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import hashlib
import json
from pathlib import Path


class SessionLockOverlay(QWidget):
    """
    Full-screen security overlay.
    Blocks all interaction until unlocked.
    """

    unlocked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAutoFillBackground(True)
        self.auth_manager = None
        
        # Try to import auth manager
        try:
            from security.auth_manager import AuthManager
            self.auth_manager = AuthManager()
        except Exception as e:
            # Auth manager not available, will use fallback password validation
            self.auth_manager = None
            self.logger = logging.getLogger(__name__)
            self.logger.debug(f"Auth manager not available: {e}")

        # Semi-transparent background
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(0, 0, 0, 240))
        self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon_lbl = QLabel("🔒")
        icon_lbl.setStyleSheet("font-size: 64pt;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Title
        title = QLabel("SESSION LOCKED")
        title.setStyleSheet("color: white; font-size: 24pt; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Password Input
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Enter Password to Unlock")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border-radius: 5px;
                font-size: 14pt;
                min-width: 300px;
            }
        """)
        self.pwd_input.returnPressed.connect(self._check_password)
        layout.addWidget(self.pwd_input)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: red; font-size: 12pt;")
        layout.addWidget(self.status_lbl)
        
        # Load stored password hash
        self._load_password_hash()

    def _load_password_hash(self):
        """Load the current user's password hash"""
        try:
            password_file = Path(__file__).parent.parent.parent.parent / 'passwords' / 'current_password.txt'
            if password_file.exists():
                with open(password_file, 'r') as f:
                    self.stored_password_hash = f.read().strip()
            else:
                # Fallback: use default admin password hash
                self.stored_password_hash = hashlib.sha256(b'admin').hexdigest()
        except:
            self.stored_password_hash = hashlib.sha256(b'admin').hexdigest()

    def _check_password(self):
        pwd = self.pwd_input.text()
        
        # Validate against stored password
        pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
        
        if pwd_hash == self.stored_password_hash:
            self.status_lbl.setText("")
            self.pwd_input.clear()
            self.hide()
            self.unlocked.emit()
        else:
            self.status_lbl.setText("Invalid Password")
            self.pwd_input.selectAll()

    def lock_session(self):
        self.show()
        self.raise_()
        self.pwd_input.setFocus()
        self.activateWindow()

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class TimelineScrubber(QGroupBox):
    """
    Forensic Timeline Scrubber.
    Allows replaying mission history and adjusting playback speed.
    """
    
    scrub_signal = pyqtSignal(float) # Emits timestamp (0.0 to 1.0 normalized)
    speed_signal = pyqtSignal(float) # Emits speed multiplier
    
    def __init__(self):
        super().__init__("🎞️ Forensic Timeline")
        
        layout = QHBoxLayout(self)
        
        # Play/Pause
        self.play_btn = QPushButton("⏸️")
        self.play_btn.setCheckable(True)
        self.play_btn.setChecked(True)
        self.play_btn.clicked.connect(self._toggle_play)
        layout.addWidget(self.play_btn)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10000)
        self.slider.sliderMoved.connect(self._on_scrub)
        layout.addWidget(self.slider)
        
        # Time Label
        self.time_lbl = QLabel("T+00:00")
        layout.addWidget(self.time_lbl)
        
        # Speed Control
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setPrefix("x")
        self.speed_spin.valueChanged.connect(self.speed_signal.emit)
        layout.addWidget(self.speed_spin)
        
    def _on_scrub(self, val):
        norm_val = val / 10000.0
        self.scrub_signal.emit(norm_val)
        
    def _toggle_play(self, checked):
        self.play_btn.setText("⏸️" if checked else "▶️")
        # In a real app, this would pause/resume the main timer
        
    def set_time(self, time_str):
        self.time_lbl.setText(time_str)
