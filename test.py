import cv2


#connecting to webcamera 
cap=cv2.VideoCapture(0) 

#get a frame value from the capture 
#put in loop to continuouly get frames 
while True: 
    #frame is img itself, ret isbool val (check if read correct) 
    ret, frame = cap.read()
    if not ret:
        print("cameras not connecting")
        break 

    #shawdow detection
    #convert to gray scale (0 black, 255 white) 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #isolate gray values (change thresh as needed)
    thresholdVal =100
    maxVal = 255 
    shadow = cv2.threshold(gray, thresholdVal, maxVal, cv2.THRESH_BINARY)

    #show both frames
    cv2.imshow("frame", frame)
    cv2.imshow("shadow", shadow[1])


    #when q is pressed then cam stopped
    if cv2.waitKey(1) == ord('q'):
        break

#release cam and close all windows 
cap.release() 
cv2.destroyAllWindows() 
