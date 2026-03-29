/**
 * f1-setup.js — Pre-race setup page
 * Circuit selection, weather, predictions, then navigate to f1-race.html
 */

// ── API URL (same-origin when served by FastAPI) ─────────────────────────────
const API_URL = (() => {
    const { protocol, origin } = window.location;
    return (protocol === 'http:' || protocol === 'https:') ? origin : 'http://127.0.0.1:8000';
})();

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

// ── Local win-probability estimates ──────────────────────────────────────────
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

const FLAG_EMOJIS = {
    AUS:'🇦🇺',CHN:'🇨🇳',JPN:'🇯🇵',USA:'🇺🇸',MCO:'🇲🇨',CAN:'🇨🇦',
    ESP:'🇪🇸',AUT:'🇦🇹',GBR:'🇬🇧',BEL:'🇧🇪',HUN:'🇭🇺',NED:'🇳🇱',
    ITA:'🇮🇹',AZE:'🇦🇿',SGP:'🇸🇬',MEX:'🇲🇽',BRA:'🇧🇷',QAT:'🇶🇦',UAE:'🇦🇪',
};

const TYPE_ICONS = { street:'🏙️', balanced:'🏎️', power:'⚡', technical:'🔧' };

// ── State ─────────────────────────────────────────────────────────────────────
let selected = null;
let weather  = 'dry';

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    renderCircuitList(CIRCUITS_2026);
    setupSearch();
    setupWeather();
    setupSimulateBtn();
    checkBackend();
});

// ── Backend check ─────────────────────────────────────────────────────────────
async function checkBackend() {
    const el = document.getElementById('backend-status-text');
    try {
        const r = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(4000) });
        if (r.ok) { el.textContent = 'Online'; el.style.color = '#00FF9D'; }
        else throw new Error();
    } catch {
        el.textContent = 'Offline';
        el.style.color = '#FF5555';
        document.getElementById('setup-error').style.display = 'block';
        document.getElementById('setup-error').textContent =
            '⚠️ Backend offline — run: uvicorn app.main:app --reload --port 8080';
    }
}

// ── Circuit list ──────────────────────────────────────────────────────────────
function renderCircuitList(circuits) {
    const el = document.getElementById('circuit-list');
    el.innerHTML = circuits.map(c => `
      <div class="circuit-row" data-id="${c.circuit_id}" onclick="selectCircuit('${c.circuit_id}')">
        <span class="circuit-row-flag">${FLAG_EMOJIS[c.circuit_id] || '🏁'}</span>
        <span class="circuit-row-name">${c.name}</span>
        <span class="circuit-row-type">${TYPE_ICONS[c.circuit_type] || '🏎️'}</span>
      </div>`).join('');
}

function setupSearch() {
    document.getElementById('circuit-search').addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        const filtered = CIRCUITS_2026.filter(c =>
            c.name.toLowerCase().includes(q) || c.circuit_id.toLowerCase().includes(q)
        );
        renderCircuitList(filtered);
    });
}

// ── Select a circuit ──────────────────────────────────────────────────────────
function selectCircuit(id) {
    selected = CIRCUITS_2026.find(c => c.circuit_id === id);
    if (!selected) return;

    // Highlight row
    document.querySelectorAll('.circuit-row').forEach(r =>
        r.classList.toggle('active', r.dataset.id === id));

    renderCircuitDetail(selected);
    loadPredictions();
    document.getElementById('simulate-btn').disabled = false;
}

