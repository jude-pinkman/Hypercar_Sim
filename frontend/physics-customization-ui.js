// ==========================================
// PHYSICS CUSTOMIZATION SYSTEM
// Adds UI for full physics parameter control
// ==========================================

class PhysicsCustomizationSystem {
    constructor() {
        this.physicsConfig = this.getDefaultConfig();
        this.presets = this.initializePresets();
    }

    // ==========================================
    // DEFAULT CONFIGURATION
    // ==========================================
    getDefaultConfig() {
        return {
            tires: {
                initial_tire_temp: 25.0,
                optimal_tire_temp: 85.0,
                max_tire_temp: 150.0,
                base_friction_coefficient: 1.3,
                cold_tire_penalty: 0.30,
                hot_tire_penalty: 0.30,
                wear_rate: 0.0001,
                heating_from_acceleration: 2.0,
                cooling_rate: 0.02
            },
            weight_transfer: {
                base_front_weight: 0.40,
                transfer_coefficient: 0.15,
                max_rear_weight: 0.85,
                center_of_gravity_height: 0.5,
                wheelbase: 2.7
            },
            launch_control: {
                enabled: true,
                rpm_target_percent: 0.65,
                rpm_variation: 50.0,
                completion_speed: 5.0,
                clutch_slip_rate: 0.3,
                max_launch_traction: 1.3
            },
            turbo: {
                enabled: true,
                max_boost_pressure: 2.0,
                spool_rate: 3.0,
                boost_decay_rate: 5.0,
                power_multiplier_per_bar: 0.12,
                min_rpm_for_boost: 2000,
                turbo_lag: 0.3
            },
            drs: {
                enabled: true,
                min_activation_speed: 150.0,
                drag_reduction: 0.15,
                downforce_reduction: 0.30,
                activation_delay: 0.5
            },
            gearbox: {
                shift_duration: 0.15,
                shift_power_loss: 0.30,
                clutch_slip: 0.15,
                gear_1_shift_percent: 0.68,
                gear_2_shift_percent: 0.72,
                gear_3_shift_percent: 0.76,
                gear_4_shift_percent: 0.78,
                gear_5_shift_percent: 0.81,
                gear_6plus_shift_percent: 0.84
            },
            fuel: {
                enabled: false,
                initial_fuel_kg: 100.0,
                fuel_tank_capacity: 100.0,
                consumption_rate_idle: 0.5,
                consumption_rate_cruise: 8.0,
                consumption_rate_full_throttle: 45.0,
                fuel_weight_affects_performance: true
            },
            brakes: {
                enabled: false,
                enable_brake_temp: false,
                initial_brake_temp: 100.0,
                optimal_brake_temp: 400.0,
                max_brake_temp: 800.0,
                brake_fade_coefficient: 0.5,
                brake_heating_rate: 50.0,
                brake_cooling_rate: 20.0
            },
            hybrid: {
                enable_battery_soc: false,
                initial_battery_soc: 1.0,
                battery_capacity_kwh: 7.5,
                max_discharge_rate_kw: 120.0,
                regen_efficiency: 0.70,
                regen_max_power_kw: 100.0,
                battery_deployment_mode: "full",
                min_battery_reserve: 0.10,
                motor_efficiency: 0.95
            },
            traction_control: {
                enabled: true,
                intervention_threshold: 0.10,
                intervention_aggression: 0.5,
                mode: "sport",
                allow_wheelspin: true
            },
            weather: {
                track_condition: "dry",
                track_temperature: 30.0,
                rain_intensity: 0.0,
                standing_water: 0.0,
                dry_grip_multiplier: 1.0,
                damp_grip_multiplier: 0.85,
                wet_grip_multiplier: 0.60,
                snow_grip_multiplier: 0.30,
                ice_grip_multiplier: 0.10,
                enable_wind: false,
                wind_speed: 0.0,
                wind_direction: 0.0
            }
        };
    }

