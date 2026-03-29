/**
 * F1 Race HUD Enhanced - Broadcast-Style Graphics
 * Provides real-time race overlays similar to F1 TV broadcasts
 */

class F1RaceHUD {
    constructor(config = {}) {
        this.config = {
            updateInterval: 100, // ms
            animationDuration: 300,
            ...config
        };

        this.raceData = null;
        this.elements = {};
        this.animationTimers = {};

        this.initializeHUD();
    }

    /**
     * Initialize HUD elements
     */
    initializeHUD() {
        // Create main HUD container if it doesn't exist
        let hudContainer = document.getElementById('broadcast-hud');
        if (!hudContainer) {
            hudContainer = document.createElement('div');
            hudContainer.id = 'broadcast-hud';
            hudContainer.className = 'broadcast-hud';
            document.querySelector('.map-container').appendChild(hudContainer);
        }

        this.elements.container = hudContainer;
        this.createHUDElements();
    }

    /**
     * Create individual HUD elements
     */
    createHUDElements() {
        // Race Info Bar (Top)
        this.elements.raceInfoBar = this.createElement('div', 'race-info-bar', this.elements.container);
        
        // Circuit name and flag
        this.elements.circuitInfo = this.createElement('div', 'circuit-info', this.elements.raceInfoBar);
        
        // Lap counter
        this.elements.lapCounter = this.createElement('div', 'lap-counter', this.elements.raceInfoBar);
        
        // Race clock
        this.elements.raceClock = this.createElement('div', 'race-clock', this.elements.raceInfoBar);
        
        // Weather indicator
        this.elements.weatherIndicator = this.createElement('div', 'weather-indicator', this.elements.raceInfoBar);

        // Leader Board (Left side - compact)
        this.elements.leaderBoard = this.createElement('div', 'hud-leaderboard', this.elements.container);
        
        // Track Sectors Display (Bottom)
        this.elements.sectorDisplay = this.createElement('div', 'sector-display', this.elements.container);

        // Interval Tower (Right side - showing gaps)
        this.elements.intervalTower = this.createElement('div', 'interval-tower', this.elements.container);
    }

    /**
     * Helper to create element
     */
    createElement(tag, className, parent) {
        const el = document.createElement(tag);
        el.className = className;
        if (parent) parent.appendChild(el);
        return el;
    }

    /**
     * Update race info bar
     */
    updateRaceInfo(circuitName, currentLap, totalLaps, raceTime, weather) {
        // Circuit name
        this.elements.circuitInfo.innerHTML = `
            <div class="circuit-flag">🏁</div>
            <div class="circuit-name">${circuitName}</div>
        `;

        // Lap counter
        this.elements.lapCounter.innerHTML = `
            <div class="lap-label">LAP</div>
            <div class="lap-value">${currentLap}/${totalLaps}</div>
        `;

        // Race clock
        this.elements.raceClock.innerHTML = `
            <div class="clock-label">TIME</div>
            <div class="clock-value">${this.formatTime(raceTime)}</div>
        `;

        // Weather
        const weatherIcons = {
            dry: '☀️',
            damp: '🌤️',
            wet: '🌧️',
            rain: '⛈️'
        };
        this.elements.weatherIndicator.innerHTML = `
            <div class="weather-icon">${weatherIcons[weather] || '☀️'}</div>
            <div class="weather-label">${weather.toUpperCase()}</div>
        `;
    }

    /**
     * Update leader board with top positions
     */
    updateLeaderBoard(positions, showCount = 5) {
        const topPositions = positions.slice(0, showCount);
        
        let html = '<div class="leaderboard-title">LIVE POSITIONS</div>';
        html += '<div class="leaderboard-items">';
        
        topPositions.forEach((driver, index) => {
            const posClass = index === 0 ? 'pos-leader' : '';
            const statusIcon = this.getStatusIcon(driver.status);
            
            html += `
                <div class="leaderboard-item ${posClass}" data-position="${driver.position}">
                    <div class="lb-position">${driver.position}</div>
                    <div class="lb-team-color" style="background-color: ${driver.teamColor}"></div>
                    <div class="lb-driver">
                        <div class="lb-driver-abbr">${driver.driverAbbr}</div>
                        <div class="lb-driver-name">${driver.driverName}</div>
                    </div>
                    <div class="lb-gap">${driver.gap || 'LEADER'}</div>
                    <div class="lb-status">${statusIcon}</div>
                </div>
            `;
        });
        
        html += '</div>';
        this.elements.leaderBoard.innerHTML = html;
    }

