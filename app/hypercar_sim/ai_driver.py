"""AI driver that decides throttle and braking for each frame."""

from __future__ import annotations

from dataclasses import dataclass

from .physics_engine import CarState, PhysicsEngine
from .track_model import AlbertParkCircuit, TrackSegment


@dataclass
class DriverCommand:
    throttle: float
    brake: float
    speed_limit_kmh: float


class AIDriver:
    """Simple rule-based AI: full push on straights, brake before corners."""

    def __init__(self, physics: PhysicsEngine) -> None:
        self.physics = physics
        self.base_straight_limit = 332.0
        self.brake_buffer_m = 28.0

    def _braking_distance_m(self, current_kmh: float, target_kmh: float) -> float:
        v = max(0.0, current_kmh / 3.6)
        vt = max(0.0, target_kmh / 3.6)
        if v <= vt:
            return 0.0
        max_eff_brake = self.physics.max_brake_decel_mps2 * 0.9
        return ((v * v) - (vt * vt)) / (2.0 * max_eff_brake)

    def _control_in_corner(self, state: CarState, seg: TrackSegment) -> DriverCommand:
        target = seg.max_speed_kmh or 140.0
        margin = state.speed_kmh - target

        if margin > 8.0:
            throttle = 0.08
            brake = min(1.0, 0.3 + margin / 55.0)
        elif margin > 2.0:
            throttle = 0.18
            brake = min(0.75, 0.12 + margin / 70.0)
        elif margin < -7.0:
            throttle = 0.72
            brake = 0.0
        else:
            throttle = 0.48
            brake = 0.0

        return DriverCommand(throttle=throttle, brake=brake, speed_limit_kmh=target)

    def _control_on_straight(self, state: CarState, track: AlbertParkCircuit) -> DriverCommand:
        next_corner, dist_to_corner = track.next_corner_info(state.position_m)

        if not next_corner:
            return DriverCommand(throttle=1.0, brake=0.0, speed_limit_kmh=self.base_straight_limit)

        corner_limit = next_corner.max_speed_kmh or 140.0
        required = self._braking_distance_m(state.speed_kmh, corner_limit) + self.brake_buffer_m

        # Start braking when within required distance to corner entry.
        if dist_to_corner <= required:
            urgency = 1.0 - max(0.0, dist_to_corner / max(required, 1.0))
            brake = min(1.0, 0.28 + urgency * 0.72)
            throttle = max(0.0, 0.22 - urgency * 0.22)
            speed_limit = max(corner_limit + 4.0, 90.0)
            return DriverCommand(throttle=throttle, brake=brake, speed_limit_kmh=speed_limit)

        # Open throttle on the straight.
        return DriverCommand(throttle=1.0, brake=0.0, speed_limit_kmh=self.base_straight_limit)

    def decide(self, state: CarState, track: AlbertParkCircuit) -> DriverCommand:
        """Compute control command for current frame."""
        _, seg, _ = track.locate(state.position_m)

        if seg.kind == "corner":
            return self._control_in_corner(state, seg)
        return self._control_on_straight(state, track)
