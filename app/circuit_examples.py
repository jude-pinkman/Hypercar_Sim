"""
Circuit Race Simulator - Usage Examples
Demonstrates racing on different circuits with realistic physics
"""

from circuit_race_simulator import (
    RaceSimulator, Circuit, TrackSection, SectionType,
    create_monaco_circuit, create_monza_circuit, create_silverstone_circuit,
    create_f1_grid
)


def example_monaco_race():
    """Example 1: Monaco GP - Tight street circuit"""
    print("\n" + "="*90)
    print("EXAMPLE 1: Monaco Grand Prix")
    print("="*90)
    print("Circuit characteristics: Tight corners, slow speeds, high precision")
    print()
    
    circuit = create_monaco_circuit()
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add top 10 drivers for faster simulation
    f1_grid = create_f1_grid()[:10]
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=True, update_interval=20.0)
    
    # Analysis
    print(f"\n🎯 Monaco is known for:")
    print(f"   • Slowest average speeds in F1")
    print(f"   • Most corners: {circuit.get_corner_count()}")
    print(f"   • Overtaking difficulty: EXTREME")
    print(f"\n📈 Results show:")
    print(f"   • Winner averaged {results[0]['average_lap']:.2f}s per lap")
    print(f"   • Fastest lap: {min(r['fastest_lap'] for r in results):.2f}s")
    print(f"   • Gap from 1st to 10th: {results[-1]['finish_time'] - results[0]['finish_time']:.2f}s")


def example_monza_race():
    """Example 2: Italian GP - High speed circuit"""
    print("\n" + "="*90)
    print("EXAMPLE 2: Italian Grand Prix at Monza")
    print("="*90)
    print("Circuit characteristics: Long straights, high speeds, low downforce")
    print()
    
    circuit = create_monza_circuit()
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add top 10 drivers
    f1_grid = create_f1_grid()[:10]
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=True, update_interval=20.0)
    
    # Analysis
    print(f"\n🎯 Monza is known for:")
    print(f"   • Fastest average speeds in F1")
    print(f"   • Long straights with DRS zones")
    print(f"   • Low drag setups")
    print(f"\n📈 Results show:")
    print(f"   • Winner averaged {results[0]['average_lap']:.2f}s per lap")
    print(f"   • Fastest lap: {min(r['fastest_lap'] for r in results):.2f}s")
    print(f"   • Average lap faster than Monaco: {True if results[0]['average_lap'] < 85 else False}")


def example_silverstone_race():
    """Example 3: British GP - Fast and flowing"""
    print("\n" + "="*90)
    print("EXAMPLE 3: British Grand Prix at Silverstone")
    print("="*90)
    print("Circuit characteristics: Fast corners, flowing layout, high downforce")
    print()
    
    circuit = create_silverstone_circuit()
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add top 10 drivers
    f1_grid = create_f1_grid()[:10]
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=True, update_interval=20.0)
    
    # Analysis
    print(f"\n🎯 Silverstone is known for:")
    print(f"   • High-speed corners (Copse, Maggotts-Becketts)")
    print(f"   • Balanced car setup required")
    print(f"   • Medium downforce")
    print(f"\n📈 Results show:")
    print(f"   • Winner averaged {results[0]['average_lap']:.2f}s per lap")
    print(f"   • Fastest lap: {min(r['fastest_lap'] for r in results):.2f}s")


def example_circuit_comparison():
    """Example 4: Compare lap times across different circuits"""
    print("\n" + "="*90)
    print("EXAMPLE 4: Circuit Comparison - Same Cars, Different Tracks")
    print("="*90)
    
    circuits = [
        create_monaco_circuit(),
        create_monza_circuit(),
        create_silverstone_circuit()
    ]
    
    # Use same car setup
    test_car = {
        "driver_name": "Test Driver",
        "team": "Test Team",
        "max_speed": 93.0,
        "acceleration": 12.0,
        "tyre_grip": 0.90,
        "drag_coefficient": 0.74,
        "cornering_ability": 0.90
    }
    
    results_by_circuit = {}
    
    for circuit in circuits:
        # Run short race (5 laps for quick comparison)
        circuit.number_of_laps = 5
        simulator = RaceSimulator(circuit=circuit, timestep=0.1)
        simulator.add_car(**test_car)
        
        results = simulator.run_simulation(verbose=False)
        results_by_circuit[circuit.name] = {
            'fastest_lap': results[0]['fastest_lap'],
            'average_lap': results[0]['average_lap'],
            'total_time': results[0]['finish_time']
        }
    
    # Print comparison
    print(f"\n{'Circuit':<30} {'Fastest Lap':<15} {'Average Lap':<15} {'5-Lap Time':<15}")
    print("-" * 80)
    
    for circuit_name, data in results_by_circuit.items():
        print(f"{circuit_name:<30} {data['fastest_lap']:<15.2f} "
              f"{data['average_lap']:<15.2f} {data['total_time']:<15.2f}")
    
    print(f"\n💡 Insights:")
    print(f"   • Monaco: Slowest lap times due to tight corners")
    print(f"   • Monza: Fastest lap times due to long straights")
    print(f"   • Silverstone: Balanced, fast flowing corners")