    // ==========================================
    // PRESETS
    // ==========================================
    initializePresets() {
        return {
            arcade: {
                name: 'Arcade',
                description: 'Simplified physics - easy to drive',
                config: {
                    tires: {
                        base_friction_coefficient: 1.5,
                        cold_tire_penalty: 0.0,
                        hot_tire_penalty: 0.0,
                        wear_rate: 0.0
                    },
                    fuel: { enabled: false },
                    brakes: { enabled: false },
                    hybrid: { enable_battery_soc: false }
                }
            },
            realistic: {
                name: 'Realistic',
                description: 'Balanced realism for comparisons',
                config: {
                    tires: {
                        optimal_tire_temp: 85.0,
                        wear_rate: 0.0001
                    },
                    fuel: {
                        enabled: true,
                        initial_fuel_kg: 80.0
                    }
                }
            },
            maximum: {
                name: 'Maximum',
                description: 'All features enabled - maximum realism',
                config: {
                    fuel: { enabled: true },
                    brakes: {
                        enabled: true,
                        enable_brake_temp: true
                    },
                    hybrid: { enable_battery_soc: true },
                    tires: {
                        wear_rate: 0.0005
                    }
                }
            },
            endurance_race: {
                name: 'Endurance Race',
                description: 'Long distance racing',
                config: {
                    fuel: {
                        enabled: true,
                        initial_fuel_kg: 80.0,
                        consumption_rate_full_throttle: 55.0
                    },
                    tires: {
                        wear_rate: 0.001
                    },
                    brakes: {
                        enabled: true,
                        enable_brake_temp: true
                    }
                }
            },
            wet_race: {
                name: 'Wet Race',
                description: 'Rain conditions',
                config: {
                    weather: {
                        track_condition: "wet",
                        rain_intensity: 0.7,
                        wet_grip_multiplier: 0.60
                    },
                    tires: {
                        optimal_tire_temp: 65.0,
                        base_friction_coefficient: 1.1
                    },
                    drs: {
                        enabled: false
                    }
                }
            }
        };
    }

