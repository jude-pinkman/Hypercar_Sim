// ==========================================
// VEHICLE TUNING SYSTEM - CLEAN REBUILD
// Zero blur, perfect functionality
// ==========================================

class VehicleTuningSystem {
    constructor() {
        this.vehicleTunes = new Map();
        this.activeTuningVehicle = null;
        this.presets = this.initializePresets();
    }

    // ==========================================
    // PRESETS CONFIGURATION
    // ==========================================
    initializePresets() {
        return {
            engine: {
                stock: { name: 'Stock', power: 1.0, torque: 1.0, desc: 'Factory settings' },
                stage1: { name: 'Stage 1', power: 1.15, torque: 1.12, desc: 'ECU tune + filter' },
                stage2: { name: 'Stage 2', power: 1.30, torque: 1.25, desc: 'Exhaust + intercooler' },
                stage3: { name: 'Stage 3', power: 1.50, torque: 1.40, desc: 'Turbo upgrade' },
                extreme: { name: 'Extreme', power: 1.75, torque: 1.65, desc: 'Built engine' }
            },
            tires: {
                street: { name: 'Street Tires', grip: 1.0, resistance: 0.012, desc: 'OEM all-season' },
                sport: { name: 'Sport Tires', grip: 1.15, resistance: 0.011, desc: 'Performance summer' },
                semi_slick: { name: 'Semi-Slick', grip: 1.30, resistance: 0.010, desc: 'Track-focused' },
                racing_slick: { name: 'Racing Slicks', grip: 1.50, resistance: 0.009, desc: 'Full racing' },
                drag_radial: { name: 'Drag Radials', grip: 1.70, resistance: 0.013, desc: 'Max launch grip' }
            },
            aero: {
                stock: { name: 'Stock Aero', drag: 1.0, desc: 'Factory bodywork' },
                low_drag: { name: 'Low Drag', drag: 0.85, desc: 'Top speed optimized' },
                balanced: { name: 'Balanced', drag: 0.95, desc: 'Street/track balance' },
                high_downforce: { name: 'High Downforce', drag: 1.15, desc: 'Maximum grip' },
                top_speed: { name: 'Top Speed', drag: 0.75, desc: 'Minimum drag' }
            },
            weight: {
                stock: { name: 'Stock Weight', reduction: 0, desc: 'Factory weight' },
                light: { name: 'Light', reduction: 50, desc: 'Wheels + battery' },
                medium: { name: 'Medium', reduction: 100, desc: '+ Carbon panels' },
                heavy: { name: 'Heavy', reduction: 200, desc: '+ Interior delete' },
                extreme: { name: 'Extreme', reduction: 300, desc: 'Full race spec' }
            },
            transmission: {
                stock: { name: 'Stock', efficiency: 0.93, shift: 0.15, desc: 'OEM transmission' },
                sport: { name: 'Sport', efficiency: 0.95, shift: 0.10, desc: 'Upgraded clutch' },
                racing: { name: 'Racing DCT', efficiency: 0.96, shift: 0.05, desc: 'Dual-clutch' },
                sequential: { name: 'Sequential', efficiency: 0.97, shift: 0.08, desc: 'Dog-box racing' },
                instant: { name: 'Instant', efficiency: 0.98, shift: 0.0, desc: 'EV-like shifts' }
            },
            drivetrain: {
                rwd: { name: 'RWD', launch: 0.85, desc: 'Rear-wheel drive' },
                fwd: { name: 'FWD', launch: 0.75, desc: 'Front-wheel drive' },
                awd: { name: 'AWD', launch: 1.0, desc: 'All-wheel drive' }
            }
        };
    }

    // ==========================================
    // TUNE INITIALIZATION
    // ==========================================
    getDefaultTune() {
        return {
            engine: 'stock',
            tires: 'street',
            aero: 'stock',
            weight: 'stock',
            transmission: 'stock',
            drivetrain: 'awd',
            boostPressure: 1.0,
            launchRPM: 3000,
            finalDrive: 1.0,
            nitrousOxide: false,
            nitrousHorsepower: 0
        };
    }

    getTune(vehicleId) {
        if (!this.vehicleTunes.has(vehicleId)) {
            this.vehicleTunes.set(vehicleId, this.getDefaultTune());
        }
        return this.vehicleTunes.get(vehicleId);
    }

    // ==========================================
    // RENDER TUNING PANEL
    // ==========================================
    openTuningPanel(vehicleId, vehicleName) {
        this.activeTuningVehicle = vehicleId;
        const tune = this.getTune(vehicleId);

        // Create overlay
        this.removeExistingPanel();

        const overlay = document.createElement('div');
        overlay.className = 'tuning-overlay';
        overlay.onclick = () => this.closeTuningPanel();
        document.body.appendChild(overlay);

        // Create panel
        const panel = document.createElement('div');
        panel.className = 'tuning-panel';
        panel.innerHTML = this.generatePanelHTML(vehicleId, vehicleName, tune);
        document.body.appendChild(panel);

        // Setup event listeners
        this.setupEventListeners();
    }

