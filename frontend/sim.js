import { RaceRenderer } from './render.js';

// Detect if we're served from backend (port 8000) or separate frontend server
const API_BASE = window.location.port === '8000' ? '/api' : 'http://localhost:8000/api';

class SimulationController {
    constructor() {
        this.vehicles = {};
        this.selectedVehicles = [];
        this.simulationData = null;
        this.renderer = null;
        this.isSimulating = false;

        this.init();
    }

    async init() {
        await this.loadVehicles();
        this.setupEventListeners();
        this.renderer = new RaceRenderer('raceCanvas');
        this.updateHUD(null);
    }

    async loadVehicles() {
        try {
            console.log('Fetching vehicles from:', `${API_BASE}/vehicles`);
            const response = await fetch(`${API_BASE}/vehicles`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.vehicles = await response.json();
            console.log('Loaded vehicles:', this.vehicles);
            this.renderVehicleOptions();
        } catch (error) {
            console.error('Failed to load vehicles:', error);
            alert('Failed to connect to simulation server. Make sure backend is running on port 8000.\n\nError: ' + error.message);
        }
    }

    renderVehicleOptions() {
        const container = document.getElementById('vehicleSelect');
        container.innerHTML = '';

        Object.entries(this.vehicles).forEach(([id, name]) => {
            const option = document.createElement('div');
            option.className = 'vehicle-option';
            option.innerHTML = `
                <input type="checkbox" id="vehicle_${id}" value="${id}">
                <label for="vehicle_${id}" style="cursor: pointer; flex: 1;">${name}</label>
            `;

            const checkbox = option.querySelector('input');
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedVehicles.push(id);
                    option.classList.add('selected');
                } else {
                    this.selectedVehicles = this.selectedVehicles.filter(v => v !== id);
                    option.classList.remove('selected');
                }
            });

            container.appendChild(option);
        });
    }

    setupEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startSimulation();
        });

        document.getElementById('resetBtn').addEventListener('click', () => {
            this.reset();
        });
    }

    async startSimulation() {
        if (this.selectedVehicles.length === 0) {
            alert('Please select at least one vehicle');
            return;
        }

        if (this.isSimulating) return;

        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = true;
        startBtn.textContent = 'SIMULATING...';
        startBtn.classList.add('loading');

        this.isSimulating = true;

        const params = {
            vehicle_ids: this.selectedVehicles,
            environment: {
                temperature_celsius: parseFloat(document.getElementById('temperature').value),
                altitude_meters: parseFloat(document.getElementById('altitude').value),
                air_pressure_kpa: 101.325
            },
            timestep: 0.01,
            max_time: 30.0
        };

        try {
            console.log('Starting simulation with params:', params);
            const response = await fetch(`${API_BASE}/simulate/drag`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Simulation failed');
            }

            this.simulationData = await response.json();
            console.log('Simulation complete:', this.simulationData);
            this.displayMetrics();
            await this.animateSimulationRealTime();

        } catch (error) {
            console.error('Simulation error:', error);
            alert('Simulation failed: ' + error.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = 'START SIMULATION';
            startBtn.classList.remove('loading');
            this.isSimulating = false;
        }
    }

    displayMetrics() {
        const metricsSection = document.getElementById('metricsSection');
        const metricsContent = document.getElementById('metricsContent');

        metricsContent.innerHTML = '';

        this.simulationData.results.forEach(result => {
            const metricItem = document.createElement('div');
            metricItem.className = 'metric-item';

            metricItem.innerHTML = `
                <div class="metric-vehicle">${result.vehicle_name}</div>
                <div class="metric-row">
                    <span class="metric-label">0-100 km/h</span>
                    <span class="metric-value">${result.time_to_100kmh ? result.time_to_100kmh + 's' : 'N/A'}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">0-200 km/h</span>
                    <span class="metric-value">${result.time_to_200kmh ? result.time_to_200kmh + 's' : 'N/A'}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Quarter Mile</span>
                    <span class="metric-value">${result.quarter_mile_time ? result.quarter_mile_time + 's' : 'N/A'}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Trap Speed</span>
                    <span class="metric-value">${result.quarter_mile_speed ? result.quarter_mile_speed + ' km/h' : 'N/A'}</span>
                </div>
            `;

            metricsContent.appendChild(metricItem);
        });

        metricsSection.style.display = 'block';
    }

    async animateSimulationRealTime() {
        if (!this.simulationData || !this.renderer) return;

        const results = this.simulationData.results;
        const startTime = performance.now();
        let lastFrameTime = startTime;

        const animate = () => {
            const currentTime = performance.now();
            const elapsedSeconds = (currentTime - startTime) / 1000;
            const deltaTime = (currentTime - lastFrameTime) / 1000;
            lastFrameTime = currentTime;

            // Find snapshots for current simulation time
            const vehicleStates = results.map(result => {
                // Find the snapshot closest to current elapsed time
                let snapshot = result.snapshots[0];
                for (let i = 0; i < result.snapshots.length; i++) {
                    if (result.snapshots[i].time <= elapsedSeconds) {
                        snapshot = result.snapshots[i];
                    } else {
                        break;
                    }
                }

                return {
                    name: result.vehicle_name,
                    distance: snapshot.distance,
                    velocity: snapshot.velocity,
                    gear: snapshot.gear,
                    rpm: snapshot.rpm,
                    time: snapshot.time
                };
            });

            // Update renderer
            this.renderer.render(vehicleStates);

            // Update HUD with first vehicle
            if (vehicleStates.length > 0) {
                this.updateHUD(vehicleStates[0]);
            }

            // Check if simulation is complete (all vehicles finished or max time reached)
            const maxTime = Math.max(...results.map(r => r.snapshots[r.snapshots.length - 1].time));

            if (elapsedSeconds < maxTime) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    updateHUD(state) {
        const speedValue = document.getElementById('speedValue');
        const gearValue = document.getElementById('gearValue');
        const rpmValue = document.getElementById('rpmValue');
        const distanceValue = document.getElementById('distanceValue');
        const speedArc = document.getElementById('speedArc');

        if (!state) {
            speedValue.textContent = '0';
            gearValue.textContent = 'N';
            rpmValue.textContent = '0';
            distanceValue.textContent = '0m';
            speedArc.setAttribute('d', 'M 30 170 A 85 85 0 0 1 30 170');
            return;
        }

        const speedKmh = Math.round(state.velocity * 3.6);
        speedValue.textContent = speedKmh;
        gearValue.textContent = state.gear;
        rpmValue.textContent = Math.round(state.rpm).toLocaleString();
        distanceValue.textContent = Math.round(state.distance) + 'm';

        // Update speedometer arc (0-350 km/h range)
        const maxSpeed = 350;
        const speedRatio = Math.min(speedKmh / maxSpeed, 1);
        const angle = speedRatio * 280; // 280 degrees total arc

        const startAngle = 220; // Start from bottom left
        const endAngle = startAngle + angle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const centerX = 100;
        const centerY = 100;
        const radius = 85;

        const startX = centerX + radius * Math.cos(startRad);
        const startY = centerY + radius * Math.sin(startRad);
        const endX = centerX + radius * Math.cos(endRad);
        const endY = centerY + radius * Math.sin(endRad);

        const largeArcFlag = angle > 180 ? 1 : 0;

        const arcPath = `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
        speedArc.setAttribute('d', arcPath);
    }

    reset() {
        this.simulationData = null;
        this.renderer.clear();
        this.updateHUD(null);
        document.getElementById('metricsSection').style.display = 'none';
    }
}

// Initialize application
const app = new SimulationController();