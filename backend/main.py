from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import math

from drone_manager import (
    get_all_drones,
    recommend_drone,
    assign_drone,
    release_drone,
)

from rescue_engine import (
    recommend_rescue as generate_rescue_recommendation,
)

from drone_simulation import simulate_drone_movement


app = FastAPI(title="RescueMesh Backend")


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# TEMPORARY STORAGE
# --------------------------------------------------

emergencies = []
victims = []


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class Emergency(BaseModel):
    type: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class VictimDetection(BaseModel):
    victim_id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    confidence: float = Field(ge=0, le=1)
    priority: str = "pending"
    road_status: str = "unknown"


class DroneRecommendationRequest(BaseModel):
    victim_id: str


class DroneAssignmentRequest(BaseModel):
    drone_id: str
    approved: bool = False


class DroneSimulationRequest(BaseModel):
    drone_id: str
    target_latitude: float = Field(ge=-90, le=90)
    target_longitude: float = Field(ge=-180, le=180)
    approved: bool = False
    steps: int = Field(default=10, ge=1, le=100)


class DroneBatteryUpdate(BaseModel):
    battery: float = Field(ge=0, le=100)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "RescueMesh Backend is running!",
        "status": "online",
    }


# --------------------------------------------------
# EMERGENCY MANAGEMENT
# --------------------------------------------------

@app.post("/emergency")
def create_emergency(data: Emergency):

    emergency = {
        "emergency_id": f"E{len(emergencies) + 1}",
        "type": data.type,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "status": "active",
    }

    emergencies.append(emergency)

    return {
        "message": "Emergency registered successfully",
        "emergency": emergency,
    }


@app.get("/emergencies")
def get_emergencies():
    return emergencies


# --------------------------------------------------
# DRONE MANAGEMENT
# --------------------------------------------------

@app.get("/drones")
def get_drones():
    return get_all_drones()


@app.get("/drones/{drone_id}")
def get_drone(drone_id: str):

    drone = next(
        (
            item
            for item in get_all_drones()
            if item["drone_id"] == drone_id
        ),
        None,
    )

    if drone is None:
        raise HTTPException(
            status_code=404,
            detail="Drone not found",
        )

    return drone


@app.patch("/drones/{drone_id}/battery")
def update_battery(drone_id: str, data: DroneBatteryUpdate):

    from drone_manager import update_drone_battery

    result = update_drone_battery(
        drone_id,
        data.battery,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


# --------------------------------------------------
# AI VICTIM DETECTION
# --------------------------------------------------

@app.post("/detect-victim")
def detect_victim(data: VictimDetection):

    victim = data.model_dump()

    # Preserve existing victim records and avoid duplicate
    # records when the same victim ID is detected again.
    existing_index = next(
        (
            index
            for index, item in enumerate(victims)
            if item["victim_id"] == victim["victim_id"]
        ),
        None,
    )

    if existing_index is None:
        victims.append(victim)
        message = "Victim detection result received"
    else:
        victims[existing_index].update(victim)
        message = "Existing victim record updated"

    return {
        "message": message,
        "victim": victim,
    }


@app.get("/victims")
def get_victims():
    return victims


@app.get("/victims/{victim_id}")
def get_victim(victim_id: str):

    victim = next(
        (
            item
            for item in victims
            if item["victim_id"] == victim_id
        ),
        None,
    )

    if victim is None:
        raise HTTPException(
            status_code=404,
            detail="Victim not found",
        )

    return victim


# --------------------------------------------------
# DRONE RECOMMENDATION
# --------------------------------------------------

@app.post("/recommend-drone")
def recommend_drone_endpoint(
    data: DroneRecommendationRequest,
):

    victim = next(
        (
            item
            for item in victims
            if item["victim_id"] == data.victim_id
        ),
        None,
    )

    if victim is None:
        raise HTTPException(
            status_code=404,
            detail="Victim not found",
        )

    result = recommend_drone(
        victim["latitude"],
        victim["longitude"],
    )

    if not result["success"]:
        return result

    return {
        "success": True,
        "victim_id": data.victim_id,
        "recommended_drone": result["drone"],
        "distance_km": result["distance_km"],
        "requires_operator_approval": True,
    }


# --------------------------------------------------
# RESCUE DECISION ENGINE
# --------------------------------------------------

@app.post("/recommend-rescue")
def recommend_rescue(victim_id: str):

    victim = next(
        (
            item
            for item in victims
            if item["victim_id"] == victim_id
        ),
        None,
    )

    if victim is None:
        raise HTTPException(
            status_code=404,
            detail="Victim not found",
        )

    return generate_rescue_recommendation(victim)


# --------------------------------------------------
# DRONE ASSIGNMENT
# --------------------------------------------------

@app.post("/assign-drone")
def assign_drone_endpoint(
    data: DroneAssignmentRequest,
):

    if not data.approved:
        raise HTTPException(
            status_code=403,
            detail="Operator approval is required before assignment",
        )

    result = assign_drone(data.drone_id)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


# --------------------------------------------------
# DRONE MOVEMENT SIMULATION
# --------------------------------------------------

@app.post("/simulate-drone")
def simulate_drone_endpoint(
    data: DroneSimulationRequest,
):

    if not data.approved:
        raise HTTPException(
            status_code=403,
            detail="Operator approval is required before simulation",
        )

    result = simulate_drone_movement(
        drone_id=data.drone_id,
        target_latitude=data.target_latitude,
        target_longitude=data.target_longitude,
        steps=data.steps,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


# --------------------------------------------------
# RELEASE DRONE
# --------------------------------------------------

@app.post("/release-drone/{drone_id}")
def release_drone_endpoint(drone_id: str):

    result = release_drone(drone_id)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"],
        )

    return result