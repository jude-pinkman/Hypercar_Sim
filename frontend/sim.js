import { RaceRenderer } from './render.js';

// ==================== CONFIGURATION ====================
// Use CONFIG for API URL (defined in config.js)
const API_URL = window.CONFIG ? window.CONFIG.API_BASE_URL : 'http://localhost:8000';

// Race mode configurations
const RACE_MODES = {
    'quarter-mile': {
        title: '1/4 Mile Drag Race',
        distance: 402.336,
        startSpeed: 0,
        maxTime: 30,
        metricsSubtitle: '0-100, 0-200 & quarter mile times',
        showSplits: true
    },
    'half-mile': {
        title: '1/2 Mile Drag Race',
        distance: 804.672,
        startSpeed: 0,
        maxTime: 45,
        metricsSubtitle: '0-100, 0-200 & half mile times',
        showSplits: true
    },
    'one-mile': {
        title: '1 Mile Drag Race',
        distance: 1609.344,
        startSpeed: 0,
        maxTime: 60,
        metricsSubtitle: '0-100, 0-200 & one mile times',
        showSplits: true
    },
    'custom-distance': {
        title: 'Custom Distance Race',
        distance: 500, // Default, user configurable
        startSpeed: 0,
        maxTime: 60,
        metricsSubtitle: 'Custom race distance performance',
        showSplits: true,
        customizable: true
    },
    'lap-race': {
        title: 'Lap Racing',
        distance: 1000, // Default lap distance
        laps: 3, // Default lap count
        startSpeed: 0,
        maxTime: 120,
        metricsSubtitle: 'Multi-lap circuit racing',
        showSplits: true,
        showLapTimes: true
    },
    'acceleration-zone': {
        title: 'Acceleration Zone',
        distance: 2000,
        startSpeed: 0, // User configurable
        targetSpeed: 100, // User configurable in km/h
        maxTime: 60,
        metricsSubtitle: 'Speed range acceleration test',
        showSplits: true,
        accelerationMode: true
    },
    'roll-race': {
        title: 'Roll Race',
        distance: 1500,
        startSpeed: 60 / 3.6, // Default 60 km/h
        targetSpeed: 200, // Default 200 km/h
        maxTime: 40,
        metricsSubtitle: 'Rolling start acceleration',
        rollStart: true,
        showSplits: true
    },
    'top-speed': {
        title: 'Top Speed Challenge',
        distance: 5000,
        startSpeed: 0,
        maxTime: 180,
        metricsSubtitle: 'Maximum velocity achieved',
        topSpeedMode: true,
        showSplits: true
    }
};

// Speed milestones for split times (km/h)
const SPEED_SPLITS = [60, 100, 150, 200, 250, 300, 350];

// ==================== STATE ====================
const state = {
    vehicles: {},
    selectedVehicles: new Set(),
    environment: {
        temperature_celsius: 20,
        altitude_meters: 0
    },
    currentMode: 'quarter-mile',
    isSimulating: false,
    animationFrame: null,
    simulationResults: null,
    modeConfig: {} // Store mode-specific configuration
};

// ==================== RENDERER ====================
let renderer = null;

// ==================== INITIALIZATION ====================
async function init() {
    console.log('🏁 Initializing Hypercar Simulator...');

    renderer = new RaceRenderer('raceCanvas');
    await loadVehicles();
    setupEventListeners();
    updateModeUI();

    console.log('✅ Simulator ready!');
}

// ==================== VEHICLE LOADING ====================
async function loadVehicles() {
    try {
        const response = await fetch(`${API_URL}/api/vehicles`);
        if (!response.ok) {
            throw new Error(`Failed to load vehicles: ${response.statusText}`);
        }

        state.vehicles = await response.json();
        console.log('Loaded vehicles:', state.vehicles);

        renderVehicleSelection();
    } catch (error) {
        console.error('Error loading vehicles:', error);
        showError('Failed to load vehicle database. Make sure the backend server is running on port 8000.');
    }
}

