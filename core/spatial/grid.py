"""
core/spatial/grid.py
Defines the 49-cell GIS grid with real-world coordinates and terrain properties.
"""
from typing import Dict, List, Any

# Top-Left Anchor Coordinate: Real Assam Brahmaputra River Catchment
BASE_LAT = 26.50
BASE_LON = 91.40
GRID_SIZE = 7          # 7x7 = 49 cells
CELL_DEGREE = 0.09     # ~10 km per grid cell

REAL_LOCATIONS = [
    {"name": "Pandu River Port", "type": "Port / Gauge Station", "critical_infra": 2, "shelters": 2},
    {"name": "Dispur Core", "type": "Capital Admin Core", "critical_infra": 3, "shelters": 3},
    {"name": "Sonapur Foothills", "type": "Hilly Village", "critical_infra": 1, "shelters": 1},
    {"name": "Saraighat North", "type": "Bridge Transit Hub", "critical_infra": 2, "shelters": 1},
    {"name": "Bhattwari Village", "type": "Agricultural Plain", "critical_infra": 1, "shelters": 2},
    {"name": "Devgaon Catchment", "type": "Drainage Funnel", "critical_infra": 2, "shelters": 1},
    {"name": "Sari Village", "type": "Riverine Settlement", "critical_infra": 1, "shelters": 1},
    {"name": "Jangal Gaon", "type": "Hilly Hamlet", "critical_infra": 0, "shelters": 1},
    {"name": "Kotreth Lowlands", "type": "Inundation Floodplain", "critical_infra": 2, "shelters": 2}
]

def get_grid_cells() -> List[Dict[str, Any]]:
    cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cell_id = row * GRID_SIZE + col
            lat = BASE_LAT - (row * CELL_DEGREE)
            lon = BASE_LON + (col * CELL_DEGREE)
            
            # Elevation profile: 50m near river plain to 350m in Meghalaya foothills
            elevation = 50.0 + (row * 38.0) + (col * 8.0)
            slope = 2.0 + (row * 2.2) + (col * 0.8)
            
            loc_info = REAL_LOCATIONS[cell_id % len(REAL_LOCATIONS)]
            
            cells.append({
                "cell_id": cell_id,
                "row": row,
                "col": col,
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "elevation_m": round(elevation, 1),
                "slope_deg": round(slope, 1),
                "name": f"{loc_info['name']} (#{cell_id:02d})",
                "location_type": loc_info["type"],
                "critical_infra": loc_info["critical_infra"],
                "shelters": loc_info["shelters"]
            })
    return cells

