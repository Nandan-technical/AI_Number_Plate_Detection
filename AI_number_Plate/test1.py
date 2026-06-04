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
# TESSERACT PATH
# =========================================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================================
# DATABASE CONNECTION
# =========================================
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="number_plate",
        user="postgres",
        password="Nandan@123"
    )

# =========================================
# STREAMLIT PAGE
# =========================================
st.set_page_config(page_title="AI Number Plate Detection")

st.title("🚗 AI Number Plate Detection System")

# =========================================
# AVOID MULTIPLE DEDUCTIONS
# =========================================
last_detected_plate = ""
last_detection_time = 0

# =========================================
# NUMBER PLATE DETECTION FUNCTION
# =========================================
def detect_number_plate(image):

    image = imutils.resize(image, width=700)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Noise reduction
    gray = cv2.bilateralFilter(gray, 13, 15, 15)

    # Edge detection
    edged = cv2.Canny(gray, 30, 200)

    # Find contours
    contours, _ = cv2.findContours(
        edged.copy(),
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True
    )[:20]

    plate_contour = None

    # =========================================
    # FIND RECTANGLE CONTOUR
    # =========================================
    for contour in contours:

        perimeter = cv2.arcLength(contour, True)

        approx = cv2.approxPolyDP(
            contour,
            0.018 * perimeter,
            True
        )

        # Number plate usually rectangle
        if len(approx) == 4:
            plate_contour = approx
            break

    if plate_contour is None:
        return None, None

    # =========================================
    # DRAW CONTOUR
    # =========================================
    cv2.drawContours(
        image,
        [plate_contour],
        -1,
        (0, 255, 0),
        3
    )

    # =========================================
    # CROP PLATE
    # =========================================
    x, y, w, h = cv2.boundingRect(plate_contour)

    padding = 15

    x = max(0, x - padding)
    y = max(0, y - padding)

    plate = image[
        y:y+h+padding,
        x:x+w+padding
    ]

    # =========================================
    # OCR PREPROCESSING
    # =========================================
    plate_gray = cv2.cvtColor(
        plate,
        cv2.COLOR_BGR2GRAY
    )

    # Blur
    plate_gray = cv2.GaussianBlur(
        plate_gray,
        (3, 3),
        0
    )

    # Threshold
    _, thresh = cv2.threshold(
        plate_gray,
        120,
        255,
        cv2.THRESH_BINARY
    )

    # Morphology
    kernel = np.ones((1, 1), np.uint8)

    thresh = cv2.dilate(
        thresh,
        kernel,
        iterations=1
    )

    thresh = cv2.erode(
        thresh,
        kernel,
        iterations=1
    )

    # =========================================
    # OCR CONFIG
    # =========================================
    config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    text = pytesseract.image_to_string(
        thresh,
        config=config
    )

    # =========================================
    # CLEAN TEXT
    # =========================================
    text = re.sub(r'[^A-Z0-9]', '', text)

    text = text.strip().upper()

    # Avoid invalid OCR
    if len(text) < 5:
        text = ""

    print("Detected Plate:", text)

    return plate, text

# =========================================
# SAVE TO CSV
# =========================================
def save_to_csv(number_plate):

    file_exists = os.path.isfile("data.csv")

    df = pd.DataFrame({
        "timestamp": [time.asctime()],
        "number_plate": [number_plate]
    })

    df.to_csv(
        "data.csv",
        mode='a',
        header=not file_exists,
        index=False
    )

# =========================================
# DEDUCT TOLL BALANCE
# =========================================
def deduct_balance(number_plate):

    global last_detected_plate
    global last_detection_time

    current_time = time.time()

    # =========================================
    # PREVENT MULTIPLE DEDUCTIONS
    # =========================================
    if (
        number_plate == last_detected_plate
        and current_time - last_detection_time < 10
    ):
        return "duplicate", None

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT amount
        FROM vehicle_registration
        WHERE vehicle_number=%s
        """,
        (number_plate,)
    )

    result = cursor.fetchone()

    if result:

        current_balance = float(result[0])

        toll_amount = 50

        # =========================================
        # CHECK BALANCE
        # =========================================
        if current_balance >= toll_amount:

            new_balance = current_balance - toll_amount

            cursor.execute(
                """
                UPDATE vehicle_registration
                SET amount=%s
                WHERE vehicle_number=%s
                """,
                (new_balance, number_plate)
            )

            conn.commit()

            # Save last detected
            last_detected_plate = number_plate
            last_detection_time = current_time

            cursor.close()
            conn.close()

            return True, new_balance

        else:

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

    if plate_img is not None and number_plate != "":

        st.image(
            plate_img,
            caption="Detected Number Plate",
            use_container_width=True
        )

        st.success(
            f"✅ Detected Number Plate: {number_plate}"
        )

        # Save CSV
        save_to_csv(number_plate)

        # Deduct Balance
        status, balance = deduct_balance(number_plate)

        if status is True:

            st.success("💰 Toll Deducted Successfully")

            st.info(
                f"Remaining Balance: ₹{balance}"
            )

        elif status == "duplicate":

            st.warning(
                "⚠ Same vehicle already detected recently"
            )

        elif status is False:

            st.error("❌ Insufficient Balance")

        else:

            st.error("❌ Vehicle Not Registered")

    else:

        st.error("❌ No Number Plate Detected")

# =========================================
# IMAGE UPLOAD
# =========================================
uploaded_file = st.file_uploader(
    "📂 Upload Vehicle Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    file_bytes = np.asarray(
        bytearray(uploaded_file.read()),
        dtype=np.uint8
    )

    image = cv2.imdecode(file_bytes, 1)

    st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )

    process_detection(image)

# =========================================
# CAMERA DETECTION
# =========================================
if st.button("📷 Open Camera & Detect"):

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        st.error("❌ Cannot Open Camera")

    else:

        st.info("📷 Press SPACE to Capture")

        captured_frame = None

        while True:

            ret, frame = cap.read()

            if not ret:
                st.error("❌ Camera Error")
                break

            frame = imutils.resize(frame, width=700)

            cv2.imshow(
                "Press SPACE to Capture",
                frame
            )

            key = cv2.waitKey(1)

            # SPACE
            if key == 32:

                captured_frame = frame.copy()
                break

            # ESC
            elif key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_frame is not None:

            process_detection(captured_frame) 