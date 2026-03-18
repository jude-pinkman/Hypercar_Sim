"""
Tyre Degradation System for Hypercar/F1 Race Simulator
Models compound selection, grip, wear, and their effect on
corner speed, acceleration, and lap time.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Compound definitions
# ---------------------------------------------------------------------------

class TyreCompound(Enum):
    SOFT   = "soft"
    MEDIUM = "medium"
    HARD   = "hard"


@dataclass(frozen=True)
class CompoundSpec:
    """Static specification for a tyre compound."""
    name: str
    # Peak grip multiplier (applied to tyre_grip on a fresh tyre)
    peak_grip: float
    # Rate at which grip is lost per lap (fraction of peak_grip lost per lap)
    wear_rate_per_lap: float
    # Total viable life in laps before the tyre is considered worn-out
    max_life_laps: int
    # How many laps the compound takes to reach peak operating temperature
    warmup_laps: float
    # Additional lap-time penalty (seconds) due to reduced cornering / traction
    # when the tyre is degraded; scales linearly with wear fraction.
    max_laptime_penalty_s: float


COMPOUND_SPECS: Dict[TyreCompound, CompoundSpec] = {
    TyreCompound.SOFT: CompoundSpec(
        name            = "Soft",
        peak_grip       = 1.10,          # +10 % grip over baseline
        wear_rate_per_lap = 0.028,       # loses ~2.8 % of peak grip per lap
        max_life_laps   = 20,
        warmup_laps     = 1.0,
        max_laptime_penalty_s = 4.5,     # up to +4.5 s/lap when fully worn
    ),
    TyreCompound.MEDIUM: CompoundSpec(
        name            = "Medium",
        peak_grip       = 1.04,          # +4 % grip over baseline
        wear_rate_per_lap = 0.018,
        max_life_laps   = 32,
        warmup_laps     = 1.5,
        max_laptime_penalty_s = 3.0,
    ),
    TyreCompound.HARD: CompoundSpec(
        name            = "Hard",
        peak_grip       = 0.98,          # −2 % grip (lower peak, more durable)
        wear_rate_per_lap = 0.010,
        max_life_laps   = 50,
        warmup_laps     = 2.5,
        max_laptime_penalty_s = 1.8,
    ),
}


# ---------------------------------------------------------------------------
# Tyre state
# ---------------------------------------------------------------------------

@dataclass
class Tyre:
    """
    Mutable tyre state attached to a single car.

    The degradation model uses two mechanisms:
    1. **Thermal warm-up** – grip builds linearly from 80 % of peak over
       ``warmup_laps`` laps to reach ``peak_grip``.
    2. **Wear degradation** – grip decays exponentially after the warm-up
       phase, parameterised by ``wear_rate_per_lap``.  An additional
       stochastic term (``±noise_factor``) is added to give each tyre a
       slightly unique degradation curve.
    """

    compound: TyreCompound
    # Optional small noise so identical cars wear slightly differently.
    noise_factor: float = 0.0

    # Accumulated laps on this set (fractional laps supported)
    laps_done: float = field(default=0.0, init=False)

    # Cached current grip multiplier (updated on each lap / step)
    _current_grip: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._current_grip = self._compute_grip(self.laps_done)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def spec(self) -> CompoundSpec:
        return COMPOUND_SPECS[self.compound]

    @property
    def wear_fraction(self) -> float:
        """0.0 = brand new, 1.0 = fully worn out."""
        return min(self.laps_done / self.spec.max_life_laps, 1.0)

    @property
    def grip_multiplier(self) -> float:
        """Current grip multiplier to apply to the car's base tyre_grip."""
        return self._current_grip

    @property
    def is_worn_out(self) -> bool:
        return self.laps_done >= self.spec.max_life_laps

    @property
    def corner_speed_factor(self) -> float:
        """
        Fraction of nominal corner speed available.
        Fully fresh soft  → ~1.10 × nominal.
        Fully worn soft   → can drop below 1.0.
        """
        return self._current_grip

    @property
    def acceleration_factor(self) -> float:
        """
        Fraction of nominal acceleration available.
        Grip loss reduces traction-limited acceleration.
        Effect is slightly less severe than cornering.
        """
        # Acceleration loss is 60 % as sensitive to grip loss as cornering.
        base_grip = COMPOUND_SPECS[TyreCompound.MEDIUM].peak_grip
        grip_delta = self._current_grip - base_grip
        return 1.0 + 0.60 * grip_delta

    @property
    def laptime_delta_s(self) -> float:
        """
        Extra lap-time (seconds) caused by tyre degradation.
        Positive = slower than a fresh tyre of this compound.
        """
        return self.spec.max_laptime_penalty_s * self.wear_fraction

    def advance_laps(self, laps: float = 1.0) -> None:
        """Progress tyre wear by ``laps`` laps."""
        self.laps_done += laps
        self._current_grip = self._compute_grip(self.laps_done)

    def get_status(self) -> Dict:
        """Return a summary dict useful for logging / UI."""
        return {
            "compound":           self.compound.value,
            "laps_done":          round(self.laps_done, 1),
            "wear_pct":           round(self.wear_fraction * 100, 1),
            "grip_multiplier":    round(self._current_grip, 4),
            "corner_speed_factor": round(self.corner_speed_factor, 4),
            "accel_factor":       round(self.acceleration_factor, 4),
            "laptime_delta_s":    round(self.laptime_delta_s, 3),
            "is_worn_out":        self.is_worn_out,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_grip(self, laps: float) -> float:
        """
        Grip model:

          Phase 1 – warm-up  (0 … warmup_laps):
            grip = peak_grip * (0.80 + 0.20 * progress)

          Phase 2 – degradation (warmup_laps … max_life_laps):
            grip = peak_grip * exp(-k * (laps - warmup_laps))

            where k = wear_rate_per_lap adjusted by noise.

          Grip is clamped to [0.40, 1.20].
        """
        spec = COMPOUND_SPECS[self.compound]
        effective_k = spec.wear_rate_per_lap * (1.0 + self.noise_factor)

        if laps <= spec.warmup_laps:
            # Linear ramp from 80 % → 100 % of peak_grip
            progress = laps / spec.warmup_laps if spec.warmup_laps > 0 else 1.0
            grip = spec.peak_grip * (0.80 + 0.20 * progress)
        else:
            wear_laps = laps - spec.warmup_laps
            grip = spec.peak_grip * (
                (1.0 - effective_k) ** wear_laps
            )

        return max(0.40, min(1.20, grip))


# ---------------------------------------------------------------------------
# Tyre factory / strategy helpers
# ---------------------------------------------------------------------------

class TyreStrategy:
    """
    Manages tyre stints for a single car across an entire race.

    A *stint* is a run on a single tyre set.  Stints are added in order;
    the strategy decides when to pit based on ``max_life_laps`` or an
    explicit override.

    When used with PitStopManager the manager drives all pit decisions;
    ``advance_lap`` and ``pit_stop`` are still the only mutating calls.
    """

    def __init__(self, stints: List[TyreCompound], noise_factor: float = 0.0):
        """
        Parameters
        ----------
        stints:
            Ordered list of compounds to use.
        noise_factor:
            Small ±variation applied to wear rate so each car differs.
        """
        if len(stints) < 1:
            raise ValueError("At least one tyre stint is required.")
        self._stints      = stints
        self._noise       = noise_factor
        self._stint_index = 0
        self.current_tyre: Tyre         = Tyre(stints[0], noise_factor=noise_factor)
        self.pit_history:  List[Dict]   = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def stints_remaining(self) -> int:
        return len(self._stints) - 1 - self._stint_index

    @property
    def total_stints(self) -> int:
        return len(self._stints)

    @property
    def current_stint_index(self) -> int:
        return self._stint_index

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def should_pit(self) -> bool:
        """True if the current tyre is worn out and a fresh set is available.

        NOTE: When PitStopManager is active, prefer using the manager's
        ``notify_lap_complete`` instead of polling this directly.
        """
        return self.current_tyre.is_worn_out and self.stints_remaining > 0

    def pit_stop(self, current_lap: int) -> Optional[TyreCompound]:
        """
        Fit the next set of tyres.

        Returns the new compound enum, or None if no stints remain.
        Safe to call multiple times — a second call on the same lap will be
        a no-op if the stint has already advanced (guarded by stints_remaining).
        """
        if self.stints_remaining <= 0:
            return None
        old_compound = self.current_tyre.compound
        self._stint_index += 1
        new_compound = self._stints[self._stint_index]
        self.pit_history.append({
            "lap":          current_lap,
            "old_compound": old_compound.value,
            "new_compound": new_compound.value,
        })
        self.current_tyre = Tyre(new_compound, noise_factor=self._noise)
        return new_compound

    def advance_lap(self) -> None:
        """Accumulate one lap of tyre wear.  Call exactly once per completed lap."""
        self.current_tyre.advance_laps(1.0)


# ---------------------------------------------------------------------------
# Degradation model – standalone convenience class
# ---------------------------------------------------------------------------

class TyreDegradationModel:
    """
    Applies tyre degradation effects to a car's base performance figures.

    This is the bridge between the Tyre/TyreStrategy objects and the
    physics parameters consumed by RaceSimulator / CircuitRaceSimulator.
    """

    @staticmethod
    def effective_tyre_grip(base_grip: float, tyre: Tyre) -> float:
        """Scale the car's base tyre_grip by the compound's current multiplier."""
        return base_grip * tyre.grip_multiplier

    @staticmethod
    def effective_max_corner_speed(nominal_corner_speed: float, tyre: Tyre) -> float:
        """
        Reduce maximum cornering speed as tyre wears.
        v_corner = v_nominal × corner_speed_factor
        """
        return nominal_corner_speed * tyre.corner_speed_factor

    @staticmethod
    def effective_acceleration(base_acceleration: float, tyre: Tyre) -> float:
        """
        Reduce traction-limited acceleration as grip drops.
        a_eff = a_base × acceleration_factor
        """
        return base_acceleration * tyre.acceleration_factor

    @staticmethod
    def apply_to_laptime(base_laptime_s: float, tyre: Tyre) -> float:
        """
        Return an estimated lap time accounting for tyre degradation.
        base_laptime_s should be the theoretical flat-out lap time.
        """
        return base_laptime_s + tyre.laptime_delta_s

    @staticmethod
    def degradation_report(tyre: Tyre) -> str:
        """Human-readable one-liner for console output."""
        s = tyre.get_status()
        return (
            f"[{s['compound'].upper():6s}] "
            f"Lap {s['laps_done']:>5.1f} | "
            f"Wear {s['wear_pct']:>5.1f}% | "
            f"Grip ×{s['grip_multiplier']:.3f} | "
            f"Corner ×{s['corner_speed_factor']:.3f} | "
            f"Accel ×{s['accel_factor']:.3f} | "
            f"ΔTime +{s['laptime_delta_s']:.2f}s"
            + (" ⚠ WORN" if s["is_worn_out"] else "")
        )
