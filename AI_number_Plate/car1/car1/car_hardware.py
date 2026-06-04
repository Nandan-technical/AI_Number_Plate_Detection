import cv2
import time
from ultralytics import YOLO
import serial
import time

# Establish serial communication with Arduino
arduino = serial.Serial(port='COM14', baudrate=9600, timeout=1)  # Replace 'COM3' with your Arduino's port
time.sleep(2)

# Initialize YOLO model
model = YOLO("yolo-Weights/yolov8n.pt")

# Vehicle classes (YOLO's COCO dataset IDs)
vehicle_classes = ["car", "motorbike", "bus", "truck"]

# Open video feeds for road 1 and road 2
video_road1 = cv2.VideoCapture("road1.mp4")  # Replace with video path for road 1
video_road2 = cv2.VideoCapture("road2.mp4")  # Replace with video path for road 2

def count_vehicles(frame):
    """Count vehicles in a given frame and return the vehicle count and frame with bounding boxes."""
    vehicle_count = 0
    results = model(frame, stream=True)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            if class_name in vehicle_classes:
                vehicle_count += 1

                # Draw bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box coordinates
                confidence = float(box.conf[0]) * 100  # Confidence score
                label = f"{class_name} {confidence:.1f}%"
                
                # Draw rectangle and label
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return vehicle_count, frame

# Initialize frame counter and traffic state
frame_counter = 0
road1_green = True
last_count_time = time.time()

while True:
    # Road 1 is Green, Road 2 is Red
    if road1_green:
        print("[INFO] Road 1: GREEN, Road 2: RED")
        ret1, frame1 = video_road1.read()
        if not ret1:
            break

        # Count vehicles on Road 1 at 3-second intervals
        vehicle_count_road1, frame1 = count_vehicles(frame1)

        # Display road status continuously
        cv2.putText(frame1, "ROAD 1: GREEN", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame1, "ROAD 2: RED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Count vehicles every 3 seconds
        if time.time() - last_count_time >= 3:
            print(f"[INFO] Vehicles on Road 1 at 3rd second: {vehicle_count_road1}")
            last_count_time = time.time()

            # Switch road status if vehicle count on Road 1 is <= 10
            if vehicle_count_road1 > 8:
                print("[INFO] Road 1 remains GREEN.")
                arduino.write(b'A')  # Send the character 'A' to Arduino
                print("[INFO] Sent 'A' to Arduino.")
            else:
                print("[INFO] Switching to Road 2: GREEN.")
                road1_green = False
                last_count_time = time.time()  # Reset the counter for Road 2

        # Display the frame with bounding boxes and status
        cv2.imshow("Traffic Analysis", frame1)

    # Road 2 is Green, Road 1 is Red
    else:
        print("[INFO] Road 2: GREEN, Road 1: RED")
        ret2, frame2 = video_road2.read()
        if not ret2:
            break

        # Count vehicles on Road 2 at 3-second intervals
        vehicle_count_road2, frame2 = count_vehicles(frame2)

        # Display road status continuously
        cv2.putText(frame2, "ROAD 1: RED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame2, "ROAD 2: GREEN", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Count vehicles every 3 seconds
        if time.time() - last_count_time >= 3:
            print(f"[INFO] Vehicles on Road 2 at 3rd second: {vehicle_count_road2}")
            last_count_time = time.time()

            # Switch road status if vehicle count on Road 2 is <= 10
            if vehicle_count_road2 > 8:
                print("[INFO] Road 2 remains GREEN.")
                arduino.write(b'B')  # Send the character 'A' to Arduino
                print("[INFO] Sent 'B' to Arduino.")
            else:
                print("[INFO] Switching to Road 1: GREEN.")
                road1_green = True
                last_count_time = time.time()  # Reset the counter for Road 1

        # Display the frame with bounding boxes and status
        cv2.imshow("Traffic Analysis", frame2)

    # Exit on ESC key
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release resources
video_road1.release()
video_road2.release()
cv2.destroyAllWindows()
