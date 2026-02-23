// ==========================================
// CIRCUITS.JS – F1-Style Lap Simulation
// Lights-out sequence, live telemetry animation,
// braking zone analysis table
// ==========================================

import { initMap, loadTrack } from './trackLoader.js';
import { simulateMonacoLap, formatLapTime } from './lapSimulator.js';

// ==========================================
// VEHICLE SPECS LOOKUP
// Keyed by vehicle_id as returned by /api/vehicles
// ==========================================
const VEHICLE_SPECS = {
    koenigsegg_jesko:          { power_kw:1195, weight_kg:1420, drag_coefficient:0.278, top_speed_kmh:531, cornering_grip:1.30, downforce_factor:1.05, transmission_efficiency:0.94 },
    koenigsegg_jesko_attack:   { power_kw:1195, weight_kg:1420, drag_coefficient:0.315, top_speed_kmh:480, cornering_grip:1.45, downforce_factor:1.25, transmission_efficiency:0.94 },
    koenigsegg_regera:         { power_kw:1100, weight_kg:1590, drag_coefficient:0.278, top_speed_kmh:410, cornering_grip:1.22, downforce_factor:1.00, transmission_efficiency:0.95 },
    koenigsegg_agera_rs:       { power_kw:1014, weight_kg:1395, drag_coefficient:0.330, top_speed_kmh:447, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.94 },
    bugatti_chiron_ss:         { power_kw:1177, weight_kg:1978, drag_coefficient:0.350, top_speed_kmh:490, cornering_grip:1.10, downforce_factor:0.90, transmission_efficiency:0.93 },
    bugatti_bolide:            { power_kw:1361, weight_kg:1240, drag_coefficient:0.670, top_speed_kmh:500, cornering_grip:1.50, downforce_factor:1.40, transmission_efficiency:0.93 },
    bugatti_veyron_ss:         { power_kw: 882, weight_kg:1888, drag_coefficient:0.360, top_speed_kmh:431, cornering_grip:1.08, downforce_factor:0.88, transmission_efficiency:0.92 },
    hennessey_venom_f5:        { power_kw:1355, weight_kg:1360, drag_coefficient:0.330, top_speed_kmh:484, cornering_grip:1.18, downforce_factor:0.95, transmission_efficiency:0.93 },
    ssc_tuatara:               { power_kw:1305, weight_kg:1247, drag_coefficient:0.279, top_speed_kmh:455, cornering_grip:1.15, downforce_factor:0.92, transmission_efficiency:0.93 },
    pagani_huayra_r:           { power_kw: 620, weight_kg:1050, drag_coefficient:0.300, top_speed_kmh:370, cornering_grip:1.55, downforce_factor:1.35, transmission_efficiency:0.94 },
    pagani_zonda_r:            { power_kw: 559, weight_kg:1070, drag_coefficient:0.360, top_speed_kmh:350, cornering_grip:1.48, downforce_factor:1.30, transmission_efficiency:0.94 },
    mclaren_speedtail:         { power_kw: 782, weight_kg:1430, drag_coefficient:0.278, top_speed_kmh:403, cornering_grip:1.18, downforce_factor:0.95, transmission_efficiency:0.93 },
    mclaren_p1:                { power_kw: 673, weight_kg:1450, drag_coefficient:0.340, top_speed_kmh:350, cornering_grip:1.42, downforce_factor:1.20, transmission_efficiency:0.93 },
    mclaren_senna:             { power_kw: 588, weight_kg:1198, drag_coefficient:0.820, top_speed_kmh:340, cornering_grip:1.60, downforce_factor:1.45, transmission_efficiency:0.93 },
    mclaren_765lt:             { power_kw: 563, weight_kg:1229, drag_coefficient:0.350, top_speed_kmh:330, cornering_grip:1.40, downforce_factor:1.18, transmission_efficiency:0.93 },
    mclaren_720s:              { power_kw: 530, weight_kg:1283, drag_coefficient:0.320, top_speed_kmh:341, cornering_grip:1.32, downforce_factor:1.10, transmission_efficiency:0.93 },
    aston_valkyrie:            { power_kw: 865, weight_kg:1030, drag_coefficient:0.650, top_speed_kmh:402, cornering_grip:1.65, downforce_factor:1.50, transmission_efficiency:0.94 },
    rimac_nevera:              { power_kw:1408, weight_kg:2150, drag_coefficient:0.300, top_speed_kmh:412, cornering_grip:1.25, downforce_factor:1.05, transmission_efficiency:0.97 },
    lotus_evija:               { power_kw:1470, weight_kg:1680, drag_coefficient:0.380, top_speed_kmh:320, cornering_grip:1.28, downforce_factor:1.08, transmission_efficiency:0.97 },
    aspark_owl:                { power_kw:1480, weight_kg:1900, drag_coefficient:0.320, top_speed_kmh:400, cornering_grip:1.20, downforce_factor:1.00, transmission_efficiency:0.97 },
    pininfarina_battista:      { power_kw:1400, weight_kg:2100, drag_coefficient:0.290, top_speed_kmh:350, cornering_grip:1.18, downforce_factor:0.98, transmission_efficiency:0.97 },
    ferrari_sf90:              { power_kw: 735, weight_kg:1570, drag_coefficient:0.340, top_speed_kmh:340, cornering_grip:1.35, downforce_factor:1.12, transmission_efficiency:0.93 },
    ferrari_laferrari:         { power_kw: 588, weight_kg:1255, drag_coefficient:0.330, top_speed_kmh:352, cornering_grip:1.45, downforce_factor:1.22, transmission_efficiency:0.93 },
    ferrari_f8:                { power_kw: 530, weight_kg:1330, drag_coefficient:0.320, top_speed_kmh:340, cornering_grip:1.30, downforce_factor:1.08, transmission_efficiency:0.93 },
    ferrari_812:               { power_kw: 588, weight_kg:1525, drag_coefficient:0.330, top_speed_kmh:340, cornering_grip:1.22, downforce_factor:1.02, transmission_efficiency:0.93 },
    lamborghini_revuelto:      { power_kw: 825, weight_kg:1772, drag_coefficient:0.320, top_speed_kmh:350, cornering_grip:1.32, downforce_factor:1.12, transmission_efficiency:0.93 },
    lamborghini_aventador_svj: { power_kw: 566, weight_kg:1525, drag_coefficient:0.350, top_speed_kmh:352, cornering_grip:1.40, downforce_factor:1.20, transmission_efficiency:0.93 },
    lamborghini_sian:          { power_kw: 602, weight_kg:1595, drag_coefficient:0.350, top_speed_kmh:350, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.94 },
    lamborghini_huracan_sto:   { power_kw: 470, weight_kg:1339, drag_coefficient:0.370, top_speed_kmh:310, cornering_grip:1.42, downforce_factor:1.22, transmission_efficiency:0.93 },
    porsche_918:               { power_kw: 652, weight_kg:1640, drag_coefficient:0.320, top_speed_kmh:345, cornering_grip:1.38, downforce_factor:1.15, transmission_efficiency:0.94 },
    porsche_911_gt2_rs:        { power_kw: 515, weight_kg:1470, drag_coefficient:0.380, top_speed_kmh:340, cornering_grip:1.44, downforce_factor:1.20, transmission_efficiency:0.93 },
    porsche_911_turbo_s:       { power_kw: 478, weight_kg:1640, drag_coefficient:0.330, top_speed_kmh:330, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.93 },
    mercedes_amg_one:          { power_kw: 782, weight_kg:1695, drag_coefficient:0.320, top_speed_kmh:352, cornering_grip:1.48, downforce_factor:1.28, transmission_efficiency:0.94 },
    gordon_murray_t50:         { power_kw: 485, weight_kg: 986, drag_coefficient:0.320, top_speed_kmh:370, cornering_grip:1.52, downforce_factor:1.32, transmission_efficiency:0.94 },
    czinger_21c:               { power_kw: 930, weight_kg:1250, drag_coefficient:0.320, top_speed_kmh:437, cornering_grip:1.40, downforce_factor:1.18, transmission_efficiency:0.94 },
    ford_gt:                   { power_kw: 485, weight_kg:1385, drag_coefficient:0.340, top_speed_kmh:348, cornering_grip:1.30, downforce_factor:1.10, transmission_efficiency:0.93 },
    corvette_z06:              { power_kw: 500, weight_kg:1560, drag_coefficient:0.340, top_speed_kmh:312, cornering_grip:1.35, downforce_factor:1.15, transmission_efficiency:0.93 },
    dodge_viper_acr:           { power_kw: 477, weight_kg:1521, drag_coefficient:0.420, top_speed_kmh:330, cornering_grip:1.38, downforce_factor:1.18, transmission_efficiency:0.92 },
    acura_nsx_type_s:          { power_kw: 447, weight_kg:1725, drag_coefficient:0.330, top_speed_kmh:307, cornering_grip:1.20, downforce_factor:1.00, transmission_efficiency:0.94 },
    nissan_gtr_nismo:          { power_kw: 441, weight_kg:1720, drag_coefficient:0.350, top_speed_kmh:315, cornering_grip:1.22, downforce_factor:1.02, transmission_efficiency:0.93 },
};

