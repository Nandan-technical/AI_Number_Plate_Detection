import cv2
import time
from ultralytics import YOLO
import serial

# -------------------------------
# Arduino Setup (SAFE)
# -------------------------------
try:
    arduino = serial.Serial(port='COM14', baudrate=9600, timeout=1)
    time.sleep(2)
    print("✅ Arduino Connected")
except:
    arduino = None
    print("⚠ Arduino not connected")

# -------------------------------
# YOLO Model
# -------------------------------
model = YOLO("yolov8n.pt")

vehicle_classes = ["car", "motorcycle", "bus", "truck"]

# -------------------------------
# Video Input
# -------------------------------
video_road1 = cv2.VideoCapture("road1.mp4")
video_road2 = cv2.VideoCapture("road2.mp4")

if not video_road1.isOpened():
    print("❌ road1.mp4 not found")
    exit()

if not video_road2.isOpened():
    print("❌ road2.mp4 not found")
    exit()

# -------------------------------
# Vehicle Detection
# -------------------------------
def count_vehicles(frame):
    results = model(frame)

    vehicle_boxes = [
        box for r in results
        for box in r.boxes
        if model.names[int(box.cls[0])] in vehicle_classes
    ]

    count = len(vehicle_boxes)

    for box in vehicle_boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0]) * 100
        cls = model.names[int(box.cls[0])]

        label = f"{cls} {conf:.1f}%"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return count, frame

# -------------------------------
# Traffic Logic
# -------------------------------
road1_green = True
last_count_time = time.time()
THRESHOLD = 8
INTERVAL = 3

# Prevent Arduino spam
last_signal = None

print("🚦 Smart Traffic System Started")

# -------------------------------
# Main Loop
# -------------------------------
while True:

    if road1_green:
        ret, frame = video_road1.read()
        if not ret:
            break

        frame = cv2.resize(frame, (800, 500))
        count, frame = count_vehicles(frame)

        cv2.putText(frame, "ROAD 1: GREEN", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "ROAD 2: RED", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if time.time() - last_count_time >= INTERVAL:
            print(f"[ROAD 1] Vehicles: {count}")

            if count > THRESHOLD:
                if arduino and last_signal != 'A':
                    arduino.write(b'A')
                    print("📤 Sent A (Road1 Green)")
                    last_signal = 'A'
            else:
                road1_green = False
                last_signal = None
                print("🔁 Switching to Road 2")

            last_count_time = time.time()

        cv2.imshow("Traffic Control", frame)

    else:
        ret, frame = video_road2.read()
        if not ret:
            break

        frame = cv2.resize(frame, (800, 500))
        count, frame = count_vehicles(frame)

        cv2.putText(frame, "ROAD 1: RED", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "ROAD 2: GREEN", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if time.time() - last_count_time >= INTERVAL:
            print(f"[ROAD 2] Vehicles: {count}")

            if count > THRESHOLD:
                if arduino and last_signal != 'B':
                    arduino.write(b'B')
                    print("📤 Sent B (Road2 Green)")
                    last_signal = 'B'
            else:
                road1_green = True
                last_signal = None
                print("🔁 Switching to Road 1")

            last_count_time = time.time()

        cv2.imshow("Traffic Control", frame)

    # Exit
    if cv2.waitKey(1) & 0xFF == 27:
        print("🛑 Exiting...")
        break

# -------------------------------
# Cleanup
# -------------------------------
video_road1.release()
video_road2.release()
cv2.destroyAllWindows()

if arduino:
    arduino.close()