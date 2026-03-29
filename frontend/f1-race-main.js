/**
 * f1-race-main.js  —  F1 Manager Race Client, 2026
 * ===================================================
 * Connects to POST /api/f1/manager/start-race, receives the full lap history
 * from the Python F1ManagerEngine, then replays it lap-by-lap in the browser.
 *
 * Map rendering delegates to TrackRenderer.js (already in the project).
 * The TrackRenderer.renderCar() API needs:
 *   { teamColor, position, drsActive, driverAbbr }
 * and a lapProgress value (0–1 from track_position).
 */

// ============================================================================
// 2026 DRIVER ROSTER  —  matches app/f1_data_2026.py exactly
// ============================================================================

const F1_DRIVERS_2026 = [
    { driver_id:"NOR", name:"Lando Norris",          abbr:"NOR", team:"McLaren",          number:4,  teamColor:"#FF8000" },
    { driver_id:"PIA", name:"Oscar Piastri",         abbr:"PIA", team:"McLaren",          number:81, teamColor:"#FF8000" },
    { driver_id:"VER", name:"Max Verstappen",        abbr:"VER", team:"Red Bull Racing",  number:1,  teamColor:"#3671C6" },
    { driver_id:"HAD", name:"Isack Hadjar",          abbr:"HAD", team:"Red Bull Racing",  number:6,  teamColor:"#3671C6" },
    { driver_id:"RUS", name:"George Russell",        abbr:"RUS", team:"Mercedes",         number:63, teamColor:"#27F4D2" },
    { driver_id:"ANT", name:"Andrea Kimi Antonelli", abbr:"ANT", team:"Mercedes",         number:12, teamColor:"#27F4D2" },
    { driver_id:"HAM", name:"Lewis Hamilton",        abbr:"HAM", team:"Ferrari",          number:44, teamColor:"#E8002D" },
    { driver_id:"LEC", name:"Charles Leclerc",       abbr:"LEC", team:"Ferrari",          number:16, teamColor:"#E8002D" },
    { driver_id:"ALO", name:"Fernando Alonso",       abbr:"ALO", team:"Aston Martin",     number:14, teamColor:"#358C75" },
    { driver_id:"STR", name:"Lance Stroll",          abbr:"STR", team:"Aston Martin",     number:18, teamColor:"#358C75" },
    { driver_id:"GAS", name:"Pierre Gasly",          abbr:"GAS", team:"Alpine",           number:10, teamColor:"#0093CC" },
    { driver_id:"COL", name:"Franco Colapinto",      abbr:"COL", team:"Alpine",           number:43, teamColor:"#0093CC" },
    { driver_id:"ALB", name:"Alexander Albon",       abbr:"ALB", team:"Williams",         number:23, teamColor:"#37BEDD" },
    { driver_id:"SAI", name:"Carlos Sainz Jr.",      abbr:"SAI", team:"Williams",         number:55, teamColor:"#37BEDD" },
    { driver_id:"OCO", name:"Esteban Ocon",          abbr:"OCO", team:"Haas F1 Team",     number:31, teamColor:"#B6BABD" },
    { driver_id:"BEA", name:"Oliver Bearman",        abbr:"BEA", team:"Haas F1 Team",     number:87, teamColor:"#B6BABD" },
    { driver_id:"HUL", name:"Nico Hülkenberg",       abbr:"HUL", team:"Audi",             number:27, teamColor:"#C6C600" },
    { driver_id:"BOR", name:"Gabriel Bortoleto",     abbr:"BOR", team:"Audi",             number:5,  teamColor:"#C6C600" },
    { driver_id:"LAW", name:"Liam Lawson",           abbr:"LAW", team:"Racing Bulls",     number:30, teamColor:"#6692FF" },
    { driver_id:"LIN", name:"Arvid Lindblad",        abbr:"LIN", team:"Racing Bulls",     number:7,  teamColor:"#6692FF" },
    { driver_id:"BOT", name:"Valtteri Bottas",       abbr:"BOT", team:"Cadillac F1 Team", number:77, teamColor:"#FFFFFF" },
    { driver_id:"PER", name:"Sergio Pérez",          abbr:"PER", team:"Cadillac F1 Team", number:11, teamColor:"#FFFFFF" },
];

const DRIVER_MAP = Object.fromEntries(F1_DRIVERS_2026.map(d => [d.driver_id, d]));

// ============================================================================
// RACE STATE
// ============================================================================

const raceState = {
    running:         false,
    lapHistory:      [],
    currentLap:      0,
    totalLaps:       0,
    replayTimer:     null,
    animFrame:       null,
    lapIntervalMs:   78000,
    speedMultiplier: 1,
    circuitName:     '',
    weather:         'dry',
    finalResults:    [],
    selectedDriver:  null,   // kept for compat
    focusDriver:     null,   // driver shown in bottom HUD
    leftDriver:      null,   // driver pinned to left panel
    rightDriver:     null,   // driver pinned to right panel
    trackRenderer:   null,
    currentCircuit:  null,
    overallFastestTime:   Infinity,
    overallFastestDriver: null,
};

// ============================================================================
// DOM READY
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initTrackRenderer();
    initRowClickTelemetry();
    initRightDriverSelector();
    initLiveSpeedButtons();
    console.log('[F1Manager] Ready — 2026 grid:', F1_DRIVERS_2026.length, 'drivers');
});

function initRightDriverSelector() {
    const select = document.getElementById('right-driver-select');
    if (!select) return;

    select.innerHTML = '<option value="">Select driver...</option>' + F1_DRIVERS_2026
        .map(d => `<option value="${d.driver_id}">${d.abbr} · ${d.name}</option>`)
        .join('');

    select.addEventListener('change', () => {
        const id = select.value;
        if (!id) return;
        selectDriver(id);
    });
}

function initLiveSpeedButtons() {
    // Wire the navbar speed buttons — work before, during, and after the race
    document.querySelectorAll('.dash-spd').forEach(btn => {
        btn.addEventListener('click', () => {
            const speed = parseFloat(btn.dataset.speed);
            raceState.speedMultiplier = speed;
            // Update active state across all nav speed buttons
            document.querySelectorAll('.dash-spd').forEach(b => {
                b.classList.toggle('active', parseFloat(b.dataset.speed) === speed);
            });
        });
    });
}

// ============================================================================
// TRACK RENDERER  —  canvas map setup
// ============================================================================

function initTrackRenderer() {
    try {
        raceState.trackRenderer = new TrackRenderer('track-canvas', {
            padding:    10,
            carRadius:  9,
        });
        console.log('[F1Manager] TrackRenderer initialised');
    } catch (e) {
        console.warn('[F1Manager] TrackRenderer init failed:', e.message);
    }
}

/**
 * Load the selected circuit into TrackRenderer and cache the static track image.
 * Called once when a race starts.
 */