    generatePanelHTML(vehicleId, vehicleName, tune) {
        return `
            <!-- Header -->
            <div class="tuning-header">
                <h3>🔧 TUNE: ${vehicleName}</h3>
                <button class="btn-close-tuning" onclick="window.tuningSystem.closeTuningPanel()">×</button>
            </div>

            <!-- Tabs -->
            <div class="tuning-tabs">
                <button class="tuning-tab active" data-tab="engine">Engine</button>
                <button class="tuning-tab" data-tab="tires">Tires</button>
                <button class="tuning-tab" data-tab="aero">Aero</button>
                <button class="tuning-tab" data-tab="weight">Weight</button>
                <button class="tuning-tab" data-tab="transmission">Transmission</button>
                <button class="tuning-tab" data-tab="advanced">Advanced</button>
            </div>

            <!-- Content -->
            <div class="tuning-content">
                ${this.generateEngineTab(tune)}
                ${this.generateTiresTab(tune)}
                ${this.generateAeroTab(tune)}
                ${this.generateWeightTab(tune)}
                ${this.generateTransmissionTab(tune)}
                ${this.generateAdvancedTab(tune)}
            </div>

            <!-- Footer -->
            <div class="tuning-footer">
                <button class="btn btn-secondary" onclick="window.tuningSystem.resetTune()">Reset to Stock</button>
                <button class="btn btn-primary" onclick="window.tuningSystem.saveTune()">Apply Tune</button>
            </div>
        `;
    }

    generateEngineTab(tune) {
        return `
            <div class="tuning-tab-content active" data-tab-content="engine">
                <h4>Engine Tuning</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('engine', tune.engine, this.presets.engine)}
                </div>
            </div>
        `;
    }

    generateTiresTab(tune) {
        return `
            <div class="tuning-tab-content" data-tab-content="tires">
                <h4>Tire Compound</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('tires', tune.tires, this.presets.tires)}
                </div>
            </div>
        `;
    }

    generateAeroTab(tune) {
        return `
            <div class="tuning-tab-content" data-tab-content="aero">
                <h4>Aerodynamics</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('aero', tune.aero, this.presets.aero)}
                </div>
            </div>
        `;
    }

    generateWeightTab(tune) {
        return `
            <div class="tuning-tab-content" data-tab-content="weight">
                <h4>Weight Reduction</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('weight', tune.weight, this.presets.weight)}
                </div>
            </div>
        `;
    }

    generateTransmissionTab(tune) {
        return `
            <div class="tuning-tab-content" data-tab-content="transmission">
                <h4>Transmission</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('transmission', tune.transmission, this.presets.transmission)}
                </div>
                
                <h4 style="margin-top: 24px;">Drivetrain</h4>
                <div class="tuning-options">
                    ${this.generateRadioOptions('drivetrain', tune.drivetrain, this.presets.drivetrain)}
                </div>
            </div>
        `;
    }

    generateAdvancedTab(tune) {
        return `
            <div class="tuning-tab-content" data-tab-content="advanced">
                <h4>Advanced Tuning</h4>
                
                <div class="tuning-slider">
                    <label>Boost Pressure</label>
                    <input type="range" id="boostPressure" min="0.5" max="2.0" step="0.1" value="${tune.boostPressure}">
                    <span class="slider-value">${tune.boostPressure.toFixed(1)}x</span>
                </div>

                <div class="tuning-slider">
                    <label>Launch RPM</label>
                    <input type="range" id="launchRPM" min="2000" max="8000" step="100" value="${tune.launchRPM}">
                    <span class="slider-value">${tune.launchRPM} RPM</span>
                </div>

                <div class="tuning-slider">
                    <label>Final Drive Ratio</label>
                    <input type="range" id="finalDrive" min="0.8" max="1.3" step="0.01" value="${tune.finalDrive}">
                    <span class="slider-value">${tune.finalDrive.toFixed(2)}x</span>
                </div>

                <div class="tuning-checkbox">
                    <label>
                        <input type="checkbox" id="nitrousOxide" ${tune.nitrousOxide ? 'checked' : ''}>
                        Enable Nitrous Oxide System
                    </label>
                </div>

                ${tune.nitrousOxide ? `
                    <div class="tuning-slider">
                        <label>Nitrous Shot (HP)</label>
                        <input type="range" id="nitrousHorsepower" min="0" max="500" step="25" value="${tune.nitrousHorsepower}">
                        <span class="slider-value">+${tune.nitrousHorsepower} HP</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateRadioOptions(category, currentValue, presets) {
        let html = '';
        for (const [key, preset] of Object.entries(presets)) {
            const checked = key === currentValue;
            html += `
                <label class="tuning-option ${checked ? 'checked' : ''}">
                    <input type="radio" name="${category}" value="${key}" ${checked ? 'checked' : ''}>
                    <div class="option-content">
                        <span class="option-name">${preset.name}</span>
                        <span class="option-details">${preset.desc}</span>
                    </div>
                </label>
            `;
        }
        return html;
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tuning-tab').forEach(tab => {
            tab.onclick = (e) => {
                const tabName = e.currentTarget.dataset.tab;

                // Update tabs
                document.querySelectorAll('.tuning-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tuning-tab-content').forEach(c => c.classList.remove('active'));

                e.currentTarget.classList.add('active');
                document.querySelector(`[data-tab-content="${tabName}"]`).classList.add('active');
            };
        });

