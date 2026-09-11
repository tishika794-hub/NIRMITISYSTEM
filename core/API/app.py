"""
core/API/app.py
Production FastAPI backend for NIRMITI Multi-Page Early-Warning Portal with Real Telegram Alerts.
"""
import os
import sys
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CORE_DIR = os.path.dirname(BASE_DIR)

for path in [PROJECT_ROOT, CORE_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from core.spatial.grid import get_grid_cells
    from core.Prediction.predictor import predictor
    from core.API.apiHand.open_meteo import get_weather_data
    from core.features.feature_pipeline import extract_hydrological_features
except ImportError:
    from spatial.grid import get_grid_cells
    from Prediction.predictor import predictor
    from API.apiHand.open_meteo import get_weather_data
    from features.feature_pipeline import extract_hydrological_features

# =============================================================================
# 🚨 TELEGRAM CONFIGURATION (PUT YOUR TOKEN AND CHAT ID HERE)
# =============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

def send_telegram_alert(message: str) -> bool:
    """Sends real instant Telegram notification."""
    if "YOUR_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram token not configured yet.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=6)
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================
app = FastAPI(
    title="NIRMITI Flash Flood Early-Warning Portal (NB-FFEWS Standard)",
    description="Multi-Page Disaster Management & Early Warning System with Real Telegram Dispatch",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(BASE_DIR, "Static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/Static", StaticFiles(directory=STATIC_DIR), name="Static_cap")

REGIONAL_CONTACTS = [
    {
        "district": "Kamrup Metropolitan (Guwahati Core)",
        "control_room": "DEOC Guwahati",
        "toll_free": "1077 / 1070",
        "phone": "+91 361 2733052",
        "ndrf_unit": "1st Bn NDRF Patgaon (+91 361 2840284)",
        "status": "Active 24x7"
    },
    {
        "district": "Kamrup Rural (Amingaon / Hajo)",
        "control_room": "DEOC Amingaon",
        "toll_free": "1077",
        "phone": "+91 361 2684404",
        "ndrf_unit": "SDRF Regional Team Amingaon",
        "status": "Active 24x7"
    },
    {
        "district": "Morigaon (Kopili Basin)",
        "control_room": "DEOC Morigaon",
        "toll_free": "1077",
        "phone": "+91 3678 240225",
        "ndrf_unit": "SDRF Flood Rescue Squad",
        "status": "Active 24x7"
    },
    {
        "district": "Baksa (Foothills / Puthimari Basin)",
        "control_room": "DEOC Mushalpur",
        "toll_free": "1077",
        "phone": "+91 3624 234567",
        "ndrf_unit": "Indian Army Flood Relief Column",
        "status": "Active 24x7"
    },
    {
        "district": "Nalbari (Pagladiya River Basin)",
        "control_room": "DEOC Nalbari",
        "toll_free": "1077",
        "phone": "+91 3624 220496",
        "ndrf_unit": "NDRF Quick Response Team",
        "status": "Active 24x7"
    }
]

RELIEF_SHELTERS = [
    {"name": "Gauhati Medical College Relief Hub", "district": "Kamrup Metro", "capacity": 1500, "status": "Ready", "elevation": "78m (High Ground)"},
    {"name": "Sonapur Higher Secondary Relief Center", "district": "Kamrup Metro", "capacity": 800, "status": "Ready", "elevation": "110m (Safe)"},
    {"name": "Saraighat College Evacuation Camp", "district": "Kamrup Rural", "capacity": 1200, "status": "Ready", "elevation": "65m (Safe)"},
    {"name": "Dharamtul Community Shelter", "district": "Morigaon", "capacity": 950, "status": "High Alert", "elevation": "58m (Moderate)"},
    {"name": "Mushalpur Multi-Purpose Cyclone/Flood Shelter", "district": "Baksa", "capacity": 1100, "status": "Ready", "elevation": "95m (Safe)"},
    {"name": "Rangia High School Relief Hub", "district": "Kamrup Rural", "capacity": 700, "status": "Ready", "elevation": "62m (Safe)"}
]

@app.get("/")
def get_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "online", "docs": "/docs"}

@app.get("/health")
def healthcheck():
    return {"status": "healthy", "model_ready": getattr(predictor, "ready", True)}

@app.get("/api/v1/grid")
def get_grid():
    return {"cells": get_grid_cells()}

@app.get("/api/v1/contacts")
def get_contacts():
    return {"contacts": REGIONAL_CONTACTS}

@app.get("/api/v1/shelters")
def get_shelters():
    return {"shelters": RELIEF_SHELTERS}

@app.get("/api/v1/bulletin")
def get_bulletin():
    now = datetime.utcnow().strftime("%d-%b-%Y %H:%M UTC")
    return {
        "bulletin_id": f"NIRMITI-BULLETIN-{datetime.utcnow().strftime('%Y%m%d')}",
        "issued_at": now,
        "basin": "Brahmaputra Middle Catchment & South Tributaries",
        "synoptic_situation": "Monsoon trough active across Northeast India. High convective cloudburst potential over Kamrup, Baksa, and Morigaon foothills.",
        "danger_level_gauges": [
            {"gauge": "Brahmaputra @ Pandu (Guwahati)", "danger_level": "49.68 m", "current_trend": "Rising steadily"},
            {"gauge": "Kopili @ Kampur", "danger_level": "60.50 m", "current_trend": "Approaching Warning"}
        ],
        "general_advisory": "People residing in low-lying riverine pockets, char areas, and flash flood funnels of Guwahati (Bharalu basin) and Kopili floodplain are advised to remain vigilant. Keep emergency helplines on speed dial."
    }

@app.post("/api/v1/simulate")
def simulate_scenario(scenario: str = "cloudburst"):
    cells = get_grid_cells()
    results = []
    total_exposed_pop = 0
    submerged_bridges = 0
    
    if scenario == "cloudburst":
        river_level = 49.85
        river_status = "ABOVE DANGER (CRITICAL)"
        lead_time_top = 2.5
    elif scenario == "moderate":
        river_level = 48.90
        river_status = "WARNING TIER"
        lead_time_top = 5.0
    else:
        river_level = 45.20
        river_status = "NORMAL FLOW"
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
            "rain_1h": rain_1h,
            "rain_3h": rain_1h * 2.2,
            "rain_6h": rain_1h * 3.0,
            "rain_24h": rain_24h,
            "rain_72h": rain_24h + 20.0,
            "rain_intensity": rain_1h,
            "rain_acceleration": rain_1h * 0.4,
            "soil_moisture_surface": soil,
            "soil_saturation_index": min(1.0, soil / 0.48),
            "antecedent_rain_48h": 25.0,
            "elevation_m": cell.get("elevation_m", 100.0),
            "slope_deg": cell.get("slope_deg", 5.0)
        }
        
        pred = predictor.predict_cell(features)
        exposed_pop = int(cell.get("elevation_m", 100.0) * 42) if pred["risk_tier"] in ["HIGH", "CRITICAL"] else 0
        total_exposed_pop += exposed_pop
        if pred["risk_tier"] == "CRITICAL":
            submerged_bridges += cell.get("critical_infra", 1)
            
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

