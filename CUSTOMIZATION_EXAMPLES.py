"""
Comprehensive Examples for Customizable Physics Engine

This file demonstrates how to customize every aspect of the physics simulation.
"""

import json
from app.physics_config import (
    PhysicsConfig, TirePhysicsConfig, WeightTransferConfig,
    LaunchControlConfig, TurboBoostConfig, DRSConfig, GearboxConfig,
    AerodynamicsConfig, FuelSystemConfig, BrakeSystemConfig,
    HybridSystemConfig, TractionControlConfig, SuspensionConfig,
    WeatherConfig, PRESET_CONFIGS
)

# =============================================================================
# EXAMPLE 1: Using Presets
# =============================================================================

def example_1_presets():
    """The easiest way - use predefined presets"""
    
    # Arcade mode - simplified physics
    arcade_config = PRESET_CONFIGS["arcade"]
    
    # Realistic mode - balanced realism
    realistic_config = PRESET_CONFIGS["realistic"]
    
    # Maximum mode - all features enabled
    maximum_config = PRESET_CONFIGS["maximum"]
    
    # Specialized presets
    endurance_config = PRESET_CONFIGS["endurance_race"]
    wet_config = PRESET_CONFIGS["wet_race"]
    
    print("Presets available:", list(PRESET_CONFIGS.keys()))
    
    # Use in API request:
    api_request = {
        "vehicle_ids": ["bugatti_chiron"],
        "preset_config": "maximum",  # ← Use preset name
    }
    
    return api_request


# =============================================================================
# EXAMPLE 2: Customizing Individual Parameters
# =============================================================================

def example_2_tire_customization():
    """Customize tire physics parameters"""
    
    config = PhysicsConfig()
    
    # Adjust tire temperatures
    config.tires.optimal_tire_temp = 90.0  # °C - higher optimal temp
    config.tires.initial_tire_temp = 30.0  # Start warmer
    config.tires.cold_tire_penalty = 0.40  # More penalty for cold tires
    
    # Adjust grip
    config.tires.base_friction_coefficient = 1.4  # Stickier tires
    
    # Adjust wear
    config.tires.wear_rate = 0.0005  # Faster wear for endurance races
    
    print("Custom tire config:")
    print(f"  Optimal temp: {config.tires.optimal_tire_temp}°C")
    print(f"  Base grip (μ): {config.tires.base_friction_coefficient}")
    
    # Use in API
    api_request = {
        "vehicle_ids": ["koenigsegg_jesko"],
        "physics_config": config.dict()
    }
    
    return config


# =============================================================================
# EXAMPLE 3: Fuel Consumption Simulation
# =============================================================================

def example_3_fuel_system():
    """Enable and configure fuel consumption"""
    
    config = PhysicsConfig()
    
    # Enable fuel system
    config.fuel.enabled = True
    config.fuel.initial_fuel_kg = 50.0  # Start with 50kg
    config.fuel.fuel_tank_capacity = 100.0  # 100kg capacity
    
    # Set consumption rates
    config.fuel.consumption_rate_idle = 1.0  # kg/hr at idle
    config.fuel.consumption_rate_cruise = 15.0  # kg/hr cruising
    config.fuel.consumption_rate_full_throttle = 60.0  # kg/hr flat out
    
    # Fuel weight affects performance
    config.fuel.fuel_weight_affects_performance = True
    
    print("Fuel system enabled:")
    print(f"  Starting fuel: {config.fuel.initial_fuel_kg} kg")
    print(f"  Full throttle consumption: {config.fuel.consumption_rate_full_throttle} kg/hr")
    print(f"  Weight affects performance: {config.fuel.fuel_weight_affects_performance}")
    
    return config


# =============================================================================
# EXAMPLE 4: Weather Conditions
# =============================================================================

def example_4_weather_conditions():
    """Simulate different weather conditions"""
    
    # Dry conditions
    dry_config = PhysicsConfig()
    dry_config.weather.track_condition = "dry"
    dry_config.weather.track_temperature = 45.0  # Hot track
    
    # Wet conditions
    wet_config = PhysicsConfig()
    wet_config.weather.track_condition = "wet"
    wet_config.weather.rain_intensity = 0.8  # Heavy rain
    wet_config.weather.standing_water = 0.5
    wet_config.weather.wet_grip_multiplier = 0.55  # Very slippery
    wet_config.drs.enabled = False  # No DRS in wet
    
    # Add tire adjustments for wet
    wet_config.tires.optimal_tire_temp = 65.0  # Lower for rain tires
    wet_config.tires.base_friction_coefficient = 1.1  # Rain tire compound
    
    # Snow conditions
    snow_config = PhysicsConfig()
    snow_config.weather.track_condition = "snow"
    snow_config.weather.snow_grip_multiplier = 0.25
    snow_config.tires.base_friction_coefficient = 0.8  # Winter tires
    
    print("Weather configurations:")
    print(f"  Wet grip: {wet_config.weather.wet_grip_multiplier}")
    print(f"  Snow grip: {snow_config.weather.snow_grip_multiplier}")
    
    # API request for wet race
    api_request = {
        "vehicle_ids": ["mclaren_p1"],
        "environment": {
            "temperature_celsius": 15,  # Cooler in rain
            "altitude_meters": 0
        },
        "physics_config": wet_config.dict()
    }
    
    return wet_config