// ==========================================
// STATE
// ==========================================
const state = {
    activeTrack: 'monaco',
    vehicles: [],
    selectedVehicle: null,
    simResult: null,
    map: null,
    telemetryChart: null,
    isSimulating: false,
    animRaf: null,
    lightsTimeout: null
};

// ==========================================
// BOOT
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    await initVehicleDropdown();
    await bootMap();
    bindUI();
});

// ==========================================
// MAP
// ==========================================
async function bootMap() {
    state.map = await initMap('circuit-map', state.activeTrack);
    await loadTrack(state.activeTrack, onTurnClick);
    const ov = document.getElementById('map-loading');
    if (ov) ov.classList.add('hidden');
}

function onTurnClick(feature) {
    const { Turn_No, Turn_Name } = feature.properties;
    const info = document.getElementById('turn-info-bar');
    if (info) {
        info.innerHTML = `<span class="turn-tag">${Turn_No != null ? `T${Turn_No}` : '—'}</span><span class="turn-tag-name">${Turn_Name}</span>`;
        info.classList.add('visible');
    }
}

// ==========================================
// VEHICLES
// ==========================================
async function initVehicleDropdown() {
    const select = document.getElementById('car-select');
    if (!select) return;
    let vehicles = [];
    try {
        const apiBase = window.CONFIG ? window.CONFIG.API_BASE_URL : 'http://localhost:8000';
        const resp = await fetch(`${apiBase}/api/vehicles`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (data && typeof data === 'object' && !Array.isArray(data)) {
            vehicles = Object.entries(data).map(([id, name]) => {
                const specs = VEHICLE_SPECS[id] || {};
                return { id, name, ...specs };
            });
        }
    } catch (err) {
        console.warn('API fallback:', err.message);
        vehicles = Object.entries(VEHICLE_SPECS).map(([id, specs]) => ({
            id, name: id.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()), ...specs
        }));
    }
    vehicles.sort((a,b) => a.name.localeCompare(b.name));
    state.vehicles = vehicles;
    select.innerHTML = '<option value="">— Select Hypercar —</option>';
    vehicles.forEach((v,i) => {
        const o = document.createElement('option');
        o.value = i; o.textContent = v.name;
        select.appendChild(o);
    });
}

