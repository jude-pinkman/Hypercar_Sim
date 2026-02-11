import math
from typing import List, Tuple, Optional
from app.models import Vehicle, EnvironmentConditions, TimeSnapshot


class PhysicsEngine:
    """Core physics simulation engine for vehicle dynamics"""
    
    # Physical constants
    GRAVITY = 9.81  # m/s²
    AIR_GAS_CONSTANT = 287.05  # J/(kg·K)
    
    def __init__(self, vehicle: Vehicle, environment: EnvironmentConditions):
        self.vehicle = vehicle
        self.environment = environment
        self.air_density = self._calculate_air_density()
        
        # Pre-calculate optimal shift points for each gear based on velocity
        self.shift_velocities = self._calculate_shift_velocities()
        
    def _calculate_air_density(self) -> float:
        """Calculate air density based on temperature and altitude"""
        temp_kelvin = self.environment.temperature_celsius + 273.15
        pressure_pa = self.environment.air_pressure_kpa * 1000
        
        # Adjust pressure for altitude (simplified barometric formula)
        altitude_m = self.environment.altitude_meters
        pressure_pa *= math.exp(-altitude_m / 8400)
        
        # Ideal gas law: ρ = P / (R * T)
        return pressure_pa / (self.AIR_GAS_CONSTANT * temp_kelvin)
    
    def _calculate_shift_velocities(self) -> List[float]:
        """
        Calculate shift velocities based on real hypercar behavior
        
        These are empirically determined from actual drag race videos and manufacturer data
        Hypercars shift at specific speeds to maintain optimal power delivery
        """
        shift_velocities_ms = []
        
        # Base shift strategy on gear ratios and optimal powerband usage
        # Real hypercars shift at 65-75% of redline for lower gears
        # and progressively higher (75-85%) for upper gears
        
        for i in range(len(self.vehicle.gear_ratios) - 1):
            # Calculate optimal shift speed for this gear
            # Lower gears: shift at 67-70% redline
            # Middle gears: shift at 70-75% redline  
            # Upper gears: shift at 75-82% redline
            
            if i == 0:  # 1st gear
                shift_rpm = self.vehicle.redline_rpm * 0.68
            elif i == 1:  # 2nd gear
                shift_rpm = self.vehicle.redline_rpm * 0.70
            elif i == 2:  # 3rd gear
                shift_rpm = self.vehicle.redline_rpm * 0.73
            elif i == 3:  # 4th gear
                shift_rpm = self.vehicle.redline_rpm * 0.76
            elif i == 4:  # 5th gear
                shift_rpm = self.vehicle.redline_rpm * 0.79
            else:  # 6th+ gear
                shift_rpm = self.vehicle.redline_rpm * 0.82
            
            # Convert RPM to velocity for this gear
            gear_ratio = self.vehicle.gear_ratios[i]
            total_ratio = gear_ratio * self.vehicle.final_drive
            
            # velocity = (rpm * 2π * tire_radius) / (60 * total_ratio)
            shift_velocity = (shift_rpm * 2 * math.pi * self.vehicle.tire_radius) / (60 * total_ratio)
            shift_velocities_ms.append(shift_velocity)
        
        # Last gear - shift at 95% redline (top speed run)
        last_gear_ratio = self.vehicle.gear_ratios[-1]
        last_total_ratio = last_gear_ratio * self.vehicle.final_drive
        last_shift_velocity = (self.vehicle.redline_rpm * 0.95 * 2 * math.pi * self.vehicle.tire_radius) / (60 * last_total_ratio)
        shift_velocities_ms.append(last_shift_velocity)
        
        return shift_velocities_ms
    
    def interpolate_torque(self, rpm: float) -> float:
        """Interpolate engine torque at given RPM from torque curve"""
        curve = self.vehicle.torque_curve
        
        # Clamp to curve bounds
        if rpm <= curve[0].rpm:
            return curve[0].torque
        if rpm >= curve[-1].rpm:
            return curve[-1].torque
        
        # Linear interpolation
        for i in range(len(curve) - 1):
            if curve[i].rpm <= rpm <= curve[i + 1].rpm:
                t1, torque1 = curve[i].rpm, curve[i].torque
                t2, torque2 = curve[i + 1].rpm, curve[i + 1].torque
                ratio = (rpm - t1) / (t2 - t1)
                return torque1 + ratio * (torque2 - torque1)
        
        return curve[-1].torque
    
    def calculate_electric_torque(self, velocity_ms: float) -> float:
        """Calculate electric motor torque contribution"""
        if not self.vehicle.electric_torque_nm or not self.vehicle.electric_max_speed_kmh:
            return 0.0
        
        velocity_kmh = velocity_ms * 3.6
        max_speed = self.vehicle.electric_max_speed_kmh
        
        # Electric motor tapers off at high speeds
        if velocity_kmh >= max_speed:
            return 0.0
        
        # Linear taper from 60% of max speed
        taper_start = max_speed * 0.6
        if velocity_kmh <= taper_start:
            return self.vehicle.electric_torque_nm
        else:
            taper_ratio = 1.0 - ((velocity_kmh - taper_start) / (max_speed - taper_start))
            return self.vehicle.electric_torque_nm * max(0, taper_ratio)
    
    def calculate_rpm_from_velocity(self, velocity_ms: float, gear: int) -> float:
        """Calculate engine RPM for given velocity and gear"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return self.vehicle.idle_rpm
        
        if velocity_ms < 0.01:
            return self.vehicle.idle_rpm
        
        # rpm = (velocity * 60 * gear_ratio * final_drive) / (2π * tire_radius)
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        
        rpm = (velocity_ms * 60 * total_ratio) / (2 * math.pi * self.vehicle.tire_radius)
        
        return max(self.vehicle.idle_rpm, rpm)
    
    def calculate_velocity_from_rpm(self, rpm: float, gear: int) -> float:
        """Calculate velocity for given RPM and gear"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return 0.0
        
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        
        # velocity = (rpm * 2π * tire_radius) / (60 * total_ratio)
        velocity_ms = (rpm * 2 * math.pi * self.vehicle.tire_radius) / (60 * total_ratio)
        
        return velocity_ms
    
    def should_shift_up(self, rpm: float, gear: int, velocity_ms: float) -> bool:
        """
        Determine if vehicle should shift to next gear based on velocity
        
        Uses pre-calculated shift velocities that match real hypercar behavior
        """
        if gear >= len(self.vehicle.gear_ratios):
            return False
        
        # Get optimal shift velocity for this gear
        shift_velocity = self.shift_velocities[gear - 1]
        
        # Check if we've reached shift velocity
        if velocity_ms >= shift_velocity:
            # Verify next gear won't bog the engine
            next_gear = gear + 1
            next_rpm = self.calculate_rpm_from_velocity(velocity_ms, next_gear)
            
            # Don't shift if it drops below 55% of redline
            min_rpm = self.vehicle.redline_rpm * 0.55
            
            if next_rpm >= min_rpm:
                return True
        
        return False
    
    def select_gear(self, velocity_ms: float, current_gear: int, current_rpm: float) -> int:
        """Select optimal gear based on velocity and RPM"""
        
        # Start from first gear if stopped or very slow
        if velocity_ms < 1.0:
            return 1
        
        # Check if we should shift up
        if self.should_shift_up(current_rpm, current_gear, velocity_ms):
            return min(current_gear + 1, len(self.vehicle.gear_ratios))
        
        # Don't downshift during acceleration
        return current_gear
    
    def calculate_wheel_torque(self, rpm: float, gear: int, velocity_ms: float) -> float:
        """Calculate torque at wheels including hybrid system"""
        if gear < 1 or gear > len(self.vehicle.gear_ratios):
            return 0.0
        
        # Engine torque from curve
        engine_torque = self.interpolate_torque(rpm)
        
        # Electric motor torque
        electric_torque = self.calculate_electric_torque(velocity_ms)
        
        # Combined torque at crank
        combined_torque = engine_torque + electric_torque
        
        # Multiply by gear ratio and final drive
        gear_ratio = self.vehicle.gear_ratios[gear - 1]
        total_ratio = gear_ratio * self.vehicle.final_drive
        
        # Apply transmission efficiency
        wheel_torque = combined_torque * total_ratio * self.vehicle.transmission_efficiency
        
        return wheel_torque
    
    def calculate_forces(self, velocity_ms: float, gear: int, rpm: float) -> Tuple[float, float, float]:
        """Calculate driving force and resistance forces"""
        
        # Driving force from wheel torque
        wheel_torque = self.calculate_wheel_torque(rpm, gear, velocity_ms)
        drive_force = wheel_torque / self.vehicle.tire_radius
        
        # Aerodynamic drag: F = 0.5 * ρ * Cd * A * v²
        drag_force = 0.5 * self.air_density * self.vehicle.drag_coefficient * \
                     self.vehicle.frontal_area * velocity_ms ** 2
        
        # Rolling resistance: F = Crr * m * g
        rolling_resistance = self.vehicle.rolling_resistance_coef * \
                           self.vehicle.mass * self.GRAVITY
        
        return drive_force, drag_force, rolling_resistance
    
    def simulate_step(self, velocity_ms: float, gear: int, dt: float) -> Tuple[float, float, int, float]:
        """
        Simulate one timestep
        Returns: (new_velocity, acceleration, new_gear, rpm)
        """
        # Calculate RPM for current gear and velocity
        rpm = self.calculate_rpm_from_velocity(velocity_ms, gear)
        
        # Determine if we should shift
        new_gear = self.select_gear(velocity_ms, gear, rpm)
        
        # Recalculate RPM if gear changed
        if new_gear != gear:
            rpm = self.calculate_rpm_from_velocity(velocity_ms, new_gear)
        
        # Calculate forces
        drive_force, drag_force, rolling_resistance = self.calculate_forces(velocity_ms, new_gear, rpm)
        
        # Net force and acceleration
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / self.vehicle.mass
        
        # Limit acceleration to realistic traction limits (approx 1.3g for hypercars with launch control)
        max_acceleration = 1.3 * self.GRAVITY
        acceleration = min(acceleration, max_acceleration)
        
        # Update velocity (simple Euler integration)
        new_velocity = velocity_ms + acceleration * dt
        new_velocity = max(0, new_velocity)  # Prevent negative velocity
        
        return new_velocity, acceleration, new_gear, rpm
    
    def run_simulation(self, timestep: float = 0.01, max_time: float = 30.0, target_distance: float = None, start_velocity: float = 0.0) -> List[TimeSnapshot]:
        """
        Run complete drag race simulation
        
        Args:
            timestep: Simulation time step in seconds
            max_time: Maximum simulation time
            target_distance: Target distance in meters (None = run until max_time)
            start_velocity: Starting velocity in m/s (for roll races)
        
        Returns list of snapshots over time
        """
        snapshots = []
        
        time = 0.0
        distance = 0.0
        velocity = start_velocity  # Use start_velocity parameter
        gear = 1 if start_velocity == 0.0 else self._get_gear_for_velocity(start_velocity)
        
        while time <= max_time:
            # Simulate one step
            new_velocity, acceleration, new_gear, rpm = self.simulate_step(velocity, gear, timestep)
            
            # Update distance (use average velocity over timestep)
            avg_velocity = (velocity + new_velocity) / 2
            distance += avg_velocity * timestep
            
            # Update state
            velocity = new_velocity
            gear = new_gear
            
            # Calculate power (P = F * v)
            drive_force, drag_force, rolling_resistance = self.calculate_forces(velocity, gear, rpm)
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
            
            # Stop if we've reached target distance (if specified)
            if target_distance is not None and distance >= target_distance:
                break
        
        return snapshots
    
    def _get_gear_for_velocity(self, velocity_ms: float) -> int:
        """Determine appropriate starting gear for a given velocity"""
        if velocity_ms < 1.0:
            return 1
        
        # Find the gear where this velocity is within the operating range
        for gear_num in range(1, len(self.vehicle.gear_ratios) + 1):
            rpm = self.calculate_rpm_from_velocity(velocity_ms, gear_num)
            # Use gear if RPM is between 50% and 95% of redline
            if self.vehicle.redline_rpm * 0.50 <= rpm <= self.vehicle.redline_rpm * 0.95:
                return gear_num
        
        # Default to highest gear if velocity is very high
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
        
        # 0-100 km/h
        if metrics['time_to_100kmh'] is None and velocity_kmh >= 100:
            metrics['time_to_100kmh'] = round(snapshot.time, 2)
        
        # 0-200 km/h
        if metrics['time_to_200kmh'] is None and velocity_kmh >= 200:
            metrics['time_to_200kmh'] = round(snapshot.time, 2)
        
        # Quarter mile (402.336 meters)
        if metrics['quarter_mile_time'] is None and snapshot.distance >= 402.336:
            metrics['quarter_mile_time'] = round(snapshot.time, 2)
            metrics['quarter_mile_speed'] = round(velocity_kmh, 1)
    
    return metrics