    /**
     * Update interval tower (timing gaps)
     */
    updateIntervalTower(positions) {
        let html = '<div class="tower-title">INTERVALS</div>';
        html += '<div class="tower-items">';
        
        positions.forEach(driver => {
            const isLeader = driver.position === 1;
            const gap = isLeader ? 'LEADER' : driver.gapToAhead || '+0.0';
            
            html += `
                <div class="tower-item" data-position="${driver.position}">
                    <div class="tower-pos">${driver.position}</div>
                    <div class="tower-abbr" style="border-left: 3px solid ${driver.teamColor}">
                        ${driver.driverAbbr}
                    </div>
                    <div class="tower-interval">${gap}</div>
                </div>
            `;
        });
        
        html += '</div>';
        this.elements.intervalTower.innerHTML = html;
    }

    /**
     * Update sector display
     */
    updateSectorDisplay(sectorData) {
        if (!sectorData || sectorData.length === 0) {
            this.elements.sectorDisplay.innerHTML = '';
            return;
        }

        let html = '<div class="sector-title">SECTOR TIMES</div>';
        html += '<div class="sector-items">';
        
        sectorData.forEach(sector => {
            const sectorClass = sector.isFastest ? 'sector-fastest' : sector.isPersonalBest ? 'sector-pb' : '';
            
            html += `
                <div class="sector-item ${sectorClass}">
                    <div class="sector-number">S${sector.number}</div>
                    <div class="sector-driver">${sector.driverAbbr}</div>
                    <div class="sector-time">${sector.time}</div>
                </div>
            `;
        });
        
        html += '</div>';
        this.elements.sectorDisplay.innerHTML = html;
    }

    /**
     * Show position change animation
     */
    animatePositionChange(driver, oldPosition, newPosition) {
        const direction = newPosition < oldPosition ? 'up' : 'down';
        const change = Math.abs(newPosition - oldPosition);
        
        // Create animated overlay
        const overlay = document.createElement('div');
        overlay.className = `position-change-overlay ${direction}`;
        overlay.innerHTML = `
            <div class="pc-driver">${driver.driverAbbr}</div>
            <div class="pc-arrow">${direction === 'up' ? '↑' : '↓'}</div>
            <div class="pc-positions">${change}</div>
        `;
        
        this.elements.container.appendChild(overlay);
        
        setTimeout(() => {
            overlay.classList.add('fade-out');
            setTimeout(() => overlay.remove(), 300);
        }, 2000);
    }

    /**
     * Show DRS indicator
     */
    showDRSIndicator(driverAbbr, isActive) {
        const existingIndicator = document.querySelector(`[data-drs="${driverAbbr}"]`);
        
        if (isActive && !existingIndicator) {
            const indicator = document.createElement('div');
            indicator.className = 'drs-indicator active';
            indicator.setAttribute('data-drs', driverAbbr);
            indicator.innerHTML = `
                <div class="drs-driver">${driverAbbr}</div>
                <div class="drs-label">DRS</div>
            `;
            this.elements.container.appendChild(indicator);
        } else if (!isActive && existingIndicator) {
            existingIndicator.remove();
        }
    }

    /**
     * Show pit stop graphic
     */
    showPitStopGraphic(driver, duration) {
        const graphic = document.createElement('div');
        graphic.className = 'pitstop-graphic';
        graphic.innerHTML = `
            <div class="ps-icon">🔧</div>
            <div class="ps-driver">${driver.driverAbbr}</div>
            <div class="ps-label">IN PITS</div>
            <div class="ps-duration">${duration.toFixed(1)}s</div>
        `;
        
        this.elements.container.appendChild(graphic);
        
        setTimeout(() => {
            graphic.classList.add('fade-out');
            setTimeout(() => graphic.remove(), 500);
        }, 3000);
    }

    /**
     * Show fastest lap graphic
     */
    showFastestLapGraphic(driver, lapTime) {
        const graphic = document.createElement('div');
        graphic.className = 'fastest-lap-graphic';
        graphic.innerHTML = `
            <div class="fl-icon">⚡</div>
            <div class="fl-driver">${driver.driverName}</div>
            <div class="fl-label">FASTEST LAP</div>
            <div class="fl-time">${lapTime}</div>
        `;
        
        this.elements.container.appendChild(graphic);
        
        setTimeout(() => {
            graphic.classList.add('fade-out');
            setTimeout(() => graphic.remove(), 500);
        }, 4000);
    }

    /**
     * Get status icon
     */
    getStatusIcon(status) {
        const icons = {
            racing: '🏎️',
            pit: '🔧',
            dnf: '❌',
            finished: '🏁'
        };
        return icons[status] || '';
    }

    /**
     * Format time (seconds to MM:SS.mmm)
     */
    formatTime(seconds) {
        if (!seconds || seconds < 0) return '00:00.000';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }

    /**
     * Show/hide HUD
     */
    show() {
        this.elements.container.style.display = 'block';
    }

    hide() {
        this.elements.container.style.display = 'none';
    }

    /**
     * Cleanup
     */
    destroy() {
        Object.values(this.animationTimers).forEach(timer => clearTimeout(timer));
        if (this.elements.container) {
            this.elements.container.remove();
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = F1RaceHUD;
}