// ==========================================
// UI BINDINGS
// ==========================================
function bindUI() {
    document.querySelectorAll('.track-card').forEach(card => {
        card.addEventListener('click', () => {
            if (card.classList.contains('coming-soon')) return;
            document.querySelectorAll('.track-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            state.activeTrack = card.dataset.track;
        });
    });
    document.getElementById('simulate-btn')?.addEventListener('click', runSimulation);
    document.getElementById('car-select')?.addEventListener('change', e => {
        const idx = parseInt(e.target.value);
        if (!isNaN(idx) && state.vehicles[idx]) {
            state.selectedVehicle = state.vehicles[idx];
            updateCarPreview(state.vehicles[idx]);
        } else {
            state.selectedVehicle = null;
            clearCarPreview();
        }
    });
}

function updateCarPreview(car) {
    const preview = document.getElementById('car-preview');
    if (!preview) return;
    preview.innerHTML = `
        <div class="preview-grid">
            <div class="preview-stat"><span class="pstat-label">POWER</span><span class="pstat-val">${car.power_kw??'—'} <span class="pstat-unit">kW</span></span></div>
            <div class="preview-stat"><span class="pstat-label">WEIGHT</span><span class="pstat-val">${car.weight_kg??'—'} <span class="pstat-unit">kg</span></span></div>
            <div class="preview-stat"><span class="pstat-label">TOP SPEED</span><span class="pstat-val">${car.top_speed_kmh??'—'} <span class="pstat-unit">km/h</span></span></div>
            <div class="preview-stat"><span class="pstat-label">DRAG Cd</span><span class="pstat-val">${car.drag_coefficient?car.drag_coefficient.toFixed(3):'—'}</span></div>
        </div>`;
    preview.classList.add('visible');
}

function clearCarPreview() {
    const p = document.getElementById('car-preview');
    if (p) { p.innerHTML=''; p.classList.remove('visible'); }
}

// ==========================================
// SIMULATION RUNNER
// ==========================================
async function runSimulation() {
    const sel = document.getElementById('car-select');
    const idx = parseInt(sel?.value);
    if (isNaN(idx) || !state.vehicles[idx]) { showError('Select a hypercar first.'); return; }
    if (state.isSimulating) return;

    const car = state.vehicles[idx];

    // Cancel any running animation
    if (state.animRaf) { cancelAnimationFrame(state.animRaf); state.animRaf = null; }
    clearTimeout(state.lightsTimeout);

    // Collapse old results instantly
    const panel = document.getElementById('result-panel');
    if (panel) { panel.classList.remove('visible'); panel.style.display='none'; }

    // Compute simulation synchronously (fast enough)
    state.isSimulating = true;
    let result;
    try {
        result = simulateMonacoLap(car, state.activeTrack);
        state.simResult = result;
    } catch(err) {
        showError('Simulation error: '+err.message);
        state.isSimulating = false;
        return;
    }

    // === F1 LIGHTS-OUT SEQUENCE ===
    await lightsOutSequence(car.name || car.id);

    // Show panel
    if (panel) { panel.style.display='block'; panel.classList.add('visible'); }

    // Set static fields immediately
    document.getElementById('res-car-name').textContent = car.name || car.id;

    // Animate the lap timer counting up
    await animateLapTimer(result.lapTimeSeconds);

    // Show secondary stats with stagger
    await delay(200);
    animateValue('res-avgspeed', 0, result.avgSpeedKph, 900, v => v.toFixed(1)+' km/h');
    await delay(150);
    animateValue('res-topspeed', 0, result.maxSpeedKph, 900, v => Math.round(v)+' km/h');

    // Sector times
    renderSectorTimes(result.sectorTimes);
    await delay(300);

    // Chart – draw line progressively
    renderTelemetryChart(result.telemetry);
    await delay(300);

    // Braking zone table
    renderBrakeZoneTable(result.brakeZoneData);

    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    state.isSimulating = false;
}

// ==========================================
// F1 LIGHTS-OUT SEQUENCE
// ==========================================
async function lightsOutSequence(carName) {
    // Overlay element
    let overlay = document.getElementById('lights-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'lights-overlay';
        overlay.innerHTML = `
            <div class="lo-track">CIRCUIT DE MONACO</div>
            <div class="lo-car">${carName}</div>
            <div class="lo-lights">
                <div class="lo-light" id="ll1"></div>
                <div class="lo-light" id="ll2"></div>
                <div class="lo-light" id="ll3"></div>
                <div class="lo-light" id="ll4"></div>
                <div class="lo-light" id="ll5"></div>
            </div>
            <div class="lo-status" id="lo-status">FORMATION LAP COMPLETE</div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.lo-car').textContent = carName;
        overlay.querySelectorAll('.lo-light').forEach(l => l.classList.remove('on'));
        overlay.querySelector('#lo-status').textContent = 'FORMATION LAP COMPLETE';
        overlay.querySelector('#lo-status').className = 'lo-status';
    }
    overlay.classList.remove('fade-out');
    overlay.style.display = 'flex';
    void overlay.offsetWidth; // reflow
    overlay.classList.add('visible');

    await delay(900);

    // Light up 5 lights one by one (1 per 700ms like real F1)
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`ll${i}`)?.classList.add('on');
        await delay(700);
    }
    await delay(1200); // hold all 5 lit

    // LIGHTS OUT — all go off simultaneously
    document.querySelectorAll('.lo-light').forEach(l => l.classList.remove('on'));
    const status = document.getElementById('lo-status');
    status.textContent = "IT'S LIGHTS OUT AND AWAY WE GO!";
    status.classList.add('go');
    await delay(1100);

    // Fade out overlay
    overlay.classList.add('fade-out');
    await delay(600);
    overlay.style.display = 'none';
    overlay.classList.remove('visible', 'fade-out');
}

// ==========================================
// ANIMATED LAP TIMER
// ==========================================
async function animateLapTimer(finalSeconds) {
    return new Promise(resolve => {
        const el = document.getElementById('res-laptime');
        if (!el) { resolve(); return; }

        const duration = 2200; // ms for animation
        const start = performance.now();
        el.classList.add('counting');

        function tick(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const currentSecs = finalSeconds * eased;
            el.textContent = formatLapTime(currentSecs);

            if (progress < 1) {
                state.animRaf = requestAnimationFrame(tick);
            } else {
                el.textContent = formatLapTime(finalSeconds);
                el.classList.remove('counting');
                el.classList.add('final');
                setTimeout(() => el.classList.remove('final'), 600);
                resolve();
            }
        }
        state.animRaf = requestAnimationFrame(tick);
    });
}

// ==========================================
// ANIMATED VALUE COUNTER
// ==========================================
function animateValue(id, from, to, durationMs, formatter) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = performance.now();
    function tick(now) {
        const p = Math.min((now - start) / durationMs, 1);
        const eased = 1 - Math.pow(1-p, 3);
        el.textContent = formatter(from + (to - from) * eased);
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

// ==========================================
// SECTOR TIMES
// ==========================================
function renderSectorTimes(sectorTimes) {
    const el = document.getElementById('sector-times');
    if (!el) return;
    const labels = ['S1','S2','S3'];
    el.innerHTML = sectorTimes.map((t,i) => `
        <div class="sector-card">
            <div class="sector-label">${labels[i]}</div>
            <div class="sector-time">${formatLapTime(t)}</div>
        </div>`).join('');
    el.classList.add('visible');
}

// ==========================================
// TELEMETRY CHART – progressive draw
// ==========================================
function renderTelemetryChart(telemetry) {
    const canvas = document.getElementById('telemetry-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    if (state.telemetryChart) { state.telemetryChart.destroy(); state.telemetryChart = null; }

    // Downsample for performance – keep ~200 points
    const step = Math.max(1, Math.floor(telemetry.length / 200));
    const sampled = telemetry.filter((_,i) => i % step === 0);

    const labels = sampled.map(p => p.dist + 'm');
    const speeds = sampled.map(p => p.speed_kph);
    const braking= sampled.map(p => p.phase === 'braking');

    // Per-point colors
    const ptColors = sampled.map(p => {
        if (p.phase === 'braking') return 'rgba(255,0,102,0.9)';
        if (p.phase === 'corner')  return 'rgba(255,165,0,0.9)';
        return 'rgba(0,255,157,0.7)';
    });

    state.telemetryChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Speed (km/h)',
                    data: speeds,
                    borderColor: '#00FF9D',
                    borderWidth: 2.5,
                    pointBackgroundColor: ptColors,
                    pointBorderColor: 'transparent',
                    pointRadius: sampled.map(p => (p.phase==='braking'||p.phase==='corner') ? 4 : 0),
                    pointHoverRadius: 6,
                    fill: true,
                    backgroundColor: ctx => {
                        const g = ctx.chart.ctx.createLinearGradient(0,0,0,280);
                        g.addColorStop(0,'rgba(0,255,157,0.22)');
                        g.addColorStop(1,'rgba(0,255,157,0.00)');
                        return g;
                    },
                    tension: 0.35
                }
            ]
        },
        options: {
            animation: {
                duration: 1600,
                easing: 'easeInOutQuart'
            },
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0A120E',
                    borderColor: '#00FF9D',
                    borderWidth: 1,
                    titleColor: '#00FF9D',
                    bodyColor: '#FFFFFF',
                    padding: 10,
                    callbacks: {
                        title: items => sampled[items[0].dataIndex]?.seg || '',
                        label: item => {
                            const pt = sampled[item.dataIndex];
                            let str = ` Speed: ${item.raw} km/h`;
                            if (pt?.decel_g) str += `  |  Braking: ${pt.decel_g}g`;
                            return str;
                        },
                        labelColor: item => {
                            const c = ptColors[item.dataIndex];
                            return { backgroundColor: c, borderColor: c };
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color:'rgba(255,255,255,0.35)', maxTicksLimit:14, font:{size:9} },
                    grid:  { color:'rgba(255,255,255,0.04)' }
                },
                y: {
                    min: 0,
                    ticks: { color:'rgba(255,255,255,0.55)', font:{family:'Orbitron',size:9} },
                    grid:  { color:'rgba(0,255,157,0.06)' },
                    title: { display:true, text:'km/h', color:'#00FF9D', font:{size:10} }
                }
            }
        }
    });
}

// ==========================================
// BRAKING ZONE TABLE
// ==========================================
function renderBrakeZoneTable(brakeZones) {
    const container = document.getElementById('brake-zone-section');
    const tbody = document.getElementById('brake-zone-body');
    if (!container || !tbody) return;

    tbody.innerHTML = '';
    brakeZones.forEach((bz, i) => {
        // Severity bar width (0-100%)
        const barPct = Math.min(100, (bz.brakingDist_m / 80) * 100);
        const barColor = bz.peakDecel_g >= 1.2 ? '#FF0066' : bz.peakDecel_g >= 0.9 ? '#FF8C00' : '#00FF9D';
        const row = document.createElement('tr');
        row.className = 'bz-row';
        row.style.animationDelay = `${i * 60}ms`;
        row.innerHTML = `
            <td class="bz-corner">${bz.corner}</td>
            <td class="bz-entry">${bz.entry_kph}</td>
            <td class="bz-apex">${bz.apex_kph}</td>
            <td class="bz-loss">−${bz.speedLoss_kph}</td>
            <td class="bz-dist">
                <div class="bz-bar-wrap">
                    <div class="bz-bar" style="width:${barPct}%;background:${barColor}"></div>
                    <span>${bz.brakingDist_m}m</span>
                </div>
            </td>
            <td class="bz-time">${bz.brakingTime_ms}ms</td>
            <td class="bz-g" style="color:${barColor}">${bz.peakDecel_g}g</td>
        `;
        tbody.appendChild(row);
    });

    container.classList.add('visible');
}

// ==========================================
// UTILITIES
// ==========================================
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function showError(msg) {
    const e = document.getElementById('sim-error');
    if (e) { e.textContent=msg; e.classList.add('visible'); setTimeout(()=>e.classList.remove('visible'),4000); }
}