def example_custom_circuit():
    """Example 5: Create a custom circuit"""
    print("\n" + "="*90)
    print("EXAMPLE 5: Custom Circuit Creation")
    print("="*90)
    
    # Create a simple oval circuit
    circuit = Circuit(
        name="Custom Speedway",
        lap_length_km=2.5,
        number_of_laps=40
    )
    
    position = 0.0
    
    # Long straight 1
    circuit.sections.append(TrackSection(
        SectionType.STRAIGHT, 800, position, position + 800, drs_zone=True
    ))
    position += 800
    
    # Turn 1 - banking
    circuit.sections.append(TrackSection(
        SectionType.CORNER, 200, position, position + 200, 
        corner_radius=100, corner_angle=90
    ))
    position += 200
    
    # Short straight
    circuit.sections.append(TrackSection(
        SectionType.STRAIGHT, 150, position, position + 150
    ))
    position += 150
    
    # Turn 2
    circuit.sections.append(TrackSection(
        SectionType.CORNER, 200, position, position + 200,
        corner_radius=100, corner_angle=90
    ))
    position += 200
    
    # Long straight 2
    circuit.sections.append(TrackSection(
        SectionType.STRAIGHT, 800, position, position + 800, drs_zone=True
    ))
    position += 800
    
    # Turn 3
    circuit.sections.append(TrackSection(
        SectionType.CORNER, 200, position, position + 200,
        corner_radius=100, corner_angle=90
    ))
    position += 200
    
    # Short straight
    circuit.sections.append(TrackSection(
        SectionType.STRAIGHT, 150, position, position + 150
    ))
    position += 150
    
    # Turn 4 - final corner
    remaining = circuit.lap_length - position
    circuit.sections.append(TrackSection(
        SectionType.CORNER, remaining, position, circuit.lap_length,
        corner_radius=100, corner_angle=90
    ))
    
    print(f"Created: {circuit.name}")
    print(f"Lap length: {circuit.lap_length_km}km")
    print(f"Corners: {circuit.get_corner_count()}")
    print(f"Straights: {circuit.get_straight_count()}")
    print(f"DRS zones: {sum(1 for s in circuit.sections if hasattr(s, 'drs_zone') and s.drs_zone)}")
    
    # Run a quick race
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add 5 cars
    for i, car_spec in enumerate(create_f1_grid()[:5], 1):
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=True, update_interval=15.0)


def example_lap_time_evolution():
    """Example 6: Track lap time evolution during race"""
    print("\n" + "="*90)
    print("EXAMPLE 6: Lap Time Evolution Analysis")
    print("="*90)
    
    circuit = create_silverstone_circuit()
    circuit.number_of_laps = 20  # Shorter race for demo
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add top 3 drivers
    for car_spec in create_f1_grid()[:3]:
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=False)
    
    # Print lap-by-lap analysis for winner
    winner = results[0]
    print(f"\n🏆 Winner: {winner['driver']} ({winner['team']})")
    print(f"\nLap-by-Lap Times:")
    print(f"{'Lap':<6} {'Time':<10} {'Delta to Best':<15} {'Trend':<10}")
    print("-" * 50)
    
    best_lap = min(winner['lap_times'])
    
    for lap_num, lap_time in enumerate(winner['lap_times'], 1):
        delta = lap_time - best_lap
        
        # Determine trend
        if lap_num == 1:
            trend = "Start"
        else:
            prev_time = winner['lap_times'][lap_num - 2]
            if lap_time < prev_time:
                trend = "↓ Faster"
            elif lap_time > prev_time:
                trend = "↑ Slower"
            else:
                trend = "→ Same"
        
        marker = "🔥" if lap_time == best_lap else ""
        print(f"{lap_num:<6} {lap_time:<10.2f} {delta:<15.3f} {trend:<10} {marker}")
    
    print(f"\n📊 Statistics:")
    print(f"   Best lap: {best_lap:.2f}s (Lap {winner['lap_times'].index(best_lap) + 1})")
    print(f"   Worst lap: {max(winner['lap_times']):.2f}s")
    print(f"   Average: {winner['average_lap']:.2f}s")
    print(f"   Consistency (range): {max(winner['lap_times']) - min(winner['lap_times']):.2f}s")


