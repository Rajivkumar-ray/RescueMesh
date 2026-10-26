import math
import time

from drone_manager import (
    get_drone_by_id,
    update_drone_location,
    update_drone_battery,
    release_drone
)


def simulate_drone_movement(
    drone_id,
    target_latitude,
    target_longitude,
    steps=10,
    delay=0.2
):
    """
    Simulate a drone moving towards a target GPS location.

    This is a software simulation only.
    It does not control real drone hardware.
    """

    drone = get_drone_by_id(drone_id)

    if drone is None:
        return {
            "success": False,
            "message": "Drone ID not found."
        }

    if drone["status"] != "assigned":
        return {
            "success": False,
            "message": "Assign the drone before starting its simulation."
        }

    if drone["battery"] < 30:
        return {
            "success": False,
            "message": "Drone battery is too low."
        }

    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
        return {
            "success": False,
            "message": "Steps must be a positive integer."
        }

    if not math.isfinite(target_latitude) or not math.isfinite(target_longitude):
        return {
            "success": False,
            "message": "Target coordinates must be finite numbers."
        }

    if not (-90 <= target_latitude <= 90):
        return {
            "success": False,
            "message": "Target latitude is out of range."
        }

    if not (-180 <= target_longitude <= 180):
        return {
            "success": False,
            "message": "Target longitude is out of range."
        }

    start_latitude = drone["latitude"]
    start_longitude = drone["longitude"]
    initial_battery = drone["battery"]

    route = []

    try:
        for step in range(1, steps + 1):
            progress = step / steps

            current_latitude = (
                start_latitude
                + (target_latitude - start_latitude) * progress
            )

            current_longitude = (
                start_longitude
                + (target_longitude - start_longitude) * progress
            )

            # Demo battery consumption.
            remaining_battery = max(
                0,
                initial_battery - (step * 0.5)
            )

            location_result = update_drone_location(
                drone_id,
                current_latitude,
                current_longitude
            )

            battery_result = update_drone_battery(
                drone_id,
                remaining_battery
            )

            if not location_result["success"] or not battery_result["success"]:
                return {
                    "success": False,
                    "message": "Could not update drone simulation state.",
                    "route": route
                }

            route.append({
                "step": step,
                "latitude": round(current_latitude, 6),
                "longitude": round(current_longitude, 6),
                "battery": remaining_battery
            })

            if step < steps:
                time.sleep(delay)

        return {
            "success": True,
            "drone_id": drone_id,
            "mission_status": "arrived_at_target",
            "final_location": {
                "latitude": target_latitude,
                "longitude": target_longitude
            },
            "route": route,
            "message": "Drone simulation completed."
        }

    finally:
        # Restore the drone to an appropriate service status.
        release_drone(drone_id)