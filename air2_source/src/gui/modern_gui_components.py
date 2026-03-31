"""
AirOne Professional v4.0 - Modern GUI Enhancements
Advanced styling, animations, and modern UI components
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from main_gui import ThemeManager, Theme
except ImportError:
    from src.gui.main_gui import ThemeManager, Theme


class ModernThemeManager(ThemeManager):
    """Enhanced theme manager with modern themes"""
    
    def __init__(self):
        super().__init__()
        
        # Add modern themes
        self.themes['modern_dark'] = {
            'background': '#1e1e2e',
            'foreground': '#cdd6f4',
            'primary': '#89b4fa',
            'secondary': '#313244',
            'accent': '#f38ba8',
            'success': '#a6e3a1',
            'warning': '#fab387',
            'error': '#f38ba8',
            'info': '#89b4fa',
            'surface': '#45475a',
            'overlay': '#585b70'
        }
        
        self.themes['modern_light'] = {
            'background': '#eff1f5',
            'foreground': '#4c4f69',
            'primary': '#1e66f5',
            'secondary': '#ccd0da',
            'accent': '#fe640b',
            'success': '#40a02b',
            'warning': '#df8e1d',
            'error': '#d20f39',
            'info': '#1e66f5',
            'surface': '#bcc0cc',
            'overlay': '#acb0be'
        }
        
        self.themes['cyberpunk'] = {
            'background': '#0d0221',
            'foreground': '#00f0ff',
            'primary': '#ff00ff',
            'secondary': '#1a0533',
            'accent': '#ffff00',
            'success': '#00ff00',
            'warning': '#ff9900',
            'error': '#ff0000',
            'info': '#00f0ff',
            'surface': '#2a0a4a',
            'overlay': '#3d0f5e'
        }
        
        self.themes['professional'] = {
            'background': '#f5f6fa',
            'foreground': '#2f3640',
            'primary': '#3498db',
            'secondary': '#dcdde1',
            'accent': '#e74c3c',
            'success': '#2ecc71',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'info': '#3498db',
            'surface': '#c8d6e5',
            'overlay': '#8395a7'
        }

    def get_modern_stylesheet(self, theme_name: str = None) -> str:
        """Get modern enhanced stylesheet"""
        if theme_name is None:
            theme_name = self.current_theme

        colors = self.themes.get(theme_name, self.themes[Theme.DARK])
        
        # Use surface color if available, otherwise use secondary
        surface = colors.get('surface', colors['secondary'])
        overlay = colors.get('overlay', colors['primary'])

        stylesheet = f"""
/* ===== Main Window ===== */
QMainWindow {{
    background-color: {colors['background']};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['background']},
                                stop:1 {surface}40);
    color: {colors['foreground']};
}}

QWidget {{
    background-color: transparent;
    color: {colors['foreground']};
    font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
    font-size: 13px;
}}

/* ===== Buttons ===== */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['accent']},
                                stop:1 {colors['accent']}cc);
}}

QPushButton:pressed {{
    background: {colors['secondary']};
    padding: 11px 19px 9px 21px;
}}

QPushButton:disabled {{
    background: {surface};
    color: {colors['foreground']}60;
}}

