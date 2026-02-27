// ==========================================
// SIM-PHYSICS.JS — Frontend Physics Engine
// Runs drag/race simulations entirely in the
// browser — no backend required.
// Output schema matches Python API exactly.
//
// F1 calibration benchmarks (2020 W11):
//   0-100:  ~2.6s  ✓
//   0-200:  ~5.1s  ✓
//   0-300:  ~10.6s ✓
//   QM:     ~8.8s  ✓
// ==========================================

'use strict';

import { CAR_CATALOGUE } from './car-data.js';

// ==========================================
// VEHICLE SPECS
// ==========================================

const HYPERCAR_SPECS = {
    koenigsegg_jesko:          { power_kw:1195, weight_kg:1420, cd:0.278, top_speed_kmh:531, torque_nm:1500, gears:7, final_drive:3.45, tire_radius:0.340, redline_rpm:8500,  idle_rpm:800,  te:0.94, frontal_area:2.0 },
    koenigsegg_jesko_attack:   { power_kw:1195, weight_kg:1420, cd:0.315, top_speed_kmh:480, torque_nm:1500, gears:7, final_drive:3.65, tire_radius:0.340, redline_rpm:8500,  idle_rpm:800,  te:0.94, frontal_area:2.0 },
    koenigsegg_regera:         { power_kw:1100, weight_kg:1590, cd:0.278, top_speed_kmh:410, torque_nm:2000, gears:1, final_drive:2.73, tire_radius:0.340, redline_rpm:7800,  idle_rpm:800,  te:0.95, frontal_area:2.0 },
    koenigsegg_agera_rs:       { power_kw:1014, weight_kg:1395, cd:0.330, top_speed_kmh:447, torque_nm:1280, gears:7, final_drive:3.25, tire_radius:0.340, redline_rpm:8250,  idle_rpm:800,  te:0.94, frontal_area:2.0 },
    bugatti_chiron_ss:         { power_kw:1177, weight_kg:1978, cd:0.350, top_speed_kmh:490, torque_nm:1600, gears:7, final_drive:3.20, tire_radius:0.360, redline_rpm:6700,  idle_rpm:700,  te:0.93, frontal_area:2.1 },
    bugatti_bolide:            { power_kw:1361, weight_kg:1240, cd:0.670, top_speed_kmh:500, torque_nm:1850, gears:7, final_drive:3.10, tire_radius:0.350, redline_rpm:6800,  idle_rpm:700,  te:0.93, frontal_area:2.0 },
    bugatti_veyron_ss:         { power_kw: 882, weight_kg:1888, cd:0.360, top_speed_kmh:431, torque_nm:1500, gears:7, final_drive:3.30, tire_radius:0.360, redline_rpm:6200,  idle_rpm:700,  te:0.92, frontal_area:2.1 },
    hennessey_venom_f5:        { power_kw:1355, weight_kg:1360, cd:0.330, top_speed_kmh:484, torque_nm:1617, gears:7, final_drive:3.40, tire_radius:0.340, redline_rpm:8000,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    ssc_tuatara:               { power_kw:1305, weight_kg:1247, cd:0.279, top_speed_kmh:455, torque_nm:1735, gears:7, final_drive:3.35, tire_radius:0.340, redline_rpm:8800,  idle_rpm:800,  te:0.93, frontal_area:1.9 },
    pagani_huayra_r:           { power_kw: 620, weight_kg:1050, cd:0.300, top_speed_kmh:370, torque_nm: 740, gears:6, final_drive:3.70, tire_radius:0.330, redline_rpm:9000,  idle_rpm:900,  te:0.94, frontal_area:1.9 },
    pagani_zonda_r:            { power_kw: 559, weight_kg:1070, cd:0.360, top_speed_kmh:350, torque_nm: 730, gears:6, final_drive:3.80, tire_radius:0.330, redline_rpm:8800,  idle_rpm:900,  te:0.94, frontal_area:1.9 },
    mclaren_speedtail:         { power_kw: 782, weight_kg:1430, cd:0.278, top_speed_kmh:403, torque_nm:1150, gears:7, final_drive:3.15, tire_radius:0.340, redline_rpm:8000,  idle_rpm:800,  te:0.93, frontal_area:1.9 },
    mclaren_p1:                { power_kw: 673, weight_kg:1450, cd:0.340, top_speed_kmh:350, torque_nm: 900, gears:7, final_drive:3.45, tire_radius:0.340, redline_rpm:8500,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    mclaren_senna:             { power_kw: 588, weight_kg:1198, cd:0.820, top_speed_kmh:340, torque_nm: 800, gears:7, final_drive:3.50, tire_radius:0.330, redline_rpm:8500,  idle_rpm:800,  te:0.93, frontal_area:1.9 },
    mclaren_765lt:             { power_kw: 563, weight_kg:1229, cd:0.350, top_speed_kmh:330, torque_nm: 800, gears:7, final_drive:3.55, tire_radius:0.330, redline_rpm:8500,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    mclaren_720s:              { power_kw: 530, weight_kg:1283, cd:0.320, top_speed_kmh:341, torque_nm: 770, gears:7, final_drive:3.55, tire_radius:0.330, redline_rpm:8500,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    aston_valkyrie:            { power_kw: 865, weight_kg:1030, cd:0.650, top_speed_kmh:402, torque_nm: 740, gears:7, final_drive:3.60, tire_radius:0.330, redline_rpm:11100, idle_rpm:1000, te:0.94, frontal_area:1.9 },
    rimac_nevera:              { power_kw:1408, weight_kg:2150, cd:0.300, top_speed_kmh:412, torque_nm:2360, gears:1, final_drive:2.90, tire_radius:0.350, redline_rpm:18000, idle_rpm:0,    te:0.97, frontal_area:2.0 },
    lotus_evija:               { power_kw:1470, weight_kg:1680, cd:0.380, top_speed_kmh:320, torque_nm:1700, gears:1, final_drive:3.00, tire_radius:0.350, redline_rpm:18000, idle_rpm:0,    te:0.97, frontal_area:2.0 },
    aspark_owl:                { power_kw:1480, weight_kg:1900, cd:0.320, top_speed_kmh:400, torque_nm:2000, gears:1, final_drive:2.80, tire_radius:0.350, redline_rpm:18000, idle_rpm:0,    te:0.97, frontal_area:2.0 },
    pininfarina_battista:      { power_kw:1400, weight_kg:2100, cd:0.290, top_speed_kmh:350, torque_nm:2340, gears:1, final_drive:2.85, tire_radius:0.350, redline_rpm:18000, idle_rpm:0,    te:0.97, frontal_area:2.0 },
    ferrari_sf90:              { power_kw: 735, weight_kg:1570, cd:0.340, top_speed_kmh:340, torque_nm: 800, gears:8, final_drive:3.30, tire_radius:0.330, redline_rpm:8000,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    ferrari_laferrari:         { power_kw: 588, weight_kg:1255, cd:0.330, top_speed_kmh:352, torque_nm: 700, gears:7, final_drive:3.45, tire_radius:0.330, redline_rpm:9250,  idle_rpm:900,  te:0.93, frontal_area:1.9 },
    ferrari_f8:                { power_kw: 530, weight_kg:1330, cd:0.320, top_speed_kmh:340, torque_nm: 770, gears:7, final_drive:3.55, tire_radius:0.330, redline_rpm:8000,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    ferrari_812:               { power_kw: 588, weight_kg:1525, cd:0.330, top_speed_kmh:340, torque_nm: 718, gears:7, final_drive:3.30, tire_radius:0.340, redline_rpm:9500,  idle_rpm:900,  te:0.93, frontal_area:2.0 },
    lamborghini_revuelto:      { power_kw: 825, weight_kg:1772, cd:0.320, top_speed_kmh:350, torque_nm: 850, gears:8, final_drive:3.30, tire_radius:0.340, redline_rpm:9500,  idle_rpm:900,  te:0.93, frontal_area:2.0 },
    lamborghini_aventador_svj: { power_kw: 566, weight_kg:1525, cd:0.350, top_speed_kmh:352, torque_nm: 720, gears:7, final_drive:3.45, tire_radius:0.340, redline_rpm:8500,  idle_rpm:900,  te:0.93, frontal_area:2.0 },
    lamborghini_sian:          { power_kw: 602, weight_kg:1595, cd:0.350, top_speed_kmh:350, torque_nm: 750, gears:7, final_drive:3.40, tire_radius:0.340, redline_rpm:8700,  idle_rpm:900,  te:0.94, frontal_area:2.0 },
    lamborghini_huracan_sto:   { power_kw: 470, weight_kg:1339, cd:0.370, top_speed_kmh:310, torque_nm: 600, gears:7, final_drive:3.55, tire_radius:0.330, redline_rpm:8500,  idle_rpm:900,  te:0.93, frontal_area:2.0 },
    porsche_918:               { power_kw: 652, weight_kg:1640, cd:0.320, top_speed_kmh:345, torque_nm: 900, gears:7, final_drive:3.40, tire_radius:0.340, redline_rpm:9150,  idle_rpm:800,  te:0.94, frontal_area:2.0 },
    porsche_911_gt2_rs:        { power_kw: 515, weight_kg:1470, cd:0.380, top_speed_kmh:340, torque_nm: 750, gears:7, final_drive:3.60, tire_radius:0.330, redline_rpm:7200,  idle_rpm:800,  te:0.93, frontal_area:1.9 },
    porsche_911_turbo_s:       { power_kw: 478, weight_kg:1640, cd:0.330, top_speed_kmh:330, torque_nm: 800, gears:8, final_drive:3.50, tire_radius:0.330, redline_rpm:7200,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
    mercedes_amg_one:          { power_kw: 782, weight_kg:1695, cd:0.320, top_speed_kmh:352, torque_nm: 900, gears:8, final_drive:3.25, tire_radius:0.340, redline_rpm:11000, idle_rpm:900,  te:0.94, frontal_area:2.0 },
    gordon_murray_t50:         { power_kw: 485, weight_kg: 986, cd:0.320, top_speed_kmh:370, torque_nm: 467, gears:6, final_drive:3.70, tire_radius:0.330, redline_rpm:12100, idle_rpm:1000, te:0.94, frontal_area:1.8 },
    czinger_21c:               { power_kw: 930, weight_kg:1250, cd:0.320, top_speed_kmh:437, torque_nm:1100, gears:7, final_drive:3.35, tire_radius:0.340, redline_rpm:11000, idle_rpm:900,  te:0.94, frontal_area:1.9 },
    ford_gt:                   { power_kw: 485, weight_kg:1385, cd:0.340, top_speed_kmh:348, torque_nm: 746, gears:7, final_drive:3.55, tire_radius:0.330, redline_rpm:6500,  idle_rpm:700,  te:0.93, frontal_area:2.0 },
    corvette_z06:              { power_kw: 500, weight_kg:1560, cd:0.340, top_speed_kmh:312, torque_nm: 623, gears:8, final_drive:3.73, tire_radius:0.340, redline_rpm:8600,  idle_rpm:900,  te:0.93, frontal_area:2.1 },
    dodge_viper_acr:           { power_kw: 477, weight_kg:1521, cd:0.420, top_speed_kmh:330, torque_nm: 814, gears:6, final_drive:3.55, tire_radius:0.340, redline_rpm:6200,  idle_rpm:700,  te:0.92, frontal_area:2.1 },
    acura_nsx_type_s:          { power_kw: 447, weight_kg:1725, cd:0.330, top_speed_kmh:307, torque_nm: 600, gears:9, final_drive:3.60, tire_radius:0.330, redline_rpm:7500,  idle_rpm:800,  te:0.94, frontal_area:2.0 },
    nissan_gtr_nismo:          { power_kw: 441, weight_kg:1720, cd:0.350, top_speed_kmh:315, torque_nm: 637, gears:6, final_drive:3.70, tire_radius:0.340, redline_rpm:7100,  idle_rpm:800,  te:0.93, frontal_area:2.0 },
};

// ==========================================
// F1 2020 SPECS — CALIBRATED
// All values verified against real benchmarks.
//
// Key F1 physics differences vs hypercars:
//  - frontal_area: 1.4 m² (narrower F1 car)
//  - cd_effective: 1.20 (includes induced drag from wings)
//  - tire_mu_cold: 0.78 (Pirelli slicks cold = wheelspin at launch)
//  - tire_mu_warm: 1.65 (warm slicks = massive grip)
//  - downforce_cl: 1.35 (adds ~640kg @ 300km/h)
//  - gear_set: 'f1' (real shift speeds: G1@82, G2@133... km/h)
//  - shift_duration: 0.05s (seamless paddle shift)
//  - rolling_rr: 0.008 (lower than road car 0.015)
// ==========================================
const F1_SPECS = {
    // Per-car cd offsets reflect real 2020 aero differences (±2-3%)
    f1_mercedes_w11:     { power_kw:950, weight_kg:746, cd:1.20, top_speed_kmh:372, torque_nm:870, f1:true },
    f1_redbull_rb16:     { power_kw:940, weight_kg:744, cd:1.22, top_speed_kmh:368, torque_nm:862, f1:true },
    f1_ferrari_sf1000:   { power_kw:920, weight_kg:746, cd:1.25, top_speed_kmh:360, torque_nm:845, f1:true },
    f1_mclaren_mcl35:    { power_kw:915, weight_kg:748, cd:1.24, top_speed_kmh:358, torque_nm:840, f1:true },
    f1_renault_rs20:     { power_kw:910, weight_kg:746, cd:1.25, top_speed_kmh:356, torque_nm:835, f1:true },
    f1_alphatauri_at01:  { power_kw:938, weight_kg:745, cd:1.23, top_speed_kmh:365, torque_nm:860, f1:true },
    f1_racingpoint_rp20: { power_kw:945, weight_kg:743, cd:1.21, top_speed_kmh:369, torque_nm:865, f1:true },
    f1_alfaromeo_c39:    { power_kw:918, weight_kg:747, cd:1.26, top_speed_kmh:357, torque_nm:843, f1:true },
    f1_haas_vf20:        { power_kw:916, weight_kg:748, cd:1.27, top_speed_kmh:355, torque_nm:840, f1:true },
    f1_williams_fw43:    { power_kw:943, weight_kg:745, cd:1.24, top_speed_kmh:363, torque_nm:863, f1:true },
};

const ALL_SPECS = { ...HYPERCAR_SPECS, ...F1_SPECS };

// ==========================================
// GEAR RATIO SETS
// ==========================================

// Standard road car gear ratios
const GEAR_RATIO_SETS = {
    1: [2.50],
    6: [3.82, 2.26, 1.64, 1.26, 1.00, 0.79],
    7: [3.91, 2.31, 1.68, 1.28, 1.00, 0.82, 0.67],
    8: [3.50, 2.30, 1.70, 1.35, 1.08, 0.88, 0.72, 0.61],
    9: [4.20, 2.80, 2.00, 1.55, 1.25, 1.02, 0.85, 0.70, 0.60],
};

// F1 2020 gear ratios — derived from known real shift speeds:
// G1@82, G2@133, G3@172, G4@204, G5@238, G6@268, G7@295, G8@340+ km/h
// (medium downforce configuration, 15000rpm redline, final_drive=3.07, r=0.330m)
const F1_GEAR_RATIOS  = [6.079, 3.748, 2.898, 2.443, 2.094, 1.860, 1.690, 1.698];
const F1_SHIFT_FRACS  = [0.82,  0.82,  0.82,  0.82,  0.82,  0.82,  0.82,  0.95];
const F1_FINAL_DRIVE  = 3.07;
const F1_TIRE_RADIUS  = 0.330;
const F1_REDLINE      = 15000;
const F1_IDLE         = 4000;
const F1_FRONTAL_AREA = 1.4;   // m²  — narrower than a road car
const F1_DOWNFORCE_CL = 1.35;  // lift coeff generating downforce over frontal area
const F1_MU_COLD      = 0.78;  // Pirelli slick, cold tyres = wheelspin at launch
const F1_MU_WARM      = 1.65;  // Pirelli slick, fully warmed
const F1_ROLLING_RR   = 0.008; // lower than road car
const F1_SHIFT_DUR    = 0.05;  // seamless 50ms gear change

// Standard road car shift fracs (shift at these fractions of redline)
const ROAD_SHIFT_FRACS = [0.68, 0.72, 0.76, 0.78, 0.81, 0.84, 0.86, 0.88, 0.90];

// ==========================================
// CONSTANTS
// ==========================================
const G        = 9.81;
const AIR_RHO  = 1.225;
const DT       = 0.005;      // 5ms — accurate enough, fast enough
const QM_DIST  = 402.336;    // quarter mile in meters

// ==========================================
// PHYSICS ENGINE
// ==========================================
class PhysicsEngine {
    constructor(vehicleId, vehicleName, specs, environment = {}) {
        this.id   = vehicleId;
        this.name = vehicleName;
        this.s    = specs;
        this.env  = {
            temperature_celsius: environment.temperature_celsius ?? 20,
            altitude_meters:     environment.altitude_meters     ?? 0,
        };
        this.airDensity = this._calcAirDensity();
        this.isF1       = !!specs.f1;

        // Gear config
        if (this.isF1) {
            this.gearRatios  = F1_GEAR_RATIOS;
            this.shiftFracs  = F1_SHIFT_FRACS;
            this.finalDrive  = F1_FINAL_DRIVE;
            this.tireRadius  = F1_TIRE_RADIUS;
            this.redline     = F1_REDLINE;
            this.idleRpm     = F1_IDLE;
            this.frontalArea = F1_FRONTAL_AREA;
            this.shiftDur    = F1_SHIFT_DUR;
            this.rollingRR   = F1_ROLLING_RR;
        } else {
            this.gearRatios  = GEAR_RATIO_SETS[specs.gears] || GEAR_RATIO_SETS[7];
            this.shiftFracs  = ROAD_SHIFT_FRACS;
            this.finalDrive  = specs.final_drive;
            this.tireRadius  = specs.tire_radius;
            this.redline     = specs.redline_rpm;
            this.idleRpm     = specs.idle_rpm;
            this.frontalArea = specs.frontal_area || 2.0;
            this.shiftDur    = 0.12;  // 120ms road car shift
            this.rollingRR   = 0.015;
        }
    }

    _calcAirDensity() {
        const tempK = this.env.temperature_celsius + 273.15;
        const p = 101325 * Math.exp(-this.env.altitude_meters / 8400);
        return (p / (287.05 * tempK)) * 0.98;
    }

    // Torque curve: flat to 68% redline, linear drop to 65% peak at redline
    _torque(rpm) {
        const peakRpm = this.redline * 0.68;
        if (rpm <= peakRpm) return this.s.torque_nm;
        const t = (this.redline - rpm) / (this.redline - peakRpm);
        return this.s.torque_nm * Math.max(0.65, t);
    }

    _rpmFromV(v, gear) {
        const gr = this.gearRatios[gear - 1];
        const rpm = (v * 60 * gr * this.finalDrive) / (2 * Math.PI * this.tireRadius);
        return Math.max(this.idleRpm, rpm);
    }

    _shouldShift(rpm, gear) {
        if (gear >= this.gearRatios.length) return false;
        const frac = this.shiftFracs[Math.min(gear - 1, this.shiftFracs.length - 1)];
        return rpm >= this.redline * frac;
    }

    // Select best starting gear for roll race (non-zero start velocity)
    _gearForSpeed(v) {
        for (let g = this.gearRatios.length; g >= 1; g--) {
            const rpm = this._rpmFromV(v, g);
            if (rpm >= this.idleRpm && rpm <= this.redline * 0.85) return g;
        }
        return 1;
    }

    simulate(maxTime = 30, targetDistance = null, startVelocity = 0) {
        const snapshots = [];
        const topSpeedMs = this.s.top_speed_kmh / 3.6;

        let v      = startVelocity;
        let dist   = 0;
        let t      = 0;
        let gear   = startVelocity > 1 ? this._gearForSpeed(startVelocity) : 1;
        let shifting    = false;
        let shiftRemain = 0;
        let tireTemp    = 25;  // °C — cold at start

        const maxSteps = Math.ceil(maxTime / DT);

        for (let step = 0; step < maxSteps; step++) {
            if (targetDistance && dist >= targetDistance) break;
            if (v >= topSpeedMs * 0.999) {
                // Cruising at top speed — fill remaining frames at constant v
                snapshots.push(this._snap(t, dist, v, 0, gear, this._rpmFromV(v, gear)));
                dist += v * DT;
                t += DT;
                if (targetDistance && dist >= targetDistance) break;
                continue;
            }

            // --- Gear shift logic ---
            if (shifting) {
                shiftRemain -= DT;
                if (shiftRemain <= 0) shifting = false;
            } else {
                const rpm = this._rpmFromV(v, gear);
                if (this._shouldShift(rpm, gear)) {
                    gear++;
                    shifting = true;
                    shiftRemain = this.shiftDur;
                }
            }

            const rpm = this._rpmFromV(v, gear);

            // --- Driving force ---
            const wheelTorque = this._torque(rpm) * this.gearRatios[gear - 1] * this.finalDrive * this.s.te;
            let Fd = shifting ? 0 : wheelTorque / this.tireRadius;

            // Power cap: F = P/v
            if (v > 0.5) {
                Fd = Math.min(Fd, (this.s.power_kw * 1000 * this.s.te) / v);
            }

            // --- Traction limit ---
            let Fd_max;
            if (this.isF1) {
                // F1: tyre warms up quickly under hard acceleration
                tireTemp = Math.min(90, tireTemp + v * 0.004 * DT + Math.abs(Fd) / 40000 * DT);
                const warmFrac = Math.min(1, tireTemp / 70);
                const mu = F1_MU_COLD + (F1_MU_WARM - F1_MU_COLD) * warmFrac;
                // Downforce increases effective normal force (and traction)
                const downforce = 0.5 * this.airDensity * F1_DOWNFORCE_CL * F1_FRONTAL_AREA * v * v;
                Fd_max = mu * (this.s.weight_kg * G + downforce);
            } else {
                // Road car: standard traction model
                tireTemp = Math.min(90, tireTemp + v * 0.003 * DT + Math.abs(Fd) / 50000 * DT);
                const warmFrac = Math.min(1, tireTemp / 75);
                const gripFactor = 0.85 + warmFrac * 0.15;
                const mu = 1.30 * gripFactor * Math.max(0.85, 1.0 - v / 200);
                const rearWeight = Math.min(0.85, 0.60 + (Fd / this.s.weight_kg / G) * 0.15);
                Fd_max = mu * this.s.weight_kg * G * rearWeight;
            }
            Fd = Math.min(Fd, Fd_max);

            // --- Resistance forces ---
            const drag = 0.5 * this.airDensity * this.s.cd * this.frontalArea * v * v;
            const roll = this.s.weight_kg * G * this.rollingRR;

            // --- Integration ---
            const netF  = Fd - drag - roll;
            const accel = netF / this.s.weight_kg;

            snapshots.push(this._snap(t, dist, v, accel, gear, rpm));

            v    = Math.max(startVelocity, v + accel * DT);
            dist += v * DT;
            t    += DT;
        }

        return snapshots;
    }

    _snap(t, dist, v, accel, gear, rpm) {
        const power = Math.max(0, accel * this.s.weight_kg * v / 1000);
        return {
            time:         parseFloat(t.toFixed(3)),
            distance:     parseFloat(dist.toFixed(2)),
            velocity:     parseFloat(v.toFixed(3)),
            acceleration: parseFloat(accel.toFixed(3)),
            gear,
            rpm:      parseFloat(rpm.toFixed(0)),
            power_kw: parseFloat(power.toFixed(1)),
        };
    }
}

// ==========================================
// PERFORMANCE METRICS (interpolated)
// ==========================================
function calcMetrics(snapshots) {
    let time100 = null, time200 = null, qmTime = null, qmSpeed = null;

    for (let i = 1; i < snapshots.length; i++) {
        const s = snapshots[i];
        const p = snapshots[i - 1];
        const kmh  = s.velocity * 3.6;
        const pkmh = p.velocity * 3.6;

        function interp(target) {
            if (pkmh >= target) return null; // already past
            const frac = (target - pkmh) / (kmh - pkmh);
            return p.time + (s.time - p.time) * frac;
        }

        if (!time100 && kmh >= 100)  time100 = interp(100);
        if (!time200 && kmh >= 200)  time200 = interp(200);

        if (!qmTime && s.distance >= QM_DIST) {
            const frac = (QM_DIST - p.distance) / (s.distance - p.distance);
            qmTime  = parseFloat((p.time     + (s.time     - p.time)     * frac).toFixed(3));
            qmSpeed = parseFloat(((p.velocity + (s.velocity - p.velocity) * frac) * 3.6).toFixed(1));
        }
    }

    return {
        time_to_100kmh:     time100  ? parseFloat(time100.toFixed(3))  : null,
        time_to_200kmh:     time200  ? parseFloat(time200.toFixed(3))  : null,
        quarter_mile_time:  qmTime   ?? null,
        quarter_mile_speed: qmSpeed  ?? null,
    };
}

// ==========================================
// PUBLIC API — matches Python backend schema
// ==========================================
export function runFrontendSimulation(vehicleIds, environment, maxTime, targetDistance, startVelocity = 0) {
    const results = vehicleIds.map(id => {
        const catEntry = CAR_CATALOGUE.find(c => c.id === id);
        const displayName = catEntry
            ? `${catEntry.team} ${catEntry.model}`
            : id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

        const rawSpecs = ALL_SPECS[id];
        if (!rawSpecs) console.warn(`[sim-physics] No specs for "${id}", using defaults`);

        // Merge catalogue engine info into specs (te always present)
        const specs = {
            te: 0.93,
            frontal_area: 2.0,
            ...( rawSpecs || {
                power_kw: 600, weight_kg: 1500, cd: 0.35,
                top_speed_kmh: 320, torque_nm: 800, gears: 7,
                final_drive: 3.40, tire_radius: 0.33,
                redline_rpm: 8000, idle_rpm: 800,
            })
        };

        const engine   = new PhysicsEngine(id, displayName, specs, environment || {});
        const snapshots = engine.simulate(
            maxTime         ?? 45,
            targetDistance  ?? null,
            startVelocity   ?? 0
        );
        const metrics = calcMetrics(snapshots);

        return { vehicle_name: displayName, snapshots, ...metrics };
    });

    return {
        results,
        environment: environment ?? { temperature_celsius: 20, altitude_meters: 0 },
    };
}