function loadTrackIntoRenderer(circuitData) {
    const tr = raceState.trackRenderer;
    if (!tr) return;

    // TrackRenderer.loadCircuit() builds trackPath from circuitData.coordinates
    // and pre-renders the static track image (DRS zones, sectors, corners, S/F line)
    if (circuitData && circuitData.coordinates && circuitData.coordinates.length > 0) {
        tr.loadCircuit(circuitData);
        console.log('[F1Manager] Track loaded into renderer:', circuitData.name,
                    '—', circuitData.coordinates.length, 'waypoints');
    } else {
        // No coordinates: show a generic oval
        tr.loadCircuit({ ...circuitData, coordinates: [] });
        console.warn('[F1Manager] No coordinates for', circuitData?.circuit_id,
                     '— using fallback oval');
    }
}

/**
 * Render all active cars onto the canvas for one lap snapshot.
 * Each driver snapshot has track_position (0–1) from the Python engine.
 *
 * We bypass the old Car.js getDisplayData() pattern and call
 * TrackRenderer.getPositionOnTrack() + renderCar() directly.
 */
function renderMapFrame(lapData) {
    const tr = raceState.trackRenderer;
    if (!tr || !tr.trackPath) return;

    // Draw cached static track background
    tr.drawTrack();

    if (!lapData || !lapData.drivers) return;

    // Render DNF cars first (greyed out, behind active cars visually)
    const dnfDrivers    = lapData.drivers.filter(d => d.dnf);
    const activeDrivers = lapData.drivers.filter(d => !d.dnf);

    // Sort active: leader rendered last = on top
    const sorted = [
        ...dnfDrivers,
        ...[...activeDrivers].sort((a, b) => b.position - a.position),
    ];

    sorted.forEach(d => {
        const info     = DRIVER_MAP[d.driver_id] || {};
        const progress = d.dnf ? (d.track_position || 0) : (d.track_position || 0);

        const xy = tr.getPositionOnTrack(progress);
        if (!xy) return;

        // Build the carData object TrackRenderer.renderCar() expects
        const carData = {
            teamColor:  d.dnf ? '#444444' : (info.teamColor || '#888888'),
            position:   d.position,
            drsActive:  d.drs_active && !d.dnf,
            driverAbbr: info.abbr || d.driver_id,
            status:     d.dnf ? 'dnf' : (d.pit_this_lap ? 'pit' : 'racing'),
        };

        // Skip DNF markers that are off the track (track_position 0)
        if (d.dnf && progress < 0.01) return;

        tr.renderCar(xy.x, xy.y, carData);
    });
}

