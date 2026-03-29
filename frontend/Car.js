/**
 * Car.js - Individual F1 Car Physics and State Management
 * Handles car movement, lap tracking, sector timing, tyre wear, and pit stops
 */

class Car {
    constructor(config) {
        // Driver & Team Info
        this.driverId = config.driverId;
        this.driverName = config.driverName;
        this.driverAbbr = config.driverAbbr;
        this.team = config.team;
        this.teamColor = config.teamColor;
        this.number = config.number;

        // Position State
        this.position = config.gridPosition || 1;
        this.lapProgress = 0;              // 0.0 - 1.0 (fraction of lap completed)
        this.currentLap = 0;
        this.distanceOnTrack = 0;          // Total distance traveled (meters)
        this.trackPosition = { x: 0, y: 0 };  // Current x,y coordinates

        // Physics
        this.baseSpeed = config.baseSpeed || 85;        // m/s (~300 km/h)
        this.speedVariation = config.speedVariation || 0.05;  // Random variation
        this.currentSpeed = this.baseSpeed;
        this.maxSpeed = config.maxSpeed || 95;
        this.acceleration = config.acceleration || 12;
        this.brakingPower = config.brakingPower || 15;
        this.cornering = config.cornering || 0.9;

        // Race State
        this.gapToLeader = 0;              // Seconds behind leader
        this.gapToAhead = 0;               // Seconds behind car ahead
        this.isInPit = false;
        this.pitStopDuration = 0;
        this.pitStopProgress = 0;

        // Tyre Management
        this.tyreCompound = config.startingTyre || 'M';  // S/M/H/I/W
        this.tyreWear = 0;                // 0-100
        this.tyreWearRate = config.tyreWearRate || 0.3;
        this.tyreGrip = this.getTyreGrip();
        this.pitStopCount = 0;
        this.plannedPitLap = config.plannedPitLap || Math.floor(Math.random() * 20) + 15;

        // Sector Timing
        this.sector1Time = null;
        this.sector2Time = null;
        this.sector3Time = null;
        this.currentSector = 1;
        this.sectorStartTime = 0;
        this.lastLapTime = null;
        this.bestLapTime = Infinity;

        // DRS
        this.drsAvailable = false;
        this.drsActive = false;
        this.drsBoost = 1.05;  // 5% speed boost

        // Fuel
        this.fuel = 100;  // kg
        this.fuelConsumption = 0.15;  // kg per second at full throttle

        // Status
        this.status = 'racing';  // racing, pit, dnf, finished
        this.dnfReason = null;

        // Performance Modifiers
        this.skillLevel = config.skillLevel || 0.9;  // 0-1
        this.consistency = config.consistency || 0.95; // 0-1
        this.aggression = config.aggression || 0.5;  // 0-1
    }

    /**
     * Update car physics and position for one simulation tick
     */
    update(deltaTime, trackData, raceTime, allCars) {
        if (this.status !== 'racing') return;

        // Handle pit stop
        if (this.isInPit) {
            this.updatePitStop(deltaTime);
            return;
        }

        // Check if pit stop needed
        if (this.shouldPit(trackData)) {
            this.enterPit();
            return;
        }

        // Update tyre wear
        this.updateTyreWear(deltaTime, trackData);

        // Update fuel consumption
        this.updateFuel(deltaTime);

        // Check DRS availability
        this.updateDRS(allCars, trackData);

        // Calculate current speed based on track section
        const currentSection = trackData.getCurrentSection(this.lapProgress);
        const targetSpeed = this.calculateSpeed(currentSection);

        // Apply speed smoothly
        if (this.currentSpeed < targetSpeed) {
            this.currentSpeed = Math.min(targetSpeed, this.currentSpeed + this.acceleration * deltaTime);
        } else {
            this.currentSpeed = Math.max(targetSpeed, this.currentSpeed - this.brakingPower * deltaTime);
        }

        // Add random variation for realism
        const variation = (Math.random() - 0.5) * this.speedVariation * this.currentSpeed;
        this.currentSpeed += variation;

        // Move car
        const distance = this.currentSpeed * deltaTime;
        this.distanceOnTrack += distance;

        // Update lap progress
        const lapLength = trackData.lapLength;
        const previousProgress = this.lapProgress;
        this.lapProgress = (this.distanceOnTrack % lapLength) / lapLength;

        // Check lap completion
        if (previousProgress > 0.9 && this.lapProgress < 0.1) {
            this.completeLap(raceTime);
        }

        // Check sector crossings
        this.updateSectorTiming(previousProgress, this.lapProgress, raceTime);

        // Update track position (x,y coordinates)
        this.trackPosition = trackData.getPositionOnTrack(this.lapProgress);
    }

