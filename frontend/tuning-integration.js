// ==========================================
// TUNING INTEGRATION - CLEAN REBUILD
// Connects tuning system to vehicle selection
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔌 Tuning integration loading...');

    // Wait for vehicles to be loaded
    setTimeout(addTuningButtons, 1000);

    // Re-add when vehicles are updated
    window.addEventListener('vehiclesLoaded', () => {
        setTimeout(addTuningButtons, 200);
    });
});

function addTuningButtons() {
    const vehicleOptions = document.querySelectorAll('.vehicle-option');

    if (vehicleOptions.length === 0) {
        console.log('⏳ No vehicles found, retrying...');
        setTimeout(addTuningButtons, 500);
        return;
    }

    console.log(`🔧 Adding tuning buttons to ${vehicleOptions.length} vehicles`);

    vehicleOptions.forEach(option => {
        // Skip if button already exists
        if (option.querySelector('.vehicle-tune-btn')) return;

        // Ensure relative positioning
        option.style.position = 'relative';

        // Create tuning button
        const tuneBtn = document.createElement('button');
        tuneBtn.className = 'vehicle-tune-btn';
        tuneBtn.innerHTML = '🔧';
        tuneBtn.title = 'Tune this vehicle';

        tuneBtn.onclick = (e) => {
            e.stopPropagation();

            const vehicleId = option.dataset.vehicleId;
            const vehicleName = option.querySelector('.vehicle-name')?.textContent || 'Unknown';

            if (window.tuningSystem) {
                window.tuningSystem.openTuningPanel(vehicleId, vehicleName);
            } else {
                console.error('❌ Tuning system not loaded');
            }
        };

        option.appendChild(tuneBtn);

        // Add tune indicator if needed
        updateTuneIndicator(option);
    });
}

function updateTuneIndicator(option) {
    if (!window.tuningSystem) return;

    const vehicleId = option.dataset.vehicleId;
    if (!vehicleId) return;

    const tune = window.tuningSystem.getTune(vehicleId);
    const isTuned = tune.engine !== 'stock' || tune.tires !== 'street' ||
        tune.aero !== 'stock' || tune.weight !== 'stock' ||
        tune.transmission !== 'stock' || tune.boostPressure !== 1.0 ||
        tune.nitrousOxide;

    // Remove existing indicator
    const existingIndicator = option.querySelector('.tune-indicator');
    if (existingIndicator) existingIndicator.remove();

    // Add if tuned
    if (isTuned) {
        const indicator = document.createElement('div');
        indicator.className = 'tune-indicator';
        indicator.innerHTML = '⚡';
        indicator.title = 'Vehicle is tuned';
        option.appendChild(indicator);
    }
}

// Listen for tune updates
window.addEventListener('tuneUpdated', (e) => {
    const vehicleId = e.detail.vehicleId;
    const vehicleOption = document.querySelector(`.vehicle-option[data-vehicle-id="${vehicleId}"]`);
    if (vehicleOption) {
        updateTuneIndicator(vehicleOption);
    }
});

// Export for use
window.addTuningButtons = addTuningButtons;
window.updateTuneIndicator = updateTuneIndicator;

console.log('✅ Tuning integration ready');