    // ==========================================
    // APPLY PRESET
    // ==========================================
    applyPreset(presetName) {
        if (!this.presets[presetName]) return;
        
        const preset = this.presets[presetName];
        
        // Deep merge preset config with default config
        this.physicsConfig = this.deepMerge(this.getDefaultConfig(), preset.config);
        
        console.log(`Applied physics preset: ${preset.name}`);
        return this.physicsConfig;
    }

    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }

    // ==========================================
    // RENDER PHYSICS PANEL
    // ==========================================
    openPhysicsPanel() {
        this.removeExistingPanel();

        const overlay = document.createElement('div');
        overlay.className = 'tuning-overlay';
        overlay.onclick = () => this.closePhysicsPanel();
        document.body.appendChild(overlay);

        const panel = document.createElement('div');
        panel.className = 'tuning-panel physics-panel';
        panel.onclick = (e) => e.stopPropagation();

        panel.innerHTML = `
            <div class="tuning-header">
                <h2>⚙️ Physics Customization</h2>
                <button class="close-btn" onclick="window.physicsCustomization.closePhysicsPanel()">✕</button>
            </div>

            <div class="preset-selector">
                <h3>Quick Presets</h3>
                <div class="preset-buttons">
                    ${Object.keys(this.presets).map(key => {
                        const preset = this.presets[key];
                        return `
                            <button class="preset-btn" onclick="window.physicsCustomization.selectPreset('${key}')">
                                <strong>${preset.name}</strong>
                                <span>${preset.description}</span>
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>

            <div class="physics-sections">
                ${this.renderTiresSection()}
                ${this.renderLaunchControlSection()}
                ${this.renderTurboSection()}
                ${this.renderDRSSection()}
                ${this.renderGearboxSection()}
                ${this.renderFuelSection()}
                ${this.renderBrakesSection()}
                ${this.renderHybridSection()}
                ${this.renderTractionControlSection()}
                ${this.renderWeatherSection()}
            </div>

            <div class="physics-footer">
                <button class="btn btn-secondary" onclick="window.physicsCustomization.resetToDefaults()">
                    Reset to Defaults
                </button>
                <button class="btn btn-primary" onclick="window.physicsCustomization.applyPhysics()">
                    Apply Physics Settings
                </button>
            </div>
        `;

        document.body.appendChild(panel);
        this.populateValues();
    }

    // ==========================================
    // RENDER SECTIONS
    // ==========================================
    renderTiresSection() {
        return `
            <div class="physics-section">
                <h3>🔥 Tire Physics</h3>
                <div class="physics-grid">
                    ${this.renderSlider('tires.optimal_tire_temp', 'Optimal Temp', 50, 120, 5, '°C')}
                    ${this.renderSlider('tires.base_friction_coefficient', 'Base Grip (μ)', 0.8, 2.0, 0.1)}
                    ${this.renderSlider('tires.cold_tire_penalty', 'Cold Penalty', 0, 0.6, 0.05)}
                    ${this.renderSlider('tires.wear_rate', 'Wear Rate', 0, 0.002, 0.0001)}
                </div>
            </div>
        `;
    }

    renderLaunchControlSection() {
        return `
            <div class="physics-section">
                <h3>🚀 Launch Control</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="launch_control.enabled" checked>
                    <span>Enable Launch Control</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('launch_control.rpm_target_percent', 'RPM Target', 0.5, 0.9, 0.05, '%')}
                    ${this.renderSlider('launch_control.max_launch_traction', 'Max Traction', 1.0, 2.0, 0.1, 'g')}
                </div>
            </div>
        `;
    }

    renderTurboSection() {
        return `
            <div class="physics-section">
                <h3>💨 Turbo/Boost</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="turbo.enabled" checked>
                    <span>Enable Turbo</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('turbo.max_boost_pressure', 'Max Boost', 1.0, 4.0, 0.1, 'bar')}
                    ${this.renderSlider('turbo.spool_rate', 'Spool Rate', 1.0, 10.0, 0.5, 'bar/s')}
                    ${this.renderSlider('turbo.power_multiplier_per_bar', 'Power/Bar', 0.05, 0.25, 0.01)}
                </div>
            </div>
        `;
    }

    renderDRSSection() {
        return `
            <div class="physics-section">
                <h3>🪂 DRS / Active Aero</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="drs.enabled" checked>
                    <span>Enable DRS</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('drs.min_activation_speed', 'Min Speed', 100, 200, 10, 'km/h')}
                    ${this.renderSlider('drs.drag_reduction', 'Drag Reduction', 0, 0.3, 0.05)}
                </div>
            </div>
        `;
    }

    renderGearboxSection() {
        return `
            <div class="physics-section">
                <h3>⚙️ Gearbox</h3>
                <div class="physics-grid">
                    ${this.renderSlider('gearbox.shift_duration', 'Shift Time', 0.05, 0.3, 0.01, 's')}
                    ${this.renderSlider('gearbox.shift_power_loss', 'Power Loss', 0, 0.5, 0.05)}
                </div>
            </div>
        `;
    }

    renderFuelSection() {
        return `
            <div class="physics-section">
                <h3>⛽ Fuel System</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="fuel.enabled">
                    <span>Enable Fuel Consumption</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('fuel.initial_fuel_kg', 'Initial Fuel', 20, 150, 10, 'kg')}
                    ${this.renderSlider('fuel.consumption_rate_full_throttle', 'Consumption', 20, 80, 5, 'kg/hr')}
                </div>
            </div>
        `;
    }

    renderBrakesSection() {
        return `
            <div class="physics-section">
                <h3>🛑 Brake System</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="brakes.enabled">
                    <span>Enable Brake Simulation</span>
                </label>
                <label class="toggle-label">
                    <input type="checkbox" id="brakes.enable_brake_temp">
                    <span>Enable Brake Temperature</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('brakes.max_brake_temp', 'Max Temp', 600, 1000, 25, '°C')}
                    ${this.renderSlider('brakes.brake_fade_coefficient', 'Fade Coeff', 0.3, 0.8, 0.1)}
                </div>
            </div>
        `;
    }

    renderHybridSection() {
        return `
            <div class="physics-section">
                <h3>⚡ Hybrid System</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="hybrid.enable_battery_soc">
                    <span>Enable Battery Management</span>
                </label>
                <div class="physics-grid">
                    ${this.renderSlider('hybrid.battery_capacity_kwh', 'Capacity', 5, 20, 0.5, 'kWh')}
                    ${this.renderSlider('hybrid.max_discharge_rate_kw', 'Max Power', 80, 200, 10, 'kW')}
                </div>
            </div>
        `;
    }

    renderTractionControlSection() {
        return `
            <div class="physics-section">
                <h3>🎯 Traction Control</h3>
                <label class="toggle-label">
                    <input type="checkbox" id="traction_control.enabled" checked>
                    <span>Enable Traction Control</span>
                </label>
                <div class="physics-grid">
                    <div class="input-field">
                        <label>Mode</label>
                        <select id="traction_control.mode">
                            <option value="off">Off</option>
                            <option value="sport" selected>Sport</option>
                            <option value="full">Full</option>
                        </select>
                    </div>
                    ${this.renderSlider('traction_control.intervention_aggression', 'Aggression', 0.2, 0.9, 0.1)}
                </div>
            </div>
        `;
    }

    renderWeatherSection() {
        return `
            <div class="physics-section">
                <h3>🌦️ Weather Conditions</h3>
                <div class="physics-grid">
                    <div class="input-field">
                        <label>Track Condition</label>
                        <select id="weather.track_condition">
                            <option value="dry" selected>Dry</option>
                            <option value="damp">Damp</option>
                            <option value="wet">Wet</option>
                            <option value="snow">Snow</option>
                            <option value="ice">Ice</option>
                        </select>
                    </div>
                    ${this.renderSlider('weather.track_temperature', 'Track Temp', 0, 50, 5, '°C')}
                    ${this.renderSlider('weather.rain_intensity', 'Rain', 0, 1, 0.1)}
                </div>
            </div>
        `;
    }

    renderSlider(path, label, min, max, step, unit = '') {
        const id = path.replace(/\./g, '_');
        return `
            <div class="input-field">
                <label for="${id}">
                    ${label}
                    ${unit ? `<span class="unit-label">${unit}</span>` : ''}
                </label>
                <input type="range" 
                       id="${id}" 
                       data-path="${path}"
                       min="${min}" 
                       max="${max}" 
                       step="${step}"
                       oninput="window.physicsCustomization.updateSliderValue(this)">
                <span class="value-display" id="${id}_value">-</span>
            </div>
        `;
    }

    // ==========================================
    // UI INTERACTIONS
    // ==========================================
    populateValues() {
        // Populate checkboxes
        const checkboxes = document.querySelectorAll('.physics-panel input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            const path = checkbox.id.split('.');
            let value = this.physicsConfig;
            path.forEach(key => {
                value = value?.[key];
            });
            checkbox.checked = value === true;
        });

        // Populate sliders
        const sliders = document.querySelectorAll('.physics-panel input[type="range"]');
        sliders.forEach(slider => {
            const path = slider.dataset.path.split('.');
            let value = this.physicsConfig;
            path.forEach(key => {
                value = value?.[key];
            });
            slider.value = value;
            this.updateSliderValue(slider);
        });

        // Populate selects
        const selects = document.querySelectorAll('.physics-panel select');
        selects.forEach(select => {
            const path = select.id.split('.');
            let value = this.physicsConfig;
            path.forEach(key => {
                value = value?.[key];
            });
            select.value = value;
        });
    }

    updateSliderValue(slider) {
        const valueDisplay = document.getElementById(slider.id + '_value');
        if (valueDisplay) {
            valueDisplay.textContent = parseFloat(slider.value).toFixed(slider.step < 0.01 ? 4 : 2);
        }
    }

    selectPreset(presetName) {
        this.applyPreset(presetName);
        this.populateValues();
        
        // Visual feedback
        const buttons = document.querySelectorAll('.preset-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        event.target.closest('.preset-btn').classList.add('active');
    }

    resetToDefaults() {
        this.physicsConfig = this.getDefaultConfig();
        this.populateValues();
        this.updatePhysicsButtonStatus(false);
        console.log('🔄 Physics reset to defaults');
    }

    applyPhysics() {
        // Collect all values from the form
        const panel = document.querySelector('.physics-panel');
        
        // Checkboxes
        const checkboxes = panel.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            const path = checkbox.id.split('.');
            this.setNestedValue(this.physicsConfig, path, checkbox.checked);
        });

        // Sliders
        const sliders = panel.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            const path = slider.dataset.path.split('.');
            this.setNestedValue(this.physicsConfig, path, parseFloat(slider.value));
        });

        // Selects
        const selects = panel.querySelectorAll('select');
        selects.forEach(select => {
            const path = select.id.split('.');
            this.setNestedValue(this.physicsConfig, path, select.value);
        });

        this.closePhysicsPanel();
        
        // Dispatch event so sim.js can access the config
        window.dispatchEvent(new CustomEvent('physicsConfigChanged', {
            detail: { config: this.physicsConfig }
        }));

        console.log('✅ Physics configuration applied:', this.physicsConfig);
        
        // Update the button to show active status
        this.updatePhysicsButtonStatus(true);
    }
    
    updatePhysicsButtonStatus(isActive) {
        // Find the physics button and update its appearance
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            if (btn.textContent.includes('Open Physics Settings')) {
                if (isActive) {
                    btn.style.background = 'linear-gradient(135deg, #00ff9d, #00d4ff)';
                    btn.innerHTML = `
                        <span class="btn-icon">⚙️</span>
                        <span class="btn-text">Physics: CUSTOM</span>
                    `;
                } else {
                    btn.style.background = '';
                    btn.innerHTML = `
                        <span class="btn-icon">⚙️</span>
                        <span class="btn-text">Open Physics Settings</span>
                    `;
                }
            }
        });
    }

    setNestedValue(obj, path, value) {
        for (let i = 0; i < path.length - 1; i++) {
            obj = obj[path[i]];
        }
        obj[path[path.length - 1]] = value;
    }

    getPhysicsConfig() {
        return this.physicsConfig;
    }

    closePhysicsPanel() {
        this.removeExistingPanel();
    }

    removeExistingPanel() {
        const existingOverlay = document.querySelector('.tuning-overlay');
        const existingPanel = document.querySelector('.physics-panel');
        if (existingOverlay) existingOverlay.remove();
        if (existingPanel) existingPanel.remove();
    }
}

// Initialize global instance
window.physicsCustomization = new PhysicsCustomizationSystem();

export { PhysicsCustomizationSystem };
