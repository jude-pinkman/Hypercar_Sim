import { RaceRenderer } from './render.js';

// ==================== CONFIGURATION ====================
const API_URL = 'http://localhost:8000';

// Race mode configurations
const RACE_MODES = {
    'quarter-mile': {
        title: '1/4 Mile Drag Race',
        distance: 402.336, // meters
        startSpeed: 0,
        maxTime: 30,
        metricsSubtitle: '0-100, 0-200 & quarter mile times'
    },
    'half-mile': {
        title: '1/2 Mile Drag Race',
        distance: 804.672, // meters
        startSpeed: 0,
        maxTime: 45,
        metricsSubtitle: '0-100, 0-200 & half mile times'
    },
    'one-mile': {
        title: '1 Mile Drag Race',
        distance: 1609.344, // meters
        startSpeed: 0,
        maxTime: 60,
        metricsSubtitle: '0-100, 0-200 & one mile times'
    },
    'roll-race': {
        title: 'Roll Race (60-200 km/h)',
        distance: 1000, // meters (sufficient for acceleration)
        startSpeed: 60 / 3.6, // 60 km/h in m/s
        maxTime: 40,
        metricsSubtitle: '60-200 km/h acceleration time',
        rollStart: true
    },
    'top-speed': {
        title: 'Top Speed Challenge',
        distance: 5000, // 5km for top speed
        startSpeed: 0,
        maxTime: 180, // 3 minutes
        metricsSubtitle: 'Maximum velocity achieved',
        topSpeedMode: true
    }
};

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
    simulationResults: null
};

// ==================== RENDERER ====================
let renderer = null;

// ==================== INITIALIZATION ====================
async function init() {
    console.log('🏁 Initializing Hypercar Simulator...');
    
    // Initialize renderer
    renderer = new RaceRenderer('raceCanvas');
    
    // Load vehicles from backend
    await loadVehicles();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize UI for default mode
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
        
        option.innerHTML = `
            <div class="vehicle-checkbox"></div>
            <div class="vehicle-name">${name}</div>
        `;
        
        option.addEventListener('click', () => toggleVehicle(id, option));
        container.appendChild(option);
    }
}

