import cv2
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path='yolov8n.pt'):
        # Load YOLOv8 model (Nano version for speed)
        self.model = YOLO(model_path)
        # Vehicle classes in COCO dataset: 2 (car), 3 (motorcycle), 5 (bus), 7 (truck)
        self.vehicle_classes = [2, 3, 5, 7]

    def detect(self, frame):
        """
        Detect vehicles in a frame.
        Returns: List of bounding boxes [x1, y1, x2, y2, confidence, class_id]
        """
        results = self.model(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            class_id = int(box.cls[0])
            if class_id in self.vehicle_classes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                detections.append([x1, y1, x2, y2, conf, class_id])
                
        return detections
