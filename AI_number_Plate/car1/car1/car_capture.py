import cv2
import numpy as np

# capturing or reading video
cap = cv2.VideoCapture('cars.mp4')

# adjusting frame rate
fps = cap.set(cv2.CAP_PROP_FPS, 1)

# minimum contour width and height for vehicle detection
min_contour_width = 40  # minimum width for valid contour
min_contour_height = 40  # minimum height for valid contour
offset = 10   # margin for line detection
line_height = 550  # height of the detection line (threshold line)
matches = []  # list of vehicle centroids
cars = 0  # number of cars detected

# defining a function to get centroid of detected contours
def get_centroid(x, y, w, h):
    x1 = int(w / 2)
    y1 = int(h / 2)

    cx = x + x1
    cy = y + y1
    return cx, cy

# Set resolution of the video feed (optional)
cap.set(3, 1920)
cap.set(4, 1080)

# read initial frames
if cap.isOpened():
    ret, frame1 = cap.read()
else:
    ret = False

ret, frame1 = cap.read()
ret, frame2 = cap.read()

while ret:
    # Compute the absolute difference between the frames
    d = cv2.absdiff(frame1, frame2)
    grey = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(grey, (5, 5), 0)
    ret, th = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

    dilated = cv2.dilate(th, np.ones((3, 3)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

    # Fill any small holes
    closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for (i, c) in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(c)
        contour_valid = (w >= min_contour_width) and (h >= min_contour_height)

        if not contour_valid:
            continue

        # Draw rectangle around the detected vehicle
        cv2.rectangle(frame1, (x - 10, y - 10), (x + w + 10, y + h + 10), (255, 0, 0), 2)
        cv2.line(frame1, (0, line_height), (1200, line_height), (0, 255, 0), 2)

        # Get the centroid of the vehicle
        centroid = get_centroid(x, y, w, h)
        matches.append(centroid)
        cv2.circle(frame1, centroid, 5, (0, 255, 0), -1)

        # Classification logic for cars
        cx, cy = get_centroid(x, y, w, h)
        if (line_height + offset) > cy > (line_height - offset):
            cars += 1  # Detected a car
            matches.remove((cx, cy))  # Remove from matches as the car has passed
            print("Car detected, Total Cars: ", cars)

    # Display the total number of cars detected
    cv2.putText(frame1, "Total Cars: " + str(cars), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 170, 0), 2)

    # Show the video feed
    cv2.imshow("OUTPUT", frame1)

    # Wait for key press (27 is for ESC)
    if cv2.waitKey(1) == 27:
        break

    frame1 = frame2
    ret, frame2 = cap.read()

# Release the video capture and close the OpenCV windows
cv2.destroyAllWindows()
cap.release()