        // Radio buttons
        document.querySelectorAll('.tuning-option input[type="radio"]').forEach(radio => {
            radio.onchange = (e) => {
                const category = e.target.name;
                const value = e.target.value;

                // Update tune
                const tune = this.getTune(this.activeTuningVehicle);
                tune[category] = value;

                // Update UI
                document.querySelectorAll(`input[name="${category}"]`).forEach(r => {
                    r.closest('.tuning-option').classList.toggle('checked', r.checked);
                });
            };
        });

        // Sliders
        this.setupSlider('boostPressure', v => `${v.toFixed(1)}x`);
        this.setupSlider('launchRPM', v => `${v} RPM`);
        this.setupSlider('finalDrive', v => `${v.toFixed(2)}x`);
        this.setupSlider('nitrousHorsepower', v => `+${v} HP`);

        // Nitrous checkbox
        const nitrousCheckbox = document.getElementById('nitrousOxide');
        if (nitrousCheckbox) {
            nitrousCheckbox.onchange = (e) => {
                const tune = this.getTune(this.activeTuningVehicle);
                tune.nitrousOxide = e.target.checked;

                // Refresh advanced tab
                const advancedContent = document.querySelector('[data-tab-content="advanced"]');
                advancedContent.innerHTML = this.generateAdvancedTab(tune).match(/<h4>[\s\S]*$/)[0];
                this.setupSlider('boostPressure', v => `${v.toFixed(1)}x`);
                this.setupSlider('launchRPM', v => `${v} RPM`);
                this.setupSlider('finalDrive', v => `${v.toFixed(2)}x`);
                this.setupSlider('nitrousHorsepower', v => `+${v} HP`);

                const newCheckbox = document.getElementById('nitrousOxide');
                if (newCheckbox) {
                    newCheckbox.checked = tune.nitrousOxide;
                    newCheckbox.onchange = arguments.callee;
                }
            };
        }
    }

    setupSlider(id, formatFunc) {
        const slider = document.getElementById(id);
        if (slider) {
            slider.oninput = (e) => {
                const value = parseFloat(e.target.value);
                const tune = this.getTune(this.activeTuningVehicle);
                tune[id] = value;

                const display = e.target.nextElementSibling;
                if (display) {
                    display.textContent = formatFunc(value);
                }
            };
        }
    }

    // ==========================================
    // SAVE & RESET
    // ==========================================
    saveTune() {
        const tune = this.getTune(this.activeTuningVehicle);
        console.log('💾 Saved tune:', tune);

        this.showNotification('✅ Tune applied successfully!', 'success');
        this.closeTuningPanel();

        // Dispatch event
        window.dispatchEvent(new CustomEvent('tuneUpdated', {
            detail: { vehicleId: this.activeTuningVehicle, tune }
        }));

        // Update indicator
        this.updateTuneIndicator(this.activeTuningVehicle);
    }

    resetTune() {
        this.vehicleTunes.set(this.activeTuningVehicle, this.getDefaultTune());

        this.showNotification('🔄 Reset to stock configuration', 'info');
        this.closeTuningPanel();

        // Dispatch event
        window.dispatchEvent(new CustomEvent('tuneUpdated', {
            detail: { vehicleId: this.activeTuningVehicle, tune: this.getDefaultTune() }
        }));

        // Update indicator
        this.updateTuneIndicator(this.activeTuningVehicle);
    }

    // ==========================================
    // UI HELPERS
    // ==========================================
    closeTuningPanel() {
        this.removeExistingPanel();
        this.activeTuningVehicle = null;
    }

    removeExistingPanel() {
        const panel = document.querySelector('.tuning-panel');
        const overlay = document.querySelector('.tuning-overlay');
        if (panel) panel.remove();
        if (overlay) overlay.remove();
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `tuning-notification tuning-notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    updateTuneIndicator(vehicleId) {
        const option = document.querySelector(`.vehicle-option[data-vehicle-id="${vehicleId}"]`);
        if (!option) return;

        const tune = this.getTune(vehicleId);
        const isTuned = tune.engine !== 'stock' || tune.tires !== 'street' ||
            tune.aero !== 'stock' || tune.weight !== 'stock' ||
            tune.transmission !== 'stock' || tune.boostPressure !== 1.0 ||
            tune.nitrousOxide;

        const existingIndicator = option.querySelector('.tune-indicator');
        if (existingIndicator) existingIndicator.remove();

        if (isTuned) {
            const indicator = document.createElement('div');
            indicator.className = 'tune-indicator';
            indicator.innerHTML = '⚡';
            indicator.title = 'Vehicle is tuned';
            option.appendChild(indicator);
        }
    }
}

// ==========================================
// INITIALIZE GLOBAL INSTANCE
// ==========================================
if (typeof window !== 'undefined') {
    window.tuningSystem = new VehicleTuningSystem();
    console.log('🔧 Tuning system initialized');
}

export { VehicleTuningSystem };