// ==================== UI RENDERING ====================
function renderVehicleSelection() {
    const container = document.getElementById('vehicleSelect');
    if (!container) return;

    container.innerHTML = '';

    for (const [id, name] of Object.entries(state.vehicles)) {
        const option = document.createElement('div');
        option.className = 'vehicle-option';
        option.dataset.vehicleId = id;

        // Check if vehicle is tuned
        const isTuned = window.tuningSystem?.vehicleTunes.has(id);
        if (isTuned) {
            option.classList.add('vehicle-tuned');
        }

        option.innerHTML = `
            <div class="vehicle-checkbox"></div>
            <div class="vehicle-name">${name}</div>
        `;

        option.addEventListener('click', () => toggleVehicle(id, option));
        container.appendChild(option);
    }

    // Trigger event so tuning system can add tune buttons
    window.dispatchEvent(new CustomEvent('vehiclesLoaded'));
}

function toggleVehicle(vehicleId, element) {
    if (state.isSimulating) return;

    if (state.selectedVehicles.has(vehicleId)) {
        state.selectedVehicles.delete(vehicleId);
        element.classList.remove('selected');
    } else {
        if (state.selectedVehicles.size >= 3) {
            showError('Maximum 3 vehicles allowed');
            return;
        }
        state.selectedVehicles.add(vehicleId);
        element.classList.add('selected');
    }

    console.log('Selected vehicles:', Array.from(state.selectedVehicles));
}

// ==================== MODE SWITCHING ====================
function updateModeUI() {
    const mode = RACE_MODES[state.currentMode];

    const raceTitle = document.getElementById('raceTitle');
    if (raceTitle) raceTitle.textContent = mode.title;

    const metricsSubtitle = document.getElementById('metricsSubtitle');
    if (metricsSubtitle) metricsSubtitle.textContent = mode.metricsSubtitle;

    renderModeSettings();
}

