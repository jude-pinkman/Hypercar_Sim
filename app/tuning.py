"""
Tuning System for Vehicle Performance Modifications
Applies performance upgrades to vehicle specifications
"""

from typing import Dict, Optional
from copy import deepcopy
from app.models import Vehicle


class TuningSystem:
    """Manages vehicle tuning modifications"""
    
    # Tuning multipliers for different upgrade levels
    ENGINE_MULTIPLIERS = {
        'stock': {'power': 1.0, 'torque': 1.0},
        'stage1': {'power': 1.15, 'torque': 1.12},
        'stage2': {'power': 1.30, 'torque': 1.25},
        'stage3': {'power': 1.50, 'torque': 1.40},
    }
    
    TIRE_MULTIPLIERS = {
        'street': {'grip': 1.0, 'rolling_resistance': 1.0},
        'sport': {'grip': 1.15, 'rolling_resistance': 0.95},
        'slick': {'grip': 1.35, 'rolling_resistance': 0.90},
    }
    
    AERO_MULTIPLIERS = {
        'stock': {'drag': 1.0, 'downforce': 1.0},
        'sport': {'drag': 0.95, 'downforce': 1.20},
        'race': {'drag': 0.88, 'downforce': 1.50},
    }
    
    WEIGHT_MULTIPLIERS = {
        'stock': 1.0,
        'lightweight': 0.95,
        'race': 0.88,
    }
    
    TRANSMISSION_MULTIPLIERS = {
        'stock': 1.0,
        'sport': 1.05,
        'race': 1.10,
    }


def apply_tuning_to_vehicles(
    vehicle_ids: list,
    base_vehicles: Dict[str, Vehicle],
    tuning_mods: Dict[str, dict]
) -> Dict[str, Vehicle]:
    """
    Apply tuning modifications to vehicles
    
    Args:
        vehicle_ids: List of vehicle IDs to tune
        base_vehicles: Dictionary of base vehicle specifications
        tuning_mods: Dictionary of tuning modifications per vehicle
        
    Returns:
        Dictionary of tuned vehicles
    """
    tuned_vehicles = {}
    
    for vehicle_id in vehicle_ids:
        if vehicle_id not in base_vehicles:
            continue
            
        # Get base vehicle and make a deep copy
        base_vehicle = base_vehicles[vehicle_id]
        tuned_vehicle = deepcopy(base_vehicle)
        
        # Apply tuning if modifications exist for this vehicle
        if vehicle_id in tuning_mods:
            mods = tuning_mods[vehicle_id]
            tuned_vehicle = apply_tuning_modifications(tuned_vehicle, mods)
        
        tuned_vehicles[vehicle_id] = tuned_vehicle
    
    return tuned_vehicles


def apply_tuning_modifications(vehicle: Vehicle, mods: dict) -> Vehicle:
    """
    Apply specific tuning modifications to a vehicle
    
    Args:
        vehicle: Base vehicle specification
        mods: Dictionary of modifications to apply
        
    Returns:
        Modified vehicle
    """
    # Engine tuning
    if 'engine' in mods and mods['engine'] in TuningSystem.ENGINE_MULTIPLIERS:
        multipliers = TuningSystem.ENGINE_MULTIPLIERS[mods['engine']]
        vehicle.power_kw *= multipliers['power']
        vehicle.torque_nm *= multipliers['torque']
        
        # Update torque curve
        for point in vehicle.torque_curve:
            point.torque *= multipliers['torque']
    
    # Tire upgrades
    if 'tires' in mods and mods['tires'] in TuningSystem.TIRE_MULTIPLIERS:
        multipliers = TuningSystem.TIRE_MULTIPLIERS[mods['tires']]
        vehicle.rolling_resistance_coef *= multipliers['rolling_resistance']
        # Grip affects traction limit (handled in physics engine)
    
    # Aerodynamic modifications
    if 'aero' in mods and mods['aero'] in TuningSystem.AERO_MULTIPLIERS:
        multipliers = TuningSystem.AERO_MULTIPLIERS[mods['aero']]
        vehicle.drag_coefficient *= multipliers['drag']
        # Downforce would be added separately if we track it
    
    # Weight reduction
    if 'weight' in mods and mods['weight'] in TuningSystem.WEIGHT_MULTIPLIERS:
        multiplier = TuningSystem.WEIGHT_MULTIPLIERS[mods['weight']]
        vehicle.mass *= multiplier
    
    # Transmission upgrades
    if 'transmission' in mods and mods['transmission'] in TuningSystem.TRANSMISSION_MULTIPLIERS:
        multiplier = TuningSystem.TRANSMISSION_MULTIPLIERS[mods['transmission']]
        vehicle.transmission_efficiency *= multiplier
    
    # Boost pressure (turbo/supercharger)
    if 'boostPressure' in mods:
        boost = float(mods['boostPressure'])
        if 0.5 <= boost <= 2.0:
            # Boost affects both power and torque
            vehicle.power_kw *= boost
            vehicle.torque_nm *= boost
            
            # Update torque curve
            for point in vehicle.torque_curve:
                point.torque *= boost
    
    # Nitrous oxide (temporary power boost)
    if 'nitrousOxide' in mods and mods['nitrousOxide']:
        # NOS adds 25% power and 20% torque
        nos_power_multiplier = 1.25
        nos_torque_multiplier = 1.20
        
        vehicle.power_kw *= nos_power_multiplier
        vehicle.torque_nm *= nos_torque_multiplier
        
        # Update torque curve
        for point in vehicle.torque_curve:
            point.torque *= nos_torque_multiplier
    
    return vehicle


def get_tuning_summary(mods: dict) -> str:
    """
    Generate a human-readable summary of tuning modifications
    
    Args:
        mods: Dictionary of modifications
        
    Returns:
        String summary of modifications
    """
    summary_parts = []
    
    if 'engine' in mods and mods['engine'] != 'stock':
        summary_parts.append(f"Engine: {mods['engine']}")
    
    if 'tires' in mods and mods['tires'] != 'street':
        summary_parts.append(f"Tires: {mods['tires']}")
    
    if 'aero' in mods and mods['aero'] != 'stock':
        summary_parts.append(f"Aero: {mods['aero']}")
    
    if 'weight' in mods and mods['weight'] != 'stock':
        summary_parts.append(f"Weight: {mods['weight']}")
    
    if 'transmission' in mods and mods['transmission'] != 'stock':
        summary_parts.append(f"Trans: {mods['transmission']}")
    
    if 'boostPressure' in mods and mods['boostPressure'] != 1.0:
        summary_parts.append(f"Boost: {mods['boostPressure']}x")
    
    if 'nitrousOxide' in mods and mods['nitrousOxide']:
        summary_parts.append("NOS: Active")
    
    return " | ".join(summary_parts) if summary_parts else "Stock"