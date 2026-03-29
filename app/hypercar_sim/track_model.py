"""Track model for a simplified Albert Park Circuit simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class TrackSegment:
    """Represents either a straight or corner section of the track."""

    name: str
    kind: str  # "straight" or "corner"
    length_m: float
    radius_m: Optional[float] = None
    max_speed_kmh: Optional[float] = None


class AlbertParkCircuit:
    """Simplified Albert Park segment model with straights and corners."""

    def __init__(self) -> None:
        # This is a simplified shape of Albert Park (not GPS-accurate),
        # tuned to create realistic speed transitions and braking zones.
        self.segments: List[TrackSegment] = [
            TrackSegment("Start/Finish Straight", "straight", 520.0),
            TrackSegment("Turn 1", "corner", 95.0, radius_m=62.0, max_speed_kmh=148.0),
            TrackSegment("Short Straight 1", "straight", 260.0),
            TrackSegment("Turn 3", "corner", 105.0, radius_m=54.0, max_speed_kmh=132.0),
            TrackSegment("Straight 2", "straight", 410.0),
            TrackSegment("Turn 4", "corner", 90.0, radius_m=46.0, max_speed_kmh=122.0),
            TrackSegment("Straight 3", "straight", 360.0),
            TrackSegment("Turn 6", "corner", 135.0, radius_m=78.0, max_speed_kmh=168.0),
            TrackSegment("Lakeside Straight", "straight", 540.0),
            TrackSegment("Turn 9", "corner", 110.0, radius_m=64.0, max_speed_kmh=152.0),
            TrackSegment("Back Straight", "straight", 720.0),
            TrackSegment("Turn 11", "corner", 130.0, radius_m=70.0, max_speed_kmh=156.0),
            TrackSegment("Straight 4", "straight", 285.0),
            TrackSegment("Turn 13", "corner", 115.0, radius_m=52.0, max_speed_kmh=134.0),
            TrackSegment("Straight 5", "straight", 305.0),
            TrackSegment("Turn 15", "corner", 120.0, radius_m=58.0, max_speed_kmh=140.0),
            TrackSegment("Final Short Straight", "straight", 240.0),
            TrackSegment("Turn 16", "corner", 118.0, radius_m=50.0, max_speed_kmh=128.0),
            TrackSegment("Pit Straight Return", "straight", 430.0),
        ]

        self.total_length_m: float = sum(seg.length_m for seg in self.segments)

    def locate(self, distance_m: float) -> Tuple[int, TrackSegment, float]:
        """Find the segment index and local distance for an absolute track distance."""
        wrapped = distance_m % self.total_length_m
        cursor = 0.0

        for idx, seg in enumerate(self.segments):
            end = cursor + seg.length_m
            if wrapped < end:
                return idx, seg, wrapped - cursor
            cursor = end

        # Fallback for floating-point edge cases.
        last_idx = len(self.segments) - 1
        return last_idx, self.segments[last_idx], self.segments[last_idx].length_m

    def next_corner_info(self, distance_m: float) -> Tuple[Optional[TrackSegment], float]:
        """Return the next corner segment and distance to its start."""
        idx, current, local = self.locate(distance_m)

        if current.kind == "corner":
            return current, 0.0

        dist_to_next_start = current.length_m - local
        n = len(self.segments)

        for step in range(1, n + 1):
            nxt = self.segments[(idx + step) % n]
            if nxt.kind == "corner":
                return nxt, dist_to_next_start
            dist_to_next_start += nxt.length_m

        return None, float("inf")