    /**
     * Calculate speed based on track section
     */
    calculateSpeed(section) {
        let speed = this.baseSpeed;

        // Apply tyre grip effect
        speed *= this.tyreGrip;

        // Apply section characteristics
        if (section.type === 'corner') {
            // Slow down for corners based on radius and cornering ability
            const cornerFactor = Math.min(1.0, section.radius / 500) * this.cornering;
            speed *= (0.6 + 0.4 * cornerFactor);
        } else if (section.type === 'straight') {
            // Full speed on straights
            speed = this.maxSpeed;

            // Apply DRS boost
            if (this.drsActive && section.drsZone) {
                speed *= this.drsBoost;
            }
        }

        // Apply fuel weight penalty (heavier = slower)
        const fuelWeight = 1 - (this.fuel / 100) * 0.03;  // Up to 3% slower with full tank
        speed *= fuelWeight;

        // Apply skill level
        speed *= (0.95 + this.skillLevel * 0.10);

        return speed;
    }

    /**
     * Update tyre wear based on driving
     */
    updateTyreWear(deltaTime, trackData) {
        const baseWear = this.tyreWearRate * deltaTime;

        // Corners cause more wear
        const section = trackData.getCurrentSection(this.lapProgress);
        const cornerMultiplier = section.type === 'corner' ? 1.5 : 1.0;

        // Aggressive driving causes more wear
        const aggressionMultiplier = 1 + this.aggression * 0.3;

        this.tyreWear += baseWear * cornerMultiplier * aggressionMultiplier;
        this.tyreWear = Math.min(100, Math.max(0, this.tyreWear));

        // Update grip based on wear
        this.tyreGrip = this.getTyreGrip();
    }

    /**
     * Get current tyre grip based on compound and wear
     */
    getTyreGrip() {
        const compoundGrip = {
            'S': 1.00,  // Soft - best grip, high wear
            'M': 0.97,  // Medium - balanced
            'H': 0.94,  // Hard - less grip, low wear
            'I': 0.90,  // Intermediate - wet conditions
            'W': 0.85   // Wet - very wet conditions
        };

        const baseGrip = compoundGrip[this.tyreCompound] || 0.97;

        // Grip degrades with wear
        const wearFactor = 1 - (this.tyreWear / 100) * 0.25;  // Up to 25% loss

        return baseGrip * wearFactor;
    }

    /**
     * Update fuel consumption
     */
    updateFuel(deltaTime) {
        const consumption = this.fuelConsumption * deltaTime * (this.currentSpeed / this.maxSpeed);
        this.fuel -= consumption;
        this.fuel = Math.max(0, this.fuel);

        if (this.fuel <= 0) {
            this.dnf('Out of fuel');
        }
    }

    /**
     * Check if car should pit
     */
    shouldPit(trackData) {
        // Pit if tyre wear is critical
        if (this.tyreWear > 90) return true;

        // Pit at planned lap
        if (this.currentLap === this.plannedPitLap && this.lapProgress > 0.85) {
            return true;
        }

        // Random pit decision based on strategy (5% chance per lap)
        if (this.currentLap > 10 && Math.random() < 0.05 && this.lapProgress > 0.85) {
            return true;
        }

        return false;
    }

    /**
     * Enter pit lane
     */
    enterPit() {
        this.isInPit = true;
        this.pitStopDuration = 20 + Math.random() * 4;  // 20-24 seconds
        this.pitStopProgress = 0;
        this.status = 'pit';
        this.currentSpeed = 0;
    }

    /**
     * Update pit stop progress
     */
    updatePitStop(deltaTime) {
        this.pitStopProgress += deltaTime;

        if (this.pitStopProgress >= this.pitStopDuration) {
            this.exitPit();
        }
    }

    /**
     * Exit pit lane
     */
    exitPit() {
        this.isInPit = false;
        this.pitStopCount++;
        this.status = 'racing';

        // Change tyres
        const compounds = ['S', 'M', 'H'];
        this.tyreCompound = compounds[this.pitStopCount % compounds.length];
        this.tyreWear = 0;
        this.tyreGrip = this.getTyreGrip();

        // Plan next pit (if needed)
        this.plannedPitLap = this.currentLap + Math.floor(Math.random() * 15) + 15;
    }

