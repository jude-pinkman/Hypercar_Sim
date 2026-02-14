// ==========================================
// IMPROVED VEHICLE SELECTION SYSTEM
// Dropdown-based selection for better UX
// ==========================================

export class VehicleSelector {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.selectedVehicles = [];
        this.availableVehicles = {};
        this.maxVehicles = 3; // Maximum vehicles that can be selected
    }

    async initialize() {
        try {
            // Fetch available vehicles from backend using CONFIG
            const response = await fetch(CONFIG.getEndpoint('vehicles'));
            this.availableVehicles = await response.json();

            this.render();
        } catch (error) {
            console.error('Failed to load vehicles:', error);
            this.container.innerHTML = '<p class="error-message">Failed to load vehicles</p>';
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="vehicle-selection-container">
                <div class="selection-header">
                    <label for="num-vehicles">Number of Vehicles:</label>
                    <select id="num-vehicles" class="vehicle-count-select">
                        <option value="1">1 Vehicle</option>
                        <option value="2" selected>2 Vehicles</option>
                        <option value="3">3 Vehicles</option>
                    </select>
                </div>

                <div id="vehicle-dropdowns" class="vehicle-dropdowns">
                    <!-- Vehicle dropdown menus will be inserted here -->
                </div>

                <div class="selection-summary">
                    <strong>Selected:</strong>
                    <span id="selection-count">0 vehicles</span>
                </div>
            </div>
        `;

        // Add event listener for vehicle count change
        document.getElementById('num-vehicles').addEventListener('change', (e) => {
            this.updateDropdownCount(parseInt(e.target.value));
        });

        // Initialize with 2 dropdowns (default)
        this.updateDropdownCount(2);
    }

    updateDropdownCount(count) {
        const container = document.getElementById('vehicle-dropdowns');
        container.innerHTML = '';

        // Limit previously selected vehicles to new count
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

        // Add placeholder option
        const placeholderOption = document.createElement('option');
        placeholderOption.value = '';
        placeholderOption.textContent = '-- Select a vehicle --';
        placeholderOption.disabled = true;
        placeholderOption.selected = this.selectedVehicles[index] === undefined;
        select.appendChild(placeholderOption);

        // Group vehicles by brand
        const grouped = this.groupVehiclesByBrand();

        // Add optgroups for each brand
        for (const [brand, vehicles] of Object.entries(grouped)) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = brand;

            vehicles.forEach(([vehicleId, vehicleName]) => {
                const option = document.createElement('option');
                option.value = vehicleId;
                option.textContent = vehicleName;

                // Pre-select if this vehicle was previously selected
                if (this.selectedVehicles[index] === vehicleId) {
                    option.selected = true;
                }

                // Disable if already selected in another dropdown
                if (this.selectedVehicles.includes(vehicleId) && this.selectedVehicles[index] !== vehicleId) {
                    option.disabled = true;
                    option.textContent += ' (Already selected)';
                }

                optgroup.appendChild(option);
            });

            select.appendChild(optgroup);
        }

        // Add change event listener
        select.addEventListener('change', (e) => {
            this.handleVehicleSelection(index, e.target.value);
        });

        wrapper.appendChild(label);
        wrapper.appendChild(select);

        return wrapper;
    }

    groupVehiclesByBrand() {
        const grouped = {};

        for (const [vehicleId, vehicleName] of Object.entries(this.availableVehicles)) {
            // Extract brand from vehicle name
            const brand = this.extractBrand(vehicleName);

            if (!grouped[brand]) {
                grouped[brand] = [];
            }

            grouped[brand].push([vehicleId, vehicleName]);
        }

        // Sort brands alphabetically
        const sortedGrouped = {};
        Object.keys(grouped).sort().forEach(key => {
            sortedGrouped[key] = grouped[key].sort((a, b) => a[1].localeCompare(b[1]));
        });

        return sortedGrouped;
    }

    extractBrand(vehicleName) {
        // Extract brand from vehicle name (e.g., "Ferrari SF90 Stradale" -> "Ferrari")
        const brands = [
            'Koenigsegg', 'Bugatti', 'McLaren', 'Ferrari', 'Lamborghini',
            'Porsche', 'Mercedes-AMG', 'Aston Martin', 'Pagani', 'Hennessey',
            'SSC', 'Rimac', 'Lotus', 'Aspark', 'Pininfarina', 'Gordon Murray',
            'Czinger', 'Ford', 'Chevrolet', 'Dodge', 'Acura', 'Nissan',
            'Lexus', 'Audi'
        ];

        for (const brand of brands) {
            if (vehicleName.startsWith(brand)) {
                return brand;
            }
        }

        return 'Other';
    }

    handleVehicleSelection(index, vehicleId) {
        if (vehicleId) {
            this.selectedVehicles[index] = vehicleId;
        } else {
            this.selectedVehicles.splice(index, 1);
        }

        // Refresh all dropdowns to update disabled states
        this.refreshDropdowns();
        this.updateSelectionSummary();
        this.dispatchChangeEvent();
    }

    refreshDropdowns() {
        const count = document.getElementById('num-vehicles').value;
        this.updateDropdownCount(parseInt(count));
    }

    updateSelectionSummary() {
        const summary = document.getElementById('selection-count');
        const count = this.selectedVehicles.filter(v => v).length;
        summary.textContent = `${count} vehicle${count !== 1 ? 's' : ''} selected`;
    }

    dispatchChangeEvent() {
        // Dispatch custom event that other parts of the app can listen to
        window.dispatchEvent(new CustomEvent('vehicleSelectionChanged', {
            detail: {
                selectedVehicles: this.getSelectedVehicles()
            }
        }));
    }

    getSelectedVehicles() {
        // Return only non-empty selections
        return this.selectedVehicles.filter(v => v);
    }
}

// Export for use in main sim.js
window.VehicleSelector = VehicleSelector;