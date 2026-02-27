// ==========================================
// VEHICLE SELECTION SYSTEM
// Supports Hypercars + Formula 1 categories
// Works offline — no backend required
// ==========================================

import { CAR_CATALOGUE } from './car-data.js';

// ---- Static catalogue split by category ----
const HYPERCAR_CATALOGUE = CAR_CATALOGUE.filter(c => c.carCategory === 'hypercar');
const F1_CATALOGUE       = CAR_CATALOGUE.filter(c => c.carCategory === 'f1');

export class VehicleSelector {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.selectedVehicles  = [];
        this.availableVehicles = {}; // { id: displayName } — kept for legacy compat
        this.maxVehicles = 3;
        this.activeCategory = 'hypercars'; // 'hypercars' | 'f1'
    }

    // ----------------------------------------
    // INITIALISE
    // Try backend for hypercar names; fall back
    // to catalogue. F1 cars always use catalogue.
    // ----------------------------------------
    async initialize() {
        // Try to fetch hypercar names from backend
        try {
            const url = window.CONFIG ? window.CONFIG.getEndpoint('vehicles') : '/api/vehicles';
            const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
            if (response.ok) {
                const backendVehicles = await response.json();
                Object.assign(this.availableVehicles, backendVehicles);
            }
        } catch (e) {
            // Backend unavailable — catalogue covers everything
        }

        // Always fill from catalogue so F1 + offline hypercars work
        CAR_CATALOGUE.forEach(car => {
            if (!this.availableVehicles[car.id]) {
                this.availableVehicles[car.id] = `${car.team} ${car.model}`;
            }
        });

        this.render();
    }

    // ----------------------------------------
    // RENDER — full UI
    // ----------------------------------------
    render() {
        this.container.innerHTML = `
            <div class="vehicle-selection-container">

                <div class="vs-category-toggle">
                    <button class="vs-cat-btn active" data-cat="hypercars">&#127950; Hypercars</button>
                    <button class="vs-cat-btn"        data-cat="f1">&#127937; Formula 1</button>
                </div>

                <div class="selection-header">
                    <label for="num-vehicles">Number of Vehicles:</label>
                    <select id="num-vehicles" class="vehicle-count-select">
                        <option value="1">1 Vehicle</option>
                        <option value="2" selected>2 Vehicles</option>
                        <option value="3">3 Vehicles</option>
                    </select>
                </div>

                <div id="vehicle-dropdowns" class="vehicle-dropdowns"></div>

                <div class="selection-summary">
                    <strong>Selected:</strong>
                    <span id="selection-count">0 vehicles selected</span>
                </div>

            </div>
        `;

        // Category toggle
        this.container.querySelectorAll('.vs-cat-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.container.querySelectorAll('.vs-cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeCategory = btn.dataset.cat;
                this.selectedVehicles = [];
                this.updateDropdownCount(parseInt(document.getElementById('num-vehicles').value));
            });
        });

        document.getElementById('num-vehicles').addEventListener('change', e => {
            this.updateDropdownCount(parseInt(e.target.value));
        });

        this.updateDropdownCount(2);
    }

    // ----------------------------------------
    // DROPDOWN MANAGEMENT
    // ----------------------------------------
    updateDropdownCount(count) {
        const container = document.getElementById('vehicle-dropdowns');
        if (!container) return;
        container.innerHTML = '';
        this.selectedVehicles = this.selectedVehicles.slice(0, count);
        for (let i = 0; i < count; i++) {
            container.appendChild(this.createVehicleDropdown(i));
        }
        this.updateSelectionSummary();
        this.dispatchChangeEvent();
    }

    createVehicleDropdown(index) {
        const wrapper = document.createElement('div');
        wrapper.className = 'vehicle-dropdown-wrapper';

        const label = document.createElement('label');
        label.textContent = `Vehicle ${index + 1}:`;
        label.className = 'vehicle-dropdown-label';

        const select = document.createElement('select');
        select.className = 'vehicle-dropdown-select';
        select.id = `vehicle-select-${index}`;

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = '-- Select a vehicle --';
        placeholder.disabled = true;
        placeholder.selected = !this.selectedVehicles[index];
        select.appendChild(placeholder);

        const catalogue = this.activeCategory === 'f1' ? F1_CATALOGUE : HYPERCAR_CATALOGUE;
        const grouped   = this._groupByTeam(catalogue);

        for (const [team, cars] of Object.entries(grouped)) {
            const og = document.createElement('optgroup');
            og.label = team;
            cars.forEach(car => {
                const opt = document.createElement('option');
                opt.value = car.id;
                opt.textContent = `${car.model} (${car.year})`;
                if (this.selectedVehicles[index] === car.id) opt.selected = true;
                if (this.selectedVehicles.includes(car.id) && this.selectedVehicles[index] !== car.id) {
                    opt.disabled = true;
                    opt.textContent += ' \u2713';
                }
                og.appendChild(opt);
            });
            select.appendChild(og);
        }

        select.addEventListener('change', e => this.handleVehicleSelection(index, e.target.value));
        wrapper.appendChild(label);
        wrapper.appendChild(select);
        return wrapper;
    }

    _groupByTeam(catalogue) {
        const grouped = {};
        catalogue.forEach(car => {
            if (!grouped[car.team]) grouped[car.team] = [];
            grouped[car.team].push(car);
        });
        return Object.fromEntries(
            Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b))
        );
    }

    handleVehicleSelection(index, vehicleId) {
        if (vehicleId) this.selectedVehicles[index] = vehicleId;
        else delete this.selectedVehicles[index];
        this.refreshDropdowns();
        this.updateSelectionSummary();
        this.dispatchChangeEvent();
    }

    refreshDropdowns() {
        const countEl = document.getElementById('num-vehicles');
        if (countEl) this.updateDropdownCount(parseInt(countEl.value));
    }

    // ----------------------------------------
    // SUMMARY + TUNING BUTTONS
    // ----------------------------------------
    updateSelectionSummary() {
        const summary = document.getElementById('selection-count');
        if (!summary) return;
        const count = this.getSelectedVehicles().length;
        summary.textContent = `${count} vehicle${count !== 1 ? 's' : ''} selected`;
        this.updateTuningButtons();
    }

    updateTuningButtons() {
        const container = document.getElementById('vehicle-tuning-buttons');
        if (!container) { this.createTuningButtonsContainer(); return; }
        container.innerHTML = '';
        const selected = this.getSelectedVehicles();
        if (selected.length === 0) { container.style.display = 'none'; return; }
        container.style.display = 'block';
        selected.forEach(vehicleId => {
            const vehicleName = this.availableVehicles[vehicleId] || vehicleId;
            const btn = document.createElement('button');
            btn.className = 'vehicle-tune-button';
            btn.innerHTML = `<span class="tune-icon">\uD83D\uDD27</span><span class="tune-label">Tune ${vehicleName}</span>`;
            btn.onclick = () => {
                if (window.tuningSystem) window.tuningSystem.openTuningPanel(vehicleId, vehicleName);
                else console.error('Tuning system not loaded');
            };
            container.appendChild(btn);
        });
    }

    createTuningButtonsContainer() {
        const selectionContainer = this.container.querySelector('.vehicle-selection-container');
        if (!selectionContainer) return;
        const tc = document.createElement('div');
        tc.id = 'vehicle-tuning-buttons';
        tc.className = 'vehicle-tuning-buttons';
        tc.style.display = 'none';
        const summary = selectionContainer.querySelector('.selection-summary');
        if (summary) summary.after(tc);
        else selectionContainer.appendChild(tc);
        this.updateTuningButtons();
    }

    // ----------------------------------------
    // PUBLIC API
    // ----------------------------------------
    dispatchChangeEvent() {
        window.dispatchEvent(new CustomEvent('vehicleSelectionChanged', {
            detail: { selectedVehicles: this.getSelectedVehicles() }
        }));
    }

    getSelectedVehicles() {
        return this.selectedVehicles.filter(v => v);
    }

    // Legacy helpers kept for backward compatibility
    groupVehiclesByBrand() {
        const grouped = {};
        for (const [id, name] of Object.entries(this.availableVehicles)) {
            const brand = this.extractBrand(name);
            if (!grouped[brand]) grouped[brand] = [];
            grouped[brand].push([id, name]);
        }
        const sorted = {};
        Object.keys(grouped).sort().forEach(k => {
            sorted[k] = grouped[k].sort((a, b) => a[1].localeCompare(b[1]));
        });
        return sorted;
    }

    extractBrand(vehicleName) {
        const brands = [
            'Koenigsegg', 'Bugatti', 'McLaren', 'Ferrari', 'Lamborghini',
            'Porsche', 'Mercedes-AMG', 'Aston Martin', 'Pagani', 'Hennessey',
            'SSC', 'Rimac', 'Lotus', 'Aspark', 'Pininfarina', 'Gordon Murray',
            'Czinger', 'Ford', 'Chevrolet', 'Dodge', 'Acura', 'Nissan', 'Lexus', 'Audi'
        ];
        for (const b of brands) { if (vehicleName.startsWith(b)) return b; }
        return 'Other';
    }
}

// ---- Inject category toggle CSS once ----
(function () {
    if (document.getElementById('vs-cat-style')) return;
    const s = document.createElement('style');
    s.id = 'vs-cat-style';
    s.textContent = `
        .vs-category-toggle {
            display: flex;
            gap: 8px;
            padding: 4px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .vs-cat-btn {
            flex: 1;
            padding: 10px 12px;
            background: transparent;
            border: 2px solid transparent;
            border-radius: 8px;
            color: rgba(255,255,255,0.55);
            font-family: 'Rajdhani', sans-serif;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .vs-cat-btn:hover {
            color: rgba(255,255,255,0.85);
            background: rgba(255,255,255,0.05);
        }
        .vs-cat-btn.active {
            background: rgba(0,255,157,0.12);
            border-color: rgba(0,255,157,0.5);
            color: #00ff9d;
            box-shadow: 0 0 12px rgba(0,255,157,0.15);
        }
    `;
    document.head.appendChild(s);
}());

window.VehicleSelector = VehicleSelector;
