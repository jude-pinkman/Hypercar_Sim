"""
Test Suite for Circuit Race Simulator
Verifies circuit physics, lap timing, and corner/straight dynamics
"""

import sys
from circuit_race_simulator import (
    RaceSimulator, Circuit, TrackSection, SectionType,
    create_monaco_circuit, create_monza_circuit, create_silverstone_circuit,
    create_f1_grid, Car
)


def test_track_section_creation():
    """Test 1: Track section creation and speed calculation"""
    print("\n" + "="*60)
    print("TEST 1: Track Section Creation")
    print("="*60)
    
    # Create a straight
    straight = TrackSection(
        section_type=SectionType.STRAIGHT,
        length=500,
        start_position=0,
        end_position=500,
        drs_zone=True
    )
    
    assert straight.section_type == SectionType.STRAIGHT
    assert straight.length == 500
    assert straight.drs_zone == True
    
    # Create a corner with auto-calculated max speed
    corner = TrackSection(
        section_type=SectionType.CORNER,
        length=100,
        start_position=500,
        end_position=600,
        corner_radius=50,
        corner_angle=90
    )
    
    assert corner.section_type == SectionType.CORNER
    assert corner.max_speed is not None, "Corner max speed should be auto-calculated"
    assert corner.max_speed > 0, "Max speed should be positive"
    
    print(f"✅ Track sections created successfully")
    print(f"   Straight: {straight.length}m, DRS: {straight.drs_zone}")
    print(f"   Corner: radius {corner.corner_radius}m, max speed: {corner.max_speed:.2f} m/s")
    return True


def test_circuit_creation():
    """Test 2: Circuit creation and properties"""
    print("\n" + "="*60)
    print("TEST 2: Circuit Creation")
    print("="*60)
    
    circuit = Circuit(
        name="Test Circuit",
        lap_length_km=4.0,
        number_of_laps=30
    )
    
    # Add sections
    pos = 0.0
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, pos, pos + 1000))
    pos += 1000
    circuit.sections.append(TrackSection(SectionType.CORNER, 200, pos, pos + 200, corner_radius=40, corner_angle=90))
    pos += 200
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 800, pos, pos + 800))
    pos += 800
    circuit.sections.append(TrackSection(SectionType.CORNER, 200, pos, pos + 200, corner_radius=40, corner_angle=90))
    pos += 200
    
    # Remaining
    remaining = circuit.lap_length - pos
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, remaining, pos, circuit.lap_length))
    
    assert circuit.lap_length == 4000, "Lap length should be 4000m"
    assert circuit.total_race_distance == 120000, "Total distance should be 120km"
    assert circuit.get_corner_count() == 2, "Should have 2 corners"
    assert circuit.get_straight_count() == 3, "Should have 3 straights"
    
    print(f"✅ Circuit created successfully")
    print(f"   Name: {circuit.name}")
    print(f"   Lap length: {circuit.lap_length_km}km")
    print(f"   Corners: {circuit.get_corner_count()}")
    print(f"   Straights: {circuit.get_straight_count()}")
    return True


def test_section_detection():
    """Test 3: Section detection at position"""
    print("\n" + "="*60)
    print("TEST 3: Section Detection")
    print("="*60)
    
    circuit = Circuit(name="Test", lap_length_km=2.0, number_of_laps=10)
    
    # Simple layout
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, 0, 1000))
    circuit.sections.append(TrackSection(SectionType.CORNER, 500, 1000, 1500, corner_radius=50))
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 500, 1500, 2000))
    
    # Test positions
    section_at_100 = circuit.get_section_at_position(100)
    assert section_at_100.section_type == SectionType.STRAIGHT
    
    section_at_1200 = circuit.get_section_at_position(1200)
    assert section_at_1200.section_type == SectionType.CORNER
    
    section_at_1700 = circuit.get_section_at_position(1700)
    assert section_at_1700.section_type == SectionType.STRAIGHT
    
    # Test position in second lap
    section_at_2100 = circuit.get_section_at_position(2100)  # 100m into lap 2
    assert section_at_2100.section_type == SectionType.STRAIGHT
    
    print(f"✅ Section detection working correctly")
    print(f"   Position 100m: {section_at_100.section_type.value}")
    print(f"   Position 1200m: {section_at_1200.section_type.value}")
    print(f"   Position 2100m (lap 2): {section_at_2100.section_type.value}")
    return True


