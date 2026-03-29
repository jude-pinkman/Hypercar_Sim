"""
F1 2026 Race API Router
FastAPI routes for F1 race simulation, predictions, and live tracking.

Endpoints:
  POST   /api/f1/start-race              Start a new F1 race
  GET    /api/f1/race/{race_id}/standings   Get current race standings
  WS     /api/f1/race/{race_id}/live     WebSocket for live race events
  GET    /api/f1/circuits                List all F1 2026 circuits
  GET    /api/f1/calendar                List 2026 season calendar (18 races)
  POST   /api/f1/predict-race            Predict next race winner
  POST   /api/f1/predict-championship    Predict championship winner
"""

from fastapi import APIRouter, HTTPException, WebSocket, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import threading
import uuid

from app.f1_data_2026 import (
    F1_DRIVERS_2026, F1_TEAMS_2026, F1_CIRCUITS_2026,
    get_championship_standings, create_f1_2026_grid,
    get_driver_by_id, get_team_by_name, get_circuit_by_id,
    SEASON_2026_CALENDAR
)
from app.circuit_race_simulator import RaceSimulator, Circuit, TrackSection, SectionType
from app.race_events import get_broadcaster, get_event_log
from app.ml.championship_predictor import ChampionshipPredictor
from app.circuit_coordinates import get_circuit_coordinates


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Driver(BaseModel):
    """Driver info for race request"""
    driver_id: str
    grid_position: int


class StartRaceRequest(BaseModel):
    """Request to start a new F1 race"""
    circuit_id: str
    drivers: Optional[List[Driver]] = None      # If None, use default grid
    weather: str = "dry"                        # dry, damp, wet
    race_speed_multiplier: float = 1.0          # 1.0-10.0
    simulation_timestep: float = 0.1


class RaceStandingsResponse(BaseModel):
    """Current race standings"""
    race_id: str
    circuit_name: str
    race_time: float
    positions: List[Dict]


class CircuitInfo(BaseModel):
    """Circuit information"""
    circuit_id: str
    name: str
    country: str
    lap_length_km: float
    corners: int
    drs_zones: int
    lap_record: str
    typical_laps: int
    coordinates: Optional[List[Dict]] = None  # Optional track coordinates for visualization


class PredictRaceRequest(BaseModel):
    """Request race winner prediction"""
    circuit_id: str
    drivers: Optional[List[str]] = None      # If None, use full F1 grid


class RaceWinnerPrediction(BaseModel):
    """Race winner prediction"""
    circuit_name: str
    predictions: List[Dict]  # [{driver, team, probability}, ...]
    confidence: float


class ChampionshipPredictionResponse(BaseModel):
    """Championship forecast"""
    champion_prediction: str
    top3: List[str]
    champion_probability: float
    drivers: List[Dict]


class CalendarRaceInfo(BaseModel):
    """Single race in season calendar"""
    round: int
    name: str
    circuit: str
    date: str


class SeasonCalendarResponse(BaseModel):
    """Season calendar data"""
    season: int
    total_races: int
    current_date: str
    races: List[CalendarRaceInfo]


# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/f1", tags=["F1 2026"])
_active_races: Dict[str, RaceSimulator] = {}
_championship_predictor = ChampionshipPredictor()


# ============================================================================
# CIRCUITS ENDPOINT
# ============================================================================

@router.get("/circuits", response_model=List[CircuitInfo], summary="Get all F1 2026 circuits")
async def get_circuits() -> List[CircuitInfo]:
    """
    Returns list of all F1 2026 circuits with metadata.
    """
    circuits = []
    for circuit in F1_CIRCUITS_2026:
        coordinates = get_circuit_coordinates(circuit.circuit_id)
        circuits.append(CircuitInfo(
            circuit_id=circuit.circuit_id,
            name=circuit.name,
            country=circuit.country,
            lap_length_km=circuit.lap_length_km,
            corners=circuit.corners,
            drs_zones=circuit.drs_zones,
            lap_record=circuit.lap_record,
            typical_laps=circuit.typical_race_laps,
            coordinates=coordinates,
        ))
    return circuits


