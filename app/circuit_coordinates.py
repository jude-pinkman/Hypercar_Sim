"""
F1 Circuit Coordinates — 2026

Albert Park (AUS): coordinates are embedded directly in TrackRenderer.js
as AUS_TRACK_POINTS (300 arc-length-sampled points from the official SVG).
The circuit is rendered using Path2D with the exact SVG bezier data.

Other circuits use polyline coordinates below.
"""

CIRCUIT_COORDINATES = {

    "MON": [  # Monaco — Street circuit
        {"x": -20.0, "y":   0.0, "sector": 1, "drsZone": False, "pitLane": True,  "corner": 0},
        {"x": -10.0, "y":   0.0, "sector": 1, "drsZone": False, "pitLane": True,  "corner": 0},
        {"x":   0.0, "y":   0.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 1},
        {"x":  20.0, "y":  20.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 1},
        {"x":  35.0, "y":  45.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 2},
        {"x":  40.0, "y":  75.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 3},
        {"x":  35.0, "y": 105.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 4},
        {"x":  20.0, "y": 125.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 5},
        {"x":  -5.0, "y": 140.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 6},
        {"x": -35.0, "y": 145.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 7},
        {"x": -60.0, "y": 135.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 8},
        {"x": -75.0, "y": 115.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 9},
        {"x": -80.0, "y":  90.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 10},
        {"x": -75.0, "y":  65.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 11},
        {"x": -60.0, "y":  45.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 12},
        {"x": -35.0, "y":  30.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 0},
    ],

    "SPA": [  # Spa-Francorchamps
        {"x":   0.0, "y":   0.0, "sector": 1, "drsZone": True,  "pitLane": True,  "corner": 0},
        {"x":  60.0, "y":   0.0, "sector": 1, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x": 120.0, "y":   5.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 1},
        {"x": 140.0, "y":  25.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 2},
        {"x": 145.0, "y":  50.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 3},
        {"x": 140.0, "y":  75.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 4},
        {"x": 120.0, "y":  90.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 5},
        {"x":  90.0, "y":  95.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 6},
        {"x":  60.0, "y":  90.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 7},
        {"x":  35.0, "y":  75.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 8},
        {"x":  20.0, "y":  55.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 9},
        {"x":  15.0, "y":  30.0, "sector": 3, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x":  20.0, "y":  10.0, "sector": 3, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x":  50.0, "y": -10.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 10},
        {"x":  95.0, "y":   5.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 11},
    ],

    "GBR": [  # Silverstone
        {"x":   0.0, "y":   0.0, "sector": 1, "drsZone": True,  "pitLane": True,  "corner": 0},
        {"x":  50.0, "y":   0.0, "sector": 1, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x":  90.0, "y":  10.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 1},
        {"x": 110.0, "y":  30.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 2},
        {"x": 120.0, "y":  55.0, "sector": 1, "drsZone": False, "pitLane": False, "corner": 3},
        {"x": 115.0, "y":  80.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 4},
        {"x":  95.0, "y": 100.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 5},
        {"x":  70.0, "y": 110.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 6},
        {"x":  45.0, "y": 110.0, "sector": 2, "drsZone": False, "pitLane": False, "corner": 7},
        {"x":  25.0, "y": 100.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 8},
        {"x":  10.0, "y":  85.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 9},
        {"x":   5.0, "y":  65.0, "sector": 3, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x":  30.0, "y":  30.0, "sector": 3, "drsZone": True,  "pitLane": False, "corner": 0},
        {"x":  55.0, "y":  20.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 10},
        {"x":  80.0, "y":  15.0, "sector": 3, "drsZone": False, "pitLane": False, "corner": 11},
    ],
}


def get_circuit_coordinates(circuit_id: str):
    """Return coordinate list for a circuit, or None if not defined.
    AUS uses embedded SVG path in TrackRenderer.js — returns None here."""
    return CIRCUIT_COORDINATES.get(circuit_id)
