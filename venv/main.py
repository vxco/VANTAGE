import json
import os
import platform
import sys
from dataclasses import dataclass

import cv2
import markdown
import numpy as np
from PyQt5.QtCore import QTimer, QPointF, QRect, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QLinearGradient, QPalette,  QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QLabel, QSlider, QGroupBox, QSplitter, QCheckBox, QRadioButton, QButtonGroup, QSplashScreen, QMessageBox
)
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QTextBrowser
from PyQt5.QtWidgets import QFileDialog, QAction

if platform.system() == 'Darwin':  # macOS
    from Foundation import NSBundle
    bundle = NSBundle.mainBundle()
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    info['CFBundleName'] = "VANTAGE"

VERSION = "2.1.4b"




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

    def detect_particles(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        _, binary = cv2.threshold(enhanced, self.threshold, 255, cv2.THRESH_BINARY)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def analyze_particles(self, contours, color):
        return [
            ParticleData(int(x), int(y), area, color, int(radius))
            for contour in contours
            if self.min_size < (area := cv2.contourArea(contour)) < self.max_size
            for ((x, y), radius) in [cv2.minEnclosingCircle(contour)]
        ]


class VideoWidgetWithOverlay(QLabel):
    def __init__(self, title):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText(title)
        self.setStyleSheet("border: 2px solid gray; background-color: black; color: white;")
        self.setMinimumSize(320, 240)
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

    def update_frame(self, frame, particles):
        self.particles = particles
        h, w, ch = frame.shape
        qt_image = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)

        self.scale_factor = min(self.width() / w, self.height() / h)
        self.offset_x = (self.width() - w * self.scale_factor) / 2
        self.offset_y = (self.height() - h * self.scale_factor) / 2

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.current_box = QRect(self.start_point, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.current_box:
                (self.green_boxes if self.current_color == 'green' else self.red_boxes).append(self.current_box)
            self.current_box = self.start_point = None
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            for particle in self.particles:
                x = int(particle.x * self.scale_factor + self.offset_x)
                y = int(particle.y * self.scale_factor + self.offset_y)
                radius = int(particle.radius * self.scale_factor)

                painter.setPen(QPen(QColor(255, 0, 0) if particle.color == 'red' else QColor(0, 255, 0), 2))
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x + radius + 5, y, f"{particle.size:.0f}")

            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
            for box in self.green_boxes:
                painter.drawRect(box)

            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            for box in self.red_boxes:
                painter.drawRect(box)

            if self.drawing and self.current_box:
                painter.setPen(QPen(Qt.green if self.current_color == 'green' else Qt.red, 2, Qt.SolidLine))
                painter.drawRect(self.current_box)

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


class ColorDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.red_detector = ColorDetector(4)
        self.green_detector = ColorDetector(25)

        self.red_analyzer = ParticleAnalyzer()
        self.green_analyzer = ParticleAnalyzer()

        self.particle_info_label = None
        self.dark_mode = True
        self.setup_ui()
        self.create_menu()
        self.set_theme(self.dark_mode)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        save_action = QAction('Save Settings', self)
        save_action.triggered.connect(self.save_settings)
        file_menu.addAction(save_action)

        load_action = QAction('Load Settings', self)
        load_action.triggered.connect(self.load_settings)
        file_menu.addAction(load_action)

        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        user_manual_action = QAction('User Manual', self)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)

    def setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(splitter)

        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        splitter.addWidget(video_widget)

        self.original_view = VideoWidgetWithOverlay("Original Feed")
        video_layout.addWidget(self.original_view)

        detection_layout = QHBoxLayout()
        video_layout.addLayout(detection_layout)

        self.red_view = VideoWidgetWithOverlay("Red Detection")
        self.green_view = VideoWidgetWithOverlay("Green Detection")
        detection_layout.addWidget(self.red_view)
        detection_layout.addWidget(self.green_view)

        control_widget = QWidget()
        self.control_layout = QVBoxLayout(control_widget)
        splitter.addWidget(control_widget)

        self.setup_color_control("Red", self.red_detector, 4)
        self.setup_color_control("Green", self.green_detector, 25)

        self.particle_info_label = QLabel("Particle Information")
        self.particle_info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.control_layout.addWidget(self.particle_info_label)

        self.dark_mode_switch = QCheckBox("Dark Mode")
        self.dark_mode_switch.setChecked(self.dark_mode)
        self.dark_mode_switch.stateChanged.connect(self.toggle_theme)
        self.control_layout.addWidget(self.dark_mode_switch)

        splitter.setSizes([800, 400])

        self.setup_roi_controls()

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

    def toggle_theme(self, state):
        self.dark_mode = state == Qt.Checked
        self.set_theme(self.dark_mode)

    def set_theme(self, is_dark):
        if is_dark:
            bg_color = "#2B2B2B"
            text_color = "#FFFFFF"
            border_color = "#555555"
            handle_color = "#4A4A4A"
        else:
            bg_color = "#FFFFFF"
            text_color = "#000000"
            border_color = "#CCCCCC"
            handle_color = "#DDDDDD"

        style = f"""
            QMainWindow, QWidget {{ background-color: {bg_color}; color: {text_color}; }}
            QLabel, QCheckBox, QRadioButton, QPushButton {{ color: {text_color}; }}
            QGroupBox {{ border: 1px solid {border_color}; margin-top: 0.5em; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }}
            QSlider::handle:horizontal {{ background-color: {handle_color}; }}
            QSplitter::handle {{ background-color: {border_color}; }}
        """
        self.setStyleSheet(style)

        for widget in self.findChildren(QWidget):
            widget.setStyleSheet(style)

            # Update specific widgets that might need additional styling
        self.original_view.setStyleSheet(f"border: 2px solid {border_color}; background-color: black; color: white;")
        self.red_view.setStyleSheet(f"border: 2px solid {border_color}; background-color: black; color: white;")
        self.green_view.setStyleSheet(f"border: 2px solid {border_color}; background-color: black; color: white;")

    def set_roi_color(self, color):
        self.original_view.set_color(color)

    def clear_rois(self):
        self.original_view.clear_boxes()

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

        slider.valueChanged.connect(update_value)

        if color.lower() == 'red':
            self.red_slider = slider
        else:
            self.green_slider = slider

        layout.addWidget(slider)
        layout.addWidget(value_label)
        group_box.setLayout(layout)
        self.control_layout.addWidget(group_box)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (960, 360))

            red_frame = self.red_detector.detect(frame, 'red')
            green_frame = self.green_detector.detect(frame, 'green')

            red_contours = self.red_analyzer.detect_particles(red_frame)
            green_contours = self.green_analyzer.detect_particles(green_frame)

            red_particles = self.red_analyzer.analyze_particles(red_contours, 'red')
            green_particles = self.green_analyzer.analyze_particles(green_contours, 'green')

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.original_view.update_frame(frame_rgb, red_particles + green_particles)

            red_frame_rgb = cv2.cvtColor(red_frame, cv2.COLOR_BGR2RGB)
            self.red_view.update_frame(red_frame_rgb, red_particles)

            green_frame_rgb = cv2.cvtColor(green_frame, cv2.COLOR_BGR2RGB)
            self.green_view.update_frame(green_frame_rgb, green_particles)

            self.update_particle_info(red_particles, green_particles)
            self.check_beads_in_rois(red_particles + green_particles)

    def show_about(self):
        about_text = f"VANTAGE \n\nVersion: {VERSION}\n\nVision Assisted Nano-particle Tracking and Guided Extraction\n\n Developed by Alfa Ozaltin and Nil Ertok @ Stanford University"
        QMessageBox.about(self, "About VANTAGE", about_text)

    def save_settings(self):
        settings = {
            'red_slider_value': self.red_slider.value(),
            'green_slider_value': self.green_slider.value(),
            'green_boxes': [(box.x(), box.y(), box.width(), box.height()) for box in self.original_view.green_boxes],
            'red_boxes': [(box.x(), box.y(), box.width(), box.height()) for box in self.original_view.red_boxes]
        }

        filename, _ = QFileDialog.getSaveFileName(self, "Save Settings", "", "VANTAGE Settings (*.vts)")
        if filename:
            with open(filename, 'w') as f:
                json.dump(settings, f)

    def load_settings(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "VANTAGE Settings (*.vts)")
        if filename:
            with open(filename, 'r') as f:
                settings = json.load(f)

            self.red_slider.setValue(settings['red_slider_value'])
            self.green_slider.setValue(settings['green_slider_value'])

            # Update the detectors with the new values
            self.red_detector.set_threshold(settings['red_slider_value'])
            self.green_detector.set_threshold(settings['green_slider_value'])

            self.original_view.green_boxes = [QRect(*box) for box in settings['green_boxes']]
            self.original_view.red_boxes = [QRect(*box) for box in settings['red_boxes']]

            self.original_view.update()

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
            point = QPointF(particle.x, particle.y)
            in_green = any(box.contains(point.toPoint()) for box in self.original_view.green_boxes)
            in_red = any(box.contains(point.toPoint()) for box in self.original_view.red_boxes)

            if in_green and particle.color == 'green':
                green_count += 1
            elif in_red and particle.color == 'red':
                red_count += 1
            elif (in_green and particle.color == 'red') or (in_red and particle.color == 'green'):
                error_count += 1

        self.update_region_display(green_count, red_count, error_count)

    def update_region_display(self, green_count, red_count, error_count):
        info_text = f"Green Count: {green_count}\nRed Count: {red_count}\nError Count: {error_count}"
        self.region_display.setText(info_text)

        def update_particle_info(self, red_particles, green_particles):
            red_count = len(red_particles)
            green_count = len(green_particles)

            red_avg_size = sum(p.size for p in red_particles) / red_count if red_count > 0 else 0
            green_avg_size = sum(p.size for p in green_particles) / green_count if green_count > 0 else 0

            info_text = f"Red Particles: {red_count} (Avg Size: {red_avg_size:.2f})\n"
            info_text += f"Green Particles: {green_count} (Avg Size: {green_avg_size:.2f})"

            self.particle_info_label.setText(info_text)

        def closeEvent(self, event):
            self.cap.release()

    def show_user_manual(self):
        dialog = UserManualDialog(self)
        dialog.exec_()

class FadingSplashScreen(QSplashScreen):
    def __init__(self, logo_path):
        pixmap = QPixmap(QSize(800, 400))

        painter = QPainter(pixmap)

        gradient = QLinearGradient(0, 0, 0, pixmap.height())
        gradient.setColorAt(0, QColor(230, 230, 250))
        gradient.setColorAt(1, QColor(201, 160, 220))

        painter.fillRect(pixmap.rect(), gradient)

        logo = QPixmap(logo_path)
        logo_rect = logo.rect()
        logo_rect.moveCenter(pixmap.rect().center())
        painter.drawPixmap(logo_rect, logo)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VANTAGE")
    app.setWindowIcon(QIcon("vantage.png"))

    splash = FadingSplashScreen("vantage_logo.png")
    splash.show()

    window = ColorDetectionApp()
    window.setWindowIcon(QIcon("vantage.png"))

    def showMain():
        splash.fadeOut()
        window.show()


    QTimer.singleShot(3500, showMain)

    sys.exit(app.exec_())


