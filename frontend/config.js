// ==========================================
// API CONFIGURATION
// ==========================================

const CONFIG = {
    // Same-origin is the secure default when the frontend is served by FastAPI.
    // Set API_BASE_URL only when the API is hosted separately.
    API_BASE_URL: (() => {
        const configured = window.__HYPERCAR_API_BASE_URL__;
        if (typeof configured === 'string' && configured.trim()) {
            return configured.trim().replace(/\/$/, '');
        }

        if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
            return window.location.origin;
        }

        return 'http://localhost:8000';
    })(),

    endpoints: {
        vehicles: '/api/vehicles',
        simulate: '/api/simulate/drag',
        health: '/api/health',
        reload: '/api/reload'
    },

    getEndpoint(endpoint) {
        const path = this.endpoints[endpoint];
        if (!path) {
            throw new Error(`Unknown API endpoint: ${endpoint}`);
        }
        return `${this.API_BASE_URL}${path}`;
    },

    async fetchAPI(endpoint, options = {}) {
        const url = this.getEndpoint(endpoint);
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            let detail = `HTTP error! status: ${response.status}`;
            try {
                const body = await response.json();
                if (typeof body.detail === 'string') {
                    detail = body.detail;
                }
            } catch (_) {
                // Preserve the status-based error when the response is not JSON.
            }
            const error = new Error(detail);
            error.status = response.status;
            throw error;
        }

        return response.json();
    }
};

window.CONFIG = CONFIG;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
