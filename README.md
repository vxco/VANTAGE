# VANTAGE User Manual
## Introduction 
Welcome to the Vision-based Automation for Nanoparticle Tracking and Guided Extraction (VANTAGE) User Manual. This comprehensive guide is designed to ensure the proper operation and optimal use of the VANTAGE software. 

VANTAGE is an advanced automation solution developed for the Durmus Lab at Stanford University. It streamlines the process of cell sorting within the Magnetic Levitation (MagLev) system, enhancing efficiency and accuracy in research applications. 
## Important Notice 
**CAUTION**: VANTAGE is intended for research purposes only. This software is not approved for use in medical environments or in any situation where human health may be directly affected. Always adhere to proper laboratory safety protocols and guidelines when using VANTAGE. 
## About This Manual 

This user manual provides: 
- Detailed instructions for software installation and setup 
- Step-by-step guidance on operating VANTAGE 
- A correct troubleshooting guide for any errors 
---
# Next Steps
1. [Setup](#setup)
2. [Error Codes](#error-codes)


## Setup

### Step By Step Setup Procedure
This setup procedure will ensure the setting of all variables adjusted correctly to your needs.


## Error Codes
There are three categories of errors, with their respected prefix.

|  Prefix  | Description                                            |
|:--------:|--------------------------------------------------------|
|   STP    | Problems in the initialization phase.                  |
|   CPT    | Problems in the image input                            |
|   EDL    | Problems in edge detection and cell location detection |
|   MLM    | Problems in the machine learning model                 |
|   LVC    | Problems in output or Labview Link                     |

Refer to the table below for detailed information on each error code, including problem identification and solving steps:

| Error Code | Description | Problem Identification | Solving Steps |
|:-----------|-------------|------------------------|---------------|
| CPT001     | Error in image capture | The software is unable to capture frames from the camera | 1. Check camera connection:<br>   - Ensure the camera is properly plugged in to the computer<br>   - Try a different USB port if applicable<br>2. Verify camera selection:<br>   - Open the VANTAGE configuration file<br>   - Confirm the correct camera index is specified<br>3. Update camera drivers:<br>   - Visit the camera manufacturer's website<br>   - Download and install the latest drivers<br>4. Restart the software:<br>   - Close VANTAGE completely<br>   - Reopen and try the operation again |
| STP001     | Error in initialization phase | The software fails to initialize properly | 1. Verify required libraries:<br>   - Check the VANTAGE documentation for required libraries<br>   - Ensure all libraries are installed and up-to-date<br>2. Check configuration files:<br>   - Locate the VANTAGE configuration files<br>   - Verify all files are present and correctly formatted<br>3. Ensure sufficient system resources:<br>   - Close unnecessary applications<br>   - Check available RAM and CPU usage<br>4. Restart the software:<br>   - Close VANTAGE completely<br>   - Reopen and try the operation again |
| LVC001     | Error in cleanup or output | Issues occur when closing or during data output | 1. Check available disk space:<br>   - Ensure there's sufficient free space on the output drive<br>   - Clear unnecessary files if needed<br>2. Verify file write permissions:<br>   - Check that VANTAGE has permission to write to the output directory<br>   - Adjust folder permissions if necessary<br>3. Check LabVIEW connection settings:<br>   - Review LabVIEW connection configuration<br>   - Ensure LabVIEW is running and accessible<br>4. Restart the software:<br>   - Close VANTAGE completely<br>   - Reopen and try the operation again |

If you encounter an error not listed here or if the solving steps do not resolve the issue, please contact the VANTAGE support team for further assistance.

Remember to document any errors you encounter and the steps you took to resolve them. This information can be valuable for future troubleshooting and software improvement.

