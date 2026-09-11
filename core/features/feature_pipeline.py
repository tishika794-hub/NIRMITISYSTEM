"""
core/features/feature_pipeline.py
Hydrological feature extraction for physical flood modeling.
"""
from typing import Dict, Any

def extract_hydrological_features(hourly_data: Dict[str, Any], cell_info: Dict[str, Any]) -> Dict[str, float]:
    precip = hourly_data.get("precipitation", [0.0] * 48)
    soil_surf = hourly_data.get("soil_moisture_0_to_7cm", [0.25] * 48)
    
    # Rainfall multi-window accumulation
    rain_1h = float(precip[-1]) if len(precip) >= 1 else 0.0
    rain_3h = float(sum(precip[-3:])) if len(precip) >= 3 else rain_1h
    rain_6h = float(sum(precip[-6:])) if len(precip) >= 6 else rain_3h
    rain_24h = float(sum(precip[-24:])) if len(precip) >= 24 else rain_6h
    rain_72h = float(sum(precip)) if len(precip) else rain_24h
    
    # Rain surge intensity and acceleration
    rain_intensity = rain_1h
    rain_acceleration = rain_1h - (rain_3h / 3.0)
    
    # Soil Saturation Index (0.0 to 1.0)
    current_soil = float(soil_surf[-1]) if len(soil_surf) >= 1 else 0.25
    soil_saturation_index = min(1.0, max(0.0, current_soil / 0.48))
    
    # Antecedent Precipitation (Past 48h excluding last 6h)
    antecedent_rain_48h = max(0.0, rain_72h - rain_6h)
    
    return {
        "rain_1h": round(rain_1h, 2),
        "rain_3h": round(rain_3h, 2),
        "rain_6h": round(rain_6h, 2),
        "rain_24h": round(rain_24h, 2),
        "rain_72h": round(rain_72h, 2),
        "rain_intensity": round(rain_intensity, 2),
        "rain_acceleration": round(rain_acceleration, 2),
        "soil_moisture_surface": round(current_soil, 3),
        "soil_saturation_index": round(soil_saturation_index, 3),
        "antecedent_rain_48h": round(antecedent_rain_48h, 2),
        "elevation_m": cell_info.get("elevation_m", 100.0),
        "slope_deg": cell_info.get("slope_deg", 5.0)
    }
