import cv2
import argparse
import time
from detection import VehicleDetector
from tracking import VehicleTracker
from motion_analysis import MotionAnalyzer
from face_detection import ContextAnalyzer
from risk_scoring import RiskScorer
from utils import draw_detections, preprocess_frame

def main(video_path, output_path='output.mp4'):
    # Open video input
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return
        
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30 # Fallback
    
    # Initialize modules (some need FPS)
    detector = VehicleDetector()
    tracker = VehicleTracker()
    motion_analyzer = MotionAnalyzer(fps=fps)
    context_analyzer = ContextAnalyzer()
    risk_scorer = RiskScorer()
    
    # Define video writer for output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"Processing video: {video_path}...")
    
    # Metadata storage for persistent vehicle info (like license plates)
    vehicle_metadata = {}
    
    frame_count = 0
    analysis_interval = 5 # Perform heavy analysis (OCR/Face) every 5 frames
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # 1. Vehicle Detection
        detections = detector.detect(frame)
        
        # 2. Vehicle Tracking (PRIMARY - DeepSORT)
        tracked_objects = tracker.update(detections, frame)
        
        # 3. Analyze each tracked vehicle
        for track in tracked_objects:
            track_id, x1, y1, x2, y2, class_id = track
            centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Initialize metadata if new track
            if track_id not in vehicle_metadata:
                vehicle_metadata[track_id] = {
                    "license_plate": None,
                    "driver_age": None,
                    "is_minor": False
                }
            
            # 4. Motion Analysis (Every frame for smooth tracking/speed)
            motion_data = motion_analyzer.analyze(track_id, centroid)
            
            # 5. Driver Context Analysis (OPTIONAL ENHANCEMENT - Every N frames)
            if frame_count % analysis_interval == 0:
                driver_context = context_analyzer.analyze(frame, [x1, y1, x2, y2])
                
                # Update metadata if new info found (e.g., plate becomes visible)
                if driver_context["license_plate"]:
                    vehicle_metadata[track_id]["license_plate"] = driver_context["license_plate"]
                if driver_context["age"]:
                    vehicle_metadata[track_id]["driver_age"] = driver_context["age"]
                    vehicle_metadata[track_id]["is_minor"] = driver_context["is_minor"]
            
            # Combine current motion with persistent metadata
            combined_driver_data = {
                "age": vehicle_metadata[track_id]["driver_age"],
                "is_minor": vehicle_metadata[track_id]["is_minor"],
                "license_plate": vehicle_metadata[track_id]["license_plate"]
            }
            
            # 6. Risk Scoring
            risk_data = risk_scorer.calculate_risk(motion_data, combined_driver_data)
            
            # 7. Output Visualization
            frame = draw_detections(frame, track_id, [x1, y1, x2, y2], class_id, risk_data)
            
            # Print explainability for risky vehicles
            if risk_data["category"] == "High Risk":
                print(f"Vehicle ID {track_id}: {risk_data['explainability']}")
                
        # Write processed frame to output video
        out.write(frame)
        
        # Display the frame (optional, for local execution)
        # cv2.imshow('RoadGuardian Analysis', frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
            
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Processing complete. Output saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RoadGuardian: Predictive Detection of Underage and Rash Driving")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--output", type=str, default="output.mp4", help="Path to save output video")
    
    args = parser.parse_args()
    main(args.video, args.output)
