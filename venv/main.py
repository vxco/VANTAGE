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


#OBS: 2920 1080
def main():
    '''main code '''
    oneCellPixelCount = 120
    aspectWidth= 73
    aspectHeight = 27
    aspectMultiplier = 14 #use 2320/73 for mac, 14 for best results
    if aspectMultiplier % 2 != 0:
        print(f"Aspect multiplier was {aspectMultiplier}, should be an even number. Reverting to {aspectMultiplier - 1} ")
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

        #Height Setup ---------------------
        initialBoundaryHeight = aspectMultiplier * 6
        secondaryBoundaryHeight = aspectMultiplier * 7
        topBottomFullBoundaryHeight = initialBoundaryHeight


        upDownPadSecondary = aspectMultiplier * 3
        upDownPadInitial = upDownPadSecondary  + (aspectMultiplier * 1)
        upDownPadTopBottomFullBoundary = (aspectMultiplier * 1)

        middlePadSecondary = imgHeight - 2*(secondaryBoundaryHeight+upDownPadSecondary)
        middlePadInitial = imgHeight - 2*(initialBoundaryHeight+upDownPadInitial)




        #Width Setup ---------------------
        initialBoundaryStartingPad = aspectMultiplier * 30

        secondaryBoundaryWidth = aspectMultiplier * 12
        beginningBoxWidth = initialBoundaryStartingPad + (aspectMultiplier * 1.5)

        tubePad = aspectMultiplier * 5
        initialBoundaryWidth = (aspectWidth - (initialBoundaryStartingPad / aspectMultiplier) - ((tubePad / aspectMultiplier) + (secondaryBoundaryWidth / aspectMultiplier))) * aspectMultiplier
        heightCheck = (2 * (secondaryBoundaryHeight / aspectMultiplier) + 2 * (upDownPadSecondary / aspectMultiplier) + middlePadSecondary / aspectMultiplier)
        if middlePadSecondary<0:
            exit("Err: STP001 - refer to the manual for troubleshooting")
        if initialBoundaryWidth < secondaryBoundaryWidth:
            exit("Err: STP002 - refer to the manual for troubleshooting")

        #Secondary Region Down Coordinates
        r2dx1, r2dy1 = (initialBoundaryStartingPad + initialBoundaryWidth), imgHeight - (upDownPadSecondary + secondaryBoundaryHeight)
        r2dx2, r2dy2 = (r2dx1 + secondaryBoundaryWidth), (imgHeight - upDownPadSecondary)
        #Secondary Region Up Coordinates
        r2ux1, r2ux2 = r2dx1, r2dx2
        r2uy1, r2uy2 = (r2dy1-(secondaryBoundaryHeight+middlePadSecondary)),(r2dy2-(secondaryBoundaryHeight+middlePadSecondary))
        lowerSecondaryRegion = erosion[int(r2dy1):int(r2dy2), int(r2dx1):int(r2dx2)]
        upperSecondaryRegion = erosion[int(r2uy1):int(r2uy2), int(r2ux1):int(r2ux2)]

        #Initial Region Down Coordinates
        r1dx1, r1dy1 = initialBoundaryStartingPad, imgHeight - (upDownPadInitial + initialBoundaryHeight)
        r1dx2, r1dy2 = r1dx1 + initialBoundaryWidth, imgHeight - upDownPadInitial
        #Initial Region Up Coordinates
        r1ux1, r1ux2 = r1dx1, r1dx2
        r1uy1, r1uy2 = r1dy1-(initialBoundaryHeight+middlePadInitial), r1dy2-(initialBoundaryHeight+middlePadInitial)

        lowerInitialRegion = erosion[int(r1dy1):int(r1dy2), int(r1dx1):int(r1dx2)]
        upperInitialRegion = erosion[int(r1uy1):int(r1uy2), int(r1ux1):int(r1ux2)]

        #beginningBox Coordinates
        bx1, by1 = 0, r1uy2
        bx2, by2 = beginningBoxWidth, r1dy1
        beginningBoxRegion = erosion[int(by1):int(by2), int(bx1):int(bx2)]

        '''#topBottomFullBoundary Up Coordinates
        tbux1, tbuy1 = 0, upDownPadTopBottomFullBoundary
        tbux2, tbuy2 = imgWidth, upDownPadTopBottomFullBoundary + topBottomFullBoundaryHeight
        topBottomFullBoundaryUp = erosion[int(tbuy1):int(tbuy2), int(tbux1):int(tbux2)]

        #topBottomFullBoundary Down Coordinates (same as up, but inverted to the bottom)
        tbdx1, tbdy1 = tbux1, imgHeight - upDownPadTopBottomFullBoundary
        tbdx2, tbdy2 = tbux2, imgHeight - upDownPadTopBottomFullBoundary - topBottomFullBoundaryHeight'''

        debugBoxThickness = 2

        debugBox = cv2.rectangle(blurred, (int(r2dx1), int(r2dy1)), (int(r2dx2), int(r2dy2)), (255, 0, 0), int(debugBoxThickness)) #secondary region down
        cv2.rectangle(debugBox, (int(r2ux1) , int(r2uy1)) , (int(r2ux2), int(r2uy2)), (255,0,0),int(debugBoxThickness)) #secondary region top
        cv2.rectangle(debugBox, (int(r1dx1), int(r1dy1)), (int(r1dx2), int(r1dy2),), (255, 255, 0), int(debugBoxThickness))
        cv2.rectangle(debugBox, (int(r1ux1), int(r1uy1)), (int(r1ux2), int(r1uy2),), (255, 255, 0), int(debugBoxThickness))
        cv2.rectangle(debugBox, (int(bx1), int(by1)), (int(bx2), int(by2),), (255, 0, 255), int(debugBoxThickness))

        #calculate the number of debugBox pixels in each box set (secondary, initial and beginning) using the coordinates and the debugBox thickness
        secondaryBoxPixelCount = ((r2dx2 - r2dx1) * debugBoxThickness + (r2dy2 - r2dy1) * debugBoxThickness) * 1.4
        initialBoxPixelCount = ((r1dx2 - r1dx1) * debugBoxThickness + (r1dy2 - r1dy1) * debugBoxThickness) *1.4
        beginningBoxPixelCount = ((bx2 - bx1) * debugBoxThickness + (by2 - by1) * debugBoxThickness) *1.4

        '''cv2.rectangle(debugBox, (int(tbux1), int(tbuy1)), (int(tbux2), int(tbuy2),), (0, 0, 255), 2)
        cv2.rectangle(debugBox, (int(tbdx1), int(tbdy1)), (int(tbdx2), int(tbdy2),), (0, 0, 255), 2)'''




        cv2.imshow("debug boundbox", debugBox)

        whiteThresh, whiteMaxVal = 254, 255

        _, thresh = cv2.threshold(beginningBoxRegion, 254, 255, cv2.THRESH_BINARY)
        nw_beginningBox = np.sum(thresh == 255)
        _, thresh = cv2.threshold(lowerInitialRegion, 254, 255, cv2.THRESH_BINARY)
        nw_lowerInitialRegion = np.sum(thresh == 255)
        _, thresh = cv2.threshold(upperInitialRegion, 254, 255, cv2.THRESH_BINARY)
        nw_upperInitialRegion = np.sum(thresh == 255)
        _, thresh = cv2.threshold(lowerSecondaryRegion, 254, 255, cv2.THRESH_BINARY)
        nw_lowerSecondaryRegion = np.sum(thresh == 255)
        _, thresh = cv2.threshold(upperSecondaryRegion, 254, 255, cv2.THRESH_BINARY)
        nw_upperSecondaryRegion = np.sum(thresh == 255)

        '''
        nw_beginningBox -= beginningBoxPixelCount
        nw_lowerInitialRegion -= initialBoxPixelCount
        nw_upperInitialRegion -= initialBoxPixelCount
        nw_lowerSecondaryRegion -= secondaryBoxPixelCount
        nw_upperSecondaryRegion -= secondaryBoxPixelCount
        '''


        #display nw in the image
        cv2.putText(blurred, f"nw_beginningBox: {nw_beginningBox}", (int(bx1), int(by1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"nw_lowerInitialRegion: {nw_lowerInitialRegion}", (int(r1dx1), int(r1dy1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"nw_upperInitialRegion: {nw_upperInitialRegion}", (int(r1ux1), int(r1uy1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"nw_lowerSecondaryRegion: {nw_lowerSecondaryRegion}", (int(r2dx1), int(r2dy1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"nw_upperSecondaryRegion: {nw_upperSecondaryRegion}", (int(r2ux1), int(r2uy1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.imshow("debug boundbox", debugBox)

        #add cellcount on all boxes by taking the number of pixels and dividing it to the oneCellPixelCount
        cc_beginningBox = (nw_beginningBox / oneCellPixelCount)
        cc_lowerInitialRegion = (nw_lowerInitialRegion / oneCellPixelCount)
        cc_upperInitialRegion = (nw_upperInitialRegion / oneCellPixelCount)
        cc_lowerSecondaryRegion = (nw_lowerSecondaryRegion / oneCellPixelCount)
        cc_upperSecondaryRegion = (nw_upperSecondaryRegion / oneCellPixelCount)

        #round the cellcount to the nearest whole number
        cc_beginningBox = round(cc_beginningBox)
        cc_lowerInitialRegion = round(cc_lowerInitialRegion)
        cc_upperInitialRegion = round(cc_upperInitialRegion)
        cc_lowerSecondaryRegion = round(cc_lowerSecondaryRegion)
        cc_upperSecondaryRegion = round(cc_upperSecondaryRegion)


        #display cc in the image
        cv2.putText(blurred, f"cc_beginningBox: {cc_beginningBox}", (int(bx1), int(by1) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"cc_lowerInitialRegion: {cc_lowerInitialRegion}", (int(r1dx1), int(r1dy1) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"cc_upperInitialRegion: {cc_upperInitialRegion}", (int(r1ux1), int(r1uy1) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"cc_lowerSecondaryRegion: {cc_lowerSecondaryRegion}", (int(r2dx1), int(r2dy1) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(blurred, f"cc_upperSecondaryRegion: {cc_upperSecondaryRegion}", (int(r2ux1), int(r2uy1) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.imshow("debug boundbox", debugBox)










        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
