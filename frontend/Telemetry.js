/**
 * Telemetry.js - Driver Telemetry Display
 * Shows detailed data for selected driver including speed, tyres, sectors, and more
 */

class Telemetry {
    constructor(panelId, config = {}) {
        this.panel = document.getElementById(panelId);
        if (!this.panel) {
            throw new Error(`Panel with id "${panelId}" not found`);
        }

        // Configuration
        this.config = {
            updateInterval: config.updateInterval || 100,  // ms
            showSectorTimes: config.showSectorTimes !== false,
            showLapTimes: config.showLapTimes !== false,
            showTyreInfo: config.showTyreInfo !== false,
            ...config
        };

        // State
        this.currentDriver = null;
        this.lastUpdateTime = 0;
    }

    /**
     * Update telemetry display
     */
    update(driverData) {
        // Throttle updates
        const now = performance.now();
        if (now - this.lastUpdateTime < this.config.updateInterval) {
            return;
        }
        this.lastUpdateTime = now;

        this.currentDriver = driverData;
        this.render();
    }

    /**
     * Render telemetry panel
     */
    render() {
        if (!this.currentDriver) {
            this.panel.innerHTML = `
                <div class="telemetry-empty">
                    <i class="fas fa-chart-line" style="font-size: 24px; color: var(--text-secondary); margin-bottom: 0.5rem;"></i>
                    <div style="color: var(--text-secondary); font-size: 12px;">No driver selected</div>
                </div>
            `;
            return;
        }

        const driver = this.currentDriver;

        let html = `
            <div class="telemetry-header">
                <div class="telemetry-driver" style="color: ${driver.teamColor}">
                    ${driver.driverName}
                </div>
                <div class="telemetry-position">P${driver.position}</div>
            </div>

            <div class="telemetry-grid">
                <!-- Speed -->
                <div class="telemetry-card">
                    <div class="telemetry-label">Speed</div>
                    <div class="telemetry-value telemetry-speed">
                        ${driver.speedKmh.toFixed(0)}
                        <span class="telemetry-unit">km/h</span>
                    </div>
                </div>

                <!-- Lap -->
                <div class="telemetry-card">
                    <div class="telemetry-label">Lap</div>
                    <div class="telemetry-value">
                        ${driver.currentLap}
                    </div>
                </div>

                <!-- Gap -->
                <div class="telemetry-card">
                    <div class="telemetry-label">Gap</div>
                    <div class="telemetry-value ${driver.gapToLeader < 0.01 ? 'telemetry-leader' : ''}">
                        ${driver.gapToLeader < 0.01 ? 'Leader' : `+${driver.gapToLeader.toFixed(2)}s`}
                    </div>
                </div>

                <!-- Tyre -->
                <div class="telemetry-card">
                    <div class="telemetry-label">Tyre</div>
                    <div class="telemetry-value">
                        <span class="tyre-compound ${this.getTyreClass(driver.tyreCompound)}">
                            ${driver.tyreCompound}
                        </span>
                    </div>
                </div>
            </div>
        `;

        // Tyre wear detail
        if (this.config.showTyreInfo) {
            html += this.renderTyreInfo(driver);
        }

        // Sector times
        if (this.config.showSectorTimes) {
            html += this.renderSectorTimes(driver);
        }

        // Lap times
        if (this.config.showLapTimes) {
            html += this.renderLapTimes(driver);
        }

        // DRS Status
        if (driver.drsAvailable || driver.drsActive) {
            html += `
                <div class="telemetry-drs ${driver.drsActive ? 'drs-active' : 'drs-available'}">
                    <i class="fas fa-wind"></i>
                    DRS ${driver.drsActive ? 'ACTIVE' : 'Available'}
                </div>
            `;
        }

        // Pit status
        if (driver.isInPit) {
            html += `
                <div class="telemetry-pit">
                    <i class="fas fa-wrench"></i>
                    IN PIT - ${driver.pitStopCount} stop${driver.pitStopCount !== 1 ? 's' : ''}
                </div>
            `;
        }

        // Fuel
        html += `
            <div class="telemetry-fuel">
                <div class="telemetry-label">Fuel</div>
                <div class="telemetry-fuel-bar">
                    <div class="telemetry-fuel-fill" style="width: ${driver.fuel}%"></div>
                </div>
                <div class="telemetry-fuel-value">${driver.fuel.toFixed(1)} kg</div>
            </div>
        `;

        this.panel.innerHTML = html;
    }