# =============================================================================
# EXAMPLE 5: Turbo/Boost Customization
# =============================================================================

def example_5_turbo_boost():
    """Customize forced induction system"""
    
    config = PhysicsConfig()
    
    # Aggressive turbo setup
    config.turbo.enabled = True
    config.turbo.max_boost_pressure = 2.5  # 2.5 bar (aggressive)
    config.turbo.spool_rate = 5.0  # Fast spool (5 bar/s)
    config.turbo.power_multiplier_per_bar = 0.15  # More power per bar
    config.turbo.turbo_lag = 0.2  # Minimal lag
    
    # Conservative setup
    conservative_turbo = TurboBoostConfig(
        max_boost_pressure=1.5,
        spool_rate=2.0,
        turbo_lag=0.5
    )
    
    print("Aggressive turbo config:")
    print(f"  Max boost: {config.turbo.max_boost_pressure} bar")
    print(f"  Spool rate: {config.turbo.spool_rate} bar/s")
    print(f"  Power gain: +{config.turbo.power_multiplier_per_bar * 100}% per bar")
    
    return config


# =============================================================================
# EXAMPLE 6: Launch Control Tuning
# =============================================================================

def example_6_launch_control():
    """Fine-tune launch control system"""
    
    config = PhysicsConfig()
    
    # Aggressive launch
    config.launch_control.enabled = True
    config.launch_control.rpm_target_percent = 0.70  # 70% redline
    config.launch_control.max_launch_traction = 1.4  # Allow more slip
    config.launch_control.clutch_slip_rate = 0.5  # Faster engagement
    
    # Conservative launch
    conservative = LaunchControlConfig(
        rpm_target_percent=0.60,  # Lower RPM
        max_launch_traction=1.2,  # Less slip
        clutch_slip_rate=0.2  # Slower engagement
    )
    
    print("Launch control settings:")
    print(f"  Target RPM: {config.launch_control.rpm_target_percent * 100}% of redline")
    print(f"  Max traction: {config.launch_control.max_launch_traction}g")
    
    return config


# =============================================================================
# EXAMPLE 7: Hybrid/Electric System
# =============================================================================

def example_7_hybrid_system():
    """Configure hybrid battery and electric motors"""
    
    config = PhysicsConfig()
    
    # Enable battery management
    config.hybrid.enable_battery_soc = True
    config.hybrid.initial_battery_soc = 1.0  # Fully charged
    config.hybrid.battery_capacity_kwh = 10.0  # 10 kWh battery
    
    # Set deployment strategy
    config.hybrid.battery_deployment_mode = "full"  # Use all available
    config.hybrid.min_battery_reserve = 0.05  # Keep 5% reserve
    
    # Motor characteristics
    config.hybrid.motor_efficiency = 0.97  # 97% efficient
    config.hybrid.max_discharge_rate_kw = 150.0  # 150 kW output
    
    # Regenerative braking
    config.hybrid.regen_efficiency = 0.75  # 75% efficient
    config.hybrid.regen_max_power_kw = 120.0  # 120 kW regen
    
    print("Hybrid system config:")
    print(f"  Battery: {config.hybrid.battery_capacity_kwh} kWh")
    print(f"  Motor output: {config.hybrid.max_discharge_rate_kw} kW")
    print(f"  Regen: {config.hybrid.regen_max_power_kw} kW")
    
    return config


# =============================================================================
# EXAMPLE 8: Gear Shift Customization
# =============================================================================

