import numpy as np
import cv2
import imutils
import pytesseract
import pandas as pd
import time
import streamlit as st
import re
import psycopg2
import os

# =========================================
# TESSERACT PATH (IMPORTANT FIX)
# =========================================
# ❌ Windows-only path removed for deployment safety
# ✔ Use environment variable or default system path

pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD",
    "tesseract"   # works in Linux/Render if installed
)

# =========================================
# DATABASE CONNECTION (SAFE)
# =========================================
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "number_plate"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Nandan@123")
        )
    except Exception as e:
        print("Database Connection Error:", e)
        return None

# =========================================
# STREAMLIT UI
# =========================================
st.set_page_config(page_title="AI Number Plate Detection")
st.title("🚗 AI Number Plate Detection System")

# =========================================
# GLOBAL VARIABLES
# =========================================
last_detected_plate = ""
last_detection_time = 0

# =========================================
# NUMBER PLATE DETECTION
# =========================================
def detect_number_plate(image):

    image = imutils.resize(image, width=700)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.bilateralFilter(gray, 13, 15, 15)

    edged = cv2.Canny(gray, 30, 200)

    contours, _ = cv2.findContours(
        edged.copy(),
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    plate_contour = None

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)

        approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)

        if len(approx) == 4:
            plate_contour = approx
            break

    if plate_contour is None:
        return None, None

    cv2.drawContours(image, [plate_contour], -1, (0, 255, 0), 3)

    x, y, w, h = cv2.boundingRect(plate_contour)

    padding = 15

    x = max(0, x - padding)
    y = max(0, y - padding)

    plate = image[y:y+h+padding, x:x+w+padding]

    plate_gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)

    plate_gray = cv2.GaussianBlur(plate_gray, (3, 3), 0)

    _, thresh = cv2.threshold(plate_gray, 120, 255, cv2.THRESH_BINARY)

    kernel = np.ones((1, 1), np.uint8)

    thresh = cv2.dilate(thresh, kernel, iterations=1)
    thresh = cv2.erode(thresh, kernel, iterations=1)

    config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    text = pytesseract.image_to_string(thresh, config=config)

    text = re.sub(r'[^A-Z0-9]', '', text).strip().upper()

    if len(text) < 5:
        text = ""

    return plate, text

# =========================================
# SAVE CSV (SAFE PATH FIX)
# =========================================
def save_to_csv(number_plate):

    file_path = os.path.join(os.getcwd(), "data.csv")
    file_exists = os.path.isfile(file_path)

    df = pd.DataFrame({
        "timestamp": [time.asctime()],
        "number_plate": [number_plate]
    })

    df.to_csv(file_path, mode='a', header=not file_exists, index=False)

# =========================================
# DEDUCT BALANCE (FIXED CONNECTION SAFETY)
# =========================================
def deduct_balance(number_plate):

    global last_detected_plate, last_detection_time

    current_time = time.time()

    if number_plate == last_detected_plate and current_time - last_detection_time < 10:
        return "duplicate", None

    conn = get_db_connection()
    if conn is None:
        return None, None

    cursor = conn.cursor()

    cursor.execute(
        "SELECT amount FROM vehicle_registration WHERE vehicle_number=%s",
        (number_plate,)
    )

    result = cursor.fetchone()

    if result:

        current_balance = float(result[0])
        toll_amount = 50

        if current_balance >= toll_amount:

            new_balance = current_balance - toll_amount

            cursor.execute(
                "UPDATE vehicle_registration SET amount=%s WHERE vehicle_number=%s",
                (new_balance, number_plate)
            )

            conn.commit()

            last_detected_plate = number_plate
            last_detection_time = current_time

            cursor.close()
            conn.close()

            return True, new_balance

        cursor.close()
        conn.close()
        return False, current_balance

    cursor.close()
    conn.close()
    return None, None

# =========================================
# PROCESS DETECTION
# =========================================
def process_detection(image):

    plate_img, number_plate = detect_number_plate(image)

    if plate_img is not None and number_plate:

        st.image(plate_img, caption="Detected Plate", use_container_width=True)

        st.success(f"Detected: {number_plate}")

        save_to_csv(number_plate)

        status, balance = deduct_balance(number_plate)

        if status is True:
            st.success("Toll Deducted Successfully")
            st.info(f"Remaining Balance: ₹{balance}")

        elif status == "duplicate":
            st.warning("Duplicate Detection Ignored")

        elif status is False:
            st.error("Insufficient Balance")

        else:
            st.error("Vehicle Not Registered")

    else:
        st.error("No Number Plate Detected")

# =========================================
# FILE UPLOAD
# =========================================
uploaded_file = st.file_uploader(
    "Upload Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)

    st.image(image, caption="Uploaded Image", use_container_width=True)

    process_detection(image)

# =========================================
# CAMERA MODE (SAFE FIX)
# =========================================
if st.button("Open Camera"):

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Camera not available")
    else:

        st.info("Press SPACE to capture")

        captured_frame = None

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            frame = imutils.resize(frame, width=700)

            cv2.imshow("Capture", frame)

            key = cv2.waitKey(1)

            if key == 32:
                captured_frame = frame.copy()
                break
            elif key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_frame is not None:
            process_detection(captured_frame)