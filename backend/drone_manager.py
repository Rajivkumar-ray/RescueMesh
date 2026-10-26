import math
from threading import Lock


# --------------------------------------------------
# DRONE DATA
# --------------------------------------------------

MIN_BATTERY = 30

drones = [
    {
        "drone_id": "D1",
        "latitude": 23.2650,
        "longitude": 77.4050,
        "battery": 85,
        "status": "available",
    },
    {
        "drone_id": "D2",
        "latitude": 23.2500,
        "longitude": 77.4200,
        "battery": 65,
        "status": "available",
    },
    {
        "drone_id": "D3",
        "latitude": 23.2800,
        "longitude": 77.3900,
        "battery": 25,
        "status": "low_battery",
    },
]

drone_lock = Lock()


# --------------------------------------------------
# DISTANCE CALCULATION
# --------------------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate approximate GPS distance in kilometres."""

    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    # Protect against floating-point rounding errors.
    a = max(0.0, min(1.0, a))

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return earth_radius * c


# --------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------

def _find_drone(drone_id):
    """Find a drone. Call while holding drone_lock."""

    for drone in drones:
        if drone["drone_id"] == drone_id:
            return drone

    return None


def _refresh_available_status(drone):
    """Update low-battery status without changing an active assignment."""

    if drone["status"] == "assigned":
        return

    if drone["battery"] < MIN_BATTERY:
        drone["status"] = "low_battery"
    else:
        drone["status"] = "available"


# --------------------------------------------------
# GET DRONES
# --------------------------------------------------

def get_all_drones():
    """Return a copy of all drone records."""

    with drone_lock:
        return [drone.copy() for drone in drones]


def get_available_drones():
    """Return available drones with sufficient battery."""

    with drone_lock:
        return [
            drone.copy()
            for drone in drones
            if drone["status"] == "available"
            and drone["battery"] >= MIN_BATTERY
        ]


def get_drone_by_id(drone_id):
    """Return a copy of a drone by ID, or None."""

    with drone_lock:
        drone = _find_drone(drone_id)
        return drone.copy() if drone else None


# --------------------------------------------------
# DRONE RECOMMENDATION
# --------------------------------------------------

def recommend_drone(victim_latitude, victim_longitude):
    """
    Recommend the nearest available drone with at least 30% battery.

    This is a recommendation only. It does not initiate a real flight.
    """

    with drone_lock:
        candidates = [
            drone
            for drone in drones
            if drone["status"] == "available"
            and drone["battery"] >= MIN_BATTERY
        ]

        if not candidates:
            return {
                "success": False,
                "message": "No suitable drone is currently available.",
            }

        selected = min(
            candidates,
            key=lambda drone: calculate_distance(
                drone["latitude"],
                drone["longitude"],
                victim_latitude,
                victim_longitude,
            ),
        )

        distance = calculate_distance(
            selected["latitude"],
            selected["longitude"],
            victim_latitude,
            victim_longitude,
        )

        return {
            "success": True,
            "drone": selected.copy(),
            "distance_km": round(distance, 2),
            "requires_operator_approval": True,
        }


# --------------------------------------------------
# ASSIGN DRONE
# --------------------------------------------------

def assign_drone(drone_id):
    """Assign an available drone after operator approval is checked by the API."""

    with drone_lock:
        drone = _find_drone(drone_id)

        if drone is None:
            return {
                "success": False,
                "message": "Drone ID not found.",
            }

        if drone["status"] != "available":
            return {
                "success": False,
                "message": "Drone is not available.",
            }

        if drone["battery"] < MIN_BATTERY:
            drone["status"] = "low_battery"

            return {
                "success": False,
                "message": "Drone battery is too low.",
            }

        drone["status"] = "assigned"

        return {
            "success": True,
            "drone": drone.copy(),
            "message": "Drone assigned successfully.",
        }


# --------------------------------------------------
# UPDATE DRONE LOCATION
# --------------------------------------------------

def update_drone_location(drone_id, latitude, longitude):
    """Update simulated GPS coordinates."""

    if not -90 <= latitude <= 90:
        return {
            "success": False,
            "message": "Latitude must be between -90 and 90.",
        }

    if not -180 <= longitude <= 180:
        return {
            "success": False,
            "message": "Longitude must be between -180 and 180.",
        }

    with drone_lock:
        drone = _find_drone(drone_id)

        if drone is None:
            return {
                "success": False,
                "message": "Drone ID not found.",
            }

        drone["latitude"] = latitude
        drone["longitude"] = longitude

        return {
            "success": True,
            "drone": drone.copy(),
        }


# --------------------------------------------------
# UPDATE BATTERY
# --------------------------------------------------

def update_drone_battery(drone_id, battery):
    """Update battery percentage and refresh status where appropriate."""

    if (
        not isinstance(battery, (int, float))
        or isinstance(battery, bool)
    ):
        return {
            "success": False,
            "message": "Battery must be a number.",
        }

    if not math.isfinite(battery) or not 0 <= battery <= 100:
        return {
            "success": False,
            "message": "Battery must be between 0 and 100.",
        }

    with drone_lock:
        drone = _find_drone(drone_id)

        if drone is None:
            return {
                "success": False,
                "message": "Drone ID not found.",
            }

        drone["battery"] = battery

        _refresh_available_status(drone)

        return {
            "success": True,
            "drone": drone.copy(),
            "message": "Drone battery updated successfully.",
        }


# --------------------------------------------------
# RELEASE DRONE
# --------------------------------------------------

def release_drone(drone_id):
    """Release an assigned drone after a mission or simulation."""

    with drone_lock:
        drone = _find_drone(drone_id)

        if drone is None:
            return {
                "success": False,
                "message": "Drone ID not found.",
            }

        if drone["status"] != "assigned":
            return {
                "success": False,
                "message": "Only an assigned drone can be released.",
            }

        if drone["battery"] < MIN_BATTERY:
            drone["status"] = "low_battery"
        else:
            drone["status"] = "available"

        return {
            "success": True,
            "drone": drone.copy(),
            "message": "Drone released successfully.",
        }