    /**
     * Render tyre information
     */
    renderTyreInfo(driver) {
        const wearPercentage = Math.min(100, Math.max(0, driver.tyreWear));
        const wearColor = this.getTyreWearColor(wearPercentage);

        return `
            <div class="telemetry-section">
                <div class="telemetry-section-title">Tyre Condition</div>
                <div class="telemetry-tyre-wear">
                    <div class="telemetry-wear-bar">
                        <div class="telemetry-wear-fill" style="width: ${wearPercentage}%; background: ${wearColor}"></div>
                    </div>
                    <div class="telemetry-wear-label">${wearPercentage.toFixed(0)}% wear</div>
                </div>
                <div class="telemetry-pit-count">
                    Pit stops: ${driver.pitStopCount}
                </div>
            </div>
        `;
    }

    /**
     * Render sector times
     */
    renderSectorTimes(driver) {
        const s1 = driver.sector1Time ? this.formatTime(driver.sector1Time) : '--:--';
        const s2 = driver.sector2Time ? this.formatTime(driver.sector2Time) : '--:--';
        const s3 = driver.sector3Time ? this.formatTime(driver.sector3Time) : '--:--';

        return `
            <div class="telemetry-section">
                <div class="telemetry-section-title">Sector Times</div>
                <div class="telemetry-sectors">
                    <div class="telemetry-sector">
                        <div class="telemetry-sector-label">S1</div>
                        <div class="telemetry-sector-time">${s1}</div>
                    </div>
                    <div class="telemetry-sector">
                        <div class="telemetry-sector-label">S2</div>
                        <div class="telemetry-sector-time">${s2}</div>
                    </div>
                    <div class="telemetry-sector">
                        <div class="telemetry-sector-label">S3</div>
                        <div class="telemetry-sector-time">${s3}</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render lap times
     */
    renderLapTimes(driver) {
        const lastLap = driver.lastLapTime ? this.formatTime(driver.lastLapTime) : '--:--';
        const bestLap = driver.bestLapTime !== Infinity ? this.formatTime(driver.bestLapTime) : '--:--';

        return `
            <div class="telemetry-section">
                <div class="telemetry-section-title">Lap Times</div>
                <div class="telemetry-lap-times">
                    <div class="telemetry-lap-time">
                        <div class="telemetry-lap-label">Last</div>
                        <div class="telemetry-lap-value">${lastLap}</div>
                    </div>
                    <div class="telemetry-lap-time">
                        <div class="telemetry-lap-label">Best</div>
                        <div class="telemetry-lap-value telemetry-best">${bestLap}</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Format time in MM:SS.mmm
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toFixed(3).padStart(6, '0')}`;
    }

    /**
     * Get tyre compound CSS class
     */
    getTyreClass(compound) {
        const mapping = {
            'S': 'tyre-soft',
            'M': 'tyre-medium',
            'H': 'tyre-hard',
            'I': 'tyre-intermediate',
            'W': 'tyre-wet',
        };
        return mapping[compound] || 'tyre-medium';
    }

    /**
     * Get tyre wear color
     */
    getTyreWearColor(wear) {
        if (wear < 30) return '#00FF9D';  // Green - good
        if (wear < 60) return '#FFD700';  // Yellow - ok
        if (wear < 85) return '#FF8700';  // Orange - worn
        return '#FF1A1A';  // Red - critical
    }

    /**
     * Clear telemetry
     */
    clear() {
        this.currentDriver = null;
        this.render();
    }

    /**
     * Add static styles
     */
    static injectStyles() {
        if (document.getElementById('telemetry-styles')) return;

        const style = document.createElement('style');
        style.id = 'telemetry-styles';
        style.textContent = `
            .telemetry-empty {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                opacity: 0.5;
            }

