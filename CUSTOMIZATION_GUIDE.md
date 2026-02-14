# 🎛️ Complete Physics Customization Guide

## Overview

The hypercar simulator now features **fully customizable physics** where you can adjust **every single parameter** including tire temps, fuel consumption, brake thermal modeling, weather conditions, and much more!

## 🚀 Quick Start

### Method 1: Use Presets (Easiest)

```python
# API Request with preset
{
  "vehicle_ids": ["bugatti_chiron"],
  "preset_config": "maximum"  # Options: arcade, realistic, maximum, endurance_race, wet_race
}
```

### Method 2: Customize Everything

```python
{
  "vehicle_ids": ["koenigsegg_jesko"],
  "physics_config": {
    "tires": {
      "optimal_tire_temp": 95.0,
      "base_friction_coefficient": 1.4,
      "wear_rate": 0.0005
    },
    "fuel": {
      "enabled": true,
      "initial_fuel_kg": 50.0
    },
    "weather": {
      "track_condition": "wet",
      "wet_grip_multiplier": 0.60
    }
  }
}
```

---

## 📋 Complete Parameter List

### 🔥 Tire Physics (`tires`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `initial_tire_temp` | 25.0 | Starting temperature (°C) |
| `optimal_tire_temp` | 85.0 | Peak grip temperature (°C) |
| `max_tire_temp` | 150.0 | Maximum before failure (°C) |
| `base_friction_coefficient` | 1.3 | Base tire grip (μ) |
| `cold_tire_penalty` | 0.30 | Grip loss when cold (0-1) |
| `hot_tire_penalty` | 0.30 | Grip loss when hot (0-1) |
| `wear_rate` | 0.0001 | Tire wear per second |
| `heating_from_acceleration` | 2.0 | Temp rise per g acceleration |
| `cooling_rate` | 0.02 | Cooling coefficient |

**Example:**
```json
"tires": {
  "optimal_tire_temp": 90.0,
  "base_friction_coefficient": 1.4,
  "wear_rate": 0.0005,
  "cold_tire_penalty": 0.40
}
```

---

### ⚖️ Weight Transfer (`weight_transfer`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_front_weight` | 0.40 | Base front weight % (0-1) |
| `transfer_coefficient` | 0.15 | Weight transfer sensitivity |
| `max_rear_weight` | 0.85 | Max rear weight during accel |
| `center_of_gravity_height` | 0.5 | CG height (meters) |
| `wheelbase` | 2.7 | Wheelbase (meters) |

**Example:**
```json
"weight_transfer": {
  "base_front_weight": 0.45,
  "transfer_coefficient": 0.20,
  "max_rear_weight": 0.80
}
```

---

### 🚀 Launch Control (`launch_control`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | true | Enable launch control |
| `rpm_target_percent` | 0.65 | Target RPM % of redline |
| `rpm_variation` | 50.0 | RPM oscillation (RPM) |
| `completion_speed` | 5.0 | Deactivation speed (m/s) |
| `clutch_slip_rate` | 0.3 | Clutch engagement rate |
| `max_launch_traction` | 1.3 | Max traction in g |

**Example:**
```json
"launch_control": {
  "enabled": true,
  "rpm_target_percent": 0.70,
  "max_launch_traction": 1.4
}
```

---

### 💨 Turbo/Boost (`turbo`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | true | Enable forced induction |
| `max_boost_pressure` | 2.0 | Maximum boost (bar) |
| `spool_rate` | 3.0 | Boost buildup (bar/s) |
| `boost_decay_rate` | 5.0 | Boost loss rate (bar/s) |
| `power_multiplier_per_bar` | 0.12 | Power gain per bar |
| `min_rpm_for_boost` | 2000 | Minimum RPM for boost |
| `turbo_lag` | 0.3 | Initial spool delay (s) |

**Example:**
```json
"turbo": {
  "enabled": true,
  "max_boost_pressure": 2.5,
  "spool_rate": 5.0,
  "power_multiplier_per_bar": 0.15
}
```

---

### 🪂 DRS / Active Aero (`drs`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | true | Enable DRS |
| `min_activation_speed` | 150.0 | Min speed (km/h) |
| `drag_reduction` | 0.15 | Drag reduction (0-1) |
| `downforce_reduction` | 0.30 | Downforce loss (0-1) |
| `activation_delay` | 0.5 | Deploy time (seconds) |

**Example:**
```json
"drs": {
  "enabled": true,
  "min_activation_speed": 120.0,
  "drag_reduction": 0.20
}
```

---

### ⚙️ Gearbox / Transmission (`gearbox`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `shift_duration` | 0.15 | Time per shift (seconds) |
| `shift_power_loss` | 0.30 | Power loss during shift |
| `clutch_slip` | 0.15 | RPM variation during shift |
| `gear_1_shift_percent` | 0.68 | 1st gear shift % redline |
| `gear_2_shift_percent` | 0.72 | 2nd gear shift % redline |
| `gear_3_shift_percent` | 0.76 | 3rd gear shift % redline |
| `gear_4_shift_percent` | 0.78 | 4th gear shift % redline |
| `gear_5_shift_percent` | 0.81 | 5th gear shift % redline |
| `gear_6plus_shift_percent` | 0.84 | 6th+ gear shift % redline |

