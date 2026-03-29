"""
Test Suite for F1 Race Simulator
Verifies core functionality and physics calculations
"""

import sys
from race_simulator import RaceSimulator, Car, create_f1_grid


def test_car_creation():
    """Test 1: Car object creation"""
    print("\n" + "="*60)
    print("TEST 1: Car Creation")
    print("="*60)
    
    car = Car(
        driver_name="Test Driver",
        team="Test Team",
        max_speed=90.0,
        acceleration=11.0,
        tyre_grip=0.90,
        drag_coefficient=0.75
    )
    
    assert car.driver_name == "Test Driver"
    assert car.team == "Test Team"
    assert car.max_speed == 90.0
    assert car.position == 0.0
    assert car.velocity == 0.0
    assert car.lap == 0
    assert car.finished == False
    
    print("✅ Car creation successful")
    print(f"   Driver: {car.driver_name}")
    print(f"   Team: {car.team}")
    print(f"   Max Speed: {car.max_speed} m/s")
    return True


def test_simulator_initialization():
    """Test 2: Simulator initialization"""
    print("\n" + "="*60)
    print("TEST 2: Simulator Initialization")
    print("="*60)
    
    simulator = RaceSimulator(
        circuit_length=5000.0,
        total_laps=40,
        timestep=0.1
    )
    
    assert simulator.circuit_length == 5000.0
    assert simulator.total_laps == 40
    assert simulator.timestep == 0.1
    assert len(simulator.cars) == 0
    assert simulator.race_time == 0.0
    assert simulator.race_active == False
    
    print("✅ Simulator initialized successfully")
    print(f"   Circuit Length: {simulator.circuit_length}m")
    print(f"   Total Laps: {simulator.total_laps}")
    print(f"   Timestep: {simulator.timestep}s")
    return True


def test_add_cars():
    """Test 3: Adding cars to simulator"""
    print("\n" + "="*60)
    print("TEST 3: Adding Cars")
    print("="*60)
    
    simulator = RaceSimulator()
    
    car1 = simulator.add_car("Driver 1", "Team A", 90.0, 11.0, 0.90, 0.75)
    car2 = simulator.add_car("Driver 2", "Team B", 89.0, 10.8, 0.88, 0.76)
    car3 = simulator.add_car("Driver 3", "Team C", 88.0, 10.6, 0.86, 0.77)
    
    assert len(simulator.cars) == 3
    assert simulator.cars[0].driver_name == "Driver 1"
    assert simulator.cars[1].driver_name == "Driver 2"
    assert simulator.cars[2].driver_name == "Driver 3"
    
    print(f"✅ Successfully added {len(simulator.cars)} cars")
    for i, car in enumerate(simulator.cars, 1):
        print(f"   Car {i}: {car.driver_name} ({car.team})")
    return True


def test_physics_calculation():
    """Test 4: Physics calculations"""
    print("\n" + "="*60)
    print("TEST 4: Physics Calculations")
    print("="*60)
    
    simulator = RaceSimulator(timestep=0.1)
    car = simulator.add_car("Test Car", "Test Team", 90.0, 12.0, 0.90, 0.75)
    
    # Test initial acceleration (should be high)
    initial_accel = simulator._calculate_acceleration(car)
    print(f"   Initial acceleration: {initial_accel:.2f} m/s²")
    assert initial_accel > 0, "Initial acceleration should be positive"
    
    # Simulate to mid-speed
    car.velocity = 45.0  # Half of max speed
    mid_accel = simulator._calculate_acceleration(car)
    print(f"   Mid-speed acceleration: {mid_accel:.2f} m/s²")
    assert mid_accel < initial_accel, "Acceleration should decrease with speed"
    
    # Simulate near max speed
    car.velocity = 89.0
    high_accel = simulator._calculate_acceleration(car)
    print(f"   Near-max acceleration: {high_accel:.2f} m/s²")
    assert high_accel < mid_accel, "Acceleration should further decrease near max speed"
    
    print("✅ Physics calculations working correctly")
    return True