// ============================================================================
// TABS
// ============================================================================

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${tab}`)?.classList.add('active');
        });
    });
}

// ============================================================================
// START RACE  —  calls backend, then kicks off replay
// ============================================================================

async function startRaceSimulation(circuitData, raceConfig) {
    clearError();
    stopReplay();

    raceState.circuitName   = circuitData.name;
    raceState.weather       = raceConfig.weather || 'dry';
    raceState.speedMultiplier = 1;  // always start at 1×; user changes via navbar
    raceState.currentCircuit= circuitData;

    showStatusBanner('⏳ Simulating race on server…', 'info');

    try {
        const response = await fetch(`${API_URL}/api/f1/manager/start-race`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                circuit_id: circuitData.circuit_id,
                weather:    raceState.weather,
                speed_mult: raceConfig.race_speed_multiplier || 1,
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        raceState.lapHistory   = data.lap_history   || [];
        raceState.finalResults = data.final_results || [];
        raceState.totalLaps    = data.total_laps    || raceState.lapHistory.length;
        raceState.currentLap          = 0;
        raceState.running             = true;
        raceState.overallFastestTime   = Infinity;
        raceState.overallFastestDriver = null;

        const firstLap = data.lap_history?.find(l => Array.isArray(l.drivers) && l.drivers.length > 0);
        const initialLeader = firstLap?.drivers?.find(d => d.position === 1 && !d.dnf) || firstLap?.drivers?.[0] || null;
        raceState.focusDriver = initialLeader?.driver_id || null;
        raceState.rightDriver = raceState.focusDriver;
        if (!raceState.leftDriver) {
            raceState.leftDriver = raceState.focusDriver;
        }

        const rightSelect = document.getElementById('right-driver-select');
        if (rightSelect && raceState.focusDriver) {
            rightSelect.value = raceState.focusDriver;
        }

        const bottomHud = document.getElementById('bottom-driver-hud');
        if (bottomHud) bottomHud.style.display = 'block';
        if (initialLeader) updateBottomHud(initialLeader);
        else resetBottomHud();

        clearStatusBanner();

        // Load track into renderer NOW (before first lap renders)
        loadTrackIntoRenderer(circuitData);

        // Show HUD, reset speed to 1×
        const hudEl = document.getElementById('race-hud');
        if (hudEl) hudEl.style.opacity = '1';
        const stopBtn2 = document.getElementById('stop-race-btn');
        if (stopBtn2) stopBtn2.style.display = 'flex';
        document.querySelectorAll('.dash-spd').forEach(b => {
            b.classList.toggle('active', b.dataset.speed === '1');
        });

        // Show the grip level indicator
        renderGripBar(data.lap_history?.[0]?.grip_level ?? 0.96);

        startReplay();

    } catch (err) {
        console.error('[F1Manager] Race error:', err);
        showError('Race failed: ' + err.message);
        clearStatusBanner();
        throw err;
    }
}

// ============================================================================
// LAP REPLAY LOOP
// ============================================================================
//
// ANIMATION MODEL:
//   The backend pre-computes all lap data (lap_time, gap_to_leader per driver).
//   The frontend replays it in real-time using requestAnimationFrame.
//
//   Each lap, every car drives ONE FULL LAP around the circuit (0.0 → 1.0).
//   Duration = leader_lap_time / speedMultiplier  (real seconds)
//   A car's phase offset on the track = gap_to_leader / leader_lap_time
//   so backmarkers visually lag behind the leader.
//
//   SEQUENCE:
//     1. Formation lap  (cars stagger onto grid, 5s)
//     2. Lights 1-5     (0.8s per light)
//     3. LIGHTS OUT     (green flash, 1.5s)
//     4. Racing laps    (real-time animation, one full lap per interval)
//     5. Results modal

function lapIntervalForSpeed(speed) {
    // Returns ms per lap at the given speed multiplier
    // Will be overridden per-lap by actual lap_time
    return Math.max(500, Math.round(78000 / (speed || 1)));
}

function startReplay() {
    if (raceState.lapHistory.length === 0) return;
    raceState.currentLap = 0;
    replayNextLap();
}

function replayNextLap() {
    if (!raceState.running) return;

    const idx = raceState.currentLap;
    if (idx >= raceState.lapHistory.length) {
        finishRace();
        return;
    }

    const lapData = raceState.lapHistory[idx];
    raceState.currentLap++;

    const phase = lapData.phase || 'racing';

    if (phase === 'formation') {
        _runFormationLap(lapData);
    } else if (phase === 'lights_out') {
        _runLightsStep(lapData);
    } else {
        _runRacingLap(lapData, idx);
    }
}

// ── Formation lap ─────────────────────────────────────────────────────────────
function _runFormationLap(lapData) {
    // Show cars stationary on their grid slots for 5 seconds
    showPhaseBanner('FORMATION LAP', '#aaaaaa');
    renderMapFrame(lapData);
    updatePositionsTable(lapData);
    if (raceState.focusDriver) {
        const snap = lapData.drivers.find(d => d.driver_id === raceState.focusDriver);
        if (snap) updateBottomHud(snap);
    }
    raceState.replayTimer = setTimeout(replayNextLap, 5000);
}

// ── Lights sequence ───────────────────────────────────────────────────────────
function _runLightsStep(lapData) {
    const n = lapData.lights_count;    // 1..5

    renderLightsPanel(n);
    renderMapFrame(lapData);           // cars still on grid

    // Last light (5) — hold an extra beat, then immediately go to LIGHTS OUT
    const holdMs = (n === 5) ? 1200 : 800;
    raceState.replayTimer = setTimeout(replayNextLap, holdMs);
}

// ── Racing lap ────────────────────────────────────────────────────────────────
function _runRacingLap(lapData, historyIdx) {
    // Lap 1 (first racing frame): flash LIGHTS OUT!
    if (lapData.lap === 1) {
        _flashLightsOut();
    } else {
        hidePhaseBanner();
    }

    updateHUD(lapData);
    updatePositionsTable(lapData);
    updateSCBanner(lapData);
    updateFastestLapBanner(lapData);
    renderGripBar(lapData.grip_level);
    // Update both driver panels
    if (raceState.leftDriver) {
        const snap = lapData.drivers.find(d => d.driver_id === raceState.leftDriver);
        if (snap) updateDriverPanel('left', snap);
    }
    if (raceState.rightDriver) {
        const snap = lapData.drivers.find(d => d.driver_id === raceState.rightDriver);
        if (snap) updateDriverPanel('right', snap);
    }
    if (raceState.focusDriver) {
        const snap = lapData.drivers.find(d => d.driver_id === raceState.focusDriver);
        if (snap) updateBottomHud(snap);
    }

    // Duration of this lap animation = leader's actual lap time ÷ speed multiplier
    const leader = lapData.drivers.find(d => d.position === 1 && !d.dnf) || lapData.drivers[0];
    const realLapMs  = (leader?.lap_time || 78) * 1000;
    const lapMs      = realLapMs / (raceState.speedMultiplier || 1);

    // Build the animation: each car drives a full lap, offset by their gap
    _animateRacingLap(lapData, lapMs);

    // Schedule next lap AFTER this animation completes
    raceState.replayTimer = setTimeout(replayNextLap, lapMs);
}

// ── Core animation: all 22 cars circling the track for one lap ────────────────
//
// Cars that are pitting (pit_this_lap=true) are routed through the pit lane:
//   - They enter at t≈0.3 (30% through the lap = approaching pit entry)
//   - They traverse the pit lane path (AUS_PIT_LANE) at slower speed
//   - They STOP at pit box centre (pitLane progress 0.4–0.6) for ~2s real time
//   - They exit and rejoin the race track
//
function _animateRacingLap(lapData, durationMs) {
    if (raceState.animFrame) cancelAnimationFrame(raceState.animFrame);

    const startTime = performance.now();

    const leader    = lapData.drivers.find(d => d.position === 1 && !d.dnf) || lapData.drivers[0];
    const leaderLap = leader?.lap_time || 78;

    // Pit lane timing based on actual Albert Park layout:
    // Pit entry is AFTER T16 hairpin (fraction ~0.84 of lap)
    // Pit exit rejoins just before S/F / T1 (fraction ~0.99)
    // So the entire pit sequence happens in the last 15% of the lap animation
    const PIT_ENTRY_T   = 0.84;   // t when car turns into pit lane (after T16)
    const PIT_STOP_T    = 0.89;   // t when car reaches mid-box and stops
    const PIT_STOP_END  = 0.94;   // t when car leaves pit box
    const PIT_EXIT_T    = 0.99;   // t when car exits and rejoins before T1

    const driverData = lapData.drivers.map(d => {
        const info = DRIVER_MAP[d.driver_id] || {};
        const gapFrac     = d.dnf ? 0 : Math.min(0.99, (d.gap_to_leader || 0) / leaderLap);
        const speedFactor = d.dnf ? 0 : (leaderLap / Math.max(d.lap_time || leaderLap, 60));
        const startPos    = ((0.955 - gapFrac) + 1.0) % 1.0;
        const isPitting   = !d.dnf && d.pit_this_lap;

        return {
            driver_id:  d.driver_id,
            dnf:        d.dnf,
            isPitting,
            position:   d.position,
            teamColor:  d.dnf ? '#444' : (info.teamColor || '#888'),
            driverAbbr: info.abbr || d.driver_id,
            drsActive:  d.drs_active && !d.dnf,
            startPos,
            speedFactor,
            parkedPos:  d.dnf ? ((0.98 - Math.min(0.99, (d.gap_to_leader||0)/leaderLap)) + 1.0) % 1.0 : 0,
        };
    });

    function updateLiveTelemetryFrame(interpDrivers, tNorm) {
        if (!raceState.rightDriver) return;

        const baseSnap = lapData.drivers.find(d => d.driver_id === raceState.rightDriver);
        const liveSnap = interpDrivers.find(d => d.driver_id === raceState.rightDriver);
        if (!baseSnap || !liveSnap) return;

        const live = computeLiveTelemetry(baseSnap, liveSnap, tNorm, leaderLap);
        updateDriverPanel('right', {
            ...baseSnap,
            speed_kmh: live.speedKmh,
            __liveThrottle: live.throttle,
            __liveBrake: live.brake,
            __liveGear: live.gear,
            __liveRpm: live.rpm,
        });
    }

    function frame() {
        if (!raceState.running) return;

        const t = Math.min((performance.now() - startTime) / durationMs, 1.0);

        const interpDrivers = driverData.map(d => {
            if (d.dnf) {
                return { driver_id:d.driver_id, track_position:d.parkedPos,
                         position:d.position, dnf:true, teamColor:d.teamColor,
                         driverAbbr:d.driverAbbr, drs_active:false, inPit:false };
            }

            // ── Pitting car: route through pit lane ──────────────────────────
            if (d.isPitting) {
                let inPit = false;
                let pitLaneProgress = 0;
                let trackProgress = (d.startPos + t * d.speedFactor) % 1.0;

                if (t >= PIT_ENTRY_T && t < PIT_EXIT_T) {
                    inPit = true;

                    if (t < PIT_STOP_T) {
                        // Approaching pit box: 0.0→0.5 of pit lane
                        pitLaneProgress = ((t - PIT_ENTRY_T) / (PIT_STOP_T - PIT_ENTRY_T)) * 0.5;
                    } else if (t < PIT_STOP_END) {
                        // STATIONARY at pit box: holds at 0.5
                        pitLaneProgress = 0.5;
                    } else {
                        // Leaving pit box: 0.5→1.0 of pit lane
                        pitLaneProgress = 0.5 + ((t - PIT_STOP_END) / (PIT_EXIT_T - PIT_STOP_END)) * 0.5;
                    }

                    return { driver_id:d.driver_id, pitLaneProgress, inPit:true,
                             position:d.position, dnf:false, teamColor:d.teamColor,
                             driverAbbr:d.driverAbbr, drs_active:false };
                }

                // Before pit entry or after pit exit: normal track position
                return { driver_id:d.driver_id, track_position:trackProgress, inPit:false,
                         position:d.position, dnf:false, teamColor:d.teamColor,
                         driverAbbr:d.driverAbbr, drs_active:d.drsActive };
            }

            // ── Normal car ───────────────────────────────────────────────────
            const progress = (d.startPos + t * d.speedFactor) % 1.0;
            return { driver_id:d.driver_id, track_position:progress, inPit:false,
                     position:d.position, dnf:false, teamColor:d.teamColor,
                     driverAbbr:d.driverAbbr, drs_active:d.drsActive };
        });

        _renderCarsOnTrack(interpDrivers);
        updateLiveTelemetryFrame(interpDrivers, t);
        if (t < 1.0) raceState.animFrame = requestAnimationFrame(frame);
    }

    raceState.animFrame = requestAnimationFrame(frame);
}

// ── Render cars directly (bypasses renderMapFrame which uses lapData.drivers) ─
function _renderCarsOnTrack(drivers) {
    const tr = raceState.trackRenderer;
    if (!tr || !tr.trackPath) return;

    tr.drawTrack();

    // Render order: DNF → pit cars → P22→P1 (leader on top)
    const dnf     = drivers.filter(d => d.dnf);
    const pitting = drivers.filter(d => d.inPit);
    const active  = drivers.filter(d => !d.dnf && !d.inPit)
                           .sort((a, b) => b.position - a.position);
    const sorted  = [...dnf, ...pitting, ...active];

    sorted.forEach(d => {
        let xy;
        if (d.inPit) {
            // Route through pit lane
            xy = tr.getPitLanePosition(d.pitLaneProgress);
        } else {
            if (d.dnf && (d.track_position < 0.01)) return;
            xy = tr.getPositionOnTrack(d.track_position);
        }
        if (!xy) return;

        tr.renderCar(xy.x, xy.y, {
            teamColor:  d.teamColor,
            position:   d.position,
            drsActive:  d.drs_active,
            driverAbbr: d.driverAbbr,
            inPit:      d.inPit || false,
        });
    });
}

// ── Lights panel UI ───────────────────────────────────────────────────────────
function renderLightsPanel(count) {
    let el = document.getElementById('lights-panel');
    if (!el) {
        el = document.createElement('div');
        el.id        = 'lights-panel';
        el.className = 'lights-panel';
        document.getElementById('map-container')?.appendChild(el);
    }
    el.style.display = 'flex';

    let html = '<div class="lights-row">';
    for (let i = 1; i <= 5; i++) {
        html += `<div class="light-bulb ${i <= count ? 'lit' : ''}"></div>`;
    }
    html += '</div>';
    el.innerHTML = html;
}

function _flashLightsOut() {
    let el = document.getElementById('lights-panel');
    if (!el) {
        el = document.createElement('div');
        el.id        = 'lights-panel';
        el.className = 'lights-panel';
        document.getElementById('map-container')?.appendChild(el);
    }
    el.style.display = 'flex';
    el.innerHTML = '<div class="lights-out-text">LIGHTS OUT!</div>';
    setTimeout(() => {
        if (el) el.style.display = 'none';
        hidePhaseBanner();
    }, 1500);
}

function showPhaseBanner(msg, color) {
    // Hide lights panel
    const lp = document.getElementById('lights-panel');
    if (lp) lp.style.display = 'none';

    let el = document.getElementById('phase-banner');
    if (!el) {
        el = document.createElement('div');
        el.id        = 'phase-banner';
        el.className = 'phase-banner';
        document.getElementById('map-container')?.appendChild(el);
    }
    el.textContent = msg;
    el.style.color = color || '#fff';
    el.style.display = 'block';
}

function hidePhaseBanner() {
    const el = document.getElementById('phase-banner');
    if (el) el.style.display = 'none';
    const ll = document.getElementById('lights-panel');
    if (ll) ll.style.display = 'none';
}

function stopReplay() {
    raceState.running = false;
    if (raceState.replayTimer) { clearTimeout(raceState.replayTimer); raceState.replayTimer = null; }
    if (raceState.animFrame)   { cancelAnimationFrame(raceState.animFrame); raceState.animFrame = null; }
}

// Keep renderMapFrame for static rendering (formation, DNF display)
function renderMapFrame(lapData) {
    const tr = raceState.trackRenderer;
    if (!tr || !tr.trackPath) return;
    tr.drawTrack();
    if (!lapData?.drivers) return;

    const sorted = [
        ...lapData.drivers.filter(d => d.dnf),
        ...[...lapData.drivers.filter(d => !d.dnf)].sort((a, b) => b.position - a.position),
    ];
    sorted.forEach(d => {
        const info  = DRIVER_MAP[d.driver_id] || {};
        const progress = d.track_position || 0;
        if (d.dnf && progress < 0.01) return;
        const xy = tr.getPositionOnTrack(progress);
        if (!xy) return;
        tr.renderCar(xy.x, xy.y, {
            teamColor:  d.dnf ? '#444' : (info.teamColor || '#888'),
            position:   d.position,
            drsActive:  d.drs_active && !d.dnf,
            driverAbbr: info.abbr || d.driver_id,
        });
    });
}

// ============================================================================
// HUD
// ============================================================================

function updateHUD(lapData) {
    const lapEl   = document.getElementById('hud-current-lap');
    const clockEl = document.getElementById('hud-clock-value');
    const leadEl  = document.getElementById('hud-leader-name');
    const gapEl   = document.getElementById('hud-leader-gap');

    if (lapEl) lapEl.textContent = `${lapData.lap}/${raceState.totalLaps}`;

    const leader = lapData.drivers.find(d => d.position === 1 && !d.dnf);
    if (leader && clockEl) {
        const t  = leader.total_race_time || 0;
        const mm = Math.floor(t / 60);
        const ss = Math.floor(t % 60);
        const ms = Math.round((t % 1) * 10);
        clockEl.textContent = `${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}.${ms}`;
    }

    if (leader && leadEl) {
        const info = DRIVER_MAP[leader.driver_id] || {};
        leadEl.textContent = info.abbr || leader.driver_id;
    }

    const p2 = lapData.drivers.find(d => d.position === 2 && !d.dnf);
    if (p2 && gapEl) gapEl.textContent = `+${p2.gap_to_leader.toFixed(2)}s`;
}

// ============================================================================
// GRIP BAR  —  shows track rubber build-up
// ============================================================================

function renderGripBar(gripLevel) {
    const fill = document.getElementById('grip-fill');
    const pct  = document.getElementById('grip-pct');
    const val  = Math.min(100, Math.round((gripLevel || 0.96) * 100));
    if (fill) fill.style.width = val + '%';
    if (pct)  pct.textContent  = val + '%';
}

// ============================================================================
// POSITIONS TABLE
// ============================================================================

function updatePositionsTable(lapData) {
    const tbody = document.getElementById('positions-tbody');
    if (!tbody) return;

    const sorted = [...lapData.drivers].sort((a, b) => {
        if (a.dnf && !b.dnf) return 1;
        if (!a.dnf && b.dnf) return -1;
        return a.position - b.position;
    });

    // Intervals (gap to car ahead)
    const intervals = {};
    for (let i = 0; i < sorted.length; i++) {
        const d = sorted[i];
        if (d.position === 1 || d.dnf) { intervals[d.driver_id] = null; continue; }
        const prev = sorted[i - 1];
        if (!prev || prev.dnf) { intervals[d.driver_id] = null; continue; }
        intervals[d.driver_id] = Math.max(0, (d.gap_to_leader || 0) - (prev.gap_to_leader || 0));
    }

    tbody.innerHTML = sorted.map(d => {
        const info  = DRIVER_MAP[d.driver_id] || {};
        const color = d.dnf ? 'var(--dim,#444)' : (info.teamColor || '#888');

        // Gap column
        let gapHtml;
        if (d.position === 1) {
            gapHtml = `<span class="pos-gap-main" style="color:var(--green,#00e676);font-weight:700">LEADER</span>`;
        } else if (d.dnf) {
            gapHtml = `<span class="pos-gap-main" style="color:var(--red,#f44)">DNF</span>`;
        } else {
            const ivl = intervals[d.driver_id];
            const ivlClass = ivl != null && ivl < 0.5 ? 'drs' : ivl != null && ivl < 1.0 ? 'close' : '';
            gapHtml = `
              <div class="pos-gap-main">+${d.gap_to_leader.toFixed(2)}s</div>
              ${ivl != null ? `<div class="pos-gap-delta ${ivlClass}">&#916;${ivl.toFixed(2)}s</div>` : ''}`;
        }

        const pitBadge = d.pit_this_lap ? `<span class="pit-badge">PIT</span>` : '';
        const drsIcon  = d.drs_active   ? `<span class="drs-icon">DRS</span>`  : '';

        return `
                    <tr data-driver="${d.driver_id}" class="${d.dnf ? 'row-dnf' : ''} ${raceState.focusDriver === d.driver_id ? 'row-focused' : ''}" onclick="selectDriver('${d.driver_id}')">
            <td><span class="pos-num" style="border-left:3px solid ${color}">${d.position}</span></td>
            <td>
              <span class="pos-driver-abbr" style="color:${color}">${info.abbr || d.driver_id}</span>
              <span class="pos-driver-team">${d.team}</span>
              ${pitBadge}${drsIcon}
            </td>
            <td>${gapHtml}</td>
            <td>
              <span class="pos-tyre-dot">${tyreEmoji(d.compound)}</span>
                            <span class="pos-tyre-age">${(tyreFullName(d.compound) || d.compound || 'M').toUpperCase()} ${d.tyre_age}L</span>
            </td>
                        <td><span class="pos-gap-main">${d.dnf ? '—' : Math.round(d.speed_kmh || 0)}</span></td>
          </tr>`;
    }).join('');
}

// ============================================================================
// TELEMETRY PANEL  —  now includes sector times
// ============================================================================

function initRowClickTelemetry() {
    document.getElementById('positions-tbody')?.addEventListener('click', e => {
        const row = e.target.closest('tr[data-driver]');
        if (!row) return;
        selectDriver(row.dataset.driver);
    });
}

function selectDriver(driverId) {
    raceState.selectedDriver = driverId;
    raceState.focusDriver = driverId;
    raceState.rightDriver = driverId;

    const rightSelect = document.getElementById('right-driver-select');
    if (rightSelect && rightSelect.value !== driverId) {
        rightSelect.value = driverId;
    }

    // Alternate: fill left first, then right; clicking same driver deselects
    if (!raceState.leftDriver) {
        raceState.leftDriver = driverId;
    }

    // Highlight rows
    document.querySelectorAll('#positions-tbody tr').forEach(r => {
        const id = r.dataset.driver;
        r.classList.toggle('row-selected', id === raceState.leftDriver || id === raceState.rightDriver);
        r.classList.toggle('row-focused', id === raceState.focusDriver);
    });

    // Render immediately
    if (raceState.lapHistory.length > 0) {
        const lapData = raceState.lapHistory[Math.max(0, raceState.currentLap - 1)];
        if (lapData) {
            if (raceState.leftDriver) {
                const snap = lapData.drivers.find(d => d.driver_id === raceState.leftDriver);
                if (snap) updateDriverPanel('left', snap);
            }
            if (raceState.rightDriver) {
                const snap = lapData.drivers.find(d => d.driver_id === raceState.rightDriver);
                if (snap) updateDriverPanel('right', snap);
            }
            const focusSnap = lapData.drivers.find(d => d.driver_id === raceState.focusDriver);
            if (focusSnap) updateBottomHud(focusSnap);
        }
    }
}

function estimateGearFromSpeed(speedKmh) {
    const s = Math.max(0, Math.round(speedKmh || 0));
    if (s === 0) return 'N';
    if (s < 45) return '1';
    if (s < 78) return '2';
    if (s < 110) return '3';
    if (s < 145) return '4';
    if (s < 182) return '5';
    if (s < 225) return '6';
    if (s < 275) return '7';
    return '8';
}

function estimateRpm(speedKmh, gear) {
    if (gear === 'N') return 0;
    const maxByGear = { 1: 62, 2: 95, 3: 128, 4: 170, 5: 220, 6: 265, 7: 300, 8: 340 };
    const g = Number(gear) || 8;
    const ratio = Math.max(0.2, Math.min(1, (speedKmh || 0) / (maxByGear[g] || 340)));
    return Math.round(3500 + ratio * 9500);
}

function getTrackDrivingDemand(progress) {
    const tr = raceState.trackRenderer;
    const pts = tr?.trackPath;
    if (!pts || pts.length < 8) {
        return { cornerDemand: 0.25, straightBias: 0.55 };
    }

    const n = pts.length;
    const idx = ((Math.floor((progress || 0) * n) % n) + n) % n;
    const current = pts[idx];

    let upcomingCorners = 0;
    for (let i = 2; i <= 12; i++) {
        const look = pts[(idx + i) % n];
        if (look?.corner && look.corner > 0) upcomingCorners += 1;
    }

    const cornerNow = current?.corner && current.corner > 0 ? 1 : 0;
    const cornerDemand = Math.max(0, Math.min(1, cornerNow * 0.7 + upcomingCorners * 0.08));
    const straightBias = 1 - cornerDemand;
    return { cornerDemand, straightBias };
}

function computeLiveTelemetry(baseSnap, interpSnap, tNorm, leaderLapSecs) {
    if (baseSnap?.dnf) {
        return { speedKmh: 0, throttle: 0, brake: 0, gear: 'N', rpm: 0 };
    }

    if (interpSnap?.inPit) {
        const pitSpeed = 78;
        return { speedKmh: pitSpeed, throttle: 16, brake: 72, gear: '2', rpm: estimateRpm(pitSpeed, '2') };
    }

    const lapLen = raceState.currentCircuit?.lap_length_km || 5.2;
    const lapTime = Math.max(60, baseSnap?.lap_time || leaderLapSecs || 78);
    const avgSpeed = (lapLen / (lapTime / 3600));
    const demand = getTrackDrivingDemand(interpSnap?.track_position || 0);

    const wave = Math.sin(((interpSnap?.track_position || 0) * Math.PI * 10) + tNorm * 3.7) * 5;
    const drsBoost = baseSnap?.drs_active ? 12 : 0;

    const speedFactor = 0.72 + demand.straightBias * 0.48;
    let speed = avgSpeed * speedFactor + drsBoost + wave;
    speed = Math.max(55, Math.min(338, speed));

    let throttle = Math.round(36 + demand.straightBias * 62 + (baseSnap?.drs_active ? 6 : 0));
    let brake = Math.round(8 + demand.cornerDemand * 74);

    if (baseSnap?.pit_this_lap && (interpSnap?.track_position || 0) > 0.8) {
        throttle = Math.max(8, throttle - 35);
        brake = Math.min(100, brake + 22);
    }

    throttle = Math.max(0, Math.min(100, throttle));
    brake = Math.max(0, Math.min(100, brake));

    const gear = estimateGearFromSpeed(speed);
    const rpm = estimateRpm(speed, gear);
    return { speedKmh: Math.round(speed), throttle, brake, gear, rpm };
}

function derivePedals(driverSnap, speedKmh) {
    if (driverSnap?.dnf) return { throttle: 0, brake: 0 };
    if (driverSnap?.pit_this_lap) return { throttle: 14, brake: 78 };

    const wear = driverSnap?.tyre_wear_pct || 0;
    const speedNorm = Math.max(0, Math.min(1, (speedKmh || 0) / 340));

    let throttle = Math.round(18 + speedNorm * 82 - Math.min(18, wear * 0.12));
    let brake = Math.round((1 - speedNorm) * 42 + (driverSnap?.drs_active ? 0 : 6));
    if ((speedKmh || 0) > 285 && !driverSnap?.pit_this_lap) brake = Math.max(0, brake - 8);

    throttle = Math.max(0, Math.min(100, throttle));
    brake = Math.max(0, Math.min(100, brake));
    return { throttle, brake };
}

function resetBottomHud(hide = false) {
    const root = document.getElementById('bottom-driver-hud');
    if (!root) return;

    if (hide) {
        root.style.display = 'none';
        return;
    }
    root.style.display = 'block';

    const text = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    const width = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.style.width = `${val}%`;
    };

    text('hud-driver-name', 'SELECT A DRIVER');
    text('hud-driver-meta', 'Click any driver in LIVE order');
    text('hud-driver-pos', 'P—');
    text('hud-driver-gap', 'GAP —');
    text('hud-driver-tyre', 'TYRE —');
    text('hud-speed', '0');
    text('hud-gear', 'N');
    text('hud-rpm', '0 RPM');
    text('hud-brake-pct', '0%');
    text('hud-throttle-pct', '0%');
    width('hud-brake', 0);
    width('hud-throttle', 0);
    const gauge = document.getElementById('hud-gauge');
    if (gauge) gauge.style.setProperty('--gauge-pct', '0');
}

function updateBottomHud(driverSnap) {
    if (!driverSnap) {
        resetBottomHud();
        return;
    }

    const root = document.getElementById('bottom-driver-hud');
    if (!root) return;
    root.style.display = 'block';

    const info = DRIVER_MAP[driverSnap.driver_id] || {};
    const speed = Math.max(0, Math.round(driverSnap.speed_kmh || 0));
    const gear = estimateGearFromSpeed(speed);
    const rpm = estimateRpm(speed, gear);
    const pedals = derivePedals(driverSnap, speed);

    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };
    const setWidth = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.style.width = `${Math.max(0, Math.min(100, value))}%`;
    };

    setText('hud-driver-name', (info.name || driverSnap.driver_id || 'UNKNOWN').toUpperCase());
    setText('hud-driver-meta', `${driverSnap.team || info.team || 'TEAM'}  ·  L${driverSnap.lap || raceState.currentLap || 0}`);
    setText('hud-driver-pos', driverSnap.dnf ? 'DNF' : `P${driverSnap.position || '—'}`);
    setText('hud-driver-gap', driverSnap.position === 1 ? 'GAP LEADER' : `GAP +${(driverSnap.gap_to_leader || 0).toFixed(2)}s`);
    setText('hud-driver-tyre', `TYRE ${(tyreFullName(driverSnap.compound) || driverSnap.compound || 'M').toUpperCase()} · ${driverSnap.tyre_age || 0}L`);

    setText('hud-speed', String(speed));
    setText('hud-gear', gear);
    setText('hud-rpm', `${rpm.toLocaleString()} RPM`);

    setWidth('hud-brake', pedals.brake);
    setWidth('hud-throttle', pedals.throttle);
    setText('hud-brake-pct', `${pedals.brake}%`);
    setText('hud-throttle-pct', `${pedals.throttle}%`);

    const gauge = document.getElementById('hud-gauge');
    if (gauge) {
        const gaugePct = Math.max(0, Math.min(100, (speed / 340) * 100));
        gauge.style.setProperty('--gauge-pct', gaugePct.toFixed(1));
    }
}

function clearDriverPanel(side) {
    const prompt = document.getElementById(`${side}-prompt`);
    if (prompt) prompt.style.display = 'block';
    // Reset all values to dash
    const ids = ['driver-name','driver-num','position','gap','cur-lap','best-lap',
                 'speed','gear','rpm','s1','s2','s3','pit-count','pit-laps','compounds',
                 'tyre-name','tyre-age','tyre-laps','wear-pct'];
    ids.forEach(id => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.textContent = '—';
    });
    ['wear','brake','throttle'].forEach(id => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.style.width = '0%';
    });
    ['drs','pit-badge','dnf'].forEach(id => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.style.display = 'none';
    });
    const tb = document.getElementById(`${side}-team-banner`);
    if (tb) { tb.textContent = 'SELECT DRIVER'; tb.style.color = ''; }
}

function renderTelemetry(d) {
    // Legacy: update whichever panel matches, or left if none
    if (raceState.leftDriver === d.driver_id)  { updateDriverPanel('left',  d); return; }
    if (raceState.rightDriver === d.driver_id) { updateDriverPanel('right', d); return; }
    // No panel pinned to this driver - do nothing
}

function updateDriverPanel(side, d) {
    const info  = DRIVER_MAP[d.driver_id] || {};
    const color = info.teamColor || '#888';

    const set = (id, val) => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.textContent = val;
    };
    const setStyle = (id, prop, val) => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.style[prop] = val;
    };
    const show = (id, visible) => {
        const el = document.getElementById(`${side}-${id}`);
        if (el) el.style.display = visible ? '' : 'none';
    };

    // Hide prompt
    show('prompt', false);

    // Team banner
    const tb = document.getElementById(`${side}-team-banner`);
    if (tb) { tb.textContent = d.team; tb.style.color = color; }

    // Name + number + position
    set('driver-name', info.name || d.driver_name || d.driver_id);
    set('driver-num', '#' + (info.number || d.number || '?'));
    set('position', d.dnf ? 'DNF' : d.position || '—');

    // Gap
    const gapTxt = d.position === 1 ? 'LEADER' : (d.gap_to_leader != null ? '+' + d.gap_to_leader.toFixed(3) + 's' : '—');
    set('gap', gapTxt);
    setStyle('gap', 'color', d.position === 1 ? 'var(--green)' : 'var(--cyan)');

    // Position colour
    setStyle('position', 'color', d.position === 1 ? 'var(--yellow)' : color);

    // Lap times
    set('cur-lap',  d.lap_time  ? formatLapTime(d.lap_time)      : '—');
    set('best-lap', d.best_lap_time ? formatLapTime(d.best_lap_time) : '—');

    // Speed
    const spd = d.speed_kmh ? Math.round(d.speed_kmh) : 0;
    set('speed', spd || '—');
    const liveGear = d.__liveGear || estimateGearFromSpeed(spd);
    const liveRpm = d.__liveRpm || estimateRpm(spd, liveGear);
    set('gear', `GEAR ${liveGear}`);
    set('rpm', `RPM ${Math.round(liveRpm).toLocaleString()}`);

    // Simulated throttle/brake from speed (no direct data, use wear/speed proxy)
    const wearPct = d.tyre_wear_pct || 0;
    const normSpd = Math.min(100, Math.max(0, (spd / 320) * 100));
    const throttlePct = d.__liveThrottle ?? (d.pit_this_lap ? 0 : normSpd);
    const brakePct    = d.__liveBrake ?? (d.pit_this_lap ? 80 : Math.max(0, 40 - normSpd * 0.35));
    setStyle('brake',    'width', brakePct.toFixed(0) + '%');
    setStyle('throttle', 'width', throttlePct.toFixed(0) + '%');

    // Tyre
    const cmpMap = {S:'SOFT',M:'MEDIUM',H:'HARD',I:'INTER',W:'WET'};
    const emojiMap = {S:'🔴',M:'🟡',H:'⚪',I:'🟢',W:'🔵'};
    const wearColor = wearPct > 80 ? 'var(--red)' : wearPct > 55 ? 'var(--orange)' : 'var(--green)';
    set('tyre-icon', emojiMap[d.compound] || '🟡');
    set('tyre-name', cmpMap[d.compound] || d.compound || '—');
    set('tyre-age', (d.tyre_age || 0) + ' laps');
    set('tyre-laps', d.tyre_age || '—');
    set('wear-pct', (wearPct || 0).toFixed(0) + '%');
    setStyle('wear-pct', 'color', wearColor);
    setStyle('wear', 'width', (wearPct || 0) + '%');
    setStyle('wear', 'background', wearColor);

    // Sectors
    set('s1', d.sector1 ? d.sector1.toFixed(3) + 's' : '—');
    set('s2', d.sector2 ? d.sector2.toFixed(3) + 's' : '—');
    set('s3', d.sector3 ? d.sector3.toFixed(3) + 's' : '—');

    // Pit info
    set('pit-count', d.pit_count || 0);
    const pitLaps = d.pit_laps || [];
    set('pit-laps', pitLaps.length ? pitLaps.map(l => 'L'+l).join(', ') : '—');
    const cpUsed = (d.compounds_used || [d.compound]).filter((v,i,a) => a.indexOf(v) === i);
    set('compounds', cpUsed.join(' + ') || '—');

    // DRS / pit / DNF badges
    show('drs',       d.drs_active   && !d.dnf);
    show('pit-badge', d.pit_this_lap && !d.dnf);
    show('dnf',       d.dnf);
}


// ============================================================================
// SC / VSC / FL BANNERS
// ============================================================================

function updateSCBanner(lapData) {
    let el = document.getElementById('sc-banner');
    if (!el) {
        el = document.createElement('div');
        el.id = 'sc-banner';
        el.className = 'sc-banner';
        document.querySelector('.f1-main')?.prepend(el);
    }
    const flag = lapData.flag || (lapData.sc_active ? 'sc' : lapData.vsc_active ? 'vsc' : 'green');
    switch (flag) {
        case 'red':
            el.textContent   = '🚩  RED FLAG — RACE STOPPED';
            el.style.display = 'block';
            el.style.background = 'rgba(200,0,0,0.25)';
            el.style.color   = '#FF4444';
            el.style.borderColor = '#FF0000';
            break;
        case 'sc':
            el.textContent   = '🚗  SAFETY CAR DEPLOYED';
            el.style.display = 'block';
            el.style.background = 'rgba(40,30,0,0.5)';
            el.style.color   = '#FFD700';
            el.style.borderColor = '#FFD700';
            break;
        case 'vsc':
            el.textContent   = '⚠️  VIRTUAL SAFETY CAR';
            el.style.display = 'block';
            el.style.background = 'rgba(40,25,0,0.5)';
            el.style.color   = '#FFA500';
            el.style.borderColor = '#FFA500';
            break;
        case 'yellow':
            el.textContent   = '⚑  YELLOW FLAG';
            el.style.display = 'block';
            el.style.background = 'rgba(40,35,0,0.5)';
            el.style.color   = '#FFD700';
            el.style.borderColor = '#FFD700';
            break;
        default:
            el.style.display = 'none';
    }
}

function updateFastestLapBanner(lapData) {
    if (!lapData.fastest_lap_driver || !lapData.fastest_lap_time) return;
    // Only show toast when a new OVERALL fastest lap is set
    if (lapData.fastest_lap_time >= raceState.overallFastestTime) return;

    raceState.overallFastestTime   = lapData.fastest_lap_time;
    raceState.overallFastestDriver = lapData.fastest_lap_driver;

    const toast = document.getElementById('fl-toast');
    const textEl = document.getElementById('fl-toast-text');
    if (!toast || !textEl) return;

    const info = DRIVER_MAP[lapData.fastest_lap_driver] || {};
    const color = info.teamColor || '#c080ff';
    textEl.innerHTML = `<span style="color:${color};font-weight:900">${info.abbr || lapData.fastest_lap_driver}</span>`
        + `  —  FASTEST LAP  —  `
        + `<span style="color:#c080ff">${formatLapTime(lapData.fastest_lap_time)}</span>`;

    toast.style.display = 'flex';
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { toast.style.display = 'none'; }, 4000);
}

// ============================================================================
// RACE FINISH
// ============================================================================

function finishRace() {
    raceState.running = false;
    const hudEl2 = document.getElementById('race-hud'); if (hudEl2) hudEl2.style.opacity = '0';
    showResultsModal(raceState.finalResults);
    document.getElementById('start-race-btn').style.display = 'flex';
    document.getElementById('stop-race-btn').style.display  = 'none';
    document.querySelectorAll('select,.weather-btn').forEach(el => el.disabled = false);
}

function showResultsModal(results) {
    document.getElementById('results-modal')?.remove();

    const top10 = results.slice(0, 10);
    const dnfs  = results.filter(r => r.dnf);

    const mkRow = (r, isDnf) => {
        const info  = DRIVER_MAP[r.driver_id] || {};
        const color = info.teamColor || '#888';
        const gap   = isDnf ? `DNF L${r.dnf_lap}` : (r.gap != null ? `+${r.gap.toFixed(3)}s` : 'WINNER');
        const fl    = r.fastest_lap ? ' ⚡' : '';
        return `<tr>
          <td style="color:${isDnf?'#f44':color};font-weight:700">${isDnf?'DNF':'P'+r.position}</td>
          <td style="color:${color}">${info.abbr||r.driver_id}${fl}</td>
          <td style="color:#aaa;font-size:.8em">${r.team}</td>
          <td>${gap}</td>
          <td style="color:#FFD700">${r.points} pts</td>
          <td style="color:#aaa;font-size:.8em">${r.pit_count} pit${r.pit_count!==1?'s':''}</td>
        </tr>`;
    };

    const modal = document.createElement('div');
    modal.id = 'results-modal';
    modal.innerHTML = `
      <div class="modal-backdrop" onclick="document.getElementById('results-modal').remove()"></div>
      <div class="modal-box">
        <div class="modal-title">🏁 ${raceState.circuitName} — RACE RESULTS</div>
        <div class="modal-weather">Weather: ${raceState.weather.toUpperCase()} &nbsp;|&nbsp; Laps: ${raceState.totalLaps}</div>
        <table class="results-table">
          <thead><tr><th>Pos</th><th>Driver</th><th>Team</th><th>Gap</th><th>Pts</th><th>Pits</th></tr></thead>
          <tbody>
            ${top10.map(r => mkRow(r, false)).join('')}
            ${dnfs.map(r  => mkRow(r, true)).join('')}
          </tbody>
        </table>
        <button class="modal-close-btn"
                onclick="document.getElementById('results-modal').remove()">CLOSE</button>
      </div>`;
    document.body.appendChild(modal);
}

// ============================================================================
// STOP
// ============================================================================

function stopRaceSimulation() {
    stopReplay();
    const hudEl2 = document.getElementById('race-hud'); if (hudEl2) hudEl2.style.opacity = '0';
    raceState.focusDriver = null;
    raceState.rightDriver = null;
    raceState.leftDriver = null;

    const rightSelect = document.getElementById('right-driver-select');
    if (rightSelect) rightSelect.value = '';

    clearDriverPanel('right');
    resetBottomHud(true);

    // Redraw empty track (keeps the circuit outline visible)
    const tr = raceState.trackRenderer;
    if (tr) tr.drawTrack();

    document.getElementById('positions-tbody').innerHTML =
        '<tr><td colspan="5" style="text-align:center;padding:20px;color:#888;">Race stopped</td></tr>';
    const panel = document.getElementById('telemetry-panel');
    if (panel) {
        panel.innerHTML = '<div style="text-align:center;color:#888;padding:12px;">No race data</div>';
    }
    const scEl = document.getElementById('sc-banner');
    if (scEl) scEl.style.display = 'none';
}

// ============================================================================
// STATUS / ERROR HELPERS
// ============================================================================

function showStatusBanner(msg, type = 'info') {
    let el = document.getElementById('status-banner');
    if (!el) {
        el = document.createElement('div');
        el.id = 'status-banner';
        el.className = 'status-banner';
        document.querySelector('.f1-race-container')?.prepend(el);
    }
    el.textContent   = msg;
    el.style.display = 'block';
    el.style.color   = type === 'error' ? '#f44' : '#00FF9D';
}
function clearStatusBanner() {
    const el = document.getElementById('status-banner');
    if (el) el.style.display = 'none';
}
function showError(msg) {
    const el = document.getElementById('race-error');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}
function clearError() {
    const el = document.getElementById('race-error');
    if (el) el.style.display = 'none';
}

// ============================================================================
// FORMATTERS
// ============================================================================

function formatLapTime(secs) {
    const m  = Math.floor(secs / 60);
    const s  = Math.floor(secs % 60);
    const ms = Math.round((secs % 1) * 1000);
    return `${m}:${String(s).padStart(2,'0')}.${String(ms).padStart(3,'0')}`;
}
function formatSector(secs) {
    return secs.toFixed(3) + 's';
}
function tyreEmoji(c)    { return {S:'🔴',M:'🟡',H:'⚪',I:'🟢',W:'🔵'}[c]||'⚪'; }
function tyreFullName(c) { return {S:'Soft',M:'Medium',H:'Hard',I:'Inter',W:'Wet'}[c]||c; }

// ============================================================================
// PUBLIC API  (consumed by f1-race-config.js)
// ============================================================================

window.raceSimulationAPI = {
    start:    startRaceSimulation,
    stop:     stopRaceSimulation,
    setSpeed: speed => { raceState.speedMultiplier = speed; },
};
