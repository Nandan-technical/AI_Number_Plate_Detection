import cv2
import numpy as np

# -------------------------------
# Video Capture
# -------------------------------
cap = cv2.VideoCapture('cars.mp4')

if not cap.isOpened():
    print("❌ Video not found")
    exit()

# -------------------------------
# Parameters
# -------------------------------
min_width = 40
min_height = 40
offset = 10
line_height = 550

detected_centers = []
car_count = 0

# -------------------------------
# Centroid Function
# -------------------------------
def get_centroid(x, y, w, h):
    return (int(x + w / 2), int(y + h / 2))

# -------------------------------
# Read Frames
# -------------------------------
ret, frame1 = cap.read()
ret, frame2 = cap.read()

while ret:

    # Frame difference
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Improved threshold
    _, thresh = cv2.threshold(blur, 25, 255, cv2.THRESH_BINARY)

    dilated = cv2.dilate(thresh, np.ones((5, 5)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw counting line ONCE
    cv2.line(frame1, (0, line_height), (1200, line_height), (0, 255, 0), 2)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if w < min_width or h < min_height:
            continue

        # Draw rectangle
        cv2.rectangle(frame1, (x, y), (x+w, y+h), (255, 0, 0), 2)

        center = get_centroid(x, y, w, h)
        detected_centers.append(center)

        cv2.circle(frame1, center, 5, (0, 0, 255), -1)

        cx, cy = center

        # Check if vehicle crosses line
        if (line_height - offset) < cy < (line_height + offset):
            car_count += 1
            print("🚗 Car Count:", car_count)

            # Remove nearby points to avoid duplicate counting
            detected_centers = [
                pt for pt in detected_centers
                if abs(pt[1] - cy) > offset
            ]

    # Display count
    cv2.putText(frame1, f"Cars: {car_count}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Vehicle Counter", frame1)

    # Exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

    frame1 = frame2
    ret, frame2 = cap.read()

# Cleanup
cap.release()
cv2.destroyAllWindows()