def test_position_update():
    """Test 5: Position and velocity updates"""
    print("\n" + "="*60)
    print("TEST 5: Position & Velocity Updates")
    print("="*60)
    
    simulator = RaceSimulator(timestep=0.1)
    car = simulator.add_car("Test Car", "Test Team", 90.0, 12.0, 0.90, 0.75)
    
    initial_pos = car.position
    initial_vel = car.velocity
    
    # Update physics
    simulator._update_car_physics(car)
    
    print(f"   Initial position: {initial_pos}m, velocity: {initial_vel}m/s")
    print(f"   After 1 step: position: {car.position:.2f}m, velocity: {car.velocity:.2f}m/s")
    
    assert car.velocity > initial_vel, "Velocity should increase"
    assert car.position > initial_pos, "Position should increase"
    
    # Update multiple times
    for _ in range(100):
        simulator._update_car_physics(car)
    
    print(f"   After 100 steps: position: {car.position:.2f}m, velocity: {car.velocity:.2f}m/s")
    
    assert car.position > 100.0, "Car should have moved significantly"
    assert car.velocity < car.max_speed, "Velocity should not exceed max speed"
    
    print("✅ Position and velocity updates working correctly")
    return True


def test_lap_tracking():
    """Test 6: Lap tracking"""
    print("\n" + "="*60)
    print("TEST 6: Lap Tracking")
    print("="*60)
    
    circuit_length = 1000.0  # Short circuit for testing
    simulator = RaceSimulator(circuit_length=circuit_length, total_laps=3, timestep=0.1)
    car = simulator.add_car("Test Car", "Test Team", 90.0, 12.0, 0.90, 0.75)
    
    # Manually advance car position
    car.position = 500.0
    simulator._update_car_physics(car)
    assert car.lap == 0, "Should be on lap 0"
    
    car.position = 1100.0
    simulator._update_car_physics(car)
    assert car.lap == 1, "Should be on lap 1"
    
    car.position = 2300.0
    simulator._update_car_physics(car)
    assert car.lap == 2, "Should be on lap 2"
    
    print(f"✅ Lap tracking working correctly")
    print(f"   Position: {car.position}m = Lap {car.lap}")
    return True


def test_race_completion():
    """Test 7: Race completion detection"""
    print("\n" + "="*60)
    print("TEST 7: Race Completion")
    print("="*60)
    
    simulator = RaceSimulator(circuit_length=1000.0, total_laps=3, timestep=0.1)
    car = simulator.add_car("Test Car", "Test Team", 90.0, 12.0, 0.90, 0.75)
    
    # Position car at finish line
    car.position = 3100.0  # Just past 3 laps
    car.lap = 2
    simulator.race_time = 100.0
    simulator._update_car_physics(car)
    
    assert car.lap == 3, "Should have completed 3 laps"
    assert car.finished == True, "Car should be marked as finished"
    assert car.finish_time == 100.0, "Finish time should be recorded"
    assert len(simulator.results) == 1, "Results should contain one entry"
    
    print(f"✅ Race completion detection working")
    print(f"   Car finished: {car.finished}")
    print(f"   Finish time: {car.finish_time}s")
    print(f"   Results recorded: {len(simulator.results)}")
    return True


def test_race_positions():
    """Test 8: Race position calculation"""
    print("\n" + "="*60)
    print("TEST 8: Race Positions")
    print("="*60)
    
    simulator = RaceSimulator(circuit_length=1000.0)
    
    # Add 3 cars at different positions
    car1 = simulator.add_car("Leader", "Team A", 90.0, 12.0, 0.90, 0.75)
    car2 = simulator.add_car("Second", "Team B", 89.0, 11.5, 0.88, 0.76)
    car3 = simulator.add_car("Third", "Team C", 88.0, 11.0, 0.86, 0.77)
    
    # Set positions
    car1.position = 3000.0  # Leading
    car1.lap = 3
    car2.position = 2800.0  # 200m behind
    car2.lap = 2
    car3.position = 2500.0  # 500m behind
    car3.lap = 2
    
    positions = simulator.get_race_positions()
    
    assert len(positions) == 3, "Should have 3 positions"
    assert positions[0][1] == "Leader", "Leader should be P1"
    assert positions[1][1] == "Second", "Second should be P2"
    assert positions[2][1] == "Third", "Third should be P3"
    
    print(f"✅ Race positions calculated correctly")
    for pos, driver, team, lap, dist in positions:
        print(f"   P{pos}: {driver} - Lap {lap}")
    return True


