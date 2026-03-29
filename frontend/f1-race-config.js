/**
 * f1-race-config.js — Race page initialiser
 * Reads circuit + weather from sessionStorage (set by f1-setup.html).
 * Falls back to AUS/dry if accessed directly.
 */

// ── API URL ───────────────────────────────────────────────────────────────────
const API_URL = (() => {
    const { protocol, origin } = window.location;
    return (protocol === 'http:' || protocol === 'https:') ? origin : 'http://127.0.0.1:8000';
})();
console.log('[F1 Config] API_URL:', API_URL);

// ── Circuit data ──────────────────────────────────────────────────────────────
const CIRCUITS_2026 = [
  {
    "circuit_id": "AUS",
    "name": "Albert Park Circuit",
    "country": "AUS",
    "lap_length_km": 5.278,
    "corners": 16,
    "drs_zones": 2,
    "lap_record": "1:17.657 (Leclerc, 2024)",
    "typical_laps": 58,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "CHN",
    "name": "Shanghai International Circuit",
    "country": "CHN",
    "lap_length_km": 5.451,
    "corners": 16,
    "drs_zones": 2,
    "lap_record": "1:31.897 (Bottas, 2018)",
    "typical_laps": 56,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "JPN",
    "name": "Suzuka International Racing Course",
    "country": "JPN",
    "lap_length_km": 5.807,
    "corners": 16,
    "drs_zones": 1,
    "lap_record": "1:27.064 (Hamilton, 2019)",
    "typical_laps": 53,
    "circuit_type": "power",
    "coordinates": null
  },
  {
    "circuit_id": "MIA",
    "name": "Miami International Autodrome",
    "country": "USA",
    "lap_length_km": 5.41,
    "corners": 19,
    "drs_zones": 2,
    "lap_record": "1:29.708 (Russell, 2023)",
    "typical_laps": 57,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "MON",
    "name": "Circuit de Monaco",
    "country": "MCO",
    "lap_length_km": 3.337,
    "corners": 19,
    "drs_zones": 0,
    "lap_record": "1:10.166 (Leclerc, 2023)",
    "typical_laps": 78,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "CAN",
    "name": "Circuit Gilles Villeneuve",
    "country": "CAN",
    "lap_length_km": 4.361,
    "corners": 13,
    "drs_zones": 1,
    "lap_record": "1:21.459 (Bottas, 2018)",
    "typical_laps": 70,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "BAR",
    "name": "Circuit de Barcelona-Catalunya",
    "country": "ESP",
    "lap_length_km": 4.657,
    "corners": 16,
    "drs_zones": 2,
    "lap_record": "1:18.149 (Bottas, 2018)",
    "typical_laps": 66,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "AUT",
    "name": "Red Bull Ring",
    "country": "AUT",
    "lap_length_km": 4.318,
    "corners": 10,
    "drs_zones": 1,
    "lap_record": "1:05.619 (Bottas, 2020)",
    "typical_laps": 71,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "GBR",
    "name": "Silverstone Circuit",
    "country": "GBR",
    "lap_length_km": 5.891,
    "corners": 18,
    "drs_zones": 2,
    "lap_record": "1:27.097 (Hamilton, 2020)",
    "typical_laps": 52,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "BEL",
    "name": "Circuit de Spa-Francorchamps",
    "country": "BEL",
    "lap_length_km": 6.996,
    "corners": 19,
    "drs_zones": 2,
    "lap_record": "1:41.252 (Verstappen, 2023)",
    "typical_laps": 44,
    "circuit_type": "power",
    "coordinates": null
  },
  {
    "circuit_id": "HUN",
    "name": "Hungaroring",
    "country": "HUN",
    "lap_length_km": 4.381,
    "corners": 14,
    "drs_zones": 0,
    "lap_record": "1:16.627 (Hamilton, 2020)",
    "typical_laps": 70,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "NED",
    "name": "Circuit Park Zandvoort",
    "country": "NED",
    "lap_length_km": 4.259,
    "corners": 14,
    "drs_zones": 2,
    "lap_record": "1:11.097 (Bottas, 2021)",
    "typical_laps": 72,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "ITA",
    "name": "Autodromo Nazionale di Monza",
    "country": "ITA",
    "lap_length_km": 5.793,
    "corners": 11,
    "drs_zones": 2,
    "lap_record": "1:19.119 (Verstappen, 2023)",
    "typical_laps": 53,
    "circuit_type": "power",
    "coordinates": null
  },
  {
    "circuit_id": "AZE",
    "name": "Baku City Circuit",
    "country": "AZE",
    "lap_length_km": 6.003,
    "corners": 18,
    "drs_zones": 2,
    "lap_record": "1:43.009 (Leclerc, 2019)",
    "typical_laps": 51,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "SIN",
    "name": "Marina Bay Street Circuit",
    "country": "SGP",
    "lap_length_km": 5.063,
    "corners": 23,
    "drs_zones": 2,
    "lap_record": "1:41.905 (Hamilton, 2019)",
    "typical_laps": 61,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "USA",
    "name": "Circuit of The Americas",
    "country": "USA",
    "lap_length_km": 5.513,
    "corners": 20,
    "drs_zones": 2,
    "lap_record": "1:32.910 (Hamilton, 2017)",
    "typical_laps": 56,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "MEX",
    "name": "Aut\u00f3dromo Hermanos Rodr\u00edguez",
    "country": "MEX",
    "lap_length_km": 4.304,
    "corners": 17,
    "drs_zones": 2,
    "lap_record": "1:18.741 (Hamilton, 2018)",
    "typical_laps": 71,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "BRA",
    "name": "Aut\u00f3dromo Jos\u00e9 Carlos Pace",
    "country": "BRA",
    "lap_length_km": 4.309,
    "corners": 15,
    "drs_zones": 1,
    "lap_record": "1:10.540 (Bottas, 2016)",
    "typical_laps": 71,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "LVG",
    "name": "Las Vegas Strip Circuit",
    "country": "USA",
    "lap_length_km": 6.12,
    "corners": 17,
    "drs_zones": 2,
    "lap_record": "1:35.490 (Sainz, 2023)",
    "typical_laps": 50,
    "circuit_type": "street",
    "coordinates": null
  },
  {
    "circuit_id": "QAT",
    "name": "Lusail International Circuit",
    "country": "QAT",
    "lap_length_km": 5.419,
    "corners": 16,
    "drs_zones": 2,
    "lap_record": "1:24.535 (Leclerc, 2021)",
    "typical_laps": 57,
    "circuit_type": "balanced",
    "coordinates": null
  },
  {
    "circuit_id": "ABU",
    "name": "Yas Marina Circuit",
    "country": "UAE",
    "lap_length_km": 5.281,
    "corners": 16,
    "drs_zones": 2,
    "lap_record": "1:26.103 (Leclerc, 2019)",
    "typical_laps": 58,
    "circuit_type": "balanced",
    "coordinates": null
  }
];

