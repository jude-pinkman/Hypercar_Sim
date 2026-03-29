/**
 * RaceEngine.js - F1 Race Simulation Engine
 * Orchestrates the race simulation, manages cars, track data, and animation loop
 */

class RaceEngine {
    constructor(config = {}) {
        // Configuration
        this.config = {
            targetFPS: config.targetFPS || 60,
            simulationSpeed: config.simulationSpeed || 1.0,
            ...config
        };

        // State
        this.isRunning = false;
        this.isPaused = false;
        this.raceTime = 0;
        this.lastUpdateTime = 0;
        this.deltaTime = 0;

        // Race data
        this.cars = [];
        this.trackData = null;
        this.totalLaps = 0;
        this.raceId = null;

        // Renderer
        this.renderer = null;

        // UI Components
        this.leaderboard = null;
        this.telemetry = null;

        // Animation
        this.animationFrameId = null;

        // Event callbacks
        this.onRaceStart = null;
        this.onLapComplete = null;
        this.onPositionChange = null;
        this.onPitStop = null;
        this.onRaceFinish = null;
        this.onUpdate = null;
    }

    /**
     * Initialize race with circuit and driver data
     */
    initialize(circuitData, driversData, totalLaps) {
        console.log('Initializing race...', circuitData, driversData);

        this.totalLaps = totalLaps;
        this.raceId = `race_${Date.now()}`;

        // Load track data
        this.trackData = this.prepareTrackData(circuitData);

        // Create cars
        this.cars = driversData.map((driver, index) => {
            return new Car({
                driverId: driver.driver_id || driver.driverId,
                driverName: driver.name || driver.driverName,
                driverAbbr: driver.abbr || driver.driverAbbr || this.generateAbbr(driver.name || driver.driverName),
                team: driver.team,
                teamColor: driver.teamColor || this.getTeamColor(driver.team),
                number: driver.number || index + 1,
                gridPosition: index + 1,
                baseSpeed: driver.baseSpeed || (85 + Math.random() * 5),
                speedVariation: driver.speedVariation || 0.05,
                maxSpeed: driver.maxSpeed || (93 + Math.random() * 3),
                acceleration: driver.acceleration || 12,
                cornering: driver.cornering || (0.88 + Math.random() * 0.08),
                tyreWearRate: driver.tyreWearRate || (0.25 + Math.random() * 0.15),
                startingTyre: driver.startingTyre || 'M',
                skillLevel: driver.skillLevel || (0.85 + Math.random() * 0.15),
                consistency: driver.consistency || (0.9 + Math.random() * 0.1),
                aggression: driver.aggression || (0.4 + Math.random() * 0.3),
                plannedPitLap: driver.plannedPitLap || Math.floor(Math.random() * 15) + 12,
            });
        });

        console.log(`Race initialized with ${this.cars.length} drivers on ${circuitData.name}`);
    }

    /**
     * Prepare track data structure from circuit
     */
    prepareTrackData(circuitData) {
        const lapLength = (circuitData.lap_length_km || circuitData.lapLength || 5) * 1000; // Convert to meters

        return {
            name: circuitData.name,
            lapLength: lapLength,
            corners: circuitData.corners || 16,
            coordinates: circuitData.coordinates || [],
            sections: this.generateTrackSections(circuitData),
            getCurrentSection: (progress) => this.getCurrentSection(progress, circuitData),
            getPositionOnTrack: (progress) => this.getPositionOnTrack(progress),
        };
    }

    /**
     * Generate track sections from circuit data
     */
    generateTrackSections(circuitData) {
        const sections = [];
        const numCorners = circuitData.corners || 16;
        const numStraights = numCorners;
        const totalSections = numCorners + numStraights;

        for (let i = 0; i < totalSections; i++) {
            const isCorner = i % 2 === 0;
            const progress = i / totalSections;
            const length = 1.0 / totalSections;

            sections.push({
                type: isCorner ? 'corner' : 'straight',
                progress: progress,
                length: length,
                radius: isCorner ? (300 + Math.random() * 200) : Infinity,
                drsZone: !isCorner && Math.random() < 0.2,  // 20% of straights are DRS
            });
        }

        return sections;
    }

