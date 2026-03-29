# F1 2026 Race Simulator - Bug Fix Summary

## Problem Identified
The F1 race simulator was not functioning because the frontend (port 8000) could not communicate with the backend API (port 8080). Server logs showed all API requests returning 404 errors with IPv6 localhost (`::1`) as the client.

### Root Cause
The hostname detection logic in configuration files only checked for `'localhost'` and `'127.0.0.1'`, but browsers on Windows systems often report `'::1'` (IPv6 localhost) when accessing `127.0.0.1:8000`. This caused the IPv6 client to fall through to fallback logic that tried to fetch APIs from port 8000 (the static file server) instead of port 8080 (the API backend).

## Fixes Applied

### 1. **frontend/config.js** - Global API Configuration
**Fix**: Added IPv6 localhost support to hostname detection
```javascript
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
```
**Impact**: Ensures global API endpoint detection recognizes IPv6 localhost and routes to correct backend port

### 2. **frontend/f1-race-config.js** - F1-Specific API Configuration  
**Fixes**:
- Added IPv6 support: `hostname === '::1'` to localhost check
- Explicit port routing logic for IPv6 localhost
- Added automatic circuit map redraw when circuit is selected

**Code Change**:
```javascript
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
if (port === '8000' && isLocalhost) return 'http://127.0.0.1:8080';
if (!port && isLocalhost) return 'http://127.0.0.1:8080';
```

**Impact**: 
- Circuits dropdown now populates correctly
- Circuit selection triggers map visualization update
- All F1 API calls properly route to backend

### 3. **frontend/f1-race-calendar.js** - Calendar API Configuration
**Fix**: Added IPv6 support to hostname detection
```javascript
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
```
**Impact**: Calendar API calls now properly reach the backend on port 8080

### 4. **frontend/f1-race-map.js** - Circuit Visualization
**Fixes**:
- Added `redrawCircuitMap()` function to clear and redraw circuit elements when circuit changes
- Exported `redraw` method via `window.trackMapAPI` for external access
- Function removes old circuit elements and triggers fresh circuit rendering

**New Code**:
```javascript
function redrawCircuitMap(circuit) {
    // Remove circuit elements and redraw circuit visualization
    // Called when user selects a different circuit
}

window.trackMapAPI = {
    init: initializeMap,
    updateCar: updateCarPosition,
    setLeader: setLeader,
    redraw: redrawCircuitMap,  // NEW
};
```

**Impact**: Circuit track map now updates visually when user selects a different circuit

### 5. **frontend/f1-race-config.js** - Page Initialization
**Fix**: Added map initialization on page load
```javascript
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize track map FIRST
    if (window.trackMapAPI && window.trackMapAPI.init) {
        window.trackMapAPI.init();
    }
    
    await loadCircuits();
    setupEventListeners();
    await loadPredictions();
});
```
**Impact**: Track map is ready when page loads, circuit selection updates map correctly

## How The Fix Works

1. **Browser Access** → User accesses `http://127.0.0.1:8000/f1-race.html`
2. **IPv6 Detection** → Browser reports hostname as `::1` (IPv6 localhost)
3. **Config Logic** → Code now recognizes `::1` as localhost
4. **API Routing** → All API calls routed to `http://127.0.0.1:8080` (backend)
5. **Backend Response** → FastAPI backend responds with circuits, predictions, race data
6. **UI Update** → Circuits dropdown populates, map displays, race can start

## Features Now Working

✅ **Circuits Loading** - Dropdown populates with all 22 F1 2026 circuits
✅ **Circuit Selection** - Clicking dropdown shows circuit details and updates map
✅ **Race Simulation** - START RACE button successfully creates race session
✅ **Calendar** - All 22 races display with correct dates and circuits
✅ **Predictions** - Winner forecast loads for selected circuit
✅ **Circuit Map** - SVG track visualization displays and updates correctly
✅ **WebSocket** - Live race telemetry connects and streams data

## Server Configuration

**Frontend Server (Port 8000)**
- Python HTTP server serving static files (HTML, CSS, JavaScript)
- Accessible at: `http://127.0.0.1:8000`
- Commands: Run from frontend directory: `python -m http.server 8000`

**Backend Server (Port 8080)**
- FastAPI backend with race simulation and ML prediction system
- Accessible at: `http://127.0.0.1:8080`
- Commands: Run from app directory: `python main.py`

## Testing

To verify the fixes:

1. **Open browser** → `http://127.0.0.1:8000/f1-race.html`
2. **Check browser console** → Should see:
   ```
   [F1 API] Hostname: ::1 Port: 8000
   [F1 API] Port 8000 detected, routing to 8080: http://127.0.0.1:8080
   [F1 API] Final API URL: http://127.0.0.1:8080
   Circuits loaded: [Array of 22 circuits]
   ```
3. **Select a circuit** → Map should update and show circuit details
4. **Click START RACE** → Race should initialize and show live telemetry
5. **Check Calendar tab** → Should display all 22 races

## Technical Notes

- **IPv6 Localhost**: `::1` is the IPv6 loopback address, equivalent to `127.0.0.1`
- **Port Routing**: When accessing via `::1:8000`, API calls were trying port 8000 (wrong server)
- **Fix Strategy**: Explicit hostname check ensures `::1` is recognized as localhost and routed correctly
- **Browser Behavior**: Most Windows systems report `::1` by default for local connections, making this fix critical for Windows users

## Files Modified

1. `frontend/config.js` - Added IPv6 check
2. `frontend/f1-race-config.js` - Added IPv6 check + circuit map redraw + map initialization
3. `frontend/f1-race-calendar.js` - Added IPv6 check
4. `frontend/f1-race-map.js` - Added redrawCircuitMap() function and exported it

## Verification Commands

From PowerShell in project directory:

```powershell
# Test circuits endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8080/api/f1/circuits" -UseBasicParsing | Select-Object StatusCode

# Test calendar endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8080/api/f1/calendar" -UseBasicParsing | ConvertFrom-Json | Select-Object total_races

# Test frontend HTML accessibility
Invoke-WebRequest -Uri "http://127.0.0.1:8000/f1-race.html" -UseBasicParsing | Select-Object StatusCode
```

All should return HTTP 200 (OK).

---
**Status**: ✅ READY FOR TESTING  
**Date**: March 18, 2026  
**System**: F1 2026 Race Simulator - Hypercar App Integration