// ── Local win predictions ─────────────────────────────────────────────────────
const LOCAL_PREDICTIONS = [
    { driver:'Max Verstappen',  team:'Red Bull Racing', probability:0.28 },
    { driver:'Lewis Hamilton',  team:'Ferrari',         probability:0.21 },
    { driver:'Lando Norris',    team:'McLaren',         probability:0.17 },
    { driver:'Charles Leclerc', team:'Ferrari',         probability:0.13 },
    { driver:'George Russell',  team:'Mercedes',        probability:0.09 },
    { driver:'Oscar Piastri',   team:'McLaren',         probability:0.07 },
    { driver:'Fernando Alonso', team:'Aston Martin',    probability:0.03 },
    { driver:'Carlos Sainz Jr.',team:'Williams',        probability:0.02 },
];

// ── Read setup from sessionStorage ───────────────────────────────────────────
const configState = (() => {
    try {
        const raw = sessionStorage.getItem('f1_race_setup');
        if (raw) {
            const parsed = JSON.parse(raw);
            return {
                selectedCircuit: parsed.circuit,
                selectedWeather: parsed.weather || 'dry',
                selectedSpeed:   1,
                isStarting:      false,
            };
        }
    } catch {}
    // Fallback: AUS dry
    const aus = CIRCUITS_2026.find(c => c.circuit_id === 'AUS') || CIRCUITS_2026[0];
    return { selectedCircuit: aus, selectedWeather: 'dry', selectedSpeed: 1, isStarting: false };
})();

// ── DOM ready — update header and auto-start ──────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    const c = configState.selectedCircuit;
    const w = configState.selectedWeather;

    // Update header
    const nameEl = document.getElementById('header-circuit-name');
    const wxEl   = document.getElementById('header-weather');
    if (nameEl) nameEl.textContent = c.name;
    if (wxEl) {
        const wxIcons = { dry:'☀️ Dry', damp:'🌦 Damp', wet:'🌧 Wet' };
        wxEl.textContent = wxIcons[w] || w;
    }

    // Wire stop button
    const stopBtn = document.getElementById('stop-race-btn');
    if (stopBtn) stopBtn.addEventListener('click', stopRaceSimulation);

    // Check backend then auto-start
    checkBackendAndStart();
});

async function checkBackendAndStart() {
    const errEl = document.getElementById('race-error');
    try {
        const r = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(5000) });
        if (!r.ok) throw new Error('not ok');
    } catch {
        if (errEl) {
            errEl.style.display = 'block';
            errEl.textContent = '⚠️ Backend offline — run: uvicorn app.main:app --reload --port 8080';
        }
        return;
    }

    // Start race automatically
    const stopBtn = document.getElementById('stop-race-btn');
    if (stopBtn) stopBtn.style.display = 'flex';

    try {
        await window.raceSimulationAPI.start(
            configState.selectedCircuit,
            { weather: configState.selectedWeather, race_speed_multiplier: 1 }
        );
    } catch (err) {
        if (errEl) {
            errEl.style.display = 'block';
            errEl.textContent = 'Race failed: ' + err.message;
        }
        if (stopBtn) stopBtn.style.display = 'none';
    }
}

function stopRaceSimulation() {
    window.raceSimulationAPI?.stop();
    const stopBtn = document.getElementById('stop-race-btn');
    if (stopBtn) stopBtn.style.display = 'none';
}

function showError(msg) {
    const el = document.getElementById('race-error');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}
function clearError() {
    const el = document.getElementById('race-error');
    if (el) el.style.display = 'none';
}
