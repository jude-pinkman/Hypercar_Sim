/**
 * F1 Race Positions Table
 * Manages live race standings display with real-time updates
 */

let positionsState = {
    drivers: {},
    currentLap: 0,
    totalLaps: 0,
};

// ============================================================================
// POSITIONS TABLE UPDATE
// ============================================================================

function updatePositionsTable(standings) {
    const tbody = document.getElementById('positions-tbody');
    if (!tbody) return;
    
    const rows = [];
    
    standings.forEach((entry, idx) => {
        rows.push({
            position: entry.position || idx + 1,
            driver: entry.driver,
            team: entry.team,
            gap: entry.gap_to_leader || 0,
            speed: entry.speed_kmh || 0,
            tyre: entry.tyre_compound || 'M',
            fuel: entry.fuel || 100,
            status: entry.status || 'racing',
        });
    });
    
    // Store for comparison
    const previousDrivers = { ...positionsState.drivers };
    
    // Clear table
    tbody.innerHTML = '';
    
    // Insert rows
    rows.forEach((row) => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-driver', row.driver);
        
        // Detect position change
        const wasPosition = previousDrivers[row.driver]?.position;
        const positionChanged = wasPosition && wasPosition !== row.position;
        const positionGained = wasPosition && row.position < wasPosition;
        
        if (positionChanged) {
            tr.classList.add(positionGained ? 'position-gained' : 'position-lost');
        }
        
        // Build row HTML
        const tyreClass = getTyreClass(row.tyre);
        const statusIcon = getStatusIcon(row.status);
        
        tr.innerHTML = `
            <td>${row.position}</td>
            <td>
                <div class="position-driver">${row.driver}</div>
                <div style="font-size:0.75rem;color:#666;">${row.team}</div>
            </td>
            <td>
                <div>${formatGap(row.gap)}</div>
            </td>
            <td>
                <div class="tyre-compound ${tyreClass}">
                    ${row.tyre}
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
        
        // Store for next update
        positionsState.drivers[row.driver] = row;
    });
}

function formatGap(gap) {
    if (gap < 0.01) return 'Leader';
    if (gap < 1) return gap.toFixed(2) + 's';
    if (gap < 100) return gap.toFixed(1) + ' laps';
    return 'DNF';
}

function getTyreClass(tyre) {
    const mapping = {
        'S': 'tyre-soft',
        'Soft': 'tyre-soft',
        'M': 'tyre-medium',
        'Medium': 'tyre-medium',
        'H': 'tyre-hard',
        'Hard': 'tyre-hard',
        'W': 'tyre-wet',
        'Wet': 'tyre-wet',
        'IN': 'tyre-wet',
        'Intermediate': 'tyre-wet',
    };
    return mapping[tyre] || 'tyre-medium';
}

function getStatusIcon(status) {
    const icons = {
        'racing': '🏎️',
        'pit': '🔧',
        'dnf': '❌',
        'finished': '🏁',
    };
    return icons[status] || '';
}

// ============================================================================
// LIVE LAP TIME UPDATES
// ============================================================================

function updateLapTime(driver, lap, lapTime) {
    const row = document.querySelector(`tr[data-driver="${driver}"]`);
    if (!row) return;
    
    // Could add lap time display here
    // For now, just store it
    if (!positionsState.drivers[driver]) {
        positionsState.drivers[driver] = {};
    }
    positionsState.drivers[driver].lastLapTime = lapTime;
}

// ============================================================================
// TELEMETRY PANEL UPDATE
// ============================================================================

function updateTelemetry(driver, data) {
    const panel = document.getElementById('telemetry-panel');
    if (!panel) return;
    
    panel.innerHTML = `
        <div class="telemetry-item">
            <span class="telemetry-label">Driver:</span>
            <span class="telemetry-value">${driver}</span>
        </div>
        <div class="telemetry-item">
            <span class="telemetry-label">Speed:</span>
            <span class="telemetry-value">${(data.speed_kmh || 0).toFixed(1)} km/h</span>
        </div>
        <div class="telemetry-item">
            <span class="telemetry-label">Lap:</span>
            <span class="telemetry-value">${data.lap || 0} / ${positionsState.totalLaps}</span>
        </div>
        <div class="telemetry-item">
            <span class="telemetry-label">Tyre:</span>
            <span class="telemetry-value">${data.tyre || 'M'}</span>
        </div>
        <div class="telemetry-item">
            <span class="telemetry-label">Fuel:</span>
            <span class="telemetry-value">${(data.fuel || 100).toFixed(1)}L</span>
        </div>
    `;
    
    // Highlight driver row
    document.querySelectorAll('tr[data-driver]').forEach(row => {
        row.classList.remove('telemetry-active');
    });
    const driverRow = document.querySelector(`tr[data-driver="${driver}"]`);
    if (driverRow) driverRow.classList.add('telemetry-active');
}

// ============================================================================
// EXPORT FOR EXTERNAL USE
// ============================================================================

window.positionsAPI = {
    updateTable: updatePositionsTable,
    updateLapTime: updateLapTime,
    updateTelemetry: updateTelemetry,
    setLapInfo: (lap, total) => {
        positionsState.currentLap = lap;
        positionsState.totalLaps = total;
    },
};
