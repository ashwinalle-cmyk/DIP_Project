import numpy as np
import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roadguardian")

logger.info("🚀 RoadGuardian Python Engine Initializing...")

app = FastAPI()

# Enable CORS (CRITICAL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC Health Check (Fixes 401 error)
@app.get("/health")
async def health():
    print("📡 Health check endpoint hit")
    return {"status": "ok"}

# FAST Calibration (Only 4-point math)
@app.post("/calibrate")
async def calibrate(data: dict):
    print("📡 Calibration endpoint hit")
    import numpy as np
    import cv2

    try:
        pixel_points = np.array(data["pixel_points"], dtype=np.float32)
        world_points = np.array(data["world_points"], dtype=np.float32)

        H, _ = cv2.findHomography(pixel_points, world_points)

        return {
            "status": "success",
            "homography": H.tolist()
        }
    except Exception as e:
        logger.error(f"Calibration error: {str(e)}")
        return {"status": "error", "message": str(e)}

# Public Analysis Endpoint
@app.post("/analyze")
async def analyze(data: dict = None):
    print("📡 Analyze endpoint hit")
    # Mock analysis data for fallback
    return {
        "total_vehicles": 2,
        "vehicles": [
            {
                "id": "V-BACKEND-01",
                "type": "car",
                "model": "Sedan",
                "behavior": "safe",
                "speed_kmh": 65.0,
                "speed_range": [64.0, 66.0],
                "driver_age_estimate": 30,
                "age_confidence": 0.9,
                "license_plate": "BACKEND-01",
                "risk_score": 10,
                "category": "Low Risk",
                "violations": [],
                "explanation": "Processed by backend fallback engine.",
                "bounding_box": [100, 100, 200, 200],
                "centroid": [200, 200],
                "world_coordinates": [5.0, 10.0]
            }
        ],
        "overall_risk_summary": "Analysis performed via backend fallback."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