function renderModeSettings() {
    const container = document.getElementById('modeSettingsContent');
    if (!container) return;

    const mode = RACE_MODES[state.currentMode];
    let html = '';

    switch (state.currentMode) {
        case 'custom-distance':
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">📏</span>
                        Race Distance
                    </label>
                    <div class="input-with-unit">
                        <input type="range" id="customDistance" min="100" max="10000" value="500" step="50">
                        <span class="unit"><span id="customDistanceValue">500</span>m</span>
                    </div>
                </div>
            `;
            break;

        case 'lap-race':
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">🔄</span>
                        Number of Laps
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="lapCount" value="3" min="1" max="10" step="1">
                        <span class="unit">laps</span>
                    </div>
                </div>
                <div class="input-field">
                    <label>
                        <span class="label-icon">📏</span>
                        Lap Distance
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="lapDistance" value="1000" min="200" max="5000" step="100">
                        <span class="unit">meters</span>
                    </div>
                </div>
                <div class="info-text">
                    Total Distance: <strong><span id="totalLapDistance">3000</span>m</strong>
                </div>
            `;
            break;

        case 'acceleration-zone':
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">🏁</span>
                        Start Speed
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="accelStartSpeed" value="0" min="0" max="300" step="10">
                        <span class="unit">km/h</span>
                    </div>
                </div>
                <div class="input-field">
                    <label>
                        <span class="label-icon">🎯</span>
                        End Speed
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="accelEndSpeed" value="100" min="10" max="400" step="10">
                        <span class="unit">km/h</span>
                    </div>
                </div>
                <div class="presets">
                    <button class="preset-btn" onclick="setAccelPreset(0, 100)">0-100</button>
                    <button class="preset-btn" onclick="setAccelPreset(0, 200)">0-200</button>
                    <button class="preset-btn" onclick="setAccelPreset(50, 100)">50-100</button>
                    <button class="preset-btn" onclick="setAccelPreset(100, 200)">100-200</button>
                </div>
            `;
            break;

        case 'roll-race':
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">🏁</span>
                        Starting Speed
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="rollStartSpeed" value="60" min="0" max="200" step="10">
                        <span class="unit">km/h</span>
                    </div>
                </div>
                <div class="input-field">
                    <label>
                        <span class="label-icon">🎯</span>
                        Target Speed
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="rollTargetSpeed" value="200" min="100" max="400" step="10">
                        <span class="unit">km/h</span>
                    </div>
                </div>
                <div class="presets">
                    <button class="preset-btn" onclick="setRollPreset(60, 200)">60-200</button>
                    <button class="preset-btn" onclick="setRollPreset(100, 250)">100-250</button>
                    <button class="preset-btn" onclick="setRollPreset(80, 180)">80-180</button>
                </div>
            `;
            break;

        case 'top-speed':
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">⏱️</span>
                        Test Duration
                    </label>
                    <div class="input-with-unit">
                        <input type="number" id="topSpeedDuration" value="120" min="60" max="300" step="10">
                        <span class="unit">seconds</span>
                    </div>
                </div>
            `;
            break;

        default:
            html = `
                <div class="input-field">
                    <label>
                        <span class="label-icon">📏</span>
                        Race Distance
                    </label>
                    <div class="input-with-unit">
                        <input type="number" value="${Math.round(mode.distance)}" disabled>
                        <span class="unit">meters</span>
                    </div>
                </div>
            `;
    }

    container.innerHTML = html;

    // Setup event listeners for dynamic updates
    if (state.currentMode === 'custom-distance') {
        const slider = document.getElementById('customDistance');
        const valueDisplay = document.getElementById('customDistanceValue');
        slider?.addEventListener('input', (e) => {
            valueDisplay.textContent = e.target.value;
        });
    }

    if (state.currentMode === 'lap-race') {
        const updateTotalDistance = () => {
            const laps = parseInt(document.getElementById('lapCount')?.value || 3);
            const distance = parseInt(document.getElementById('lapDistance')?.value || 1000);
            const total = laps * distance;
            const display = document.getElementById('totalLapDistance');
            if (display) display.textContent = total;
        };

        document.getElementById('lapCount')?.addEventListener('input', updateTotalDistance);
        document.getElementById('lapDistance')?.addEventListener('input', updateTotalDistance);
    }
}

// Global preset functions for acceleration zone and roll race
window.setAccelPreset = (start, end) => {
    const startInput = document.getElementById('accelStartSpeed');
    const endInput = document.getElementById('accelEndSpeed');
    if (startInput) startInput.value = start;
    if (endInput) endInput.value = end;
};

window.setRollPreset = (start, target) => {
    const startInput = document.getElementById('rollStartSpeed');
    const targetInput = document.getElementById('rollTargetSpeed');
    if (startInput) startInput.value = start;
    if (targetInput) targetInput.value = target;
};

// ==================== SIMULATION ====================
async function startSimulation() {
    if (state.isSimulating) return;

    if (state.selectedVehicles.size === 0) {
        showError('Please select at least one vehicle');
        return;
    }

    state.isSimulating = true;
    updateButtonStates();
    updateStatusIndicator('Running', 'warning');

    const metricsPanel = document.getElementById('metricsPanel');
    if (metricsPanel) metricsPanel.style.display = 'none';

    try {
        const mode = RACE_MODES[state.currentMode];
        const config = getModeConfig();

        const params = {
            vehicle_ids: Array.from(state.selectedVehicles),
            environment: {
                temperature_celsius: parseFloat(document.getElementById('temperature')?.value || 20),
                altitude_meters: parseFloat(document.getElementById('altitude')?.value || 0)
            },
            timestep: 0.01,
            max_time: config.maxTime,
            target_distance: config.distance,
            start_velocity: config.startSpeed,
            tuning_mods: getTuningMods()
        };

        console.log('Starting simulation with params:', params);

        const response = await fetch(`${API_URL}/api/simulate/drag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            throw new Error(`Simulation failed: ${response.statusText}`);
        }

        const results = await response.json();
        state.simulationResults = results;

        console.log('Simulation complete:', results);

        renderSpeedometers(results.results);
        animateRace(results, config);

    } catch (error) {
        console.error('Simulation error:', error);
        showError(`Simulation failed: ${error.message}`);
        state.isSimulating = false;
        updateButtonStates();
        updateStatusIndicator('Error', 'error');
    }
}

