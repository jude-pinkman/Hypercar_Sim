/**
 * circuit-map.js
 * F1 TV-style live circuit map renderer for Albert Park, Melbourne.
 * Drop into frontend/ alongside render.js and include before circuits-rt.js.
 *
 * Usage:
 *   const renderer = new CircuitMapRenderer('race-canvas');
 *   renderer.render(raceState);
 */

'use strict';

// ---------------------------------------------------------------------------
// Albert Park centerline points (scaled to ~660×500 canvas area)
// Generated from Melbourne.csv (x_m, y_m columns → pixel coords)
// ---------------------------------------------------------------------------
const albertParkPoints = [{"x":301.7,"y":134.4},{"x":297.2,"y":138.8},{"x":292.6,"y":143.1},{"x":288.1,"y":147.5},{"x":283.6,"y":151.8},{"x":279.1,"y":156.2},{"x":274.5,"y":160.6},{"x":270.0,"y":164.9},{"x":265.5,"y":169.3},{"x":260.9,"y":173.6},{"x":256.4,"y":178.0},{"x":251.8,"y":182.3},{"x":247.3,"y":186.6},{"x":242.7,"y":190.9},{"x":238.2,"y":195.3},{"x":234.3,"y":200.1},{"x":235.8,"y":206.0},{"x":238.1,"y":211.8},{"x":239.4,"y":218.0},{"x":239.3,"y":224.2},{"x":238.0,"y":230.4},{"x":235.4,"y":236.1},{"x":231.6,"y":241.1},{"x":227.0,"y":245.3},{"x":222.3,"y":249.5},{"x":217.7,"y":253.7},{"x":213.0,"y":258.0},{"x":208.4,"y":262.3},{"x":203.9,"y":266.6},{"x":199.5,"y":271.1},{"x":195.2,"y":275.7},{"x":191.1,"y":280.4},{"x":187.0,"y":285.2},{"x":182.9,"y":290.0},{"x":178.9,"y":294.8},{"x":174.9,"y":299.7},{"x":171.1,"y":304.7},{"x":167.5,"y":309.8},{"x":164.2,"y":315.2},{"x":160.9,"y":320.5},{"x":157.6,"y":325.9},{"x":154.4,"y":331.3},{"x":151.1,"y":336.7},{"x":148.1,"y":342.1},{"x":145.9,"y":348.0},{"x":149.3,"y":352.7},{"x":155.5,"y":353.9},{"x":161.6,"y":355.5},{"x":167.8,"y":356.8},{"x":173.9,"y":358.1},{"x":179.3,"y":361.1},{"x":181.2,"y":367.0},{"x":180.7,"y":373.2},{"x":180.3,"y":379.5},{"x":179.8,"y":385.8},{"x":179.3,"y":392.0},{"x":179.0,"y":398.3},{"x":179.0,"y":404.6},{"x":178.8,"y":410.9},{"x":179.9,"y":416.8},{"x":184.5,"y":421.1},{"x":189.4,"y":425.0},{"x":194.3,"y":428.9},{"x":199.3,"y":432.7},{"x":204.3,"y":436.5},{"x":209.5,"y":440.2},{"x":214.8,"y":443.5},{"x":220.4,"y":446.3},{"x":226.2,"y":448.7},{"x":232.1,"y":451.0},{"x":237.9,"y":453.3},{"x":243.7,"y":455.7},{"x":249.4,"y":458.2},{"x":255.0,"y":461.1},{"x":260.5,"y":464.3},{"x":265.6,"y":467.9},{"x":271.2,"y":469.7},{"x":275.8,"y":465.4},{"x":280.9,"y":461.8},{"x":286.5,"y":458.9},{"x":292.2,"y":456.3},{"x":298.4,"y":455.6},{"x":304.7,"y":455.4},{"x":311.0,"y":454.7},{"x":317.0,"y":453.3},{"x":322.9,"y":451.0},{"x":328.4,"y":448.0},{"x":333.5,"y":444.3},{"x":338.2,"y":440.1},{"x":342.3,"y":435.3},{"x":345.7,"y":430.1},{"x":348.3,"y":424.3},{"x":350.1,"y":418.3},{"x":351.5,"y":412.2},{"x":352.7,"y":406.1},{"x":354.0,"y":399.9},{"x":355.3,"y":393.7},{"x":356.5,"y":387.6},{"x":357.8,"y":381.4},{"x":359.1,"y":375.3},{"x":360.5,"y":369.2},{"x":362.0,"y":363.0},{"x":363.2,"y":356.9},{"x":360.4,"y":352.0},{"x":354.3,"y":350.3},{"x":348.8,"y":347.4},{"x":344.1,"y":343.3},{"x":341.8,"y":337.4},{"x":340.5,"y":331.3},{"x":339.4,"y":325.1},{"x":338.5,"y":318.9},{"x":337.4,"y":312.7},{"x":336.4,"y":306.5},{"x":335.5,"y":300.3},{"x":334.6,"y":294.1},{"x":334.2,"y":287.8},{"x":334.2,"y":281.5},{"x":334.7,"y":275.3},{"x":335.7,"y":269.1},{"x":336.9,"y":262.9},{"x":338.6,"y":256.8},{"x":340.8,"y":250.9},{"x":343.4,"y":245.2},{"x":346.3,"y":239.7},{"x":349.6,"y":234.3},{"x":353.2,"y":229.2},{"x":357.1,"y":224.3},{"x":361.5,"y":219.8},{"x":366.2,"y":215.5},{"x":371.0,"y":211.5},{"x":375.9,"y":207.6},{"x":380.7,"y":203.5},{"x":385.5,"y":199.4},{"x":390.2,"y":195.3},{"x":395.1,"y":191.4},{"x":401.1,"y":189.7},{"x":407.3,"y":190.5},{"x":413.5,"y":191.3},{"x":419.7,"y":192.3},{"x":425.9,"y":193.4},{"x":431.6,"y":191.7},{"x":436.3,"y":187.5},{"x":441.2,"y":183.5},{"x":446.1,"y":179.6},{"x":451.0,"y":175.6},{"x":455.9,"y":171.7},{"x":460.7,"y":167.6},{"x":465.4,"y":163.5},{"x":470.3,"y":159.6},{"x":475.0,"y":155.4},{"x":479.7,"y":151.2},{"x":483.8,"y":146.5},{"x":487.4,"y":141.3},{"x":490.5,"y":135.9},{"x":492.7,"y":130.0},{"x":494.6,"y":124.0},{"x":496.5,"y":118.0},{"x":498.3,"y":112.0},{"x":500.2,"y":106.0},{"x":502.1,"y":100.0},{"x":503.9,"y":94.0},{"x":505.7,"y":88.0},{"x":507.4,"y":81.9},{"x":508.9,"y":75.8},{"x":510.4,"y":69.7},{"x":511.9,"y":63.6},{"x":513.3,"y":57.5},{"x":513.8,"y":51.4},{"x":508.0,"y":48.9},{"x":502.2,"y":46.6},{"x":496.3,"y":44.3},{"x":490.5,"y":42.0},{"x":484.7,"y":39.7},{"x":478.8,"y":37.4},{"x":473.0,"y":35.0},{"x":467.2,"y":32.5},{"x":461.3,"y":30.4},{"x":455.1,"y":30.3},{"x":449.4,"y":33.0},{"x":444.9,"y":37.3},{"x":441.7,"y":42.7},{"x":438.5,"y":48.1},{"x":435.3,"y":53.5},{"x":432.2,"y":59.0},{"x":429.0,"y":64.4},{"x":425.7,"y":69.7},{"x":422.4,"y":75.0},{"x":418.7,"y":80.2},{"x":413.2,"y":79.7},{"x":409.1,"y":74.9},{"x":405.1,"y":70.1},{"x":401.1,"y":65.2},{"x":396.7,"y":60.8},{"x":390.9,"y":58.3},{"x":384.7,"y":58.2},{"x":379.0,"y":60.6},{"x":374.1,"y":64.6},{"x":369.5,"y":68.9},{"x":365.0,"y":73.3},{"x":360.5,"y":77.7},{"x":356.0,"y":82.1},{"x":351.5,"y":86.5},{"x":347.0,"y":90.8},{"x":342.5,"y":95.2},{"x":337.9,"y":99.5},{"x":333.4,"y":103.9},{"x":328.9,"y":108.3},{"x":324.3,"y":112.6},{"x":319.8,"y":117.0},{"x":315.3,"y":121.3},{"x":310.7,"y":125.7},{"x":306.2,"y":130.0}];

