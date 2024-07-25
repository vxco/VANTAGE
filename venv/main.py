import cv2
import numpy as np
import time
import argparse
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QGroupBox, QGridLayout, QSlider, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont




def list_ports():
    is_working = True
    dev_port = 0
    working_ports = []
    available_ports = []
    while is_working:
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            is_working = False

        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                working_ports.append(dev_port)
            else:
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports



class Region:
    def __init__(self, x1, y1, x2, y2, name):
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.x2 = int(x2)
        self.y2 = int(y2)
        self.name = name
        self.cell_count = 0
        self.white_pixels = 0
        self.red_green_ratio = 0
        self.cell_count_history = []
        self.last_update_time = time.time()
        self.update_interval = 1 / 3
        self.red_cells = 0
        self.green_cells = 0

    def update_white_pixels(self, erosion):
        region = erosion[self.y1:self.y2, self.x1:self.x2]
        _, thresh = cv2.threshold(region, 254, 255, cv2.THRESH_BINARY)
        self.white_pixels = np.sum(thresh == 255)

    def calculate_cell_count(self, one_cell_pixel_count):
        current_cell_count = round(self.white_pixels / one_cell_pixel_count)
        self.cell_count_history.append(current_cell_count)

        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.cell_count = round(np.mean(self.cell_count_history))
            self.cell_count_history = []
            self.last_update_time = current_time

    def calculate_red_green_ratio(self, frame):
        region = frame[self.y1:self.y2, self.x1:self.x2]

        # Convert to HSV color space
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])

        lower_green = np.array([40, 70, 50])
        upper_green = np.array([80, 255, 255])

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        mask_green = cv2.inRange(hsv, lower_green, upper_green)

        red_pixels = cv2.countNonZero(mask_red)
        green_pixels = cv2.countNonZero(mask_green)

        self.red_green_ratio = red_pixels / green_pixels if green_pixels != 0 else red_pixels

    def calculate_red_green_cells(self):
        if self.red_green_ratio > 0:
            self.red_cells = round(self.cell_count * (self.red_green_ratio / (1 + self.red_green_ratio)))
            self.green_cells = self.cell_count - self.red_cells
        elif self.red_green_ratio == 0:
            self.red_cells = 0
            self.green_cells = self.cell_count
        else:
            self.red_cells = self.cell_count
            self.green_cells = 0

    def draw(self, image, color, thickness):
        cv2.rectangle(image, (self.x1, self.y1), (self.x2, self.y2), color, thickness)
        cv2.putText(image, f"nwp: {self.white_pixels}", (self.x1, self.y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                    2)
        cv2.putText(image, f"CC: {self.cell_count}", (self.x1, self.y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 0, 0), 2)
        cv2.putText(image, f"R: {self.red_cells}", (self.x1, self.y1 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 0, 0), 2)
        cv2.putText(image, f"G: {self.green_cells}", (self.x1 + 50, self.y1 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 0, 0), 2)


class CellDetector:
    def __init__(self, aspect_width=73, aspect_height=27, aspect_multiplier=14):
        self.aspect_width = aspect_width
        self.aspect_height = aspect_height
        self.aspect_multiplier = aspect_multiplier
        self.img_width = aspect_width * aspect_multiplier
        self.img_height = aspect_height * aspect_multiplier
        self.one_cell_pixel_count = 125
        self.regions = []
        self.setup_regions()

    def setup_regions(self):
        initial_boundary_height = self.aspect_multiplier * 6
        secondary_boundary_height = self.aspect_multiplier * 7
        up_down_pad_secondary = self.aspect_multiplier * 3
        up_down_pad_initial = up_down_pad_secondary + (self.aspect_multiplier * 1)
        initial_boundary_starting_pad = self.aspect_multiplier * 30
        secondary_boundary_width = self.aspect_multiplier * 12
        beginning_box_width = initial_boundary_starting_pad + (self.aspect_multiplier * 1.5)
        tube_pad = self.aspect_multiplier * 5
        initial_boundary_width = (self.aspect_width - (initial_boundary_starting_pad / self.aspect_multiplier) - (
                (tube_pad / self.aspect_multiplier) + (
                secondary_boundary_width / self.aspect_multiplier))) * self.aspect_multiplier

        # region constructor: Region(x1, y1, x2, y2, name)
        self.regions.append(
            Region(x1=0,
                   y1=up_down_pad_initial + initial_boundary_height,
                   x2=beginning_box_width,
                   y2=self.img_height - (up_down_pad_initial + initial_boundary_height),
                   name="Beginning Box"))

        self.regions.append(
            Region(x1=initial_boundary_starting_pad,
                   y1=self.img_height - (up_down_pad_initial + initial_boundary_height),
                   x2=initial_boundary_starting_pad + initial_boundary_width,
                   y2=self.img_height - up_down_pad_initial,
                   name="Lower Initial"))

        self.regions.append(
            Region(x1=initial_boundary_starting_pad,
                   y1=up_down_pad_initial,
                   x2=initial_boundary_starting_pad + initial_boundary_width,
                   y2=up_down_pad_initial + initial_boundary_height,
                   name="Upper Initial"))

        self.regions.append(
            Region(x1=initial_boundary_starting_pad + initial_boundary_width,
                   y1=self.img_height - (up_down_pad_secondary + secondary_boundary_height),
                   x2=initial_boundary_starting_pad + initial_boundary_width + secondary_boundary_width,
                   y2=self.img_height - up_down_pad_secondary,
                   name="Lower Secondary"))

        self.regions.append(
            Region(x1=initial_boundary_starting_pad + initial_boundary_width,
                   y1=up_down_pad_secondary,
                   x2=initial_boundary_starting_pad + initial_boundary_width + secondary_boundary_width,
                   y2=up_down_pad_secondary + secondary_boundary_height,
                   name="Upper Secondary"))

    def process_frame(self, frame):
        blurred, edges = self.canny_edge_detection(frame)
        erosion = self.fill_edges(edges)

        for region in self.regions:
            region.update_white_pixels(erosion)
            region.calculate_cell_count(self.one_cell_pixel_count)
            region.calculate_red_green_ratio(frame)
            region.calculate_red_green_cells()

        return blurred, edges, erosion

    def canny_edge_detection(self, frame):
        blurred = cv2.GaussianBlur(src=frame, ksize=(3, 5), sigmaX=0.8)
        edges = cv2.Canny(image=blurred, threshold1=100, threshold2=200)
        return blurred, edges

    def fill_edges(self, edges):
        _, thresh = cv2.threshold(edges, 100, 255, cv2.THRESH_BINARY)
        rect = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilation = cv2.dilate(thresh, rect, iterations=5)
        erosion = cv2.erode(dilation, rect, iterations=1)
        return erosion

    def draw_regions(self, image):
        for region in self.regions:
            region.draw(image, (255, 0, 0), 2)
            #help

    def get_cell_counts(self):
        return [region.cell_count for region in self.regions]


class MainWindow(QMainWindow):
    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.initUI()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, detector.img_width)
        self.cap.set(4, detector.img_height)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms

    def initUI(self):
        self.setWindowTitle('VANTAGE - Vision Assisted Nanoparticle Tracking and Guided Extraction')
        self.setFixedSize(1200, 800)
        self.setStyleSheet("background-color: #F89880;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()

        # Left panel for video feed
        left_panel = QVBoxLayout()
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(800, 600)
        self.image_label.setStyleSheet("border: 2px solid #3498db;")
        left_panel.addWidget(self.image_label)

        # Right panel for controls and info
        right_panel = QVBoxLayout()

        # Debug controls
        debug_group = QGroupBox("Debug Controls")
        debug_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        debug_layout = QVBoxLayout()
        self.debug_button = QPushButton('Toggle Debug Mode')
        self.debug_button.clicked.connect(self.toggle_debug)
        self.debug_button.setStyleSheet("background-color: #3498db; color: white;")
        debug_layout.addWidget(self.debug_button)

        # Add dropdown for selecting debug screen
        self.debug_screen_selector = QComboBox()
        self.debug_screen_selector.addItems(["Original", "Edges", "Erosion"])
        debug_layout.addWidget(self.debug_screen_selector)

        debug_group.setLayout(debug_layout)
        right_panel.addWidget(debug_group)

        # Cell count display
        count_group = QGroupBox("Cell Counts")
        count_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        count_layout = QGridLayout()
        self.count_labels = []
        for i, region in enumerate(self.detector.regions):
            label = QLabel(f"{region.name}: 0")
            label.setStyleSheet("font-size: 14px;")
            count_layout.addWidget(label, i // 2, i % 2)
            self.count_labels.append(label)
        count_group.setLayout(count_layout)
        right_panel.addWidget(count_group)

        # Threshold control
        threshold_group = QGroupBox("Threshold Control")
        threshold_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        threshold_layout = QVBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(100)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_group.setLayout(threshold_layout)
        right_panel.addWidget(threshold_group)

        # Quit button
        self.quit_button = QPushButton('Quit')
        self.quit_button.clicked.connect(self.close)
        self.quit_button.setStyleSheet("background-color: #e74c3c; color: white;")
        right_panel.addWidget(self.quit_button)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 1)
        central_widget.setLayout(main_layout)

        self.debug_mode = False

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Err: CPT001 - refer to the manual for troubleshooting")
            return

        blurred, edges, erosion = self.detector.process_frame(frame)

        if self.debug_mode:
            selected_screen = self.debug_screen_selector.currentText()
            if selected_screen == "Original":
                debug_frame = frame
            elif selected_screen == "Edges":
                debug_frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            elif selected_screen == "Erosion":
                debug_frame = cv2.cvtColor(erosion, cv2.COLOR_GRAY2BGR)
            self.detector.draw_regions(debug_frame)
            self.display_image(debug_frame)
        else:
            self.display_image(frame)

        # Update cell count labels
        for i, region in enumerate(self.detector.regions):
            self.count_labels[i].setText(f"{region.name}: {region.cell_count}")

    def display_image(self, img):
        qformat = QImage.Format_RGB888
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        pixmap = QPixmap.fromImage(img)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def toggle_debug(self):
        self.debug_mode = not self.debug_mode
        self.debug_button.setText('Disable Debug Mode' if self.debug_mode else 'Enable Debug Mode')

    def update_threshold(self):
        threshold = self.threshold_slider.value()
        # self.detector.update_threshold(threshold)  # Implement this method in your CellDetector class

    def closeEvent(self, event):
        self.cap.release()


def main():
    detector = CellDetector()
    app = QApplication(sys.argv)
    main_window = MainWindow(detector)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", help="list all the available cameras", action="store_true")
    args = parser.parse_args()

    if args.list:
        available_ports, working_ports = list_ports()
        print("Available ports: ", available_ports)
        print("Working ports: ", working_ports)
    else:
        main()