    /**
     * Get current track section for a given progress
     */
    getCurrentSection(progress, circuitData) {
        const sections = this.trackData.sections;
        const section = sections[Math.floor(progress * sections.length)] || sections[0];
        return section;
    }

    /**
     * Get x, y position on track from progress
     */
    getPositionOnTrack(progress) {
        if (this.renderer) {
            return this.renderer.getPositionOnTrack(progress);
        }
        return { x: 0, y: 0 };
    }

    /**
     * Set renderer
     */
    setRenderer(renderer) {
        this.renderer = renderer;

        // Load circuit into renderer
        if (this.trackData) {
            this.renderer.loadCircuit({
                ...this.trackData,
                lap_length_km: this.trackData.lapLength / 1000,
            });
        }
    }

    /**
     * Set leaderboard component
     */
    setLeaderboard(leaderboard) {
        this.leaderboard = leaderboard;
    }

    /**
     * Set telemetry component
     */
    setTelemetry(telemetry) {
        this.telemetry = telemetry;
    }

    /**
     * Start race
     */
    start() {
        if (this.isRunning) return;

        console.log('Starting race...');

        this.isRunning = true;
        this.isPaused = false;
        this.raceTime = 0;
        this.lastUpdateTime = performance.now();

        // Fire race start event
        if (this.onRaceStart) {
            this.onRaceStart({
                raceId: this.raceId,
                circuit: this.trackData.name,
                totalLaps: this.totalLaps,
                gridSize: this.cars.length,
            });
        }

        // Start animation loop
        this.animationLoop();
    }

    /**
     * Pause race
     */
    pause() {
        this.isPaused = true;
    }

    /**
     * Resume race
     */
    resume() {
        this.isPaused = false;
        this.lastUpdateTime = performance.now();
    }

    /**
     * Stop race
     */
    stop() {
        console.log('Stopping race...');

        this.isRunning = false;

        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }

