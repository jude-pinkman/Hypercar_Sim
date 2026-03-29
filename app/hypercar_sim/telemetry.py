"""Telemetry formatting and output utilities."""

from __future__ import annotations

from .physics_engine import CarState
from .track_model import TrackSegment


def format_time(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = seconds - mins * 60
    return f"{mins:02d}:{secs:06.3f}"


def telemetry_line(state: CarState, segment: TrackSegment) -> str:
    return (
        f"Speed: {state.speed_kmh:6.1f} km/h | "
        f"RPM: {state.rpm:7.0f} | "
        f"Gear: {state.gear} | "
        f"Throttle: {state.throttle:0.2f} | "
        f"Brake: {state.brake:0.2f} | "
        f"Lap: {state.lap_count + 1} | "
        f"Segment: {segment.name}"
    )


def lap_summary(state: CarState) -> str:
    best = format_time(state.best_lap_time_s) if state.best_lap_time_s > 0 else "N/A"
    last = format_time(state.last_lap_time_s) if state.last_lap_time_s > 0 else "N/A"
    return f"Last Lap: {last} | Best Lap: {best}"
