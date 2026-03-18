"""
Circuit Registry
Provides access to all available F1 circuits
"""

from app.circuit_race_simulator import (
    Circuit,
    create_monaco_circuit,
    create_monza_circuit,
    create_silverstone_circuit
)


AVAILABLE_CIRCUITS = {
    'monaco': {
        'name': 'Monaco Grand Prix',
        'location': 'Monte Carlo, Monaco',
        'lap_length_km': 3.337,
        'description': 'Tight street circuit with slow corners',
        'difficulty': 'Extreme',
        'function': create_monaco_circuit
    },
    'monza': {
        'name': 'Italian Grand Prix',
        'location': 'Monza, Italy',
        'lap_length_km': 5.793,
        'description': 'High-speed circuit with long straights',
        'difficulty': 'Medium',
        'function': create_monza_circuit
    },
    'silverstone': {
        'name': 'British Grand Prix',
        'location': 'Silverstone, UK',
        'lap_length_km': 5.891,
        'description': 'Fast and flowing with high-speed corners',
        'difficulty': 'High',
        'function': create_silverstone_circuit
    }
}


def get_circuit(circuit_key: str) -> Circuit:
    """Get a circuit by its key"""
    if circuit_key.lower() in AVAILABLE_CIRCUITS:
        return AVAILABLE_CIRCUITS[circuit_key.lower()]['function']()
    return None


def list_circuits():
    """List all available circuits with details"""
    return [
        {
            'key': key,
            'name': data['name'],
            'location': data['location'],
            'lap_length_km': data['lap_length_km'],
            'description': data['description'],
            'difficulty': data['difficulty']
        }
        for key, data in AVAILABLE_CIRCUITS.items()
    ]