// ---------------------------------------------------------------------------
// Sector boundary indices (approximate, based on Melbourne layout)
// Sector 1: Turn 1-5, Sector 2: Turn 6-12, Sector 3: Turn 13-16
// ---------------------------------------------------------------------------
const SECTOR_BOUNDARIES = {
  s1Start: 0,
  s2Start: Math.floor(albertParkPoints.length * 0.30),  // ~30%
  s3Start: Math.floor(albertParkPoints.length * 0.63),  // ~63%
};

// Speed trap approximate location (back straight, ~85% through lap)
const SPEED_TRAP_IDX = Math.floor(albertParkPoints.length * 0.85);

// ---------------------------------------------------------------------------
// Sector color highlights (subtle overlay on track)
// ---------------------------------------------------------------------------
const SECTOR_COLORS = {
  s1: 'rgba(255, 40, 40, 0.55)',   // red
  s2: 'rgba(40, 200, 255, 0.55)',  // blue
  s3: 'rgba(80, 255, 80, 0.55)',   // green
};

// ---------------------------------------------------------------------------
// CircuitMapRenderer
// ---------------------------------------------------------------------------
class CircuitMapRenderer {
  /**
   * @param {string} canvasId - ID of the <canvas> element
   */
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      throw new Error(`CircuitMapRenderer: canvas #${canvasId} not found`);
    }
    this.ctx = this.canvas.getContext('2d');
    this.points = albertParkPoints;

    // Pre-compute cumulative arc lengths for smooth progress interpolation
    this._arcLengths = this._computeArcLengths(this.points);
    this._totalLength = this._arcLengths[this._arcLengths.length - 1];

    // Bind resize handler
    this._onResize = this._onResize.bind(this);
    window.addEventListener('resize', this._onResize);
    this._onResize(); // initial sizing
  }

  // -------------------------------------------------------------------------
  // Resize: keep canvas crisp on high-DPI screens
  // -------------------------------------------------------------------------
  _onResize() {
    const container = this.canvas.parentElement;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width  = rect.width  * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width  = rect.width  + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // Store logical dims for drawing
    this._logicalW = rect.width;
    this._logicalH = rect.height;
  }

  // -------------------------------------------------------------------------
  // Arc-length table for uniform-speed interpolation along the centerline
  // -------------------------------------------------------------------------
  _computeArcLengths(pts) {
    const len = [0];
    for (let i = 1; i < pts.length; i++) {
      const dx = pts[i].x - pts[i-1].x;
      const dy = pts[i].y - pts[i-1].y;
      len.push(len[i-1] + Math.sqrt(dx*dx + dy*dy));
    }
    return len;
  }

  // -------------------------------------------------------------------------
  // getPositionOnTrack(progress 0→1) → {x, y}
  // Uses arc-length parameterisation so cars move at consistent pixel speed.
  // -------------------------------------------------------------------------
  getPositionOnTrack(progress) {
    // Wrap progress into [0,1)
    const p = ((progress % 1) + 1) % 1;
    const target = p * this._totalLength;

    // Binary search for segment
    let lo = 0, hi = this._arcLengths.length - 1;
    while (lo < hi - 1) {
      const mid = (lo + hi) >> 1;
      if (this._arcLengths[mid] < target) lo = mid; else hi = mid;
    }

    const segLen = this._arcLengths[hi] - this._arcLengths[lo];
    const t = segLen > 0 ? (target - this._arcLengths[lo]) / segLen : 0;

    const a = this.points[lo];
    const b = this.points[hi % this.points.length];
    return {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t
    };
  }

  // -------------------------------------------------------------------------
  // Build a transform that maps the circuit into canvas logical px, preserving aspect ratio
  // -------------------------------------------------------------------------
  _getTransform() {
    const DESIGN_W = 660, DESIGN_H = 500;
    const W = this._logicalW  || this.canvas.offsetWidth  || DESIGN_W;
    const H = this._logicalH || this.canvas.offsetHeight || DESIGN_H;
    
    // Calculate aspect ratios
    const designAspect = DESIGN_W / DESIGN_H;
    const canvasAspect = W / H;
    
    let scale, offX, offY;
    if (canvasAspect > designAspect) {
      // Canvas is wider: fit to height
      scale = H / DESIGN_H;
      offX = (W - DESIGN_W * scale) / 2;
      offY = 0;
    } else {
      // Canvas is taller: fit to width
      scale = W / DESIGN_W;
      offX = 0;
      offY = (H - DESIGN_H * scale) / 2;
    }
    
    return { scale, offX, offY };
  }

  // -------------------------------------------------------------------------
  // drawTrack() — fills lake, strokes white centerline with cyan glow
  // -------------------------------------------------------------------------
  drawTrack() {
    const ctx = this.ctx;
    const { scale, offX, offY } = this._getTransform();
    const pts = this.points;

    // Helper: map design coords → canvas coords
    const tx = x => x * scale + offX;
    const ty = y => y * scale + offY;

    // --- 1. Lake / interior fill (closed loop, dark blue) ---
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(tx(pts[0].x), ty(pts[0].y));
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(tx(pts[i].x), ty(pts[i].y));
    }
    ctx.closePath();
    ctx.fillStyle = '#012a4a';  // dark navy lake
    ctx.fill();

    // Optional: subtle lake shimmer gradient
    const grad = ctx.createRadialGradient(
      tx(270), ty(300), 20,
      tx(270), ty(300), 180 * scale
    );
    grad.addColorStop(0, 'rgba(0,80,160,0.25)');
    grad.addColorStop(1, 'rgba(0,20,60,0)');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();

    // --- 2. Sector highlight bands ---
    this._drawSectorHighlights(tx, ty, scale);

    // --- 3. Outer glow pass (wide, dim cyan) ---
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(tx(pts[0].x), ty(pts[0].y));
    for (let i = 1; i < pts.length; i++) ctx.lineTo(tx(pts[i].x), ty(pts[i].y));
    ctx.closePath();
    ctx.strokeStyle = 'rgba(0, 200, 255, 0.18)';
    ctx.lineWidth   = 26 * scale;
    ctx.lineCap     = 'round';
    ctx.lineJoin    = 'round';
    ctx.shadowColor = '#00d4ff';
    ctx.shadowBlur  = 24;
    ctx.stroke();
    ctx.restore();

    // --- 4. Main white track line ---
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(tx(pts[0].x), ty(pts[0].y));
    for (let i = 1; i < pts.length; i++) ctx.lineTo(tx(pts[i].x), ty(pts[i].y));
    ctx.closePath();
    ctx.strokeStyle = '#e8eef4';
    ctx.lineWidth   = 13 * scale;
    ctx.lineCap     = 'round';
    ctx.lineJoin    = 'round';
    ctx.shadowColor = 'rgba(255,255,255,0.4)';
    ctx.shadowBlur  = 6;
    ctx.stroke();
    ctx.restore();

    // --- 5. Start/Finish line marker ---
    this._drawStartFinish(tx, ty, scale);

    // --- 6. Static labels ---
    this._drawStaticLabels(tx, ty, scale);
  }

  // -------------------------------------------------------------------------
  // Sector highlights: colour the track segments by sector
  // -------------------------------------------------------------------------
  _drawSectorHighlights(tx, ty, scale) {
    const ctx = this.ctx;
    const pts = this.points;
    const { s1Start, s2Start, s3Start } = SECTOR_BOUNDARIES;

    const segments = [
      { from: s1Start,  to: s2Start - 1, color: SECTOR_COLORS.s1 },
      { from: s2Start,  to: s3Start - 1, color: SECTOR_COLORS.s2 },
      { from: s3Start,  to: pts.length,  color: SECTOR_COLORS.s3 },
    ];

    segments.forEach(seg => {
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(tx(pts[seg.from].x), ty(pts[seg.from].y));
      for (let i = seg.from + 1; i < seg.to; i++) {
        ctx.lineTo(tx(pts[i].x), ty(pts[i].y));
      }
      ctx.strokeStyle = seg.color;
      ctx.lineWidth   = 14 * scale;
      ctx.lineCap     = 'round';
      ctx.lineJoin    = 'round';
      ctx.stroke();
      ctx.restore();
    });
  }

  // -------------------------------------------------------------------------
  // Start/Finish line: short perpendicular tick across the track
  // -------------------------------------------------------------------------
  _drawStartFinish(tx, ty, scale) {
    const ctx = this.ctx;
    const p0 = this.points[0];
    const p1 = this.points[1];

    // Perpendicular direction
    const dx = p1.x - p0.x, dy = p1.y - p0.y;
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const hw = 10 * scale; // half-width of the tick

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(tx(p0.x + nx * hw), ty(p0.y + ny * hw));
    ctx.lineTo(tx(p0.x - nx * hw), ty(p0.y - ny * hw));
    ctx.strokeStyle = '#ff2020';
    ctx.lineWidth   = 3 * scale;
    ctx.lineCap     = 'butt';
    ctx.shadowColor = '#ff0000';
    ctx.shadowBlur  = 8;
    ctx.stroke();
    ctx.restore();

    // "S/F" label
    ctx.save();
    ctx.font         = `bold ${Math.round(9 * scale)}px 'Barlow Condensed', 'Arial Narrow', sans-serif`;
    ctx.fillStyle    = '#ff4444';
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText('S/F', tx(p0.x + nx * (hw + 4)), ty(p0.y + ny * (hw + 4)));
    ctx.restore();
  }

  // -------------------------------------------------------------------------
  // Static circuit labels: sectors + speed trap
  // -------------------------------------------------------------------------
  _drawStaticLabels(tx, ty, scale) {
    const ctx = this.ctx;
    const pts = this.points;

    const labels = [
      { idx: SECTOR_BOUNDARIES.s1Start + 8, text: 'SECTOR 1', anchor: 'right', offX: -12, offY: -12 },
      { idx: SECTOR_BOUNDARIES.s2Start + 5, text: 'SECTOR 2', anchor: 'left',  offX:  14, offY: -10 },
      { idx: SECTOR_BOUNDARIES.s3Start + 4, text: 'SECTOR 3', anchor: 'left',  offX:  14, offY:  -8 },
      { idx: SPEED_TRAP_IDX,                text: '⚡ SPEED TRAP', anchor: 'right', offX: -10, offY: -14 },
    ];

    labels.forEach(lbl => {
      const pt = pts[Math.min(lbl.idx, pts.length - 1)];
      const cx = tx(pt.x) + lbl.offX * scale;
      const cy = ty(pt.y) + lbl.offY * scale;
      const fontSize = Math.max(7, Math.round(8 * scale));

      ctx.save();
      ctx.font         = `600 ${fontSize}px 'Barlow Condensed', 'Arial Narrow', sans-serif`;
      ctx.fillStyle    = 'rgba(255,255,255,0.75)';
      ctx.textAlign    = lbl.anchor === 'right' ? 'right' : 'left';
      ctx.textBaseline = 'middle';
      ctx.shadowColor  = 'rgba(0,0,0,0.8)';
      ctx.shadowBlur   = 4;
      ctx.fillText(lbl.text, cx, cy);
      ctx.restore();
    });
  }

  // -------------------------------------------------------------------------
  // drawCar(car, transform) — colored circle + 3-letter code label
  // -------------------------------------------------------------------------
  /**
   * @param {object} car  - { progress, color, code, isLeader }
   */
  drawCar(car) {
    const { scale, offX, offY } = this._getTransform();
    const pos = this.getPositionOnTrack(car.progress);
    const ctx = this.ctx;

    const cx = pos.x * scale + offX;
    const cy = pos.y * scale + offY;
    const r  = Math.max(5, 8 * scale);

    // Outer glow ring
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r + 3, 0, Math.PI * 2);
    ctx.fillStyle    = car.color + '55';
    ctx.shadowColor  = car.color;
    ctx.shadowBlur   = 12;
    ctx.fill();
    ctx.restore();

    // Main dot
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle   = car.color;
    ctx.shadowColor = car.color;
    ctx.shadowBlur  = 8;
    ctx.fill();

    // White centre pip for visibility
    ctx.beginPath();
    ctx.arc(cx, cy, r * 0.35, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.fill();
    ctx.restore();

    // 3-letter code below dot
    const fontSize = Math.max(7, Math.round(8.5 * scale));
    ctx.save();
    ctx.font         = `bold ${fontSize}px 'Barlow Condensed', 'Arial Narrow', monospace`;
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'top';
    ctx.shadowColor  = 'rgba(0,0,0,0.9)';
    ctx.shadowBlur   = 4;
    ctx.fillStyle    = '#ffffff';
    ctx.fillText(car.code, cx, cy + r + 3);
    ctx.restore();
  }

  // -------------------------------------------------------------------------
  // render(raceState) — main entry point called each tick
  // raceState: { cars: [{id, code, color, progress, lap}], lap, totalLaps }
  // -------------------------------------------------------------------------
  render(raceState) {
    const W = this._logicalW || this.canvas.offsetWidth;
    const H = this._logicalH || this.canvas.offsetHeight;
    const ctx = this.ctx;

    // Clear
    ctx.clearRect(0, 0, W, H);

    // Draw track
    this.drawTrack();

    // Draw each car (sorted so leader renders on top)
    if (raceState && raceState.cars) {
      // Draw back-to-front (higher progress = further ahead = draw last = on top)
      const sorted = [...raceState.cars].sort((a, b) => a.progress - b.progress);
      sorted.forEach(car => this.drawCar(car));
    }
  }

  // -------------------------------------------------------------------------
  // Cleanup
  // -------------------------------------------------------------------------
  destroy() {
    window.removeEventListener('resize', this._onResize);
  }
}
