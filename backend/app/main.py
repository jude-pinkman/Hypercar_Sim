from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List
from pathlib import Path

from app.models import SimulationParams, SimulationResponse, VehicleResult
from app.database import get_database, reload_database
from app.physics import PhysicsEngine, calculate_performance_metrics

app = FastAPI(
    title="Hypercar Performance Simulation API",
    description="Physics-based vehicle dynamics simulation with CSV database",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    results: List[VehicleResult] = []
    
    for vehicle_id in params.vehicle_ids:
        try:
            # Get vehicle from database
            vehicle = db.get_vehicle(vehicle_id)
            
            # Create physics engine
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


# Serve frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")
    
    @app.get("/index.html")
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))
    
    @app.get("/sim.js")
    async def serve_sim_js():
        return FileResponse(str(frontend_path / "sim.js"))
    
    @app.get("/render.js")
    async def serve_render_js():
        return FileResponse(str(frontend_path / "render.js"))
    
    @app.get("/style.css")
    async def serve_style_css():
        return FileResponse(str(frontend_path / "style.css"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
