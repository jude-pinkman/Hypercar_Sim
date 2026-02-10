import { RaceRenderer } from './render.js';

const API_BASE = 'http://localhost:8000';

class SimulationController {
    constructor() {
        this.renderer = null;
        this.vehicles = {};
        this.selectedVehicles = new Set();
        this.isRunning = false;
        this.animationFrame = null;
    }

    async init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        // Initialize renderer
        this.renderer = new RaceRenderer('raceCanvas');

        // Load vehicles
        await this.loadVehicles();

        // Setup event listeners
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

            // Make entire card clickable
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
        // Create speedometer displays
        this.createSpeedometers(results);

        const maxFrames = Math.max(...results.map(r => r.snapshots.length));
        let currentFrame = 0;

        const animate = () => {
            if (currentFrame >= maxFrames) {
                this.showMetrics(results);
                this.isRunning = false;

                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.classList.remove('loading');
                }
                return;
            }

            const vehicleStates = results.map(result => {
                const snapshot = result.snapshots[Math.min(currentFrame, result.snapshots.length - 1)];
                return {
                    name: result.vehicle_name,
                    distance: snapshot.distance,
                    velocity: snapshot.velocity,
                    gear: snapshot.gear,
                    rpm: snapshot.rpm,
                    acceleration: snapshot.acceleration,
                    power_kw: snapshot.power_kw
                };
            });

            // Update race visualization
            if (this.renderer) {
                this.renderer.render(vehicleStates);
            }

            // Update speedometers
            this.updateSpeedometers(vehicleStates);

            currentFrame++;
            this.animationFrame = requestAnimationFrame(animate);
        };

        animate();
    }

    createSpeedometers(results) {
        const container = document.getElementById('speedometersContainer');
        if (!container) {
            console.error('Speedometers container not found');
            return;
        }

        container.innerHTML = '';

        results.forEach((result, index) => {
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

        // Calculate arc path
        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startRad);
        const y1 = centerY + radius * Math.sin(startRad);
        const x2 = centerX + radius * Math.cos(endRad);
        const y2 = centerY + radius * Math.sin(endRad);

        const largeArc = totalAngle > 180 ? 1 : 0;

        const arcPath = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;

        // Calculate total arc length for animation
        const arcLength = (totalAngle / 360) * (2 * Math.PI * radius);

        // Brand-specific colors
        const colors = {
            koenigsegg: '#FFD700',
            bugatti: '#0066FF',
            hennessey: '#FF0066'
        };

        const color = colors[brandClass] || '#00FF9D';

        // Speed markers
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
            <!-- Background arc -->
            <path d="${arcPath}" fill="none" class="gauge-bg" />
            
            <!-- Progress arc -->
            <path d="${arcPath}" 
                  fill="none" 
                  class="speed-arc gauge-progress" 
                  stroke-dasharray="${arcLength}" 
                  stroke-dashoffset="${arcLength}"
                  stroke-linecap="round" />
            
            <!-- Speed markers -->
            ${markers.join('')}
            
            <!-- Center dot -->
            <circle cx="${centerX}" cy="${centerY}" r="4" fill="${color}" opacity="0.8" />
        `;
    }

    updateSpeedometers(vehicleStates) {
        vehicleStates.forEach((state, index) => {
            const vehicleId = this.getVehicleId(state.name);
            const card = document.querySelector(`[data-vehicle-id="${vehicleId}"]`);
            if (!card) return;

            const speedKmh = Math.round(state.velocity * 3.6);
            const maxSpeed = 400; // km/h

            // Update speed value
            const speedValue = card.querySelector('.speed-value');
            if (speedValue) {
                speedValue.textContent = speedKmh;
            }

            // Update stats
            const statGear = card.querySelector('.stat-gear');
            const statRpm = card.querySelector('.stat-rpm');
            const statPower = card.querySelector('.stat-power');

            if (statGear) statGear.textContent = state.gear;
            if (statRpm) statRpm.textContent = Math.round(state.rpm).toLocaleString();
            if (statPower) statPower.textContent = `${Math.round(state.power_kw)} kW`;

            // Update progress arc
            const arc = card.querySelector('.speed-arc');
            if (arc) {
                const totalLength = parseFloat(arc.getAttribute('stroke-dasharray'));
                const progress = Math.min(speedKmh / maxSpeed, 1);
                const offset = totalLength * (1 - progress);
                arc.setAttribute('stroke-dashoffset', offset);
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

        if (this.renderer) {
            this.renderer.clear();
            this.renderer.render([]);
        }
    }
}

// Initialize the application
const app = new SimulationController();
app.init();