            .telemetry-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                padding-bottom: 0.8rem;
                border-bottom: 1px solid var(--border);
            }

            .telemetry-driver {
                font-family: var(--font-display);
                font-size: 14px;
                font-weight: 900;
                letter-spacing: 0.1em;
            }

            .telemetry-position {
                font-size: 20px;
                font-weight: 900;
                color: var(--primary);
                font-family: var(--font-title);
            }

            .telemetry-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.8rem;
                margin-bottom: 1rem;
            }

            .telemetry-card {
                background: var(--bg-dark);
                padding: 0.8rem;
                border-radius: 4px;
                border-left: 2px solid var(--primary);
            }

            .telemetry-label {
                font-size: 9px;
                letter-spacing: 0.1em;
                color: var(--text-secondary);
                text-transform: uppercase;
                font-weight: 700;
                margin-bottom: 0.4rem;
            }

            .telemetry-value {
                font-size: 18px;
                font-weight: 900;
                color: var(--text-primary);
                font-family: var(--font-title);
            }

            .telemetry-unit {
                font-size: 11px;
                color: var(--text-secondary);
                font-weight: 600;
            }

            .telemetry-speed {
                color: var(--primary);
            }

            .telemetry-leader {
                color: var(--secondary);
            }

            .telemetry-section {
                background: var(--bg-dark);
                padding: 1rem;
                border-radius: 4px;
                margin-bottom: 0.8rem;
            }

            .telemetry-section-title {
                font-size: 10px;
                letter-spacing: 0.1em;
                color: var(--primary);
                text-transform: uppercase;
                font-weight: 700;
                margin-bottom: 0.8rem;
            }

            .telemetry-tyre-wear {
                display: flex;
                flex-direction: column;
                gap: 0.4rem;
            }

            .telemetry-wear-bar {
                height: 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                overflow: hidden;
            }

            .telemetry-wear-fill {
                height: 100%;
                transition: width 0.3s ease;
            }

            .telemetry-wear-label {
                font-size: 11px;
                color: var(--text-secondary);
                text-align: right;
            }

            .telemetry-pit-count {
                font-size: 11px;
                color: var(--text-secondary);
                margin-top: 0.4rem;
            }

            .telemetry-sectors {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 0.6rem;
            }

            .telemetry-sector {
                background: rgba(255, 255, 255, 0.03);
                padding: 0.6rem;
                border-radius: 4px;
                text-align: center;
            }

            .telemetry-sector-label {
                font-size: 9px;
                color: var(--text-secondary);
                margin-bottom: 0.3rem;
            }

            .telemetry-sector-time {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: 700;
                color: var(--primary);
            }

            .telemetry-lap-times {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.6rem;
            }

            .telemetry-lap-time {
                background: rgba(255, 255, 255, 0.03);
                padding: 0.6rem;
                border-radius: 4px;
                text-align: center;
            }

            .telemetry-lap-label {
                font-size: 9px;
                color: var(--text-secondary);
                margin-bottom: 0.3rem;
            }

            .telemetry-lap-value {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: 700;
                color: var(--text-primary);
            }

            .telemetry-best {
                color: var(--secondary);
            }

            .telemetry-drs {
                padding: 0.6rem;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                font-weight: 700;
                margin-bottom: 0.8rem;
            }

            .drs-available {
                background: rgba(0, 255, 0, 0.1);
                color: #00FF00;
                border: 1px solid rgba(0, 255, 0, 0.3);
            }

            .drs-active {
                background: rgba(0, 255, 0, 0.2);
                color: #00FF00;
                border: 1px solid #00FF00;
                animation: drs-pulse 1s ease-in-out infinite;
            }

            @keyframes drs-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }

            .telemetry-pit {
                padding: 0.6rem;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                font-weight: 700;
                margin-bottom: 0.8rem;
                background: rgba(255, 170, 0, 0.1);
                color: #FFAA00;
                border: 1px solid rgba(255, 170, 0, 0.3);
            }

            .telemetry-fuel {
                background: var(--bg-dark);
                padding: 0.8rem;
                border-radius: 4px;
            }

            .telemetry-fuel-bar {
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                overflow: hidden;
                margin: 0.4rem 0;
            }

            .telemetry-fuel-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
                transition: width 0.3s ease;
            }

            .telemetry-fuel-value {
                font-size: 10px;
                color: var(--text-secondary);
                text-align: right;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Cleanup
     */
    destroy() {
        this.clear();
    }
}

// Inject styles on load
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => Telemetry.injectStyles());
    } else {
        Telemetry.injectStyles();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Telemetry;
}