@router.get("/circuits/{circuit_id}", response_model=CircuitInfo, summary="Get specific circuit")
async def get_circuit(circuit_id: str) -> CircuitInfo:
    """Get detailed info for a specific circuit"""
    circuit = get_circuit_by_id(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")

    coordinates = get_circuit_coordinates(circuit.circuit_id)

    return CircuitInfo(
        circuit_id=circuit.circuit_id,
        name=circuit.name,
        country=circuit.country,
        lap_length_km=circuit.lap_length_km,
        corners=circuit.corners,
        drs_zones=circuit.drs_zones,
        lap_record=circuit.lap_record,
        typical_laps=circuit.typical_race_laps,
        coordinates=coordinates,
    )


# ============================================================================
# SEASON CALENDAR ENDPOINT
# ============================================================================

@router.get("/calendar", response_model=SeasonCalendarResponse, summary="Get F1 2026 season calendar")
async def get_season_calendar() -> SeasonCalendarResponse:
    """
    Returns the complete F1 2026 season calendar with all 18 races.
    Includes race names, circuits, and scheduled dates.
    """
    races = [
        CalendarRaceInfo(
            round=race["round"],
            name=race["name"],
            circuit=race["circuit"],
            date=race["date"]
        )
        for race in SEASON_2026_CALENDAR
    ]
    
    return SeasonCalendarResponse(
        season=2026,
        total_races=len(SEASON_2026_CALENDAR),
        current_date="2026-03-06",  # Current date - now March 6 (Round 1 start date)
        races=races
    )


# ============================================================================
# RACE START ENDPOINT
# ============================================================================

def _run_race_background(simulator: RaceSimulator) -> None:
    """Run race simulation in background thread"""
    try:
        simulator.run_simulation(verbose=True, update_interval=10.0)
    except Exception as e:
        print(f"Race simulation error: {e}")


def _convert_f1_circuit_to_simulator(f1_circuit) -> Circuit:
    """
    Convert F1 circuit data to RaceSimulator circuit format.
    Creates a simplified circuit with generic sections based on track characteristics.
    """
    # Create basic track layout: alternating straights and corners
    sections = []
    lap_length_m = f1_circuit.lap_length_km * 1000
    
    # Estimate section distribution based on corners
    # Assume roughly even distribution of straights and corners
    num_corners = f1_circuit.corners
    num_straights = num_corners  # Roughly equal number of straights
    
    total_sections = num_corners + num_straights
    section_length = lap_length_m / total_sections if total_sections > 0 else lap_length_m
    
    position = 0.0
    is_corner = True  # Start with a corner
    drs_zone_count = 0
    max_drs = f1_circuit.drs_zones
    
    for i in range(total_sections):
        start_pos = position
        end_pos = position + section_length
        
        if is_corner:
            # Create a corner section
            corner_radius = 300 + (i % 200)  # Vary radius for realism
            sections.append(
                TrackSection(
                    section_type=SectionType.CORNER,
                    length=section_length,
                    start_position=start_pos,
                    end_position=end_pos,
                    corner_radius=corner_radius,
                    corner_angle=45 + (i % 45),
                )
            )
        else:
            # Create a straight section - some are DRS zones
            is_drs = drs_zone_count < max_drs
            if is_drs:
                drs_zone_count += 1
            
            sections.append(
                TrackSection(
                    section_type=SectionType.STRAIGHT,
                    length=section_length,
                    start_position=start_pos,
                    end_position=end_pos,
                    drs_zone=is_drs,
                )
            )
        
        position = end_pos
        is_corner = not is_corner  # Alternate between corners and straights
    
    # Calculate number of laps based on typical race duration
    # Estimate: 75 minutes typical F1 race
    lap_time_estimate = (1.5 + f1_circuit.lap_record_seconds / 100)  # Rough estimate in minutes
    estimated_laps = max(50, int(75 / lap_time_estimate))
    
    return Circuit(
        name=f1_circuit.name,
        lap_length_km=f1_circuit.lap_length_km,
        number_of_laps=estimated_laps,
        sections=sections,
    )


@router.post("/start-race", summary="Start a new F1 race")
async def start_race(
    request: StartRaceRequest,
    background_tasks: BackgroundTasks,
) -> Dict:
    """
    Start a new F1 race simulation with live WebSocket updates.
    
    Returns race_id for connecting to WebSocket updates at /api/f1/race/{race_id}/live
    """
    
    # Get circuit
    circuit_data = get_circuit_by_id(request.circuit_id)
    if not circuit_data:
        raise HTTPException(status_code=404, detail=f"Circuit {request.circuit_id} not found")
    
    # Convert F1 circuit data to RaceSimulator circuit format
    circuit = _convert_f1_circuit_to_simulator(circuit_data)
    
    # Create race simulator
    race_id = str(uuid.uuid4())
    simulator = RaceSimulator(
        circuit=circuit,
        timestep=request.simulation_timestep,
        enable_tyre_degradation=True,
        race_id=race_id,
        emit_events=True,
    )
    
    # Add grid
    if request.drivers:
        # Custom grid provided
        for driver_spec in request.drivers:
            driver = get_driver_by_id(driver_spec.driver_id)
            if not driver:
                continue
            team = get_team_by_name(driver.team)
            if not team:
                continue
            
            # Build car physics params from driver profile
            grid_spec = {
                "driver_name": driver.name,
                "team": driver.team,
                "max_speed": 90.0 +  (team.power * 8.0),
                "acceleration": 10.8 + (team.power * 2.0),
                "tyre_grip": 0.80 + (team.handling * 0.18),
                "drag_coefficient": 0.72 - (team.power * 0.08),
                "cornering_ability": 0.85 + (driver.racecraft * 0.15),
            }
            simulator.add_car(**grid_spec)
    else:
        # Use default full F1 2026 grid
        grid = create_f1_2026_grid()
        for car_spec in grid:
            simulator.add_car(**car_spec)
    
    # Store race reference
    _active_races[race_id] = simulator
    
    # Run in background
    background_tasks.add_task(_run_race_background, simulator)
    
    # Return race info
    return {
        "race_id": race_id,
        "circuit": circuit.name,
        "circuit_id": request.circuit_id,
        "total_laps": circuit.number_of_laps,
        "grid_size": len(simulator.cars),
        "websocket_url": f"/api/f1/race/{race_id}/live",
    }


# ============================================================================
# RACE STANDINGS ENDPOINT
# ============================================================================

@router.get("/race/{race_id}/standings", response_model=RaceStandingsResponse, summary="Get current race standings")
async def get_race_standings(race_id: str) -> RaceStandingsResponse:
    """Get current standings for an active or completed race"""
    
    if race_id not in _active_races:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found")
    
    simulator = _active_races[race_id]
    positions = simulator.get_race_positions()
    
    standings = []
    for pos, driver, team, lap, distance, speed_kmh in positions:
        standings.append({
            "position": pos,
            "driver": driver,
            "team": team,
            "lap": lap,
            "gap_to_leader": 0.0 if pos == 1 else (
                ((positions[0][4] - distance) % simulator.circuit.lap_length) / 1000
            ),
            "speed_kmh": round(speed_kmh, 1),
            "finished": False,  # Would track this properly in real implementation
        })
    
    return RaceStandingsResponse(
        race_id=race_id,
        circuit_name=simulator.circuit.name,
        race_time=simulator.race_time,
        positions=standings,
    )


# ============================================================================
# WEBSOCKET ENDPOINT (LIVE RACE EVENTS)
# ============================================================================

@router.websocket("/race/{race_id}/live")
async def websocket_race_live(websocket: WebSocket, race_id: str):
    """
    WebSocket endpoint for live race event streaming.
    
    Clients connect here to receive real-time updates:
    - Lap completions
    - Position changes
    - Pit stops
    - Weather changes
    - Race finished
    """
    
    await websocket.accept()
    
    if race_id not in _active_races:
        await websocket.send_json({
            "error": f"Race {race_id} not found",
        })
        await websocket.close()
        return
    
    # Define callback to send events to this WebSocket
    async def send_event(event):
        try:
            await websocket.send_json(event.to_dict())
        except Exception as e:
            print(f"WebSocket send error: {e}")
    
    # Subscribe to race events
    broadcaster = get_broadcaster()
    await broadcaster.subscribe(race_id, send_event)
    
    try:
        # Keep connection alive and receive any client messages
        while True:
            data = await websocket.receive_json()
            # Could handle client messages here (e.g., pause, speed control)
            if data.get("action") == "ping":
                await websocket.send_json({"action": "pong"})
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        await broadcaster.unsubscribe(race_id, send_event)
        await websocket.close()


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@router.post("/predict-race", response_model=RaceWinnerPrediction, summary="Predict race winner")
async def predict_race(request: PredictRaceRequest) -> RaceWinnerPrediction:
    """
    Predict the winner of an F1 race on a given circuit.
    
    Uses the trained ML model to estimate win probabilities for each driver.
    """
    
    circuit = get_circuit_by_id(request.circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {request.circuit_id} not found")
    
    # For now, return a simplified prediction based on driver ratings
    # In production, would use the trained ML model
    
    drivers_to_predict = []
    if request.drivers:
        for driver_id in request.drivers:
            driver = get_driver_by_id(driver_id)
            if driver:
                drivers_to_predict.append(driver)
    else:
        drivers_to_predict = F1_DRIVERS_2026
    
    # Calculate win probability for each driver
    predictions = []
    total_rating = 0.0
    
    ratings = {}
    for driver in drivers_to_predict:
        team = get_team_by_name(driver.team)
        if not team:
            continue
        
        # Combined rating: team performance + driver skill
        rating = (team.power * 0.6 + driver.speed * 0.4)
        ratings[driver.name] = rating
        total_rating += rating
    
    # Normalize to probabilities
    for driver_name, rating in ratings.items():
        driver = next((d for d in drivers_to_predict if d.name == driver_name), None)
        team = next((t for t in F1_TEAMS_2026 if t.name == driver.team), None) if driver else None
        
        prob = rating / total_rating if total_rating > 0 else 0
        predictions.append({
            "driver": driver_name,
            "team": driver.team if driver else "Unknown",
            "probability": round(prob, 4),
        })
    
    # Sort by probability
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    
    top_prob = predictions[0]["probability"] if predictions else 0
    
    return RaceWinnerPrediction(
        circuit_name=circuit.name,
        predictions=predictions[:10],  # Top 10
        confidence=round(top_prob, 3),
    )


@router.post("/predict-championship", response_model=ChampionshipPredictionResponse, 
             summary="Predict F1 championship winner")
async def predict_championship() -> ChampionshipPredictionResponse:
    """
    Predict the F1 2026 championship winner based on current standings.
    
    Takes into account:
    - Current championship points
    - Team & driver performance ratings
    - Remaining races in season
    """
    
    # Get current standings
    standings = get_championship_standings()
    
    # Prepare driver data for prediction
    drivers_data = []
    for driver in F1_DRIVERS_2026:
        team = get_team_by_name(driver.team)
        if not team:
            continue
        
        drivers_data.append({
            "name": driver.name,
            "team": driver.team,
            "current_points": standings.get(driver.driver_id, 0),
            "speed_rating": driver.speed,
            "consistency": driver.consistency,
        })
    
    # Generate forecast (14 races remaining from race 1)
    remaining_races = 17  # 18 total - 1 completed
    
    forecast = _championship_predictor.forecast_championship(
        drivers=drivers_data,
        teams=[
            {
                "name": t.name,
                "power": t.power,
                "reliability": t.reliability,
            }
            for t in F1_TEAMS_2026
        ],
        races_completed=1,
        remaining_races=remaining_races,
    )
    
    # Format response
    drivers_forecast = []
    for driver_forecast in forecast.drivers[:5]:  # Top 5
        drivers_forecast.append({
            "driver": driver_forecast.driver_name,
            "team": driver_forecast.team,
            "points": driver_forecast.current_points,
            "predicted_final": driver_forecast.predicted_final_points,
            "championship_probability": driver_forecast.win_probability,
        })
    
    return ChampionshipPredictionResponse(
        champion_prediction=forecast.champion_prediction,
        top3=forecast.top3_predictions,
        champion_probability=round(forecast.champion_probability, 4),
        drivers=drivers_forecast,
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", summary="Check API health")
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "active_races": len(_active_races),
    }


# ============================================================================
# F1 MANAGER ENGINE — NEW ENDPOINTS
# ============================================================================
# These endpoints expose the lap-by-lap F1 Manager style race engine.
# The engine is imported from app.f1_manager_engine.

from app.f1_manager_engine import F1ManagerEngine, RaceLapData

class ManagerRaceRequest(BaseModel):
    """Start a Manager-style lap-by-lap race"""
    circuit_id: str
    weather: str = "dry"        # dry | damp | wet
    speed_mult: float = 1.0
    driver_ids: Optional[List[str]] = None  # None = full grid


@router.post("/manager/start-race", summary="Start an F1 Manager lap-by-lap race")
async def manager_start_race(req: ManagerRaceRequest) -> Dict:
    """
    Simulate a complete Grand Prix lap-by-lap using the F1 Manager engine.
    Returns final classification + full lap telemetry history.

    Weather options: dry | damp | wet
    """
    try:
        engine  = F1ManagerEngine(
            circuit_id = req.circuit_id,
            weather    = req.weather,
            speed_mult = req.speed_mult,
            driver_ids = req.driver_ids,
        )
        results = engine.simulate_race()

        # Serialise lap history (condensed — last lap only for each driver)
        lap_history_out = []
        for lap_data in engine.lap_history:
            lap_history_out.append({
                "lap":        lap_data.lap,
                "sc_active":  lap_data.sc_active,
                "vsc_active": lap_data.vsc_active,
                "fastest_lap_driver": lap_data.fastest_lap_driver,
                "fastest_lap_time":   lap_data.fastest_lap_time,
                "drivers": [
                    {
                        "driver_id":       s.driver_id,
                        "driver_name":     s.driver_name,
                        "team":            s.team,
                        "number":          s.number,
                        "position":        s.position,
                        "lap_time":        s.lap_time,
                        "gap_to_leader":   s.gap_to_leader,
                        "compound":        s.compound,
                        "tyre_age":        s.tyre_age,
                        "tyre_deg":        s.tyre_deg,
                        "pit_this_lap":    s.pit_this_lap,
                        "pit_count":       s.pit_count,
                        "drs_active":      s.drs_active,
                        "dnf":             s.dnf,
                        "track_position":  s.track_position,
                        "sector1":         s.sector1,
                        "sector2":         s.sector2,
                        "sector3":         s.sector3,
                        "speed_kmh":       s.speed_kmh,
                        "tyre_wear_pct":   s.tyre_wear_pct,
                        "compounds_used":  s.compounds_used,
                        "pit_laps":        s.pit_laps,
                        "best_lap_time":   s.best_lap_time,
                        "laps_completed":  s.laps_completed,
                        "skill_rating":    s.skill_rating,
                        "car_performance": s.car_performance,
                    }
                    for s in lap_data.drivers
                ],
                "phase":        lap_data.phase,
                "lights_count":  lap_data.lights_count,
                "flag":          lap_data.flag,
                "red_flag":      lap_data.red_flag,
            })

        return {
            "circuit":       engine.circuit.name,
            "circuit_id":    req.circuit_id,
            "weather":       req.weather,
            "total_laps":    engine.total_laps,
            "final_results": results,
            "lap_history":   lap_history_out,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/manager/quick-race", summary="Simulate a race and return podium only")
async def manager_quick_race(req: ManagerRaceRequest) -> Dict:
    """
    Lightweight race simulation — returns only the final top-10 classification.
    Faster than /manager/start-race (no lap history serialisation).
    """
    try:
        engine  = F1ManagerEngine(
            circuit_id = req.circuit_id,
            weather    = req.weather,
            speed_mult = req.speed_mult,
            driver_ids = req.driver_ids,
        )
        results = engine.simulate_race()
        return {
            "circuit":    engine.circuit.name,
            "weather":    req.weather,
            "total_laps": engine.total_laps,
            "top10":      results[:10],
            "dnfs":       [r for r in results if r["dnf"]],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/manager/drivers", summary="List 2026 driver roster with skill profiles")
async def manager_drivers() -> Dict:
    """Return all 22 drivers with skill ratings."""
    from app.f1_data_2026 import F1_DRIVERS_2026
    return {
        "season": 2026,
        "count":  len(F1_DRIVERS_2026),
        "drivers": [
            {
                "driver_id":   d.driver_id,
                "name":        d.name,
                "number":      d.number,
                "team":        d.team,
                "nationality": d.nationality,
                "skill_rating":round(d.get_skill_rating(), 3),
                "speed":       d.speed,
                "consistency": d.consistency,
                "wet_weather": d.wet_weather,
                "racecraft":   d.racecraft,
            }
            for d in F1_DRIVERS_2026
        ],
    }


@router.get("/manager/teams", summary="List 2026 team / constructor profiles")
async def manager_teams() -> Dict:
    """Return all 11 constructor profiles."""
    from app.f1_data_2026 import F1_TEAMS_2026
    return {
        "season": 2026,
        "count":  len(F1_TEAMS_2026),
        "teams": [
            {
                "team_id":       t.team_id,
                "name":          t.name,
                "country":       t.country,
                "power":         t.power,
                "handling":      t.handling,
                "reliability":   t.reliability,
                "pit_efficiency":t.pit_efficiency,
            }
            for t in F1_TEAMS_2026
        ],
    }