function getModeConfig() {
    const mode = RACE_MODES[state.currentMode];
    const config = { ...mode };

    switch (state.currentMode) {
        case 'custom-distance':
            config.distance = parseFloat(document.getElementById('customDistance')?.value || 500);
            break;

        case 'lap-race':
            const laps = parseInt(document.getElementById('lapCount')?.value || 3);
            const lapDistance = parseFloat(document.getElementById('lapDistance')?.value || 1000);
            config.distance = laps * lapDistance;
            config.laps = laps;
            config.lapDistance = lapDistance;
            break;

        case 'acceleration-zone':
            const accelStart = parseFloat(document.getElementById('accelStartSpeed')?.value || 0);
            const accelEnd = parseFloat(document.getElementById('accelEndSpeed')?.value || 100);
            config.startSpeed = accelStart / 3.6; // Convert to m/s
            config.targetSpeed = accelEnd;
            config.distance = 2000; // Sufficient for most acceleration tests
            break;

        case 'roll-race':
            const rollStart = parseFloat(document.getElementById('rollStartSpeed')?.value || 60);
            const rollTarget = parseFloat(document.getElementById('rollTargetSpeed')?.value || 200);
            config.startSpeed = rollStart / 3.6; // Convert to m/s
            config.targetSpeed = rollTarget;
            break;

        case 'top-speed':
            config.maxTime = parseFloat(document.getElementById('topSpeedDuration')?.value || 120);
            break;
    }

    return config;
}