def example_team_battle():
    """Example 7: Team vs Team battle"""
    print("\n" + "="*90)
    print("EXAMPLE 7: Team Battle - Red Bull vs Ferrari vs Mercedes")
    print("="*90)
    
    circuit = create_monza_circuit()
    circuit.number_of_laps = 25
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add only top 3 teams (6 cars total)
    f1_grid = create_f1_grid()
    teams_to_include = ["Red Bull Racing", "Ferrari", "Mercedes"]
    
    for car_spec in f1_grid:
        if car_spec['team'] in teams_to_include:
            simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=True, update_interval=15.0)
    
    # Team analysis
    print(f"\n🏁 TEAM STANDINGS")
    print("="*90)
    
    team_results = {}
    for result in results:
        team = result['team']
        if team not in team_results:
            team_results[team] = {
                'positions': [],
                'total_points': 0,
                'best_position': 100,
                'fastest_lap': None
            }
        
        team_results[team]['positions'].append(result['position'])
        team_results[team]['best_position'] = min(team_results[team]['best_position'], result['position'])
        
        # F1 points system (simplified)
        points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8}
        team_results[team]['total_points'] += points_map.get(result['position'], 0)
        
        if team_results[team]['fastest_lap'] is None or result['fastest_lap'] < team_results[team]['fastest_lap']:
            team_results[team]['fastest_lap'] = result['fastest_lap']
    
    # Sort by points
    sorted_teams = sorted(team_results.items(), key=lambda x: x[1]['total_points'], reverse=True)
    
    print(f"{'Team':<25} {'Points':<10} {'Positions':<20} {'Fastest Lap':<12}")
    print("-" * 80)
    
    for team, data in sorted_teams:
        positions_str = ", ".join([f"P{p}" for p in sorted(data['positions'])])
        print(f"{team:<25} {data['total_points']:<10} {positions_str:<20} {data['fastest_lap']:<12.2f}")


def example_qualifying_vs_race():
    """Example 8: Simulate qualifying lap vs race pace"""
    print("\n" + "="*90)
    print("EXAMPLE 8: Qualifying Lap vs Race Pace")
    print("="*90)
    
    circuit = create_monaco_circuit()
    
    # Qualifying simulation (1 flying lap)
    print("\n🏁 QUALIFYING SESSION (Single lap push)")
    circuit.number_of_laps = 1
    quali_sim = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add top 5 drivers with slight boost for quali mode
    for car_spec in create_f1_grid()[:5]:
        # Boost performance for qualifying (lower fuel, engine mode, fresh tires)
        quali_sim.add_car(
            driver_name=car_spec['driver_name'],
            team=car_spec['team'],
            max_speed=car_spec['max_speed'] * 1.03,  # 3% boost
            acceleration=car_spec['acceleration'] * 1.05,  # 5% boost
            tyre_grip=car_spec['tyre_grip'] * 1.02,  # 2% boost
            drag_coefficient=car_spec['drag_coefficient'] * 0.97,  # Less drag
            cornering_ability=car_spec['cornering_ability'] * 1.02
        )
    
    quali_results = quali_sim.run_simulation(verbose=False)
    
    print(f"{'Pos':<5} {'Driver':<20} {'Team':<20} {'Time':<10}")
    print("-" * 60)
    for result in quali_results:
        print(f"{result['position']:<5} {result['driver']:<20} {result['team']:<20} {result['fastest_lap']:<10.2f}")
    
    # Race simulation (10 laps)
    print("\n\n🏁 RACE (10 laps, race pace)")
    circuit.number_of_laps = 10
    race_sim = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add same drivers with race setup
    for car_spec in create_f1_grid()[:5]:
        race_sim.add_car(**car_spec)
    
    race_results = race_sim.run_simulation(verbose=False)
    
    print(f"{'Pos':<5} {'Driver':<20} {'Team':<20} {'Fastest Lap':<12} {'Avg Lap':<10}")
    print("-" * 75)
    for result in race_results:
        print(f"{result['position']:<5} {result['driver']:<20} {result['team']:<20} "
              f"{result['fastest_lap']:<12.2f} {result['average_lap']:<10.2f}")
    
    print(f"\n💡 Notice:")
    print(f"   • Qualifying laps are typically 1-2s faster than race laps")
    print(f"   • Race pace is more consistent but slower due to fuel load")


if __name__ == "__main__":
    print("\n\n")
    print("╔" + "="*88 + "╗")
    print("║" + " "*20 + "CIRCUIT RACE SIMULATOR - COMPREHENSIVE EXAMPLES" + " "*21 + "║")
    print("╚" + "="*88 + "╝")
    
    # Run the examples you want (comment/uncomment as needed)
    
    # example_monaco_race()
    # example_monza_race()
    # example_silverstone_race()
    # example_circuit_comparison()
    # example_custom_circuit()
    example_lap_time_evolution()
    # example_team_battle()
    # example_qualifying_vs_race()
    
    print("\n\n✅ Examples completed!")