**Example:**
```json
"gearbox": {
  "shift_duration": 0.10,
  "shift_power_loss": 0.20,
  "gear_1_shift_percent": 0.70
}
```

---

### ⛽ Fuel System (`fuel`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | false | Enable fuel consumption |
| `initial_fuel_kg` | 100.0 | Starting fuel (kg) |
| `fuel_tank_capacity` | 100.0 | Max capacity (kg) |
| `consumption_rate_idle` | 0.5 | Idle consumption (kg/hr) |
| `consumption_rate_cruise` | 8.0 | Cruise consumption (kg/hr) |
| `consumption_rate_full_throttle` | 45.0 | Full throttle (kg/hr) |
| `fuel_weight_affects_performance` | true | Fuel weight impacts accel |

**Example:**
```json
"fuel": {
  "enabled": true,
  "initial_fuel_kg": 50.0,
  "consumption_rate_full_throttle": 60.0,
  "fuel_weight_affects_performance": true
}
```

---

### 🛑 Brake System (`brakes`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | false | Enable brake simulation |
| `enable_brake_temp` | false | Enable thermal modeling |
| `initial_brake_temp` | 100.0 | Starting temp (°C) |
| `optimal_brake_temp` | 400.0 | Optimal temp (°C) |
| `max_brake_temp` | 800.0 | Max before fade (°C) |
| `brake_fade_coefficient` | 0.5 | Braking loss at max temp |
| `brake_heating_rate` | 50.0 | Temp rise per brake |
| `brake_cooling_rate` | 20.0 | Cooling rate (°C/s) |

**Example:**
```json
"brakes": {
  "enabled": true,
  "enable_brake_temp": true,
  "max_brake_temp": 750.0,
  "brake_fade_coefficient": 0.60
}
```

---

### ⚡ Hybrid System (`hybrid`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_battery_soc` | false | Enable battery management |
| `initial_battery_soc` | 1.0 | Starting charge (0-1) |
| `battery_capacity_kwh` | 7.5 | Battery capacity (kWh) |
| `max_discharge_rate_kw` | 120.0 | Max power output (kW) |
| `regen_efficiency` | 0.70 | Regen brake efficiency |
| `regen_max_power_kw` | 100.0 | Max regen power (kW) |
| `battery_deployment_mode` | "full" | Mode: full/balanced/conservative |
| `min_battery_reserve` | 0.10 | Min reserve (0-1) |
| `motor_efficiency` | 0.95 | Electric motor efficiency |

**Example:**
```json
"hybrid": {
  "enable_battery_soc": true,
  "battery_capacity_kwh": 10.0,
  "max_discharge_rate_kw": 150.0,
  "battery_deployment_mode": "balanced"
}
```

---

### 🎯 Traction Control (`traction_control`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | true | Enable traction control |
| `intervention_threshold` | 0.10 | Slip ratio for TC |
| `intervention_aggression` | 0.5 | How aggressively TC cuts power |
| `mode` | "sport" | Mode: off/sport/full |
| `allow_wheelspin` | true | Allow slip in sport mode |

**Example:**
```json
"traction_control": {
  "enabled": true,
  "mode": "full",
  "intervention_aggression": 0.7
}
```

---

### 🌦️ Weather (`weather`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `track_condition` | "dry" | dry/damp/wet/snow/ice |
| `track_temperature` | 30.0 | Track surface temp (°C) |
| `rain_intensity` | 0.0 | Rain level (0-1) |
| `standing_water` | 0.0 | Water on track (0-1) |
| `dry_grip_multiplier` | 1.0 | Grip in dry |
| `damp_grip_multiplier` | 0.85 | Grip when damp |
| `wet_grip_multiplier` | 0.60 | Grip in wet |
| `snow_grip_multiplier` | 0.30 | Grip in snow |
| `ice_grip_multiplier` | 0.10 | Grip on ice |
| `enable_wind` | false | Enable wind effects |
| `wind_speed` | 0.0 | Wind speed (m/s) |
| `wind_direction` | 0.0 | Direction (degrees) |

**Example:**
```json
"weather": {
  "track_condition": "wet",
  "rain_intensity": 0.8,
  "wet_grip_multiplier": 0.55,
  "track_temperature": 18.0
}
```

---

## 🎯 Pre-Made Presets

### 1. **Arcade** - Simplified Physics
- No tire temperature effects
- No fuel consumption
- Simplified grip model
- Easy to drive

```json
"preset_config": "arcade"
```

### 2. **Realistic** - Balanced Realism
- Moderate tire effects
- Fuel consumption enabled
- Realistic grip and wear
- Good for comparisons

```json
"preset_config": "realistic"
```

