from pydantic import BaseModel, Field
from typing import Optional


class TirePhysicsConfig(BaseModel):
    """Configuration for tire physics simulation"""
    
    # Temperature settings
    initial_tire_temp: float = Field(default=25.0, description="Starting tire temperature (°C)")
    optimal_tire_temp: float = Field(default=85.0, description="Peak grip temperature (°C)")
    max_tire_temp: float = Field(default=150.0, description="Maximum tire temperature before failure (°C)")
    
    # Heating rates
    heating_from_acceleration: float = Field(default=2.0, description="Temperature rise per g of acceleration per second")
    heating_from_speed: float = Field(default=0.5, description="Temperature rise from friction at 100 m/s")
    cooling_rate: float = Field(default=0.02, description="Cooling rate coefficient towards ambient")
    
    # Grip factors
    base_friction_coefficient: float = Field(default=1.3, description="Base tire friction coefficient (μ)")
    cold_tire_penalty: float = Field(default=0.30, description="Grip reduction when cold (0-1)")
    hot_tire_penalty: float = Field(default=0.30, description="Grip reduction when overheated (0-1)")
    optimal_temp_window: float = Field(default=5.0, description="Temperature range for peak grip (±°C)")
    
    # Wear settings
    wear_rate: float = Field(default=0.0001, description="Tire wear per second")
    max_wear_grip_loss: float = Field(default=0.30, description="Maximum grip loss from wear (0-1)")
    wear_heating_multiplier: float = Field(default=1.2, description="Worn tires heat up faster")
    
    # Speed effects
    speed_grip_reduction: float = Field(default=0.15, description="Grip loss at high speed (0-1)")
    hydroplaning_speed: float = Field(default=200.0, description="Speed where grip starts reducing (m/s)")


class WeightTransferConfig(BaseModel):
    """Configuration for weight transfer dynamics"""
    
    base_front_weight: float = Field(default=0.40, description="Base front weight distribution (0-1)")
    transfer_coefficient: float = Field(default=0.15, description="Weight transfer sensitivity to acceleration")
    max_rear_weight: float = Field(default=0.85, description="Maximum rear weight during hard acceleration")
    min_rear_weight: float = Field(default=0.40, description="Minimum rear weight")
    
    # Advanced options
    center_of_gravity_height: float = Field(default=0.5, description="CG height in meters")
    wheelbase: float = Field(default=2.7, description="Wheelbase in meters")
    

class LaunchControlConfig(BaseModel):
    """Configuration for launch control system"""
    
    enabled: bool = Field(default=True, description="Enable launch control")
    rpm_target_percent: float = Field(default=0.65, description="Target RPM as % of redline (0-1)")
    rpm_variation: float = Field(default=50.0, description="RPM oscillation amplitude")
    completion_speed: float = Field(default=5.0, description="Speed to deactivate launch control (m/s)")
    clutch_slip_rate: float = Field(default=0.3, description="Clutch engagement rate")
    max_launch_traction: float = Field(default=1.3, description="Maximum traction in g during launch")


class TurboBoostConfig(BaseModel):
    """Configuration for turbocharger/supercharger boost"""
    
    enabled: bool = Field(default=True, description="Enable forced induction simulation")
    max_boost_pressure: float = Field(default=2.0, description="Maximum boost pressure (bar)")
    spool_rate: float = Field(default=3.0, description="Boost buildup rate (bar/s)")
    boost_decay_rate: float = Field(default=5.0, description="Boost loss rate off throttle (bar/s)")
    power_multiplier_per_bar: float = Field(default=0.12, description="Power gain per bar of boost")
    
    # Advanced turbo settings
    min_rpm_for_boost: float = Field(default=2000, description="Minimum RPM for boost")
    max_rpm_for_boost: float = Field(default=8000, description="Maximum RPM for boost")
    throttle_threshold: float = Field(default=0.5, description="Minimum throttle for boost (0-1)")
    turbo_lag: float = Field(default=0.3, description="Initial spool delay (seconds)")