/* ===== Input Fields ===== */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {surface};
    border: 2px solid {colors['primary']}40;
    border-radius: 6px;
    padding: 8px 12px;
    color: {colors['foreground']};
    font-size: 13px;
    selection-background-color: {colors['primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, 
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 2px solid {colors['primary']};
    background-color: {surface}e0;
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{
    border: 2px solid {colors['primary']}80;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    border: 2px solid {surface};
    background-color: {surface}40;
    border-radius: 8px;
    padding: 4px;
}}

QTabBar::tab {{
    background-color: {surface};
    color: {colors['foreground']};
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    border: 2px solid transparent;
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background-color: {colors['primary']};
    color: white;
    border: 2px solid {colors['primary']};
    border-bottom: none;
}}

QTabBar::tab:hover:!selected {{
    background-color: {colors['primary']}60;
    border: 2px solid {colors['primary']}80;
    border-bottom: none;
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {surface};
    color: {colors['foreground']};
    padding: 6px 8px;
    border-bottom: 2px solid {colors['primary']}40;
    font-weight: 500;
}}

QMenuBar::item:selected {{
    background-color: {colors['primary']};
    color: white;
    border-radius: 4px;
    padding: 4px 8px;
}}

QMenu {{
    background-color: {surface};
    border: 2px solid {colors['primary']}40;
    border-radius: 8px;
    padding: 8px 0;
}}

QMenu::item:selected {{
    background-color: {colors['primary']};
    color: white;
    padding: 6px 20px;
}}

QMenu::separator {{
    height: 2px;
    background: {colors['primary']}40;
    margin: 6px 10px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {surface},
                                stop:1 {colors['secondary']});
    color: {colors['foreground']};
    border-top: 2px solid {colors['primary']}40;
    font-weight: 500;
    padding: 4px;
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    border: 2px solid {surface};
    border-radius: 8px;
    text-align: center;
    background-color: {surface};
    height: 20px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {colors['success']},
                                stop:1 {colors['primary']});
    border-radius: 6px;
}}

/* ===== Group Box ===== */
QGroupBox {{
    font-weight: 600;
    border: 2px solid {surface};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: {surface}30;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {colors['primary']};
    background-color: {surface};
    border-radius: 4px;
}}

/* ===== Table Widget ===== */
QTableWidget {{
    background-color: {surface}40;
    alternate-background-color: {surface}20;
    gridline-color: {surface};
    border: 2px solid {surface};
    border-radius: 8px;
    selection-background-color: {colors['primary']}60;
}}

QTableWidget::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
    color: white;
    padding: 8px;
    border: none;
    font-weight: 600;
    border-bottom: 2px solid {colors['primary']}80;
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {{
    background-color: {surface};
    width: 14px;
    border-radius: 7px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {surface};
    height: 14px;
    border-radius: 7px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {colors['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ===== Combo Box ===== */
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 7px solid {colors['foreground']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {surface};
    border: 2px solid {colors['primary']}40;
    border-radius: 6px;
    selection-background-color: {colors['primary']};
    selection-color: white;
    outline: none;
    padding: 4px;
}}

/* ===== Check Box ===== */
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {colors['primary']};
    border-radius: 5px;
    background-color: {surface};
}}

QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
}}

QCheckBox::indicator:hover {{
    border: 2px solid {colors['accent']};
}}

/* ===== Radio Button ===== */
QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {colors['primary']};
    border-radius: 10px;
    background-color: {surface};
}}

QRadioButton::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {colors['primary']},
                                stop:1 {colors['primary']}cc);
}}

QRadioButton::indicator:hover {{
    border: 2px solid {colors['accent']};
}}

/* ===== Tool Tips ===== */
QToolTip {{
    background-color: {colors['primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 500;
}}

/* ===== Splitter ===== */
QSplitter::handle {{
    background-color: {surface};
}}

QSplitter::handle:horizontal {{
    width: 6px;
    border-radius: 3px;
}}

QSplitter::handle:vertical {{
    height: 6px;
    border-radius: 3px;
}}

/* ===== Slider ===== */
QSlider::groove:horizontal {{
    border: 1px solid {surface};
    height: 8px;
    background: {surface};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {colors['primary']};
    border: 2px solid {colors['primary']};
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {colors['accent']};
}}

/* ===== List Widget ===== */
QListWidget {{
    background-color: {surface}40;
    border: 2px solid {surface};
    border-radius: 8px;
    outline: none;
    padding: 4px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
    margin: 2px 0;
}}

QListWidget::item:selected {{
    background-color: {colors['primary']};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {colors['primary']}40;
}}

/* ===== Spin Box Buttons ===== */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    width: 20px;
    border: none;
    background: {colors['primary']}60;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {colors['primary']};
}}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: {colors['secondary']};
}}

