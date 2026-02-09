export class RaceRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Colors for different vehicles
        this.vehicleColors = [
            '#00ff88',
            '#00d4ff',
            '#ff0080',
            '#ffaa00'
        ];
    }

    resizeCanvas() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    clear() {
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    render(vehicleStates) {
        this.clear();

        if (!vehicleStates || vehicleStates.length === 0) {
            this.drawStartingLine();
            return;
        }

        // Use quarter mile (402.336m) as the full track length for zoomed out view
        const trackLength = 450; // Show slightly more than quarter mile

        // Draw track
        this.drawTrack(trackLength);

        // Draw vehicles
        vehicleStates.forEach((state, index) => {
            this.drawVehicle(state, index, trackLength);
        });

        // Draw distance markers
        this.drawDistanceMarkers(trackLength);
    }

    drawTrack(maxDistance) {
        const trackY = this.canvas.height / 2;
        const laneHeight = 60;
        const numLanes = 4;

        // Draw lanes
        for (let i = 0; i < numLanes; i++) {
            const y = trackY - (laneHeight * (numLanes / 2)) + (i * laneHeight);

            // Lane background
            this.ctx.fillStyle = 'rgba(255,255,255,0.02)';
            this.ctx.fillRect(0, y, this.canvas.width, laneHeight);

            // Lane dividers
            this.ctx.strokeStyle = 'rgba(255,255,255,0.1)';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([20, 10]);
            this.ctx.beginPath();
            this.ctx.moveTo(0, y + laneHeight);
            this.ctx.lineTo(this.canvas.width, y + laneHeight);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
    }

    drawStartingLine() {
        const x = 50;
        const startY = this.canvas.height / 2 - 120;
        const endY = this.canvas.height / 2 + 120;

        // Starting line
        this.ctx.strokeStyle = '#00ff88';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(x, startY);
        this.ctx.lineTo(x, endY);
        this.ctx.stroke();

        // Checkered pattern
        const checkSize = 15;
        for (let y = startY; y < endY; y += checkSize) {
            for (let i = 0; i < 2; i++) {
                if ((Math.floor((y - startY) / checkSize) + i) % 2 === 0) {
                    this.ctx.fillStyle = '#ffffff';
                } else {
                    this.ctx.fillStyle = '#000000';
                }
                this.ctx.fillRect(x - checkSize * (i + 1), y, checkSize, checkSize);
            }
        }

        // "START" label
        this.ctx.fillStyle = '#00ff88';
        this.ctx.font = 'bold 16px "Segoe UI"';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('START', x, startY - 10);
    }

    drawDistanceMarkers(maxDistance) {
        const markers = [
            { distance: 100, label: '100m' },
            { distance: 200, label: '200m' },
            { distance: 300, label: '300m' },
            { distance: 402.336, label: '1/4 Mile' }
        ];

        const padding = 50;
        const usableWidth = this.canvas.width - padding * 2;
        const scale = usableWidth / maxDistance;

        markers.forEach(marker => {
            if (marker.distance <= maxDistance) {
                const x = padding + (marker.distance * scale);
                const y = this.canvas.height / 2;

                // Marker line
                this.ctx.strokeStyle = marker.distance === 402.336 ?
                    'rgba(0,255,136,0.5)' : 'rgba(255,255,255,0.3)';
                this.ctx.lineWidth = marker.distance === 402.336 ? 3 : 2;
                this.ctx.setLineDash([5, 5]);
                this.ctx.beginPath();
                this.ctx.moveTo(x, y - 150);
                this.ctx.lineTo(x, y + 150);
                this.ctx.stroke();
                this.ctx.setLineDash([]);

                // Label
                this.ctx.fillStyle = marker.distance === 402.336 ?
                    '#00ff88' : 'rgba(255,255,255,0.6)';
                this.ctx.font = marker.distance === 402.336 ?
                    'bold 14px "Segoe UI"' : '12px "Segoe UI"';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(marker.label, x, y - 160);
            }
        });
    }

    drawVehicle(state, index, maxDistance) {
        const padding = 50;
        const usableWidth = this.canvas.width - padding * 2;
        const scale = usableWidth / maxDistance;
        const x = padding + (state.distance * scale);

        const laneHeight = 60;
        const numLanes = 4;
        const trackCenterY = this.canvas.height / 2;
        const laneIndex = index % numLanes;
        const y = trackCenterY - (laneHeight * (numLanes / 2)) + (laneIndex * laneHeight) + (laneHeight / 2);

        const color = this.vehicleColors[index % this.vehicleColors.length];

        // Vehicle body
        const carWidth = 50;
        const carHeight = 28;

        // Glow effect
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = color;

        // Car body
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x - carWidth / 2, y - carHeight / 2, carWidth, carHeight);

        // Reset shadow
        this.ctx.shadowBlur = 0;

        // Car details
        this.ctx.fillStyle = 'rgba(0,0,0,0.5)';
        this.ctx.fillRect(x - carWidth / 2 + 5, y - carHeight / 2 + 5, 18, 7); // Windshield

        // Wheels
        this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
        this.ctx.fillRect(x - carWidth / 2 + 5, y - carHeight / 2 - 2, 8, 4);
        this.ctx.fillRect(x + carWidth / 2 - 13, y - carHeight / 2 - 2, 8, 4);
        this.ctx.fillRect(x - carWidth / 2 + 5, y + carHeight / 2 - 2, 8, 4);
        this.ctx.fillRect(x + carWidth / 2 - 13, y + carHeight / 2 - 2, 8, 4);

        // Vehicle name label
        this.ctx.fillStyle = color;
        this.ctx.font = 'bold 11px "Segoe UI"';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(state.name, x, y - carHeight / 2 - 10);

        // Speed and gear label
        const speedKmh = Math.round(state.velocity * 3.6);
        this.ctx.fillStyle = 'rgba(255,255,255,0.9)';
        this.ctx.font = 'bold 10px "Segoe UI"';
        this.ctx.fillText(`${speedKmh} km/h | Gear ${state.gear}`, x, y + carHeight / 2 + 15);

        // Motion lines (when moving fast)
        if (speedKmh > 50) {
            const numLines = Math.min(5, Math.floor(speedKmh / 50));
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 2;
            this.ctx.globalAlpha = 0.3;

            for (let i = 0; i < numLines; i++) {
                const lineX = x - carWidth / 2 - 10 - (i * 8);
                this.ctx.beginPath();
                this.ctx.moveTo(lineX, y - 10);
                this.ctx.lineTo(lineX - 12, y - 10);
                this.ctx.stroke();

                this.ctx.beginPath();
                this.ctx.moveTo(lineX, y + 10);
                this.ctx.lineTo(lineX - 12, y + 10);
                this.ctx.stroke();
            }

            this.ctx.globalAlpha = 1;
        }
    }
}