// ==========================================
// SELECTED VEHICLES DISPLAY
// Shows selected cars with images and tuning buttons
// ==========================================

export class SelectedVehiclesDisplay {
    constructor() {
        this.selectedVehicles = new Set();
        this.vehicleNames = {};
        this.container = null;
    }

    initialize() {
        this.createContainer();
        this.setupEventListeners();
    }

    createContainer() {
        // Find the control panel
        const controlPanel = document.querySelector('.control-panel');
        if (!controlPanel) return;

        // Create selected vehicles card
        const card = document.createElement('div');
        card.className = 'card selected-vehicles-card';
        card.id = 'selectedVehiclesCard';
        card.style.display = 'none'; // Hidden by default

        card.innerHTML = `
            <div class="card-header">
                <h3>Selected Vehicles</h3>
                <span class="card-subtitle">Your racing lineup</span>
            </div>
            <div class="card-content">
                <div id="selectedVehiclesGrid" class="selected-vehicles-grid">
                    <!-- Dynamically populated -->
                </div>
            </div>
        `;

        // Insert after vehicle selection card
        const vehicleSelectionCard = controlPanel.querySelector('.card');
        if (vehicleSelectionCard) {
            vehicleSelectionCard.after(card);
        } else {
            controlPanel.insertBefore(card, controlPanel.firstChild);
        }

        this.container = card;
    }

    setupEventListeners() {
        // Listen for vehicle selection changes from checkboxes
        document.addEventListener('click', (e) => {
            const vehicleOption = e.target.closest('.vehicle-option');
            if (vehicleOption) {
                setTimeout(() => this.updateDisplay(), 100);
            }
        });

        // Also listen for programmatic updates
        window.addEventListener('vehicleSelectionChanged', () => {
            this.updateDisplay();
        });
    }

    updateDisplay() {
        // Get currently selected vehicles from the main state or checkboxes
        const selected = this.getSelectedVehicles();

        if (selected.length === 0) {
            this.container.style.display = 'none';
            return;
        }

        this.container.style.display = 'block';
        this.renderSelectedVehicles(selected);
    }

    getSelectedVehicles() {
        const selectedOptions = document.querySelectorAll('.vehicle-option.selected');
        const vehicles = [];

        selectedOptions.forEach(option => {
            const vehicleId = option.dataset.vehicleId;
            const vehicleName = option.querySelector('.vehicle-name')?.textContent;

            if (vehicleId && vehicleName) {
                vehicles.push({ id: vehicleId, name: vehicleName });
            }
        });

        return vehicles;
    }

    renderSelectedVehicles(vehicles) {
        const grid = document.getElementById('selectedVehiclesGrid');
        if (!grid) return;

        grid.innerHTML = '';

        vehicles.forEach(vehicle => {
            const vehicleCard = this.createVehicleCard(vehicle);
            grid.appendChild(vehicleCard);
        });
    }

    createVehicleCard(vehicle) {
        const card = document.createElement('div');
        card.className = 'selected-vehicle-item';
        card.dataset.vehicleId = vehicle.id;

        // Get vehicle image
        const imageUrl = this.getVehicleImage(vehicle.id);

        card.innerHTML = `
            <div class="selected-vehicle-image">
                <img src="${imageUrl}" alt="${vehicle.name}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22120%22%3E%3Crect fill=%22%23222%22 width=%22200%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 fill=%22%23666%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22 font-family=%22Arial%22 font-size=%2214%22%3E${vehicle.name.substring(0, 15)}%3C/text%3E%3C/svg%3E'">
            </div>
            <div class="selected-vehicle-info">
                <h4 class="selected-vehicle-name">${vehicle.name}</h4>
                <div class="selected-vehicle-actions">
                    <button class="btn-tune" data-vehicle-id="${vehicle.id}">
                        <span class="btn-icon">🔧</span>
                        <span class="btn-text">Tune</span>
                    </button>
                    <button class="btn-remove" data-vehicle-id="${vehicle.id}">
                        <span class="btn-icon">✕</span>
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        const tuneBtn = card.querySelector('.btn-tune');
        const removeBtn = card.querySelector('.btn-remove');

        tuneBtn.addEventListener('click', () => {
            if (window.tuningSystem) {
                window.tuningSystem.openTuningPanel(vehicle.id, vehicle.name);
            } else {
                console.error('Tuning system not loaded');
            }
        });

        removeBtn.addEventListener('click', () => {
            this.removeVehicle(vehicle.id);
        });

        return card;
    }

    getVehicleImage(vehicleId) {
        // Map of vehicle IDs to image URLs
        const imageMap = {
            'koenigsegg_jesko': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400&h=240&fit=crop',
            'bugatti_chiron': 'https://images.unsplash.com/photo-1566024287286-457247b70310?w=400&h=240&fit=crop',
            'bugatti_chiron_ss': 'https://images.unsplash.com/photo-1566024287286-457247b70310?w=400&h=240&fit=crop',
            'hennessey_venom': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=240&fit=crop',
            'hennessey_venom_f5': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=240&fit=crop',
            'ssc_tuatara': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400&h=240&fit=crop',
            'bugatti_bolide': 'https://images.unsplash.com/photo-1566024287286-457247b70310?w=400&h=240&fit=crop',
            'koenigsegg_jesko_attack': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400&h=240&fit=crop',
            'pagani_huayra': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=240&fit=crop',
            'mclaren_speedtail': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=240&fit=crop',
            'aston_martin_valkyrie': 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=400&h=240&fit=crop',
            // Add more as needed - these use Unsplash car photos
        };

        return imageMap[vehicleId] || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22120%22%3E%3Crect fill=%22%23222%22 width=%22200%22 height=%22120%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 fill=%22%23666%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22 font-family=%22Arial%22 font-size=%2216%22%3E🏎️%3C/text%3E%3C/svg%3E';
    }

    removeVehicle(vehicleId) {
        // Find and click the vehicle option to deselect it
        const vehicleOption = document.querySelector(`.vehicle-option[data-vehicle-id="${vehicleId}"]`);
        if (vehicleOption) {
            vehicleOption.click();
        }
    }
}

// Initialize when DOM is ready
let selectedVehiclesDisplay = null;

document.addEventListener('DOMContentLoaded', () => {
    selectedVehiclesDisplay = new SelectedVehiclesDisplay();
    selectedVehiclesDisplay.initialize();
    console.log('✅ Selected Vehicles Display initialized');
});

// Export for use in other modules
export { selectedVehiclesDisplay };
window.selectedVehiclesDisplay = selectedVehiclesDisplay;