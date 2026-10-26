"use strict";

// =====================================================
// 1. CONFIGURATION
// =====================================================

const API_BASE_URL = "http://127.0.0.1:8000";
const REFRESH_INTERVAL = 5000;

const map = L.map("map").setView(
    [23.2599, 77.4126],
    13
);

L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
        attribution:
            "Sources: Esri, HERE, Garmin, USGS, and the GIS User Community",
        maxZoom: 19
    }
).addTo(map);


// =====================================================
// 2. MARKER STORAGE
// =====================================================

const droneMarkers = new Map();
const victimMarkers = new Map();
const emergencyMarkers = new Map();

let refreshInProgress = false;
let movementInProgress = false;


// Rescue team demo marker
L.marker([23.2500, 77.4100])
    .addTo(map)
    .bindPopup(
        "<b>Rescue Team R1</b><br>Status: Available"
    );


// Drone-to-victim route
const routeLine = L.polyline([], {
    color: "blue",
    weight: 4,
    dashArray: "8, 8"
}).addTo(map);


// =====================================================
// 3. UTILITY FUNCTIONS
// =====================================================

function showMessage(message) {
    const element = document.getElementById("message");

    if (element) {
        element.textContent = message;
    }
}

function showMovementMessage(message) {
    const element = document.getElementById(
        "droneMovementMessage"
    );

    if (element) {
        element.textContent = message;
    }
}

function validCoordinates(latitude, longitude) {
    const lat = Number(latitude);
    const lon = Number(longitude);

    return (
        Number.isFinite(lat) &&
        Number.isFinite(lon) &&
        lat >= -90 &&
        lat <= 90 &&
        lon >= -180 &&
        lon <= 180
    );
}

