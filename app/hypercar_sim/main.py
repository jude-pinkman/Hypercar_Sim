"""Entry point for the hypercar_sim real-time Albert Park lap simulation."""

from __future__ import annotations

import time

from .ai_driver import AIDriver
from .physics_engine import CarState, PhysicsEngine
from .telemetry import lap_summary, telemetry_line
from .track_model import AlbertParkCircuit


def run_simulation(target_laps: int = 1) -> None:
    dt = 1.0 / 60.0  # 60 Hz update rate

    track = AlbertParkCircuit()
    physics = PhysicsEngine()
    driver = AIDriver(physics)
    state = CarState()

    print("=" * 88)
    print("hypercar_sim :: Albert Park Telemetry Simulation")
    print(f"Track length: {track.total_length_m:.1f} m | Update rate: 60 Hz | Target laps: {target_laps}")
    print("=" * 88)

    wall_start = time.perf_counter()
    next_tick = wall_start

    while state.lap_count < target_laps:
        frame_start = time.perf_counter()

        _, segment, _ = track.locate(state.position_m)
        cmd = driver.decide(state, track)

        physics.update(
            state=state,
            target_throttle=cmd.throttle,
            target_brake=cmd.brake,
            dt=dt,
            speed_limit_kmh=cmd.speed_limit_kmh,
            track_length_m=track.total_length_m,
        )

        print(telemetry_line(state, segment), flush=True)

        # Keep simulation in real time at 60 Hz.
        next_tick += dt
        sleep_for = next_tick - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)

        # Guard against timing drift if machine is overloaded.
        if (time.perf_counter() - frame_start) > 0.25:
            next_tick = time.perf_counter()

    elapsed_wall = time.perf_counter() - wall_start

    print("=" * 88)
    print("Simulation complete")
    print(f"Completed laps: {state.lap_count}")
    print(lap_summary(state))
    print(f"Wall-clock runtime: {elapsed_wall:.2f}s")
    print("=" * 88)


if __name__ == "__main__":
    run_simulation(target_laps=1)
