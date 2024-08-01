import json
import os
import platform
import sys
import ctypes
from dataclasses import dataclass

import markdown
import cv2
import numpy as np

from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint, QRect, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QSettings
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QLinearGradient, QPalette, QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QGroupBox, QSplitter, QCheckBox, QRadioButton,
    QButtonGroup, QSplashScreen, QMessageBox, QDialog, QLineEdit,
    QPushButton, QTextBrowser, QFileDialog, QAction, QListWidget,
    QInputDialog, QDialogButtonBox, QSpinBox, QSizePolicy, QSpacerItem, QShortcut
)
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
                             QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QFileDialog)


if platform.system() == 'Darwin':  # macOS
    from Foundation import NSBundle
    bundle = NSBundle.mainBundle()
    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    info['CFBundleName'] = "VANTAGE"

VERSION = "3.0.1b"


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(400, 300)
        self.settings = QSettings("VANTAGE", "ColorDetectionApp")

        layout = QVBoxLayout(self)

        # Create a tab widget
        self.tab_widget = QTabWidget()

        self.setup_general_tab()
        self.setup_camera_tab()

        # Add the tab widget to the main layout
        layout.addWidget(self.tab_widget)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_preferences)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def setup_general_tab(self):
        general_tab = QWidget()
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

        self.tab_widget.addTab(general_tab, "General")

    def setup_camera_tab(self):
        camera_tab = QWidget()
        camera_layout = QFormLayout(camera_tab)

        self.default_camera_port = QSpinBox()
        self.default_camera_port.setRange(0, 10)
        self.default_camera_port.setValue(int(self.settings.value("default_camera_port", 0)))

        self.default_resolution = QLineEdit(self.settings.value("default_resolution", "1280x720"))

        self.min_particle_size = QSpinBox()
        self.min_particle_size.setRange(1, 1000)
        self.min_particle_size.setValue(int(self.settings.value("min_particle_size", 30)))

        self.max_particle_size = QSpinBox()
        self.max_particle_size.setRange(1, 10000)
        self.max_particle_size.setValue(int(self.settings.value("max_particle_size", 600)))

        camera_layout.addRow("Default Camera Port:", self.default_camera_port)
        camera_layout.addRow("Default Resolution:", self.default_resolution)
        camera_layout.addRow("Min Particle Size:", self.min_particle_size)
        camera_layout.addRow("Max Particle Size:", self.max_particle_size)

        self.tab_widget.addTab(camera_tab, "Camera")

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

        title_label = QLabel(" ")
        title_label.setStyleSheet("color: white; font-weight: bold; padding-left: 10px;")
        layout.addWidget(title_label)

        layout.addStretch()

        for button_data in [("minimize", self.parent.showMinimized), ("close", self.parent.close)]:
            button = QPushButton(self)
            button.setIcon(QIcon(f"assets/{button_data[0]}_icon.png"))
            button.setFixedSize(30, 30)
            button.clicked.connect(button_data[1])
            button.setStyleSheet(self.get_button_style(button_data[0]))
            layout.addWidget(button)

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
        self.setFixedSize(650, 450)

        self.recent_projects_manager = RecentProjectsManager()
        self.moving = False
        self.offset = QPoint()

        self.setup_ui()
        self.set_dark_theme()

    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(TitleBar(self))

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        main_layout.addWidget(content_widget)

        self.setup_logo(content_layout)
        content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setup_buttons(content_layout)
        content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setup_recent_projects(content_layout)

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
                camera_port = settings.get('camera_port', 0)
                resolution = settings.get('resolution', "960x360")

            self.color_detection_app = ColorDetectionApp(camera_port, resolution, project_name, settings, self)
            self.color_detection_app.current_project_path = project_path
            self.color_detection_app.show()
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the project: {str(e)}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.moving:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = False


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
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def _enhance_image(self, gray):
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(blurred)

    def _create_binary_image(self, enhanced):
        _, binary = cv2.threshold(enhanced, self.threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    def analyze_particles(self, contours, color):
        particles = []
        for contour in contours:
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
            self.regionChanged.emit()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            self._draw_particles(painter)
            self._draw_boxes(painter)
            self._draw_current_box(painter)

    def _draw_particles(self, painter):
        for particle in self.particles:
            x = int(particle.x * self.scale_factor + self.offset_x)
            y = int(particle.y * self.scale_factor + self.offset_y)
            radius = int(particle.radius * self.scale_factor)

            color = QColor(255, 0, 0) if particle.color == 'red' else QColor(0, 255, 0)
            painter.setPen(QPen(color, 2))
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x + radius + 5, y, f"{particle.size:.0f}")

    def _draw_boxes(self, painter):
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        for box in self.green_boxes:
            painter.drawRect(box)

        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for box in self.red_boxes:
            painter.drawRect(box)

    def _draw_current_box(self, painter):
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