function renderCircuitDetail(c) {
    const flag = FLAG_EMOJIS[c.circuit_id] || '🏁';
    const icon = TYPE_ICONS[c.circuit_type] || '🏎️';

    // Convert lap_record to total seconds for display
    const recParts = c.lap_record.split(':');
    const recSecs  = recParts.length === 2
        ? (parseInt(recParts[0])*60 + parseFloat(recParts[1])).toFixed(3)
        : c.lap_record;

    document.getElementById('circuit-detail').innerHTML = `
      <div class="cd-hero">
        <div class="cd-flag">${flag}</div>
        <div class="cd-title-block">
          <div class="cd-name">${c.name}</div>
          <div class="cd-country">${c.circuit_id} · ${icon} ${(c.circuit_type||'').charAt(0).toUpperCase()+(c.circuit_type||'').slice(1)}</div>
        </div>
      </div>

      <div class="cd-stats-grid">
        <div class="cd-stat">
          <div class="cd-stat-label">Lap Length</div>
          <div class="cd-stat-value">${c.lap_length_km} km</div>
        </div>
        <div class="cd-stat">
          <div class="cd-stat-label">Race Distance</div>
          <div class="cd-stat-value">${(c.lap_length_km * c.typical_laps).toFixed(1)} km</div>
        </div>
        <div class="cd-stat">
          <div class="cd-stat-label">Laps</div>
          <div class="cd-stat-value">${c.typical_laps}</div>
        </div>
        <div class="cd-stat">
          <div class="cd-stat-label">Corners</div>
          <div class="cd-stat-value">${c.corners}</div>
        </div>
        <div class="cd-stat">
          <div class="cd-stat-label">DRS Zones</div>
          <div class="cd-stat-value">${c.drs_zones}</div>
        </div>
        <div class="cd-stat">
          <div class="cd-stat-label">Type</div>
          <div class="cd-stat-value">${(c.circuit_type||'').charAt(0).toUpperCase()+(c.circuit_type||'').slice(1)}</div>
        </div>
      </div>

      <div class="cd-record-block">
        <div class="cd-record-label">⚡ LAP RECORD</div>
        <div class="cd-record-value">${c.lap_record}</div>
      </div>
    `;
}

// ── Weather ───────────────────────────────────────────────────────────────────
function setupWeather() {
    document.querySelectorAll('.setup-wx-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.setup-wx-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            weather = btn.dataset.weather;
            if (selected) loadPredictions();
        });
    });
}

// ── Predictions ───────────────────────────────────────────────────────────────
async function loadPredictions() {
    const el = document.getElementById('predictions-list');
    el.innerHTML = '<div style="color:#333;text-align:center;padding:20px">Loading…</div>';

    // Try live backend
    try {
        const r = await fetch(`${API_URL}/api/f1/predict-race`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ circuit_id: selected.circuit_id }),
            signal: AbortSignal.timeout(4000),
        });
        if (r.ok) {
            const data = await r.json();
            renderPredictions(data.predictions.slice(0,8));
            return;
        }
    } catch {}

    renderPredictions(LOCAL_PREDICTIONS);
}

function renderPredictions(preds) {
    const el = document.getElementById('predictions-list');
    const max = preds[0]?.probability || 0.28;

    el.innerHTML = preds.map((p, i) => {
        const pct = (p.probability * 100).toFixed(1);
        const barW = Math.round((p.probability / max) * 100);
        const medal = ['🥇','🥈','🥉'][i] || '';
        return `
          <div class="pred-row">
            <div class="pred-rank">${medal || (i+1)}</div>
            <div class="pred-info">
              <div class="pred-driver">${p.driver}</div>
              <div class="pred-team">${p.team || ''}</div>
            </div>
            <div class="pred-bar-col">
              <div class="pred-bar-bg">
                <div class="pred-bar-fill" style="width:${barW}%"></div>
              </div>
              <div class="pred-pct">${pct}%</div>
            </div>
          </div>`;
    }).join('');
}

// ── Simulate button ───────────────────────────────────────────────────────────
function setupSimulateBtn() {
    document.getElementById('simulate-btn').addEventListener('click', () => {
        if (!selected) return;
        // Pass selection to race page via sessionStorage
        sessionStorage.setItem('f1_race_setup', JSON.stringify({
            circuit: selected,
            weather: weather,
        }));
        window.location.href = 'f1-race.html';
    });
}