function renderSpeedometers(results) {
    const container = document.getElementById('speedometersContainer');
    if (!container) return;

    container.innerHTML = '';

    results.forEach(result => {
        const card = document.createElement('div');
        card.className = 'speedometer-card';
        card.dataset.vehicleName = result.vehicle_name;

        card.innerHTML = `
            <div class="speedometer-header">${result.vehicle_name}</div>
            <div class="speedometer-display">
                <div class="speedometer-value">
                    <span class="speed-number">0</span>
                    <span class="speed-unit">km/h</span>
                </div>
                <div class="speedometer-rpm">
                    <span>RPM:</span>
                    <span class="rpm-value">0</span>
                </div>
                <div class="speedometer-gear">
                    <span>Gear:</span>
                    <span>1</span>
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}

function animateRace(results, config) {
    const maxSnapshots = Math.max(...results.results.map(r => r.snapshots.length));
    let currentFrame = 0;
    const frameDelay = 16; // ~60fps

    const animate = () => {
        if (currentFrame >= maxSnapshots) {
            state.isSimulating = false;
            updateButtonStates();
            updateStatusIndicator('Complete', 'success');
            displayResults(results, config);
            return;
        }

        const vehicleStates = results.results.map(result => {
            const snapshot = result.snapshots[Math.min(currentFrame, result.snapshots.length - 1)];
            return {
                name: result.vehicle_name,
                distance: snapshot.distance,
                velocity: snapshot.velocity,
                rpm: snapshot.rpm,
                gear: snapshot.gear
            };
        });

        if (renderer) {
            renderer.render(vehicleStates, config.distance);
        }

        updateSpeedometers(vehicleStates);

        const currentTime = results.results[0].snapshots[currentFrame]?.time || 0;
        updateRaceStats(currentTime, config);

        currentFrame++;
        state.animationFrame = setTimeout(animate, frameDelay);
    };

    animate();
}

function updateSpeedometers(vehicleStates) {
    vehicleStates.forEach(state => {
        const card = document.querySelector(`.speedometer-card[data-vehicle-name="${state.name}"]`);
        if (card) {
            const speedKmh = Math.round(state.velocity * 3.6);
            card.querySelector('.speed-number').textContent = speedKmh;
            card.querySelector('.rpm-value').textContent = Math.round(state.rpm);
            card.querySelector('.speedometer-gear span').textContent = state.gear;
        }
    });
}

function updateRaceStats(time, config) {
    const statsContainer = document.getElementById('raceStats');
    if (!statsContainer) return;

    statsContainer.innerHTML = `
        <span class="stat-item">Time: <strong>${time.toFixed(2)}s</strong></span>
    `;
}

function displayResults(results, config) {
    const metricsPanel = document.getElementById('metricsPanel');
    const metricsContent = document.getElementById('metricsContent');

    if (!metricsPanel || !metricsContent) return;

    metricsContent.innerHTML = '';

    results.results.forEach(result => {
        const vehicleDiv = document.createElement('div');
        vehicleDiv.className = 'vehicle-metrics';

        let metricsHTML = `<div class="vehicle-metrics-header">${result.vehicle_name}</div>`;

        // Add tuning stats if vehicle is tuned
        const tuningStats = getTuningStatsHTML(result.vehicle_name);
        if (tuningStats) {
            metricsHTML += tuningStats;
        }

        // Split times section
        if (config.showSplits) {
            const splits = calculateSpeedSplits(result.snapshots);
            metricsHTML += '<div class="splits-section"><h4>Split Times</h4><div class="splits-grid">';

            SPEED_SPLITS.forEach(speed => {
                if (splits[speed]) {
                    metricsHTML += `
                        <div class="split-item">
                            <div class="split-label">${speed} km/h</div>
                            <div class="split-value">${splits[speed].toFixed(2)}s</div>
                        </div>
                    `;
                }
            });

            metricsHTML += '</div></div>';
        }

        // Mode-specific metrics
        metricsHTML += '<div class="metrics-grid">';

        if (config.accelerationMode) {
            const accelTime = calculateAccelerationTime(result.snapshots, config.startSpeed * 3.6, config.targetSpeed);
            const avgAccel = calculateAverageAcceleration(result.snapshots, config.startSpeed * 3.6, config.targetSpeed);

            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">${Math.round(config.startSpeed * 3.6)}-${config.targetSpeed} km/h</div>
                    <div class="metric-value">${accelTime ? accelTime.toFixed(2) : 'N/A'}s</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Acceleration</div>
                    <div class="metric-value">${avgAccel ? avgAccel.toFixed(2) : 'N/A'} m/s²</div>
                </div>
            `;
        } else if (config.rollStart) {
            const rollTime = calculateAccelerationTime(result.snapshots, config.startSpeed * 3.6, config.targetSpeed);
            const avgAccel = calculateAverageAcceleration(result.snapshots, config.startSpeed * 3.6, config.targetSpeed);

            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">${Math.round(config.startSpeed * 3.6)}-${config.targetSpeed} km/h</div>
                    <div class="metric-value">${rollTime ? rollTime.toFixed(2) : 'N/A'}s</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Acceleration</div>
                    <div class="metric-value">${avgAccel ? avgAccel.toFixed(2) : 'N/A'} m/s²</div>
                </div>
            `;
        } else if (config.topSpeedMode) {
            const topSpeed = Math.max(...result.snapshots.map(s => s.velocity * 3.6));

            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">Top Speed</div>
                    <div class="metric-value">${topSpeed.toFixed(1)} km/h</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Time to Top Speed</div>
                    <div class="metric-value">${result.snapshots[result.snapshots.length - 1].time.toFixed(2)}s</div>
                </div>
            `;
        } else if (config.showLapTimes) {
            // Lap times
            const lapTimes = calculateLapTimes(result.snapshots, config.laps, config.lapDistance);
            const totalTime = result.snapshots[result.snapshots.length - 1].time;
            const avgSpeed = (config.distance / totalTime) * 3.6;

            lapTimes.forEach((lapTime, index) => {
                metricsHTML += `
                    <div class="metric-item">
                        <div class="metric-label">Lap ${index + 1}</div>
                        <div class="metric-value">${lapTime.toFixed(2)}s</div>
                    </div>
                `;
            });

            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">Total Time</div>
                    <div class="metric-value">${totalTime.toFixed(2)}s</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Average Speed</div>
                    <div class="metric-value">${avgSpeed.toFixed(1)} km/h</div>
                </div>
            `;
        } else {
            // Standard drag race metrics
            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">0-100 km/h</div>
                    <div class="metric-value">${result.time_to_100kmh || 'N/A'}s</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">0-200 km/h</div>
                    <div class="metric-value">${result.time_to_200kmh || 'N/A'}s</div>
                </div>
            `;

            const finalSnapshot = result.snapshots[result.snapshots.length - 1];

            if (state.currentMode === 'quarter-mile') {
                metricsHTML += `
                    <div class="metric-item">
                        <div class="metric-label">1/4 Mile Time</div>
                        <div class="metric-value">${result.quarter_mile_time || 'N/A'}s</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">1/4 Mile Speed</div>
                        <div class="metric-value">${result.quarter_mile_speed || 'N/A'} km/h</div>
                    </div>
                `;
            } else {
                metricsHTML += `
                    <div class="metric-item">
                        <div class="metric-label">Finish Time</div>
                        <div class="metric-value">${finalSnapshot.time.toFixed(2)}s</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Finish Speed</div>
                        <div class="metric-value">${(finalSnapshot.velocity * 3.6).toFixed(1)} km/h</div>
                    </div>
                `;
            }
        }

        metricsHTML += '</div>';
        vehicleDiv.innerHTML = metricsHTML;
        metricsContent.appendChild(vehicleDiv);
    });

    metricsPanel.style.display = 'block';
}

