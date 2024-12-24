import cv2
import numpy as np
from django.http import StreamingHttpResponse
from django.shortcuts import render

# Load the MobileNet-SSD model
MODEL_PATH = "models/"
prototxt_path = MODEL_PATH + "deploy.prototxt"
model_path = MODEL_PATH + "mobilenet_iter_73000.caffemodel"
net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

# Open the webcam feed
cap = cv2.VideoCapture(0)

def detect_person(frame):
    """Run MobileNet-SSD detection on the frame."""
    # Prepare the frame for the network
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)

    # Pass the blob through the network
    net.setInput(blob)
    detections = net.forward()

    # Loop through detections
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        # Filter out weak detections
        if confidence > 0.5:
            idx = int(detections[0, 0, i, 1])  # Class index
            if idx == 15:  # Class ID 15 corresponds to 'person'
                # Get bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Draw the bounding box and label
                label = f"Person: {confidence * 100:.2f}%"
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.putText(frame, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame

def generate_frames():
    """Generate video frames with detection."""
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = detect_person(frame)  # Process the frame
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def video_feed(request):
    """Stream the video feed."""
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    """Render the main page."""
    return render(request, 'index.html')
