// Predictions Page JavaScript
// Handles circuit selection, race simulation, and results display

// Get API base URL from config
const API_BASE_URL = window.CONFIG?.API_BASE_URL || 'http://localhost:8080';

// State
let selectedCircuit = null;
let raceResults = null;

// DOM Elements
const circuitsGrid = document.getElementById('circuitsGrid');
const simulateBtn = document.getElementById('simulateBtn');
const simulationStatus = document.getElementById('simulationStatus');
const resultsSection = document.getElementById('resultsSection');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCircuits();
    setupEventListeners();
});

// Load available circuits
async function loadCircuits() {
    console.log('Loading circuits from:', `${API_BASE_URL}/api/circuits/list`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/circuits/list`);
        console.log('Circuits response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Circuits data:', data);
        
        if (data.circuits && data.circuits.length > 0) {
            displayCircuits(data.circuits);
        } else {
            showError('No circuits available');
        }
    } catch (error) {
        console.error('Error loading circuits:', error);
        showError(`Failed to load circuits: ${error.message}`);
    }
}

// Display circuits as cards
function displayCircuits(circuits) {
    circuitsGrid.innerHTML = '';
    
    circuits.forEach(circuit => {
        const card = createCircuitCard(circuit);
        circuitsGrid.appendChild(card);
    });
}

// Create a circuit card element
function createCircuitCard(circuit) {
    const card = document.createElement('div');
    card.className = 'circuit-card';
    card.dataset.circuitKey = circuit.key;
    
    // Determine difficulty class
    const difficultyClass = `difficulty-${circuit.difficulty.toLowerCase()}`;
    
    card.innerHTML = `
        <div class="circuit-card-content">
            <h3 class="circuit-name">${circuit.name}</h3>
            <p class="circuit-location">📍 ${circuit.location}</p>
            <p class="circuit-description">${circuit.description}</p>
            <div class="circuit-stats">
                <div class="circuit-stat">
                    <div class="stat-value-circuit">${circuit.lap_length_km}</div>
                    <div class="stat-label-circuit">Lap Length (km)</div>
                </div>
                <div class="circuit-stat">
                    <div class="stat-value-circuit">${circuit.difficulty}</div>
                    <div class="stat-label-circuit">Difficulty</div>
                </div>
            </div>
            <div class="difficulty-badge ${difficultyClass}">
                ${circuit.difficulty.toUpperCase()}
            </div>
        </div>
    `;
    
    // Click handler
    card.addEventListener('click', () => selectCircuit(circuit.key, card));
    
    return card;
}

// Select a circuit
function selectCircuit(circuitKey, cardElement) {
    // Remove previous selection
    document.querySelectorAll('.circuit-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection to clicked card
    cardElement.classList.add('selected');
    selectedCircuit = circuitKey;
    
    // Enable simulate button
    simulateBtn.disabled = false;
    
    // Hide previous results
    resultsSection.style.display = 'none';
}

// Setup event listeners
function setupEventListeners() {
    simulateBtn.addEventListener('click', runSimulation);
}

// Run race simulation
async function runSimulation() {
    if (!selectedCircuit) {
        alert('Please select a circuit first');
        return;
    }
    
    console.log('Starting simulation for circuit:', selectedCircuit);
    
    // Update UI
    simulateBtn.disabled = true;
    simulationStatus.textContent = '🏎️ Running race simulation...';
    simulationStatus.className = 'simulation-status running';
    resultsSection.style.display = 'none';
    
    const url = `${API_BASE_URL}/api/predict/race?circuit_name=${selectedCircuit}`;
    console.log('Simulation URL:', url);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Simulation response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Simulation error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Simulation data received:', data);
        raceResults = data;
        
        // Display results
        displayResults(data);
        
        // Update status
        simulationStatus.textContent = '✅ Simulation complete!';
        simulationStatus.className = 'simulation-status';
        
        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
        
    } catch (error) {
        console.error('Simulation error:', error);
        simulationStatus.textContent = `❌ Simulation failed: ${error.message}`;
        simulationStatus.className = 'simulation-status';
        alert(`Simulation failed: ${error.message}\n\nCheck the browser console for more details.`);
    } finally {
        simulateBtn.disabled = false;
    }
}

// Display race results
function displayResults(data) {
    // Show results section
    resultsSection.style.display = 'block';
    
    // Display winner
    displayWinner(data.winner);
    
    // Display top 10
    displayTop10(data.top_10);
    
    // Setup lap times selector
    setupLapTimesSelector(data.top_10, data.lap_times);
    
    // Display pit stops
    displayPitStops(data.pit_stops);
    
    // Display statistics
    displayStatistics(data);
}

// Display race winner
function displayWinner(winner) {
    if (!winner) return;
    
    document.getElementById('winnerName').textContent = winner.driver;
    document.getElementById('winnerTeam').textContent = winner.team;
    document.getElementById('winnerTime').textContent = formatTime(winner.finish_time);
}

// Display top 10 finishers
function displayTop10(top10) {
    const tbody = document.querySelector('#top10Table tbody');
    tbody.innerHTML = '';
    
    if (!top10 || top10.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No results available</td></tr>';
        return;
    }
    
    const winnerTime = top10[0].finish_time;
    
    top10.forEach((result, index) => {
        const row = document.createElement('tr');
        const gap = index === 0 ? '-' : `+${(result.finish_time - winnerTime).toFixed(3)}s`;
        
        row.innerHTML = `
            <td class="position-cell position-${result.position}">${result.position}</td>
            <td class="driver-cell">${result.driver}</td>
            <td class="team-cell">${result.team}</td>
            <td class="time-cell">${formatTime(result.finish_time)}</td>
            <td class="gap-cell">${gap}</td>
            <td class="time-cell">${formatTime(result.fastest_lap)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Setup lap times selector
function setupLapTimesSelector(top10, lapTimes) {
    const select = document.getElementById('driverSelect');
    select.innerHTML = '<option value="">Choose a driver...</option>';
    
    top10.forEach(result => {
        const option = document.createElement('option');
        option.value = result.driver;
        option.textContent = `${result.driver} (${result.team})`;
        select.appendChild(option);
    });
    
    select.addEventListener('change', (e) => {
        const driverName = e.target.value;
        if (driverName && lapTimes[driverName]) {
            displayLapTimes(driverName, lapTimes[driverName]);
        } else {
            document.getElementById('lapTimesChart').innerHTML = 
                '<p class="no-data">No lap time data available for this driver</p>';
        }
    });
}

// Display lap times for a driver
function displayLapTimes(driverName, times) {
    const container = document.getElementById('lapTimesChart');
    
    if (!times || times.length === 0) {
        container.innerHTML = '<p class="no-data">No lap time data available</p>';
        return;
    }
    
    container.innerHTML = '';
    const bestLap = Math.min(...times);
    
    times.forEach((time, index) => {
        const item = document.createElement('div');
        item.className = 'lap-time-item';
        
        const delta = time - bestLap;
        const deltaText = delta === 0 ? 'Best lap 🔥' : `+${delta.toFixed(3)}s`;
        
        item.innerHTML = `
            <span class="lap-number">Lap ${index + 1}</span>
            <span class="lap-time">${formatTime(time)}</span>
            <span class="lap-delta">${deltaText}</span>
        `;
        
        container.appendChild(item);
    });
}

// Display pit stops
function displayPitStops(pitStops) {
    const tbody = document.querySelector('#pitstopsTable tbody');
    tbody.innerHTML = '';
    
    if (!pitStops || pitStops.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No pit stops recorded</td></tr>';
        return;
    }
    
    pitStops.forEach(stop => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="driver-cell">${stop.driver}</td>
            <td>${stop.lap}</td>
            <td class="time-cell">${formatTime(stop.race_time)}</td>
            <td class="time-cell">${stop.service_time.toFixed(2)}s</td>
            <td class="compound-change">${stop.compound_change}</td>
        `;
        tbody.appendChild(row);
    });
}

// Display statistics
function displayStatistics(data) {
    document.getElementById('totalLaps').textContent = data.total_laps || '-';
    
    const raceDistance = data.total_laps * data.circuit_length_km;
    document.getElementById('raceDistance').textContent = `${raceDistance.toFixed(1)} km`;
    
    // Find fastest lap
    let fastestLap = Infinity;
    if (data.top_10) {
        data.top_10.forEach(result => {
            if (result.fastest_lap < fastestLap) {
                fastestLap = result.fastest_lap;
            }
        });
    }
    document.getElementById('fastestLap').textContent = 
        fastestLap !== Infinity ? formatTime(fastestLap) : '-';
    
    document.getElementById('totalPitStops').textContent = 
        data.pit_stops ? data.pit_stops.length : '0';
}

// Format time in seconds to readable format
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '-';
    
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    
    if (mins > 0) {
        return `${mins}:${secs.padStart(6, '0')}`;
    }
    return `${secs}s`;
}

// Show error message
function showError(message) {
    circuitsGrid.innerHTML = `
        <div class="circuit-loading">
            <p style="color: var(--accent);">⚠️ ${message}</p>
        </div>
    `;
}