function escapeHTML(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function apiRequest(path, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${path}`,
        {
            ...options,
            headers: {
                ...(options.body
                    ? { "Content-Type": "application/json" }
                    : {}),
                ...options.headers
            }
        }
    );

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
        const detail = result.detail || result.error;

        throw new Error(
            typeof detail === "string"
                ? detail
                : JSON.stringify(detail || `HTTP ${response.status}`)
        );
    }

    return result;
}


// =====================================================
// 4. DRONE MANAGEMENT
// =====================================================

async function fetchDrones() {
    const drones = await apiRequest("/drones");

    if (!Array.isArray(drones)) {
        throw new Error("Invalid drone data received.");
    }

    updateDroneMarkers(drones);
    updateDroneDetails(drones);
    updateRouteLine(drones);

    return drones;
}

function updateDroneMarkers(drones) {
    const currentIds = new Set();

    drones.forEach(drone => {
        const id = String(drone.drone_id ?? "");

        if (!id) return;

        if (
            !validCoordinates(
                drone.latitude,
                drone.longitude
            )
        ) {
            console.warn(
                "Invalid coordinates for drone:",
                id
            );
            return;
        }

        currentIds.add(id);

        const position = [
            Number(drone.latitude),
            Number(drone.longitude)
        ];

        let marker = droneMarkers.get(id);

        if (!marker) {
            marker = L.marker(position).addTo(map);
            droneMarkers.set(id, marker);
        } else {
            marker.setLatLng(position);
        }

        marker.bindPopup(
            `<b>Drone ${escapeHTML(id)}</b><br>` +
            `Battery: ${escapeHTML(drone.battery)}%<br>` +
            `Status: ${escapeHTML(drone.status)}<br>` +
            `Latitude: ${position[0].toFixed(5)}<br>` +
            `Longitude: ${position[1].toFixed(5)}`
        );
    });

    // Remove markers for drones no longer returned by backend
    for (const [id, marker] of droneMarkers.entries()) {
        if (!currentIds.has(id)) {
            map.removeLayer(marker);
            droneMarkers.delete(id);
        }
    }
}

function updateDroneDetails(drones) {
    if (!drones.length) return;

    const drone =
        drones.find(item => item.drone_id === "D1") ||
        drones[0];

    const idElement = document.getElementById("droneId");
    const batteryElement = document.getElementById("battery");
    const statusElement = document.getElementById("droneStatus");
    const latElement = document.getElementById("droneLatitude");
    const lonElement = document.getElementById("droneLongitude");

    if (idElement) {
        idElement.textContent = drone.drone_id;
    }

    if (batteryElement) {
        batteryElement.textContent = `${drone.battery}%`;
    }

    if (statusElement) {
        statusElement.textContent = drone.status;
    }

    if (latElement) {
        latElement.textContent =
            Number(drone.latitude).toFixed(5);
    }

    if (lonElement) {
        lonElement.textContent =
            Number(drone.longitude).toFixed(5);
    }
}


// =====================================================
// 5. VICTIM MANAGEMENT
// =====================================================

async function fetchVictims() {
    const victims = await apiRequest("/victims");

    if (!Array.isArray(victims)) {
        throw new Error("Invalid victim data received.");
    }

    updateVictimMarkers(victims);
    updateVictimDetails(victims);

    return victims;
}

function updateVictimMarkers(victims) {
    const currentIds = new Set();

    victims.forEach(victim => {
        const id = String(victim.victim_id ?? "");

        if (!id) return;

        if (
            !validCoordinates(
                victim.latitude,
                victim.longitude
            )
        ) {
            return;
        }

        currentIds.add(id);

        const position = [
            Number(victim.latitude),
            Number(victim.longitude)
        ];

        let marker = victimMarkers.get(id);

        if (!marker) {
            marker = L.marker(position).addTo(map);
            victimMarkers.set(id, marker);
        } else {
            marker.setLatLng(position);
        }

        marker.bindPopup(
            `<b>Victim ${escapeHTML(id)}</b><br>` +
            `Priority: ${escapeHTML(victim.priority)}<br>` +
            `Confidence: ${escapeHTML(victim.confidence)}<br>` +
            `Road status: ${escapeHTML(
                victim.road_status ?? victim.speed_status ?? "Unknown"
            )}`
        );
    });

    // Remove stale victim markers
    for (const [id, marker] of victimMarkers.entries()) {
        if (!currentIds.has(id)) {
            map.removeLayer(marker);
            victimMarkers.delete(id);
        }
    }
}

function updateVictimDetails(victims) {
    const panel = document.getElementById("victimDetails");

    if (!panel) return;

    if (!victims.length) {
        panel.innerHTML = `
            <h3>🆘 Victim Details</h3>
            <p>No victims detected yet.</p>
        `;
        return;
    }

    const victim = victims[victims.length - 1];

    panel.innerHTML = `
        <h3>🆘 Victim Details</h3>
        <p>Victim ID: ${escapeHTML(victim.victim_id)}</p>
        <p>Priority: ${escapeHTML(victim.priority)}</p>
        <p>Road Status: ${escapeHTML(
            victim.road_status ?? victim.speed_status ?? "Unknown"
        )}</p>
        <p>Confidence: ${escapeHTML(victim.confidence)}</p>
    `;
}


// =====================================================
// 6. EMERGENCY MANAGEMENT
// =====================================================

async function fetchEmergencies() {
    const emergencies = await apiRequest("/emergencies");

    if (!Array.isArray(emergencies)) {
        throw new Error("Invalid emergency data received.");
    }

    updateEmergencyMarkers(emergencies);

    return emergencies;
}

function updateEmergencyMarkers(emergencies) {
    const currentIds = new Set();

    emergencies.forEach(emergency => {
        const id = String(emergency.emergency_id ?? "");

        if (!id) return;

        if (
            !validCoordinates(
                emergency.latitude,
                emergency.longitude
            )
        ) {
            return;
        }

        currentIds.add(id);

        const position = [
            Number(emergency.latitude),
            Number(emergency.longitude)
        ];

        let marker = emergencyMarkers.get(id);

        if (!marker) {
            marker = L.marker(position).addTo(map);
            emergencyMarkers.set(id, marker);
        } else {
            marker.setLatLng(position);
        }

        marker.bindPopup(
            `<b>Emergency ${escapeHTML(id)}</b><br>` +
            `Type: ${escapeHTML(emergency.type)}<br>` +
            `Status: ${escapeHTML(emergency.status)}`
        );
    });

    // Remove emergencies no longer returned by backend
    for (const [id, marker] of emergencyMarkers.entries()) {
        if (!currentIds.has(id)) {
            map.removeLayer(marker);
            emergencyMarkers.delete(id);
        }
    }
}


// =====================================================
// 7. REGISTER EMERGENCY BUTTON
// =====================================================

const emergencyButton =
    document.getElementById("emergencyBtn");

if (emergencyButton) {
    emergencyButton.addEventListener("click", async () => {
        emergencyButton.disabled = true;
        showMessage("Registering emergency...");

        try {
            const result = await apiRequest("/emergency", {
                method: "POST",
                body: JSON.stringify({
                    type: "flood",
                    latitude: 23.2599,
                    longitude: 77.4126
                })
            });

            const emergency = result.emergency;

            if (!emergency) {
                throw new Error(
                    "Backend did not return emergency details."
                );
            }

            showMessage(
                `Emergency registered: ${emergency.emergency_id}`
            );

            await fetchEmergencies();

        } catch (error) {
            console.error(
                "Emergency registration error:",
                error
            );

            showMessage(
                `Emergency registration failed: ${error.message}`
            );
        } finally {
            emergencyButton.disabled = false;
        }
    });
}


// =====================================================
// 8. BACKEND-INTEGRATED DRONE MOVEMENT
// =====================================================

const droneButton = document.getElementById("droneBtn");

if (droneButton) {
    droneButton.addEventListener("click", async () => {
        if (movementInProgress) return;

        movementInProgress = true;
        droneButton.disabled = true;

        showMovementMessage("Starting drone simulation...");

        try {
            // Request the backend to simulate movement.
            // This is a simulation, not real drone control.
            const result = await apiRequest("/simulate-drone", {
                method: "POST",
                body: JSON.stringify({
                    drone_id: "D1",
                    target_latitude: 23.2600,
                    target_longitude: 77.4100,
                    approved: true,
                    steps: 5
                })
            });

            if (result.success !== true) {
                throw new Error(
                    "Drone simulation was not successful."
                );
            }

            // Fetch updated location and battery from backend.
            await fetchDrones();

            showMovementMessage(
                `Drone ${result.drone_id} mission: ` +
                `${result.mission_status}. ` +
                "Backend data refreshed."
            );

            console.log(
                "Drone simulation result:",
                result
            );

        } catch (error) {
            console.error(
                "Drone movement error:",
                error
            );

            showMovementMessage(
                `Drone movement failed: ${error.message}`
            );

        } finally {
            movementInProgress = false;
            droneButton.disabled = false;
        }
    });
}


// =====================================================
// 9. ROUTE LINE UPDATE
// =====================================================

function updateRouteLine(drones) {
    const drone =
        drones.find(item => item.drone_id === "D1");

    const victimMarker =
        victimMarkers.values().next().value;

    if (!drone || !victimMarker) {
        routeLine.setLatLngs([]);
        return;
    }

    if (
        !validCoordinates(
            drone.latitude,
            drone.longitude
        )
    ) {
        routeLine.setLatLngs([]);
        return;
    }

    routeLine.setLatLngs([
        [
            Number(drone.latitude),
            Number(drone.longitude)
        ],
        victimMarker.getLatLng()
    ]);
}


// =====================================================
// 10. REFRESH DASHBOARD
// =====================================================

async function refreshDashboard() {
    if (refreshInProgress) return;

    refreshInProgress = true;

    try {
        const results = await Promise.allSettled([
            fetchDrones(),
            fetchVictims(),
            fetchEmergencies()
        ]);

        results.forEach((result, index) => {
            if (result.status === "rejected") {
                const sections = [
                    "Drone",
                    "Victim",
                    "Emergency"
                ];

                console.error(
                    `${sections[index]} refresh failed:`,
                    result.reason
                );
            }
        });

    } finally {
        refreshInProgress = false;
    }
}


// =====================================================
// 11. START DASHBOARD
// =====================================================

async function startDashboard() {
    await refreshDashboard();

    // Automatically refresh backend data every five seconds.
    setInterval(refreshDashboard, REFRESH_INTERVAL);
}

startDashboard();