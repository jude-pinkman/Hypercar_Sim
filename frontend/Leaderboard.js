/**
 * Leaderboard.js - Real-time Race Standings Display
 * Manages the positions table with live updates, animations, and highlighting
 */

class Leaderboard {
    constructor(tableId, config = {}) {
        this.tbody = document.getElementById(tableId);
        if (!this.tbody) {
            throw new Error(`Table body with id "${tableId}" not found`);
        }

        // Configuration
        this.config = {
            highlightDuration: config.highlightDuration || 2000,
            updateThrottle: config.updateThrottle || 100,  // ms
            showTeam: config.showTeam !== false,
            showSpeed: config.showSpeed || false,
            ...config
        };

        // State
        this.positions = [];
        this.previousPositions = new Map();
        this.lastUpdateTime = 0;
        this.currentLap = 0;
        this.totalLaps = 0;

        // Animation timeouts
        this.highlightTimeouts = new Map();
    }

    /**
     * Update leaderboard with new data
     */
    update(data) {
        // Throttle updates
        const now = performance.now();
        if (now - this.lastUpdateTime < this.config.updateThrottle) {
            return;
        }
        this.lastUpdateTime = now;

        // Store lap info
        this.currentLap = data.currentLap || 0;
        this.totalLaps = data.totalLaps || 0;

        // Store positions
        this.positions = data.positions || [];

        // Render table
        this.render();
    }

    /**
     * Render the leaderboard table
     */
    render() {
        // Clear table
        this.tbody.innerHTML = '';

        // Render each position
        this.positions.forEach((car, index) => {
            const row = this.createRow(car, index + 1);
            this.tbody.appendChild(row);

            // Store for comparison
            this.previousPositions.set(car.driverId, car.position);
        });
    }

    /**
     * Create a table row for a car
     */
    createRow(car, position) {
        const tr = document.createElement('tr');
        tr.setAttribute('data-driver', car.driverId);

        // Detect position change
        const previousPos = this.previousPositions.get(car.driverId);
        if (previousPos !== undefined && previousPos !== position) {
            const gained = position < previousPos;
            tr.classList.add(gained ? 'position-gained' : 'position-lost');

            // Clear highlight after delay
            this.clearHighlightAfterDelay(car.driverId, tr);
        }

        // Add pit stop indicator
        if (car.isInPit) {
            tr.classList.add('in-pit');
        }

        // Add status class
        tr.classList.add(`status-${car.status}`);

        // Build row content
        tr.innerHTML = this.buildRowContent(car, position);

        return tr;
    }

    /**
     * Build row HTML content
     */
    buildRowContent(car, position) {
        const gap = this.formatGap(car.gapToLeader, car.currentLap);
        const tyreClass = this.getTyreClass(car.tyreCompound);
        const tyreWearIndicator = this.getTyreWearIndicator(car.tyreWear);

        let content = `
            <td class="pos-cell">
                <div class="position-number">${position}</div>
            </td>
            <td class="driver-cell">
                <div class="driver-info">
                    <div class="driver-name" style="color: ${car.teamColor}">
                        ${car.driverAbbr}
                        ${car.drsActive ? '<span class="drs-indicator">DRS</span>' : ''}
                    </div>
        `;

        if (this.config.showTeam) {
            content += `<div class="driver-team">${car.team}</div>`;
        }

        content += `
                </div>
            </td>
            <td class="gap-cell">
                <div class="gap-value">${gap}</div>
        `;

        if (this.config.showSpeed) {
            content += `<div class="speed-value">${car.speedKmh.toFixed(0)} km/h</div>`;
        }

        content += `
            </td>
            <td class="tyre-cell">
                <div class="tyre-info">
                    <span class="tyre-compound ${tyreClass}">${car.tyreCompound}</span>
                    <span class="tyre-wear">${tyreWearIndicator}</span>
                </div>
            </td>
        `;

        return content;
    }

