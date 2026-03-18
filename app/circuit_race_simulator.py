"""
Enhanced F1 Race Simulator with Full Circuit Support
Includes realistic corner and straight simulation
"""

import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

from app.tyre import (
    Tyre, TyreCompound, TyreStrategy, TyreDegradationModel,
    COMPOUND_SPECS,
)


class SectionType(Enum):
    """Track section types"""
    STRAIGHT = "straight"
    CORNER = "corner"


@dataclass
class TrackSection:
    """Individual section of the track (straight or corner)"""
    section_type: SectionType
    length: float  # meters
    start_position: float  # meters from start line
    end_position: float  # meters from start line
    
    # Corner-specific attributes
    corner_radius: Optional[float] = None  # meters (for corners)
    corner_angle: Optional[float] = None  # degrees (for corners)
    max_speed: Optional[float] = None  # m/s (speed limit for this corner)
    
    # Straight-specific attributes
    drs_zone: bool = False  # DRS available on this straight
    
    def __post_init__(self):
        """Calculate derived properties"""
        if self.section_type == SectionType.CORNER and self.corner_radius:
            # Calculate safe cornering speed based on radius
            # v = sqrt(μ * g * r) where μ is friction coefficient
            g = 9.81  # m/s²
            friction = 2.5  # High-performance racing tires
            self.max_speed = np.sqrt(friction * g * self.corner_radius)


@dataclass
class Circuit:
    """Race circuit with detailed track layout"""
    name: str
    lap_length_km: float
    number_of_laps: int
    sections: List[TrackSection] = field(default_factory=list)
    
    @property
    def lap_length(self) -> float:
        """Get lap length in meters"""
        return self.lap_length_km * 1000
    
    @property
    def total_race_distance(self) -> float:
        """Get total race distance in meters"""
        return self.lap_length * self.number_of_laps
    
    def get_section_at_position(self, position: float) -> Optional[TrackSection]:
        """Get the track section at a given position"""
        # Normalize position to single lap
        lap_position = position % self.lap_length
        
        for section in self.sections:
            if section.start_position <= lap_position < section.end_position:
                return section
        return None
    
    def get_corner_count(self) -> int:
        """Get total number of corners"""
        return sum(1 for s in self.sections if s.section_type == SectionType.CORNER)
    
    def get_straight_count(self) -> int:
        """Get total number of straights"""
        return sum(1 for s in self.sections if s.section_type == SectionType.STRAIGHT)


@dataclass
class Car:
    """Individual car with physics properties and state"""
    driver_name: str
    team: str
    max_speed: float  # m/s (max speed achievable)
    acceleration: float  # m/s² (acceleration capability)
    tyre_grip: float  # 0.0-1.0 (affects cornering and acceleration)
    drag_coefficient: float  # air resistance factor
    cornering_ability: float = 0.9  # 0.0-1.0 (how well car handles corners)

    # State variables
    position: float = 0.0  # Distance traveled on track (meters)
    velocity: float = 0.0  # Current speed (m/s)
    lap: int = 0  # Current lap number
    finished: bool = False
    finish_time: float = None

    # Lap time tracking
    lap_times: List[float] = field(default_factory=list)
    last_lap_start_time: float = 0.0
    current_sector_times: List[float] = field(default_factory=list)

    # Current section
    current_section: Optional[TrackSection] = None
    in_corner: bool = False

    # ── Tyre degradation ─────────────────────────────────────────────────
    tyre_strategy: Optional[TyreStrategy] = field(default=None, repr=False)
    _base_tyre_grip: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._base_tyre_grip = self.tyre_grip

    # ------------------------------------------------------------------
    # Degradation-aware helpers
    # ------------------------------------------------------------------

    @property
    def current_tyre(self) -> Optional[Tyre]:
        return self.tyre_strategy.current_tyre if self.tyre_strategy else None

    @property
    def effective_tyre_grip(self) -> float:
        if self.tyre_strategy is None:
            return self.tyre_grip
        return TyreDegradationModel.effective_tyre_grip(
            self._base_tyre_grip, self.tyre_strategy.current_tyre
        )

    @property
    def effective_acceleration(self) -> float:
        if self.tyre_strategy is None:
            return self.acceleration
        return TyreDegradationModel.effective_acceleration(
            self.acceleration, self.tyre_strategy.current_tyre
        )

    @property
    def effective_cornering_speed_factor(self) -> float:
        """Combined cornering ability × tyre corner_speed_factor."""
        if self.tyre_strategy is None:
            return self.cornering_ability
        return self.cornering_ability * self.tyre_strategy.current_tyre.corner_speed_factor

    @property
    def tyre_laptime_penalty(self) -> float:
        if self.tyre_strategy is None:
            return 0.0
        return self.tyre_strategy.current_tyre.laptime_delta_s


