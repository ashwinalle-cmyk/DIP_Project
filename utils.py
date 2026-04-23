import cv2

def draw_detections(frame, track_id, ltrb, class_id, risk_data):
    """
    Draw bounding boxes, ID, and risk score on the frame.
    """
    x1, y1, x2, y2 = map(int, ltrb)
    color = (0, 255, 0) # Green for safe
    if risk_data["category"] == "High Risk":
        color = (0, 0, 255) # Red for high risk
    elif risk_data["category"] == "Moderate Risk":
        color = (0, 255, 255) # Yellow for moderate risk
        
    # Draw bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Draw ID, risk score, speed, and license plate
    plate = f" | Plate: {risk_data['license_plate']}" if risk_data.get('license_plate') else ""
    speed = f" | {risk_data.get('speed_kmh', 0)} km/h"
    label = f"ID: {track_id} | Risk: {risk_data['score']}% ({risk_data['category']}){speed}{plate}"
    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Draw explainability text
    explanation = risk_data["explainability"]
    cv2.putText(frame, explanation, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return frame

def preprocess_frame(frame, target_size=(640, 640)):
    """
    Resize and normalize frame.
    """
    frame_resized = cv2.resize(frame, target_size)
    return frame_resized
