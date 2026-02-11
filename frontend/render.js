export class RaceRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Minimalistic brand colors
        this.vehicleColors = {
            'koenigsegg': '#FFD700',
            'bugatti': '#0066FF',
            'hennessey': '#FF0066',
            'default': '#00FF9D'
        };
    }

    resizeCanvas() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    clear() {
        this.ctx.fillStyle = '#0D0D0D';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    render(vehicleStates, maxDistance = 450) {
        this.clear();

        if (!vehicleStates || vehicleStates.length === 0) {
            this.drawEmptyState();
            return;
        }

        const trackLength = maxDistance + 50; // Add buffer

        // Draw track
        this.drawMinimalistTrack(trackLength, vehicleStates.length);

        // Draw distance markers
        this.drawDistanceMarkers(trackLength);

        // Draw vehicles
        vehicleStates.forEach((state, index) => {
            this.drawMinimalistVehicle(state, index, trackLength, vehicleStates.length);
        });
    }

    drawEmptyState() {
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.font = '14px Inter';
        this.ctx.fillText('Select vehicles and start simulation', this.canvas.width / 2, this.canvas.height / 2);
    }

    drawMinimalistTrack(maxDistance, numVehicles) {
        const trackY = this.canvas.height / 2;
        const laneHeight = 50;
        const totalHeight = laneHeight * numVehicles;
        const startY = trackY - (totalHeight / 2);

        // Draw subtle lanes
        for (let i = 0; i < numVehicles; i++) {
            const y = startY + (i * laneHeight);

            // Lane background
            this.ctx.fillStyle = i % 2 === 0 ? 'rgba(255, 255, 255, 0.01)' : 'rgba(255, 255, 255, 0.02)';
            this.ctx.fillRect(0, y, this.canvas.width, laneHeight);

            // Lane separator
            if (i > 0) {
                this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
                this.ctx.lineWidth = 1;
                this.ctx.beginPath();
                this.ctx.moveTo(0, y);
                this.ctx.lineTo(this.canvas.width, y);
                this.ctx.stroke();
            }
        }

        // Starting line
        const startLineX = 60;
        this.ctx.strokeStyle = '#00FF9D';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(startLineX, startY);
        this.ctx.lineTo(startLineX, startY + totalHeight);
        this.ctx.stroke();

        // Start label
        this.ctx.fillStyle = '#00FF9D';
        this.ctx.font = '600 11px Inter';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('START', startLineX, startY - 15);
    }

    drawDistanceMarkers(maxDistance) {
        // Dynamic markers based on race distance
        let markers = [];
        
        if (maxDistance <= 500) {
            // Quarter mile
            markers = [
                { distance: 100, label: '100m', primary: false },
                { distance: 200, label: '200m', primary: false },
                { distance: 300, label: '300m', primary: false },
                { distance: 402.336, label: '1/4 Mile', primary: true }
            ];
        } else if (maxDistance <= 900) {
            // Half mile
            markers = [
                { distance: 200, label: '200m', primary: false },
                { distance: 402.336, label: '1/4 Mile', primary: false },
                { distance: 600, label: '600m', primary: false },
                { distance: 804.672, label: '1/2 Mile', primary: true }
            ];
        } else if (maxDistance <= 2000) {
            // One mile
            markers = [
                { distance: 402.336, label: '1/4 Mile', primary: false },
                { distance: 804.672, label: '1/2 Mile', primary: false },
                { distance: 1207, label: '3/4 Mile', primary: false },
                { distance: 1609.344, label: '1 Mile', primary: true }
            ];
        } else {
            // Top speed (5km+)
            markers = [
                { distance: 1000, label: '1km', primary: false },
                { distance: 2000, label: '2km', primary: false },
                { distance: 3000, label: '3km', primary: false },
                { distance: 4000, label: '4km', primary: false },
                { distance: 5000, label: '5km', primary: true }
            ];
        }

        const padding = 60;
        const usableWidth = this.canvas.width - padding * 2;
        const scale = usableWidth / maxDistance;

        markers.forEach(marker => {
            if (marker.distance <= maxDistance) {
                const x = padding + (marker.distance * scale);
                const y = this.canvas.height / 2;
                const height = 120;

                // Marker line
                this.ctx.strokeStyle = marker.primary
                    ? 'rgba(0, 255, 157, 0.3)'
                    : 'rgba(255, 255, 255, 0.1)';
                this.ctx.lineWidth = marker.primary ? 2 : 1;
                this.ctx.setLineDash(marker.primary ? [] : [4, 4]);
                this.ctx.beginPath();
                this.ctx.moveTo(x, y - height);
                this.ctx.lineTo(x, y + height);
                this.ctx.stroke();
                this.ctx.setLineDash([]);

                // Label
                this.ctx.fillStyle = marker.primary
                    ? '#00FF9D'
                    : 'rgba(255, 255, 255, 0.4)';
                this.ctx.font = marker.primary
                    ? '600 11px Inter'
                    : '500 10px Inter';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(marker.label, x, y - height - 10);
            }
        });
    }

    drawMinimalistVehicle(state, index, maxDistance, totalVehicles) {
        const padding = 60;
        const usableWidth = this.canvas.width - padding * 2;
        const scale = usableWidth / maxDistance;
        const x = padding + (state.distance * scale);

        const laneHeight = 50;
        const totalHeight = laneHeight * totalVehicles;
        const trackCenterY = this.canvas.height / 2;
        const startY = trackCenterY - (totalHeight / 2);
        const y = startY + (index * laneHeight) + (laneHeight / 2);

        // Determine color based on vehicle name
        const brandId = this.getBrandId(state.name);
        const color = this.vehicleColors[brandId] || this.vehicleColors.default;

        // Vehicle dimensions
        const carWidth = 60;
        const carHeight = 24;

        // Glow effect
        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = color;

        // Main body - rounded rectangle
        this.ctx.fillStyle = color;
        this.roundRect(x - carWidth / 2, y - carHeight / 2, carWidth, carHeight, 4);
        this.ctx.fill();

        // Reset shadow
        this.ctx.shadowBlur = 0;

        // Windshield
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        this.roundRect(x - carWidth / 2 + 8, y - carHeight / 2 + 4, 16, 8, 2);
        this.ctx.fill();

        // Wheels (simplified)
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        const wheelWidth = 6;
        const wheelHeight = 3;
        this.ctx.fillRect(x - carWidth / 2 + 8, y - carHeight / 2 - 1, wheelWidth, wheelHeight);
        this.ctx.fillRect(x + carWidth / 2 - 14, y - carHeight / 2 - 1, wheelWidth, wheelHeight);
        this.ctx.fillRect(x - carWidth / 2 + 8, y + carHeight / 2 - 2, wheelWidth, wheelHeight);
        this.ctx.fillRect(x + carWidth / 2 - 14, y + carHeight / 2 - 2, wheelWidth, wheelHeight);

        // Speed indicator
        const speedKmh = Math.round(state.velocity * 3.6);

        // Speed label above car
        this.ctx.fillStyle = color;
        this.ctx.font = '600 12px Inter';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`${speedKmh} km/h`, x, y - carHeight / 2 - 12);

        // Motion blur effect for high speeds
        if (speedKmh > 50) {
            const intensity = Math.min(speedKmh / 300, 1);
            const numLines = Math.floor(3 * intensity);

            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 1.5;
            this.ctx.globalAlpha = 0.2 * intensity;

            for (let i = 0; i < numLines; i++) {
                const lineX = x - carWidth / 2 - 8 - (i * 6);
                const lineLength = 10 + (i * 2);

                this.ctx.beginPath();
                this.ctx.moveTo(lineX, y - 6);
                this.ctx.lineTo(lineX - lineLength, y - 6);
                this.ctx.stroke();

                this.ctx.beginPath();
                this.ctx.moveTo(lineX, y + 6);
                this.ctx.lineTo(lineX - lineLength, y + 6);
                this.ctx.stroke();
            }

            this.ctx.globalAlpha = 1;
        }
    }

    roundRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
    }

    getBrandId(vehicleName) {
        const name = vehicleName.toLowerCase();
        if (name.includes('koenigsegg')) return 'koenigsegg';
        if (name.includes('bugatti')) return 'bugatti';
        if (name.includes('hennessey')) return 'hennessey';
        return 'default';
    }
}