class RaceSimulator:
    """
    Manages race simulation for multiple cars with realistic circuit physics
    """

    def __init__(
        self,
        circuit: Circuit,
        timestep: float = 0.1,
        enable_tyre_degradation: bool = True,
    ):
        """
        Initialize race simulator with circuit

        Args:
            circuit: Circuit object with track layout
            timestep: Simulation time step in seconds
            enable_tyre_degradation: Apply compound grip/wear to physics
        """
        self.circuit = circuit
        self.timestep = timestep
        self.enable_tyre_degradation = enable_tyre_degradation
        self.cars: List[Car] = []
        self.race_time = 0.0
        self.race_active = False
        self.results: List[Dict] = []
        self._pit_events: List[Dict] = []

    def add_car(
        self,
        driver_name: str,
        team: str,
        max_speed: float,
        acceleration: float,
        tyre_grip: float,
        drag_coefficient: float,
        cornering_ability: float = 0.9,
        tyre_strategy: Optional[TyreStrategy] = None,
    ) -> Car:
        """
        Add a car to the race

        Args:
            driver_name: Name of the driver
            team: Team name
            max_speed: Maximum speed in m/s
            acceleration: Base acceleration in m/s²
            tyre_grip: Tyre grip factor (0.0-1.0)
            drag_coefficient: Drag coefficient for air resistance
            cornering_ability: Corner handling ability (0.0-1.0)
            tyre_strategy: Pre-built TyreStrategy; auto-assigned if None and
                           enable_tyre_degradation is True.

        Returns:
            Car object that was added
        """
        car = Car(
            driver_name=driver_name,
            team=team,
            max_speed=max_speed,
            acceleration=acceleration,
            tyre_grip=tyre_grip,
            drag_coefficient=drag_coefficient,
            cornering_ability=cornering_ability,
        )

        if self.enable_tyre_degradation:
            if tyre_strategy is None:
                noise = random.uniform(-0.05, 0.05)
                tyre_strategy = TyreStrategy(
                    [TyreCompound.SOFT, TyreCompound.MEDIUM],
                    noise_factor=noise,
                )
            car.tyre_strategy = tyre_strategy

        self.cars.append(car)
        return car
    
    def _calculate_target_speed(self, car: Car, section: TrackSection) -> float:
        """
        Calculate target speed for current track section, accounting for
        tyre compound and wear state.
        """
        if section.section_type == SectionType.STRAIGHT:
            target = car.max_speed
            if section.drs_zone:
                target *= 1.08  # 8% speed boost with DRS
        else:  # CORNER
            if section.max_speed:
                base_corner_speed = section.max_speed
                # Use degradation-aware cornering factor instead of raw values
                grip_factor = (car.effective_tyre_grip + car.effective_cornering_speed_factor) / 2
                target = TyreDegradationModel.effective_max_corner_speed(
                    base_corner_speed * grip_factor, car.current_tyre
                ) if car.current_tyre else base_corner_speed * grip_factor
                target = min(target, car.max_speed)
            else:
                target = car.max_speed * 0.6

        return target
    
    def _calculate_acceleration(self, car: Car, target_speed: float) -> float:
        """
        Calculate effective acceleration based on physics, track section,
        and current tyre state.
        """
        speed_diff = target_speed - car.velocity
        grip_factor = car.effective_tyre_grip          # degradation-aware
        drag_force = car.drag_coefficient * (car.velocity ** 2) * 0.001

        if speed_diff < -5.0:  # Significant braking needed
            braking_power = 15.0
            effective_accel = -braking_power * grip_factor
        elif speed_diff > 0:
            speed_ratio = car.velocity / target_speed if target_speed > 0 else 0
            speed_factor = 1.0 - (speed_ratio ** 2)
            effective_accel = car.effective_acceleration * grip_factor * speed_factor - drag_force
            if car.in_corner:
                effective_accel *= 0.7
        else:
            effective_accel = -drag_force

        if car.velocity >= car.max_speed and effective_accel > 0:
            effective_accel = -drag_force

        return effective_accel
    
    def _update_car_physics(self, car: Car) -> None:
        """Update car position and velocity for one timestep."""
        if car.finished:
            return

        section = self.circuit.get_section_at_position(car.position)
        if section:
            car.current_section = section
            car.in_corner = (section.section_type == SectionType.CORNER)

        target_speed = self._calculate_target_speed(car, section) if section else car.max_speed
        accel = self._calculate_acceleration(car, target_speed)

        car.velocity += accel * self.timestep

        # Lap-time penalty from tyre wear manifests as a tiny velocity bleed
        if self.enable_tyre_degradation and car.tyre_strategy:
            penalty_bleed = car.tyre_laptime_penalty * 0.002
            car.velocity = max(0.0, car.velocity - penalty_bleed)

        car.velocity = max(0.0, min(car.velocity, car.max_speed))

        old_position = car.position
        car.position += car.velocity * self.timestep

        # Lap completion
        old_lap = int(old_position / self.circuit.lap_length)
        new_lap = int(car.position / self.circuit.lap_length)

        if new_lap > old_lap:
            lap_time = self.race_time - car.last_lap_start_time
            car.lap_times.append(lap_time)
            car.last_lap_start_time = self.race_time
            car.lap = new_lap

            # ── tyre management ───────────────────────────────────────
            if self.enable_tyre_degradation and car.tyre_strategy:
                car.tyre_strategy.advance_lap()
                if car.tyre_strategy.should_pit():
                    old_c = car.tyre_strategy.current_tyre.compound.value
                    new_c = car.tyre_strategy.pit_stop(car.lap)
                    if new_c is not None:
                        self._pit_events.append({
                            "lap":    car.lap,
                            "driver": car.driver_name,
                            "old":    old_c,
                            "new":    new_c.value,
                        })

        # Race finish
        if car.position >= self.circuit.total_race_distance and not car.finished:
            car.finished = True
            car.finish_time = self.race_time

            if len(car.lap_times) < self.circuit.number_of_laps:
                final_lap_time = self.race_time - car.last_lap_start_time
                car.lap_times.append(final_lap_time)

            self.results.append({
                'position':    len(self.results) + 1,
                'driver':      car.driver_name,
                'team':        car.team,
                'finish_time': car.finish_time,
                'laps':        car.lap,
                'lap_times':   car.lap_times.copy(),
                'fastest_lap': min(car.lap_times) if car.lap_times else None,
                'average_lap': sum(car.lap_times) / len(car.lap_times) if car.lap_times else None,
                'tyre_stints': (
                    car.tyre_strategy.pit_history if car.tyre_strategy else []
                ),
            })
    
    def get_race_positions(self) -> List[Tuple[int, str, str, int, float, float]]:
        """
        Get current race positions sorted by distance traveled
        
        Returns:
            List of (position, driver_name, team, lap, distance_in_lap, current_speed_kmh)
        """
        positions = []
        for car in self.cars:
            distance_in_current_lap = car.position - (car.lap * self.circuit.lap_length)
            positions.append({
                'car': car,
                'total_distance': car.position,
                'lap': car.lap,
                'distance_in_lap': distance_in_current_lap,
                'speed_kmh': car.velocity * 3.6
            })
        
        # Sort by total distance (descending)
        positions.sort(key=lambda x: x['total_distance'], reverse=True)
        
        # Format output
        result = []
        for idx, data in enumerate(positions):
            car = data['car']
            result.append((
                idx + 1,  # Position
                car.driver_name,
                car.team,
                data['lap'],
                data['distance_in_lap'],
                data['speed_kmh']
            ))
        
        return result
    
    def simulate_step(self) -> bool:
        """
        Simulate one timestep for all cars
        
        Returns:
            True if race is still active, False if race is complete
        """
        if not self.race_active:
            return False
        
        # Update all cars
        for car in self.cars:
            self._update_car_physics(car)
        
        # Increment race time
        self.race_time += self.timestep
        
        # Check if all cars finished
        if all(car.finished for car in self.cars):
            self.race_active = False
            return False
        
        return True
    
    def run_simulation(self, verbose: bool = True, update_interval: float = 5.0) -> List[Dict]:
        """
        Run complete race simulation
        
        Args:
            verbose: Print progress updates
            update_interval: How often to print updates (seconds of race time)
            
        Returns:
            List of results dictionaries with finishing positions
        """
        self.race_active = True
        self.race_time = 0.0
        self.results = []
        
        if verbose:
            print(f"\n{'='*90}")
            print(f"🏁 RACE START - {self.circuit.name}")
            print(f"{'='*90}")
            print(f"Circuit: {self.circuit.lap_length_km}km | "
                  f"Laps: {self.circuit.number_of_laps} | "
                  f"Total Distance: {self.circuit.total_race_distance/1000:.1f}km")
            print(f"Corners: {self.circuit.get_corner_count()} | "
                  f"Straights: {self.circuit.get_straight_count()}")
            print(f"Cars: {len(self.cars)}")
            print(f"{'='*90}\n")
        
        last_update = 0.0
        
        while self.simulate_step():
            # Print periodic updates
            if verbose and (self.race_time - last_update) >= update_interval:
                self._print_race_status()
                last_update = self.race_time
        
        if verbose:
            print(f"\n{'='*90}")
            print("🏁 RACE COMPLETE")
            print(f"{'='*90}\n")
            self._print_final_results()
        
        return self.results
    
    def _print_race_status(self) -> None:
        """Print current race status."""
        positions = self.get_race_positions()

        print(f"\n⏱️  Race Time: {self.race_time:.1f}s ({self.race_time/60:.2f} min)")
        print(f"📍 Top 5 Positions:")
        header = f"{'Pos':<5} {'Driver':<20} {'Team':<20} {'Lap':<5} {'Speed':<12} {'Section':<10}"
        if self.enable_tyre_degradation:
            header += f" {'Tyre':<8} {'Wear%':<6}"
        print(header)
        print("-" * (90 if not self.enable_tyre_degradation else 108))

        for i in range(min(5, len(positions))):
            pos, driver, team, lap, dist, speed = positions[i]
            car = next(c for c in self.cars if c.driver_name == driver)
            section_type = car.current_section.section_type.value if car.current_section else "unknown"
            row = f"{pos:<5} {driver:<20} {team:<20} {lap:<5} {speed:<12.1f} {section_type:<10}"
            if self.enable_tyre_degradation and car.current_tyre:
                s = car.current_tyre.get_status()
                row += f" {s['compound'].upper():<8} {s['wear_pct']:<6.1f}"
            print(row)
    
    def _print_final_results(self) -> None:
        """Print final race results with lap times and tyre strategy."""
        print(f"\n🏆 FINAL RESULTS")
        print(f"{'Pos':<5} {'Driver':<20} {'Team':<25} {'Time':<15} {'Gap':<12} {'Fastest Lap':<14} {'Stints'}")
        print("=" * 110)

        if not self.results:
            print("No finishers")
            return

        winner_time = self.results[0]['finish_time']
        fastest_lap_overall = min(r['fastest_lap'] for r in self.results if r['fastest_lap'])

        for result in self.results:
            gap = result['finish_time'] - winner_time
            gap_str = f"+{gap:.2f}s" if gap > 0 else "—"
            fastest_lap_str = f"{result['fastest_lap']:.2f}s" if result['fastest_lap'] else "N/A"
            if result['fastest_lap'] == fastest_lap_overall:
                fastest_lap_str += " 🔥"

            stints_str = ""
            if result.get('tyre_stints'):
                stints_str = " → ".join(
                    f"L{p['lap']}: {p['old'].upper()}→{p['new'].upper()}"
                    for p in result['tyre_stints']
                )

            print(
                f"{result['position']:<5} {result['driver']:<20} {result['team']:<25} "
                f"{result['finish_time']:.2f}s{'':<7} {gap_str:<12} {fastest_lap_str:<14} {stints_str}"
            )

        # Lap time analysis
        print(f"\n📊 LAP TIME ANALYSIS")
        print(f"{'Driver':<20} {'Fastest':<12} {'Average':<12} {'Slowest':<12} {'Consistency':<12}")
        print("-" * 80)

        for result in self.results[:5]:
            lap_times = result['lap_times']
            if lap_times:
                fastest = min(lap_times)
                slowest = max(lap_times)
                average = result['average_lap']
                consistency = slowest - fastest
                print(
                    f"{result['driver']:<20} {fastest:<12.2f} {average:<12.2f} "
                    f"{slowest:<12.2f} {consistency:<12.2f}"
                )

        # Pit stop summary
        if self._pit_events:
            print(f"\n🔧 PIT STOPS")
            print(f"{'Lap':<6} {'Driver':<22} {'Change'}")
            print("-" * 50)
            for ev in sorted(self._pit_events, key=lambda e: e['lap']):
                print(f"{ev['lap']:<6} {ev['driver']:<22} {ev['old'].upper()} → {ev['new'].upper()}")
    
    def reset(self) -> None:
        """Reset race state for new simulation."""
        self.race_time = 0.0
        self.race_active = False
        self.results = []
        self._pit_events = []

        for car in self.cars:
            car.position = 0.0
            car.velocity = 0.0
            car.lap = 0
            car.finished = False
            car.finish_time = None
            car.lap_times = []
            car.last_lap_start_time = 0.0
            car.current_section = None
            car.in_corner = False


