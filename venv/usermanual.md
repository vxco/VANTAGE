
# VANTAGE User Manual

## Table of Contents

1. [Introduction](#introduction)

2. [System Requirements](#system-requirements)

3. [Installation](#installation)

4. [Software Architecture](#software-architecture)

5. [Usage Guide](#usage-guide)

6. [Advanced Configuration](#advanced-configuration)

7. [Troubleshooting](#troubleshooting)

8. [Appendix](#appendix)

## 1. Introduction

Welcome to the Vision-based Automation for Nanoparticle Tracking and Guided Extraction (VANTAGE) User Manual. This comprehensive guide is designed to ensure the proper operation and optimal use of the VANTAGE software.

VANTAGE is an advanced automation solution developed for the Durmus Lab at Stanford University. It streamlines the process of cell sorting within the Magnetic Levitation (MagLev) system, enhancing efficiency and accuracy in research applications.

### 1.1 Important Notice

**CAUTION**: VANTAGE is intended for research purposes only. This software is not approved for use in medical environments or in any situation where human health may be directly affected. Always adhere to proper laboratory safety protocols and guidelines when using VANTAGE.

### 1.2 About This Manual

This user manual provides:

- Detailed instructions for software installation and setup

- Step-by-step guidance on operating VANTAGE

- A comprehensive troubleshooting guide for any errors

For the latest updates and additional resources, please visit our official website: [simitbey.github.io/VANTAGE](https://simitbey.github.io/VANTAGE)

## 2. System Requirements

- Operating System: Windows 10 (64-bit), macOS 10.14+, or Ubuntu 18.04+

- Processor: Intel Core i5 or equivalent (i7 recommended for optimal performance)

- RAM: 8 GB minimum (16 GB recommended)

- Storage: 1 GB of available space

- Camera: USB 3.0 compatible camera with at least 720p resolution

- Python: Version 3.9 or higher

- OpenCV: Version 4.5 or higher

- NumPy: Latest stable version

## 3. Installation

1. Download the VANTAGE software package from the official website.

2. Extract the downloaded package to your desired installation directory.

3. Open a terminal or command prompt and navigate to the installation directory.

4. Run the following command to install required dependencies:

```

pip install -r requirements.txt

```

5. Verify the installation by running:

```

python vantage.py --version

```

## 4. Software Architecture

VANTAGE is built on a modular architecture, consisting of two main classes:

### 4.1 Region Class

The `Region` class represents a specific area of interest in the image.

Key attributes and methods:

- `x1, y1, x2, y2`: Coordinates defining the region's boundaries

- `name`: Identifier for the region

- `cell_count`: Number of cells detected in the region

- `white_pixels`: Count of white pixels in the region after processing

- `update_white_pixels(erosion)`: Updates the white pixel count

- `calculate_cell_count(one_cell_pixel_count)`: Estimates the number of cells

- `draw(image, color, thickness)`: Draws the region on the image

### 4.2 CellDetector Class

The `CellDetector` class is the core of the VANTAGE system, handling image processing and cell detection.

Key attributes and methods:

- `aspect_width, aspect_height, aspect_multiplier`: Image sizing parameters

- `img_width, img_height`: Calculated image dimensions

- `one_cell_pixel_count`: Estimated pixel count for a single cell

- `regions`: List of Region objects

- `setup_regions()`: Initializes the regions of interest

- `process_frame(frame)`: Processes a single video frame

- `canny_edge_detection(frame)`: Applies Canny edge detection

- `fill_edges(edges)`: Fills and erodes detected edges

- `draw_regions(image)`: Draws all regions on the image

- `get_cell_counts()`: Returns cell counts for all regions

## 5. Usage Guide

### 5.1 Starting VANTAGE

To start VANTAGE, open a terminal in the installation directory and run:

```

python vantage.py

```

### 5.2 Main Interface

Upon launching, VANTAGE will display the following windows:

1. Main Display: Shows the processed image with regions of interest and cell counts

2. Debug Blur: Displays the blurred image

3. Debug Edges: Shows the result of edge detection

4. Debug Fill: Displays the filled and eroded edges


### 5.5 Recommended Camera Setup

For optimal performance with VANTAGE, we recommend the following camera setup:

#### 5.5.1 Aspect Ratio

We strongly recommend using a 73:27 aspect ratio for your camera feed. This specific ratio has been optimized for the VANTAGE software and the MagLev system, ensuring the best detection and analysis results.

To set up this aspect ratio:

1. Configure your camera or capture software to output a resolution that matches or can be cropped to a 73:27 ratio.

2. If your camera doesn't support this ratio natively, you can use software cropping to achieve it.

#### 5.5.2 AmScope and OBS Setup - Aspect Ratio and Resolution Settings

For users with AmScope microscopes, we recommend using Open Broadcaster Software (OBS) to capture and stream the microscope feed. This setup provides greater flexibility and control over the video input.

To set up OBS with your AmScope:

1. Download and install OBS from the official website (https://obsproject.com/).

2. Launch OBS and create a new scene.

3. Add a new source by clicking the '+' button in the Sources box and select 'Window Capture.

4. Choose your AmScope window from the device dropdown.

5. In the OBS Settings menu, go under video to set the resolution to a 73:27 aspect ratio, i.e: 2920x1080

6. If needed, use the 'Crop/Pad' filter to fine-tune the aspect ratio.

7. Start the Virtual Camera in OBS before running VANTAGE.

#### 5.5.3 Configuring VANTAGE for OBS Output

To use the OBS output with VANTAGE:

1. Ensure OBS is running before starting VANTAGE.

2. In the VANTAGE configuration file, set the video source to the OBS Virtual Camera's port. i.e:

```python

cap = cv2.VideoCapture(0)

```
> To find the port the camera is setup at, run the camera listing function by running the software with the -l flag.

3. Run VANTAGE as usual. It will now process the OBS recording instead of a live camera feed.

By using this setup, you ensure that VANTAGE receives a consistent, high-quality video stream in the optimal aspect ratio, which can significantly improve the accuracy of cell detection and counting.

### 5.12 Interpreting the Display

- Each region of interest is outlined in blue

- "nwp" indicates the number of white pixels in the region

- "CC" shows the estimated cell count for the region

- FPS (Frames Per Second) is displayed in the top-left corner

### 5.13 Exiting the Program

To exit VANTAGE, press the 'q' key while the main display window is active.

## 6. Advanced Configuration

### 6.1 Adjusting Region Parameters

To modify region parameters, edit the `setup_regions()` method in the `CellDetector` class:

```python

def setup_regions(self):

# Modify these values to adjust region sizes and positions

initial_boundary_height = self.aspect_multiplier * 6

secondary_boundary_height = self.aspect_multiplier * 7

# ... (other parameters)

# Add or modify regions as needed

self.regions.append(Region(x1, y1, x2, y2, "Custom Region"))

```

### 6.2 Calibrating Cell Detection

To adjust the cell detection sensitivity, modify the `one_cell_pixel_count` attribute in the `CellDetector` class:

```python

class CellDetector:

def __init__(self, aspect_width=73, aspect_height=27, aspect_multiplier=14):

# ...

self.one_cell_pixel_count = 125 # Adjust this value for calibration

# ...

```

## 7. Troubleshooting

### 7.1 Common Error Codes

| Error Code | Description | Problem Identification | Solving Steps |
|------------|-------------|------------------------|---------------|
| CPT001 | Error in image capture | Unable to capture frames from the camera | 1. Check camera connection<br>2. Verify camera selection<br>3. Update camera drivers<br>4. Restart the software |
| STP001 | Error in initialization phase | Software fails to initialize properly | 1. Verify required libraries<br>2. Check configuration files<br>3. Ensure sufficient system resources<br>4. Restart the software |
| LVC001 | Error in cleanup or output | Issues occur when closing or during data output | 1. Check available disk space<br>2. Verify file write permissions<br>3. Check LabVIEW connection settings<br>4. Restart the software |

For detailed solving steps, refer to the Error Codes section in the full manual.

## 8. Appendix

### 8.1 Glossary of Terms

- **MagLev**: Magnetic Levitation, the principle used for cell sorting in this system

- **ROI**: Region of Interest, a specific area in the image for analysis

- **FPS**: Frames Per Second, the rate at which video frames are processed

### 8.2 Contact Information

For additional support or inquiries, please contact:

- Email: support@vantage.io

- Phone: +90 (538) 796 16 79

- Website: [simitbey.github.io/VANTAGE](https://simitbey.github.io/VANTAGE)

---