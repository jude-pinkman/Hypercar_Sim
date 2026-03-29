"""Vehicle state and simplified F1-style physics model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CarState:
    speed_kmh: float = 0.0
    rpm: float = 3500.0
    gear: int = 1
    throttle: float = 0.0
    brake: float = 0.0
    position_m: float = 0.0

    lap_count: int = 0
    lap_time_s: float = 0.0
    last_lap_time_s: float = 0.0
    best_lap_time_s: float = 0.0


class PhysicsEngine:
    """Simple but smooth longitudinal model with auto-shifting."""

    def __init__(self) -> None:
        self.max_engine_accel_mps2 = 10.8
        self.max_brake_decel_mps2 = 19.5
        self.drag_coeff = 0.00185
        self.rolling_res_mps2 = 0.32
        self.vmax_kmh_power_limited = 344.0

        self.wheel_radius_m = 0.34
        self.final_drive = 3.55
        self.gear_ratios: List[float] = [3.15, 2.45, 1.95, 1.55, 1.28, 1.08, 0.93, 0.82]

        self.idle_rpm = 3500.0
        self.redline_rpm = 12500.0
        self.upshift_rpm = 11850.0
        self.downshift_rpm = 6200.0

        self.throttle_rise_rate = 2.8
        self.throttle_fall_rate = 5.0
        self.brake_rise_rate = 4.6
        self.brake_fall_rate = 6.5

    @staticmethod
    def _approach(current: float, target: float, rise_rate: float, fall_rate: float, dt: float) -> float:
        if target > current:
            return min(target, current + rise_rate * dt)
        return max(target, current - fall_rate * dt)

    def _calc_rpm(self, speed_kmh: float, gear: int) -> float:
        speed_mps = max(0.0, speed_kmh / 3.6)
        wheel_rps = speed_mps / (2.0 * 3.1415926535 * self.wheel_radius_m)
        ratio = self.gear_ratios[max(0, min(7, gear - 1))]
        rpm = wheel_rps * 60.0 * ratio * self.final_drive
        return max(self.idle_rpm, min(self.redline_rpm, rpm))

    def _auto_shift(self, state: CarState) -> None:
        if state.gear < 8 and state.rpm >= self.upshift_rpm:
            state.gear += 1
        elif state.gear > 1 and state.rpm <= self.downshift_rpm:
            state.gear -= 1

    def update(
        self,
        state: CarState,
        target_throttle: float,
        target_brake: float,
        dt: float,
        speed_limit_kmh: float,
        track_length_m: float,
    ) -> None:
        """Advance the car state by one fixed timestep."""
        target_throttle = max(0.0, min(1.0, target_throttle))
        target_brake = max(0.0, min(1.0, target_brake))

        # Keep controls smooth to avoid instant jumps.
        state.throttle = self._approach(state.throttle, target_throttle, self.throttle_rise_rate, self.throttle_fall_rate, dt)
        state.brake = self._approach(state.brake, target_brake, self.brake_rise_rate, self.brake_fall_rate, dt)

        speed_mps = state.speed_kmh / 3.6
        speed_ratio = min(1.0, state.speed_kmh / self.vmax_kmh_power_limited)

        engine_accel = state.throttle * self.max_engine_accel_mps2 * (1.0 - speed_ratio ** 1.35)
        brake_decel = state.brake * self.max_brake_decel_mps2
        aero_drag = self.drag_coeff * speed_mps * speed_mps
        net_accel = engine_accel - brake_decel - aero_drag - self.rolling_res_mps2

        speed_mps = max(0.0, speed_mps + net_accel * dt)

        # Soft-limit to segment/corner speed limits.
        speed_limit_mps = max(0.0, speed_limit_kmh / 3.6)
        if speed_mps > speed_limit_mps:
            bleed = min(speed_mps - speed_limit_mps, self.max_brake_decel_mps2 * 0.55 * dt)
            speed_mps -= bleed

        state.speed_kmh = speed_mps * 3.6
        state.rpm = self._calc_rpm(state.speed_kmh, state.gear)
        self._auto_shift(state)
        state.rpm = self._calc_rpm(state.speed_kmh, state.gear)

        state.position_m += speed_mps * dt
        state.lap_time_s += dt

        while state.position_m >= track_length_m:
            state.position_m -= track_length_m
            state.lap_count += 1
            state.last_lap_time_s = state.lap_time_s
            if state.best_lap_time_s <= 0.0 or state.lap_time_s < state.best_lap_time_s:
                state.best_lap_time_s = state.lap_time_s
            state.lap_time_s = 0.0
