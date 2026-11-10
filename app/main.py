import logging
import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import get_database, reload_database
from app.ml.predict import router as ml_router
from app.models import SimulationParams, SimulationResponse, VehicleResult
from app.physics import PhysicsEngine, calculate_performance_metrics
from app.physics_config import PRESET_CONFIGS, PhysicsConfig
from app.physics_customizable import ConfigurablePhysicsEngine
from app.physics_improved import ImprovedPhysicsEngine
from app.routes_f1_race import router as f1_router
from app.tuning import apply_tuning_to_vehicles

logger = logging.getLogger("hypercar_sim")

DEFAULT_CORS_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
}


def _get_cors_origins() -> List[str]:
    """Return an explicit CORS allowlist from the environment."""
    configured = os.getenv("CORS_ORIGINS")
    if configured is None:
        return sorted(DEFAULT_CORS_ORIGINS)
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


app = FastAPI(
    title="Hypercar Performance Simulation API",
    description="Physics-based vehicle dynamics simulation with CSV database",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

app.include_router(ml_router)
app.include_router(f1_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    db = get_database()
    logger.info("Hypercar Simulation API started with %d vehicles", len(db.vehicles))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hypercar Performance Simulation API",
        "version": "2.0.0",
        "database": "CSV-based (hypercar_data.csv)",
        "note": "Use /api/ endpoints or visit /docs for API documentation",
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Hypercar Performance Simulation API",
        "version": "2.0.0",
        "endpoints": {
            "vehicles": "/api/vehicles",
            "simulate": "/api/simulate/drag",
            "reload": "/api/reload",
            "health": "/api/health",
            "docs": "/docs",
        },
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db = get_database()
    return {
        "status": "healthy",
        "message": "Backend is running",
        "vehicles_loaded": len(db.vehicles),
    }


@app.get("/api/vehicles")
async def get_vehicles() -> Dict[str, str]:
    """List all available vehicles from database."""
    db = get_database()
    return db.list_vehicles()


@app.post("/api/reload")
async def reload_db(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Reload the vehicle database when an admin token is configured."""
    configured_token = os.getenv("RELOAD_TOKEN")
    if not configured_token:
        raise HTTPException(status_code=404, detail="Not found")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, configured_token):
        raise HTTPException(status_code=401, detail="Invalid admin token")

    try:
        reload_database()
        db = get_database()
        return {
            "status": "success",
            "message": "Database reloaded successfully",
            "vehicles_loaded": len(db.vehicles),
            "vehicles": db.list_vehicles(),
        }
    except Exception:
        logger.exception("Database reload failed")
        raise HTTPException(status_code=500, detail="Failed to reload database")


@app.post("/api/simulate/drag")
async def simulate_drag_race(params: SimulationParams) -> SimulationResponse:
    """Run a bounded drag race simulation for the requested vehicles."""
    db = get_database()

    try:
        base_vehicles = {
            vehicle_id: db.get_vehicle(vehicle_id)
            for vehicle_id in params.vehicle_ids
        }
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        logger.exception("Vehicle lookup failed")
        raise HTTPException(status_code=500, detail="Unable to load requested vehicles")

    if params.tuning_mods:
        logger.info("Applying tuning modifications to %d vehicles", len(params.tuning_mods))
        tuned_vehicles = apply_tuning_to_vehicles(
            params.vehicle_ids,
            base_vehicles,
            params.tuning_mods,
        )
    else:
        tuned_vehicles = base_vehicles

    results: List[VehicleResult] = []

    for vehicle_id in params.vehicle_ids:
        try:
            vehicle = tuned_vehicles[vehicle_id]

            if params.physics_config or params.preset_config:
                if params.preset_config:
                    physics_config = PRESET_CONFIGS.get(params.preset_config)
                    if not physics_config:
                        raise ValueError(f"Invalid preset: {params.preset_config}")
                else:
                    physics_config = PhysicsConfig.model_validate(params.physics_config)
                engine = ConfigurablePhysicsEngine(vehicle, params.environment, physics_config)
            elif params.use_improved_physics:
                engine = ImprovedPhysicsEngine(vehicle, params.environment)
            else:
                engine = PhysicsEngine(vehicle, params.environment)

            snapshots = engine.run_simulation(
                timestep=params.timestep,
                max_time=params.max_time,
                target_distance=params.target_distance,
                start_velocity=params.start_velocity,
            )
            metrics = calculate_performance_metrics(snapshots)

            results.append(
                VehicleResult(
                    vehicle_name=vehicle.name,
                    snapshots=snapshots,
                    time_to_100kmh=metrics["time_to_100kmh"],
                    time_to_200kmh=metrics["time_to_200kmh"],
                    quarter_mile_time=metrics["quarter_mile_time"],
                    quarter_mile_speed=metrics["quarter_mile_speed"],
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            logger.exception("Simulation failed for vehicle %s", vehicle_id)
            raise HTTPException(status_code=500, detail="Simulation failed")

    return SimulationResponse(results=results, environment=params.environment)


frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    @app.get("/")
    async def serve_root():
        return FileResponse(str(frontend_path / "home.html"))

    @app.get("/index.html")
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))

    @app.get("/home.html")
    async def serve_home():
        return FileResponse(str(frontend_path / "home.html"))

    @app.get("/simulator.html")
    async def serve_simulator():
        return FileResponse(str(frontend_path / "simulator.html"))

    @app.get("/circuits.html")
    async def serve_circuits():
        return FileResponse(str(frontend_path / "circuits.html"))

    @app.get("/f1-race.html")
    async def serve_f1_race():
        return FileResponse(str(frontend_path / "f1-race.html"))

    @app.get("/about.html")
    async def serve_about():
        return FileResponse(str(frontend_path / "about.html"))

    app.mount("/", StaticFiles(directory=str(frontend_path)), name="frontend")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
