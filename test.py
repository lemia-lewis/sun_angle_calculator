import time
import cv2
import numpy as np
import math
import tkinter as tk
from PIL import Image, ImageTk


#shadow sensitivity
shadowThreshold = 80

#***********************************
#Example code to show video feed in tkinter window
#***********************************
# def show_frame():
#     ret, frame = cap.read()
#     if ret:
#         # Convert BGR to RGB and update label
#         cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2_image))
#         label.imgtk = imgtk  # Crucial: Prevent garbage collection
#         label.configure(image=imgtk)
#     label.after(15, show_frame) # Refresh rate


#***********************************
#Object and shadow dimension functions
#***********************************

def get_object_dimensions_grid(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # --- Object mask ---
    _, mask = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    obj = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(obj)

    # --- Grid spacing ---
    edges = cv2.Canny(gray, 50, 150)

    vertical_profile = np.sum(edges, axis=0)
    horizontal_profile = np.sum(edges, axis=1)

    def get_spacing(profile):
        peaks = np.where(profile > np.mean(profile))[0]
        if len(peaks) < 2:
            return None
        return int(np.median(np.diff(peaks)))

    grid_x = get_spacing(vertical_profile)
    grid_y = get_spacing(horizontal_profile)

    if grid_x is None or grid_y is None:
        return None

    # Convert to grid boxes
    boxes_x = w / grid_x
    boxes_y = h / grid_y

    return boxes_x, boxes_y
def get_shadow_grid_length(frame, shadowThreshold=80):

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold to isolate shadow
    _, mask = cv2.threshold(gray, shadowThreshold, 255, cv2.THRESH_BINARY_INV)

    # Clean noise
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Largest contour = shadow
    shadow = max(contours, key=cv2.contourArea)

    # Get bounding box
    x, y, w, h = cv2.boundingRect(shadow)

    # --- Estimate grid size ---
    # Detect grid spacing using edges
    edges = cv2.Canny(gray, 50, 150)

    # Sum edges vertically and horizontally
    vertical_profile = np.sum(edges, axis=0)
    horizontal_profile = np.sum(edges, axis=1)

    # Find peaks (grid lines)
    def get_spacing(profile):
        peaks = np.where(profile > np.mean(profile))[0]
        if len(peaks) < 2:
            return None
        diffs = np.diff(peaks)
        return int(np.median(diffs))

    grid_x = get_spacing(vertical_profile)
    grid_y = get_spacing(horizontal_profile)

    if grid_x is None or grid_y is None:
        return None

    # Convert pixel length → grid boxes
    boxes_x = w / grid_x
    boxes_y = h / grid_y

    return boxes_x, boxes_y
def get_object_dimensions():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Getting object dimensions", frame)
        if cv2.waitKey(1) == ord('q'):
            break
        result = get_object_dimensions_grid(frame)

    cap.release()
    return result

#***********************************
#Gui Functions
#***********************************
# def get_object_button_clicked():
#     object_y, object_x = get_object_dimensions()
#     print(f"Object dimensions: {object_x:.1f} grid boxes (x), {object_y:.1f} grid boxes (y)")

# def define_gui():
#     root = tk.Tk()
#     root.title("Shadow Angle Estimation")
#     get_object = tk.Button(root, text="Get Object Dimensions", command=get_object_button_clicked)



    # Create a label to display the video feed
    # label = tk.Label(root)
    # label.pack()

    # return root, label



#***********************************
#Main code to run angle estimation
#***********************************
if __name__ == "__main__":
   
    #Get object dimensions (in grid boxes)
    object_y, object_x = get_object_dimensions()
    angle=None

    #Open new window to estimate angle
    cap = cv2.VideoCapture(0)
    while True:
        if object_x is None or object_y is None:
            break

        ret, frame = cap.read()
        if not ret:
            break

        result = get_shadow_grid_length(frame)
        if result:
            boxes_x, boxes_y = result
            print(f"Shadow length: {boxes_x:.1f} grid boxes (x), {boxes_y:.1f} grid boxes (y)")

        #See which shadow is actually y based on the aspect ratio
        base_shadow_length=0
        height_shadow_length=0
        base_object_length=0
        height_object_length=0
        if boxes_x and boxes_y:
            #Dimenstion closest to the objects dimeension should be labeled as base the other is height
            ratios=[boxes_x/object_x, boxes_y/object_y, boxes_x/object_y, boxes_y/object_x]
            closest_ratio = min(ratios, key=lambda x: abs(x - 1))
            if closest_ratio == ratios[0] or closest_ratio == ratios[3]:
                print("Base (x) is the shadow length, Height (y) is the shadow width")
                base_shadow_length = boxes_x
                height_shadow_length = boxes_y
                if closest_ratio == ratios[0]:
                    base_object_length = object_x
                    height_object_length = object_y
                else:
                    base_object_length = object_y
                    height_object_length = object_x
            else:
                print("Height (y) is the shadow length, Base (x) is the shadow width")
                base_shadow_length = boxes_y
                height_shadow_length = boxes_x
                if closest_ratio == ratios[1]:
                    base_object_length = object_y
                    height_object_length = object_x
                else:
                    base_object_length = object_x
                    height_object_length = object_y
            pass

        #Get angle using ratio of shadow length to object length
        angle=float(math.degrees(math.atan(height_object_length/height_shadow_length)))
        

        cv2.imshow("Estimated Angle", frame)
        if cv2.waitKey(1) == ord('q'):
            break
        time.sleep(0.05)#Slow down loop

    cap.release()
    cv2.destroyAllWindows()
    print(f"Estimated angle of light source: {angle:6.1f} degrees")