def create_monaco_circuit() -> Circuit:
    """Create Monaco street circuit (3.337km, tight and twisty)"""
    circuit = Circuit(
        name="Circuit de Monaco",
        lap_length_km=3.337,
        number_of_laps=78
    )
    
    position = 0.0
    
    # Sainte Devote (Turn 1) - tight right
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 180, position, position + 180, drs_zone=False))
    position += 180
    circuit.sections.append(TrackSection(SectionType.CORNER, 80, position, position + 80, corner_radius=25, corner_angle=90))
    position += 80
    
    # Massenet (Turn 2-3)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 120, position, position + 120))
    position += 120
    circuit.sections.append(TrackSection(SectionType.CORNER, 100, position, position + 100, corner_radius=30, corner_angle=120))
    position += 100
    
    # Casino Square (Turn 4-5)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 90, position, position + 90))
    position += 90
    circuit.sections.append(TrackSection(SectionType.CORNER, 70, position, position + 70, corner_radius=20, corner_angle=80))
    position += 70
    
    # Mirabeau (Turn 6)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 110, position, position + 110))
    position += 110
    circuit.sections.append(TrackSection(SectionType.CORNER, 60, position, position + 60, corner_radius=15, corner_angle=70))
    position += 60
    
    # Portier (Turn 8)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 100, position, position + 100))
    position += 100
    circuit.sections.append(TrackSection(SectionType.CORNER, 80, position, position + 80, corner_radius=28, corner_angle=90))
    position += 80
    
    # Tunnel
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 340, position, position + 340, drs_zone=False))
    position += 340
    
    # Nouvelle Chicane (Turn 10-11)
    circuit.sections.append(TrackSection(SectionType.CORNER, 90, position, position + 90, corner_radius=22, corner_angle=85))
    position += 90
    
    # Tabac (Turn 12)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 140, position, position + 140))
    position += 140
    circuit.sections.append(TrackSection(SectionType.CORNER, 75, position, position + 75, corner_radius=35, corner_angle=75))
    position += 75
    
    # Swimming Pool section (Turn 13-15)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 85, position, position + 85))
    position += 85
    circuit.sections.append(TrackSection(SectionType.CORNER, 110, position, position + 110, corner_radius=18, corner_angle=100))
    position += 110
    
    # Rascasse (Turn 17)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 95, position, position + 95))
    position += 95
    circuit.sections.append(TrackSection(SectionType.CORNER, 70, position, position + 70, corner_radius=12, corner_angle=120))
    position += 70
    
    # Anthony Noghes (Turn 18-19) to finish
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 105, position, position + 105))
    position += 105
    circuit.sections.append(TrackSection(SectionType.CORNER, 85, position, position + 85, corner_radius=25, corner_angle=90))
    position += 85
    
    # Final straight
    remaining = circuit.lap_length - position
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, remaining, position, circuit.lap_length))
    
    return circuit


