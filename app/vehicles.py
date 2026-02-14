import math
from typing import List, Tuple, Optional, Dict
from app.models import Vehicle, EnvironmentConditions, TimeSnapshot, GearInfo


class PhysicsEngine:
    """Core physics simulation engine for vehicle dynamics"""
    
    # Physical constants
    GRAVITY = 9.81  # m/s²
    AIR_GAS_CONSTANT = 287.05  # J/(kg·K)
    
    def __init__(self, vehicle: Vehicle, environment: EnvironmentConditions):
        self.vehicle = vehicle
        self.environment = environment
        self.air_density = self._calculate_air_density()
        
        # Build gear lookup dictionary
        self.gear_lookup = {gear.gear_number: gear for gear in self.vehicle.gears}
        
    def _calculate_air_density(self) -> float:
        """Calculate air density based on temperature and altitude"""
        temp_kelvin = self.environment.temperature_celsius + 273.15
        pressure_pa = self.environment.air_pressure_kpa * 1000
        
        # Adjust pressure for altitude
        altitude_m = self.environment.altitude_meters
        pressure_pa *= math.exp(-altitude_m / 8400)
        
        # Ideal gas law: ρ = P / (R * T)
        return pressure_pa / (self.AIR_GAS_CONSTANT * temp_kelvin)
    
    def get_gear_info(self, gear_number: int) -> Optional[GearInfo]:
        """Get gear information from database"""
        return self.gear_lookup.get(gear_number)
    
    def interpolate_torque(self, rpm: float) -> float:
        """Interpolate engine torque at given RPM from torque curve"""
        curve = self.vehicle.torque_curve
        
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
        
        if velocity_kmh >= max_speed:
            return 0.0
        
        # Linear taper from 60% of max speed
        taper_start = max_speed * 0.6
        if velocity_kmh <= taper_start:
            return self.vehicle.electric_torque_nm
        else:
            taper_ratio = 1.0 - ((velocity_kmh - taper_start) / (max_speed - taper_start))
            return self.vehicle.electric_torque_nm * max(0, taper_ratio)
    
    def calculate_rpm_from_velocity(self, velocity_ms: float, gear_number: int) -> float:
        """Calculate engine RPM for given velocity and gear"""
        gear_info = self.get_gear_info(gear_number)
        if not gear_info:
            return self.vehicle.idle_rpm
        
        if velocity_ms < 0.01:
            return self.vehicle.idle_rpm
        
        total_ratio = gear_info.ratio * self.vehicle.final_drive
        rpm = (velocity_ms * 60 * total_ratio) / (2 * math.pi * self.vehicle.tire_radius)
        
        return max(self.vehicle.idle_rpm, rpm)
    
    def should_shift_up(self, rpm: float, gear_number: int, velocity_ms: float) -> bool:
        """
        Determine if vehicle should shift to next gear
        Uses shift_speed_kmh from gear database (CSV)
        """
        if gear_number >= len(self.vehicle.gears):
            return False
        
        current_gear = self.get_gear_info(gear_number)
        if not current_gear:
            return False
        
        velocity_kmh = velocity_ms * 3.6
        
        # Check if we've reached the shift speed from database
        if velocity_kmh >= current_gear.shift_speed_kmh:
            # Verify next gear won't bog the engine
            next_gear = self.get_gear_info(gear_number + 1)
            if next_gear:
                next_rpm = self.calculate_rpm_from_velocity(velocity_ms, gear_number + 1)
                min_rpm = self.vehicle.redline_rpm * 0.50
                
                if next_rpm >= min_rpm:
                    return True
        
        return False
    
    def select_gear(self, velocity_ms: float, current_gear: int, current_rpm: float) -> int:
        """Select optimal gear based on velocity"""
        if velocity_ms < 1.0:
            return 1
        
        if self.should_shift_up(current_rpm, current_gear, velocity_ms):
            return min(current_gear + 1, len(self.vehicle.gears))
        
        return current_gear
    
    def calculate_wheel_torque(self, rpm: float, gear_number: int, velocity_ms: float) -> float:
        """Calculate torque at wheels including hybrid system"""
        gear_info = self.get_gear_info(gear_number)
        if not gear_info:
            return 0.0
        
        engine_torque = self.interpolate_torque(rpm)
        electric_torque = self.calculate_electric_torque(velocity_ms)
        combined_torque = engine_torque + electric_torque
        
        total_ratio = gear_info.ratio * self.vehicle.final_drive
        wheel_torque = combined_torque * total_ratio * self.vehicle.transmission_efficiency
        
        return wheel_torque
    
    def calculate_forces(self, velocity_ms: float, gear: int, rpm: float) -> Tuple[float, float, float]:
        """Calculate driving force and resistance forces"""
        wheel_torque = self.calculate_wheel_torque(rpm, gear, velocity_ms)
        drive_force = wheel_torque / self.vehicle.tire_radius
        
        drag_force = 0.5 * self.air_density * self.vehicle.drag_coefficient * \
                     self.vehicle.frontal_area * velocity_ms ** 2
        
        rolling_resistance = self.vehicle.rolling_resistance_coef * \
                           self.vehicle.mass * self.GRAVITY
        
        return drive_force, drag_force, rolling_resistance
    
    def simulate_step(self, velocity_ms: float, gear: int, dt: float) -> Tuple[float, float, int, float]:
        """Simulate one timestep"""
        rpm = self.calculate_rpm_from_velocity(velocity_ms, gear)
        new_gear = self.select_gear(velocity_ms, gear, rpm)
        
        if new_gear != gear:
            rpm = self.calculate_rpm_from_velocity(velocity_ms, new_gear)
        
        drive_force, drag_force, rolling_resistance = self.calculate_forces(velocity_ms, new_gear, rpm)
        
        net_force = drive_force - drag_force - rolling_resistance
        acceleration = net_force / self.vehicle.mass
        
        # Limit acceleration to realistic traction limits
        max_acceleration = 1.3 * self.GRAVITY
        acceleration = min(acceleration, max_acceleration)
        
        new_velocity = velocity_ms + acceleration * dt
        new_velocity = max(0, new_velocity)
        
        return new_velocity, acceleration, new_gear, rpm
    
    def run_simulation(self, timestep: float = 0.01, max_time: float = 30.0) -> List[TimeSnapshot]:
        """Run complete drag race simulation"""
        snapshots = []
        
        time = 0.0
        distance = 0.0
        velocity = 0.0
        gear = 1
        
        while time <= max_time:
            new_velocity, acceleration, new_gear, rpm = self.simulate_step(velocity, gear, timestep)
            
            avg_velocity = (velocity + new_velocity) / 2
            distance += avg_velocity * timestep
            
            velocity = new_velocity
            gear = new_gear
            
            drive_force, drag_force, rolling_resistance = self.calculate_forces(velocity, gear, rpm)
            power_kw = (drive_force * velocity) / 1000
            
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
            
            if distance >= 402.336:
                break
        
        return snapshots


def calculate_performance_metrics(snapshots: List[TimeSnapshot]) -> dict:
    """Extract key performance metrics"""
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