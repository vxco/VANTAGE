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

    def update_white_pixels(self, erosion):
        region = erosion[self.y1:self.y2, self.x1:self.x2]
        _, thresh = cv2.threshold(region, 254, 255, cv2.THRESH_BINARY)
        self.white_pixels = np.sum(thresh == 255)

    def calculate_cell_count(self, one_cell_pixel_count):
        self.cell_count = round(self.white_pixels / one_cell_pixel_count)

    def draw(self, image, color, thickness):
        cv2.rectangle(image, (self.x1, self.y1), (self.x2, self.y2), color, thickness)
        cv2.putText(image, f"nwp: {self.white_pixels}", (self.x1, self.y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                    2)
        cv2.putText(image, f"CC: {self.cell_count}", (self.x1, self.y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
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

        # Create regions
        self.regions.append(Region(0, self.img_height - (up_down_pad_initial + initial_boundary_height), beginning_box_width,
                                    self.img_height - up_down_pad_initial,
                                    "Beginning Box"))

        self.regions.append(Region(initial_boundary_starting_pad, self.img_height - (up_down_pad_initial + initial_boundary_height),
                                   initial_boundary_starting_pad + initial_boundary_width, self.img_height - up_down_pad_initial,
                                   "Lower Initial"))

        self.regions.append(Region(initial_boundary_starting_pad, up_down_pad_initial,
                                   initial_boundary_starting_pad + initial_boundary_width,
                                   up_down_pad_initial + initial_boundary_height,
                                   "Upper Initial"))

        self.regions.append(Region(initial_boundary_starting_pad + initial_boundary_width,
                                   self.img_height - (up_down_pad_secondary + secondary_boundary_height),
                                   initial_boundary_starting_pad + initial_boundary_width + secondary_boundary_width,
                                   self.img_height - up_down_pad_secondary,
                                   "Lower Secondary"))

        self.regions.append(Region(initial_boundary_starting_pad + initial_boundary_width, up_down_pad_secondary,
                                   initial_boundary_starting_pad + initial_boundary_width + secondary_boundary_width,
                                   up_down_pad_secondary + secondary_boundary_height,
                                   "Upper Secondary"))

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

    last_update_time = time.time()
    update_interval = 1 / 6
    cell_counts = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Err: CPT001 - refer to the manual for troubleshooting")
            break

        blurred, edges, erosion = detector.process_frame(frame)
        detector.draw_regions(blurred)

        fps = cap.get(cv2.CAP_PROP_FPS)
        cv2.putText(blurred, f"FPS: {fps}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        cell_counts.append(detector.get_cell_counts())

        current_time = time.time()
        elapsed_time = current_time - last_update_time

        if elapsed_time >= update_interval:
            averages = np.mean(cell_counts, axis=0)
            for region, avg in zip(detector.regions, averages):
                region.cell_count = round(avg)
            last_update_time = current_time
            cell_counts = []

        cv2.imshow("debug blur", blurred)
        cv2.imshow("debug edges", edges)
        cv2.imshow("debug fill", erosion)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()