// ==================== CALCULATION HELPERS ====================
function calculateSpeedSplits(snapshots) {
    const splits = {};

    SPEED_SPLITS.forEach(targetSpeed => {
        for (const snapshot of snapshots) {
            const speedKmh = snapshot.velocity * 3.6;
            if (speedKmh >= targetSpeed) {
                splits[targetSpeed] = snapshot.time;
                break;
            }
        }
    });

    return splits;
}

function calculateAccelerationTime(snapshots, startKmh, targetKmh) {
    let startTime = null;
    let endTime = null;

    for (const snapshot of snapshots) {
        const speedKmh = snapshot.velocity * 3.6;

        if (startTime === null && speedKmh >= startKmh) {
            startTime = snapshot.time;
        }

        if (startTime !== null && speedKmh >= targetKmh) {
            endTime = snapshot.time;
            break;
        }
    }

    if (startTime !== null && endTime !== null) {
        return endTime - startTime;
    }

    return null;
}

function calculateAverageAcceleration(snapshots, startKmh, targetKmh) {
    let startSnapshot = null;
    let endSnapshot = null;

    for (const snapshot of snapshots) {
        const speedKmh = snapshot.velocity * 3.6;

        if (!startSnapshot && speedKmh >= startKmh) {
            startSnapshot = snapshot;
        }

        if (startSnapshot && speedKmh >= targetKmh) {
            endSnapshot = snapshot;
            break;
        }
    }

    if (startSnapshot && endSnapshot) {
        const deltaV = (endSnapshot.velocity - startSnapshot.velocity);
        const deltaT = endSnapshot.time - startSnapshot.time;
        return deltaV / deltaT;
    }

    return null;
}

function calculateLapTimes(snapshots, numLaps, lapDistance) {
    const lapTimes = [];
    let previousLapTime = 0;

    for (let lap = 1; lap <= numLaps; lap++) {
        const targetDistance = lap * lapDistance;

        for (const snapshot of snapshots) {
            if (snapshot.distance >= targetDistance) {
                lapTimes.push(snapshot.time - previousLapTime);
                previousLapTime = snapshot.time;
                break;
            }
        }
    }

    return lapTimes;
}

function resetSimulation() {
    if (state.animationFrame) {
        clearTimeout(state.animationFrame);
        state.animationFrame = null;
    }

    if (renderer) {
        renderer.render([]);
    }

    const speedometersContainer = document.getElementById('speedometersContainer');
    if (speedometersContainer) {
        speedometersContainer.innerHTML = '';
    }

    const metricsPanel = document.getElementById('metricsPanel');
    if (metricsPanel) {
        metricsPanel.style.display = 'none';
    }

    const statsContainer = document.getElementById('raceStats');
    if (statsContainer) {
        statsContainer.innerHTML = '<span class="stat-item">Time: <strong>0.0s</strong></span>';
    }

    state.isSimulating = false;
    state.simulationResults = null;
    updateButtonStates();
    updateStatusIndicator('Ready', 'ready');
}

// ==================== UI HELPERS ====================
function updateButtonStates() {
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (startBtn) {
        startBtn.disabled = state.isSimulating;
        startBtn.style.opacity = state.isSimulating ? '0.5' : '1';
        startBtn.style.cursor = state.isSimulating ? 'not-allowed' : 'pointer';
    }

    if (resetBtn) {
        resetBtn.disabled = state.isSimulating;
        resetBtn.style.opacity = state.isSimulating ? '0.5' : '1';
        resetBtn.style.cursor = state.isSimulating ? 'not-allowed' : 'pointer';
    }
}

function updateStatusIndicator(text, status) {
    const statusText = document.querySelector('.status-text');
    const statusDot = document.querySelector('.status-dot');

    if (statusText) statusText.textContent = text;

    if (statusDot) {
        statusDot.style.background =
            status === 'success' ? '#00FF9D' :
                status === 'warning' ? '#FFD700' :
                    status === 'error' ? '#FF0066' :
                        '#00FF9D';
    }
}