def example_8_gear_shifts():
    """Customize transmission and shifting"""
    
    config = PhysicsConfig()
    
    # Fast DCT shifts
    config.gearbox.shift_duration = 0.10  # 100ms shifts
    config.gearbox.shift_power_loss = 0.20  # 20% loss during shift
    config.gearbox.clutch_slip = 0.10  # Minimal slip
    
    # Adjust shift points for each gear
    config.gearbox.gear_1_shift_percent = 0.70  # Shift 1st at 70% redline
    config.gearbox.gear_2_shift_percent = 0.75
    config.gearbox.gear_3_shift_percent = 0.78
    config.gearbox.gear_4_shift_percent = 0.82
    config.gearbox.gear_5_shift_percent = 0.85
    config.gearbox.gear_6plus_shift_percent = 0.88
    
    # Slow manual shifts
    manual_shifts = GearboxConfig(
        shift_duration=0.30,  # 300ms
        shift_power_loss=0.40,  # 40% loss
        clutch_slip=0.25  # More slip
    )
    
    print("Shift configuration:")
    print(f"  Shift time: {config.gearbox.shift_duration * 1000}ms")
    print(f"  1st gear shift: {config.gearbox.gear_1_shift_percent * 100}% redline")
    
    return config


# =============================================================================
# EXAMPLE 9: Complete Endurance Race Setup
# =============================================================================

def example_9_endurance_race():
    """Full configuration for a long-distance race"""
    
    config = PhysicsConfig()
    
    # Aggressive tire wear
    config.tires.wear_rate = 0.001  # Fast wear
    config.tires.max_wear_grip_loss = 0.40  # Significant loss when worn
    
    # Fuel management
    config.fuel.enabled = True
    config.fuel.initial_fuel_kg = 100.0  # Full tank
    config.fuel.fuel_weight_affects_performance = True
    
    # Brake thermal management
    config.brakes.enabled = True
    config.brakes.enable_brake_temp = True
    config.brakes.max_brake_temp = 750.0
    config.brakes.brake_fade_coefficient = 0.60  # Significant fade
    
    # Hybrid battery management
    config.hybrid.enable_battery_soc = True
    config.hybrid.battery_deployment_mode = "balanced"
    
    # Conservative traction control
    config.traction_control.enabled = True
    config.traction_control.mode = "full"
    
    print("Endurance race configuration:")
    print(f"  Tire wear rate: {config.tires.wear_rate}")
    print(f"  Fuel enabled: {config.fuel.enabled}")
    print(f"  Brake temps: {config.brakes.enable_brake_temp}")
    print(f"  Battery mode: {config.hybrid.battery_deployment_mode}")
    
    # API request
    api_request = {
        "vehicle_ids": ["porsche_918"],
        "max_time": 600.0,  # 10 minute race
        "physics_config": config.dict()
    }
    
    return config


# =============================================================================
# EXAMPLE 10: DRS and Active Aero
# =============================================================================

def example_10_active_aero():
    """Configure DRS and active aerodynamics"""
    
    config = PhysicsConfig()
    
    # Aggressive DRS
    config.drs.enabled = True
    config.drs.min_activation_speed = 120.0  # Activate at 120 km/h
    config.drs.drag_reduction = 0.20  # 20% drag reduction
    config.drs.downforce_reduction = 0.40  # Lose 40% downforce
    config.drs.activation_delay = 0.3  # Fast deployment
    
    # Conservative DRS
    conservative_drs = DRSConfig(
        min_activation_speed = 180.0,  # Higher speed requirement
        drag_reduction = 0.12,  # Less reduction
        downforce_reduction = 0.25  # Keep more downforce
    )
    
    print("DRS configuration:")
    print(f"  Activation speed: {config.drs.min_activation_speed} km/h")
    print(f"  Drag reduction: {config.drs.drag_reduction * 100}%")
    print(f"  Downforce loss: {config.drs.downforce_reduction * 100}%")
    
    return config


# =============================================================================
# EXAMPLE 11: JSON Configuration for API
# =============================================================================

def example_11_api_json():
    """Generate JSON for API requests"""
    
    config = PhysicsConfig()
    
    # Customize some parameters
    config.tires.optimal_tire_temp = 95.0
    config.fuel.enabled = True
    config.fuel.initial_fuel_kg = 75.0
    config.weather.track_condition = "damp"
    config.drs.enabled = True
    
    # Convert to dict for JSON
    config_dict = config.dict()
    
    # Complete API request
    api_request = {
        "vehicle_ids": ["bugatti_chiron", "koenigsegg_jesko"],
        "environment": {
            "temperature_celsius": 25,
            "altitude_meters": 100,
            "air_pressure_kpa": 101.325
        },
        "max_time": 30.0,
        "target_distance": 402.336,  # Quarter mile
        "physics_config": config_dict
    }
    
    # Print as JSON
    json_output = json.dumps(api_request, indent=2)
    print("API request JSON:")
    print(json_output[:500] + "...")  # First 500 chars
    
    return api_request


# =============================================================================
# EXAMPLE 12: Mixing Presets with Custom Values
# =============================================================================

