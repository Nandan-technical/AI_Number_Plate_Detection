import cv2
import time
import os
import sys
from ultralytics import YOLO

# -------------------------------
# Load YOLO Model
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

model = YOLO(MODEL_PATH)

# Correct COCO vehicle classes
vehicle_classes = ["car", "motorcycle", "bus", "truck"]

# -------------------------------
# Load Videos
# -------------------------------
video_road1 = cv2.VideoCapture(
    os.path.join(BASE_DIR, "road1.mp4")
)

video_road2 = cv2.VideoCapture(
    os.path.join(BASE_DIR, "road2.mp4")
)

# Check if videos opened
if not video_road1.isOpened():
    print("❌ road1.mp4 not found")
    sys.exit()

if not video_road2.isOpened():
    print("❌ road2.mp4 not found")
    sys.exit()

# -------------------------------
# Count Vehicles Function
# -------------------------------
def count_vehicles(frame):

    results = model(frame)

    vehicle_boxes = [
        box
        for r in results
        for box in r.boxes
        if (
            model.names[int(box.cls[0])] in vehicle_classes
            and float(box.conf[0]) > 0.50
        )
    ]

    vehicle_count = len(vehicle_boxes)

    for box in vehicle_boxes:

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        conf = float(box.conf[0]) * 100

        cls = model.names[
            int(box.cls[0])
        ]

        label = f"{cls} {conf:.1f}%"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    return vehicle_count, frame

# -------------------------------
# Traffic Logic Variables
# -------------------------------
road1_green = True

last_count_time = time.time()

THRESHOLD = 8
INTERVAL = 3

print(
    "🚦 Traffic system started... Press ESC to exit"
)

# -------------------------------
# Main Loop
# -------------------------------
while True:

    # ---------------- ROAD 1 ----------------
    if road1_green:

        ret1, frame1 = video_road1.read()

        if not ret1:
            print("⚠ End of Road 1 video")
            break

        frame1 = cv2.resize(
            frame1,
            (800, 500)
        )

        vehicle_count, frame1 = count_vehicles(
            frame1
        )

        cv2.putText(
            frame1,
            "ROAD 1: GREEN",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame1,
            "ROAD 2: RED",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        if time.time() - last_count_time >= INTERVAL:

            print(
                f"[ROAD 1] Vehicles: {vehicle_count}"
            )

            if vehicle_count > THRESHOLD:

                print(
                    "➡ Road 1 stays GREEN"
                )

            else:

                print(
                    "🔁 Switching to Road 2 GREEN"
                )

                road1_green = False

            last_count_time = time.time()

        cv2.imshow(
            "Traffic Control",
            frame1
        )

    # ---------------- ROAD 2 ----------------
    else:

        ret2, frame2 = video_road2.read()

        if not ret2:
            print("⚠ End of Road 2 video")
            break

        frame2 = cv2.resize(
            frame2,
            (800, 500)
        )

        vehicle_count, frame2 = count_vehicles(
            frame2
        )

        cv2.putText(
            frame2,
            "ROAD 1: RED",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame2,
            "ROAD 2: GREEN",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        if time.time() - last_count_time >= INTERVAL:

            print(
                f"[ROAD 2] Vehicles: {vehicle_count}"
            )

            if vehicle_count > THRESHOLD:

                print(
                    "➡ Road 2 stays GREEN"
                )

            else:

                print(
                    "🔁 Switching to Road 1 GREEN"
                )

                road1_green = True

            last_count_time = time.time()

        cv2.imshow(
            "Traffic Control",
            frame2
        )

    # Exit on ESC
    if cv2.waitKey(1) & 0xFF == 27:

        print("🛑 Exiting...")
        break

# -------------------------------
# Cleanup
# -------------------------------
if video_road1:
    video_road1.release()

if video_road2:
    video_road2.release()

cv2.destroyAllWindows()