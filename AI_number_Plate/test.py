import numpy as np
import cv2
import imutils
import pytesseract
import pandas as pd
import time
import re
import os

# ==========================================
# TESSERACT PATH
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ==========================================
# OPEN CAMERA
# ==========================================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera not working")
    exit()

print("📷 Press 'C' to Capture")
print("❌ Press 'ESC' to Exit")

image = None

# ==========================================
# CAMERA LOOP
# ==========================================
while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Failed to read camera")
        break

    # Resize for better speed
    frame = imutils.resize(frame, width=700)

    cv2.putText(
        frame,
        "Press C to Capture",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Number Plate Detection", frame)

    key = cv2.waitKey(1) & 0xFF

    # Capture
    if key == ord('c'):
        image = frame.copy()
        print("✅ Image Captured")
        break

    # ESC
    elif key == 27:
        print("❌ Detection Cancelled")
        break

cap.release()
cv2.destroyAllWindows()

# ==========================================
# CHECK IMAGE
# ==========================================
if image is None:
    print("❌ No Image Captured")
    exit()

# ==========================================
# IMAGE PREPROCESSING
# ==========================================
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Noise reduction
gray = cv2.bilateralFilter(gray, 13, 15, 15)

# Edge detection
edged = cv2.Canny(gray, 30, 200)

# ==========================================
# FIND CONTOURS
# ==========================================
contours, _ = cv2.findContours(
    edged.copy(),
    cv2.RETR_TREE,
    cv2.CHAIN_APPROX_SIMPLE
)

contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

number_plate_contour = None

# ==========================================
# DETECT RECTANGLE PLATE
# ==========================================
for contour in contours:

    perimeter = cv2.arcLength(contour, True)

    approx = cv2.approxPolyDP(
        contour,
        0.018 * perimeter,
        True
    )

    # Plate usually has 4 corners
    if len(approx) == 4:
        number_plate_contour = approx
        break

# ==========================================
# OCR DETECTION
# ==========================================
detected_number = "UNKNOWN"

if number_plate_contour is not None:

    # Draw contour
    cv2.drawContours(image, [number_plate_contour], -1, (0, 255, 0), 3)

    x, y, w, h = cv2.boundingRect(number_plate_contour)

    # Add padding
    padding = 15

    x = max(0, x - padding)
    y = max(0, y - padding)

    w = w + (padding * 2)
    h = h + (padding * 2)

    plate = image[y:y+h, x:x+w]

    # ==========================================
    # OCR PREPROCESSING
    # ==========================================
    plate_gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)

    # Sharpen image
    plate_gray = cv2.GaussianBlur(plate_gray, (3, 3), 0)

    # Binary threshold
    _, thresh = cv2.threshold(
        plate_gray,
        120,
        255,
        cv2.THRESH_BINARY
    )

    # ==========================================
    # OCR CONFIG
    # ==========================================
    config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    text = pytesseract.image_to_string(thresh, config=config)

    # ==========================================
    # CLEAN TEXT
    # ==========================================
    detected_number = re.sub(r'[^A-Z0-9]', '', text)

    detected_number = detected_number.strip().upper()

    # ==========================================
    # FAIL SAFE
    # ==========================================
    if len(detected_number) < 5:
        detected_number = "UNKNOWN"

    print("🚗 Detected Number Plate:", detected_number)

    # ==========================================
    # SHOW DETECTED PLATE
    # ==========================================
    cv2.imshow("Detected Plate", plate)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

else:
    print("❌ No Number Plate Found")

# ==========================================
# SAVE CSV
# ==========================================
try:

    # Create file if not exists
    file_exists = os.path.isfile("data.csv")

    df = pd.DataFrame({
        "timestamp": [time.asctime()],
        "number_plate": [detected_number]
    })

    df.to_csv(
        "data.csv",
        mode='a',
        header=not file_exists,
        index=False
    )

    print("✅ Saved to data.csv")

except Exception as e:
    print("❌ CSV Error:", e)

# ==========================================
# FINAL OUTPUT
# ==========================================
print("===================================")
print("FINAL DETECTED NUMBER :", detected_number)
print("===================================")