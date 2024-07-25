import cv2
import numpy as np
import time


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
        self.update_interval = 1 / 6

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

    def calculate_red_green_ratio(self, blurred):
        region = blurred[self.y1:self.y2, self.x1:self.x2]
        _, thresh = cv2.threshold(region, 200, 255, cv2.THRESH_BINARY)
        red_pixels = np.sum(thresh == 255)
        _, thresh = cv2.threshold(region, 100, 200, cv2.THRESH_BINARY)
        green_pixels = np.sum(thresh == 255)
        self.red_green_ratio = red_pixels / green_pixels if green_pixels > 0 else 0

    def draw(self, image, color, thickness):
        cv2.rectangle(image, (self.x1, self.y1), (self.x2, self.y2), color, thickness)
        cv2.putText(image, f"nwp: {self.white_pixels}", (self.x1, self.y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                    2)
        cv2.putText(image, f"CC: {self.cell_count}", (self.x1, self.y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 0, 0), 2)
        cv2.putText(image, f"RGR: {self.red_green_ratio:.2f}", (self.x1, self.y1 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
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

    def get_cell_counts(self):
        return [region.cell_count for region in self.regions]


def main():
    detector = CellDetector()
    cap = cv2.VideoCapture(0)
    cap.set(3, detector.img_width)
    cap.set(4, detector.img_height)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Err: CPT001 - refer to the manual for troubleshooting")
            break

        blurred, edges, erosion = detector.process_frame(frame)
        detector.draw_regions(blurred)


        cv2.imshow("debug blur", blurred)
        cv2.imshow("debug edges", edges)
        cv2.imshow("debug fill", erosion)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