### 3. **Maximum** - All Features
- Full tire thermal model
- Fuel and brake temps
- Hybrid battery management
- Suspension and weather
- Maximum realism

```json
"preset_config": "maximum"
```

### 4. **Endurance Race** - Long Distance
- Aggressive tire wear
- Fuel management critical
- Brake fade modeling
- Battery strategy important

```json
"preset_config": "endurance_race"
```

### 5. **Wet Race** - Rain Conditions
- Wet track surface
- Rain tires optimized
- Reduced grip
- DRS disabled

```json
"preset_config": "wet_race"
```

---

## 📝 Complete API Examples

### Example 1: Quarter Mile with Custom Tires

```json
{
  "vehicle_ids": ["bugatti_chiron"],
  "target_distance": 402.336,
  "physics_config": {
    "tires": {
      "optimal_tire_temp": 95.0,
      "base_friction_coefficient": 1.4,
      "cold_tire_penalty": 0.35
    }
  }
}
```

### Example 2: Endurance Race with Fuel

```json
{
  "vehicle_ids": ["porsche_918"],
  "max_time": 600.0,
  "physics_config": {
    "fuel": {
      "enabled": true,
      "initial_fuel_kg": 80.0,
      "consumption_rate_full_throttle": 55.0
    },
    "tires": {
      "wear_rate": 0.001
    },
    "brakes": {
      "enabled": true,
      "enable_brake_temp": true
    }
  }
}
```

### Example 3: Wet Weather Race

```json
{
  "vehicle_ids": ["mclaren_p1"],
  "environment": {
    "temperature_celsius": 15,
    "altitude_meters": 0
  },
  "physics_config": {
    "weather": {
      "track_condition": "wet",
      "rain_intensity": 0.7,
      "wet_grip_multiplier": 0.60
    },
    "tires": {
      "optimal_tire_temp": 65.0,
      "base_friction_coefficient": 1.1
    },
    "drs": {
      "enabled": false
    }
  }
}
```

### Example 4: Maximum Boost Setup

```json
{
  "vehicle_ids": ["koenigsegg_jesko"],
  "physics_config": {
    "turbo": {
      "enabled": true,
      "max_boost_pressure": 2.8,
      "spool_rate": 6.0,
      "power_multiplier_per_bar": 0.18
    },
    "launch_control": {
      "rpm_target_percent": 0.75,
      "max_launch_traction": 1.5
    }
  }
}
```

---

## 🔧 Python Usage

```python
from app.physics_config import PhysicsConfig, PRESET_CONFIGS

# Method 1: Use preset
config = PRESET_CONFIGS["maximum"]

# Method 2: Create custom
config = PhysicsConfig()
config.tires.optimal_tire_temp = 95.0
config.fuel.enabled = True
config.fuel.initial_fuel_kg = 50.0
config.weather.track_condition = "damp"

# Method 3: Modify preset
config = PRESET_CONFIGS["realistic"].copy(deep=True)
config.turbo.max_boost_pressure = 2.5
config.tires.wear_rate = 0.0005

# Use in simulation
from app.physics_customizable import ConfigurablePhysicsEngine

engine = ConfigurablePhysicsEngine(vehicle, environment, config)
results = engine.run_simulation()
```

---

## 📊 Parameter Impact Guide

### What affects 0-60 time the most?
1. **Tire grip** (`base_friction_coefficient`)
2. **Launch control** (`rpm_target_percent`)
3. **Weight transfer** (`transfer_coefficient`)
4. **Tire temperature** (`optimal_tire_temp`)

### What affects top speed?
1. **DRS** (`drag_reduction`)
2. **Turbo boost** (`max_boost_pressure`)
3. **Air density** (altitude/temperature)
4. **Aerodynamics** (`drag_multiplier`)

### What affects fuel efficiency?
1. **Consumption rates** (`consumption_rate_full_throttle`)
2. **Driving style** (throttle usage)
3. **Aerodynamics** (drag affects fuel use)
4. **Vehicle weight** (including fuel weight)

---

## 🎮 Tips & Best Practices

### For Drag Racing:
- Enable launch control
- Optimize tire temps (85-90°C)
- Aggressive boost settings
- DRS enabled for high speed

### For Circuit Racing:
- Enable brake thermal modeling
- Tire wear management
- Fuel strategy important
- Conservative traction control

### For Endurance:
- Monitor fuel consumption
- Manage tire wear carefully
- Watch brake temperatures
- Balance battery deployment

### For Wet Conditions:
- Reduce tire optimal temp (65-70°C)
- Lower grip coefficient (1.0-1.1)
- Disable DRS
- Enable full traction control

---

## 📖 See Also

- **CUSTOMIZATION_EXAMPLES.py** - 13 detailed examples
- **app/physics_config.py** - Full configuration classes
- **app/physics_customizable.py** - Physics engine implementation

---

## 🆘 Need Help?

Run the examples file:
```bash
python CUSTOMIZATION_EXAMPLES.py
```

This will show you 13 different customization scenarios with explanations!
