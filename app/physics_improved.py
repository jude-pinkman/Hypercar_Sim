import math
from typing import List, Tuple, Optional
from app.models import Vehicle, EnvironmentConditions, TimeSnapshot


class ImprovedPhysicsEngine:
    """
    Advanced physics simulation engine with realistic hypercar dynamics
    
    Improvements over basic physics:
    - Tire slip and grip modeling with temperature effects
    - Weight transfer during acceleration and cornering
    - Launch control system simulation
    - Turbo lag and boost dynamics
    - DRS (Drag Reduction System) simulation
    - Tire wear over time
    - Realistic clutch slip during gear changes
    - Power loss at high RPM due to air resistance in intake
    - Variable rolling resistance based on speed
    - More accurate gear shift timing with shift duration
    """
    
    # Physical constants
    GRAVITY = 9.81  # m/s²
    AIR_GAS_CONSTANT = 287.05  # J/(kg·K)
    
    def __init__(self, vehicle: Vehicle, environment: EnvironmentConditions):
        self.vehicle = vehicle
        self.environment = environment
        self.air_density = self._calculate_air_density()
        
        # Tire physics state
        self.tire_temp = 25.0  # °C - starts at ambient
        self.optimal_tire_temp = 85.0  # °C - peak grip temperature
        self.tire_wear = 0.0  # 0 to 1.0 (1.0 = completely worn)
        
        # Launch control state
        self.launch_control_active = True
        self.launch_rpm_target = self.vehicle.redline_rpm * 0.65  # Hold at 65% redline
        self.launch_completed = False
        
        # Turbo/boost state (for turbocharged engines)
        self.boost_pressure = 0.0  # Bar
        self.max_boost = 2.0  # Bar - typical for hypercars
        self.turbo_spool_rate = 3.0  # Bar/s
        
        # DRS (Drag Reduction System) state
        self.drs_available = True
        self.drs_active = False
        self.drs_min_speed = 150 / 3.6  # 150 km/h minimum for DRS activation
        self.drs_drag_reduction = 0.15  # 15% drag reduction when active
        
        # Gear shift state
        self.is_shifting = False
        self.shift_time_remaining = 0.0
        self.shift_duration = 0.15  # 150ms shift time (DCT/Sequential)
        
        # Weight transfer
        self.weight_on_rear_wheels = 0.5  # Proportion (0.5 = 50% weight distribution)
        self.base_weight_distribution = 0.4  # Base 40% front, 60% rear (typical mid-engine)
        
        # Pre-calculate optimal shift points
        self.shift_velocities = self._calculate_shift_velocities()
        
    def _calculate_air_density(self) -> float:
        """Calculate air density based on temperature, altitude, and humidity"""
        temp_kelvin = self.environment.temperature_celsius + 273.15
        pressure_pa = self.environment.air_pressure_kpa * 1000
        
        # Adjust pressure for altitude (barometric formula)
        altitude_m = self.environment.altitude_meters
        pressure_pa *= math.exp(-altitude_m / 8400)
        
        # Ideal gas law: ρ = P / (R * T)
        density = pressure_pa / (self.AIR_GAS_CONSTANT * temp_kelvin)
        
        # Humidity reduces air density slightly (moist air is less dense)
        # Assuming 50% relative humidity at sea level
        humidity_factor = 0.98
        density *= humidity_factor
        
        return density
    
    def _calculate_shift_velocities(self) -> List[float]:
        """Calculate optimal shift velocities with real hypercar shift logic"""
        shift_velocities_ms = []
        
        for i in range(len(self.vehicle.gear_ratios) - 1):
            # Variable shift point based on power band optimization
            if i == 0:  # 1st gear - shift early to avoid wheelspin
                shift_rpm = self.vehicle.redline_rpm * 0.68
            elif i == 1:  # 2nd gear
                shift_rpm = self.vehicle.redline_rpm * 0.72
            elif i == 2:  # 3rd gear
                shift_rpm = self.vehicle.redline_rpm * 0.76
            elif i == 3:  # 4th gear
                shift_rpm = self.vehicle.redline_rpm * 0.78
            elif i == 4:  # 5th gear
                shift_rpm = self.vehicle.redline_rpm * 0.81
            else:  # 6th+ gear
                shift_rpm = self.vehicle.redline_rpm * 0.84
            
            gear_ratio = self.vehicle.gear_ratios[i]
            total_ratio = gear_ratio * self.vehicle.final_drive
            shift_velocity = (shift_rpm * 2 * math.pi * self.vehicle.tire_radius) / (60 * total_ratio)
            shift_velocities_ms.append(shift_velocity)
        
        # Last gear - shift at 95% redline
        last_gear_ratio = self.vehicle.gear_ratios[-1]
        last_total_ratio = last_gear_ratio * self.vehicle.final_drive
        last_shift_velocity = (self.vehicle.redline_rpm * 0.95 * 2 * math.pi * self.vehicle.tire_radius) / (60 * last_total_ratio)
        shift_velocities_ms.append(last_shift_velocity)
        
        return shift_velocities_ms
    
    def update_tire_temperature(self, acceleration: float, velocity_ms: float, dt: float):
        """Update tire temperature based on usage"""
        # Tire heating from acceleration (slip)
        if acceleration > 2.0:
            heating_rate = (acceleration - 2.0) * 2.0
            self.tire_temp += heating_rate * dt
        
        # Tire heating from speed (friction)
        speed_heating = (velocity_ms / 100) * 0.5
        self.tire_temp += speed_heating * dt
        
        # Cooling towards ambient
        cooling_rate = (self.tire_temp - self.environment.temperature_celsius) * 0.02
        self.tire_temp -= cooling_rate * dt
        
        # Clamp temperature
        self.tire_temp = max(self.environment.temperature_celsius, min(150, self.tire_temp))
    
    def get_tire_grip_factor(self) -> float:
        """
        Calculate tire grip multiplier based on temperature
        Cold tires = reduced grip, optimal temp = maximum grip, overheated = reduced grip
        """
        temp_diff = abs(self.tire_temp - self.optimal_tire_temp)
        
        if temp_diff < 5:
            # Within 5°C of optimal - full grip
            return 1.0
        elif temp_diff < 20:
            # Slightly off optimal
            return 1.0 - (temp_diff - 5) * 0.015
        else:
            # Significantly off optimal
            return max(0.7, 1.0 - (temp_diff * 0.02))
    
    def calculate_weight_transfer(self, acceleration: float) -> float:
        """
        Calculate weight transfer to rear wheels during acceleration
        Returns: proportion of weight on rear wheels (0.5 = even, 0.7 = 70% rear)
        """
        # Weight transfer: ΔW = (m * a * h) / (g * L)
        # Where h = center of gravity height, L = wheelbase
        # Approximation: higher acceleration = more weight on rear
        
        # Base distribution (mid-engine is ~40% front, 60% rear)
        base_rear = 0.6
        
        # Transfer coefficient (depends on CG height and wheelbase)
        transfer_coef = 0.15  # Typical for low-CG hypercars
        
        # Calculate additional rear weight from acceleration
        accel_g = acceleration / self.GRAVITY
        weight_transfer = accel_g * transfer_coef
        
        # Clamp to realistic limits
        rear_weight = base_rear + weight_transfer
        return max(0.4, min(0.85, rear_weight))
    
    def calculate_max_traction_force(self, velocity_ms: float, acceleration: float) -> float:
        """
        Calculate maximum traction force based on tire grip and weight transfer
        This limits acceleration to realistic levels
        """
        # Get tire grip factor
        grip_factor = self.get_tire_grip_factor()
        
        # Calculate weight transfer
        rear_weight_proportion = self.calculate_weight_transfer(acceleration)
        
        # Weight on driven wheels (assuming RWD/AWD)
        # For hypercars, most are RWD or AWD. Assuming 100% power to rear or split
        driven_weight = self.vehicle.mass * rear_weight_proportion * self.GRAVITY
        
        # Tire coefficient of friction (μ)
        # Peak μ for race tires: ~1.4, Sport tires: ~1.2
        base_mu = 1.3  # High-performance tire
        
        # μ decreases slightly with speed (hydroplaning risk)
        speed_factor = max(0.85, 1.0 - (velocity_ms / 200))
        
        # Wear reduces grip
        wear_factor = 1.0 - (self.tire_wear * 0.3)
        
        effective_mu = base_mu * grip_factor * speed_factor * wear_factor
        
        # Maximum traction force: F = μ * N
        max_traction = effective_mu * driven_weight
        
        return max_traction
    
    def simulate_launch_control(self, velocity_ms: float, dt: float) -> Tuple[bool, float]:
        """
        Simulate launch control system for standing starts
        Returns: (still_active, target_rpm)
        """
        if not self.launch_control_active or self.launch_completed:
            return False, 0.0
        
        # Launch control stays active until wheels start moving significantly
        if velocity_ms > 5.0:  # ~18 km/h - clutch is fully engaged
            self.launch_completed = True
            self.launch_control_active = False
            return False, 0.0
        
        # Hold RPM at launch target with slight variation for realism
        rpm_variation = math.sin(dt * 50) * 50  # Small oscillation
        target_rpm = self.launch_rpm_target + rpm_variation
        
        return True, target_rpm
    
    def update_turbo_boost(self, rpm: float, throttle_position: float, dt: float):
        """Update turbo boost pressure based on RPM and throttle"""
        # Boost builds with RPM and throttle position
        target_boost = (rpm / self.vehicle.redline_rpm) * throttle_position * self.max_boost
        
        # Spool up or down towards target
        boost_diff = target_boost - self.boost_pressure
        boost_change = boost_diff * self.turbo_spool_rate * dt
        
        self.boost_pressure += boost_change
        self.boost_pressure = max(0, min(self.max_boost, self.boost_pressure))
    
    def get_boost_multiplier(self) -> float:
        """Calculate power multiplier from turbo boost"""
        # Each bar of boost adds approximately 10-15% power
        return 1.0 + (self.boost_pressure * 0.12)
    
    def update_drs(self, velocity_ms: float, is_straight: bool = True):
        """Update DRS state based on conditions"""
        velocity_kmh = velocity_ms * 3.6
        
        if velocity_kmh >= self.drs_min_speed and is_straight and self.drs_available:
            self.drs_active = True
        else:
            self.drs_active = False
    
    def get_effective_drag_coefficient(self) -> float:
        """Get current drag coefficient considering DRS"""
        if self.drs_active:
            return self.vehicle.drag_coefficient * (1.0 - self.drs_drag_reduction)
        return self.vehicle.drag_coefficient
    
    def interpolate_torque(self, rpm: float) -> float:
        """Interpolate engine torque with high-RPM power loss"""
        curve = self.vehicle.torque_curve
        
        if rpm <= curve[0].rpm:
            return curve[0].torque
        if rpm >= curve[-1].rpm:
            # Power loss at extreme high RPM
            return curve[-1].torque * 0.95
        
        # Linear interpolation
        for i in range(len(curve) - 1):
            if curve[i].rpm <= rpm <= curve[i + 1].rpm:
                t1, torque1 = curve[i].rpm, curve[i].torque
                t2, torque2 = curve[i + 1].rpm, curve[i + 1].torque
                ratio = (rpm - t1) / (t2 - t1)
                return torque1 + ratio * (torque2 - torque1)
        
        return curve[-1].torque
    
    def calculate_electric_torque(self, velocity_ms: float) -> float:
        """Calculate electric motor torque with realistic taper"""
        if not self.vehicle.electric_torque_nm or not self.vehicle.electric_max_speed_kmh:
            return 0.0
        
        velocity_kmh = velocity_ms * 3.6
        max_speed = self.vehicle.electric_max_speed_kmh
        
        if velocity_kmh >= max_speed:
            return 0.0
        
        # More realistic taper curve for electric motors
        taper_start = max_speed * 0.5
        if velocity_kmh <= taper_start:
            return self.vehicle.electric_torque_nm
        else:
            # Exponential taper for realistic motor characteristics
            taper_ratio = ((max_speed - velocity_kmh) / (max_speed - taper_start)) ** 1.5
            return self.vehicle.electric_torque_nm * max(0, taper_ratio)
    
    def calculate_rpm_from_velocity(self, velocity_ms: float, gear: int) -> float:
        """Calculate engine RPM considering clutch slip during shifts"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return self.vehicle.idle_rpm
        
        if velocity_ms < 0.01:
            return self.vehicle.idle_rpm
        
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        rpm = (velocity_ms * 60 * total_ratio) / (2 * math.pi * self.vehicle.tire_radius)
        
        # Add clutch slip during shifts
        if self.is_shifting:
            slip_factor = 1.0 + (self.shift_time_remaining / self.shift_duration) * 0.15
            rpm *= slip_factor
        
        return max(self.vehicle.idle_rpm, rpm)
    
    def should_shift_up(self, rpm: float, gear: int, velocity_ms: float) -> bool:
        """Determine shift point with improved logic"""
        if gear >= len(self.vehicle.gear_ratios) or self.is_shifting:
            return False
        
        shift_velocity = self.shift_velocities[gear - 1]
        
        if velocity_ms >= shift_velocity:
            next_gear = gear + 1
            next_rpm = self.calculate_rpm_from_velocity(velocity_ms, next_gear)
            min_rpm = self.vehicle.redline_rpm * 0.52  # Don't drop below 52%
            
            if next_rpm >= min_rpm:
                return True
        
        return False
    
    def select_gear(self, velocity_ms: float, current_gear: int, current_rpm: float) -> int:
        """Select optimal gear with shift timing"""
        if velocity_ms < 1.0:
            return 1
        
        if self.should_shift_up(current_rpm, current_gear, velocity_ms):
            # Initiate shift
            self.is_shifting = True
            self.shift_time_remaining = self.shift_duration
            return min(current_gear + 1, len(self.vehicle.gear_ratios))
        
        return current_gear
    
    def calculate_wheel_torque(self, rpm: float, gear: int, velocity_ms: float) -> float:
        """Calculate wheel torque with all realistic factors"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return 0.0
        
        # Base engine torque
        engine_torque = self.interpolate_torque(rpm)
        
        # Apply boost multiplier
        boost_mult = self.get_boost_multiplier()
        engine_torque *= boost_mult
        
        # Electric torque
        electric_torque = self.calculate_electric_torque(velocity_ms)
        
        # Combined torque
        combined_torque = engine_torque + electric_torque
        
        # Gear multiplication
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        
        # Transmission efficiency (reduced during shifts)
        efficiency = self.vehicle.transmission_efficiency
        if self.is_shifting:
            efficiency *= 0.7  # 30% power loss during shift
        
        wheel_torque = combined_torque * total_ratio * efficiency
        
        return wheel_torque
    
    def calculate_rolling_resistance(self, velocity_ms: float) -> float:
        """Calculate speed-dependent rolling resistance"""
        # Base rolling resistance
        base_rr = self.vehicle.rolling_resistance_coef * self.vehicle.mass * self.GRAVITY
        
        # Rolling resistance increases slightly with speed (tire deformation)
        speed_factor = 1.0 + (velocity_ms / 100) * 0.15
        
        return base_rr * speed_factor
    
    def calculate_forces(self, velocity_ms: float, gear: int, rpm: float, acceleration: float) -> Tuple[float, float, float]:
        """Calculate all forces with improved realism"""
        # Drive force
        wheel_torque = self.calculate_wheel_torque(rpm, gear, velocity_ms)
        drive_force = wheel_torque / self.vehicle.tire_radius
        
        # Limit by traction
        max_traction = self.calculate_max_traction_force(velocity_ms, acceleration)
        drive_force = min(drive_force, max_traction)
        
        # Aerodynamic drag with DRS
        effective_cd = self.get_effective_drag_coefficient()
        drag_force = 0.5 * self.air_density * effective_cd * \
                     self.vehicle.frontal_area * velocity_ms ** 2
        
        # Speed-dependent rolling resistance
        rolling_resistance = self.calculate_rolling_resistance(velocity_ms)
        
        return drive_force, drag_force, rolling_resistance
    
    def simulate_step(self, velocity_ms: float, gear: int, dt: float) -> Tuple[float, float, int, float]:
        """
        Enhanced physics simulation step
        Returns: (new_velocity, acceleration, new_gear, rpm)
        """
        # Handle shift timing
        if self.is_shifting:
            self.shift_time_remaining -= dt
            if self.shift_time_remaining <= 0:
                self.is_shifting = False
                self.shift_time_remaining = 0
        
        # Launch control for standing starts
        launch_active, launch_rpm = self.simulate_launch_control(velocity_ms, dt)
        
        if launch_active:
            # During launch control, hold at target RPM
            rpm = launch_rpm
            gear = 1
        else:
            # Normal operation
            rpm = self.calculate_rpm_from_velocity(velocity_ms, gear)
            new_gear = self.select_gear(velocity_ms, gear, rpm)
            
            if new_gear != gear:
                rpm = self.calculate_rpm_from_velocity(velocity_ms, new_gear)
                gear = new_gear
        
        # Update turbo boost (assuming full throttle)
        self.update_turbo_boost(rpm, 1.0, dt)
        
        # Update DRS
        self.update_drs(velocity_ms, is_straight=True)
        
        # Calculate forces (pass previous acceleration for weight transfer)
        drive_force, drag_force, rolling_resistance = self.calculate_forces(
            velocity_ms, gear, rpm, 0.0  # Use 0 for first iteration
        )
        
        # Net force and acceleration
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / self.vehicle.mass
        
        # Recalculate with proper weight transfer
        drive_force, drag_force, rolling_resistance = self.calculate_forces(
            velocity_ms, gear, rpm, acceleration
        )
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / self.vehicle.mass
        
        # Update tire temperature
        self.update_tire_temperature(acceleration, velocity_ms, dt)
        
        # Update tire wear (very gradual)
        self.tire_wear += dt * 0.0001
        
        # Update velocity
        new_velocity = velocity_ms + acceleration * dt
        new_velocity = max(0, new_velocity)
        
        return new_velocity, acceleration, gear, rpm
    
    def run_simulation(self, timestep: float = 0.01, max_time: float = 30.0, 
                       target_distance: float = None, start_velocity: float = 0.0) -> List[TimeSnapshot]:
        """
        Run complete simulation with improved physics
        """
        snapshots = []
        
        time = 0.0
        distance = 0.0
        velocity = start_velocity
        gear = 1 if start_velocity == 0.0 else self._get_gear_for_velocity(start_velocity)
        
        # Reset state for new simulation
        self.launch_control_active = (start_velocity == 0.0)
        self.launch_completed = False
        self.tire_temp = self.environment.temperature_celsius + 10  # Tires warm up quickly
        self.tire_wear = 0.0
        self.boost_pressure = 0.0
        
        while time <= max_time:
            # Simulate step
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
            
            if target_distance is not None and distance >= target_distance:
                break
        
        return snapshots
    
    def _get_gear_for_velocity(self, velocity_ms: float) -> int:
        """Determine appropriate starting gear for a given velocity"""
        if velocity_ms < 1.0:
            return 1
        
        for gear_num in range(1, len(self.vehicle.gear_ratios) + 1):
            rpm = self.calculate_rpm_from_velocity(velocity_ms, gear_num)
            if self.vehicle.redline_rpm * 0.50 <= rpm <= self.vehicle.redline_rpm * 0.90:
                return gear_num
        
        return len(self.vehicle.gear_ratios)


def calculate_performance_metrics(snapshots: List[TimeSnapshot]) -> dict:
    """Extract key performance metrics from simulation data"""
    metrics = {
        'time_to_100kmh': None,
        'time_to_200kmh': None,
        'quarter_mile_time': None,
        'quarter_mile_speed': None,
    }
    
    for snapshot in snapshots:
        velocity_kmh = snapshot.velocity * 3.6
        
        if metrics['time_to_100kmh'] is None and velocity_kmh >= 100:
            metrics['time_to_100kmh'] = round(snapshot.time, 2)
        
        if metrics['time_to_200kmh'] is None and velocity_kmh >= 200:
            metrics['time_to_200kmh'] = round(snapshot.time, 2)
        
        if metrics['quarter_mile_time'] is None and snapshot.distance >= 402.336:
            metrics['quarter_mile_time'] = round(snapshot.time, 2)
            metrics['quarter_mile_speed'] = round(velocity_kmh, 1)
    
    return metrics
