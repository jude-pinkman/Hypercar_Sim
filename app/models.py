from pydantic import BaseModel, Field
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.physics_config import PhysicsConfig


class TorquePoint(BaseModel):
    """Single point on engine torque curve"""
    rpm: float
    torque: float  # Nm


class GearInfo(BaseModel):
    """Complete information for a single gear"""
    gear_number: int
    ratio: float
    top_speed_kmh: float
    shift_speed_kmh: float


class Vehicle(BaseModel):
    """Complete vehicle specification"""
    vehicle_id: str
    name: str
    mass: float
    power_kw: float
    torque_nm: float
    
    # Aerodynamics
    drag_coefficient: float
    frontal_area: float
    
    # Drivetrain
    final_drive: float
    transmission_efficiency: float
    
    # Gear database
    gears: List[GearInfo]
    
    # Hybrid system (optional)
    electric_power_kw: Optional[float] = None
    electric_torque_nm: Optional[float] = None
    electric_max_speed_kmh: Optional[float] = None
    
    # Engine characteristics
    idle_rpm: float
    redline_rpm: float
    torque_curve: List[TorquePoint]
    
    # Tire specifications
    tire_radius: float
    rolling_resistance_coef: float
    
    # Helper property
    @property
    def gear_ratios(self) -> List[float]:
        """Extract gear ratios from gear database"""
        return [gear.ratio for gear in self.gears]


class EnvironmentConditions(BaseModel):
    """Environmental parameters"""
    temperature_celsius: float = 20
    altitude_meters: float = 0
    air_pressure_kpa: float = 101.325


class SimulationParams(BaseModel):
    """Simulation configuration"""
    vehicle_ids: List[str]
    environment: EnvironmentConditions = Field(default_factory=EnvironmentConditions)
    timestep: float = 0.01
    max_time: float = 30.0
    target_distance: Optional[float] = None  # Target distance in meters (None = no distance limit)
    start_velocity: float = 0.0  # Starting velocity in m/s (for roll races)
    tuning_mods: Optional[Dict[str, dict]] = None  # Tuning modifications per vehicle
    use_improved_physics: bool = True  # Toggle for improved physics engine
    physics_config: Optional[Dict] = None  # Custom physics configuration (PhysicsConfig as dict)
    preset_config: Optional[str] = None  # Preset: 'arcade', 'realistic', 'maximum', 'endurance_race', 'wet_race'


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