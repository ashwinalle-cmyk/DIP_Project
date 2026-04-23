class RiskScorer:
    def __init__(self):
        # Weights for risk factors
        self.weights = {
            "speed": 0.4,
            "motion": 0.3,
            "age": 0.3
        }

    def calculate_risk(self, motion_data, driver_data):
        """
        Calculate risk score (0-100).
        """
        speed_score = min(100, motion_data["speed"] * 2) # Normalize speed to 0-100
        motion_score = 100 if motion_data["is_rash"] else 0
        age_score = 100 if driver_data and driver_data["is_minor"] else 0
        
        # Final risk score calculation
        risk_score = (speed_score * self.weights["speed"] + 
                      motion_score * self.weights["motion"] + 
                      age_score * self.weights["age"])
        
        # Categorize risk
        category = "Safe"
        if risk_score > 70:
            category = "High Risk"
        elif risk_score > 40:
            category = "Moderate Risk"
            
        return {
            "score": round(risk_score, 2),
            "category": category,
            "speed_kmh": motion_data.get("speed_kmh", 0),
            "license_plate": driver_data.get("license_plate") if driver_data else None,
            "explainability": self.generate_explanation(motion_data, driver_data, risk_score)
        }

    def generate_explanation(self, motion_data, driver_data, risk_score):
        """
        Generate explainable output for the risk score.
        """
        explanations = []
        if motion_data["is_rash"]:
            explanations.append(f"Rash driving detected: {motion_data['reason']}")
        if driver_data and driver_data["is_minor"]:
            explanations.append(f"Potential underage driver detected (Estimated age: {driver_data['age']})")
        if motion_data.get("speed_kmh", 0) > 80:
            explanations.append(f"High speed detected: {motion_data['speed_kmh']} km/h")
            
        if not explanations:
            return "Vehicle behavior is within safe limits."
            
        return " | ".join(explanations)