def test_car_with_cornering():
    """Test 4: Car creation with cornering ability"""
    print("\n" + "="*60)
    print("TEST 4: Car with Cornering Ability")
    print("="*60)
    
    car = Car(
        driver_name="Test Driver",
        team="Test Team",
        max_speed=90.0,
        acceleration=12.0,
        tyre_grip=0.90,
        drag_coefficient=0.75,
        cornering_ability=0.88
    )
    
    assert car.cornering_ability == 0.88
    assert car.in_corner == False
    assert len(car.lap_times) == 0
    assert car.current_section is None
    
    print(f"✅ Car created with cornering ability")
    print(f"   Driver: {car.driver_name}")
    print(f"   Cornering ability: {car.cornering_ability}")
    return True


def test_speed_in_sections():
    """Test 5: Speed adjustment in different sections"""
    print("\n" + "="*60)
    print("TEST 5: Speed Adjustment in Sections")
    print("="*60)
    
    # Create simple circuit
    circuit = Circuit(name="Test", lap_length_km=2.0, number_of_laps=5)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, 0, 1000, drs_zone=True))
    circuit.sections.append(TrackSection(SectionType.CORNER, 500, 1000, 1500, corner_radius=30))
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 500, 1500, 2000))
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    car = simulator.add_car("Test", "Team", 90.0, 12.0, 0.90, 0.75, 0.88)
    
    # Get straight section
    straight_section = circuit.sections[0]
    target_straight = simulator._calculate_target_speed(car, straight_section)
    
    # Get corner section
    corner_section = circuit.sections[1]
    target_corner = simulator._calculate_target_speed(car, corner_section)
    
    assert target_straight > target_corner, "Target speed should be higher on straight than corner"
    assert target_straight > car.max_speed * 1.0, "DRS should boost speed"
    
    print(f"✅ Speed adjustment working correctly")
    print(f"   Target speed on straight (with DRS): {target_straight:.2f} m/s")
    print(f"   Target speed in corner: {target_corner:.2f} m/s")
    print(f"   Difference: {target_straight - target_corner:.2f} m/s")
    return True


def test_lap_time_tracking():
    """Test 6: Lap time recording"""
    print("\n" + "="*60)
    print("TEST 6: Lap Time Tracking")
    print("="*60)
    
    circuit = Circuit(name="Test", lap_length_km=1.0, number_of_laps=3)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, 0, 1000))
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    car = simulator.add_car("Test", "Team", 90.0, 12.0, 0.90, 0.75, 0.88)
    
    # Simulate until car completes 2 laps
    simulator.race_active = True
    
    while car.lap < 2 and simulator.race_time < 200:
        simulator.simulate_step()
    
    assert len(car.lap_times) >= 1, "Should have at least 1 lap time recorded"
    assert car.lap >= 1, "Should have completed at least 1 lap"
    
    print(f"✅ Lap time tracking working")
    print(f"   Laps completed: {car.lap}")
    print(f"   Lap times recorded: {len(car.lap_times)}")
    if car.lap_times:
        print(f"   Lap 1 time: {car.lap_times[0]:.2f}s")
    return True


def test_monaco_circuit():
    """Test 7: Monaco circuit pre-built track"""
    print("\n" + "="*60)
    print("TEST 7: Monaco Circuit")
    print("="*60)
    
    circuit = create_monaco_circuit()
    
    assert circuit.name == "Circuit de Monaco"
    assert circuit.lap_length_km == 3.337
    assert circuit.number_of_laps == 78
    assert len(circuit.sections) > 0, "Should have sections"
    
    # Check has mix of corners and straights
    corners = circuit.get_corner_count()
    straights = circuit.get_straight_count()
    
    assert corners > 10, "Monaco should have many corners"
    assert straights > 5, "Monaco should have some straights"
    
    print(f"✅ Monaco circuit loaded")
    print(f"   Lap length: {circuit.lap_length_km}km")
    print(f"   Corners: {corners}")
    print(f"   Straights: {straights}")
    print(f"   Total sections: {len(circuit.sections)}")
    return True