    /**
     * Update DRS availability and activation
     */
    updateDRS(allCars, trackData) {
        // Reset DRS
        this.drsAvailable = false;
        this.drsActive = false;

        // Check if in DRS zone
        const section = trackData.getCurrentSection(this.lapProgress);
        if (!section.drsZone) return;

        // Find car ahead
        const sortedCars = allCars
            .filter(c => c.status === 'racing' && c !== this)
            .sort((a, b) => {
                if (a.currentLap !== b.currentLap) return b.currentLap - a.currentLap;
                return b.lapProgress - a.lapProgress;
            });

        const carAheadIndex = sortedCars.findIndex(c => {
            if (c.currentLap > this.currentLap) return true;
            if (c.currentLap === this.currentLap && c.lapProgress > this.lapProgress) return true;
            return false;
        });

        if (carAheadIndex >= 0) {
            const carAhead = sortedCars[carAheadIndex];

            // Calculate time gap
            const gap = this.calculateGap(carAhead, trackData);

            // DRS available if within 1 second
            if (gap < 1.0) {
                this.drsAvailable = true;
                this.drsActive = true;
            }
        }
    }

    /**
     * Calculate time gap to another car
     */
    calculateGap(otherCar, trackData) {
        const lapDiff = otherCar.currentLap - this.currentLap;
        const progressDiff = otherCar.lapProgress - this.lapProgress;

        const totalProgressDiff = lapDiff + progressDiff;
        const distanceDiff = totalProgressDiff * trackData.lapLength;

        // Convert to time (using average speed)
        const avgSpeed = (this.baseSpeed + otherCar.baseSpeed) / 2;
        return Math.abs(distanceDiff / avgSpeed);
    }

    /**
     * Update sector timing
     */
    updateSectorTiming(previousProgress, currentProgress, raceTime) {
        // Sector 1: 0.00 - 0.33
        // Sector 2: 0.33 - 0.66
        // Sector 3: 0.66 - 1.00

        // Sector 1 -> 2
        if (previousProgress < 0.33 && currentProgress >= 0.33 && this.currentSector === 1) {
            this.sector1Time = raceTime - this.sectorStartTime;
            this.currentSector = 2;
            this.sectorStartTime = raceTime;
        }

        // Sector 2 -> 3
        if (previousProgress < 0.66 && currentProgress >= 0.66 && this.currentSector === 2) {
            this.sector2Time = raceTime - this.sectorStartTime;
            this.currentSector = 3;
            this.sectorStartTime = raceTime;
        }
    }

    /**
     * Complete a lap
     */
    completeLap(raceTime) {
        // Record sector 3 time
        if (this.currentSector === 3) {
            this.sector3Time = raceTime - this.sectorStartTime;
        }

        // Calculate lap time
        if (this.sector1Time && this.sector2Time && this.sector3Time) {
            this.lastLapTime = this.sector1Time + this.sector2Time + this.sector3Time;

            if (this.lastLapTime < this.bestLapTime) {
                this.bestLapTime = this.lastLapTime;
            }
        }

        // Reset sectors
        this.sector1Time = null;
        this.sector2Time = null;
        this.sector3Time = null;
        this.currentSector = 1;
        this.sectorStartTime = raceTime;

        // Increment lap
        this.currentLap++;
    }

    /**
     * Mark car as DNF
     */
    dnf(reason) {
        this.status = 'dnf';
        this.dnfReason = reason;
        this.currentSpeed = 0;
    }

    /**
     * Mark car as finished
     */
    finish() {
        this.status = 'finished';
        this.currentSpeed = 0;
    }

    /**
     * Get display data for UI
     */
    getDisplayData() {
        return {
            driverId: this.driverId,
            driverName: this.driverName,
            driverAbbr: this.driverAbbr,
            team: this.team,
            teamColor: this.teamColor,
            number: this.number,
            position: this.position,
            currentLap: this.currentLap,
            lapProgress: this.lapProgress,
            trackPosition: this.trackPosition,
            currentSpeed: this.currentSpeed,
            speedKmh: this.currentSpeed * 3.6,
            gapToLeader: this.gapToLeader,
            gapToAhead: this.gapToAhead,
            tyreCompound: this.tyreCompound,
            tyreWear: this.tyreWear,
            fuel: this.fuel,
            sector1Time: this.sector1Time,
            sector2Time: this.sector2Time,
            sector3Time: this.sector3Time,
            lastLapTime: this.lastLapTime,
            bestLapTime: this.bestLapTime,
            drsAvailable: this.drsAvailable,
            drsActive: this.drsActive,
            isInPit: this.isInPit,
            pitStopCount: this.pitStopCount,
            status: this.status,
            dnfReason: this.dnfReason,
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Car;
}
