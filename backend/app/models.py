from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class TorquePoint(BaseModel):
    """Single point on engine torque curve"""
    rpm: float
    torque: float  # Nm


class Vehicle(BaseModel):
    """Complete vehicle specification"""
    name: str
    mass: float = Field(..., description="Vehicle mass in kg")
    power_kw: float = Field(..., description="Peak power in kW")
    torque_nm: float = Field(..., description="Peak torque in Nm")
    
    # Aerodynamics
    drag_coefficient: float = Field(..., description="Cd")
    frontal_area: float = Field(..., description="Frontal area in m²")
    
    # Drivetrain
    gear_ratios: List[float] = Field(..., description="Gear ratios (1st to top gear)")
    final_drive: float = Field(..., description="Final drive ratio")
    transmission_efficiency: float = Field(default=0.95, description="Drivetrain efficiency")
    
    # Hybrid system (optional)
    electric_power_kw: Optional[float] = Field(default=None, description="Electric motor power in kW")
    electric_torque_nm: Optional[float] = Field(default=None, description="Electric motor torque in Nm")
    electric_max_speed_kmh: Optional[float] = Field(default=None, description="Max speed for electric assist")
    
    # Engine characteristics
    idle_rpm: float = Field(default=1000, description="Idle RPM")
    redline_rpm: float = Field(default=8500, description="Redline RPM")
    torque_curve: List[TorquePoint] = Field(..., description="Engine torque curve")
    
    # Tire specifications
    tire_radius: float = Field(default=0.35, description="Effective tire radius in m")
    rolling_resistance_coef: float = Field(default=0.012, description="Rolling resistance coefficient")


class EnvironmentConditions(BaseModel):
    """Environmental parameters affecting performance"""
    temperature_celsius: float = Field(default=20, description="Ambient temperature")
    altitude_meters: float = Field(default=0, description="Altitude above sea level")
    air_pressure_kpa: float = Field(default=101.325, description="Air pressure in kPa")


class SimulationParams(BaseModel):
    """Simulation configuration"""
    vehicle_ids: List[str] = Field(..., description="List of vehicle IDs to simulate")
    environment: EnvironmentConditions = Field(default_factory=EnvironmentConditions)
    timestep: float = Field(default=0.01, description="Simulation timestep in seconds")
    max_time: float = Field(default=30.0, description="Maximum simulation time in seconds")


class TimeSnapshot(BaseModel):
    """Single frame of simulation data"""
    time: float
    distance: float
    velocity: float
    acceleration: float
    gear: int
    rpm: float
    power_kw: float


class VehicleResult(BaseModel):
    """Complete simulation results for one vehicle"""
    vehicle_name: str
    snapshots: List[TimeSnapshot]
    
    # Performance metrics
    time_to_100kmh: Optional[float] = None
    time_to_200kmh: Optional[float] = None
    quarter_mile_time: Optional[float] = None
    quarter_mile_speed: Optional[float] = None


class SimulationResponse(BaseModel):
    """API response containing all simulation results"""
    results: List[VehicleResult]
    environment: EnvironmentConditions