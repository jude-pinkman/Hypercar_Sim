import { RaceRenderer } from './render.js';

const API_BASE = 'http://localhost:8000';

class SimulationController {
    constructor() {
        this.renderer = null;
        this.vehicles = {};
        this.selectedVehicles = new Set();
        this.isRunning = false;
        this.animationFrame = null;
        this.simulationStartTime = 0;
        this.simulationResults = null;
    }

    async init() {
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        this.renderer = new RaceRenderer('raceCanvas');
        await this.loadVehicles();
        this.setupEventListeners();
    }

    async loadVehicles() {
        try {
            const response = await fetch(`${API_BASE}/api/vehicles`);
            this.vehicles = await response.json();
            this.renderVehicleList();
        } catch (error) {
            console.error('Failed to load vehicles:', error);
        }
    }

    renderVehicleList() {
        const container = document.getElementById('vehicleSelect');
        if (!container) {
            console.error('Vehicle select container not found');
            return;
        }

        container.innerHTML = '';

        Object.entries(this.vehicles).forEach(([id, name]) => {
            const item = document.createElement('div');
            item.className = 'vehicle-item';
            item.innerHTML = `
                <input type="checkbox" id="vehicle-${id}" value="${id}">
                <label for="vehicle-${id}">${name}</label>
            `;

            const checkbox = item.querySelector('input');
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedVehicles.add(id);
                    item.classList.add('selected');
                } else {
                    this.selectedVehicles.delete(id);
                    item.classList.remove('selected');
                }
            });

            item.addEventListener('click', (e) => {
                if (e.target !== checkbox) {
                    checkbox.click();
                }
            });

