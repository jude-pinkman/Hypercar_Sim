import math
from typing import List, Tuple, Optional
from app.models import Vehicle, EnvironmentConditions, TimeSnapshot
from app.physics_config import PhysicsConfig


class ConfigurablePhysicsEngine:
    """
    Fully customizable physics simulation engine
    
    Every aspect of the simulation can be configured through PhysicsConfig.
    Supports:
    - Tire physics (temperature, wear, grip)
    - Weight transfer dynamics
    - Launch control systems
    - Forced induction (turbo/supercharger)
    - Active aerodynamics (DRS)
    - Fuel consumption and weight
    - Brake thermal modeling
    - Hybrid/electric systems with battery management
    - Traction control
    - Suspension effects
    - Weather conditions
    """
    
    # Physical constants
    GRAVITY = 9.81  # m/s²
    AIR_GAS_CONSTANT = 287.05  # J/(kg·K)
    
    def __init__(self, vehicle: Vehicle, environment: EnvironmentConditions, config: PhysicsConfig):
        self.vehicle = vehicle
        self.environment = environment
        self.config = config
        
        # Calculate initial air density
        self.air_density = self._calculate_air_density()
        
        # Initialize state based on configuration
        self._initialize_state()
        
    def _initialize_state(self):
        """Initialize all simulation state variables based on config"""
        
        # Tire state
        self.tire_temp_fl = self.config.tires.initial_tire_temp
        self.tire_temp_fr = self.config.tires.initial_tire_temp
        self.tire_temp_rl = self.config.tires.initial_tire_temp
        self.tire_temp_rr = self.config.tires.initial_tire_temp
        self.tire_wear = 0.0
        
        # Launch control
        self.launch_control_active = self.config.launch_control.enabled
        self.launch_completed = False
        
        # Turbo/boost
        self.boost_pressure = 0.0
        self.boost_active_time = 0.0
        
        # DRS
        self.drs_active = False
        self.drs_deployment = 0.0  # 0 to 1
        
        # Gear shifting
        self.is_shifting = False
        self.shift_time_remaining = 0.0
        
        # Fuel
        self.current_fuel_kg = self.config.fuel.initial_fuel_kg if self.config.fuel.enabled else 0.0
        
        # Brakes
        self.brake_temp_front = self.config.brakes.initial_brake_temp if self.config.brakes.enabled else 100.0
        self.brake_temp_rear = self.config.brakes.initial_brake_temp if self.config.brakes.enabled else 100.0
        
        # Hybrid battery
        self.battery_soc = self.config.hybrid.initial_battery_soc if self.config.hybrid.enable_battery_soc else 1.0
        
        # Traction control
        self.tc_intervention = 0.0  # 0 to 1
        
        # Pre-calculate shift velocities
        self.shift_velocities = self._calculate_shift_velocities()
        
    def _calculate_air_density(self) -> float:
        """Calculate air density with weather effects"""
        temp_kelvin = self.environment.temperature_celsius + 273.15
        pressure_pa = self.environment.air_pressure_kpa * 1000
        
        # Altitude adjustment
        altitude_m = self.environment.altitude_meters
        pressure_pa *= math.exp(-altitude_m / 8400)
        
        # Base density
        density = pressure_pa / (self.AIR_GAS_CONSTANT * temp_kelvin)
        
        # Apply config multipliers
        density *= self.config.aerodynamics.air_density_multiplier
        density *= self.config.aerodynamics.humidity_factor
        
        return density
    
    def _calculate_shift_velocities(self) -> List[float]:
        """Calculate shift velocities based on config"""
        shift_velocities_ms = []
        gear_config = self.config.gearbox
        
        shift_percents = [
            gear_config.gear_1_shift_percent,
            gear_config.gear_2_shift_percent,
            gear_config.gear_3_shift_percent,
            gear_config.gear_4_shift_percent,
            gear_config.gear_5_shift_percent,
        ]
        
        for i in range(len(self.vehicle.gear_ratios)):
            if i < len(shift_percents):
                shift_percent = shift_percents[i]
            elif i == len(self.vehicle.gear_ratios) - 1:
                shift_percent = gear_config.final_gear_shift_percent
            else:
                shift_percent = gear_config.gear_6plus_shift_percent
            
            shift_rpm = self.vehicle.redline_rpm * shift_percent
            gear_ratio = self.vehicle.gear_ratios[i]
            total_ratio = gear_ratio * self.vehicle.final_drive
            shift_velocity = (shift_rpm * 2 * math.pi * self.vehicle.tire_radius) / (60 * total_ratio)
            shift_velocities_ms.append(shift_velocity)
        
        return shift_velocities_ms
    
    def get_current_mass(self) -> float:
        """Calculate current vehicle mass including fuel"""
        base_mass = self.vehicle.mass
        if self.config.fuel.enabled and self.config.fuel.fuel_weight_affects_performance:
            return base_mass + self.current_fuel_kg
        return base_mass
    
    def update_tire_temperature(self, acceleration: float, velocity_ms: float, dt: float):
        """Update tire temperatures based on usage and config"""
        if not self.config.enable_all_systems:
            return
        
        # Average tire temp for simplicity (can be expanded to per-wheel)
        avg_temp = (self.tire_temp_fl + self.tire_temp_fr + self.tire_temp_rl + self.tire_temp_rr) / 4
        
        # Heating from acceleration
        if abs(acceleration) > 2.0:
            heating_rate = (abs(acceleration) - 2.0) * self.config.tires.heating_from_acceleration
            # Worn tires heat up faster
            if self.tire_wear > 0.3:
                heating_rate *= self.config.tires.wear_heating_multiplier
            avg_temp += heating_rate * dt
        
        # Heating from speed
        speed_heating = (velocity_ms / 100) * self.config.tires.heating_from_speed
        avg_temp += speed_heating * dt
        
        # Cooling
        temp_diff = avg_temp - self.environment.temperature_celsius
        cooling = temp_diff * self.config.tires.cooling_rate
        avg_temp -= cooling * dt
        
        # Clamp
        avg_temp = max(self.environment.temperature_celsius, 
                      min(self.config.tires.max_tire_temp, avg_temp))
        
        # Update all tire temps
        self.tire_temp_fl = self.tire_temp_fr = self.tire_temp_rl = self.tire_temp_rr = avg_temp
    
    def get_tire_grip_factor(self) -> float:
        """Calculate grip multiplier from tire temperature and wear"""
        avg_temp = (self.tire_temp_fl + self.tire_temp_fr + self.tire_temp_rl + self.tire_temp_rr) / 4
        
        temp_diff = abs(avg_temp - self.config.tires.optimal_tire_temp)
        
        if temp_diff < self.config.tires.optimal_temp_window:
            grip = 1.0
        elif temp_diff < 20:
            grip = 1.0 - (temp_diff - self.config.tires.optimal_temp_window) * 0.015
        else:
            # Apply cold or hot penalty
            if avg_temp < self.config.tires.optimal_tire_temp:
                max_penalty = self.config.tires.cold_tire_penalty
            else:
                max_penalty = self.config.tires.hot_tire_penalty
            grip = max(1.0 - max_penalty, 1.0 - (temp_diff * 0.02))
        
        # Apply wear reduction
        wear_factor = 1.0 - (self.tire_wear * self.config.tires.max_wear_grip_loss)
        
        # Apply weather/track condition
        weather_factor = self._get_weather_grip_factor()
        
        return grip * wear_factor * weather_factor
    
    def _get_weather_grip_factor(self) -> float:
        """Get grip multiplier based on weather/track conditions"""
        condition = self.config.weather.track_condition
        
        multipliers = {
            'dry': self.config.weather.dry_grip_multiplier,
            'damp': self.config.weather.damp_grip_multiplier,
            'wet': self.config.weather.wet_grip_multiplier,
            'snow': self.config.weather.snow_grip_multiplier,
            'ice': self.config.weather.ice_grip_multiplier
        }
        
        return multipliers.get(condition, 1.0)
    
    def calculate_weight_transfer(self, acceleration: float) -> float:
        """Calculate rear weight proportion with weight transfer"""
        if not self.config.enable_all_systems:
            return 0.6  # Default mid-engine
        
        base_rear = 1.0 - self.config.weight_transfer.base_front_weight
        accel_g = acceleration / self.GRAVITY
        transfer = accel_g * self.config.weight_transfer.transfer_coefficient
        rear_weight = base_rear + transfer
        
        return max(self.config.weight_transfer.min_rear_weight,
                  min(self.config.weight_transfer.max_rear_weight, rear_weight))
    
    def calculate_max_traction_force(self, velocity_ms: float, acceleration: float) -> float:
        """Calculate maximum traction with all factors"""
        grip_factor = self.get_tire_grip_factor()
        rear_weight_proportion = self.calculate_weight_transfer(acceleration)
        
        current_mass = self.get_current_mass()
        driven_weight = current_mass * rear_weight_proportion * self.GRAVITY
        
        # Base friction coefficient
        base_mu = self.config.tires.base_friction_coefficient
        
        # Speed reduction
        if velocity_ms > self.config.tires.hydroplaning_speed:
            speed_factor = 1.0 - self.config.tires.speed_grip_reduction
        else:
            speed_factor = 1.0
        
        effective_mu = base_mu * grip_factor * speed_factor
        max_traction = effective_mu * driven_weight
        
        # Apply traction control if enabled
        if self.config.traction_control.enabled:
            max_traction *= (1.0 - self.tc_intervention * self.config.traction_control.intervention_aggression)
        
        return max_traction
    
    def simulate_launch_control(self, velocity_ms: float, dt: float) -> Tuple[bool, float]:
        """Simulate launch control system"""
        if not self.config.launch_control.enabled or self.launch_completed:
            return False, 0.0
        
        if velocity_ms > self.config.launch_control.completion_speed:
            self.launch_completed = True
            self.launch_control_active = False
            return False, 0.0
        
        target_rpm = self.vehicle.redline_rpm * self.config.launch_control.rpm_target_percent
        rpm_variation = math.sin(dt * 50) * self.config.launch_control.rpm_variation
        
        return True, target_rpm + rpm_variation
    
    def update_turbo_boost(self, rpm: float, throttle: float, dt: float):
        """Update turbo boost pressure"""
        if not self.config.turbo.enabled:
            self.boost_pressure = 0.0
            return
        
        # Check RPM range
        if rpm < self.config.turbo.min_rpm_for_boost or rpm > self.config.turbo.max_rpm_for_boost:
            target_boost = 0.0
        elif throttle < self.config.turbo.throttle_threshold:
            target_boost = 0.0
        else:
            # Target boost based on RPM and throttle
            rpm_factor = (rpm - self.config.turbo.min_rpm_for_boost) / \
                        (self.vehicle.redline_rpm - self.config.turbo.min_rpm_for_boost)
            target_boost = rpm_factor * throttle * self.config.turbo.max_boost_pressure
        
        # Spool up or down
        if target_boost > self.boost_pressure:
            rate = self.config.turbo.spool_rate
            self.boost_active_time += dt
        else:
            rate = self.config.turbo.boost_decay_rate
        
        boost_diff = target_boost - self.boost_pressure
        self.boost_pressure += boost_diff * rate * dt
        self.boost_pressure = max(0, min(self.config.turbo.max_boost_pressure, self.boost_pressure))
    
    def get_boost_multiplier(self) -> float:
        """Calculate power multiplier from boost"""
        if not self.config.turbo.enabled:
            return 1.0
        return 1.0 + (self.boost_pressure * self.config.turbo.power_multiplier_per_bar)
    
    def update_drs(self, velocity_ms: float, dt: float):
        """Update DRS state and deployment"""
        if not self.config.drs.enabled:
            self.drs_active = False
            self.drs_deployment = 0.0
            return
        
        velocity_kmh = velocity_ms * 3.6
        should_activate = velocity_kmh >= self.config.drs.min_activation_speed
        
        if should_activate and not self.drs_active:
            self.drs_active = True
        elif not should_activate and self.drs_active:
            self.drs_active = False
        
        # Smooth deployment/retraction
        if self.drs_active:
            self.drs_deployment = min(1.0, self.drs_deployment + dt / self.config.drs.activation_delay)
        else:
            self.drs_deployment = max(0.0, self.drs_deployment - dt / self.config.drs.deactivation_delay)
    
    def get_effective_drag_coefficient(self) -> float:
        """Get current drag coefficient with DRS"""
        base_cd = self.vehicle.drag_coefficient
        if self.config.drs.enabled and self.drs_deployment > 0:
            reduction = self.config.drs.drag_reduction * self.drs_deployment
            return base_cd * (1.0 - reduction)
        return base_cd * self.config.aerodynamics.drag_multiplier
    
    def update_fuel(self, rpm: float, throttle: float, dt: float):
        """Update fuel consumption"""
        if not self.config.fuel.enabled:
            return
        
        # Calculate consumption rate based on RPM and throttle
        rpm_factor = rpm / self.vehicle.redline_rpm
        
        if throttle > 0.9:
            rate_per_hour = self.config.fuel.consumption_rate_full_throttle
        elif throttle > 0.3:
            rate_per_hour = self.config.fuel.consumption_rate_cruise
        else:
            rate_per_hour = self.config.fuel.consumption_rate_idle
        
        # Adjust by RPM
        rate_per_hour *= (0.5 + 0.5 * rpm_factor)
        
        # Convert to kg/s and apply
        rate_per_second = rate_per_hour / 3600
        self.current_fuel_kg -= rate_per_second * dt
        self.current_fuel_kg = max(0, self.current_fuel_kg)
    
    def update_battery(self, power_kw: float, dt: float):
        """Update hybrid battery state of charge"""
        if not self.config.hybrid.enable_battery_soc:
            return
        
        # Power draw in kWh
        energy_used_kwh = (power_kw / 1000) * (dt / 3600)
        
        # Update SOC
        soc_change = energy_used_kwh / self.config.hybrid.battery_capacity_kwh
        self.battery_soc -= soc_change
        self.battery_soc = max(self.config.hybrid.min_battery_reserve, min(1.0, self.battery_soc))
    
    def interpolate_torque(self, rpm: float) -> float:
        """Interpolate engine torque from curve"""
        curve = self.vehicle.torque_curve
        
        if rpm <= curve[0].rpm:
            return curve[0].torque
        if rpm >= curve[-1].rpm:
            return curve[-1].torque * 0.95  # Power loss at redline
        
        for i in range(len(curve) - 1):
            if curve[i].rpm <= rpm <= curve[i + 1].rpm:
                t1, torque1 = curve[i].rpm, curve[i].torque
                t2, torque2 = curve[i + 1].rpm, curve[i + 1].torque
                ratio = (rpm - t1) / (t2 - t1)
                return torque1 + ratio * (torque2 - torque1)
        
        return curve[-1].torque
    
    def calculate_electric_torque(self, velocity_ms: float) -> float:
        """Calculate electric motor torque with battery SOC"""
        if not self.vehicle.electric_torque_nm:
            return 0.0
        
        velocity_kmh = velocity_ms * 3.6
        max_speed = self.vehicle.electric_max_speed_kmh or 200
        
        if velocity_kmh >= max_speed:
            return 0.0
        
        # Base taper
        taper_start = max_speed * 0.5
        if velocity_kmh <= taper_start:
            torque = self.vehicle.electric_torque_nm
        else:
            taper_ratio = ((max_speed - velocity_kmh) / (max_speed - taper_start)) ** 1.5
            torque = self.vehicle.electric_torque_nm * taper_ratio
        
        # Apply battery SOC limitation
        if self.config.hybrid.enable_battery_soc:
            if self.battery_soc < self.config.hybrid.min_battery_reserve:
                torque = 0.0
            elif self.battery_soc < 0.3:
                torque *= (self.battery_soc - self.config.hybrid.min_battery_reserve) / \
                         (0.3 - self.config.hybrid.min_battery_reserve)
        
        return torque * self.config.hybrid.motor_efficiency
    
    def calculate_rpm_from_velocity(self, velocity_ms: float, gear: int) -> float:
        """Calculate engine RPM for velocity and gear"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return self.vehicle.idle_rpm
        
        if velocity_ms < 0.01:
            return self.vehicle.idle_rpm
        
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        rpm = (velocity_ms * 60 * total_ratio) / (2 * math.pi * self.vehicle.tire_radius)
        
        # Add clutch slip during shifts
        if self.is_shifting:
            slip = 1.0 + (self.shift_time_remaining / self.config.gearbox.shift_duration) * \
                   self.config.gearbox.clutch_slip
            rpm *= slip
        
        return max(self.vehicle.idle_rpm, rpm)
    
    def should_shift_up(self, rpm: float, gear: int, velocity_ms: float) -> bool:
        """Determine if should upshift"""
        if gear >= len(self.vehicle.gear_ratios) or self.is_shifting:
            return False
        
        shift_velocity = self.shift_velocities[gear - 1]
        
        if velocity_ms >= shift_velocity:
            next_gear = gear + 1
            next_rpm = self.calculate_rpm_from_velocity(velocity_ms, next_gear)
            min_rpm = self.vehicle.redline_rpm * self.config.gearbox.min_rpm_after_shift
            
            if next_rpm >= min_rpm:
                return True
        
        return False
    
    def select_gear(self, velocity_ms: float, current_gear: int, current_rpm: float) -> int:
        """Select optimal gear"""
        if velocity_ms < 1.0:
            return 1
        
        if self.should_shift_up(current_rpm, current_gear, velocity_ms):
            self.is_shifting = True
            self.shift_time_remaining = self.config.gearbox.shift_duration
            return min(current_gear + 1, len(self.vehicle.gear_ratios))
        
        return current_gear
    
    def calculate_wheel_torque(self, rpm: float, gear: int, velocity_ms: float) -> float:
        """Calculate torque at wheels"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return 0.0
        
        # Engine torque
        engine_torque = self.interpolate_torque(rpm)
        
        # Apply boost
        engine_torque *= self.get_boost_multiplier()
        
        # Electric torque
        electric_torque = self.calculate_electric_torque(velocity_ms)
        
        # Combined
        combined_torque = engine_torque + electric_torque
        
        # Gear multiplication
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        
        # Transmission efficiency
        efficiency = self.vehicle.transmission_efficiency
        if self.is_shifting:
            efficiency *= (1.0 - self.config.gearbox.shift_power_loss)
        
        return combined_torque * total_ratio * efficiency
    
    def calculate_forces(self, velocity_ms: float, gear: int, rpm: float, acceleration: float) -> Tuple[float, float, float]:
        """Calculate all forces"""
        # Drive force
        wheel_torque = self.calculate_wheel_torque(rpm, gear, velocity_ms)
        drive_force = wheel_torque / self.vehicle.tire_radius
        
        # Limit by traction
        max_traction = self.calculate_max_traction_force(velocity_ms, acceleration)
        drive_force = min(drive_force, max_traction)
        
        # Drag with DRS
        effective_cd = self.get_effective_drag_coefficient()
        drag_force = 0.5 * self.air_density * effective_cd * \
                     self.vehicle.frontal_area * velocity_ms ** 2
        
        # Rolling resistance
        rolling_resistance = self.vehicle.rolling_resistance_coef * \
                           self.get_current_mass() * self.GRAVITY
        
        return drive_force, drag_force, rolling_resistance
    
    def simulate_step(self, velocity_ms: float, gear: int, dt: float) -> Tuple[float, float, int, float]:
        """Main simulation step"""
        # Handle gear shifting
        if self.is_shifting:
            self.shift_time_remaining -= dt
            if self.shift_time_remaining <= 0:
                self.is_shifting = False
                self.shift_time_remaining = 0
        
        # Launch control
        launch_active, launch_rpm = self.simulate_launch_control(velocity_ms, dt)
        
        if launch_active:
            rpm = launch_rpm
            gear = 1
        else:
            rpm = self.calculate_rpm_from_velocity(velocity_ms, gear)
            new_gear = self.select_gear(velocity_ms, gear, rpm)
            if new_gear != gear:
                rpm = self.calculate_rpm_from_velocity(velocity_ms, new_gear)
                gear = new_gear
        
        # Update systems
        self.update_turbo_boost(rpm, 1.0, dt)
        self.update_drs(velocity_ms, dt)
        self.update_fuel(rpm, 1.0, dt)
        
        # Calculate forces
        drive_force, drag_force, rolling_resistance = self.calculate_forces(
            velocity_ms, gear, rpm, 0.0
        )
        
        # Acceleration
        current_mass = self.get_current_mass()
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / current_mass
        
        # Recalculate with proper weight transfer
        drive_force, drag_force, rolling_resistance = self.calculate_forces(
            velocity_ms, gear, rpm, acceleration
        )
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / current_mass
        
        # Update states
        self.update_tire_temperature(acceleration, velocity_ms, dt)
        self.tire_wear += self.config.tires.wear_rate * dt
        
        # Update velocity
        new_velocity = velocity_ms + acceleration * dt
        new_velocity = max(0, new_velocity)
        
        return new_velocity, acceleration, gear, rpm
    
    def run_simulation(self, timestep: float = 0.01, max_time: float = 30.0,
                      target_distance: float = None, start_velocity: float = 0.0) -> List[TimeSnapshot]:
        """Run complete simulation"""
        snapshots = []
        
        time = 0.0
        distance = 0.0
        velocity = start_velocity
        gear = 1 if start_velocity == 0.0 else self._get_gear_for_velocity(start_velocity)
        
        # Reset state
        self._initialize_state()
        if start_velocity > 0:
            self.launch_control_active = False
        
        while time <= max_time:
            # Simulate
            new_velocity, acceleration, new_gear, rpm = self.simulate_step(velocity, gear, timestep)
            
            # Update distance
            avg_velocity = (velocity + new_velocity) / 2
            distance += avg_velocity * timestep
            
            # Update state
            velocity = new_velocity
            gear = new_gear
            
            # Calculate power
            drive_force, drag_force, rolling_resistance = self.calculate_forces(velocity, gear, rpm, acceleration)
            power_kw = (drive_force * velocity) / 1000
            
            # Record snapshot
            snapshot = TimeSnapshot(
                time=round(time, 3),
                distance=round(distance, 2),
                velocity=round(velocity, 2),
                acceleration=round(acceleration, 3),
                gear=gear,
                rpm=round(rpm, 0),
                power_kw=round(power_kw, 1)
            )
            snapshots.append(snapshot)
            
            time += timestep
            
            # Check if fuel ran out
            if self.config.fuel.enabled and self.current_fuel_kg <= 0:
                break
            
            if target_distance is not None and distance >= target_distance:
                break
        
        return snapshots
    
    def _get_gear_for_velocity(self, velocity_ms: float) -> int:
        """Determine appropriate starting gear"""
        if velocity_ms < 1.0:
            return 1
        
        for gear_num in range(1, len(self.vehicle.gear_ratios) + 1):
            rpm = self.calculate_rpm_from_velocity(velocity_ms, gear_num)
            if self.vehicle.redline_rpm * 0.50 <= rpm <= self.vehicle.redline_rpm * 0.90:
                return gear_num
        
        return len(self.vehicle.gear_ratios)
