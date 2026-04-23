import cv2
import numpy as np
import mediapipe as mp

class ContextAnalyzer:
    def __init__(self, min_detection_confidence=0.5):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, # 1 for far range (0-5m), 0 for short range (0-2m)
            min_detection_confidence=min_detection_confidence
        )

    def estimate_age(self, face_roi):
        """
        Estimate age from face ROI.
        """
        return 16 # Mocking an underage driver for testing

    def detect_license_plate(self, vehicle_roi):
        """
        Detect and read license plate from vehicle ROI.
        """
        # Placeholder for OCR (e.g., EasyOCR, Tesseract)
        # In a real app, you'd use a specialized model for plate detection and OCR.
        return "ABC-1234" # Mocking a license plate

    def analyze(self, frame, bbox):
        """
        Analyze vehicle context: Face (for age) and License Plate.
        Both are optional; tracking continues even if both are missing.
        """
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        vehicle_roi = frame[y1:y2, x1:x2]
        if vehicle_roi.size == 0:
            return {"age": None, "is_minor": False, "license_plate": None}
            
        driver_data = {"age": None, "is_minor": False, "license_plate": None}
        
        # 1. OPTIONAL: Face Detection (Only if visible)
        rgb_roi = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_roi)
        
        if results.detections:
            best_detection = max(results.detections, key=lambda d: d.score[0])
            bbox_rel = best_detection.location_data.relative_bounding_box
            v_h, v_w = vehicle_roi.shape[:2]
            
            fx = int(bbox_rel.xmin * v_w)
            fy = int(bbox_rel.ymin * v_h)
            fw = int(bbox_rel.width * v_w)
            fh = int(bbox_rel.height * v_h)
            
            fx, fy = max(0, fx), max(0, fy)
            fw, fh = min(v_w - fx, fw), min(v_h - fy, fh)
            
            if fw > 0 and fh > 0:
                face_roi = vehicle_roi[fy:fy+fh, fx:fx+fw]
                age = self.estimate_age(face_roi)
                driver_data["age"] = age
                driver_data["is_minor"] = age < 18
                driver_data["confidence"] = float(best_detection.score[0])

        # 2. OPTIONAL: License Plate Detection (Only if visible)
        # In a real app, you'd use a plate detector first, then OCR.
        # Here we mock the behavior of finding a plate.
        plate = self.detect_license_plate(vehicle_roi)
        if plate:
            driver_data["license_plate"] = plate
        
        return driver_data