def create_monza_circuit() -> Circuit:
    """Create Monza circuit (5.793km, high speed)"""
    circuit = Circuit(
        name="Autodromo Nazionale di Monza",
        lap_length_km=5.793,
        number_of_laps=53
    )
    
    position = 0.0
    
    # Start/finish straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 620, position, position + 620, drs_zone=True))
    position += 620
    
    # Variante del Rettifilo (Turn 1-2) - first chicane
    circuit.sections.append(TrackSection(SectionType.CORNER, 120, position, position + 120, corner_radius=40, corner_angle=110))
    position += 120
    
    # Straight to Curva Grande
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 450, position, position + 450))
    position += 450
    
    # Curva Grande (Turn 3) - fast right
    circuit.sections.append(TrackSection(SectionType.CORNER, 180, position, position + 180, corner_radius=150, corner_angle=60))
    position += 180
    
    # Straight to Variante della Roggia
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 380, position, position + 380))
    position += 380
    
    # Variante della Roggia (Turn 4-5) - second chicane
    circuit.sections.append(TrackSection(SectionType.CORNER, 100, position, position + 100, corner_radius=35, corner_angle=100))
    position += 100
    
    # Straight to Lesmo
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 520, position, position + 520))
    position += 520
    
    # Lesmo 1 (Turn 6)
    circuit.sections.append(TrackSection(SectionType.CORNER, 110, position, position + 110, corner_radius=60, corner_angle=75))
    position += 110
    
    # Short straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 140, position, position + 140))
    position += 140
    
    # Lesmo 2 (Turn 7)
    circuit.sections.append(TrackSection(SectionType.CORNER, 95, position, position + 95, corner_radius=55, corner_angle=70))
    position += 95
    
    # Straight to Ascari
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 680, position, position + 680, drs_zone=True))
    position += 680
    
    # Ascari chicane (Turn 8-9-10)
    circuit.sections.append(TrackSection(SectionType.CORNER, 180, position, position + 180, corner_radius=45, corner_angle=130))
    position += 180
    
    # Straight to Parabolica
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 410, position, position + 410))
    position += 410
    
    # Parabolica (Turn 11) - long fast right
    circuit.sections.append(TrackSection(SectionType.CORNER, 240, position, position + 240, corner_radius=120, corner_angle=180))
    position += 240
    
    # Final section to finish
    remaining = circuit.lap_length - position
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, remaining, position, circuit.lap_length))
    
    return circuit