class VideoProcessor:
    def __init__(self, camera_port, width, height):
        self.cap = cv2.VideoCapture(camera_port)
        self.set_resolution(width, height)
        self.red_detector = ColorDetector(0)
        self.green_detector = ColorDetector(0)
        self.red_analyzer = ParticleAnalyzer()
        self.green_analyzer = ParticleAnalyzer()


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
        red_frame = self.red_detector.detect(frame, 'red')
        green_frame = self.green_detector.detect(frame, 'green')

        red_contours = self.red_analyzer.detect_particles(red_frame)
        green_contours = self.green_analyzer.detect_particles(green_frame)

        red_particles = self.red_analyzer.analyze_particles(red_contours, 'red')
        green_particles = self.green_analyzer.analyze_particles(green_contours, 'green')

        return frame, red_particles, green_particles

    def release(self):
        self.cap.release()


class ColorDetectionApp(QMainWindow):
    def __init__(self, camera_port, resolution, project_name, settings=None, main_menu=None):
        super().__init__()
        self.project_name = project_name
        self.settings = settings or {}
        self.main_menu = main_menu
        self.setup_shortcuts()
        self.unsaved_changes = True  # Set to True initially
        self.current_project_path = None

        self.settings = QSettings("VANTAGE", "ColorDetectionApp")
        self.load_preferences()

        width, height = map(int, resolution.split('x'))
        self.video_processor = VideoProcessor(camera_port, width, height)
        self.setup_ui()
        self.setup_timer()
        self.create_menu()

        if settings:
            self.load_settings(settings)
        else:
            self.unsaved_changes = True

        self.update_title()

    def create_menu(self):
        menubar = self.menuBar()

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

        # Project menu
        project_menu = menubar.addMenu('Project')

        select_port_action = QAction('Select Camera Port', self)
        select_port_action.triggered.connect(self.select_camera_port)
        project_menu.addAction(select_port_action)

        close_project_action = QAction('Close Project', self)
        close_project_action.triggered.connect(self.closeEvent)
        project_menu.addAction(close_project_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        user_manual_action = QAction('User Manual', self)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)

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

    def select_camera_port(self):
        current_port = int(self.video_processor.cap.get(cv2.CAP_PROP_POS_FRAMES))
        port, ok = QInputDialog.getInt(self, "Camera Port", "Enter the USB camera port:",
                                       current_port, 0, 10)
        if ok:
            self.video_processor.release()
            self.video_processor = VideoProcessor(port)
            self.unsaved_changes = True
            self.update_title()

    def show_preferences(self):
        preferences_dialog = PreferencesDialog(self)
        if preferences_dialog.exec_() == QDialog.Accepted:
            self.load_preferences()

    def show_about(self):
        about_text = f"VANTAGE \n\nVersion: {VERSION}\n\nVision Assisted Nano-particle Tracking and Guided Extraction\n\n Developed by Alfa Ozaltin and Nil Ertok @ Stanford University"
        QMessageBox.about(self, "About VANTAGE", about_text)

    def show_user_manual(self):
        user_manual_dialog = UserManualDialog(self)
        user_manual_dialog.exec_()

    def apply_particle_analysis_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.red_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
            self.video_processor.green_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)

    def load_preferences(self):
        # Load general preferences
        self.default_project_location = self.settings.value("default_project_location", "")
        self.auto_save_interval = int(self.settings.value("auto_save_interval", 5))

        # Load camera preferences
        self.default_camera_port = int(self.settings.value("default_camera_port", 0))
        self.default_resolution = self.settings.value("default_resolution", "1280x720")

        # Set up auto-save timer
        self.setup_auto_save()

        # Load color detection preferences
        self.red_threshold = int(self.settings.value("red_threshold", 20))
        self.green_threshold = int(self.settings.value("green_threshold", 20))

        # Apply color detection settings
        self.apply_color_detection_settings()

        self.min_particle_size = int(self.settings.value("min_particle_size", 30))
        self.max_particle_size = int(self.settings.value("max_particle_size", 600))
        self.apply_particle_analysis_settings()

        # Load particle analysis preferences
        self.min_particle_size = int(self.settings.value("min_particle_size", 30))
        self.max_particle_size = int(self.settings.value("max_particle_size", 600))

        # Apply particle analysis settings
        self.apply_particle_analysis_settings()

    def apply_camera_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.set_camera_port(self.default_camera_port)
            width, height = map(int, self.camera_resolution.split('x'))
            self.video_processor.set_resolution(width, height)

    def setup_auto_save(self):
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(self.auto_save_interval * 60000)  # Convert minutes to milliseconds

    def apply_color_detection_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.red_detector.set_threshold(self.red_threshold)
            self.video_processor.green_detector.set_threshold(self.green_threshold)

        # Update UI elements if they exist
        if hasattr(self, 'red_slider'):
            self.red_slider.setValue(self.red_threshold)
        if hasattr(self, 'green_slider'):
            self.green_slider.setValue(self.green_threshold)

    def apply_particle_analysis_settings(self):
        if hasattr(self, 'video_processor'):
            self.video_processor.red_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)
            self.video_processor.green_analyzer.set_size_range(self.min_particle_size, self.max_particle_size)

    def auto_save(self):
        if self.current_project_path and self.unsaved_changes:
            self.save_project()
            QMessageBox.information(self, "Auto Save", "Project auto-saved successfully.")

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

    def setup_shortcuts(self):
        # Determine the operating system
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

        self.setup_color_control("Red", self.video_processor.red_detector, 4)
        self.setup_color_control("Green", self.video_processor.green_detector, 25)

        self.setup_particle_info()
        self.setup_roi_controls()
        self.setup_dark_mode_switch()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        frame, red_particles, green_particles = self.video_processor.process_frame()
        if frame is None:
            return

        self.original_view.update_frame(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), red_particles + green_particles)
        self.red_view.update_frame(cv2.cvtColor(self.video_processor.red_detector.detect(frame, 'red'), cv2.COLOR_BGR2RGB), red_particles)
        self.green_view.update_frame(cv2.cvtColor(self.video_processor.green_detector.detect(frame, 'green'), cv2.COLOR_BGR2RGB), green_particles)

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
        else:
            self.green_slider = slider

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

    def setup_dark_mode_switch(self):
        self.dark_mode_switch = QCheckBox("Dark Mode")
        self.dark_mode_switch.setChecked(True)
        self.dark_mode_switch.stateChanged.connect(self.toggle_theme)
        self.control_layout.addWidget(self.dark_mode_switch)

    def update_particle_info(self, red_particles, green_particles):
        '''red_count = len(red_particles)
        green_count = len(green_particles)

        red_avg_size = sum(p.size for p in red_particles) / red_count if red_count > 0 else 0
        green_avg_size = sum(p.size for p in green_particles) / green_count if green_count > 0 else 0

        info_text = f"Red Particles: {red_count} (Avg Size: {red_avg_size:.2f})\n"
        info_text += f"Green Particles: {green_count} (Avg Size: {green_avg_size:.2f})"

        self.particle_info_label.setText(info_text)'''
        pass

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

    def toggle_theme(self, state):
        is_dark = state == Qt.Checked
        self.set_theme(is_dark)

    def set_theme(self, is_dark):
        if is_dark:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #2B2B2B; color: #FFFFFF; }
                QLabel, QCheckBox, QRadioButton { color: #FFFFFF; }
                QGroupBox { border: 1px solid #555555; }
                QSlider::handle:horizontal { background-color: #4A4A4A; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #FFFFFF; color: #000000; }
                QLabel, QCheckBox, QRadioButton { color: #000000; }
                QGroupBox { border: 1px solid #CCCCCC; }
                QSlider::handle:horizontal { background-color: #DDDDDD; }
            """)

    def update_title(self):
        title = f"VANTAGE - {self.project_name}"
        if self.unsaved_changes:
            title += " (unsaved changes)"
        self.setWindowTitle(title)

    def save_project(self):
        if not self.current_project_path:
            self.save_project_as()
        else:
            self._save_project(self.current_project_path)

    def save_project_as(self):
        suggested_name = f"{self.project_name}.vtp" if not self.project_name.endswith('.vtp') else self.project_name
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", suggested_name, "VANTAGE Project (*.vtp)")
        if filename:
            self._save_project(os.path.abspath(filename))
        else:
            pass

    def _save_project(self, filename):
        if not filename.lower().endswith('.vtp'):
            filename += '.vtp'

        settings = {
            'camera_port': int(self.video_processor.cap.get(cv2.CAP_PROP_POS_FRAMES)),
            'resolution': f"{self.video_processor.width}x{self.video_processor.height}",
            'red_slider_value': self.red_slider.value(),
            'green_slider_value': self.green_slider.value(),
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
            QMessageBox.information(self, "Project Saved", f"Project saved successfully to {self.project_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")

    def load_settings(self, settings):
        self.red_slider.setValue(settings.get('red_slider_value', 0))
        self.green_slider.setValue(settings.get('green_slider_value', 0))

        self.video_processor.red_detector.set_threshold(settings.get('red_slider_value', 0))
        self.video_processor.green_detector.set_threshold(settings.get('green_slider_value', 0))

        self.original_view.green_boxes = [QRect(*box) for box in settings.get('green_boxes', [])]
        self.original_view.red_boxes = [QRect(*box) for box in settings.get('red_boxes', [])]

        resolution = settings.get('resolution', '1280x720')
        width, height = map(int, resolution.split('x'))
        self.video_processor.set_resolution(width, height)

        self.original_view.update()
        self.unsaved_changes = False
        self.update_title()

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(self, 'Save Project',
                                         "Do you want to save the project before closing?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

            if reply == QMessageBox.Yes:
                self.save_project()
                if self.unsaved_changes:  # If user cancelled the save dialog
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        if self.current_project_path and self.main_menu:
            self.main_menu.recent_projects_manager.add(self.current_project_path)
            self.main_menu.update_recent_projects()

        self.video_processor.release()
        if self.main_menu:
            self.main_menu.show()
        event.accept()


class FadingSplashScreen(QSplashScreen):
    def __init__(self, logo_path):
        pixmap = QPixmap(QSize(600, 300))  # Reduced size of the splash screen

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VANTAGE")

    app.setStyle("Fusion")

    app_icon = QIcon()
    if platform.system() == 'Windows':
        myappid = f'vxsoftware.vantage.beta.214b'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        icon_path = 'vantage.ico'
    else:
        icon_path = 'assets/v3/vtg_icon_comet.png'

    app_icon.addFile(icon_path, QSize(16, 16))
    app_icon.addFile(icon_path, QSize(24, 24))
    app_icon.addFile(icon_path, QSize(32, 32))
    app_icon.addFile(icon_path, QSize(48, 48))
    app_icon.addFile(icon_path, QSize(256, 256))
    app.setWindowIcon(app_icon)

    splash = FadingSplashScreen("assets/v3/vtg_logo_full_splash")
    splash.show()

    main_menu = MainMenu()
    main_menu.setWindowIcon(app_icon)

    def showMainMenu():
        splash.fadeOut()
        main_menu.show()

    QTimer.singleShot(2500, showMainMenu)

    sys.exit(app.exec_())