    /**
     * Format gap to leader
     */
    formatGap(gap, currentLap) {
        if (gap < 0.01) {
            return '<span class="gap-leader">Leader</span>';
        }

        if (gap < 1) {
            // Less than 1 second
            return `<span class="gap-close">${gap.toFixed(2)}s</span>`;
        }

        if (gap < 10) {
            // 1-10 seconds
            return `<span class="gap-normal">${gap.toFixed(1)}s</span>`;
        }

        if (gap < 60) {
            // 10-60 seconds
            return `<span class="gap-far">${gap.toFixed(1)}s</span>`;
        }

        // More than a minute (lapped)
        const laps = Math.floor(currentLap / 10);
        return `<span class="gap-lapped">+${laps} lap${laps !== 1 ? 's' : ''}</span>`;
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
     * Get tyre wear indicator
     */
    getTyreWearIndicator(wear) {
        if (wear < 20) return '●●●●●';  // Fresh
        if (wear < 40) return '●●●●○';  // Good
        if (wear < 60) return '●●●○○';  // Used
        if (wear < 80) return '●●○○○';  // Worn
        return '●○○○○';  // Critical
    }

    /**
     * Clear highlight after delay
     */
    clearHighlightAfterDelay(driverId, row) {
        // Clear existing timeout
        if (this.highlightTimeouts.has(driverId)) {
            clearTimeout(this.highlightTimeouts.get(driverId));
        }

        // Set new timeout
        const timeout = setTimeout(() => {
            row.classList.remove('position-gained', 'position-lost');
            this.highlightTimeouts.delete(driverId);
        }, this.config.highlightDuration);

        this.highlightTimeouts.set(driverId, timeout);
    }

    /**
     * Highlight a specific driver
     */
    highlightDriver(driverId) {
        // Remove previous highlights
        this.tbody.querySelectorAll('tr').forEach(row => {
            row.classList.remove('highlighted');
        });

        // Add highlight to selected driver
        const row = this.tbody.querySelector(`tr[data-driver="${driverId}"]`);
        if (row) {
            row.classList.add('highlighted');
        }
    }

    /**
     * Clear all highlights
     */
    clearHighlights() {
        this.tbody.querySelectorAll('tr').forEach(row => {
            row.classList.remove('highlighted');
        });
    }

    /**
     * Set lap information
     */
    setLapInfo(currentLap, totalLaps) {
        this.currentLap = currentLap;
        this.totalLaps = totalLaps;
    }

    /**
     * Add click listeners to rows
     */
    addRowClickListener(callback) {
        this.tbody.addEventListener('click', (e) => {
            const row = e.target.closest('tr[data-driver]');
            if (row) {
                const driverId = row.getAttribute('data-driver');
                callback(driverId);
            }
        });
    }

    /**
     * Add additional CSS for styling
     */
    static injectStyles() {
        if (document.getElementById('leaderboard-styles')) return;

        const style = document.createElement('style');
        style.id = 'leaderboard-styles';
        style.textContent = `
            .pos-cell {
                text-align: center;
                font-weight: 900;
                font-family: var(--font-display);
            }

            .position-number {
                font-size: 14px;
                color: var(--primary);
            }

            .driver-cell {
                padding: 0.5rem !important;
            }

            .driver-info {
                display: flex;
                flex-direction: column;
                gap: 0.2rem;
            }

            .driver-name {
                font-weight: 700;
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .driver-team {
                font-size: 10px;
                color: var(--text-secondary);
            }

            .drs-indicator {
                background: #00FF00;
                color: #000;
                padding: 2px 4px;
                border-radius: 2px;
                font-size: 8px;
                font-weight: 900;
                letter-spacing: 0.05em;
            }

            .gap-cell {
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }

            .gap-leader {
                color: var(--primary);
                font-weight: 700;
            }

            .gap-close {
                color: #FFD700;
                font-weight: 700;
            }

            .gap-normal {
                color: var(--text-primary);
            }

            .gap-far {
                color: var(--text-secondary);
            }

            .gap-lapped {
                color: #FF6666;
                font-style: italic;
            }

            .speed-value {
                font-size: 10px;
                color: var(--text-secondary);
                margin-top: 0.2rem;
            }

            .tyre-cell {
                text-align: center;
            }

            .tyre-info {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.2rem;
            }

            .tyre-compound {
                font-weight: 900;
                font-size: 13px;
                letter-spacing: 0.1em;
            }

            .tyre-wear {
                font-size: 10px;
                letter-spacing: 0.1em;
            }

            .in-pit {
                background: rgba(255, 170, 0, 0.1) !important;
                border-left: 3px solid #FFAA00 !important;
            }

            .status-dnf {
                opacity: 0.4;
            }

            .status-finished {
                opacity: 0.7;
            }

            .highlighted {
                background: rgba(0, 255, 157, 0.15) !important;
                border-left: 3px solid var(--primary) !important;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Cleanup
     */
    destroy() {
        // Clear all timeouts
        this.highlightTimeouts.forEach(timeout => clearTimeout(timeout));
        this.highlightTimeouts.clear();

        // Clear table
        this.tbody.innerHTML = '';
    }
}

// Inject styles on load
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => Leaderboard.injectStyles());
    } else {
        Leaderboard.injectStyles();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Leaderboard;
}
