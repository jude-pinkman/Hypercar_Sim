from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List
from pathlib import Path
import os

from app.models import SimulationParams, SimulationResponse, VehicleResult
from app.database import get_database, reload_database
from app.physics import PhysicsEngine, calculate_performance_metrics
from app.physics_improved import ImprovedPhysicsEngine
from app.physics_customizable import ConfigurablePhysicsEngine
from app.physics_config import PhysicsConfig, PRESET_CONFIGS
from app.tuning import apply_tuning_to_vehicles, TuningSystem

app = FastAPI(
    title="Hypercar Performance Simulation API",
    description="Physics-based vehicle dynamics simulation with CSV database",
    version="2.0.0"
)

# CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://*.onrender.com",  # Allow all Render subdomains
        "*"  # Allow all origins - you can restrict this later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("\n" + "="*60)
    print("🚗 Hypercar Simulation API Starting...")
    print("="*60)
    # Database will be loaded on first access
    db = get_database()
    print(f"✅ Loaded {len(db.vehicles)} vehicles from database")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hypercar Performance Simulation API",
        "version": "2.0.0",
        "database": "CSV-based (hypercar_data.csv)",
        "note": "Use /api/ endpoints or visit /docs for API documentation"
    }


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Hypercar Performance Simulation API",
        "version": "2.0.0",
        "endpoints": {
            "vehicles": "/api/vehicles",
            "simulate": "/api/simulate/drag",
            "reload": "/api/reload",
            "health": "/api/health",
            "docs": "/docs"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db = get_database()
    return {
        "status": "healthy",
        "message": "Backend is running",
        "vehicles_loaded": len(db.vehicles)
    }


@app.get("/api/vehicles")
async def get_vehicles() -> Dict[str, str]:
    """List all available vehicles from database"""
    db = get_database()
    return db.list_vehicles()


@app.post("/api/reload")
async def reload_db():
    """
    Reload database from CSV file
    
    Use this endpoint after updating the CSV file to refresh the database
    without restarting the server
    """
    try:
        reload_database()
        db = get_database()
        return {
            "status": "success",
            "message": "Database reloaded successfully",
            "vehicles_loaded": len(db.vehicles),
            "vehicles": db.list_vehicles()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload database: {str(e)}")


@app.post("/api/simulate/drag")
async def simulate_drag_race(params: SimulationParams) -> SimulationResponse:
    """
    Run drag race simulation for specified vehicles
    
    Returns complete simulation data including:
    - Time-series snapshots (velocity, acceleration, RPM, gear, etc.)
    - Performance metrics (0-100, 0-200, quarter mile)
    """
    db = get_database()
    
    # Get base vehicles from database
    base_vehicles = {vid: db.get_vehicle(vid) for vid in params.vehicle_ids}
    
    # Apply tuning modifications if provided
    if params.tuning_mods:
        print(f"\n🔧 Applying tuning modifications to {len(params.tuning_mods)} vehicles")
        tuned_vehicles = apply_tuning_to_vehicles(
            params.vehicle_ids,
            base_vehicles,
            params.tuning_mods
        )
    else:
        tuned_vehicles = base_vehicles
    
    results: List[VehicleResult] = []
    
    for vehicle_id in params.vehicle_ids:
        try:
            # Get vehicle (tuned or stock)
            vehicle = tuned_vehicles[vehicle_id]
            
            # Determine which physics engine to use
            if params.physics_config or params.preset_config:
                # Use ConfigurablePhysicsEngine with custom physics
                print(f"\n⚙️ Using ConfigurablePhysicsEngine for {vehicle.name}")
                
                # Get physics config
                if params.preset_config:
                    print(f"   📋 Applying preset: {params.preset_config}")
                    physics_config = PRESET_CONFIGS.get(params.preset_config)
                    if not physics_config:
                        raise ValueError(f"Invalid preset: {params.preset_config}")
                elif params.physics_config:
                    print(f"   🔧 Applying custom physics configuration")
                    # Convert dict to PhysicsConfig object
                    physics_config = PhysicsConfig.parse_obj(params.physics_config)
                
                engine = ConfigurablePhysicsEngine(vehicle, params.environment, physics_config)
                
            elif params.use_improved_physics:
                # Use ImprovedPhysicsEngine (default)
                engine = ImprovedPhysicsEngine(vehicle, params.environment)
            else:
                # Use basic PhysicsEngine
                engine = PhysicsEngine(vehicle, params.environment)
            
            # Run simulation
            snapshots = engine.run_simulation(
                timestep=params.timestep,
                max_time=params.max_time,
                target_distance=params.target_distance,
                start_velocity=params.start_velocity
            )
            
            # Calculate metrics
            metrics = calculate_performance_metrics(snapshots)
            
            # Create result
            result = VehicleResult(
                vehicle_name=vehicle.name,
                snapshots=snapshots,
                time_to_100kmh=metrics['time_to_100kmh'],
                time_to_200kmh=metrics['time_to_200kmh'],
                quarter_mile_time=metrics['quarter_mile_time'],
                quarter_mile_speed=metrics['quarter_mile_speed']
            )
            
            results.append(result)
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
    
    return SimulationResponse(
        results=results,
        environment=params.environment
    )


# Serve frontend static files (optional - only if frontend is in same repo)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")
    
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
    
    @app.get("/about.html")
    async def serve_about():
        return FileResponse(str(frontend_path / "about.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)