class DRSConfig(BaseModel):
    """Configuration for Drag Reduction System / Active Aero"""
    
    enabled: bool = Field(default=True, description="Enable DRS")
    min_activation_speed: float = Field(default=150.0, description="Minimum speed for DRS (km/h)")
    drag_reduction: float = Field(default=0.15, description="Drag coefficient reduction (0-1)")
    downforce_reduction: float = Field(default=0.30, description="Downforce loss when active (0-1)")
    activation_delay: float = Field(default=0.5, description="Time to fully deploy (seconds)")
    deactivation_delay: float = Field(default=0.3, description="Time to fully retract (seconds)")
    

class GearboxConfig(BaseModel):
    """Configuration for transmission and gear shifting"""
    
    shift_duration: float = Field(default=0.15, description="Time per shift (seconds)")
    shift_power_loss: float = Field(default=0.30, description="Power loss during shift (0-1)")
    clutch_slip: float = Field(default=0.15, description="RPM variation during shift (0-1)")
    
    # Shift point customization
    gear_1_shift_percent: float = Field(default=0.68, description="1st gear shift at % redline")
    gear_2_shift_percent: float = Field(default=0.72, description="2nd gear shift at % redline")
    gear_3_shift_percent: float = Field(default=0.76, description="3rd gear shift at % redline")
    gear_4_shift_percent: float = Field(default=0.78, description="4th gear shift at % redline")
    gear_5_shift_percent: float = Field(default=0.81, description="5th gear shift at % redline")
    gear_6plus_shift_percent: float = Field(default=0.84, description="6th+ gear shift at % redline")
    final_gear_shift_percent: float = Field(default=0.95, description="Final gear shift at % redline")
    
    # Protection
    min_rpm_after_shift: float = Field(default=0.52, description="Minimum RPM after upshift (% redline)")
    rev_limiter_active: bool = Field(default=True, description="Enable RPM limiter")


class AerodynamicsConfig(BaseModel):
    """Configuration for aerodynamic effects"""
    
    # Drag
    enable_drag: bool = Field(default=True, description="Enable aerodynamic drag")
    drag_multiplier: float = Field(default=1.0, description="Drag force multiplier")
    
    # Downforce
    enable_downforce: bool = Field(default=True, description="Enable downforce simulation")
    downforce_coefficient: float = Field(default=0.0, description="Downforce coefficient (CL)")
    downforce_distribution_rear: float = Field(default=0.65, description="Rear downforce % (0-1)")
    
    # Speed effects
    air_density_multiplier: float = Field(default=1.0, description="Air density adjustment")
    humidity_factor: float = Field(default=0.98, description="Humidity effect on air density")


class FuelSystemConfig(BaseModel):
    """Configuration for fuel consumption and weight"""
    
    enabled: bool = Field(default=False, description="Enable fuel consumption")
    initial_fuel_kg: float = Field(default=100.0, description="Starting fuel load (kg)")
    fuel_tank_capacity: float = Field(default=100.0, description="Maximum fuel capacity (kg)")
    
    # Consumption rates
    consumption_rate_idle: float = Field(default=0.5, description="Fuel use at idle (kg/hr)")
    consumption_rate_cruise: float = Field(default=8.0, description="Fuel use at cruise (kg/hr)")
    consumption_rate_full_throttle: float = Field(default=45.0, description="Fuel use at full throttle (kg/hr)")
    
    # Performance effects
    fuel_weight_affects_performance: bool = Field(default=True, description="Fuel weight affects acceleration")
    
    
class BrakeSystemConfig(BaseModel):
    """Configuration for brake system"""
    
    enabled: bool = Field(default=False, description="Enable brake simulation")
    
    # Brake performance
    max_brake_force: float = Field(default=15000.0, description="Maximum brake force (N)")
    brake_balance_front: float = Field(default=0.60, description="Front brake bias (0-1)")
    
    # Thermal modeling
    enable_brake_temp: bool = Field(default=False, description="Enable brake temperature")
    initial_brake_temp: float = Field(default=100.0, description="Starting brake temperature (°C)")
    optimal_brake_temp: float = Field(default=400.0, description="Optimal brake temp (°C)")
    max_brake_temp: float = Field(default=800.0, description="Maximum brake temp before fade (°C)")
    brake_fade_coefficient: float = Field(default=0.5, description="Braking loss at max temp (0-1)")
    
    # Cooling
    brake_heating_rate: float = Field(default=50.0, description="Temperature rise per brake application")
    brake_cooling_rate: float = Field(default=20.0, description="Cooling rate (°C/s)")


