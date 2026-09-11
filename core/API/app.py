"""
core/API/app.py
Production FastAPI backend for NIRMITI Early Warning System.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from core.spatial.grid import get_grid_cells
from core.Prediction.predictor import predictor
from core.API.apiHand.open_meteo import get_weather_data
from core.features.feature_pipeline import extract_hydrological_features

app = FastAPI(
    title="NIRMITI Flash Flood Early-Warning API",
    description="Operational Flash Flood Risk & Infrastructure Impact System for Hilly Regions",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def get_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "online", "docs": "/docs"}

@app.get("/health")
def healthcheck():
    return {"status": "healthy", "model_ready": predictor.ready}

@app.get("/api/v1/grid")
def get_grid():
    return {"cells": get_grid_cells()}

@app.post("/api/v1/simulate")
def simulate_scenario(scenario: str = "cloudburst"):
    cells = get_grid_cells()
    results = []
    total_exposed_pop = 0
    submerged_bridges = 0
    
    # CWC Gauge Level simulation
    if scenario == "cloudburst":
        river_level = 49.85  # Above Pandu Danger Level (49.68m)
        river_status = "ABOVE DANGER (CRITICAL)"
        lead_time_top = 2.5
    elif scenario == "moderate":
        river_level = 48.90  # Above Warning Level (48.68m)
        river_status = "WARNING TIER"
        lead_time_top = 5.0
    else:
        river_level = 45.20
        river_status = "NORMAL"
        lead_time_top = 12.0
    
    for cell in cells:
        is_epicenter = cell["cell_id"] in [21, 22, 23, 28, 29, 30]
        
        if scenario == "cloudburst" and is_epicenter:
            rain_24h, rain_1h, soil = 220.0, 78.0, 0.46
        elif scenario == "moderate":
            rain_24h, rain_1h, soil = 65.0, 15.0, 0.35
        else:
            rain_24h, rain_1h, soil = 12.0, 2.0, 0.22
            
        features = {
            "rain_1h": rain_1h, "rain_3h": rain_1h * 2.2, "rain_6h": rain_1h * 3.0,
            "rain_24h": rain_24h, "rain_72h": rain_24h + 20.0,
            "rain_intensity": rain_1h, "rain_acceleration": rain_1h * 0.4,
            "soil_moisture_surface": soil,
            "soil_saturation_index": min(1.0, soil / 0.48),
            "antecedent_rain_48h": 25.0,
            "elevation_m": cell["elevation_m"],
            "slope_deg": cell["slope_deg"]
        }
        
        pred = predictor.predict_cell(features)
        
        exposed_pop = int(cell["elevation_m"] * 42) if pred["risk_tier"] in ["HIGH", "CRITICAL"] else 0
        total_exposed_pop += exposed_pop
        if pred["risk_tier"] == "CRITICAL":
            submerged_bridges += cell["critical_infra"]
            
        results.append({
            **cell,
            **pred,
            "rainfall_24h": rain_24h,
            "exposed_population": exposed_pop
        })
        
    return {
        "scenario": scenario,
        "river_level_m": river_level,
        "river_status": river_status,
        "lead_time_top_hrs": lead_time_top,
        "total_exposed_population": total_exposed_pop,
        "submerged_bridges_count": submerged_bridges,
        "cells": results
    }