def test_full_race_simulation():
    """Test 9: Complete race simulation"""
    print("\n" + "="*60)
    print("TEST 9: Full Race Simulation (Small Grid)")
    print("="*60)
    
    simulator = RaceSimulator(
        circuit_length=2000.0,  # 2km circuit
        total_laps=10,  # 10 laps
        timestep=0.1
    )
    
    # Add 5 cars
    simulator.add_car("Driver 1", "Team A", 92.0, 12.0, 0.92, 0.73)
    simulator.add_car("Driver 2", "Team B", 91.0, 11.5, 0.90, 0.74)
    simulator.add_car("Driver 3", "Team C", 90.0, 11.0, 0.88, 0.75)
    simulator.add_car("Driver 4", "Team D", 89.0, 10.8, 0.86, 0.76)
    simulator.add_car("Driver 5", "Team E", 88.0, 10.5, 0.84, 0.77)
    
    # Run simulation
    results = simulator.run_simulation(verbose=False)
    
    assert len(results) == 5, "Should have 5 results"
    assert results[0]['position'] == 1, "Winner should be position 1"
    assert results[-1]['position'] == 5, "Last place should be position 5"
    
    # Verify results are in order
    for i in range(len(results) - 1):
        assert results[i]['finish_time'] < results[i+1]['finish_time'], \
            "Results should be in time order"
    
    print(f"✅ Full race simulation completed successfully")
    print(f"   Cars: {len(results)}")
    print(f"   Winner: {results[0]['driver']} ({results[0]['team']})")
    print(f"   Time: {results[0]['finish_time']:.2f}s")
    print(f"   Gap to last: {results[-1]['finish_time'] - results[0]['finish_time']:.2f}s")
    return True


def test_f1_grid():
    """Test 10: Full 22-car F1 grid"""
    print("\n" + "="*60)
    print("TEST 10: Full 22-Car F1 Grid")
    print("="*60)
    
    simulator = RaceSimulator(circuit_length=5000.0, total_laps=20, timestep=0.1)
    
    # Load F1 grid
    f1_grid = create_f1_grid()
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    assert len(simulator.cars) == 22, "Should have 22 cars"
    
    print(f"✅ F1 grid loaded successfully")
    print(f"   Total cars: {len(simulator.cars)}")
    print(f"   Teams represented:")
    
    teams = set(car.team for car in simulator.cars)
    for team in sorted(teams):
        drivers = [car.driver_name for car in simulator.cars if car.team == team]
        print(f"      {team}: {', '.join(drivers)}")
    
    # Run a quick simulation test
    print("\n   Running quick simulation test (5 laps)...")
    simulator.total_laps = 5
    results = simulator.run_simulation(verbose=False)
    
    assert len(results) == 22, "All 22 cars should finish"
    print(f"   ✅ All 22 cars completed the race")
    print(f"   Winner: {results[0]['driver']} ({results[0]['team']})")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "F1 RACE SIMULATOR - TEST SUITE" + " "*27 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_car_creation,
        test_simulator_initialization,
        test_add_cars,
        test_physics_calculation,
        test_position_update,
        test_lap_tracking,
        test_race_completion,
        test_race_positions,
        test_full_race_simulation,
        test_f1_grid,
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
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe F1 Race Simulator is ready for integration with Hypercar_Sim!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