            container.appendChild(item);
        });
    }

    setupEventListeners() {
        const startBtn = document.getElementById('startBtn');
        const resetBtn = document.getElementById('resetBtn');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startSimulation());
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.reset());
        }
    }

    async startSimulation() {
        if (this.selectedVehicles.size === 0) {
            alert('Please select at least one vehicle');
            return;
        }

        if (this.isRunning) return;

        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.classList.add('loading');
        }

        this.isRunning = true;

        try {
            const params = {
                vehicle_ids: Array.from(this.selectedVehicles),
                environment: {
                    temperature_celsius: parseFloat(document.getElementById('temperature')?.value || 20),
                    altitude_meters: parseFloat(document.getElementById('altitude')?.value || 0),
                    air_pressure_kpa: 101.325
                },
                timestep: 0.01,
                max_time: 30.0
            };

            const response = await fetch(`${API_BASE}/api/simulate/drag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.animateSimulation(data.results);
        } catch (error) {
            console.error('Simulation failed:', error);
            alert(`Simulation failed: ${error.message}`);
            this.reset();
        }
    }

    animateSimulation(results) {
        this.simulationResults = results;
        this.createSpeedometers(results);
        
        // Reset the start time for real-time playback
        this.simulationStartTime = null;
        
        const animate = (currentTimestamp) => {
            if (!this.isRunning) return;

            // Initialize start time on first frame
            if (this.simulationStartTime === null) {
                this.simulationStartTime = currentTimestamp;
            }

            // Calculate elapsed time in REAL SECONDS since animation started
            const elapsedRealTime = (currentTimestamp - this.simulationStartTime) / 1000;

            // Update race stats timer
            const raceStats = document.getElementById('raceStats');
            if (raceStats) {
                raceStats.innerHTML = `<span class="stat-item">Time: <strong>${elapsedRealTime.toFixed(1)}s</strong></span>`;
            }

            // Find the simulation data that matches current real time
            const vehicleStates = results.map(result => {
                // Find the snapshot closest to current elapsed time
                const snapshot = this.findSnapshotAtTime(result.snapshots, elapsedRealTime);
                
                return {
                    name: result.vehicle_name,
                    distance: snapshot.distance,
                    velocity: snapshot.velocity,
                    gear: snapshot.gear,
                    rpm: snapshot.rpm,
                    acceleration: snapshot.acceleration,
                    power_kw: snapshot.power_kw,
                    time: snapshot.time
                };
            });

            // Update race visualization
            if (this.renderer) {
                this.renderer.render(vehicleStates);
            }

            // Update speedometers with smooth transitions
            this.updateSpeedometers(vehicleStates);

            // Check if race is finished (all vehicles crossed quarter mile or max time reached)
            const maxSimTime = Math.max(...results.map(r => 
                r.snapshots[r.snapshots.length - 1].time
            ));
            
            const allFinished = vehicleStates.every(state => state.distance >= 402.336);
            
            if (elapsedRealTime >= maxSimTime || allFinished) {
                this.showMetrics(results);
                this.isRunning = false;

                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.classList.remove('loading');
                }
                return;
            }

            this.animationFrame = requestAnimationFrame(animate);
        };

        this.animationFrame = requestAnimationFrame(animate);
    }

    findSnapshotAtTime(snapshots, targetTime) {
        // Find the snapshot at or just before the target time
        // If target time is past all snapshots, return the last one
        
        if (targetTime <= 0) return snapshots[0];
        if (targetTime >= snapshots[snapshots.length - 1].time) {
            return snapshots[snapshots.length - 1];
        }

        // Binary search for efficiency with large datasets
        let left = 0;
        let right = snapshots.length - 1;
        
        while (left < right) {
            const mid = Math.floor((left + right + 1) / 2);
            if (snapshots[mid].time <= targetTime) {
                left = mid;
            } else {
                right = mid - 1;
            }
        }

        // Interpolate between current and next snapshot for smooth animation
        const current = snapshots[left];
        const next = snapshots[Math.min(left + 1, snapshots.length - 1)];
        
        if (left === snapshots.length - 1 || current.time === next.time) {
            return current;
        }

        // Linear interpolation
        const t = (targetTime - current.time) / (next.time - current.time);
        
        return {
            time: targetTime,
            distance: current.distance + (next.distance - current.distance) * t,
            velocity: current.velocity + (next.velocity - current.velocity) * t,
            acceleration: current.acceleration + (next.acceleration - current.acceleration) * t,
            gear: next.gear, // Use next gear (discrete value)
            rpm: current.rpm + (next.rpm - current.rpm) * t,
            power_kw: current.power_kw + (next.power_kw - current.power_kw) * t
        };
    }

    createSpeedometers(results) {
        const container = document.getElementById('speedometersContainer');
        if (!container) {
            console.error('Speedometers container not found');
            return;
        }

        container.innerHTML = '';

        results.forEach((result) => {
            const vehicleId = this.getVehicleId(result.vehicle_name);
            const brandClass = this.getBrandClass(vehicleId);
            const logoUrl = this.getBrandLogoUrl(brandClass);

            const card = document.createElement('div');
            card.className = `speedometer-card speedometer-${brandClass}`;
            card.dataset.vehicleId = vehicleId;

            card.innerHTML = `
                <div class="vehicle-name">${result.vehicle_name}</div>
                <div class="speedometer">
                    ${logoUrl ? `<img src="${logoUrl}" alt="${brandClass} logo" class="brand-logo">` : ''}
                    <svg class="speedo-svg" viewBox="0 0 200 200">
                        ${this.createSpeedoSVG(brandClass)}
                    </svg>
                    <div class="speedo-center ${brandClass}-center">
                        <div class="speed-value">0</div>
                        <div class="speed-unit">KM/H</div>
                    </div>
                </div>
                <div class="vehicle-stats">
                    <div class="stat-item">
                        <div class="stat-label">Gear</div>
                        <div class="stat-value stat-gear">1</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">RPM</div>
                        <div class="stat-value stat-rpm">0</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Power</div>
                        <div class="stat-value stat-power">0 kW</div>
                    </div>
                </div>
            `;

            container.appendChild(card);
        });
    }

    getBrandLogoUrl(brandClass) {
        const logos = {
            koenigsegg: 'https://www.carlogos.org/car-logos/koenigsegg-logo.png',
            bugatti: 'https://www.carlogos.org/car-logos/bugatti-logo.png',
            hennessey: 'https://www.carlogos.org/car-logos/hennessey-logo.png'
        };

        return logos[brandClass] || null;
    }

    createSpeedoSVG(brandClass) {
        const centerX = 100;
        const centerY = 100;
        const radius = 80;
        const startAngle = -225;
        const endAngle = 45;
        const totalAngle = endAngle - startAngle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startRad);
        const y1 = centerY + radius * Math.sin(startRad);
        const x2 = centerX + radius * Math.cos(endRad);
        const y2 = centerY + radius * Math.sin(endRad);

        const largeArc = totalAngle > 180 ? 1 : 0;

        const arcPath = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
        const arcLength = (totalAngle / 360) * (2 * Math.PI * radius);

        const colors = {
            koenigsegg: '#FFD700',
            bugatti: '#0066FF',
            hennessey: '#FF0066'
        };

        const color = colors[brandClass] || '#00FF9D';

        const markers = [];
        const speeds = [0, 50, 100, 150, 200, 250, 300, 350, 400];

        speeds.forEach(speed => {
            const angle = startAngle + (speed / 400) * totalAngle;
            const rad = (angle * Math.PI) / 180;
            const x = centerX + (radius - 5) * Math.cos(rad);
            const y = centerY + (radius - 5) * Math.sin(rad);
            const textX = centerX + (radius - 20) * Math.cos(rad);
            const textY = centerY + (radius - 20) * Math.sin(rad);

            markers.push(`
                <line x1="${centerX + (radius - 10) * Math.cos(rad)}" 
                      y1="${centerY + (radius - 10) * Math.sin(rad)}" 
                      x2="${x}" y2="${y}" 
                      class="gauge-marker" />
                ${speed % 100 === 0 ? `<text x="${textX}" y="${textY}" class="gauge-text" text-anchor="middle">${speed}</text>` : ''}
            `);
        });

        return `
            <path d="${arcPath}" fill="none" class="gauge-bg" />
            <path d="${arcPath}" 
                  fill="none" 
                  class="speed-arc gauge-progress" 
                  stroke-dasharray="${arcLength}" 
                  stroke-dashoffset="${arcLength}"
                  stroke-linecap="round" />
            ${markers.join('')}
            <circle cx="${centerX}" cy="${centerY}" r="4" fill="${color}" opacity="0.8" />
        `;
    }

    updateSpeedometers(vehicleStates) {
        vehicleStates.forEach((state) => {
            const vehicleId = this.getVehicleId(state.name);
            const card = document.querySelector(`[data-vehicle-id="${vehicleId}"]`);
            if (!card) return;

            const speedKmh = Math.round(state.velocity * 3.6);
            const maxSpeed = 400;

            // Update speed value with smooth number changes
            const speedValue = card.querySelector('.speed-value');
            if (speedValue) {
                speedValue.textContent = speedKmh;
            }

            const statGear = card.querySelector('.stat-gear');
            const statRpm = card.querySelector('.stat-rpm');
            const statPower = card.querySelector('.stat-power');

            if (statGear) statGear.textContent = state.gear;
            if (statRpm) statRpm.textContent = Math.round(state.rpm).toLocaleString();
            if (statPower) statPower.textContent = `${Math.round(state.power_kw)} kW`;

            // Update speedometer arc with smooth transitions
            const arc = card.querySelector('.speed-arc');
            if (arc) {
                const totalLength = parseFloat(arc.getAttribute('stroke-dasharray'));
                const progress = Math.min(speedKmh / maxSpeed, 1);
                const offset = totalLength * (1 - progress);
                arc.style.strokeDashoffset = offset;
            }
        });
    }

    showMetrics(results) {
        const panel = document.getElementById('metricsPanel');
        const content = document.getElementById('metricsContent');

        if (!panel || !content) {
            console.warn('Metrics panel not found in DOM');
            return;
        }

        content.innerHTML = '';

        results.forEach(result => {
            const card = document.createElement('div');
            card.className = 'metric-card';

            const metrics = [
                { label: '0-100 km/h', value: result.time_to_100kmh ? `${result.time_to_100kmh}s` : 'N/A' },
                { label: '0-200 km/h', value: result.time_to_200kmh ? `${result.time_to_200kmh}s` : 'N/A' },
                { label: 'Quarter Mile', value: result.quarter_mile_time ? `${result.quarter_mile_time}s` : 'N/A' },
                { label: 'Quarter Mile Speed', value: result.quarter_mile_speed ? `${result.quarter_mile_speed} km/h` : 'N/A' }
            ];

            card.innerHTML = `
                <div class="metric-vehicle">${result.vehicle_name}</div>
                ${metrics.map(m => `
                    <div class="metric-row">
                        <span class="metric-label">${m.label}</span>
                        <span class="metric-value">${m.value}</span>
                    </div>
                `).join('')}
            `;

            content.appendChild(card);
        });

        panel.style.display = 'block';
    }

    getVehicleId(vehicleName) {
        for (const [id, name] of Object.entries(this.vehicles)) {
            if (name === vehicleName) return id;
        }
        return '';
    }

    getBrandClass(vehicleId) {
        if (vehicleId.includes('koenigsegg')) return 'koenigsegg';
        if (vehicleId.includes('bugatti')) return 'bugatti';
        if (vehicleId.includes('hennessey')) return 'hennessey';
        return 'default';
    }

    reset() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }

        this.isRunning = false;
        this.simulationStartTime = 0;

        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.classList.remove('loading');
        }

        const speedometersContainer = document.getElementById('speedometersContainer');
        if (speedometersContainer) {
            speedometersContainer.innerHTML = '';
        }

        const metricsPanel = document.getElementById('metricsPanel');
        if (metricsPanel) {
            metricsPanel.style.display = 'none';
        }

        const raceStats = document.getElementById('raceStats');
        if (raceStats) {
            raceStats.innerHTML = '<span class="stat-item">Time: <strong>0.0s</strong></span>';
        }

        if (this.renderer) {
            this.renderer.clear();
            this.renderer.render([]);
        }
    }
}

const app = new SimulationController();
app.init();