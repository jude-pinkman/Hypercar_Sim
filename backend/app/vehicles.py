from app.models import Vehicle, TorquePoint
from typing import Dict


def get_mclaren_p1() -> Vehicle:
    """McLaren P1 - Hybrid hypercar"""
    # P1 torque curve (realistic representation)
    torque_curve = [
        TorquePoint(rpm=1200, torque=450),
        TorquePoint(rpm=2000, torque=550),
        TorquePoint(rpm=3000, torque=650),
        TorquePoint(rpm=4000, torque=720),
        TorquePoint(rpm=5000, torque=750),
        TorquePoint(rpm=6000, torque=730),
        TorquePoint(rpm=7000, torque=710),
        TorquePoint(rpm=7500, torque=690),
        TorquePoint(rpm=8000, torque=660),
        TorquePoint(rpm=8500, torque=630),
    ]
    
    return Vehicle(
        name="McLaren P1",
        mass=1490,  # kg (with driver and fluids)
        power_kw=673,  # 903 hp combined
        torque_nm=720,
        
        drag_coefficient=0.34,
        frontal_area=1.98,
        
        # McLaren 7-speed DCT ratios (more accurate)
        gear_ratios=[3.31, 2.05, 1.52, 1.22, 1.02, 0.87, 0.74],
        final_drive=3.36,
        transmission_efficiency=0.93,
        
        electric_power_kw=131,
        electric_torque_nm=260,
        electric_max_speed_kmh=300,
        
        idle_rpm=1200,
        redline_rpm=8500,
        torque_curve=torque_curve,
        
        tire_radius=0.358,
        rolling_resistance_coef=0.010,
    )


def get_ferrari_sf90() -> Vehicle:
    """Ferrari SF90 Stradale - Hybrid hypercar"""
    torque_curve = [
        TorquePoint(rpm=1200, torque=500),
        TorquePoint(rpm=2000, torque=600),
        TorquePoint(rpm=3000, torque=700),
        TorquePoint(rpm=4000, torque=760),
        TorquePoint(rpm=5000, torque=800),
        TorquePoint(rpm=6000, torque=800),
        TorquePoint(rpm=7000, torque=790),
        TorquePoint(rpm=7500, torque=770),
        TorquePoint(rpm=8000, torque=740),
    ]
    
    return Vehicle(
        name="Ferrari SF90 Stradale",
        mass=1600,  # kg (with driver and fluids)
        power_kw=735,  # 986 hp combined
        torque_nm=800,
        
        drag_coefficient=0.36,
        frontal_area=2.02,
        
        # Ferrari 8-speed DCT ratios (more accurate)
        gear_ratios=[3.08, 2.19, 1.63, 1.29, 1.03, 0.84, 0.69, 0.58],
        final_drive=3.36,
        transmission_efficiency=0.94,
        
        electric_power_kw=162,
        electric_torque_nm=315,
        electric_max_speed_kmh=290,
        
        idle_rpm=1200,
        redline_rpm=8000,
        torque_curve=torque_curve,
        
        tire_radius=0.362,
        rolling_resistance_coef=0.0095,
    )


VEHICLE_DATABASE: Dict[str, Vehicle] = {
    "mclaren_p1": get_mclaren_p1(),
    "ferrari_sf90": get_ferrari_sf90(),
}


def get_vehicle(vehicle_id: str) -> Vehicle:
    """Retrieve vehicle by ID"""
    if vehicle_id not in VEHICLE_DATABASE:
        raise ValueError(f"Vehicle '{vehicle_id}' not found")
    return VEHICLE_DATABASE[vehicle_id]


def list_vehicles() -> Dict[str, str]:
    """List all available vehicles"""
    return {vid: v.name for vid, v in VEHICLE_DATABASE.items()}