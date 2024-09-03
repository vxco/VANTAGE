import ctypes
import json
import logging
import os
import platform
import random as r
import sys
import time
import traceback
from dataclasses import dataclass
from scipy import ndimage


import cv2
import markdown
import numpy as np
import psutil

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget,
                             QPushButton, QTextBrowser, QMessageBox, QHBoxLayout, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QFont, QPixmap, QColor, QPalette, QIcon, QLinearGradient, QPainter, QDesktopServices
from PyQt5.QtCore import Qt, PYQT_VERSION_STR, QSize, QUrl, QRect
from PyQt5.QtSvg import QSvgWidget

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget,
                             QPushButton, QTextBrowser, QMessageBox, QHBoxLayout, QFrame)
from PyQt5.QtGui import QFont, QPixmap, QColor, QPalette, QIcon
from PyQt5.QtCore import Qt, PYQT_VERSION_STR, QSize, QUrl
from PyQt5.QtSvg import QSvgWidget

from PyQt5.QtCore import QUrl, PYQT_VERSION_STR
from PyQt5.QtCore import Qt, QTimer, QObject, QPoint, QRect, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, \
    QSettings
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QLinearGradient, QPalette, QIcon, QKeySequence, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSlider, QGroupBox, QSplitter, QCheckBox, QRadioButton,
    QButtonGroup, QSplashScreen, QMessageBox, QTextBrowser, QAction, QInputDialog, QGraphicsOpacityEffect, QSizePolicy,
    QSpacerItem, QShortcut, QDoubleSpinBox, QFrame
)
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QWidget, QFormLayout,
                             QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QFileDialog)
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QHBoxLayout, QSizeGrip
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import (QTabWidget)

from s826 import setChanVolt, detectBoard


logging.basicConfig(filename='s826Debug.log', level=logging.DEBUG,
                    format='s826DEBUG | %(asctime)s - %(levelname)s - %(message)s')

logging.basicConfig(filename='vantage_debug.log', level=logging.DEBUG,
                    format='VantageDebug | %(asctime)s - %(levelname)s - %(message)s')


if platform.system() == 'Darwin':
    from Foundation import NSBundle
    bundle = NSBundle.mainBundle()
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    info['CFBundleName'] = "VANTAGE"
else:
    import wmi

VERSION = "4.0.1b"

DARK_MODE_STYLE = """
    QMainWindow, QWidget {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenuBar, QMenu {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenuBar::item:selected, QMenu::item:selected {
        background-color: #3A3A3A;
    }
    QLabel, QCheckBox, QRadioButton {
        color: #FFFFFF;
    }
    QPushButton {
        background-color: #3A3A3A;
        color: #FFFFFF;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #4A4A4A;
    }
    QPushButton:pressed {
        background-color: #555555;
    }
    QGroupBox {
        border: 1px solid #555555;
        margin-top: 0.5em;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    QSlider::handle:horizontal {
        background-color: #4A4A4A;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox {
        background-color: #3A3A3A;
        color: #FFFFFF;
        border: 1px solid #555555;
        padding: 2px;
    }
    QTextBrowser {
        background-color: #2B2B2B;
        color: #FFFFFF;
        border: 1px solid #555555;
    }
    QScrollBar:vertical, QScrollBar:horizontal {
        background-color: #2B2B2B;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background-color: #4A4A4A;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
        background-color: #555555;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        height: 0px;
    }
"""

FAST_BOOT = True

def global_exception_handler(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(f"Uncaught exception:\n{error_msg}")
    logging.critical(f"Uncaught exception:\n{error_msg}")
    QMessageBox.critical(None, "Critical Exception", f"An unexpected error occurred:\n{str(value)}\n\nPlease check the log file for more details.")


sys.excepthook = global_exception_handler

class ModernDialog(QDialog):
    def __init__(self, parent=None, title=""):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setWindowTitle(title)
        self.oldPos = self.pos()

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = QWidget(self)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FF5555;
                color: white;
            }
        """)
        title_layout.addWidget(close_button)

        self.main_layout.addWidget(self.title_bar)

        # Content widget
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)

        self.apply_theme(True)  # Start with dark theme by default

    def apply_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #2B2B2B;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox {
                    background-color: #3A3A3A;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #357abd;
                }
                QPushButton:pressed {
                    background-color: #2a5f9e;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    margin-top: 10px;
                    color: #FFFFFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
            """)
            self.title_bar.setStyleSheet("background-color: #1E1E1E;")
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                }
                QLabel {
                    color: #333333;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #357abd;
                }
                QPushButton:pressed {
                    background-color: #2a5f9e;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    margin-top: 10px;
                    color: #333333;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
            """)
            self.title_bar.setStyleSheet("background-color: #E0E0E0;")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


class ModernTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.apply_theme(True)  # Start with dark theme by default

    def apply_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background: #2B2B2B;
                    border-radius: 4px;
                }
                QTabWidget::tab-bar {
                    left: 5px;
                }
                QTabBar::tab {
                    background: #3A3A3A;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-bottom-color: #555555;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 5px;
                }
                QTabBar::tab:selected, QTabBar::tab:hover {
                    background: #4a90e2;
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background: white;
                    border-radius: 4px;
                }
                QTabWidget::tab-bar {
                    left: 5px;
                }
                QTabBar::tab {
                    background: #e0e0e0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-bottom-color: #cccccc;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 5px;
                }
                QTabBar::tab:selected, QTabBar::tab:hover {
                    background: #4a90e2;
                    color: white;
                }
            """)


class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0

    def compute(self, setpoint, current_value, dt):
        error = setpoint - current_value
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.prev_error = error
        return output

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About VANTAGE")
        self.setFixedSize(550, 550)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        # Icon (flipped colors)
        icon_label = QLabel(self)
        pixmap = QPixmap("assets/v3/vtg_icon_comet.png")
        inverted_pixmap = self.invert_pixmap(pixmap)
        icon_label.setPixmap(inverted_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel("VANTAGE", self)
        title_label.setFont(QFont("Roboto", 28, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("background: -webkit-linear-gradient(top, #007AFF, #00BFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;")
        layout.addWidget(title_label)

        # Version
        version_label = QLabel(f"Version {VERSION}", self)
        version_label.setFont(QFont("Roboto", 12))
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Description
        description = QTextBrowser(self)
        description.setOpenExternalLinks(True)
        description.setHtml(f"""
        <div style='text-align: center; font-family: Roboto, Arial, sans-serif;'>
            <p style='font-size: 16px; font-weight: bold; margin: 20px 0;'>
                <span style='color: #007AFF;'>V</span>ision 
                <span style='color: #007AFF;'>A</span>ssisted 
                <span style='color: #007AFF;'>N</span>ano-particle 
                <span style='color: #007AFF;'>T</span>racking and 
                <span style='color: #007AFF;'>G</span>uided 
                <span style='color: #007AFF;'>E</span>xtraction
            </p>
            <p style='font-size: 14px; margin: 15px 0;'>
                Developed by<br>
                <strong>Alfa Ozaltin</strong>
                @ Stanford University
            </p>
            <p style='margin: 20px 0;'>
                <a href='https://vantage.software' style='color: #007AFF; text-decoration: none; font-weight: bold;'>Visit VANTAGE Website</a>
            </p>
            <p style='font-size: 12px; color: #888;'>
                © 2024 Stanford University & VX Software. All rights reserved.
            </p>
        </div>
        """)
        description.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(description)

    def invert_pixmap(self, pixmap):
        img = pixmap.toImage()
        img.invertPixels()
        return QPixmap.fromImage(img)

    def apply_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QTextBrowser {
                    color: #FFFFFF;
                    background-color: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QTextBrowser {
                    color: #000000;
                    background-color: transparent;
                }
            """)


class PreferencesDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Preferences")
        self.setMinimumSize(500, 400)
        self.settings = QSettings("VANTAGE", "ColorDetectionApp")

        # Setup the main layout
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.setup_tabs()
        self.create_button_box()

    def setup_tabs(self):
        self.tab_widget = ModernTabWidget(self)
        self.content_layout.addWidget(self.tab_widget)

        self.setup_general_tab()
        self.setup_camera_tab()
        self.setup_analysis_tab()

    def create_button_box(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_preferences)
        button_box.rejected.connect(self.reject)
        self.content_layout.addWidget(button_box)

    def setup_general_tab(self):
        general_tab = QWidget()
        self.tab_widget.addTab(general_tab, "General")

        general_layout = QFormLayout(general_tab)

        self.default_project_location = QLineEdit(self.settings.value("default_project_location", ""))
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_project_location)

        location_layout = QHBoxLayout()
        location_layout.addWidget(self.default_project_location)
        location_layout.addWidget(browse_button)

        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(int(self.settings.value("auto_save_interval", 5)))

        general_layout.addRow("Default Project Location:", location_layout)
        general_layout.addRow("Auto-save Interval (minutes):", self.auto_save_interval)

    def setup_camera_tab(self):
        camera_tab = QWidget()
        self.tab_widget.addTab(camera_tab, "Camera")

        camera_layout = QFormLayout(camera_tab)

        self.default_camera_port = QSpinBox()
        self.default_camera_port.setRange(0, 10)
        self.default_camera_port.setValue(int(self.settings.value("default_camera_port", 0)))

        self.default_resolution = QLineEdit(self.settings.value("default_resolution", "1280x720"))

        camera_layout.addRow("Default Camera Port:", self.default_camera_port)
        camera_layout.addRow("Default Resolution:", self.default_resolution)

    def setup_analysis_tab(self):
        analysis_tab = QWidget()
        self.tab_widget.addTab(analysis_tab, "Analysis")

        analysis_layout = QFormLayout(analysis_tab)

        self.min_particle_size = QSpinBox()
        self.min_particle_size.setRange(1, 1000)
        self.min_particle_size.setValue(int(self.settings.value("min_particle_size", 30)))

        self.max_particle_size = QSpinBox()
        self.max_particle_size.setRange(1, 10000)
        self.max_particle_size.setValue(int(self.settings.value("max_particle_size", 600)))

        analysis_layout.addRow("Minimum Particle Size:", self.min_particle_size)
        analysis_layout.addRow("Maximum Particle Size:", self.max_particle_size)

    def browse_project_location(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Default Project Location")
        if directory:
            self.default_project_location.setText(directory)

    def save_preferences(self):
        self.settings.setValue("default_project_location", self.default_project_location.text())
        self.settings.setValue("auto_save_interval", self.auto_save_interval.value())
        self.settings.setValue("default_camera_port", self.default_camera_port.value())
        self.settings.setValue("default_resolution", self.default_resolution.text())
        self.settings.setValue("min_particle_size", self.min_particle_size.value())
        self.settings.setValue("max_particle_size", self.max_particle_size.value())
        self.accept()


class FlashingTimedDialog(QDialog):
    def __init__(self, title, message, secs, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMinimumWidth(400)
        self.secs = secs

        layout = QVBoxLayout(self)

        # Add icon and message in a horizontal layout
        message_layout = QHBoxLayout()

        # Add critical error icon
        icon_label = QLabel()
        icon = QIcon("assets/critical_error_icon.png")  # Make sure this icon exists in your assets folder
        icon_label.setPixmap(icon.pixmap(QSize(64, 64)))
        message_layout.addWidget(icon_label)

        # Message label with bold, larger font
        self.message_label = QLabel(message)
        font = QFont("Arial", 14, QFont.Bold)
        self.message_label.setFont(font)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setStyleSheet("color: white; padding: 10px;")
        message_layout.addWidget(self.message_label, 1)

        layout.addLayout(message_layout)

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.timer_label)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.try_accept)
        self.ok_button.setEnabled(False)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4136;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
        """)
        layout.addWidget(self.ok_button)

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.flash)
        self.flash_timer.start(500)

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

        self.countdown = secs
        self.update_countdown()

        self.flash_state = False

        # Sound setup
        self.beep_sound = None
        self.media_player = None
        try:
            self.beep_sound = QSound("assets/error.wav")
            self.play_beep()  # Play the sound immediately
        except Exception as e:
            logging.error(f"Failed to initialize QSound: {str(e)}")
            try:
                self.media_player = QMediaPlayer()
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile("assets/error.wav")))
                self.media_player.play()
            except Exception as e:
                logging.error(f"Failed to initialize QMediaPlayer: {str(e)}")

        self.beep_timer = QTimer(self)
        self.beep_timer.timeout.connect(self.play_beep)
        self.beep_timer.start(2000)

        # Set initial background color
        self.setStyleSheet("background-color: #D50000;")

    def play_beep(self):
        try:
            if self.beep_sound:
                self.beep_sound.play()
            elif self.media_player:
                self.media_player.setPosition(0)
                self.media_player.play()
        except Exception as e:
            logging.error(f"Failed to play sound: {str(e)}")


    def flash(self):
        if self.flash_state:
            self.setStyleSheet("background-color: #D50000;")
        else:
            self.setStyleSheet("background-color: #FF1744;")
        self.flash_state = not self.flash_state

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.timer_label.setText(f"This message can be dismissed in {self.countdown} seconds")
        else:
            self.countdown_timer.stop()
            self.ok_button.setEnabled(True)
            self.timer_label.setText("You can now dismiss this message")


    def try_accept(self):
        if self.countdown <= 0:
            self.flash_timer.stop()
            self.beep_timer.stop()
            super().accept()

    def closeEvent(self, event):
        if self.countdown > 0:
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if self.countdown > 0:
            event.ignore()
        else:
            super().keyPressEvent(event)


