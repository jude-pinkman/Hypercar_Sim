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
        
        # Pre-calculate optimal shift points for each gear
        self.shift_points = self._calculate_shift_points()
        
    def _calculate_air_density(self) -> float:
        """Calculate air density based on temperature and altitude"""
        temp_kelvin = self.environment.temperature_celsius + 273.15
        pressure_pa = self.environment.air_pressure_kpa * 1000
        
        # Adjust pressure for altitude (simplified barometric formula)
        altitude_m = self.environment.altitude_meters
        pressure_pa *= math.exp(-altitude_m / 8400)
        
        # Ideal gas law: ρ = P / (R * T)
        return pressure_pa / (self.AIR_GAS_CONSTANT * temp_kelvin)
    
    def _calculate_shift_points(self) -> List[float]:
        """
        Calculate optimal shift RPM for each gear based on power curves
        
        Optimal shift point is where power in next gear at post-shift RPM
        equals power in current gear at current RPM
        
        Formula: shift_rpm_current = shift_rpm_next * (gear_ratio_next / gear_ratio_current)
        """
        shift_points = []
        
        for i in range(len(self.vehicle.gear_ratios) - 1):
            current_gear_ratio = self.vehicle.gear_ratios[i]
            next_gear_ratio = self.vehicle.gear_ratios[i + 1]
            
            # Calculate ratio between gears
            gear_ratio_factor = current_gear_ratio / next_gear_ratio
            
            # For optimal acceleration, shift when the power after shifting
            # to next gear equals current power
            # This typically happens around 85-92% of redline for modern performance cars
            # depending on torque curve shape
            
            # Find the RPM where torque * RPM (power) in current gear at shift RPM
            # equals torque * RPM in next gear at (shift_RPM / gear_ratio_factor)
            
            # Simplified approach: shift at point where next gear will drop to 60-65% of current RPM
            # This keeps the engine in the meat of the powerband
            target_rpm_drop_ratio = 0.62  # After shift, drop to 62% of pre-shift RPM
            
            # Calculate shift point
            # If we shift at shift_rpm, we'll drop to: shift_rpm / gear_ratio_factor
            # We want: shift_rpm / gear_ratio_factor = shift_rpm * target_rpm_drop_ratio
            # Therefore: shift_rpm = redline * optimal_percentage
            
            # For performance cars, this is typically around peak power RPM or slightly above
            # Peak power for these cars is typically 6500-7500 RPM
            # So shift points are usually 7000-8000 RPM
            
            # More accurate: find where power curves intersect
            optimal_shift_rpm = self._find_optimal_shift_rpm(i, i + 1)
            shift_points.append(optimal_shift_rpm)
        
        # Last gear - shift at redline
        shift_points.append(self.vehicle.redline_rpm * 0.98)
        
        return shift_points
    
    def _find_optimal_shift_rpm(self, current_gear_idx: int, next_gear_idx: int) -> float:
        """
        Find optimal shift point between two gears
        
        The optimal shift point is where wheel force in next gear (after shift)
        equals wheel force in current gear (before shift)
        """
        current_ratio = self.vehicle.gear_ratios[current_gear_idx]
        next_ratio = self.vehicle.gear_ratios[next_gear_idx]
        gear_ratio_factor = current_ratio / next_ratio
        
        # Sample RPMs from 60% to 98% of redline
        best_shift_rpm = self.vehicle.redline_rpm * 0.75
        max_advantage = 0
        
        for rpm_percent in range(60, 99):
            test_rpm = self.vehicle.redline_rpm * (rpm_percent / 100.0)
            
            # Calculate wheel force at this RPM in current gear
            current_torque = self.interpolate_torque(test_rpm)
            current_wheel_force = (current_torque * current_ratio * 
                                  self.vehicle.final_drive * 
                                  self.vehicle.transmission_efficiency) / self.vehicle.tire_radius
            
            # Calculate RPM after shifting to next gear
            next_rpm = test_rpm / gear_ratio_factor
            
            # Skip if next gear drops below powerband
            if next_rpm < self.vehicle.redline_rpm * 0.50:
                continue
            
            # Calculate wheel force at post-shift RPM in next gear
            next_torque = self.interpolate_torque(next_rpm)
            next_wheel_force = (next_torque * next_ratio * 
                               self.vehicle.final_drive * 
                               self.vehicle.transmission_efficiency) / self.vehicle.tire_radius
            
            # We want to shift when next gear force is slightly less than current
            # (around 95-98% is optimal)
            force_ratio = next_wheel_force / current_wheel_force if current_wheel_force > 0 else 0
            
            # Optimal shift is when next gear gives 95-98% of current force
            if 0.95 <= force_ratio <= 1.0:
                advantage = force_ratio
                if advantage > max_advantage:
                    max_advantage = advantage
                    best_shift_rpm = test_rpm
        
        return best_shift_rpm
    
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
        
        # velocity = (rpm * 2π * tire_radius) / (60 * gear_ratio * final_drive)
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
        Determine if vehicle should shift to next gear
        
        Uses pre-calculated optimal shift points based on power curves
        """
        if gear >= len(self.vehicle.gear_ratios):
            return False
        
        # Get the optimal shift RPM for this gear
        shift_rpm = self.shift_points[gear - 1]
        
        # Add small hysteresis to prevent rapid shifting
        shift_threshold = shift_rpm * 0.98
        
        if rpm >= shift_threshold:
            # Double-check that next gear won't drop us too low
            next_gear = gear + 1
            next_rpm = self.calculate_rpm_from_velocity(velocity_ms, next_gear)
            
            # Don't shift if it would drop below 50% of redline
            min_acceptable_rpm = self.vehicle.redline_rpm * 0.50
            
            if next_rpm >= min_acceptable_rpm:
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
    
    def run_simulation(self, timestep: float = 0.01, max_time: float = 30.0) -> List[TimeSnapshot]:
        """
        Run complete drag race simulation
        Returns list of snapshots over time
        """
        snapshots = []
        
        time = 0.0
        distance = 0.0
        velocity = 0.0  # m/s
        gear = 1
        
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
            
            # Stop if we've completed quarter mile
            if distance >= 402.336:
                break
        
        return snapshots


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