/**
 * F1 Race Track Map
 * Renders circuit layout and animates car positions in real-time
 */

const MAP_CONFIG = {
    padding: 40,
    circuitLineWidth: 3,
    carRadius: 8,
    drsZoneColor: 'rgba(0, 255, 0, 0.1)',
    trackColor: '#333',
    gridColor: 'rgba(0, 212, 255, 0.05)',
};

let mapState = {
    svg: null,
    cars: {},
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    trackPath: null,
};

// ============================================================================
// MAP INITIALIZATION
// ============================================================================

function initializeMap() {
    const container = document.getElementById('track-map');
    
    // Create SVG
    mapState.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    mapState.svg.setAttribute('width', container.offsetWidth);
    mapState.svg.setAttribute('height', container.offsetHeight);
    mapState.svg.setAttribute('viewBox', `0 0 ${container.offsetWidth} ${container.offsetHeight}`);
    
    container.appendChild(mapState.svg);
    
    // Draw grid background
    drawGrid();
    
    // Draw a simple circular track (Monaco-style)
    drawCircuit();
    
    // Add resize listener
    window.addEventListener('resize', () => {
        const newWidth = container.offsetWidth;
        const newHeight = container.offsetHeight;
        mapState.svg.setAttribute('width', newWidth);
        mapState.svg.setAttribute('height', newHeight);
        mapState.svg.setAttribute('viewBox', `0 0 ${newWidth} ${newHeight}`);
    });
}

function drawGrid() {
    const width = mapState.svg.getAttribute('width');
    const height = mapState.svg.getAttribute('height');
    
    const spacing = 50;
    for (let x = 0; x < width; x += spacing) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x);
        line.setAttribute('y1', 0);
        line.setAttribute('x2', x);
        line.setAttribute('y2', height);
        line.setAttribute('stroke', MAP_CONFIG.gridColor);
        line.setAttribute('stroke-width', '1');
        mapState.svg.appendChild(line);
    }
    for (let y = 0; y < height; y += spacing) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', 0);
        line.setAttribute('y1', y);
        line.setAttribute('x2', width);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', MAP_CONFIG.gridColor);
        line.setAttribute('stroke-width', '1');
        mapState.svg.appendChild(line);
    }
}

function drawCircuit() {
    const width = parseInt(mapState.svg.getAttribute('width'));
    const height = parseInt(mapState.svg.getAttribute('height'));
    
    const centerX = width / 2;
    const centerY = height / 2;
    const innerRadius = Math.min(width, height) / 4;
    const outerRadius = innerRadius + 30;
    
    // Outer track boundary
    const outerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    outerCircle.setAttribute('cx', centerX);
    outerCircle.setAttribute('cy', centerY);
    outerCircle.setAttribute('r', outerRadius);
    outerCircle.setAttribute('fill', 'none');
    outerCircle.setAttribute('stroke', MAP_CONFIG.trackColor);
    outerCircle.setAttribute('stroke-width', MAP_CONFIG.circuitLineWidth);
    mapState.svg.appendChild(outerCircle);
    
    // Inner track boundary
    const innerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    innerCircle.setAttribute('cx', centerX);
    innerCircle.setAttribute('cy', centerY);
    innerCircle.setAttribute('r', innerRadius);
    innerCircle.setAttribute('fill', 'none');
    innerCircle.setAttribute('stroke', MAP_CONFIG.trackColor);
    innerCircle.setAttribute('stroke-width', MAP_CONFIG.circuitLineWidth);
    mapState.svg.appendChild(innerCircle);
    
    // DRS zone indicator (top straight)
    const drsZone = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    drsZone.setAttribute('x', centerX - 15);
    drsZone.setAttribute('y', centerY - outerRadius - 20);
    drsZone.setAttribute('width', 30);
    drsZone.setAttribute('height', 20);
    drsZone.setAttribute('fill', 'rgba(0, 255, 0, 0.15)');
    drsZone.setAttribute('stroke', 'rgba(0, 255, 0, 0.4)');
    drsZone.setAttribute('stroke-width', '1');
    mapState.svg.appendChild(drsZone);
    
    const drsLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    drsLabel.setAttribute('x', centerX);
    drsLabel.setAttribute('y', centerY - outerRadius - 28);
    drsLabel.setAttribute('text-anchor', 'middle');
    drsLabel.setAttribute('fill', '#00ff00');
    drsLabel.setAttribute('font-size', '10');
    drsLabel.textContent = 'DRS';
    mapState.svg.appendChild(drsLabel);
    
    // Start/finish line
    const finishLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    finishLine.setAttribute('x1', centerX - 20);
    finishLine.setAttribute('y1', centerY - innerRadius);
    finishLine.setAttribute('x2', centerX + 20);
    finishLine.setAttribute('y2', centerY - innerRadius);
    finishLine.setAttribute('stroke', '#ff1a1a');
    finishLine.setAttribute('stroke-width', '3');
    finishLine.setAttribute('stroke-dasharray', '5,5');
    mapState.svg.appendChild(finishLine);
    
    // Pit lane (indicator)
    const pitLane = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    pitLane.setAttribute('x', centerX + outerRadius + 20);
    pitLane.setAttribute('y', centerY);
    pitLane.setAttribute('fill', '#ffaa00');
    pitLane.setAttribute('font-size', '10');
    pitLane.textContent = '🔧 PIT';
    mapState.svg.appendChild(pitLane);
    
    mapState.trackPath = { centerX, centerY, innerRadius, outerRadius };
}