function showError(message) {
    console.error(message);
    alert(message);
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.addEventListener('click', startSimulation);
    }

    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetSimulation);
    }

    const modeTabs = document.querySelectorAll('.mode-tab');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            if (mode && !state.isSimulating) {
                modeTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                state.currentMode = mode;
                updateModeUI();
                resetSimulation();
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (state.isSimulating) return;

        // Number keys 1-8 for mode switching
        if (e.key >= '1' && e.key <= '8') {
            const modes = Object.keys(RACE_MODES);
            const index = parseInt(e.key) - 1;
            if (index < modes.length) {
                const mode = modes[index];
                state.currentMode = mode;
                modeTabs.forEach((tab, i) => {
                    tab.classList.toggle('active', i === index);
                });
                updateModeUI();
                resetSimulation();
            }
        }

        // Space to start/stop
        if (e.code === 'Space' && !state.isSimulating) {
            e.preventDefault();
            startSimulation();
        }

        // R to reset
        if (e.key === 'r' || e.key === 'R') {
            resetSimulation();
        }
    });
}

// ==================== TUNING SYSTEM INTEGRATION ====================
function applyVehicleTuning(vehicleIds) {
    if (!window.tuningSystem) {
        console.log('Tuning system not available, using stock specs');
        return null;
    }

    const tunedVehicles = {};

    vehicleIds.forEach(vehicleId => {
        const tune = window.tuningSystem.vehicleTunes.get(vehicleId);
        if (tune) {
            tunedVehicles[vehicleId] = tune;
            console.log(`Applied tuning for ${vehicleId}:`, tune);
        }
    });

    return Object.keys(tunedVehicles).length > 0 ? tunedVehicles : null;
}
function getTuningMods() {
    if (!window.tuningSystem) return null;

    const selectedVehicles = Array.from(state.selectedVehicles || []);
    const tuningMods = {};
    let hasMods = false;

    selectedVehicles.forEach(vehicleId => {
        const tune = window.tuningSystem.getTune(vehicleId);
        tuningMods[vehicleId] = tune;

        // Check if actually modified
        if (tune.engine !== 'stock' || tune.tires !== 'street' ||
            tune.aero !== 'stock' || tune.weight !== 'stock' ||
            tune.transmission !== 'stock' || tune.boostPressure !== 1.0 ||
            tune.nitrousOxide) {
            hasMods = true;
        }
    });

    return hasMods ? tuningMods : null;
}

function getTuningStatsHTML(vehicleId) {
    if (!window.tuningSystem) return '';

    const tune = window.tuningSystem.vehicleTunes.get(vehicleId);
    if (!tune) return '';

    const presets = window.tuningSystem.defaultTunePresets;
    const stats = [];

    if (tune.engine !== 'stock') {
        const enginePreset = presets.engine[tune.engine];
        stats.push(`Engine: ${enginePreset.name} (+${Math.round((enginePreset.powerMultiplier - 1) * 100)}%)`);
    }

    if (tune.tires !== 'street') {
        const tirePreset = presets.tires[tune.tires];
        stats.push(`Tires: ${tirePreset.name}`);
    }

    if (tune.aero !== 'stock') {
        const aeroPreset = presets.aero[tune.aero];
        stats.push(`Aero: ${aeroPreset.name}`);
    }

    if (tune.weight !== 'stock') {
        const weightPreset = presets.weight[tune.weight];
        stats.push(`Weight: -${weightPreset.weightReduction}kg`);
    }

    if (tune.transmission !== 'stock') {
        const transPreset = presets.transmission[tune.transmission];
        stats.push(`Trans: ${transPreset.name}`);
    }

    if (tune.boostPressure !== 1.0) {
        stats.push(`Boost: ${tune.boostPressure.toFixed(1)}x`);
    }

    if (tune.nitrousOxide && tune.nitrousHorsepower > 0) {
        stats.push(`Nitrous: +${tune.nitrousHorsepower}HP`);
    }

    if (stats.length === 0) return '';

    return `
        <div class="tuning-stats">
            <h5>⚡ Tuning Modifications:</h5>
            <ul>
                ${stats.map(stat => `<li>${stat}</li>`).join('')}
            </ul>
        </div>
    `;
}

window.applyVehicleTuning = applyVehicleTuning;
window.getTuningStatsHTML = getTuningStatsHTML;

// ==================== START APP ====================
document.addEventListener('DOMContentLoaded', init);