def create_silverstone_circuit() -> Circuit:
    """Create Silverstone circuit (5.891km, fast and flowing)"""
    circuit = Circuit(
        name="Silverstone Circuit",
        lap_length_km=5.891,
        number_of_laps=52
    )
    
    position = 0.0
    
    # Start/finish straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 380, position, position + 380))
    position += 380
    
    # Abbey (Turn 1) - fast right
    circuit.sections.append(TrackSection(SectionType.CORNER, 95, position, position + 95, corner_radius=80, corner_angle=65))
    position += 95
    
    # Farm Straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 290, position, position + 290))
    position += 290
    
    # Village (Turn 3-4-5)
    circuit.sections.append(TrackSection(SectionType.CORNER, 160, position, position + 160, corner_radius=50, corner_angle=110))
    position += 160
    
    # The Loop (Turn 6)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 180, position, position + 180))
    position += 180
    circuit.sections.append(TrackSection(SectionType.CORNER, 120, position, position + 120, corner_radius=45, corner_angle=90))
    position += 120
    
    # Wellington Straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 550, position, position + 550, drs_zone=True))
    position += 550
    
    # Brooklands (Turn 7)
    circuit.sections.append(TrackSection(SectionType.CORNER, 85, position, position + 85, corner_radius=70, corner_angle=75))
    position += 85
    
    # Luffield (Turn 8-9)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 110, position, position + 110))
    position += 110
    circuit.sections.append(TrackSection(SectionType.CORNER, 105, position, position + 105, corner_radius=40, corner_angle=95))
    position += 105
    
    # Woodcote
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 220, position, position + 220))
    position += 220
    
    # Copse (Turn 10) - very fast
    circuit.sections.append(TrackSection(SectionType.CORNER, 110, position, position + 110, corner_radius=100, corner_angle=70))
    position += 110
    
    # Maggotts-Becketts (Turn 11-12-13) - high speed complex
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 190, position, position + 190))
    position += 190
    circuit.sections.append(TrackSection(SectionType.CORNER, 240, position, position + 240, corner_radius=90, corner_angle=140))
    position += 240
    
    # Hangar Straight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 480, position, position + 480, drs_zone=True))
    position += 480
    
    # Stowe (Turn 15)
    circuit.sections.append(TrackSection(SectionType.CORNER, 88, position, position + 88, corner_radius=55, corner_angle=80))
    position += 88
    
    # Vale-Club (Turn 16-17-18)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 165, position, position + 165))
    position += 165
    circuit.sections.append(TrackSection(SectionType.CORNER, 135, position, position + 135, corner_radius=42, corner_angle=105))
    position += 135
    
    # Final section
    remaining = circuit.lap_length - position
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, remaining, position, circuit.lap_length))
    
    return circuit