def test_monza_circuit():
    """Test 8: Monza circuit pre-built track"""
    print("\n" + "="*60)
    print("TEST 8: Monza Circuit")
    print("="*60)
    
    circuit = create_monza_circuit()
    
    assert circuit.name == "Autodromo Nazionale di Monza"
    assert circuit.lap_length_km == 5.793
    assert circuit.number_of_laps == 53
    
    # Check for DRS zones
    drs_zones = sum(1 for s in circuit.sections 
                    if s.section_type == SectionType.STRAIGHT and s.drs_zone)
    
    assert drs_zones >= 2, "Monza should have at least 2 DRS zones"
    
    print(f"✅ Monza circuit loaded")
    print(f"   Lap length: {circuit.lap_length_km}km")
    print(f"   DRS zones: {drs_zones}")
    print(f"   Corners: {circuit.get_corner_count()}")
    return True


def test_silverstone_circuit():
    """Test 9: Silverstone circuit pre-built track"""
    print("\n" + "="*60)
    print("TEST 9: Silverstone Circuit")
    print("="*60)
    
    circuit = create_silverstone_circuit()
    
    assert circuit.name == "Silverstone Circuit"
    assert circuit.lap_length_km == 5.891
    assert circuit.number_of_laps == 52
    
    print(f"✅ Silverstone circuit loaded")
    print(f"   Lap length: {circuit.lap_length_km}km")
    print(f"   Corners: {circuit.get_corner_count()}")
    print(f"   Straights: {circuit.get_straight_count()}")
    return True


def test_full_race_on_circuit():
    """Test 10: Complete race simulation on circuit"""
    print("\n" + "="*60)
    print("TEST 10: Full Race Simulation on Circuit")
    print("="*60)
    
    # Short race for testing
    circuit = create_monaco_circuit()
    circuit.number_of_laps = 5  # Shorter for testing
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    
    # Add 3 cars
    for car_spec in create_f1_grid()[:3]:
        simulator.add_car(**car_spec)
    
    results = simulator.run_simulation(verbose=False)
    
    assert len(results) == 3, "Should have 3 results"
    assert all('lap_times' in r for r in results), "All results should have lap times"
    assert all('fastest_lap' in r for r in results), "All results should have fastest lap"
    assert all('average_lap' in r for r in results), "All results should have average lap"
    
    # Verify lap times make sense
    for result in results:
        assert len(result['lap_times']) == 5, "Should have 5 lap times"
        assert result['fastest_lap'] == min(result['lap_times']), "Fastest lap should be minimum"
        
        # Check consistency - lap times shouldn't vary too wildly
        lap_range = max(result['lap_times']) - min(result['lap_times'])
        assert lap_range < 10.0, "Lap time variation should be reasonable"
    
    print(f"✅ Full race simulation completed")
    print(f"   Cars: {len(results)}")
    print(f"   Laps per car: {len(results[0]['lap_times'])}")
    print(f"   Winner: {results[0]['driver']}")
    print(f"   Winner's fastest lap: {results[0]['fastest_lap']:.2f}s")
    print(f"   Winner's average lap: {results[0]['average_lap']:.2f}s")
    return True