class HybridSystemConfig(BaseModel):
    """Configuration for hybrid/electric motors"""
    
    # Battery management
    enable_battery_soc: bool = Field(default=False, description="Enable battery state of charge")
    initial_battery_soc: float = Field(default=1.0, description="Starting battery charge (0-1)")
    battery_capacity_kwh: float = Field(default=7.5, description="Battery capacity (kWh)")
    
    # Discharge/Charge rates
    max_discharge_rate_kw: float = Field(default=120.0, description="Maximum power output (kW)")
    regen_efficiency: float = Field(default=0.70, description="Regenerative braking efficiency")
    regen_max_power_kw: float = Field(default=100.0, description="Maximum regen power (kW)")
    
    # Deployment strategy
    battery_deployment_mode: str = Field(default="full", description="Battery use: 'full', 'balanced', 'conservative'")
    min_battery_reserve: float = Field(default=0.10, description="Minimum battery reserve (0-1)")
    
    # Motor characteristics
    motor_efficiency: float = Field(default=0.95, description="Electric motor efficiency")
    motor_thermal_limit: bool = Field(default=False, description="Enable motor thermal limits")


class TractionControlConfig(BaseModel):
    """Configuration for traction and stability control"""
    
    enabled: bool = Field(default=True, description="Enable traction control")
    intervention_threshold: float = Field(default=0.10, description="Slip ratio for intervention (0-1)")
    intervention_aggression: float = Field(default=0.5, description="How aggressively TC cuts power (0-1)")
    
    # System modes
    mode: str = Field(default="sport", description="TC mode: 'off', 'sport', 'full'")
    allow_wheelspin: bool = Field(default=True, description="Allow some wheelspin in sport mode")
    

class SuspensionConfig(BaseModel):
    """Configuration for suspension effects"""
    
    enabled: bool = Field(default=False, description="Enable suspension modeling")
    
    # Damping
    damping_coefficient: float = Field(default=5000.0, description="Suspension damping (N·s/m)")
    spring_stiffness: float = Field(default=50000.0, description="Spring stiffness (N/m)")
    
    # Active suspension
    active_suspension: bool = Field(default=False, description="Enable active suspension")
    ride_height_adjustment: bool = Field(default=False, description="Dynamic ride height")
    min_ride_height: float = Field(default=0.05, description="Minimum ride height (m)")
    max_ride_height: float = Field(default=0.15, description="Maximum ride height (m)")


class WeatherConfig(BaseModel):
    """Configuration for weather effects"""
    
    # Track conditions
    track_condition: str = Field(default="dry", description="Track: 'dry', 'damp', 'wet', 'snow', 'ice'")
    track_temperature: float = Field(default=30.0, description="Track surface temperature (°C)")
    
    # Precipitation
    rain_intensity: float = Field(default=0.0, description="Rain intensity (0-1)")
    standing_water: float = Field(default=0.0, description="Standing water level (0-1)")
    
    # Grip modifiers by condition
    dry_grip_multiplier: float = Field(default=1.0, description="Grip multiplier for dry")
    damp_grip_multiplier: float = Field(default=0.85, description="Grip multiplier for damp")
    wet_grip_multiplier: float = Field(default=0.60, description="Grip multiplier for wet")
    snow_grip_multiplier: float = Field(default=0.30, description="Grip multiplier for snow")
    ice_grip_multiplier: float = Field(default=0.10, description="Grip multiplier for ice")
    
    # Wind
    enable_wind: bool = Field(default=False, description="Enable wind effects")
    wind_speed: float = Field(default=0.0, description="Wind speed (m/s)")
    wind_direction: float = Field(default=0.0, description="Wind direction (degrees, 0=headwind)")


