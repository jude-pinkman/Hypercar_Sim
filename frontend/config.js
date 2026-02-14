// ==========================================
// API CONFIGURATION
// Automatically detects environment
// ==========================================

const CONFIG = {
    // Determine API base URL based on environment
    API_BASE_URL: (() => {
        const hostname = window.location.hostname;

        // Local development
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }

        // Production on Render
        // Your actual backend URL
        return 'https://hypercar-sim.onrender.com';
    })(),

    // API endpoints
    endpoints: {
        vehicles: '/api/vehicles',
        simulate: '/api/simulate/drag',
        health: '/api/health',
        reload: '/api/reload'
    },

    // Helper method to build full URL
    getEndpoint(endpoint) {
        return `${this.API_BASE_URL}${this.endpoints[endpoint]}`;
    },

    // Helper to make API calls
    async fetchAPI(endpoint, options = {}) {
        const url = this.getEndpoint(endpoint);
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }
};

// Log configuration for debugging
console.log('🔧 API Configuration:', {
    baseURL: CONFIG.API_BASE_URL,
    environment: window.location.hostname === 'localhost' ? 'development' : 'production',
    endpoints: CONFIG.endpoints
});

// Make available globally
window.CONFIG = CONFIG;

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}