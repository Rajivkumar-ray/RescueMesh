from drone_manager import recommend_drone


def recommend_rescue(victim):
    """
    Generate a demo rescue recommendation.
    This system supports human decision-making and does not
    independently dispatch a drone or rescue team.
    """

    # Read victim information
    victim_id = victim.get("victim_id", "Unknown")
    priority = str(victim.get("priority", "medium")).lower()

    latitude = victim.get("latitude")
    longitude = victim.get("longitude")

    # Validate GPS coordinates
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return {
            "success": False,
            "victim_id": victim_id,
            "message": "Valid victim latitude and longitude are required."
        }

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return {
            "success": False,
            "victim_id": victim_id,
            "message": "Victim GPS coordinates are out of range."
        }

    # Check road or access condition.
    # Supports both field names used by different versions of the backend.
    access_status = str(
        victim.get("road_status")
        or victim.get("speed_status")
        or "unknown"
    ).lower()

    # Recommend a drone
    drone_result = recommend_drone(latitude, longitude)

    if not drone_result["success"]:
        return {
            "success": True,
            "victim_id": victim_id,
            "priority": priority,
            "recommended_drone": None,
            "recommended_resource": "Human rescue team assessment",
            "reason": drone_result["message"],
            "requires_operator_approval": True
        }

    selected_drone = drone_result["drone"]

    # Generate recommendation based on priority and access conditions.
    if priority == "high":
        resource = "Nearest eligible drone and urgent human rescue assessment"
        reason = "Victim record is marked high priority."

    elif priority == "low":
        resource = "Drone assessment and planned rescue response"
        reason = "Victim record is marked low priority."

    else:
        resource = "Nearest eligible drone and human rescue assessment"
        reason = "Standard demo rescue recommendation."

    # If access is unsafe, recommend an alternative access assessment.
    if access_status in ["unsafe", "blocked", "water", "flooded"]:
        resource += "; assess boat or alternative-access rescue resources"
        reason += " Road/access status indicates a possible access issue."

    return {
        "success": True,
        "victim_id": victim_id,
        "priority": priority,
        "recommended_drone": selected_drone["drone_id"],
        "drone_distance_km": drone_result["distance_km"],
        "recommended_resource": resource,
        "reason": reason,
        "access_status": access_status,
        "requires_operator_approval": True
    }