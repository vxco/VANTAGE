import cv2
import numpy as np


def list_ports():
    '''Debug for listing available ports'''
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6:  # if there are more than 5 non working ports stop the testing.
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." % dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" % (dev_port, h, w))
                working_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." % (dev_port, h, w))
                available_ports.append(dev_port)
        dev_port += 1
    return available_ports, working_ports, non_working_ports


def cEd(frame):
    '''Uses Canny Edge Detection, from a blurred input to detect the outline of the cells.'''
    blurred = cv2.GaussianBlur(src=frame, ksize=(3, 5), sigmaX=0.8)
    edges = cv2.Canny(image=blurred, threshold1=100, threshold2=200)
    return blurred, edges


def main():
    aspectWidth = 73
    aspectHeight = 27
    aspectMultiplier = 16
    if aspectMultiplier % 2 == 1:
        print(
            f"Aspect multiplier was {aspectMultiplier}, should be an even number. Reverting to {aspectMultiplier - 1} ")
        aspectMultiplier -= 1

    imgWidth = aspectWidth * aspectMultiplier
    imgHeight = aspectHeight * aspectMultiplier

    cap = cv2.VideoCapture(0)
    cap.set(3, imgWidth)
    cap.set(4, imgHeight)
    #capturing the image, setting to a 73:27 Aspect ratio, (as the image input suggests by the capillery size)

    while True:
        ret, frame = cap.read()
        if not ret:
            exit("Err: CPT001 - refer to the manual for troubleshooting")

        '''Uses Dilation and Erosion algorithms to fill the detected cell edges, for better location detection of cells.'''
        blurred, edges = cEd(frame)
        _, thresh = cv2.threshold(edges, 100, 255, cv2.THRESH_BINARY)
        rect = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilation = cv2.dilate(thresh, rect, iterations=5)
        erosion = cv2.erode(dilation, rect, iterations=1)
        cv2.imshow("debug blur", blurred)
        cv2.imshow("debug edges", edges)
        cv2.imshow("debug fill", erosion)
        '''Color Detection for bounds Setup'''

        #Height Setup
        boundaryHeight = aspectMultiplier * 6
        upDownPadSecondary = aspectMultiplier * 3
        upDownPadInitial = upDownPadSecondary
        middlePadSecondary = imgHeight - 2*(boundaryHeight+upDownPadSecondary)

        middlePadInitial = imgHeight - 2*(boundaryHeight+upDownPadSecondary)

        #Width Setup
        initialBoundaryStartingPad = aspectMultiplier * 30
        secondaryBoundaryWidth = aspectMultiplier * 12
        tubePad = aspectMultiplier * 5
        initialBoundaryWidth = (aspectWidth - (initialBoundaryStartingPad / aspectMultiplier) - ((tubePad / aspectMultiplier) + (secondaryBoundaryWidth / aspectMultiplier))) * aspectMultiplier
        heightCheck = (2 * (boundaryHeight / aspectMultiplier) + 2 * (upDownPadSecondary / aspectMultiplier) + middlePadSecondary / aspectMultiplier)
        if middlePadSecondary<0:
            exit("Err: STP001 - refer to the manual for troubleshooting")
        if initialBoundaryWidth < secondaryBoundaryWidth:
            exit("Err: STP002 - refer to the manual for troubleshooting")

        #Secondary Region Down Coordinates
        r2dx1, r2dy1 = (initialBoundaryStartingPad + initialBoundaryWidth), imgHeight - (upDownPadSecondary + boundaryHeight)
        r2dx2, r2dy2 = (r2dx1 + secondaryBoundaryWidth), (imgHeight - upDownPadSecondary)
        #Secondary Region Up Coordinates
        r2ux1, r2ux2 = r2dx1, r2dx2
        r2uy1, r2uy2 = (r2dy1-(boundaryHeight+middlePadSecondary)),(r2dy2-(boundaryHeight+middlePadSecondary))
        lowerSecondaryRegion = erosion[int(r2dy1):int(r2dy2), int(r2dx1):int(r2dx2)]
        upperSecondaryRegion = erosion[int(r2uy1):int(r2uy2), int(r2ux1):int(r2ux2)]




        debugBox = cv2.rectangle(blurred, (int(r2dx1), int(r2dy1)), (int(r2dx2), int(r2dy2)), (255, 0, 0), 2) #secondary region down
        cv2.rectangle(debugBox, (int(r2ux1) , int(r2uy1)) , (int(r2ux2), int(r2uy2)), (255,0,0),2) #secondary region top





        cv2.imshow("debug boundbox", debugBox)




        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