def create_f1_grid() -> List[Dict]:
    """Create a realistic F1 grid with 22 cars"""
    f1_grid = [
        # Red Bull Racing - Best overall, excellent in all areas
        {"driver_name": "Max Verstappen", "team": "Red Bull Racing", "max_speed": 95.0, "acceleration": 12.5, "tyre_grip": 0.95, "drag_coefficient": 0.70, "cornering_ability": 0.95},
        {"driver_name": "Sergio Perez", "team": "Red Bull Racing", "max_speed": 94.5, "acceleration": 12.3, "tyre_grip": 0.93, "drag_coefficient": 0.71, "cornering_ability": 0.92},
        
        # Ferrari - Strong on corners
        {"driver_name": "Charles Leclerc", "team": "Ferrari", "max_speed": 94.0, "acceleration": 12.2, "tyre_grip": 0.92, "drag_coefficient": 0.72, "cornering_ability": 0.94},
        {"driver_name": "Carlos Sainz", "team": "Ferrari", "max_speed": 93.8, "acceleration": 12.1, "tyre_grip": 0.91, "drag_coefficient": 0.72, "cornering_ability": 0.91},
        
        # Mercedes - Good straight line speed
        {"driver_name": "Lewis Hamilton", "team": "Mercedes", "max_speed": 93.5, "acceleration": 12.0, "tyre_grip": 0.91, "drag_coefficient": 0.73, "cornering_ability": 0.93},
        {"driver_name": "George Russell", "team": "Mercedes", "max_speed": 93.3, "acceleration": 11.9, "tyre_grip": 0.90, "drag_coefficient": 0.73, "cornering_ability": 0.90},
        
        # McLaren - Balanced
        {"driver_name": "Lando Norris", "team": "McLaren", "max_speed": 92.5, "acceleration": 11.7, "tyre_grip": 0.89, "drag_coefficient": 0.74, "cornering_ability": 0.89},
        {"driver_name": "Oscar Piastri", "team": "McLaren", "max_speed": 92.3, "acceleration": 11.6, "tyre_grip": 0.88, "drag_coefficient": 0.74, "cornering_ability": 0.88},
        
        # Aston Martin
        {"driver_name": "Fernando Alonso", "team": "Aston Martin", "max_speed": 91.8, "acceleration": 11.5, "tyre_grip": 0.87, "drag_coefficient": 0.75, "cornering_ability": 0.90},
        {"driver_name": "Lance Stroll", "team": "Aston Martin", "max_speed": 91.5, "acceleration": 11.4, "tyre_grip": 0.86, "drag_coefficient": 0.75, "cornering_ability": 0.85},
        
        # Alpine
        {"driver_name": "Pierre Gasly", "team": "Alpine", "max_speed": 90.5, "acceleration": 11.2, "tyre_grip": 0.85, "drag_coefficient": 0.76, "cornering_ability": 0.86},
        {"driver_name": "Esteban Ocon", "team": "Alpine", "max_speed": 90.3, "acceleration": 11.1, "tyre_grip": 0.84, "drag_coefficient": 0.76, "cornering_ability": 0.84},
        
        # Williams
        {"driver_name": "Alex Albon", "team": "Williams", "max_speed": 89.5, "acceleration": 11.0, "tyre_grip": 0.83, "drag_coefficient": 0.77, "cornering_ability": 0.84},
        {"driver_name": "Logan Sargeant", "team": "Williams", "max_speed": 89.0, "acceleration": 10.9, "tyre_grip": 0.82, "drag_coefficient": 0.77, "cornering_ability": 0.81},
        
        # Alfa Romeo
        {"driver_name": "Valtteri Bottas", "team": "Alfa Romeo", "max_speed": 88.8, "acceleration": 10.8, "tyre_grip": 0.82, "drag_coefficient": 0.78, "cornering_ability": 0.83},
        {"driver_name": "Zhou Guanyu", "team": "Alfa Romeo", "max_speed": 88.5, "acceleration": 10.7, "tyre_grip": 0.81, "drag_coefficient": 0.78, "cornering_ability": 0.80},
        
        # Haas
        {"driver_name": "Nico Hulkenberg", "team": "Haas F1 Team", "max_speed": 88.0, "acceleration": 10.6, "tyre_grip": 0.80, "drag_coefficient": 0.79, "cornering_ability": 0.82},
        {"driver_name": "Kevin Magnussen", "team": "Haas F1 Team", "max_speed": 87.8, "acceleration": 10.5, "tyre_grip": 0.79, "drag_coefficient": 0.79, "cornering_ability": 0.79},
        
        # AlphaTauri
        {"driver_name": "Yuki Tsunoda", "team": "AlphaTauri", "max_speed": 87.5, "acceleration": 10.4, "tyre_grip": 0.79, "drag_coefficient": 0.80, "cornering_ability": 0.81},
        {"driver_name": "Daniel Ricciardo", "team": "AlphaTauri", "max_speed": 87.3, "acceleration": 10.3, "tyre_grip": 0.78, "drag_coefficient": 0.80, "cornering_ability": 0.80},
        
        # Racing Bulls
        {"driver_name": "Liam Lawson", "team": "Racing Bulls", "max_speed": 87.0, "acceleration": 10.2, "tyre_grip": 0.78, "drag_coefficient": 0.81, "cornering_ability": 0.80},
        {"driver_name": "Ayumu Iwasa", "team": "Racing Bulls", "max_speed": 86.8, "acceleration": 10.1, "tyre_grip": 0.77, "drag_coefficient": 0.81, "cornering_ability": 0.78},
    ]
    return f1_grid


