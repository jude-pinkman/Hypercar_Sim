/**
 * F1 Race WebSocket Client
 * Connects to live race events and updates the UI in real-time
 */

let wsState = {
    connected: false,
    raceTime: 0,
    leaderDriver: '',
    circuitName: '',
};

const PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

// Get WebSocket host from API_URL or use current location
function getWebSocketHost() {
    if (typeof API_URL !== 'undefined' && API_URL) {
        // Extract host and port from API_URL (e.g., "http://127.0.0.1:8080" -> "127.0.0.1:8080")
        try {
            const url = new URL(API_URL);
            return url.host;
        } catch (e) {
            console.warn('Failed to parse API_URL:', API_URL);
        }
    }
    // Fallback to current location
    return window.location.host;
}

// ============================================================================
// WEBSOCKET CONNECTION
// ============================================================================

async function connectToRaceWebSocket(raceId) {
    const wsHost = getWebSocketHost();
    const wsUrl = `${PROTOCOL}//${wsHost}/api/f1/race/${raceId}/live`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            wsState.connected = true;
            window.raceWebSocket = ws;
            
            // Initialize map
            setTimeout(() => {
                if (window.trackMapAPI) {
                    window.trackMapAPI.init();
                }
            }, 100);
            
            resolve();
        };
        
        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleRaceEvent(message);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            wsState.connected = false;
            reject(error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket closed');
            wsState.connected = false;
        };
    });
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function handleRaceEvent(event) {
    const { event_type, timestamp, data } = event;
    
    console.log(`Race event: ${event_type}`, data);
    
    switch (event_type) {
        case 'race_started':
            handleRaceStarted(data, timestamp);
            break;
        
        case 'lap_completed':
            handleLapCompleted(data, timestamp);
            break;
        
        case 'position_change':
            handlePositionChange(data, timestamp);
            break;
        
        case 'pit_stop_enter':
            handlePitEnter(data, timestamp);
            break;
        
        case 'pit_stop_exit':
            handlePitExit(data, timestamp);
            break;
        
        case 'weather_change':
            handleWeatherChange(data, timestamp);
            break;
        
        case 'race_finished':
            handleRaceFinished(data, timestamp);
            break;
        
        default:
            console.log('Unknown event type:', event_type);
    }
}

function handleRaceStarted(data, timestamp) {
    console.log('Race started!', data);
    
    wsState.circuitName = data.circuit;
    wsState.totalLaps = data.total_laps;
    
    // Update position table header
    if (window.positionsAPI) {
        window.positionsAPI.setLapInfo(0, data.total_laps);
    }
    
    // Show starting grid positions
    const standings = data.grid_positions.map(pos => ({
        position: pos.position,
        driver: pos.driver,
        team: pos.team,
        gap_to_leader: 0,
        speed_kmh: 0,
        tyre_compound: 'M',
        status: 'grid',
    }));
    
    if (window.positionsAPI) {
        window.positionsAPI.updateTable(standings);
    }
}

function handleLapCompleted(data, timestamp) {
    console.log(`${data.driver} completed lap ${data.lap}: ${data.lap_time.toFixed(3)}s`);
    
    wsState.raceTime = timestamp;
    updateHUD();
    
    // Update telemetry
    if (window.positionsAPI) {
        window.positionsAPI.updateLapTime(data.driver, data.lap, data.lap_time);
    }
}

function handlePositionChange(data, timestamp) {
    console.log(`${data.driver}: ${data.old_position} → ${data.new_position}`);
    
    // Trigger visual feedback (could add animation)
    const rowElement = document.querySelector(`tr[data-driver="${data.driver}"]`);
    if (rowElement) {
        if (data.new_position < data.old_position) {
            rowElement.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
        } else {
            rowElement.style.backgroundColor = 'rgba(255, 26, 26, 0.1)';
        }
        
        setTimeout(() => {
            rowElement.style.backgroundColor = '';
        }, 2000);
    }
}

function handlePitEnter(data, timestamp) {
    console.log(`${data.driver} entering pit lane`);
    
    const rowElement = document.querySelector(`tr[data-driver="${data.driver}"]`);
    if (rowElement) {
        rowElement.classList.add('pit-stop');
    }
}

function handlePitExit(data, timestamp) {
    console.log(`${data.driver} exiting pit lane - Tyre: ${data.tyre_to}`);
    
    const rowElement = document.querySelector(`tr[data-driver="${data.driver}"]`);
    if (rowElement) {
        rowElement.classList.remove('pit-stop');
    }
}

function handleWeatherChange(data, timestamp) {
    console.log(`Weather changed to ${data.condition} (grip: ${data.grip_level})`);
    
    // Could update weather display here
}

function handleRaceFinished(data, timestamp) {
    console.log('Race finished!', data);
    
    // Display final results
    showRaceResults(data.results);
    
    // Reconnect to standings endpoint instead of WebSocket
    wsState.connected = false;
}

// ============================================================================
// LIVE STANDINGS UPDATES
// ============================================================================

async function pollRaceStandings(raceId, interval = 1000) {
    const poll = async () => {
        if (!wsState.connected) return;
        
        try {
            const response = await fetch(`${API_URL}/api/f1/race/${raceId}/standings`);
            if (!response.ok) throw new Error('Failed to fetch standings');
            
            const raceData = await response.json();
            
            // Update positions table
            const standings = raceData.positions.map(pos => ({
                position: pos.position,
                driver: pos.driver,
                team: pos.team,
                gap_to_leader: pos.gap_to_leader,
                speed_kmh: pos.speed_kmh,
                tyre_compound: 'M', // Would come from telemetry
                status: pos.status || 'racing',
            }));
            
            if (window.positionsAPI) {
                window.positionsAPI.updateTable(standings);
                
                // Update leader
                if (standings.length > 0) {
                    wsState.leaderDriver = standings[0].driver;
                    if (window.trackMapAPI) {
                        window.trackMapAPI.setLeader(standings[0].driver);
                    }
                }
            }
            
            // Continue polling
            setTimeout(poll, interval);
        } catch (error) {
            console.error('Error polling standings:', error);
            setTimeout(poll, interval * 2);
        }
    };
    
    poll();
}

// ============================================================================
// HUD UPDATES
// ============================================================================

function updateHUD() {
    // Update race clock
    const minutes = Math.floor(wsState.raceTime / 60);
    const seconds = (wsState.raceTime % 60).toFixed(0);
    
    const clockEl = document.getElementById('hud-clock-value');
    if (clockEl) {
        clockEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    // Update leader
    const leaderEl = document.getElementById('hud-leader-name');
    if (leaderEl) {
        leaderEl.textContent = wsState.leaderDriver || '---';
    }
}

// ============================================================================
// RACE RESULTS
// ============================================================================

function showRaceResults(results) {
    console.log('Final results:', results);
    
    // Could display a modal or separate view
    // For now, just log
    
    alert(`🏁 Race Finished!\n\n` +
          `1st: ${results[0]?.driver || 'Unknown'}\n` +
          `2nd: ${results[1]?.driver || 'Unknown'}\n` +
          `3rd: ${results[2]?.driver || 'Unknown'}`);
}

// ============================================================================
// EXPORT FOR EXTERNAL USE
// ============================================================================

window.raceWebSocketAPI = {
    connect: connectToRaceWebSocket,
    pollStandings: pollRaceStandings,
};
