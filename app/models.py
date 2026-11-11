from typing import Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from app.physics_config import PhysicsConfig


class TorquePoint(BaseModel):
    """Single point on engine torque curve."""

    rpm: float
    torque: float  # Nm


class GearInfo(BaseModel):
    """Complete information for a single gear."""

    gear_number: int
    ratio: float
    top_speed_kmh: float
    shift_speed_kmh: float


class Vehicle(BaseModel):
    """Complete vehicle specification."""

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

    @property
    def gear_ratios(self) -> List[float]:
        """Extract gear ratios from gear database."""
        return [gear.ratio for gear in self.gears]


class EnvironmentConditions(BaseModel):
    """Environmental parameters accepted by the simulation engine."""

    temperature_celsius: float = Field(20, ge=-80, le=70)
    altitude_meters: float = Field(0, ge=-500, le=10000)
    air_pressure_kpa: float = Field(101.325, gt=50, le=120)


class SimulationParams(BaseModel):
    """Bounded simulation configuration."""

    vehicle_ids: List[str] = Field(..., min_length=1, max_length=3)
    environment: EnvironmentConditions = Field(default_factory=EnvironmentConditions)
    timestep: float = Field(0.01, gt=0, le=0.1)
    max_time: float = Field(30.0, gt=0, le=120)
    target_distance: Optional[float] = Field(None, gt=0, le=100000)
    start_velocity: float = Field(0.0, ge=0, le=150)
    tuning_mods: Optional[Dict[str, dict]] = None
    use_improved_physics: bool = True
    physics_config: Optional[Dict[str, object]] = None
    preset_config: Optional[str] = Field(
        None,
        pattern="^(arcade|realistic|maximum|endurance_race|wet_race)$",
    )

    @model_validator(mode="after")
    def reject_conflicting_physics_options(self) -> "SimulationParams":
        if self.physics_config is not None and self.preset_config is not None:
            raise ValueError("Choose either physics_config or preset_config, not both")
        if self.tuning_mods is not None:
            unknown = set(self.tuning_mods) - set(self.vehicle_ids)
            if unknown:
                raise ValueError("tuning_mods contains an unknown vehicle ID")
        return self


class TimeSnapshot(BaseModel):
    """Single frame of simulation data."""

    time: float
    distance: float
    velocity: float
    acceleration: float
    gear: int
    rpm: float
    power_kw: float


class VehicleResult(BaseModel):
    """Complete simulation results for one vehicle."""

    vehicle_name: str
    snapshots: List[TimeSnapshot]

    time_to_100kmh: Optional[float] = None
    time_to_200kmh: Optional[float] = None
    quarter_mile_time: Optional[float] = None
    quarter_mile_speed: Optional[float] = None


class SimulationResponse(BaseModel):
    """API response containing all simulation results."""

    results: List[VehicleResult]
    environment: EnvironmentConditions