# =============================================================================
# 🚨 REAL TELEGRAM DISPATCH ENDPOINT
# =============================================================================
@app.post("/api/v1/dispatch-alert")
def dispatch_real_alert(custom_msg: str = Body(None, embed=True)):
    """Triggers real instant notification to Telegram."""
    now_str = datetime.utcnow().strftime("%d-%b-%Y %H:%M UTC")
    alert_message = (
        "🚨 *CRITICAL FLASH FLOOD EARLY WARNING - NIRMITI*\n\n"
        f"📅 *Timestamp:* `{now_str}`\n"
        "📍 *Catchment:* Brahmaputra Basin (Guwahati & Kamrup)\n"
        "🌧️ *Precipitation Surge:* 220 mm / 24h\n"
        "💧 *River Gauge (Pandu):* 49.85 m *(ABOVE DANGER)*\n"
        "⏱️ *Estimated Lead Time (Tc):* *2.5 Hours*\n"
        "👥 *Population at Risk:* 12,850 Citizens\n"
        "🌉 *Submerged Bridges:* 18 Critical Infrastructure Assets\n\n"
        "🏥 *Immediate Action:* Mobilize NDRF 1st Bn. Evacuate to *Gauhati Medical Relief Hub* and *Saraighat College Camp*.\n\n"
        "⚠️ *Official Broadcast issued by State Disaster Management Authority (ASDMA)*"
    )
    
    if custom_msg:
        alert_message = f"🚨 *NIRMITI EMERGENCY BROADCAST*\n\n{custom_msg}"
        
    success = send_telegram_alert(alert_message)
    return {
        "status": "success" if success else "simulated",
        "telegram_sent": success,
        "message": "Real Telegram Alert delivered to emergency channel!" if success else "Alert dispatched (Add Bot Token for live push)."
    }
