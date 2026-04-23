from deep_sort_realtime.deepsort_tracker import DeepSort

class VehicleTracker:
    def __init__(self, max_age=30, n_init=3):
        # Initialize DeepSORT tracker
        self.tracker = DeepSort(max_age=max_age, n_init=n_init)

    def update(self, detections, frame):
        """
        Update tracker with detections.
        Detections format: [[x1, y1, x2, y2, confidence, class_id], ...]
        Returns: List of tracked objects [track_id, x1, y1, x2, y2, class_id]
        """
        # Format for DeepSORT: ([x1, y1, w, h], confidence, class_id)
        formatted_detections = []
        for d in detections:
            x1, y1, x2, y2, conf, cls_id = d
            w, h = x2 - x1, y2 - y1
            formatted_detections.append(([x1, y1, w, h], conf, cls_id))
            
        tracks = self.tracker.update_tracks(formatted_detections, frame=frame)
        
        tracked_objects = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            ltrb = track.to_ltrb() # Left, Top, Right, Bottom
            class_id = track.get_det_class()
            tracked_objects.append([track_id, ltrb[0], ltrb[1], ltrb[2], ltrb[3], class_id])
            
        return tracked_objects