function toggleVehicle(vehicleId, element) {
    if (state.isSimulating) return;
    
    if (state.selectedVehicles.has(vehicleId)) {
        state.selectedVehicles.delete(vehicleId);
        element.classList.remove('selected');
    } else {
        // Limit to 3 vehicles for performance
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
    
    // Update race title
    const raceTitle = document.getElementById('raceTitle');
    if (raceTitle) raceTitle.textContent = mode.title;
    
    // Update metrics subtitle
    const metricsSubtitle = document.getElementById('metricsSubtitle');
    if (metricsSubtitle) metricsSubtitle.textContent = mode.metricsSubtitle;
    
    // Update mode-specific settings
    renderModeSettings();
}

function renderModeSettings() {
    const container = document.getElementById('modeSettingsContent');
    if (!container) return;
    
    const mode = RACE_MODES[state.currentMode];
    
    if (state.currentMode === 'roll-race') {
        container.innerHTML = `
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
        `;
    } else if (state.currentMode === 'top-speed') {
        container.innerHTML = `
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
    } else {
        // Drag race modes
        container.innerHTML = `
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
}

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
    
    // Hide previous results
    const metricsPanel = document.getElementById('metricsPanel');
    if (metricsPanel) metricsPanel.style.display = 'none';
    
    try {
        const mode = RACE_MODES[state.currentMode];
        
        // Prepare simulation parameters
        const params = {
            vehicle_ids: Array.from(state.selectedVehicles),
            environment: {
                temperature_celsius: parseFloat(document.getElementById('temperature').value),
                altitude_meters: parseFloat(document.getElementById('altitude').value)
            },
            timestep: 0.01,
            max_time: mode.maxTime,
            target_distance: mode.topSpeedMode ? null : mode.distance, // No distance limit for top speed
            start_velocity: mode.startSpeed || 0
        };
        
        console.log('Starting simulation with params:', params);
        
        const response = await fetch(`${API_URL}/api/simulate/drag`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error(`Simulation failed: ${response.statusText}`);
        }
        
        const results = await response.json();
        state.simulationResults = results;
        
        console.log('Simulation complete:', results);
        
        // Animate the race
        await animateRace(results, mode);
        
        // Show final results
        displayResults(results, mode);
        
        updateStatusIndicator('Complete', 'success');
    } catch (error) {
        console.error('Simulation error:', error);
        showError(`Simulation failed: ${error.message}`);
        updateStatusIndicator('Error', 'error');
    } finally {
        state.isSimulating = false;
        updateButtonStates();
    }
}

function animateRace(results, mode) {
    return new Promise((resolve) => {
        const allSnapshots = results.results.map(r => r.snapshots);
        const maxFrames = Math.max(...allSnapshots.map(s => s.length));
        let currentFrame = 0;
        const frameDelay = 16; // ~60 FPS
        const speedMultiplier = 2; // Animation speed
        
        function animate() {
            if (currentFrame >= maxFrames) {
                resolve();
                return;
            }
            
            // Get current state for each vehicle
            const vehicleStates = results.results.map((result, index) => {
                const snapshot = allSnapshots[index][Math.min(currentFrame, allSnapshots[index].length - 1)];
                return {
                    name: result.vehicle_name,
                    distance: snapshot.distance,
                    velocity: snapshot.velocity,
                    gear: snapshot.gear,
                    rpm: snapshot.rpm
                };
            });
            
            // Render race track
            renderer.render(vehicleStates, mode.distance);
            
            // Update speedometers
            updateSpeedometers(vehicleStates);
            
            // Update race stats
            if (vehicleStates.length > 0) {
                const leadSnapshot = allSnapshots[0][Math.min(currentFrame, allSnapshots[0].length - 1)];
                updateRaceStats(leadSnapshot.time, mode);
            }
            
            currentFrame += speedMultiplier;
            state.animationFrame = setTimeout(animate, frameDelay);
        }
        
        animate();
    });
}

function updateSpeedometers(vehicleStates) {
    const container = document.getElementById('speedometersContainer');
    if (!container) return;
    
    // Create speedometer cards if needed
    if (container.children.length !== vehicleStates.length) {
        container.innerHTML = '';
        vehicleStates.forEach(state => {
            const card = document.createElement('div');
            card.className = 'speedometer-card';
            card.dataset.vehicleName = state.name;
            card.innerHTML = `
                <div class="speedometer-name">${state.name}</div>
                <div class="speedometer-value">0</div>
                <div class="speedometer-unit">km/h</div>
                <div class="speedometer-gear" style="margin-top: 8px; font-size: 12px; color: var(--text-tertiary);">Gear: <span>1</span></div>
            `;
            container.appendChild(card);
        });
    }
    
    // Update values
    vehicleStates.forEach(state => {
        const card = container.querySelector(`[data-vehicle-name="${state.name}"]`);
        if (card) {
            const speedKmh = Math.round(state.velocity * 3.6);
            card.querySelector('.speedometer-value').textContent = speedKmh;
            card.querySelector('.speedometer-gear span').textContent = state.gear;
        }
    });
}

function updateRaceStats(time, mode) {
    const statsContainer = document.getElementById('raceStats');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <span class="stat-item">Time: <strong>${time.toFixed(2)}s</strong></span>
    `;
}

function displayResults(results, mode) {
    const metricsPanel = document.getElementById('metricsPanel');
    const metricsContent = document.getElementById('metricsContent');
    
    if (!metricsPanel || !metricsContent) return;
    
    metricsContent.innerHTML = '';
    
    results.results.forEach(result => {
        const vehicleDiv = document.createElement('div');
        vehicleDiv.className = 'vehicle-metrics';
        
        let metricsHTML = `<div class="vehicle-metrics-header">${result.vehicle_name}</div><div class="metrics-grid">`;
        
        if (state.currentMode === 'roll-race') {
            // Roll race metrics
            const rollStart = parseFloat(document.getElementById('rollStartSpeed')?.value || 60);
            const rollTarget = parseFloat(document.getElementById('rollTargetSpeed')?.value || 200);
            
            const rollTime = calculateRollTime(result.snapshots, rollStart, rollTarget);
            
            metricsHTML += `
                <div class="metric-item">
                    <div class="metric-label">${rollStart}-${rollTarget} km/h</div>
                    <div class="metric-value">${rollTime ? rollTime.toFixed(2) : 'N/A'}s</div>
                </div>
            `;
        } else if (state.currentMode === 'top-speed') {
            // Top speed metrics
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
        } else {
            // Drag race metrics
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
                // For half-mile and one-mile, show final time and speed
                const finalSnapshot = result.snapshots[result.snapshots.length - 1];
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

function calculateRollTime(snapshots, startKmh, targetKmh) {
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

function resetSimulation() {
    // Cancel any ongoing animation
    if (state.animationFrame) {
        clearTimeout(state.animationFrame);
        state.animationFrame = null;
    }
    
    // Clear visualization
    if (renderer) {
        renderer.render([]);
    }
    
    // Clear speedometers
    const speedometersContainer = document.getElementById('speedometersContainer');
    if (speedometersContainer) {
        speedometersContainer.innerHTML = '';
    }
    
    // Hide metrics
    const metricsPanel = document.getElementById('metricsPanel');
    if (metricsPanel) {
        metricsPanel.style.display = 'none';
    }
    
    // Reset race stats
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
    // Start button
    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.addEventListener('click', startSimulation);
    }
    
    // Reset button
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetSimulation);
    }
    
    // Mode tabs
    const modeTabs = document.querySelectorAll('.mode-tab');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            if (mode && !state.isSimulating) {
                // Update active tab
                modeTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update state
                state.currentMode = mode;
                
                // Update UI
                updateModeUI();
                
                // Reset simulation
                resetSimulation();
            }
        });
    });
}

// ==================== START APP ====================
document.addEventListener('DOMContentLoaded', init);