def test_corner_braking():
    """Test 11: Cars brake for corners"""
    print("\n" + "="*60)
    print("TEST 11: Corner Braking Behavior")
    print("="*60)
    
    # Create circuit with straight then tight corner
    circuit = Circuit(name="Test", lap_length_km=1.0, number_of_laps=2)
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 800, 0, 800))
    circuit.sections.append(TrackSection(SectionType.CORNER, 100, 800, 900, corner_radius=15))  # Very tight
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 100, 900, 1000))
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    car = simulator.add_car("Test", "Team", 90.0, 12.0, 0.90, 0.75, 0.88)
    
    simulator.race_active = True
    
    # Run until car reaches corner
    while car.position < 750:
        simulator.simulate_step()
    
    speed_before_corner = car.velocity
    
    # Continue through corner
    while car.position < 850:
        simulator.simulate_step()
    
    speed_in_corner = car.velocity
    
    assert speed_in_corner < speed_before_corner, "Car should slow down in corner"
    
    print(f"✅ Corner braking working correctly")
    print(f"   Speed before corner: {speed_before_corner:.2f} m/s")
    print(f"   Speed in corner: {speed_in_corner:.2f} m/s")
    print(f"   Speed reduction: {speed_before_corner - speed_in_corner:.2f} m/s")
    return True


def test_drs_boost():
    """Test 12: DRS provides speed boost"""
    print("\n" + "="*60)
    print("TEST 12: DRS Speed Boost")
    print("="*60)
    
    circuit = Circuit(name="Test", lap_length_km=2.0, number_of_laps=2)
    
    # Straight without DRS
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, 0, 1000, drs_zone=False))
    # Straight with DRS
    circuit.sections.append(TrackSection(SectionType.STRAIGHT, 1000, 1000, 2000, drs_zone=True))
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    car = simulator.add_car("Test", "Team", 90.0, 12.0, 0.90, 0.75, 0.88)
    
    # Get target speeds
    normal_straight = circuit.sections[0]
    drs_straight = circuit.sections[1]
    
    target_normal = simulator._calculate_target_speed(car, normal_straight)
    target_drs = simulator._calculate_target_speed(car, drs_straight)
    
    assert target_drs > target_normal, "DRS should provide speed boost"
    boost_percent = ((target_drs - target_normal) / target_normal) * 100
    
    assert boost_percent > 5.0, "DRS boost should be at least 5%"
    
    print(f"✅ DRS boost working correctly")
    print(f"   Normal straight target: {target_normal:.2f} m/s")
    print(f"   DRS straight target: {target_drs:.2f} m/s")
    print(f"   Boost: {boost_percent:.1f}%")
    return True


def test_lap_time_consistency():
    """Test 13: Lap times are consistent"""
    print("\n" + "="*60)
    print("TEST 13: Lap Time Consistency")
    print("="*60)
    
    circuit = create_silverstone_circuit()
    circuit.number_of_laps = 10
    
    simulator = RaceSimulator(circuit=circuit, timestep=0.1)
    car = simulator.add_car("Test", "Team", 92.0, 12.0, 0.91, 0.73, 0.90)
    
    results = simulator.run_simulation(verbose=False)
    
    lap_times = results[0]['lap_times']
    
    # Calculate standard deviation
    import statistics
    std_dev = statistics.stdev(lap_times)
    mean_lap = statistics.mean(lap_times)
    coefficient_of_variation = (std_dev / mean_lap) * 100
    
    # Lap times should be relatively consistent (CV < 3%)
    assert coefficient_of_variation < 3.0, "Lap times should be consistent"
    
    print(f"✅ Lap times are consistent")
    print(f"   Mean lap time: {mean_lap:.2f}s")
    print(f"   Std deviation: {std_dev:.2f}s")
    print(f"   Coefficient of variation: {coefficient_of_variation:.2f}%")
    print(f"   Lap time range: {min(lap_times):.2f}s - {max(lap_times):.2f}s")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "CIRCUIT RACE SIMULATOR - TEST SUITE" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_track_section_creation,
        test_circuit_creation,
        test_section_detection,
        test_car_with_cornering,
        test_speed_in_sections,
        test_lap_time_tracking,
        test_monaco_circuit,
        test_monza_circuit,
        test_silverstone_circuit,
        test_full_race_on_circuit,
        test_corner_braking,
        test_drs_boost,
        test_lap_time_consistency,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe Circuit Race Simulator is ready for integration!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
