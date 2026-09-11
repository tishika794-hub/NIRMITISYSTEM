"""
core/prediction/predictor.py
Inference engine for real-time flood probability and impact analytics.
"""
import os
import numpy as np
from xgboost import XGBClassifier

FEATURE_NAMES = [
    "rain_1h", "rain_3h", "rain_6h", "rain_24h", "rain_72h",
    "rain_intensity", "rain_acceleration", "soil_moisture_surface",
    "soil_saturation_index", "antecedent_rain_48h", "elevation_m", "slope_deg"
]

class FlashFloodPredictor:
    def __init__(self):
        self.model = XGBClassifier()
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "xgboost_flood_model.json")
        if os.path.exists(model_path):
            self.model.load_model(model_path)
            self.ready = True
        else:
            self.ready = False

    def predict_cell(self, features: dict) -> dict:
        if not self.ready:
            prob = min(1.0, (features.get("rain_24h", 0) / 180.0) * features.get("soil_saturation_index", 0.5))
        else:
            vector = np.array([[features[k] for k in FEATURE_NAMES]])
            prob = float(self.model.predict_proba(vector)[0][1])
        
        # Kirpich formula lead-time estimation based on slope
        slope = max(1.0, features.get("slope_deg", 5.0))
        tc = max(1.5, min(8.0, 5.5 * (slope ** -0.38)))
        
        if prob >= 0.80:
            tier = "CRITICAL"
            lead_time = round(tc * 0.6, 1)  # Fast crest in steep terrain (~2.0 - 2.5 hrs)
        elif prob >= 0.55:
            tier = "HIGH"
            lead_time = round(tc * 0.9, 1)
        elif prob >= 0.25:
            tier = "MODERATE"
            lead_time = round(tc * 1.5, 1)
        else:
            tier = "LOW"
            lead_time = 12.0
            
        return {
            "flood_probability": round(prob, 3),
            "risk_tier": tier,
            "estimated_lead_time_hrs": lead_time,
            "requires_evacuation": prob >= 0.65
        }

predictor = FlashFloodPredictor()