// ============================================================================
// REDRAW FOR CIRCUIT SELECTION
// ============================================================================

function redrawCircuitMap(circuit) {
    // Remove all SVG elements except grid (keep first N grid lines)
    // We need to remove: circles, lines (finish line), rects (DRS zone), text (DRS/PIT labels)
    if (!mapState.svg) return;
    
    const elementsToRemove = [];
    mapState.svg.querySelectorAll('circle:not(.car-marker), line:not([stroke="#333"]), rect, text:not([data-driver])').forEach(el => {
        // Don't remove grid lines (they have gridColor pattern)
        if (el.getAttribute('stroke') !== MAP_CONFIG.gridColor && el.tagName !== 'circle') {
            elementsToRemove.push(el);
        } else if (el.tagName === 'circle' && el.getAttribute('stroke') === MAP_CONFIG.trackColor) {
            elementsToRemove.push(el);
        }
    });
    
    elementsToRemove.forEach(el => el.remove());
    
    // Redraw the circuit
    drawCircuit();
    
    // Optionally update circuit info if available
    console.log(`Circuit map redrawn for: ${circuit.name || 'unknown circuit'}`);
}

// ============================================================================
// CAR RENDERING & ANIMATION
// ============================================================================

function updateCarPosition(driver, position, team) {
    const { centerX, centerY, innerRadius, outerRadius } = mapState.trackPath;
    const trackRadius = (outerRadius + innerRadius) / 2;
    
    // position: 0.0 - 1.0 (normalized track position)
    const angle = (position * 2 * Math.PI) - Math.PI / 2;
    
    const x = centerX + trackRadius * Math.cos(angle);
    const y = centerY + trackRadius * Math.sin(angle);
    
    // Get or create car marker
    let carMarker = mapState.cars[driver];
    
    if (!carMarker) {
        // Create new car element
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('data-driver', driver);
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', MAP_CONFIG.carRadius);
        circle.setAttribute('fill', getTeamColor(team));
        circle.classList.add('car-marker');
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('font-size', '8');
        label.setAttribute('fill', 'white');
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('dy', '0.3em');
        label.textContent = driver.split(' ')[1].substring(0, 3).toUpperCase();
        
        group.appendChild(circle);
        group.appendChild(label);
        mapState.svg.appendChild(group);
        
        carMarker = { group, circle, label };
        mapState.cars[driver] = carMarker;
    }
    
    // Update position with smooth animation
    carMarker.group.setAttribute('transform', `translate(${x}, ${y})`);
}

function getTeamColor(team) {
    const colors = {
        'Red Bull Racing': '#0600ef',
        'Ferrari': '#dc0000',
        'McLaren': '#ff8700',
        'Mercedes': '#00d2be',
        'Aston Martin': '#006f62',
        'Alpine': '#0082fa',
        'Williams': '#005aff',
        'Haas F1 Team': '#ffffff',
        'Racing Bulls': '#5e8faa',
        'Kick Sauber': '#c8102e',
    };
    return colors[team] || '#888';
}

function setLeader(driver) {
    // Remove previous leader styling
    document.querySelectorAll('.car-marker.leader').forEach(el => {
        el.classList.remove('leader');
    });
    
    // Add leader styling to current leader
    if (mapState.cars[driver]) {
        mapState.cars[driver].circle.classList.add('leader');
    }
}

// ============================================================================
// EXPORT FOR EXTERNAL USE
// ============================================================================

window.trackMapAPI = {
    init: initializeMap,
    updateCar: updateCarPosition,
    setLeader: setLeader,
    redraw: redrawCircuitMap,
};