class PhysicsConfig(BaseModel):
    """Master configuration for all physics simulation parameters"""
    
    # Sub-configurations
    tires: TirePhysicsConfig = Field(default_factory=TirePhysicsConfig)
    weight_transfer: WeightTransferConfig = Field(default_factory=WeightTransferConfig)
    launch_control: LaunchControlConfig = Field(default_factory=LaunchControlConfig)
    turbo: TurboBoostConfig = Field(default_factory=TurboBoostConfig)
    drs: DRSConfig = Field(default_factory=DRSConfig)
    gearbox: GearboxConfig = Field(default_factory=GearboxConfig)
    aerodynamics: AerodynamicsConfig = Field(default_factory=AerodynamicsConfig)
    fuel: FuelSystemConfig = Field(default_factory=FuelSystemConfig)
    brakes: BrakeSystemConfig = Field(default_factory=BrakeSystemConfig)
    hybrid: HybridSystemConfig = Field(default_factory=HybridSystemConfig)
    traction_control: TractionControlConfig = Field(default_factory=TractionControlConfig)
    suspension: SuspensionConfig = Field(default_factory=SuspensionConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    
    # General simulation settings
    enable_all_systems: bool = Field(default=True, description="Master enable for advanced physics")
    realism_level: str = Field(default="maximum", description="Preset: 'arcade', 'realistic', 'maximum', 'custom'")
    
    # Debug options
    debug_mode: bool = Field(default=False, description="Enable detailed logging")
    log_interval: float = Field(default=1.0, description="Logging interval (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "realism_level": "maximum",
                "tires": {
                    "optimal_tire_temp": 90.0,
                    "base_friction_coefficient": 1.4
                },
                "fuel": {
                    "enabled": True,
                    "initial_fuel_kg": 50.0
                },
                "weather": {
                    "track_condition": "wet",
                    "wet_grip_multiplier": 0.65
                }
            }
        }


# Preset configurations
PRESET_CONFIGS = {
    "arcade": PhysicsConfig(
        realism_level="arcade",
        tires=TirePhysicsConfig(
            base_friction_coefficient=1.5,
            cold_tire_penalty=0.0,
            wear_rate=0.0
        ),
        launch_control=LaunchControlConfig(enabled=False),
        turbo=TurboBoostConfig(enabled=False),
        fuel=FuelSystemConfig(enabled=False),
        weather=WeatherConfig(track_condition="dry")
    ),
    
    "realistic": PhysicsConfig(
        realism_level="realistic",
        tires=TirePhysicsConfig(
            base_friction_coefficient=1.3,
            cold_tire_penalty=0.15,
            wear_rate=0.00005
        ),
        fuel=FuelSystemConfig(enabled=True),
        weather=WeatherConfig(track_condition="dry")
    ),
    
    "maximum": PhysicsConfig(
        realism_level="maximum",
        tires=TirePhysicsConfig(
            base_friction_coefficient=1.3,
            cold_tire_penalty=0.30,
            wear_rate=0.0001
        ),
        fuel=FuelSystemConfig(enabled=True),
        brakes=BrakeSystemConfig(enabled=True, enable_brake_temp=True),
        hybrid=HybridSystemConfig(enable_battery_soc=True),
        suspension=SuspensionConfig(enabled=True),
        weather=WeatherConfig(track_condition="dry", enable_wind=True)
    ),
    
    "endurance_race": PhysicsConfig(
        realism_level="custom",
        tires=TirePhysicsConfig(wear_rate=0.0005),  # Faster tire wear
        fuel=FuelSystemConfig(
            enabled=True,
            initial_fuel_kg=80.0,
            consumption_rate_full_throttle=60.0
        ),
        brakes=BrakeSystemConfig(
            enabled=True,
            enable_brake_temp=True,
            brake_heating_rate=100.0
        )
    ),
    
    "wet_race": PhysicsConfig(
        realism_level="custom",
        tires=TirePhysicsConfig(
            base_friction_coefficient=1.1,  # Rain tires
            optimal_tire_temp=65.0  # Lower optimal for rain
        ),
        weather=WeatherConfig(
            track_condition="wet",
            rain_intensity=0.7,
            standing_water=0.3
        ),
        drs=DRSConfig(enabled=False)  # No DRS in wet
    )
}