        // Fire race finish event
        if (this.onRaceFinish) {
            this.onRaceFinish({
                raceId: this.raceId,
                results: this.getFinalResults(),
            });
        }
    }

    /**
     * Main animation loop
     */
    animationLoop() {
        if (!this.isRunning) return;

        const currentTime = performance.now();
        this.deltaTime = (currentTime - this.lastUpdateTime) / 1000; // Convert to seconds
        this.lastUpdateTime = currentTime;

        // Apply simulation speed multiplier
        const adjustedDelta = this.deltaTime * this.config.simulationSpeed;

        // Update simulation
        if (!this.isPaused) {
            this.update(adjustedDelta);
        }

        // Render
        this.render();

        // Continue loop
        this.animationFrameId = requestAnimationFrame(() => this.animationLoop());
    }

    /**
     * Update simulation state
     */
    update(deltaTime) {
        // Increment race time
        this.raceTime += deltaTime;

        // Update all cars
        this.cars.forEach(car => {
            car.update(deltaTime, this.trackData, this.raceTime, this.cars);
        });

        // Update positions and gaps
        this.updatePositions();

        // Check race completion
        this.checkRaceCompletion();

        // Fire update event
        if (this.onUpdate) {
            this.onUpdate({
                raceTime: this.raceTime,
                positions: this.getPositions(),
            });
        }

        // Update UI components
        if (this.leaderboard) {
            this.leaderboard.update(this.getLeaderboardData());
        }

        if (this.telemetry) {
            // Update telemetry for leader
            const leader = this.cars.find(c => c.position === 1);
            if (leader) {
                this.telemetry.update(leader.getDisplayData());
            }
        }
    }

    /**
     * Update car positions and gaps
     */
    updatePositions() {
        // Sort cars by race progress
        const sorted = [...this.cars].sort((a, b) => {
            // First by lap
            if (b.currentLap !== a.currentLap) {
                return b.currentLap - a.currentLap;
            }
            // Then by progress
            return b.lapProgress - a.lapProgress;
        });

        // Update positions and gaps
        const previousPositions = new Map(this.cars.map(c => [c.driverId, c.position]));

        sorted.forEach((car, index) => {
            const newPosition = index + 1;
            const oldPosition = car.position;

            car.position = newPosition;

            // Calculate gaps
            if (index === 0) {
                car.gapToLeader = 0;
                car.gapToAhead = 0;
            } else {
                const leader = sorted[0];
                const carAhead = sorted[index - 1];

                car.gapToLeader = car.calculateGap(leader, this.trackData);
                car.gapToAhead = car.calculateGap(carAhead, this.trackData);
            }

            // Fire position change event
            if (newPosition !== oldPosition && this.onPositionChange) {
                this.onPositionChange({
                    driver: car.driverName,
                    oldPosition: oldPosition,
                    newPosition: newPosition,
                    raceTime: this.raceTime,
                });
            }
        });
    }

    /**
     * Check if race is complete
     */
    checkRaceCompletion() {
        // Check if leader has finished
        const leader = this.cars.find(c => c.position === 1);

        if (leader && leader.currentLap >= this.totalLaps) {
            // Mark leader as finished
            if (leader.status === 'racing') {
                leader.finish();
            }

            // Check if all cars are finished or should be finished
            const finishedCount = this.cars.filter(c => c.status === 'finished').length;

            if (finishedCount === this.cars.length) {
                // All cars finished
                this.stop();
            } else {
                // Mark remaining cars as finished if they're too far behind
                this.cars.forEach(car => {
                    if (car.status === 'racing' && car.gapToLeader > 60) {
                        car.finish();
                    }
                });
            }
        }
    }

    /**
     * Render the race
     */
    render() {
        if (this.renderer) {
            this.renderer.renderCars(this.cars);
        }
    }

    /**
     * Get current positions
     */
    getPositions() {
        return this.cars
            .sort((a, b) => a.position - b.position)
            .map(car => car.getDisplayData());
    }

    /**
     * Get leaderboard data
     */
    getLeaderboardData() {
        return {
            currentLap: this.cars[0]?.currentLap || 0,
            totalLaps: this.totalLaps,
            positions: this.getPositions(),
        };
    }

    /**
     * Get final results
     */
    getFinalResults() {
        return this.getPositions().map((car, index) => ({
            position: index + 1,
            driver: car.driverName,
            team: car.team,
            laps: car.currentLap,
            bestLapTime: car.bestLapTime,
            pitStops: car.pitStopCount,
            status: car.status,
        }));
    }

    /**
     * Generate driver abbreviation from name
     */
    generateAbbr(name) {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return parts[parts.length - 1].substring(0, 3).toUpperCase();
        }
        return name.substring(0, 3).toUpperCase();
    }

    /**
     * Get team color
     */
    getTeamColor(team) {
        const colors = {
            'Red Bull Racing': '#0600ef',
            'Ferrari': '#dc0000',
            'McLaren': '#ff8700',
            'Mercedes': '#00d2be',
            'Aston Martin': '#006f62',
            'Alpine': '#0082fa',
            'Williams': '#005aff',
            'Haas F1 Team': '#ffffff',
            'Racing Bulls': '#5e8faa',
            'Kick Sauber': '#c8102e',
        };
        return colors[team] || '#888888';
    }

    /**
     * Set simulation speed
     */
    setSimulationSpeed(speed) {
        this.config.simulationSpeed = Math.max(0.1, Math.min(10, speed));
    }

    /**
     * Cleanup
     */
    destroy() {
        this.stop();

        if (this.renderer) {
            this.renderer.destroy();
        }

        this.cars = [];
        this.trackData = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RaceEngine;
}