def main():
    """Example: Run races on different circuits"""
    
    # Choose circuit
    print("\n" + "="*90)
    print("AVAILABLE CIRCUITS:")
    print("1. Monaco (3.337km, 78 laps) - Tight and technical")
    print("2. Monza (5.793km, 53 laps) - High speed temple")
    print("3. Silverstone (5.891km, 52 laps) - Fast and flowing")
    print("="*90)
    
    # For demo, run Monaco
    circuit = create_monaco_circuit()
    # circuit = create_monza_circuit()
    # circuit = create_silverstone_circuit()
    
    # Create simulator
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add all 22 cars
    f1_grid = create_f1_grid()
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    print(f"\nGrid size: {len(simulator.cars)} cars")
    
    # Run simulation
    results = simulator.run_simulation(verbose=True, update_interval=15.0)
    
    # Additional analysis
    print(f"\n📊 RACE STATISTICS")
    print("="*90)
    print(f"Circuit: {circuit.name}")
    print(f"Total distance: {circuit.total_race_distance / 1000:.1f} km")
    print(f"Race duration: {results[-1]['finish_time']:.1f} seconds ({results[-1]['finish_time']/60:.2f} minutes)")
    print(f"Winner: {results[0]['driver']} ({results[0]['team']})")
    print(f"Fastest lap: {results[0]['fastest_lap']:.2f}s")
    print(f"Winner's average lap: {results[0]['average_lap']:.2f}s")
    print(f"Gap to last place: {results[-1]['finish_time'] - results[0]['finish_time']:.2f} seconds")


if __name__ == "__main__":
    main()