def example_12_preset_override():
    """Start with a preset and override specific values"""
    
    # Start with realistic preset
    config = PRESET_CONFIGS["realistic"].copy(deep=True)
    
    # Override specific values
    config.tires.optimal_tire_temp = 100.0  # Different optimal temp
    config.turbo.max_boost_pressure = 2.5  # More boost
    config.fuel.consumption_rate_full_throttle = 50.0  # Less consumption
    config.weather.track_condition = "damp"  # Change conditions
    
    print("Modified realistic preset:")
    print(f"  Base: realistic")
    print(f"  Tire temp: {config.tires.optimal_tire_temp}°C")
    print(f"  Boost: {config.turbo.max_boost_pressure} bar")
    print(f"  Track: {config.weather.track_condition}")
    
    return config


# =============================================================================
# EXAMPLE 13: Per-Parameter Documentation
# =============================================================================

def example_13_parameter_reference():
    """Show all available parameters with descriptions"""
    
    config = PhysicsConfig()
    
    print("\n" + "="*80)
    print("COMPLETE PARAMETER REFERENCE")
    print("="*80)
    
    # Tire parameters
    print("\n📍 TIRE PHYSICS:")
    print(f"  initial_tire_temp: {config.tires.initial_tire_temp} °C")
    print(f"  optimal_tire_temp: {config.tires.optimal_tire_temp} °C")
    print(f"  base_friction_coefficient: {config.tires.base_friction_coefficient}")
    print(f"  wear_rate: {config.tires.wear_rate} per second")
    print(f"  cold_tire_penalty: {config.tires.cold_tire_penalty * 100}%")
    
    # Weight transfer
    print("\n⚖️  WEIGHT TRANSFER:")
    print(f"  base_front_weight: {config.weight_transfer.base_front_weight * 100}%")
    print(f"  transfer_coefficient: {config.weight_transfer.transfer_coefficient}")
    print(f"  max_rear_weight: {config.weight_transfer.max_rear_weight * 100}%")
    
    # Launch control
    print("\n🚀 LAUNCH CONTROL:")
    print(f"  enabled: {config.launch_control.enabled}")
    print(f"  rpm_target_percent: {config.launch_control.rpm_target_percent * 100}%")
    print(f"  max_launch_traction: {config.launch_control.max_launch_traction}g")
    
    # Turbo
    print("\n💨 TURBO/BOOST:")
    print(f"  enabled: {config.turbo.enabled}")
    print(f"  max_boost_pressure: {config.turbo.max_boost_pressure} bar")
    print(f"  spool_rate: {config.turbo.spool_rate} bar/s")
    print(f"  power_multiplier_per_bar: +{config.turbo.power_multiplier_per_bar * 100}%")
    
    # DRS
    print("\n🪂 DRS/ACTIVE AERO:")
    print(f"  enabled: {config.drs.enabled}")
    print(f"  min_activation_speed: {config.drs.min_activation_speed} km/h")
    print(f"  drag_reduction: {config.drs.drag_reduction * 100}%")
    
    # Fuel
    print("\n⛽ FUEL SYSTEM:")
    print(f"  enabled: {config.fuel.enabled}")
    print(f"  initial_fuel_kg: {config.fuel.initial_fuel_kg} kg")
    print(f"  consumption_full_throttle: {config.fuel.consumption_rate_full_throttle} kg/hr")
    
    # Weather
    print("\n🌦️  WEATHER:")
    print(f"  track_condition: {config.weather.track_condition}")
    print(f"  wet_grip_multiplier: {config.weather.wet_grip_multiplier}")
    print(f"  enable_wind: {config.weather.enable_wind}")
    
    print("\n" + "="*80)
    
    return config


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PHYSICS CUSTOMIZATION EXAMPLES")
    print("="*80)
    
    examples = [
        ("Using Presets", example_1_presets),
        ("Tire Customization", example_2_tire_customization),
        ("Fuel System", example_3_fuel_system),
        ("Weather Conditions", example_4_weather_conditions),
        ("Turbo Boost", example_5_turbo_boost),
        ("Launch Control", example_6_launch_control),
        ("Hybrid System", example_7_hybrid_system),
        ("Gear Shifts", example_8_gear_shifts),
        ("Endurance Race", example_9_endurance_race),
        ("Active Aero/DRS", example_10_active_aero),
        ("API JSON", example_11_api_json),
        ("Preset Override", example_12_preset_override),
        ("Parameter Reference", example_13_parameter_reference),
    ]
    
    for name, func in examples:
        print(f"\n{'='*80}")
        print(f"EXAMPLE: {name}")
        print('='*80)
        result = func()
        print()
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)
