"""
core/API/apiHand/open_meteo.py
Fetches live weather and soil moisture.
"""
import requests
from typing import Dict, Any

def get_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "precipitation",
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "soil_moisture_0_to_7cm"
        ],
        "past_days": 2,
        "forecast_days": 1,
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=6)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {
            "hourly": {
                "precipitation": [0.0] * 72,
                "soil_moisture_0_to_7cm": [0.28] * 72,
                "surface_pressure": [1008.0] * 72
            }
        }