/* ===== LCD Number (Enhanced) ===== */
QLCDNumber {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {surface},
                                stop:1 {colors['secondary']});
    border: 3px solid {colors['primary']}40;
    border-radius: 8px;
    color: {colors['primary']};
    font-family: 'Courier New', monospace;
    padding: 8px;
}}

/* ===== Labels with Primary Color ===== */
QLabel#primaryLabel {{
    color: {colors['primary']};
    font-weight: 600;
}}

QLabel#successLabel {{
    color: {colors['success']};
    font-weight: 600;
}}

QLabel#warningLabel {{
    color: {colors['warning']};
    font-weight: 600;
}}

QLabel#errorLabel {{
    color: {colors['error']};
    font-weight: 600;
}}

/* ===== Frame ===== */
QFrame {{
    background-color: {surface}30;
    border: 2px solid {surface};
    border-radius: 8px;
}}

QFrame#cardFrame {{
    background-color: {surface}40;
    border: 2px solid {colors['primary']}20;
    border-radius: 10px;
}}

/* ===== Tool Button ===== */
QToolButton {{
    background-color: {colors['primary']};
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: 600;
}}

QToolButton:hover {{
    background-color: {colors['accent']};
}}

QToolButton:pressed {{
    background-color: {colors['secondary']};
}}

/* ===== Dialog ===== */
QDialog {{
    background-color: {colors['background']};
}}

QMessageBox {{
    background-color: {colors['background']};
}}

QMessageBox QLabel {{
    color: {colors['foreground']};
    padding: 8px;
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 8px 16px;
}}
        """

        return stylesheet


class AnimatedButton(QPushButton):
    """Button with hover animation effects"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        
    def enterEvent(self, event):
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.width() + 10)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.width() - 10)
        self.animation.start()
        super().leaveEvent(event)


class GradientLabel(QLabel):
    """Label with gradient background"""
    
    def __init__(self, text, color1, color2, parent=None):
        super().__init__(text, parent)
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("padding: 10px; font-weight: bold; border-radius: 8px;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        super().paintEvent(event)


class CardWidget(QFrame):
    """Modern card-style widget"""
    
    def __init__(self, title="", content="", parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(title_label)
        
        if content:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
        
        layout.addStretch()


class StatusIndicator(QFrame):
    """Animated status indicator"""
    
    def __init__(self, color="#4caf50", parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setStyleSheet(f"""
            StatusIndicator {{
                background-color: {color};
                border-radius: 8px;
                border: 2px solid white;
            }}
        """)
        
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.3)
        self.animation.setLoopCount(-1)
        self.animation.start()


class ModernProgressBar(QProgressBar):
    """Modern styled progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setFormat("%p%")
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                text-align: center;
                background-color: #2b2b2b;
                height: 24px;
                font-weight: 600;
                font-size: 13px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4caf50,
                                            stop:0.5 #8bc34a,
                                            stop:1 #4caf50);
                border-radius: 6px;
            }
        """)


class LoadingOverlay(QWidget):
    """Overlay widget for loading states"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.spinner = QProgressBar()
        self.spinner.setFixedSize(100, 100)
        self.spinner.setMinimum(0)
        self.spinner.setMaximum(0)
        self.spinner.setTextVisible(False)
        self.spinner.setStyleSheet("""
            QProgressBar {
                border: 4px solid #3c3c3c;
                border-top: 4px solid #007acc;
                border-radius: 50%;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.spinner)
        
        self.label = QLabel("Loading...")
        self.label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
    def showEvent(self, event):
        self.raise_()
        super().showEvent(event)


def apply_modern_theme(app, theme_name='modern_dark'):
    """Apply modern theme to application"""
    theme_manager = ModernThemeManager()
    theme_manager.current_theme = theme_name
    app.setStyleSheet(theme_manager.get_modern_stylesheet(theme_name))
    return theme_manager
