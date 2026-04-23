import numpy as np
import cv2
from collections import deque

class SpeedEstimator:
    def __init__(self, fps=30, history_len=10):
        self.fps = fps
        self.history_len = history_len
        self.pixel_to_meter_matrix = None
        self.is_calibrated = False
        
        # Default calibration points (example for a typical road scene)
        # These should be adjusted based on the specific camera view
        # Format: [top-left, top-right, bottom-right, bottom-left]
        src_points = np.float32([[467, 352], [1105, 352], [1280, 720], [0, 720]])
        # Real-world coordinates in meters (assuming 3.7m lane width and 20m distance)
        dst_points = np.float32([[0, 0], [3.7, 0], [3.7, 20], [0, 20]])
        
        self.calibrate(src_points, dst_points)

    def calibrate(self, src_points, dst_points):
        """
        Calculate homography matrix for perspective transformation.
        """
        try:
            self.pixel_to_meter_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            self.is_calibrated = True
        except Exception as e:
            print(f"Calibration failed: {e}")
            self.is_calibrated = False

    def transform_point(self, point):
        """
        Transform pixel coordinates to real-world coordinates (meters).
        """
        if not self.is_calibrated:
            return None
            
        point_array = np.array([[[point[0], point[1]]]], dtype=np.float32)
        transformed_point = cv2.perspectiveTransform(point_array, self.pixel_to_meter_matrix)
        return transformed_point[0][0]

    def calculate_speed(self, p1_px, p2_px):
        """
        Calculate speed between two pixel points in km/h.
        """
        if not self.is_calibrated:
            # Fallback to approximate mode (pixels to meters scale)
            # Assuming 100 pixels = 1 meter as a rough fallback
            dist_px = np.sqrt((p2_px[0] - p1_px[0])**2 + (p2_px[1] - p1_px[1])**2)
            dist_m = dist_px / 100.0
        else:
            p1_m = self.transform_point(p1_px)
            p2_m = self.transform_point(p2_px)
            dist_m = np.sqrt((p2_m[0] - p1_m[0])**2 + (p2_m[1] - p1_m[1])**2)
            
        # Speed = distance / time
        time_s = 1.0 / self.fps
        speed_mps = dist_m / time_s
        speed_kmph = speed_mps * 3.6
        
        return speed_kmph

class MotionAnalyzer:
    def __init__(self, fps=30, history_len=30):
        # Store history of centroids for each vehicle ID
        self.history = {} # {track_id: deque([centroid1, centroid2, ...])}
        self.speed_history = {} # {track_id: deque([speed1, speed2, ...])}
        self.history_len = history_len
        self.speed_estimator = SpeedEstimator(fps=fps)
        
        # Thresholds for rash driving detection (in km/h)
        self.speed_threshold = 80 # km/h
        self.zigzag_threshold = 0.8 # Variance in direction
        self.sudden_braking_threshold = 15 # km/h change per frame

    def analyze(self, track_id, centroid):
        """
        Analyze motion for a specific vehicle using high-precision speed estimation.
        """
        if track_id not in self.history:
            self.history[track_id] = deque(maxlen=self.history_len)
            self.speed_history[track_id] = deque(maxlen=10) # Smoothing over 10 frames
        
        self.history[track_id].append(centroid)
        
        if len(self.history[track_id]) < 2:
            return {
                "speed": 0, 
                "speed_kmh": 0,
                "acceleration": 0, 
                "direction_change": 0, 
                "is_rash": False, 
                "reason": "",
                "is_calibrated": self.speed_estimator.is_calibrated
            }
            
        # Calculate high-precision speed
        p1 = self.history[track_id][-2]
        p2 = self.history[track_id][-1]
        raw_speed_kmh = self.speed_estimator.calculate_speed(p1, p2)
        
        # Filter sudden spikes (e.g., tracking jumps)
        if raw_speed_kmh > 200: # Unrealistic speed
            raw_speed_kmh = self.speed_history[track_id][-1] if self.speed_history[track_id] else 0
            
        self.speed_history[track_id].append(raw_speed_kmh)
        
        # Smoothing (Moving Average)
        smooth_speed_kmh = sum(self.speed_history[track_id]) / len(self.speed_history[track_id])
        
        # Calculate acceleration (change in speed)
        acceleration = 0
        if len(self.speed_history[track_id]) >= 2:
            acceleration = smooth_speed_kmh - self.speed_history[track_id][-2]
            
        # Direction change (angle between vectors)
        direction_change = 0
        if len(self.history[track_id]) >= 3:
            p0 = self.history[track_id][-3]
            v1 = np.array([p1[0] - p0[0], p1[1] - p0[1]])
            v2 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 > 0 and norm2 > 0:
                cos_theta = np.dot(v1, v2) / (norm1 * norm2)
                direction_change = np.arccos(np.clip(cos_theta, -1.0, 1.0))
                
        # Rash driving detection logic
        is_rash = False
        reason = ""
        
        if smooth_speed_kmh > self.speed_threshold:
            is_rash = True
            reason = f"Speeding ({round(smooth_speed_kmh, 1)} km/h)"
        elif abs(acceleration) > self.sudden_braking_threshold:
            is_rash = True
            reason = "Sudden braking/acceleration"
        elif direction_change > 0.8: # High angle change
            is_rash = True
            reason = "Sharp turn/Zig-zag"
            
        return {
            "speed": smooth_speed_kmh, # For internal use
            "speed_kmh": round(smooth_speed_kmh, 1),
            "acceleration": acceleration,
            "direction_change": direction_change,
            "is_rash": is_rash,
            "reason": reason,
            "is_calibrated": self.speed_estimator.is_calibrated
        }
