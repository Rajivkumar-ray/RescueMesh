import cv2
import requests
import sys
import uuid
import time

from ultralytics import YOLO


# ==========================================
# RESCUEMESH AI VICTIM DETECTION
# ==========================================

# FastAPI Backend URL
API_URL = "http://127.0.0.1:8000/detect-victim"

# Demo location (Bhopal)
# Replace with actual GPS coordinates later
LATITUDE = 23.265
LONGITUDE = 77.405

# Load YOLO Model
model = YOLO("yolo11n.pt")

# Store already reported victim IDs
sent_victims = set()


# ==========================================
# SEND VICTIM DATA TO BACKEND
# ==========================================

def send_victim_to_backend(victim_id, confidence):

    payload = {
        "victim_id": victim_id,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "confidence": round(confidence, 2),
        "priority": "high",
        "road_status": "unsafe"
    }

    try:

        response = requests.post(
            API_URL,
            json=payload,
            timeout=3
        )

        if response.status_code == 200:

            print(
                "Victim successfully saved:",
                victim_id
            )

            sent_victims.add(victim_id)

        else:

            print(
                "API Error:",
                response.status_code,
                response.text
            )

    except requests.RequestException as error:

        print(
            "Backend connection error:",
            error
        )


# ==========================================
# MAIN AI DETECTION FUNCTION
# ==========================================

def main():

    print("=================================")
    print("RescueMesh AI Detection Starting")
    print("=================================")

    # Open laptop webcam
    cap = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():

        print("ERROR: Webcam open nahi ho raha.")
        print("Camera permissions check karo.")

        sys.exit(1)

    print("Webcam successfully opened!")
    print("Camera ke saamne aao.")
    print("Detection stop karne ke liye Q press karo.")

    # Track when each person was last reported
    last_reported = {}

    # Minimum interval between reports
    REPORT_INTERVAL = 30

    try:

        while True:

            # Read camera frame
            ret, frame = cap.read()

            if not ret:

                print("ERROR: Camera frame nahi mila.")
                break

            # ==================================
            # RUN YOLO AI DETECTION
            # ==================================

            results = model.track(
                source=frame,
                conf=0.40,
                classes=[0],
                persist=True,
                verbose=False
            )

            person_count = 0

            # ==================================
            # PROCESS DETECTED PERSONS
            # ==================================

            for result in results:

                for box in result.boxes:

                    class_id = int(box.cls[0])

                    confidence = float(box.conf[0])

                    # COCO class 0 = person
                    if class_id != 0:
                        continue

                    person_count += 1

                    # Bounding box coordinates
                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0].tolist()
                    )

                    # ==================================
                    # GENERATE VICTIM ID
                    # ==================================

                    if box.id is not None:

                        track_id = int(box.id[0])

                        victim_id = f"V{track_id}"

                    else:

                        victim_id = (
                            "V" +
                            uuid.uuid4().hex[:8]
                        )

                    # ==================================
                    # SEND DATA TO BACKEND
                    # ==================================

                    current_time = time.time()

                    last_time = last_reported.get(
                        victim_id,
                        0
                    )

                    if (
                        victim_id not in sent_victims
                        and current_time - last_time
                        >= REPORT_INTERVAL
                    ):

                        last_reported[victim_id] = current_time

                        send_victim_to_backend(
                            victim_id,
                            confidence
                        )

                    # ==================================
                    # DRAW GREEN BOUNDING BOX
                    # ==================================

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    # Display detection confidence
                    label = (
                        f"{victim_id} "
                        f"Person: {confidence:.2f}"
                    )

                    cv2.putText(
                        frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

            # ==================================
            # DISPLAY PERSON COUNT
            # ==================================

            cv2.putText(
                frame,
                f"Persons Detected: {person_count}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            # ==================================
            # SHOW LIVE CAMERA
            # ==================================

            cv2.imshow(
                "RescueMesh - AI Victim Detection",
                frame
            )

            # Press Q to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:

        print("Detection interrupted.")

    finally:

        cap.release()

        cv2.destroyAllWindows()

        print("=================================")
        print("RescueMesh AI Detection Stopped")
        print("=================================")


# ==========================================
# PROGRAM ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()