class LoadingSplashScreen(QSplashScreen):
    def __init__(self, logo_path):
        pixmap = QPixmap(QSize(600, 350))
        painter = QPainter(pixmap)
        gradient = QLinearGradient(0, 0, 0, pixmap.height())
        gradient.setColorAt(0, QColor(230, 230, 250))
        gradient.setColorAt(1, QColor(201, 160, 220))
        painter.fillRect(pixmap.rect(), gradient)
        logo = QPixmap(logo_path)
        scaled_logo = logo.scaled(520, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_rect = scaled_logo.rect()
        logo_rect.moveCenter(QPoint(pixmap.width() // 2, pixmap.height() // 2 - 30))
        painter.drawPixmap(logo_rect, scaled_logo)
        painter.end()
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.progress = 0

    def drawContents(self, painter):
        super().drawContents(painter)
        rect = self.rect()
        bottom_section_height = 60

        painter.fillRect(0, rect.height() - bottom_section_height, rect.width(), bottom_section_height,
                         QColor(0, 0, 0, 40))

        # Draw progress text
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        text_rect = QRect(10, rect.height() - bottom_section_height, rect.width() - 20, 30)
        painter.drawText(text_rect, Qt.AlignBottom | Qt.AlignHCenter, f"Loading... {self.progress}%")

        # Draw version text
        monospace_font = QFont("Courier", 9)
        painter.setFont(monospace_font)
        painter.setPen(QColor(100, 100, 100, 180))  # Faded gray color
        version_text = f"v{VERSION}"
        version_rect = QRect(10, rect.height() - bottom_section_height - 20, 100, 20)
        painter.drawText(version_rect, Qt.AlignLeft | Qt.AlignBottom, version_text)

    def setProgress(self, value, message=""):
        self.progress = value
        self.showMessage(message, Qt.AlignBottom | Qt.AlignHCenter, Qt.black)
        self.repaint()


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #202020;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        # Add help button
        self.help_button = self.create_help_button()
        layout.addWidget(self.help_button)

        layout.addStretch()

        for button_data in [("minimize", self.parent.showMinimized), ("close", self.parent.close)]:
            button = QPushButton(self)
            button.setIcon(QIcon(f"assets/{button_data[0]}_icon.png"))
            button.setFixedSize(30, 30)
            button.clicked.connect(button_data[1])
            button.setStyleSheet(self.get_button_style(button_data[0]))
            layout.addWidget(button)

    def create_help_button(self):
        help_button = QPushButton("Help", self)
        help_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        help_button.setCursor(Qt.PointingHandCursor)

        help_menu = QMenu(self)
        help_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3a3a3a;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
        """)

        about_action = help_menu.addAction('About')
        user_manual_action = help_menu.addAction('User Manual')
        preferences_action = help_menu.addAction('Preferences')

        help_button.setMenu(help_menu)

        about_action.triggered.connect(self.parent.show_about)
        user_manual_action.triggered.connect(self.parent.show_user_manual)
        preferences_action.triggered.connect(self.parent.show_preferences)

        return help_button

    @staticmethod
    def get_button_style(button_type):
        base_style = """
            QPushButton {
                border: none;
                padding: 0px;
            }
        """
        hover_color = "#DC5F00" if button_type == "minimize" else "#CD1818"
        return base_style + f"QPushButton:hover {{ background-color: {hover_color}; }}"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.moving = True
            self.parent.offset = event.globalPos() - self.parent.pos()

    def mouseMoveEvent(self, event):
        if self.parent.moving:
            self.parent.move(event.globalPos() - self.parent.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.moving = False


class ProjectSettingsDialog(ModernDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent, "Project Settings")
        self.setMinimumSize(400, 200)
        self.current_settings = current_settings or {}

        # Setup the main layout
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.setup_camera_settings()
        self.create_button_box()

    def setup_camera_settings(self):
        group_box = QGroupBox("Camera Settings")
        form_layout = QFormLayout(group_box)

        self.camera_port = QSpinBox()
        self.camera_port.setRange(0, 10)
        self.camera_port.setValue(self.current_settings.get('camera_port', 0))

        self.resolution = QLineEdit(self.current_settings.get('resolution', '1280x720'))

        form_layout.addRow("Camera Port:", self.camera_port)
        form_layout.addRow("Resolution:", self.resolution)

        self.content_layout.addWidget(group_box)

    def create_button_box(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.content_layout.addWidget(button_box)

    def get_settings(self):
        return {
            'camera_port': self.camera_port.value(),
            'resolution': self.resolution.text(),
        }


class MagnetDebugDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Magnet Debug")
        self.setMinimumSize(400, 300)

        # Setup the main layout
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # Driver Check
        driver_group = QGroupBox("Driver Status")
        driver_layout = QVBoxLayout(driver_group)
        self.driver_label = QLabel("Sensoray 826 Driver: Checking...")
        self.filter_label = QLabel("Sensoray 826 Filter: Checking...")
        driver_layout.addWidget(self.driver_label)
        driver_layout.addWidget(self.filter_label)
        self.content_layout.addWidget(driver_group)

        # Board ID
        board_group = QGroupBox("Board Information")
        board_layout = QVBoxLayout(board_group)
        self.board_id_label = QLabel("Board ID: Checking...")
        board_layout.addWidget(self.board_id_label)
        self.content_layout.addWidget(board_group)

        # Magnet Control
        magnet_group = QGroupBox("Magnet Control")
        magnet_layout = QVBoxLayout(magnet_group)
        self.totalM_spinbox = QDoubleSpinBox()
        self.totalM_spinbox.setRange(-4, 4)
        self.totalM_spinbox.setSingleStep(0.1)
        self.totalM_spinbox.setDecimals(1)
        magnet_layout.addWidget(QLabel('Magnet Amp:'))
        magnet_layout.addWidget(self.totalM_spinbox)

        self.apply_button = QPushButton("Apply Voltages")
        self.apply_button.clicked.connect(self.apply_voltages)
        magnet_layout.addWidget(self.apply_button)
        self.content_layout.addWidget(magnet_group)

        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.content_layout.addWidget(close_button)

        # Check driver and board ID
        QTimer.singleShot(0, self.check_driver_and_board)


    def check_driver_and_board(self):
        if sys.platform.startswith('win'):
            c = wmi.WMI()

            # Check for Sensoray 826 Driver
            driver_devices = c.Win32_PnPEntity(Name="Sensoray 826 Driver")
            driver_found = len(list(driver_devices)) > 0
            self.driver_label.setText(f"Sensoray 826 Driver: {'Found' if driver_found else 'Not Found'}")
            self.driver_label.setStyleSheet(f"color: {'green' if driver_found else 'red'}")

            # Check for Sensoray 826 Filter
            filter_devices = c.Win32_PnPEntity(Name="Sensoray 826 Filter")
            filter_found = len(list(filter_devices)) > 0
            self.filter_label.setText(f"Sensoray 826 Filter: {'Found' if filter_found else 'Not Found'}")
            self.filter_label.setStyleSheet(f"color: {'green' if filter_found else 'red'}")

            # Both should be present
            all_found = driver_found and filter_found
        else:
            all_found = False
            self.driver_label.setText("Sensoray 826 Driver: N/A (Not Windows)")
            self.filter_label.setText("Sensoray 826 Filter: N/A (Not Windows)")

        # Check for board ID
        if all_found:
            try:
                board_id = detectBoard()
                self.board_id_label.setText(f"Board ID: {board_id}")
                self.board_id_label.setStyleSheet("color: green")
            except Exception as e:
                self.board_id_label.setText(f"Board ID: Error - {str(e)}")
                self.board_id_label.setStyleSheet("color: red")
        else:
            self.board_id_label.setText("Board ID: N/A (Driver or Filter not found)")
            self.board_id_label.setStyleSheet("color: red")

    def apply_voltages(self):
        totM = self.totalM_spinbox.value()
        upM = totM * 0.57
        botM = totM * -0.57
        if upM > 2.28 or upM < -2.28:
            setChanVolt(4, 0)
            setChanVolt(7, 0)
            logging.warning('Magnet settings zeroed due to unsafe upper magnet value.')
            logging.critical(
                'Safety Protocol: magnet amp above safe operating value. Contact VANTAGE Support with error code SP1 before reusing the software.')
            QMessageBox.critical(self, "Safety Error",
                                 "Magnet amp above safe operating value. Contact VANTAGE Support with error code SP1 before reusing the software.")
            return

        if botM > 3 or botM < -2.28:
            setChanVolt(4, 0)
            setChanVolt(7, 0)
            logging.warning('Magnet settings zeroed due to unsafe bottom magnet value.')
            logging.critical(
                'Safety Protocol: magnet amp above safe operating value. Contact VANTAGE Support with error code SP1 before reusing the software.')
            QMessageBox.critical(self, "Safety Error",
                                 "Magnet amp above safe operating value. Contact VANTAGE Support with error code SP1 before reusing the software.")
            return

        try:
            logging.info(f"Attempting to set voltages: Up = {upM}V, Bottom = {botM}V - Amp: {totM}")
            setChanVolt(4, upM)
            setChanVolt(7, botM)
            logging.info('Magnet settings applied successfully.')
            QMessageBox.information(self, "Success", f"Voltages applied: Up = {upM}V, Bottom = {botM}V")

        except Exception as e:
            logging.error(f"Failed to apply voltages: {str(e)}")
            setChanVolt(4, 0)
            setChanVolt(7, 0)
            logging.warning('Magnet settings zeroed due to error.')
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to apply voltages: {str(e)}")


class RecentProjectsManager:
    def __init__(self, filename="recent_projects.json"):
        self.filename = filename
        self.projects = self.load()

    def load(self):
        try:
            with open(self.filename, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.projects, f)

    def add(self, project_path):
        absolute_path = os.path.abspath(project_path)
        if absolute_path in self.projects:
            self.projects.remove(absolute_path)
        self.projects.insert(0, absolute_path)
        self.projects = self.projects[:10]  # Keep only the 10 most recent
        self.save()

    def update_project_path(self, old_path, new_path):
        if old_path in self.projects:
            index = self.projects.index(old_path)
            self.projects[index] = new_path
            self.save()

    def remove(self, project_path):
        if project_path in self.projects:
            self.projects.remove(project_path)
            self.save()


class RecentProjectsListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3a3a3a;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)

    def addProject(self, project_path, open_function, rename_function):
        item = QListWidgetItem(self)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        label = QLabel(project_path)
        label.setStyleSheet("color: white;")
        label.setWordWrap(True)
        layout.addWidget(label, 1)

        open_button = self.create_icon_button("assets/open_icon.png", "Open project", open_function, project_path)
        rename_button = self.create_icon_button("assets/rename_icon.png", "Rename project", rename_function, item, project_path)

        for button in (open_button, rename_button):
            layout.addWidget(button)
            button.hide()

        widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #3a3a3a;
            }
        """)

        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)

    def create_icon_button(self, icon_path, tooltip, function, *args):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setToolTip(tooltip)
        button.clicked.connect(lambda: function(*args))
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        button.setFixedSize(30, 30)
        button.setIconSize(QSize(20, 20))
        return button

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        item = self.itemAt(event.pos())
        for index in range(self.count()):
            list_item = self.item(index)
            widget = self.itemWidget(list_item)
            if widget:
                if list_item == item:
                    self._set_button_visibility(widget, True)
                else:
                    self._set_button_visibility(widget, False)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        for index in range(self.count()):
            list_item = self.item(index)
            widget = self.itemWidget(list_item)
            if widget:
                self._set_button_visibility(widget, False)

    def _set_button_visibility(self, widget, visible):
        for button in widget.findChildren(QPushButton):
            button.setVisible(visible)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            widget = self.itemWidget(item)
            if widget:
                open_button = widget.findChild(QPushButton)
                if open_button:
                    open_button.click()




class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(650, 500)

        self.recent_projects_manager = RecentProjectsManager()
        self.moving = False
        self.offset = QPoint()

        self.setup_ui()
        self.set_dark_theme()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom titlebar
        self.titlebar = TitleBar(self)
        main_layout.addWidget(self.titlebar)

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(content_widget)

        # Setup logo
        self.setup_logo(content_layout)
        content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setup_buttons(content_layout)
        content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setup_recent_projects(content_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.titlebar.geometry().contains(event.pos()):
            self.moving = True
            self.offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self.moving:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = False

    def show_about(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def show_user_manual(self):
        user_manual_dialog = UserManualDialog(self)
        user_manual_dialog.exec_()

    def show_preferences(self):
        preferences_dialog = PreferencesDialog(self)
        if preferences_dialog.exec_() == QDialog.Accepted:
            self.load_preferences()


    def load_preferences(self):
        # Load preferences here (you may need to adjust this method based on your needs)
        pass

    def setup_logo(self, layout):
        logo_label = QLabel()
        logo_pixmap = self.get_inverted_logo_pixmap("assets/v3/vtg_logo_text.png", 500, 250)
        logo_label.setPixmap(logo_pixmap)
        layout.addWidget(logo_label, alignment=Qt.AlignCenter)

    def setup_recent_projects(self, layout):
        recent_projects_label = QLabel("Recent Projects:")
        recent_projects_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(recent_projects_label)

        self.recent_projects_list = RecentProjectsListWidget(self)
        self.recent_projects_list.setMinimumHeight(150)
        layout.addWidget(self.recent_projects_list)

        self.load_recent_projects()

    def rename_project(self, item, old_path):
        new_name, ok = QInputDialog.getText(self, "Rename Project", "Enter new project name:",
                                            text=os.path.basename(old_path))
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            if not new_path.lower().endswith('.vtp'):
                new_path += '.vtp'

            if os.path.exists(new_path) and new_path.lower() != old_path.lower():
                QMessageBox.warning(self, "Error", "A project with this name already exists.")
                return

            try:
                os.rename(old_path, new_path)
                self.recent_projects_manager.remove(old_path)
                self.recent_projects_manager.add(new_path)
                self.load_recent_projects()
                QMessageBox.information(self, "Success", "Project renamed successfully.")
            except OSError as e:
                QMessageBox.warning(self, "Error", f"Failed to rename project: {str(e)}")

    def update_recent_projects(self):
        self.recent_projects_manager.save()
        self.load_recent_projects()

    def add_recent_project(self, project_path):
        self.recent_projects_manager.add(project_path)
        self.load_recent_projects()  # Refresh the list display

    def open_selected_project_from_button(self, project_path):
        if os.path.isfile(project_path):
            self.open_color_detection_app(project_path)
        else:
            QMessageBox.warning(self, "Error", f"Project file not found: {project_path}")
            self.recent_projects_manager.remove(project_path)
            self.load_recent_projects()

    def load_recent_projects(self):
        self.recent_projects_list.clear()
        for project in self.recent_projects_manager.projects:
            self.recent_projects_list.addProject(project, self.open_selected_project_from_button, self.rename_project)
        if not self.recent_projects_manager.projects:
            self.recent_projects_list.addItem("No recent projects")

    def setup_buttons(self, layout):
        button_layout = QHBoxLayout()
        for button_text, slot in [("New Project", self.create_project), ("Open Project", self.open_project)]:
            button = QPushButton(button_text)
            button.setStyleSheet(self.get_button_style())
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(slot)
            button_layout.addWidget(button)
        layout.addLayout(button_layout)


    @staticmethod
    def get_inverted_logo_pixmap(path, width, height):
        original_pixmap = QPixmap(path)
        image = original_pixmap.toImage()

        # Convert QImage to numpy array
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        arr = np.array(ptr).reshape(image.height(), image.width(), 4)  # 4 for RGBA

        # Invert the colors (excluding alpha channel)
        arr[:, :, :3] = 255 - arr[:, :, :3]

        # Convert back to QImage
        inverted_image = QImage(arr.data, arr.shape[1], arr.shape[0], QImage.Format_RGBA8888)

        # Create QPixmap from inverted QImage and scale it
        inverted_pixmap = QPixmap.fromImage(inverted_image)
        return inverted_pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    @staticmethod
    def get_button_style():
        return """
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: 2px solid #6a6a6a;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 2px solid #7a7a7a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """

    @staticmethod
    def get_list_style():
        return """
            QListWidget {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3a3a3a;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
        """

    def set_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2B2B2B;
                color: #FFFFFF;
            }
        """)

    def open_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "VANTAGE Project (*.vtp)")
        if filename:
            self.open_color_detection_app(filename)

    def open_recent_project(self, item):
        project_path = item.text()
        if os.path.exists(project_path):
            self.open_color_detection_app(project_path)
        else:
            QMessageBox.warning(self, "Error", f"Project file not found: {project_path}")
            self.recent_projects_manager.remove(project_path)
            self.load_recent_projects()

    def open_selected_project(self, item):
        project_path = item.text()
        if os.path.exists(project_path):
            self.open_color_detection_app(project_path)
        else:
            QMessageBox.warning(self, "Error", f"Project file not found: {project_path}")
            self.recent_projects_manager.remove(project_path)
            self.load_recent_projects()

    def create_project(self):
        settings = QSettings("VANTAGE", "ColorDetectionApp")
        default_port = settings.value("default_camera_port", 0, type=int)
        default_resolution = settings.value("default_resolution", "1280x720")

        dialog = DarkThemeDialog(self, "Create New Project")
        layout = QVBoxLayout(dialog)

        port_layout = QHBoxLayout()
        port_label = QLabel("Camera Port:")
        port_spinbox = QSpinBox()
        port_spinbox.setRange(0, 10)
        port_spinbox.setValue(default_port)
        port_layout.addWidget(port_label)
        port_layout.addWidget(port_spinbox)
        layout.addLayout(port_layout)

        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution:")
        resolution_input = QLineEdit(default_resolution)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(resolution_input)
        layout.addLayout(resolution_layout)

        name_layout = QHBoxLayout()
        name_label = QLabel("Project Name:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            port = port_spinbox.value()
            resolution = resolution_input.text()
            project_name = name_input.text()
            if project_name:
                project_path = f"{project_name}.vtp"
                self.open_color_detection_app(project_path, camera_port=port, resolution=resolution,
                                              is_new_project=True)
            else:
                QMessageBox.warning(self, "Error", "Project name cannot be empty.")

    def open_color_detection_app(self, project_path, camera_port=None, resolution=None, is_new_project=False):
        try:
            project_name = os.path.basename(project_path)
            if is_new_project:
                settings = {"camera_port": camera_port, "resolution": resolution}
            else:
                with open(project_path, 'r') as f:
                    settings = json.load(f)

            self.color_detection_app = ColorDetectionApp(settings.get('camera_port', 0),
                                                         settings.get('resolution', "1280x720"),
                                                         project_name,
                                                         settings,
                                                         self)
            self.color_detection_app.current_project_path = project_path
            self.color_detection_app.load_settings(settings)  # Add this line
            self.color_detection_app.show()
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the project: {str(e)}")


class DarkThemeDialog(QDialog):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QSpinBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #5d5d5d;
                padding: 5px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: 2px solid #6a6a6a;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)


@dataclass
class ParticleData:
    x: int
    y: int
    size: float
    color: str
    radius: int


class ParticleAnalyzer:
    def __init__(self, min_size=30, max_size=600, threshold=20):
        self.min_size = min_size
        self.max_size = max_size
        self.threshold = threshold

    def set_size_range(self, min_size, max_size):
        self.min_size = min_size
        self.max_size = max_size

    def detect_particles(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = self._enhance_image(gray)
        binary = self._create_binary_image(enhanced)

        # Apply distance transform
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)

        # Find unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(binary, sure_fg)

        # Marker labelling
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        # Apply watershed
        markers = cv2.watershed(frame, markers)

        return markers

    def _enhance_image(self, gray):
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(blurred)

    def _create_binary_image(self, enhanced):
        _, binary = cv2.threshold(enhanced, self.threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    def analyze_particles(self, markers, color):
        particles = []
        for label in range(2, markers.max() + 1):  # Start from 2 to skip background (0) and unknown (1)
            mask = np.zeros(markers.shape, dtype=np.uint8)
            mask[markers == label] = 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                contour = contours[0]
                area = cv2.contourArea(contour)
                if self.min_size < area < self.max_size:
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    particles.append(ParticleData(int(x), int(y), area, color, int(radius)))

        return particles


class VideoWidgetWithOverlay(QLabel):
    regionChanged = pyqtSignal()

    def __init__(self, title):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText(title)
        self.setStyleSheet("border: 2px solid gray; background-color: black; color: white;")
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.particles = []
        self.scale_factor = 1.0
        self.offset_x = self.offset_y = 0
        self.drawing = False
        self.green_boxes = []
        self.red_boxes = []
        self.current_box = None
        self.current_color = 'green'
        self.start_point = None
        self.setMouseTracking(True)
        self.original_pixmap = None

    def update_frame(self, frame, particles):
        self.particles = particles
        self.frame_size = (frame.shape[1], frame.shape[0])
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.original_pixmap = QPixmap.fromImage(qt_image)
        self.update_scaled_pixmap()

    def update_scaled_pixmap(self):
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.update_scale_and_offset()

    def update_scale_and_offset(self):
        if self.pixmap():
            pixmap_size = self.pixmap().size()
            widget_size = self.size()
            self.scale_factor = min(widget_size.width() / pixmap_size.width(),
                                    widget_size.height() / pixmap_size.height())
            self.offset_x = (widget_size.width() - pixmap_size.width() * self.scale_factor) / 2
            self.offset_y = (widget_size.height() - pixmap_size.height() * self.scale_factor) / 2

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scaled_pixmap()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw debug information
            painter.setPen(Qt.white)
            painter.drawText(10, 20, f"Widget size: {self.size().width()}x{self.size().height()}")
            painter.drawText(10, 40, f"Pixmap size: {self.pixmap().width()}x{self.pixmap().height()}")
            painter.drawText(10, 60, f"Scale factor: {self.scale_factor:.2f}")
            painter.drawText(10, 80, f"Offset: ({self.offset_x:.2f}, {self.offset_y:.2f})")
            painter.drawText(10, 100, f"Frame size: {self.frame_size[0]}x{self.frame_size[1]}")

            self._draw_particles(painter)
            self._draw_boxes(painter)
            self._draw_current_box(painter)

    def _draw_particles(self, painter):
        for particle in self.particles:
            # Calculate position based on original frame size
            rel_x = particle.x / self.frame_size[0]
            rel_y = particle.y / self.frame_size[1]

            x = int(rel_x * self.pixmap().width() + self.offset_x)
            y = int(rel_y * self.pixmap().height() + self.offset_y)

            radius = int((particle.radius / max(self.frame_size)) * min(self.pixmap().width(), self.pixmap().height()))

            color = QColor(255, 0, 0) if particle.color == 'red' else QColor(0, 255, 0)
            painter.setPen(QPen(color, 2))
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x + radius + 5, y, f"{particle.size:.0f}")

            # Draw debug cross at particle center
            painter.setPen(QPen(Qt.yellow, 1))
            painter.drawLine(x - 5, y, x + 5, y)
            painter.drawLine(x, y - 5, x, y + 5)

    def _draw_boxes(self, painter):
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        for box in self.green_boxes:
            painter.drawRect(self._scale_rect(box))

        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for box in self.red_boxes:
            painter.drawRect(self._scale_rect(box))

    def _draw_current_box(self, painter):
        if self.drawing and self.current_box:
            painter.setPen(QPen(Qt.green if self.current_color == 'green' else Qt.red, 2, Qt.SolidLine))
            painter.drawRect(self._scale_rect(self.current_box))

    def _scale_rect(self, rect):
        return QRect(
            int(rect.x() * self.scale_factor + self.offset_x),
            int(rect.y() * self.scale_factor + self.offset_y),
            int(rect.width() * self.scale_factor),
            int(rect.height() * self.scale_factor)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = self._unscale_point(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing:
            end_point = self._unscale_point(event.pos())
            self.current_box = QRect(self.start_point, end_point).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.current_box:
                (self.green_boxes if self.current_color == 'green' else self.red_boxes).append(self.current_box)
            self.current_box = self.start_point = None
            self.update()
            self.regionChanged.emit()

    def _unscale_point(self, pos):
        return QPoint(
            int((pos.x() - self.offset_x) / self.scale_factor),
            int((pos.y() - self.offset_y) / self.scale_factor)
        )

    def set_color(self, color):
        self.current_color = color

    def clear_boxes(self):
        self.green_boxes.clear()
        self.red_boxes.clear()
        self.update()


class ColorDetector:
    def __init__(self, initial_value):
        self.set_threshold(initial_value)

    def set_threshold(self, value):
        hue = int(value * 1.79)
        self.lower_threshold = np.array([max(0, hue - 20), 50, 50])
        self.upper_threshold = np.array([min(179, hue + 20), 255, 255])

    def detect(self, frame, color):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_threshold, self.upper_threshold)
        return cv2.bitwise_and(frame, frame, mask=mask)


class UserManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Manual")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        layout.addWidget(self.search_bar)

        # Search button
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_content)
        layout.addWidget(search_button)

        # Text browser for rendered markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)

        self.setLayout(layout)

        self.load_manual()

    def load_manual(self):
        manual_path = os.path.join(os.path.dirname(__file__), 'usermanual.md')
        try:
            with open(manual_path, 'r', encoding='utf-8') as file:
                content = file.read()

                # Convert markdown to HTML with extended features
                html = markdown.markdown(content, extensions=['fenced_code', 'codehilite', 'tables'])

                # Get the application's palette
                palette = QApplication.palette()

                # Determine if we're in dark mode
                is_dark = palette.color(QPalette.Window).lightness() < 128

                # Set colors based on the theme
                if is_dark:
                    bg_color = palette.color(QPalette.Window).name()
                    text_color = palette.color(QPalette.WindowText).name()
                    heading_color = "#88CCFF"
                    code_bg_color = "#2A2A2A"
                else:
                    bg_color = palette.color(QPalette.Window).name()
                    text_color = palette.color(QPalette.WindowText).name()
                    heading_color = "#333366"
                    code_bg_color = "#F0F0F0"

                css = f"""
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        background-color: {bg_color}; 
                        color: {text_color}; 
                    }}
                    h1, h2, h3 {{ color: {heading_color}; }}
                    code {{ 
                        background-color: {code_bg_color}; 
                        padding: 2px 4px; 
                        border-radius: 4px; 
                    }}
                    pre {{ 
                        background-color: {code_bg_color}; 
                        padding: 10px; 
                        border-radius: 4px; 
                        overflow-x: auto; 
                    }}
                    pre code {{ 
                        background-color: transparent; 
                        padding: 0; 
                    }}
                    a {{ color: {heading_color}; }}
                    table {{
        border-collapse: collapse;
        margin: 15px 0;
        width: 100%;
    }}
    th, td {{
        border: 1px solid {text_color};
        padding: 8px;
        text-align: left;
    }}
    th {{
        background-color: {code_bg_color};
        font-weight: bold;
    }}
                </style>
                """

                self.text_browser.setHtml(css + html)
        except FileNotFoundError:
            self.text_browser.setHtml("<h1>User manual file not found.</h1>")
        except Exception as e:
            self.text_browser.setHtml(f"<h1>An error occurred while reading the user manual:</h1><p>{str(e)}</p>")

    def search_content(self):
        search_text = self.search_bar.text()
        if search_text:
            # Clear previous search
            cursor = self.text_browser.textCursor()
            cursor.clearSelection()
            self.text_browser.setTextCursor(cursor)

            # Perform new search
            found = self.text_browser.find(search_text)
            if not found:
                # If not found, show a message
                self.text_browser.append(f"<br><i>Search term '{search_text}' not found.</i>")


class VideoProcessor:
    def __init__(self, camera_port, width, height):
        self.camera_port = camera_port
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(self.camera_port)
        self.set_resolution(width, height)
        self.red_detector = ColorDetector(0)
        self.green_detector = ColorDetector(0)
        self.red_analyzer = ParticleAnalyzer()
        self.green_analyzer = ParticleAnalyzer()
        self.particle_heights = []
        self.particle_analyzer = ParticleAnalyzer()


    def set_camera_port(self, camera_port):
        if camera_port != self.camera_port:
            self.camera_port = camera_port
            self.cap.release()
            self.cap = cv2.VideoCapture(self.camera_port)
            self.set_resolution(self.width, self.height)

    def set_resolution(self, width, height):
        self.width = width
        self.height = height
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, [], []

        frame = cv2.resize(frame, (self.width, self.height))

        # Process red particles
        red_frame = self.red_detector.detect(frame, 'red')
        red_markers = self.particle_analyzer.detect_particles(red_frame)
        red_particles = self.particle_analyzer.analyze_particles(red_markers, 'red')

        # Process green particles
        green_frame = self.green_detector.detect(frame, 'green')
        green_markers = self.particle_analyzer.detect_particles(green_frame)
        green_particles = self.particle_analyzer.analyze_particles(green_markers, 'green')

        self.particle_heights = [self.height - p.y for p in red_particles + green_particles]

        return frame, red_particles, green_particles

    def release(self):
        self.cap.release()


class ColorDetectionApp(QMainWindow):
    def __init__(self, camera_port, resolution, project_name, settings=None, main_menu=None):
        super().__init__()
        self.project_name = project_name
        self.settings = settings or {}
        self.main_menu = main_menu
        self.current_amp = 0.0
        self.setup_shortcuts()
        self.unsaved_changes = False
        self.current_project_path = None

        self.min_particle_size = 30
        self.max_particle_size = 600

        width, height = map(int, resolution.split('x'))
        self.video_processor = VideoProcessor(camera_port, width, height)

        # Initialize PID controller
        self.pid = PIDController(kp=0.1, ki=0.01, kd=0.05)
        self.height_setpoint = 50  # Initial setpoint (middle of the range)

        self.setup_ui()
        self.setup_timer()
        self.setup_pid_controller()
        self.create_menu()

        if settings:
            self.load_settings(settings)
        else:
            self.unsaved_changes = True

        self.update_title()

        self.apply_theme(True)

        self.setFocusPolicy(Qt.StrongFocus)

    def create_menu(self):
        menubar = self.menuBar()
        self.simulate_magnet_error = False  # Add this line

        # File menu
        file_menu = menubar.addMenu('&File')

        # Save action
        save_action = QAction('&Save', self)
        save_action.triggered.connect(self.save_project)
        if platform.system() == 'Darwin':  # macOS
            save_action.setShortcut(QKeySequence.Save)
        else:  # Windows and Linux
            save_action.setShortcut(QKeySequence.Save)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction('Save &As...', self)
        save_as_action.triggered.connect(self.save_project_as)
        if platform.system() == 'Darwin':  # macOS
            save_as_action.setShortcut(QKeySequence.SaveAs)
        else:  # Windows and Linux
            save_as_action.setShortcut(QKeySequence.SaveAs)
        file_menu.addAction(save_as_action)

        project_menu = menubar.addMenu('Project')

        project_settings_action = QAction('Project Settings', self)
        project_settings_action.triggered.connect(self.show_project_settings)
        project_menu.addAction(project_settings_action)


        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        user_manual_action = QAction('User Manual', self)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)

        # Magnet Debug
        magnet_debug_action = QAction('Magnet Debug', self)
        magnet_debug_action.triggered.connect(self.show_magnet_debug)
        project_menu.addAction(magnet_debug_action)

        debug_menu = menubar.addMenu('Simulate')

        simulate_magnet_error_action = QAction('Simulate Magnet Zero Error', self, checkable=True)
        simulate_magnet_error_action.triggered.connect(self.toggle_simulate_magnet_error)
        debug_menu.addAction(simulate_magnet_error_action)

        close_project_action = QAction('Close Project', self)
        close_project_action.triggered.connect(self.close_project)
        project_menu.addAction(close_project_action)

        # Preferences
        if platform.system() == 'Darwin':  # macOS
            preferences_action = QAction('Preferences...', self)
            preferences_action.setShortcut(QKeySequence.Preferences)
            preferences_action.triggered.connect(self.show_preferences)

            app_menu = menubar.addMenu('VANTAGE')
            app_menu.addAction(preferences_action)
        else:  # Windows and Linux
            preferences_action = QAction('Preferences...', self)
            preferences_action.setShortcut(QKeySequence('Ctrl+,'))
            preferences_action.triggered.connect(self.show_preferences)
            file_menu.addAction(preferences_action)

    def apply_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet(DARK_MODE_STYLE)
            app = QApplication.instance()
            app.setPalette(self.get_dark_palette())
        else:
            self.setStyleSheet("")
            app = QApplication.instance()
            app.setPalette(app.style().standardPalette())

        self.update_ui_for_theme(is_dark)

        # Update the checkbox state
        if hasattr(self, 'dark_mode_switch'):
            self.dark_mode_switch.setChecked(is_dark)
    @staticmethod
    def get_dark_palette():
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        return dark_palette

    def toggle_theme(self, state):
        is_dark = state == Qt.Checked
        self.apply_theme(is_dark)
        self.update_ui_for_theme(is_dark)
    def toggle_simulate_magnet_error(self, checked):
        self.simulate_magnet_error = checked
        if checked:
            QMessageBox.warning(self, 'Debug',
                                'Magnet zero error simulation is now ON. The app will show an error message when closing.')
        else:
            QMessageBox.information(self, 'Debug', 'Magnet zero error simulation is now OFF.')

    def update_ui_for_theme(self, is_dark):
        # Update specific UI elements for the theme
        if is_dark:
            text_color = "white"
            bg_color = "#2B2B2B"
        else:
            text_color = "black"
            bg_color = "white"

        # Update labels
        for label in self.findChildren(QLabel):
            label.setStyleSheet(f"color: {text_color};")

        # Update group boxes
        for group_box in self.findChildren(QGroupBox):
            group_box.setStyleSheet(f"color: {text_color}; background-color: {bg_color};")

        # Update sliders
        for slider in self.findChildren(QSlider):
            slider.setStyleSheet(f"background-color: {bg_color};")

        # Update buttons
        for button in self.findChildren(QPushButton):
            button.setStyleSheet(f"color: {text_color}; background-color: {bg_color};")

        # Update video widgets
        for video_widget in [self.original_view, self.red_view, self.green_view]:
            video_widget.setStyleSheet(f"color: {text_color}; background-color: black;")

        # Update the main window background
        self.setStyleSheet(f"background-color: {bg_color};")

    def show_magnet_debug(self):
        try:
            magnet_debug_dialog = MagnetDebugDialog(self)
            magnet_debug_dialog.exec_()
        except Exception as e:
            logging.error(f"Error in show_magnet_debug: {str(e)}")
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to open Magnet Debug dialog: {str(e)}")

    def remove_project_menus(self):
        menubar = self.menuBar()
        for action in menubar.actions():
            if action.text() in ['&File', 'Project']:
                menubar.removeAction(action)

    def setup_particle_size_control(self):
        group_box = QGroupBox("Particle Size Control")
        layout = QVBoxLayout()

        min_size_layout = QHBoxLayout()
        min_size_label = QLabel("Min Size:")
        self.min_size_spinbox = QSpinBox()
        self.min_size_spinbox.setRange(1, 249000)
        self.min_size_spinbox.setValue(self.min_particle_size)
        self.min_size_spinbox.valueChanged.connect(self.update_particle_size)
        min_size_layout.addWidget(min_size_label)
        min_size_layout.addWidget(self.min_size_spinbox)

        max_size_layout = QHBoxLayout()
        max_size_label = QLabel("Max Size:")
        self.max_size_spinbox = QSpinBox()
        self.max_size_spinbox.setRange(1, 250000)
        self.max_size_spinbox.setValue(self.max_particle_size)
        self.max_size_spinbox.valueChanged.connect(self.update_particle_size)
        max_size_layout.addWidget(max_size_label)
        max_size_layout.addWidget(self.max_size_spinbox)

        layout.addLayout(min_size_layout)
        layout.addLayout(max_size_layout)
        group_box.setLayout(layout)
        self.control_layout.addWidget(group_box)

    def setup_height_control(self):
        self.height_slider = QSlider(Qt.Vertical)
        self.height_slider.setRange(0, 100)
        self.height_slider.setValue(50)
        self.height_slider.setTickPosition(QSlider.TicksRight)
        self.height_slider.setTickInterval(10)
        self.height_slider.valueChanged.connect(self.update_height_setpoint)

        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.height_slider)
        slider_widget = QWidget()
        slider_widget.setLayout(slider_layout)

        main_layout = self.centralWidget().layout()
        main_layout.addWidget(slider_widget)

    def setup_pid_controller(self):
        self.pid_timer = QTimer()
        self.pid_timer.timeout.connect(self.update_particle_height)
        self.pid_timer.start(100)

    def setup_pid_controls(self):
        pid_group = QGroupBox("PID Control")
        pid_layout = QVBoxLayout()

        # Height setpoint slider
        self.height_setpoint_slider = QSlider(Qt.Horizontal)
        self.height_setpoint_slider.setRange(0, 100)
        self.height_setpoint_slider.setValue(50)
        self.height_setpoint_slider.valueChanged.connect(self.update_height_setpoint)
        pid_layout.addWidget(QLabel("Height Setpoint:"))
        pid_layout.addWidget(self.height_setpoint_slider)

        # PID parameter inputs
        for param in ['Kp', 'Ki', 'Kd']:
            layout = QHBoxLayout()
            layout.addWidget(QLabel(f"{param}:"))
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0, 1)
            spinbox.setSingleStep(0.01)
            spinbox.setValue(getattr(self.pid, param.lower()))
            spinbox.valueChanged.connect(lambda value, param=param: self.update_pid_param(param, value))
            setattr(self, f"{param.lower()}_spinbox", spinbox)
            layout.addWidget(spinbox)
            pid_layout.addLayout(layout)

        pid_group.setLayout(pid_layout)
        self.control_layout.addWidget(pid_group)

    def update_height_setpoint(self, value):
        self.height_setpoint = value

    def update_particle_height(self):
        if not self.particle_heights:
            return

        current_height = np.mean(self.particle_heights)
        normalized_height = current_height / self.video_processor.height  # Normalize to 0-1 range
        normalized_setpoint = self.height_setpoint / 100  # Convert from 0-100 to 0-1 range

        output = self.pid.compute(normalized_setpoint, normalized_height, dt=0.1)
        self.adjust_magnet_strength(output)

        # Update UI with current values
        self.update_pid_info(normalized_setpoint, normalized_height, output)

    def adjust_magnet_strength(self, strength):
        # Clamp the strength to a reasonable range, e.g., -1 to 1
        strength = max(-1, min(1, strength))
        self.pid_intended_output = strength * 3  # Assuming 3 is the max amp

        if self.pid_active:
            # Scale the strength to appropriate voltage ranges
            upM = strength * 2.28  # Assuming max voltage is 2.28V
            botM = -strength * 2.28

            try:
                setChanVolt(4, upM)
                setChanVolt(7, botM)
                self.current_amp = self.pid_intended_output
                logging.info(f'Magnet strength adjusted: Up = {upM}V, Bottom = {botM}V, Amp = {self.current_amp:.2f}')
            except Exception as e:
                logging.error(f"Error adjusting magnet strength: {e}")
                QMessageBox.warning(self, "Error", f"Failed to adjust magnet strength: {str(e)}")

        self.updateAmpOutput()

    def select_camera_port(self):
        current_port = int(self.video_processor.cap.get(cv2.CAP_PROP_POS_FRAMES))
        port, ok = QInputDialog.getInt(self, "Camera Port", "Enter the USB camera port:",
                                       current_port, 0, 10)
        if ok:
            self.video_processor.release()
            self.video_processor = VideoProcessor(port)
            self.unsaved_changes = True
            self.update_title()

    def update_pid_info(self, setpoint, current_height, output):
        info_text = (f"Setpoint: {setpoint:.2f}\n"
                     f"Current Height: {current_height:.2f}\n"
                     f"PID Output: {output:.2f}")
        if hasattr(self, 'pid_info_label'):
            self.pid_info_label.setText(info_text)
        else:
            self.pid_info_label = QLabel(info_text)
            self.control_layout.addWidget(self.pid_info_label)

    def close_project(self):
        self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'icon_label'):
            self.icon_label.setGeometry(self.width() - 40, 10, 32, 32)

    def show_preferences(self):
        try:
            preferences_dialog = PreferencesDialog(self)
            preferences_dialog.apply_theme(self.dark_mode_switch.isChecked())
            if preferences_dialog.exec_() == QDialog.Accepted:
                self.load_preferences()
        except Exception as e:
            logging.error(f"Error in show_preferences: {str(e)}")
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to show preferences: {str(e)}")


    def update_magnet_amp_display(self):
        self.magnet_amp_label.setText(f"Current Magnet Amp: {self.current_amp:.2f}")

    def get_current_magnet_amp(self):

        return self.current_amp if hasattr(self, 'current_amp') else 0.0

    def show_project_settings(self):
        current_settings = {
            'camera_port': self.video_processor.camera_port,
            'resolution': f"{self.video_processor.width}x{self.video_processor.height}"
        }
        dialog = ProjectSettingsDialog(self, current_settings)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.apply_project_settings(new_settings)
            self.unsaved_changes = True
            self.update_title()

    def show_about(self):
        about_dialog = AboutDialog(self)
        if hasattr(self, 'dark_mode_switch'):
            about_dialog.apply_theme(self.dark_mode_switch.isChecked())
        else:
            # Default to dark theme if dark_mode_switch doesn't exist
            about_dialog.apply_theme(True)
        about_dialog.exec_()

    def show_user_manual(self):
        user_manual_dialog = UserManualDialog(self)
        user_manual_dialog.exec_()


    def show_save_icon(self):
        self.show_icon("assets/save_icon.svg", "Project Saved")

    def show_autosave_icon(self):
        self.show_icon("assets/autosave_icon.svg", "Project Auto-saved")

    def show_icon(self, icon_path, tooltip):
        if not hasattr(self, 'icon_label'):
            self.icon_label = QLabel(self)
            self.icon_label.setStyleSheet("background-color: transparent;")
            self.icon_label.setGeometry(self.width() - 40, 10, 32, 32)

            self.opacity_effect = QGraphicsOpacityEffect(self.icon_label)
            self.icon_label.setGraphicsEffect(self.opacity_effect)

        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            print(f"Failed to load icon: {icon_path}")
            return

        scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(scaled_pixmap)
        self.icon_label.setToolTip(tooltip)

        self.opacity_effect.setOpacity(1.0)
        self.icon_label.raise_()
        self.icon_label.show()

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.finished.connect(self.icon_label.hide)
        QTimer.singleShot(3000, self.start_fade_out)
        QTimer.singleShot(5000, self.icon_label.hide)

    def start_fade_out(self):
        if hasattr(self, 'fade_animation'):
            self.fade_animation.start()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def apply_particle_analysis_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.red_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
            self.video_processor.green_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
        if hasattr(self, 'min_size_spinbox'):
            self.min_size_spinbox.setValue(self.min_particle_size)
        if hasattr(self, 'max_size_spinbox'):
            self.max_size_spinbox.setValue(self.max_particle_size)

    def load_preferences(self):
        settings = QSettings("VANTAGE", "ColorDetectionApp")

        # Load general preferences
        self.default_project_location = settings.value("default_project_location", "")
        self.auto_save_interval = int(settings.value("auto_save_interval", 5))

        # Load camera preferences
        self.default_camera_port = int(settings.value("default_camera_port", 0))
        self.default_resolution = settings.value("default_resolution", "1280x720")

        # Load particle analysis preferences
        self.min_particle_size = int(settings.value("min_particle_size", 30))
        self.max_particle_size = int(settings.value("max_particle_size", 600))

        # Apply the loaded preferences
        self.setup_auto_save()
        self.apply_camera_settings()
        self.apply_particle_analysis_settings()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def apply_project_settings(self, settings):
        # Apply the new settings to the project
        self.video_processor.set_camera_port(settings.get('camera_port', 0))
        width, height = map(int, settings.get('resolution', '1280x720').split('x'))
        self.video_processor.set_resolution(width, height)

        # Only update these values if they are present in the settings
        if 'red_threshold' in settings:
            red_threshold = settings['red_threshold']
            self.red_slider.setValue(red_threshold)
            self.red_value_label.setText(f"Value: {red_threshold}")
            self.video_processor.red_detector.set_threshold(red_threshold)

        if 'green_threshold' in settings:
            green_threshold = settings['green_threshold']
            self.green_slider.setValue(green_threshold)
            self.green_value_label.setText(f"Value: {green_threshold}")
            self.video_processor.green_detector.set_threshold(green_threshold)

        if 'min_particle_size' in settings and 'max_particle_size' in settings:
            min_size = settings['min_particle_size']
            max_size = settings['max_particle_size']
            self.min_size_spinbox.setValue(min_size)
            self.max_size_spinbox.setValue(max_size)
            self.video_processor.red_analyzer.set_size_range(min_size, max_size)
            self.video_processor.green_analyzer.set_size_range(min_size, max_size)



    def setup_auto_save(self):
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(self.auto_save_interval * 60 * 1000)  # Convert minutes to milliseconds

    def apply_color_detection_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.red_detector.set_threshold(self.red_threshold)
            self.video_processor.green_detector.set_threshold(self.green_threshold)

        # Update UI elements if they exist
        if hasattr(self, 'red_slider'):
            self.red_slider.setValue(self.red_threshold)
        if hasattr(self, 'green_slider'):
            self.green_slider.setValue(self.green_threshold)



    def update_particle_size(self):
        self.min_particle_size = self.min_size_spinbox.value()
        self.max_particle_size = self.max_size_spinbox.value()
        self.video_processor.red_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
        self.video_processor.green_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
        self.unsaved_changes = True
        self.update_title()

    def auto_save(self):
        if self.current_project_path and self.unsaved_changes:
            self.save_project()
            self.show_autosave_icon()

    def apply_camera_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.set_camera_port(self.default_camera_port)
            width, height = map(int, self.default_resolution.split('x'))
            self.video_processor.set_resolution(width, height)

    def setup_ui(self):
        self.setWindowTitle(f"VANTAGE - {self.project_name}")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.setup_video_widget(splitter)
        self.setup_control_widget(splitter)

        splitter.setSizes([800, 400])

    def setup_logo(self):
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/v3/vtg_icon_comet.png")
        logo_pixmap = logo_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        return logo_label

    def setup_shortcuts(self):
        os_name = platform.system()

        if os_name == 'Darwin':
            save_shortcut = QShortcut(QKeySequence('Cmd+S'), self)
        else:
            save_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        save_shortcut.activated.connect(self.save_project)

        if os_name == 'Darwin':
            save_as_shortcut = QShortcut(QKeySequence('Cmd+Shift+S'), self)
        else:  # Windows and Linux
            save_as_shortcut = QShortcut(QKeySequence('Ctrl+Shift+S'), self)
        save_as_shortcut.activated.connect(self.save_project_as)

    def setup_video_widget(self, parent):
        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        parent.addWidget(video_widget)

        self.original_view = VideoWidgetWithOverlay("Original Feed")
        video_layout.addWidget(self.original_view)

        detection_layout = QHBoxLayout()
        video_layout.addLayout(detection_layout)

        self.red_view = VideoWidgetWithOverlay("Red Detection")
        self.green_view = VideoWidgetWithOverlay("Green Detection")
        detection_layout.addWidget(self.red_view)
        detection_layout.addWidget(self.green_view)

    def setup_control_widget(self, parent):
        control_widget = QWidget()
        self.control_layout = QVBoxLayout(control_widget)
        parent.addWidget(control_widget)

        # Add a horizontal layout for the project name and logo
        header_layout = QHBoxLayout()
        self.control_layout.addLayout(header_layout)

        # Add project name label
        self.project_name_label = QLabel(self.project_name)
        self.project_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.project_name_label)

        # Add stretching space
        header_layout.addStretch()

        # Add logo
        logo_label = self.setup_logo()
        header_layout.addWidget(logo_label)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.control_layout.addWidget(separator)

        # Rest of the controls
        self.setup_color_control("Red", self.video_processor.red_detector, 4)
        self.setup_color_control("Green", self.video_processor.green_detector, 25)
        self.setup_particle_size_control()
        self.setup_particle_info()
        self.setup_roi_controls()
        self.setup_dark_mode_switch()
        self.setup_pid_controls()
        self.setupPIDStop()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def setupPIDStop(self):
        pid_stop_group = QGroupBox("PID Control Output")
        pid_stop_layout = QHBoxLayout()

        self.pid_output_label = QLabel("PID AMP OUTPUT: 0.00")
        self.pid_output_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        pid_stop_layout.addWidget(self.pid_output_label)

        self.pid_arrow_button = QPushButton("→")
        self.pid_arrow_button.setFixedSize(40, 40)
        self.pid_arrow_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 24px;
                background-color: #4a4a4a;
                border: 2px solid #6a6a6a;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        self.pid_arrow_button.clicked.connect(self.togglePIDOutput)
        pid_stop_layout.addWidget(self.pid_arrow_button)

        self.amp_output_label = QLabel("AMP OUTPUT: 0.00")
        self.amp_output_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        pid_stop_layout.addWidget(self.amp_output_label)

        pid_stop_group.setLayout(pid_stop_layout)
        self.control_layout.addWidget(pid_stop_group)

        self.pid_active = True
        self.pid_intended_output = 0.00

    def togglePIDOutput(self):
        self.pid_active = not self.pid_active
        if self.pid_active:
            self.pid_arrow_button.setText("→")
        else:
            self.pid_arrow_button.setText("↛")
        self.updateAmpOutput()

    def updateAmpOutput(self):
        self.pid_output_label.setText(f"PID AMP OUTPUT: {self.pid_intended_output:.2f}")
        if self.pid_active:
            self.amp_output_label.setText(f"AMP OUTPUT: {self.current_amp:.2f}")
        else:
            self.amp_output_label.setText("AMP OUTPUT: N/A")

    def update_frame(self):
        frame, red_particles, green_particles = self.video_processor.process_frame()
        if frame is not None:
            self.original_view.update_frame(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), red_particles + green_particles)
            self.red_view.update_frame(
                cv2.cvtColor(self.video_processor.red_detector.detect(frame, 'red'), cv2.COLOR_BGR2RGB), red_particles)
            self.green_view.update_frame(
                cv2.cvtColor(self.video_processor.green_detector.detect(frame, 'green'), cv2.COLOR_BGR2RGB),
                green_particles)

            # Calculate particle heights
            frame_height = frame.shape[0]
            self.particle_heights = [frame_height - p.y for p in red_particles + green_particles]

            self.update_particle_info(red_particles, green_particles)
            self.check_beads_in_rois(red_particles + green_particles)


    def setup_color_control(self, color, detector, initial_value):
        group_box = QGroupBox(f"{color} Control")
        layout = QVBoxLayout()

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(initial_value)

        value_label = QLabel(f"Value: {initial_value}")

        def update_value(value):
            value_label.setText(f"Value: {value}")
            detector.set_threshold(value)
            self.unsaved_changes = True
            self.update_title()

        slider.valueChanged.connect(update_value)

        if color.lower() == 'red':
            self.red_slider = slider
            self.red_value_label = value_label
        else:
            self.green_slider = slider
            self.green_value_label = value_label

        layout.addWidget(slider)
        layout.addWidget(value_label)
        group_box.setLayout(layout)
        self.control_layout.addWidget(group_box)

    def setup_particle_info(self):
        self.particle_info_label = QLabel("Particle Information")
        self.particle_info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.control_layout.addWidget(self.particle_info_label)

    def setup_roi_controls(self):
        roi_controls = QGroupBox("ROI Controls")
        roi_layout = QVBoxLayout()

        color_group = QButtonGroup(self)
        green_btn = QRadioButton("Green")
        red_btn = QRadioButton("Red")
        green_btn.setChecked(True)
        color_group.addButton(green_btn)
        color_group.addButton(red_btn)
        green_btn.toggled.connect(lambda: self.set_roi_color('green'))
        red_btn.toggled.connect(lambda: self.set_roi_color('red'))

        clear_roi_button = QPushButton("Clear ROIs")
        clear_roi_button.clicked.connect(self.clear_rois)

        roi_layout.addWidget(green_btn)
        roi_layout.addWidget(red_btn)
        roi_layout.addWidget(clear_roi_button)

        roi_controls.setLayout(roi_layout)
        self.control_layout.addWidget(roi_controls)

        self.region_display = QLabel("Region Information")
        self.region_display.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.control_layout.addWidget(self.region_display)

    def update_pid_param(self, param, value):
        setattr(self.pid, param.lower(), value)

    def setup_dark_mode_switch(self):
        self.dark_mode_switch = QCheckBox("Dark Mode")
        self.dark_mode_switch.setChecked(True)  # Set to checked by default
        self.dark_mode_switch.stateChanged.connect(self.toggle_theme)
        self.control_layout.addWidget(self.dark_mode_switch)

    def update_particle_info(self, red_particles, green_particles):
        red_count = len(red_particles)
        green_count = len(green_particles)

        red_avg_size = sum(p.size for p in red_particles) / red_count if red_count > 0 else 0
        green_avg_size = sum(p.size for p in green_particles) / green_count if green_count > 0 else 0

        info_text = f"Red Particles: {red_count} (Avg Size: {red_avg_size:.2f})\n"
        info_text += f"Green Particles: {green_count} (Avg Size: {green_avg_size:.2f})"

        self.particle_info_label.setText(info_text)


    def check_beads_in_rois(self, particles):
        green_count = red_count = error_count = 0

        for particle in particles:
            point = QPoint(particle.x, particle.y)
            in_green = any(box.contains(point) for box in self.original_view.green_boxes)
            in_red = any(box.contains(point) for box in self.original_view.red_boxes)

            if in_green and particle.color == 'green':
                green_count += 1
            elif in_red and particle.color == 'red':
                red_count += 1
            elif (in_green and particle.color == 'red') or (in_red and particle.color == 'green'):
                error_count += 1

        self.update_region_display(green_count, red_count, error_count)

    def update_region_display(self, green_count, red_count, error_count):

        '''info_text = f"Green Count: {green_count}\nRed Count: {red_count}\nError Count: {error_count}"
        self.region_display.setText(info_text)'''
        pass

    def set_roi_color(self, color):
        self.original_view.set_color(color)
        self.unsaved_changes = True
        self.update_title()

    def clear_rois(self):
        self.original_view.clear_boxes()
        self.red_view.clear_boxes()
        self.green_view.clear_boxes()
        self.unsaved_changes = True
        self.update_title()

    def update_title(self):
        title = f"VANTAGE - {self.project_name}"
        if self.unsaved_changes:
            title += " *"
        self.setWindowTitle(title)
        self.project_name_label.setText(self.project_name)

    def save_project(self):
        if not self.current_project_path:
            self.save_project_as()
            self.show_save_icon()
        else:
            self._save_project(self.current_project_path)
            self.show_save_icon()


    def save_project_as(self):
        suggested_name = f"{self.project_name}.vtp" if not self.project_name.endswith('.vtp') else self.project_name
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", suggested_name, "VANTAGE Project (*.vtp)")
        if filename:
            self._save_project(os.path.abspath(filename))
            QMessageBox.information(self, "Project Saved", f"Project saved successfully to: {filename}")
        else:
            pass

    def _save_project(self, filename):
        if not filename.lower().endswith('.vtp'):
            filename += '.vtp'

        settings = {
            'camera_port': self.video_processor.camera_port,
            'resolution': f"{self.video_processor.width}x{self.video_processor.height}",
            'red_threshold': self.red_slider.value(),
            'green_threshold': self.green_slider.value(),
            'min_particle_size': self.min_size_spinbox.value(),
            'max_particle_size': self.max_size_spinbox.value(),
            'green_boxes': [box.getRect() for box in self.original_view.green_boxes],
            'red_boxes': [box.getRect() for box in self.original_view.red_boxes]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(settings, f)
            self.current_project_path = filename
            self.project_name = os.path.basename(filename)
            self.unsaved_changes = False
            self.update_title()
            if self.main_menu:
                self.main_menu.recent_projects_manager.add(self.current_project_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")

    def load_settings(self, settings):
        # Update camera settings
        self.video_processor.set_camera_port(settings.get('camera_port', 0))
        width, height = map(int, settings.get('resolution', '1280x720').split('x'))
        self.video_processor.set_resolution(width, height)

        # Update color thresholds
        red_threshold = settings.get('red_threshold', 20)
        green_threshold = settings.get('green_threshold', 20)
        self.red_slider.setValue(red_threshold)
        self.green_slider.setValue(green_threshold)
        self.video_processor.red_detector.set_threshold(red_threshold)
        self.video_processor.green_detector.set_threshold(green_threshold)

        # Update particle size settings
        self.min_particle_size = settings.get('min_particle_size', 30)
        self.max_particle_size = settings.get('max_particle_size', 600)
        self.min_size_spinbox.setValue(self.min_particle_size)
        self.max_size_spinbox.setValue(self.max_particle_size)
        self.video_processor.red_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
        self.video_processor.green_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)

        # Load ROIs
        self.original_view.green_boxes = [QRect(*box) for box in settings.get('green_boxes', [])]
        self.original_view.red_boxes = [QRect(*box) for box in settings.get('red_boxes', [])]

        self.original_view.update()
        self.unsaved_changes = False
        self.update_title()

    def closeEvent(self, event):
        try:
            self.timer.stop()
            self.video_processor.release()

            try:
                if self.simulate_magnet_error:
                    raise Exception("Simulated magnet zeroing error")
                setChanVolt(4, 0)
                setChanVolt(7, 0)
                logging.info('Magnet settings zeroed.')
            except Exception as e:
                error_msg = f"Failed to zero magnets: {str(e)}"
                logging.critical(error_msg)

                error_dialog = FlashingTimedDialog(
                    'CRITICAL ERROR',
                    'MAGNET AMP FAILED TO ZERO. MANUALLY SHUTDOWN POWER SUPPLIES AND ZERO MAGNET AMP USING BACKUP SOFTWARE',
                    8,
                    self
                )
                error_dialog.exec_()

            if self.unsaved_changes:
                reply = QMessageBox.question(self, 'Save Project',
                                             "Do you want to save the project before closing?",
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

                if reply == QMessageBox.Yes:
                    self.save_project()
                    QMessageBox.information(self, "Project Saved", "Project saved successfully.")
                    if self.unsaved_changes:  # If user cancelled the save dialog
                        event.ignore()
                        return
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return

            if self.current_project_path and self.main_menu:
                self.main_menu.recent_projects_manager.add(self.current_project_path)
                self.main_menu.update_recent_projects()

            if self.main_menu:
                self.remove_project_menus()
                self.main_menu.show()

            # Close the PID graph window if it's open
            if hasattr(self, 'pid_graph_window') and self.pid_graph_window:
                self.pid_graph_window.close()

            event.accept()
        except Exception as e:
            error_msg = f"An error occurred while closing the application: {str(e)}\n{traceback.format_exc()}"
            logging.critical(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            event.ignore()


class FadingSplashScreen(QSplashScreen):
    def __init__(self, logo_path):
        pixmap = QPixmap(QSize(600, 450))

        painter = QPainter(pixmap)

        gradient = QLinearGradient(0, 0, 0, pixmap.height())
        gradient.setColorAt(0, QColor(230, 230, 250))
        gradient.setColorAt(1, QColor(201, 160, 220))

        painter.fillRect(pixmap.rect(), gradient)

        logo = QPixmap(logo_path)
        scaled_logo = logo.scaled(520, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_rect = scaled_logo.rect()
        logo_rect.moveCenter(pixmap.rect().center())
        painter.drawPixmap(logo_rect, scaled_logo)

        painter.end()

        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(2000)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutQuad)

    def fadeOut(self):
        self.fade_anim.start()


class AppLoader(QObject):
    progress_updated = pyqtSignal(int, str)
    loading_finished = pyqtSignal(MainMenu)

    def __init__(self):
        super().__init__()
        self.main_menu = None

    def load(self):

        if not FAST_BOOT: time.sleep(0.4)
        self.progress_updated.emit(0, "Initializing application...")
        self.main_menu = MainMenu()
        if not FAST_BOOT: time.sleep(0.1)
        self.progress_updated.emit(r.randint(10, 32), "Initializing application...")
        if not FAST_BOOT: time.sleep(0.1)



        self.progress_updated.emit(40, "Setting up user interface...")
        self.main_menu.setup_ui()
        if not FAST_BOOT: time.sleep(0.2)
        self.progress_updated.emit(r.randint(42, 58), "Setting up user interface...")
        if not FAST_BOOT: time.sleep(0.3)

        self.progress_updated.emit(60, "Creating menu...")
        if not FAST_BOOT: time.sleep(0.1)
        self.progress_updated.emit(r.randint(63,79), "Creating menu...")
        if not FAST_BOOT: time.sleep(r.randint(50,200)/100)


        self.progress_updated.emit(80, "Loading preferences...")
        self.main_menu.load_preferences()
        if not FAST_BOOT: time.sleep(r.randint(0,20)/100)

        self.progress_updated.emit(90, "Loading recent projects...")
        self.main_menu.load_recent_projects()
        if not FAST_BOOT: time.sleep(0.2)
        self.progress_updated.emit(r.randint(91,99), "Loading recent projects...")

        self.progress_updated.emit(100, "Finalizing...")
        if not FAST_BOOT: time.sleep(r.randint(50, 200) / 100)
        self.loading_finished.emit(self.main_menu)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VANTAGE")
    app.setStyle("Fusion")
    app.setPalette(ColorDetectionApp.get_dark_palette())
    app.setStyleSheet(DARK_MODE_STYLE)

    app_icon = QIcon()
    icon_sizes = [16, 24, 32, 48, 64, 128, 256]

    if platform.system() == 'Windows':
        # Windows-specific setup
        myappid = 'vxsoftware.vantage.beta.214b'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        icon_path = 'assets/vantage.ico'
        app_icon.addFile(icon_path)
    elif platform.system() == 'Darwin':  # macOS
        icon_path = 'assets/v3/vtg_icon_comet.icns'
        app_icon.addFile(icon_path)
    else:
        icon_path = 'assets/v3/vtg_icon_comet.png'
        for size in icon_sizes:
            app_icon.addFile(icon_path, QSize(size, size))

    app.setWindowIcon(app_icon)

    splash = LoadingSplashScreen("assets/v3/vtg_logo_full_splash")
    splash.show()

    loader = AppLoader()
    loader.progress_updated.connect(splash.setProgress)

    def on_loading_finished(main_menu):
        main_menu.setWindowIcon(app_icon)
        main_menu.show()
        splash.finish(main_menu)

    loader.loading_finished.connect(on_loading_finished)

    QTimer.singleShot(100, loader.load)

    sys.exit(app.exec_())
