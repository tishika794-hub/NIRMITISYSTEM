const map = L.map('map').setView([26.25, 91.75], 10);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 18
}).addTo(map);

let cellLayers = [];

function getTierColor(tier) {
    switch (tier) {
        case "CRITICAL": return "#ef4444";
        case "HIGH": return "#f97316";
        case "MODERATE": return "#eab308";
        default: return "#22c55e";
    }
}

async function runScenario(scenarioType) {
    try {
        const res = await fetch(`/api/v1/simulate?scenario=${scenarioType}`, { method: 'POST' });
        const data = await res.json();

        document.getElementById('m-river').innerText = `${data.river_level_m} m`;
        document.getElementById('m-lead').innerText = `${data.lead_time_top_hrs} hrs`;

        let highestProb = 0;
        let critCount = 0;
        data.cells.forEach(c => {
            if (c.flood_probability > highestProb) highestProb = c.flood_probability;
            if (c.risk_tier === "CRITICAL" || c.risk_tier === "HIGH") critCount++;
        });

        document.getElementById('m-prob').innerText = `${(highestProb * 100).toFixed(0)}%`;
        document.getElementById('m-danger').innerText = highestProb >= 0.8 ? "Critical" : highestProb >= 0.55 ? "High Alert" : "Moderate";

        document.getElementById('stat-pop').innerText = data.total_exposed_population.toLocaleString();
        document.getElementById('stat-villages').innerText = critCount;
        document.getElementById('stat-infra').innerText = `${data.submerged_bridges_count} Submerged`;

        cellLayers.forEach(l => map.removeLayer(l));
        cellLayers = [];

        data.cells.forEach(cell => {
            const color = getTierColor(cell.risk_tier);
            const radius = 4500;

            const circle = L.circle([cell.lat, cell.lon], {
                color: color,
                fillColor: color,
                fillOpacity: cell.risk_tier === "CRITICAL" ? 0.65 : cell.risk_tier === "HIGH" ? 0.45 : 0.25,
                weight: 1.5,
                radius: radius
            }).addTo(map);

            circle.bindPopup(`
                <div style="color: #0f172a; font-family: sans-serif; font-size: 13px;">
                    <strong style="font-size: 14px;">${cell.name}</strong><hr style="margin: 4px 0;"/>
                    <b>Type:</b> ${cell.location_type}<br/>
                    <b>Risk Level:</b> <span style="color:${color}; font-weight:bold;">${cell.risk_tier}</span> (${(cell.flood_probability * 100).toFixed(1)}%)<br/>
                    <b>24h Rainfall:</b> ${cell.rainfall_24h} mm<br/>
                    <b>Elevation:</b> ${cell.elevation_m} m | <b>Slope:</b> ${cell.slope_deg}°<br/>
                    <b>Est. Lead Time:</b> ${cell.estimated_lead_time_hrs} hrs<br/>
                    <b>Exposed Citizens:</b> ${cell.exposed_population}<br/>
                    <b>Open Shelters:</b> ${cell.shelters} Active
                </div>
            `);

            cellLayers.push(circle);
        });
    } catch (err) {
        console.error("Simulation error:", err);
    }
}

function dispatchAlerts() {
    alert("🚨 NIRMITI Emergency Advisory Broadcast Dispatched!\n\n• District Magistrate: Alerted via CAP Protocol\n• NDRF & SDRF: Mobilization coordinates shared\n• Local Villagers: 12,850 Geo-fenced SMS & WhatsApp alerts sent in Assamese/Hindi.");
}

runScenario('cloudburst');
