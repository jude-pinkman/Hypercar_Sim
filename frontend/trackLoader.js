// ==========================================
// TRACK LOADER
// Loads GeoJSON track data and renders via Leaflet
// Scalable to multiple tracks
// ==========================================

'use strict';

/**
 * Track metadata registry.
 * New tracks added here (Spa, Monza, etc.)
 */
const TRACK_ASSETS = {
    monaco: {
        trackGeoJson: 'data/Monaco_Track.geojson',
        turnsGeoJson: 'data/Monaco_Turns.geojson',
        defaultCenter: [43.7374, 7.4265],
        defaultZoom: 15
    },
    // Future tracks:
    // spa: { trackGeoJson: 'data/Spa_Track.geojson', ... }
};

/**
 * Leaflet map instance (singleton per session).
 */
let mapInstance = null;
let trackLayerGroup = null;
let turnsLayerGroup = null;

/**
 * Initialize the Leaflet map in a given container.
 * @param {string} containerId – HTML element id
 * @param {string} trackId – key in TRACK_ASSETS
 * @returns {Promise<L.Map>}
 */
async function initMap(containerId, trackId = 'monaco') {
    const assets = TRACK_ASSETS[trackId];
    if (!assets) throw new Error(`No assets registered for track: ${trackId}`);

    // Destroy previous map if re-initialising
    if (mapInstance) {
        mapInstance.remove();
        mapInstance = null;
    }

    mapInstance = L.map(containerId, {
        center: assets.defaultCenter,
        zoom: assets.defaultZoom,
        zoomControl: true,
        attributionControl: false,
        scrollWheelZoom: true,
        doubleClickZoom: false
    });

    // Dark tile layer (CartoDB dark matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap, © CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(mapInstance);

    // Layer groups
    trackLayerGroup = L.layerGroup().addTo(mapInstance);
    turnsLayerGroup = L.layerGroup().addTo(mapInstance);

    return mapInstance;
}

/**
 * Load and render a track from GeoJSON.
 * @param {string} trackId
 * @param {function} onTurnClick – callback(turnFeature)
 */
async function loadTrack(trackId = 'monaco', onTurnClick = null) {
    const assets = TRACK_ASSETS[trackId];

    // Clear previous layers
    if (trackLayerGroup) trackLayerGroup.clearLayers();
    if (turnsLayerGroup) turnsLayerGroup.clearLayers();

    // Fetch both GeoJSON files
    const [trackData, turnsData] = await Promise.all([
        fetch(assets.trackGeoJson).then(r => r.json()),
        fetch(assets.turnsGeoJson).then(r => r.json())
    ]);

    // ---- Render track line ----
    const trackLayer = L.geoJSON(trackData, {
        style: {
            color: '#00FF9D',
            weight: 4,
            opacity: 1,
            lineCap: 'round',
            lineJoin: 'round'
        }
    });
    trackLayerGroup.addLayer(trackLayer);

    // Glow effect – second slightly wider, semi-transparent line
    const glowLayer = L.geoJSON(trackData, {
        style: {
            color: '#00FF9D',
            weight: 10,
            opacity: 0.18,
            lineCap: 'round',
            lineJoin: 'round'
        }
    });
    trackLayerGroup.addLayer(glowLayer);

    // Fit map to track
    if (trackLayer.getBounds().isValid()) {
        mapInstance.fitBounds(trackLayer.getBounds(), { padding: [30, 30] });
    }

    // ---- Render turn markers ----
    turnsData.features.forEach(feature => {
        const { Turn_No, Turn_Name } = feature.properties;
        const coords = feature.geometry.coordinates; // [lng, lat]

        // Skip pit in/out markers from labeled dots
        const isPit = Turn_Name === 'PIT IN' || Turn_Name === 'PIT_OUT';

        const label = Turn_No != null ? `T${Turn_No}` : (isPit ? '⏷' : '·');
        const markerColor = isPit ? '#FF6600' : '#00FF9D';
        const bgColor = isPit ? 'rgba(255,102,0,0.18)' : 'rgba(0,255,157,0.12)';

        const icon = L.divIcon({
            className: '',
            html: `<div class="turn-marker" style="border-color:${markerColor};background:${bgColor};color:${markerColor};">${label}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });

        const marker = L.marker([coords[1], coords[0]], { icon });

        // Popup
        const popupContent = `
            <div class="turn-popup">
                <div class="turn-popup-num">${Turn_No != null ? `T${Turn_No}` : '—'}</div>
                <div class="turn-popup-name">${Turn_Name}</div>
            </div>`;
        marker.bindPopup(popupContent, {
            className: 'circuit-popup',
            closeButton: false,
            maxWidth: 200
        });

        marker.on('click', () => {
            if (onTurnClick) onTurnClick(feature);
        });

        turnsLayerGroup.addLayer(marker);
    });

    return { trackData, turnsData };
}

/**
 * Highlight a specific segment on the map (future telemetry overlay use).
 */
function highlightSegment(coords) {
    if (!mapInstance) return;
    L.polyline(coords, {
        color: '#FF0066',
        weight: 5,
        opacity: 0.9
    }).addTo(mapInstance);
}

/**
 * Get the current map instance.
 */
function getMap() {
    return mapInstance;
}

export { initMap, loadTrack, highlightSegment, getMap, TRACK_ASSETS };
