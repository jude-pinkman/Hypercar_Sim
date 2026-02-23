// ==========================================
// LAP SIMULATOR – High-Fidelity Physics Engine
// 10ms integration timestep
// Real braking zones, traction limits, aero downforce
// Based on real Monaco F1 reference data
// ==========================================

'use strict';

const G          = 9.81;
const AIR_RHO    = 1.225;
const DT         = 0.010;   // 10ms step
const TIRE_MU_BASE = 1.55;  // baseline peak lateral μ

// ==========================================
// MONACO TRACK – Real segment data
// ==========================================
const MONACO_CONFIG = {
    id: 'monaco',
    name: 'Circuit de Monaco',
    country: 'Monaco',
    length_m: 3337,
    cornerCount: 19,
    difficulty: 'extreme',
    referenceGrip: 1.80,
    tarmacGrip: 0.97,

    segments: [
        // SECTOR 1
        { id:'s0',  type:'straight', name:'Start / Pit Straight',          length_m:170, sector:0 },
        { id:'b1',  type:'braking',  name:'BZ T1 – Sainte-Dévote',         length_m: 62, brakingG_ref:3.8, sector:0, isBrakeZone:true, cornerRef:'T1 Sainte-Dévote' },
        { id:'c1',  type:'corner',   name:'T1 – Sainte-Dévote',            length_m: 55, apexSpeed_kph: 73, sector:0 },
        { id:'a1',  type:'accel',    name:'Exit T1',                        length_m: 35, sector:0 },
        { id:'s1',  type:'straight', name:'Beau Rivage Climb',              length_m:175, sector:0 },
        { id:'b3',  type:'braking',  name:'BZ T3 – Massenet',              length_m: 40, brakingG_ref:3.2, sector:0, isBrakeZone:true, cornerRef:'T3 Massenet' },
        { id:'c3',  type:'corner',   name:'T3 – Massenet',                 length_m: 50, apexSpeed_kph: 92, sector:0 },
        { id:'a3',  type:'accel',    name:'Exit T3',                        length_m: 25, sector:0 },
        { id:'b4',  type:'braking',  name:'BZ T4 – Casino',                length_m: 30, brakingG_ref:3.0, sector:0, isBrakeZone:true, cornerRef:'T4 Casino' },
        { id:'c4',  type:'corner',   name:'T4 – Casino',                   length_m: 48, apexSpeed_kph: 82, sector:0 },
        { id:'a4',  type:'accel',    name:'Exit T4',                        length_m: 20, sector:0 },
        // SECTOR 2
        { id:'b5',  type:'braking',  name:'BZ T5 – Mirabeau Haute',        length_m: 35, brakingG_ref:3.4, sector:1, isBrakeZone:true, cornerRef:'T5 Mirabeau Haute' },
        { id:'c5',  type:'corner',   name:'T5 – Mirabeau Haute',           length_m: 42, apexSpeed_kph: 63, sector:1 },
        { id:'a5',  type:'accel',    name:'Exit T5',                        length_m: 15, sector:1 },
        { id:'b6',  type:'braking',  name:"BZ T6 – Grand Hôtel Hairpin",   length_m: 42, brakingG_ref:4.2, sector:1, isBrakeZone:true, cornerRef:"T6 Grand Hôtel Hairpin" },
        { id:'c6',  type:'corner',   name:"T6 – Grand Hôtel Hairpin",      length_m: 55, apexSpeed_kph: 44, sector:1 },
        { id:'a6',  type:'accel',    name:'Exit T6',                        length_m: 20, sector:1 },
        { id:'b7',  type:'braking',  name:'BZ T7 – Mirabeau Bas',          length_m: 22, brakingG_ref:2.8, sector:1, isBrakeZone:true, cornerRef:'T7 Mirabeau Bas' },
        { id:'c7',  type:'corner',   name:'T7 – Mirabeau Bas',             length_m: 38, apexSpeed_kph: 60, sector:1 },
        { id:'a7',  type:'accel',    name:'Exit T7',                        length_m: 18, sector:1 },
        { id:'b8',  type:'braking',  name:'BZ T8 – Portier',               length_m: 28, brakingG_ref:2.6, sector:1, isBrakeZone:true, cornerRef:'T8 Portier' },
        { id:'c8',  type:'corner',   name:'T8 – Portier',                  length_m: 52, apexSpeed_kph: 88, sector:1 },
        { id:'a8',  type:'accel',    name:'Exit T8',                        length_m: 22, sector:1 },
        { id:'s2',  type:'straight', name:'Tunnel Approach',                length_m:135, sector:1 },
        { id:'b9',  type:'braking',  name:'BZ T9 – Tunnel Exit',           length_m: 50, brakingG_ref:3.8, sector:1, isBrakeZone:true, cornerRef:'T9 Tunnel Exit' },
        { id:'c9',  type:'corner',   name:'T9 – Tunnel Exit',              length_m: 58, apexSpeed_kph:128, sector:1 },
        { id:'a9',  type:'accel',    name:'Exit T9',                        length_m: 28, sector:1 },
        // SECTOR 3
        { id:'s3',  type:'straight', name:'Harbour Straight',               length_m:168, sector:2 },
        { id:'b10', type:'braking',  name:'BZ T10/11 – Nouvelle Chicane',  length_m: 55, brakingG_ref:4.0, sector:2, isBrakeZone:true, cornerRef:'T10/11 Nouvelle Chicane' },
        { id:'c10', type:'corner',   name:'T10/11 – Nouvelle Chicane',     length_m: 72, apexSpeed_kph: 65, sector:2 },
        { id:'a10', type:'accel',    name:'Exit Chicane',                   length_m: 30, sector:2 },
        { id:'b12', type:'braking',  name:'BZ T12 – Tabac',                length_m: 25, brakingG_ref:2.5, sector:2, isBrakeZone:true, cornerRef:'T12 Tabac' },
        { id:'c12', type:'corner',   name:'T12 – Tabac',                   length_m: 58, apexSpeed_kph:105, sector:2 },
        { id:'a12', type:'accel',    name:'Exit T12',                       length_m: 25, sector:2 },
        { id:'b13', type:'braking',  name:'BZ T13 – Louis',                length_m: 22, brakingG_ref:2.4, sector:2, isBrakeZone:true, cornerRef:'T13 Louis' },
        { id:'c13', type:'corner',   name:'T13 – Louis / Chiron',          length_m: 75, apexSpeed_kph: 90, sector:2 },
        { id:'a13', type:'accel',    name:'Exit T13/14',                    length_m: 25, sector:2 },
        { id:'b15', type:'braking',  name:'BZ T15/16 – Piscine',           length_m: 30, brakingG_ref:2.8, sector:2, isBrakeZone:true, cornerRef:'T15/16 Piscine' },
        { id:'c15', type:'corner',   name:'T15/16 – Piscine',              length_m: 62, apexSpeed_kph: 70, sector:2 },
        { id:'a15', type:'accel',    name:'Exit Piscine',                   length_m: 20, sector:2 },
        { id:'s4',  type:'straight', name:'Pre-Rascasse',                   length_m: 52, sector:2 },
        { id:'b18', type:'braking',  name:'BZ T18 – La Rascasse',          length_m: 38, brakingG_ref:3.6, sector:2, isBrakeZone:true, cornerRef:'T18 La Rascasse' },
        { id:'c18', type:'corner',   name:'T18 – La Rascasse',             length_m: 48, apexSpeed_kph: 43, sector:2 },
        { id:'a18', type:'accel',    name:'Exit Rascasse',                  length_m: 18, sector:2 },
        { id:'b19', type:'braking',  name:"BZ T19 – Anthony Noghès",       length_m: 22, brakingG_ref:2.8, sector:2, isBrakeZone:true, cornerRef:"T19 Anthony Noghès" },
        { id:'c19', type:'corner',   name:"T19 – Anthony Noghès",          length_m: 40, apexSpeed_kph: 58, sector:2 },
        { id:'a19', type:'accel',    name:'Exit T19 to Grid',               length_m: 95, sector:2 },
    ]
};

const TRACK_REGISTRY = { monaco: MONACO_CONFIG };

// ==========================================
// PHYSICS HELPERS
// ==========================================
function dragForce(v, Cd, A) { return 0.5*AIR_RHO*Cd*A*v*v; }
function downforceN(v, car) {
    const Cl = (car.downforce_factor??1.0)*1.4;
    return 0.5*AIR_RHO*Cl*1.85*v*v;
}
function normalLoad(v, car) { return car.weight_kg*G + downforceN(v,car); }
function engineForce(v, car) {
    if(v<0.5) v=0.5;
    const eff = car.transmission_efficiency??0.92;
    return (car.power_kw*1000*eff)/v;
}
function maxTractionForce(v, car) {
    const mu = TIRE_MU_BASE*(car.cornering_grip??1.0)/1.55;
    return mu*normalLoad(v,car);
}
function tractionForce(v, car) {
    return Math.min(engineForce(v,car), maxTractionForce(v,car), car.weight_kg*G*1.65);
}
function apexSpeedForCar(apexKph_ref, car, track) {
    const gr = (car.cornering_grip??1.2)*(car.downforce_factor??1.0)/track.referenceGrip;
    return Math.min(apexKph_ref*Math.sqrt(gr), apexKph_ref*1.35);
}
function brakingGForCar(brakingG_ref, car) {
    const carMu = (car.cornering_grip??1.2)*0.92;
    const f1Mu  = 4.2;
    return Math.min(brakingG_ref*(carMu/f1Mu), 1.55); // cap road car at ~1.55g
}

// ==========================================
// SEGMENT INTEGRATORS
// ==========================================
function integrateStraight(seg, v0, car, topV) {
    const Cd=car.drag_coefficient??0.35, A=1.85, m=car.weight_kg;
    let v=v0, dist=0, t=0;
    const pts=[]; let ns=0;
    while(dist<seg.length_m) {
        const Fd=dragForce(v,Cd,A);
        const Ft=tractionForce(v,car);
        const a=(Ft-Fd)/m;
        v=Math.min(v+a*DT, topV);
        dist=Math.min(dist+v*DT, seg.length_m);
        t+=DT;
        if(dist>=ns){ pts.push({dist:Math.round(dist),speed_kph:Math.round(v*3.6),phase:'accel',seg:seg.name}); ns+=8; }
        if(v>=topV && a<=0.01) break;
    }
    if(dist<seg.length_m){ t+=(seg.length_m-dist)/Math.max(v,1); }
    return {time_s:t, v_exit_ms:v, points:pts};
}

function integrateBraking(seg, v0, v_target, car) {
    const brakingG = brakingGForCar(seg.brakingG_ref, car);
    const Cd=car.drag_coefficient??0.35, A=1.85, m=car.weight_kg;
    let v=v0, dist=0, t=0, peakDecel=0;
    const pts=[]; let ns=0;
    while(v>v_target && dist<seg.length_m*1.8) {
        const Fd=dragForce(v,Cd,A);
        const Fdf=downforceN(v,car);
        const Fn=m*G+Fdf;
        const Fbr=Math.min(brakingG*G*m, TIRE_MU_BASE*(car.cornering_grip??1.2)*Fn*0.92);
        const a=(-(Fbr+Fd))/m;
        const g_val=Math.abs(a)/G;
        if(g_val>peakDecel) peakDecel=g_val;
        v=Math.max(v+a*DT, v_target);
        dist+=v*DT;
        t+=DT;
        if(dist>=ns){ pts.push({dist:Math.round(dist),speed_kph:Math.round(v*3.6),phase:'braking',seg:seg.name,decel_g:Math.round(g_val*10)/10}); ns+=4; }
    }
    return {
        time_s:t, v_exit_ms:v, points:pts,
        braking_dist_m:Math.round(dist),
        braking_time_ms:Math.round(t*1000),
        peak_decel_g:Math.round(peakDecel*10)/10
    };
}

function integrateCorner(seg, v_apex) {
    const t=seg.length_m/Math.max(v_apex,1);
    return {
        time_s:t, v_exit_ms:v_apex,
        points:[
            {dist:0,              speed_kph:Math.round(v_apex*3.6),phase:'corner',seg:seg.name},
            {dist:Math.round(seg.length_m), speed_kph:Math.round(v_apex*3.6),phase:'corner',seg:seg.name}
        ]
    };
}

// ==========================================
// MAIN ENTRY POINT
// ==========================================
function simulateMonacoLap(car, trackId='monaco') {
    const track=TRACK_REGISTRY[trackId];
    if(!track) throw new Error('Unknown track: '+trackId);

    const topV=car.top_speed_kmh/3.6;
    let totalTime=0, totalDist=0;
    let v=80/3.6;  // flying lap entry speed

    const telemetry=[], brakeZoneData=[], sectorTimes=[0,0,0];

    // Pre-compute apex speeds
    const apexSpeeds={};
    for(const s of track.segments) {
        if(s.type==='corner') apexSpeeds[s.id]=apexSpeedForCar(s.apexSpeed_kph,car,track)/3.6;
    }
    function targetForBrake(bSeg) {
        const cid=bSeg.id.replace('b','c');
        return apexSpeeds[cid]??(50/3.6);
    }

    for(const seg of track.segments) {
        let res;
        switch(seg.type) {
            case 'straight': res=integrateStraight(seg,v,car,topV); break;
            case 'braking': {
                const vt=targetForBrake(seg);
                res=integrateBraking(seg,v,vt,car);
                brakeZoneData.push({
                    corner:       seg.cornerRef||seg.name,
                    brakingDist_m:res.braking_dist_m,
                    brakingTime_ms:res.braking_time_ms,
                    peakDecel_g:  res.peak_decel_g,
                    entry_kph:    Math.round(v*3.6),
                    apex_kph:     Math.round(vt*3.6),
                    speedLoss_kph:Math.round((v-vt)*3.6)
                });
                break;
            }
            case 'corner': { const va=apexSpeeds[seg.id]??(50/3.6); res=integrateCorner(seg,va); break; }
            case 'accel':  res=integrateStraight(seg,v,car,topV); break;
            default: continue;
        }

        totalTime+=res.time_s;
        totalDist+=seg.length_m;
        v=res.v_exit_ms;
        sectorTimes[seg.sector]+=res.time_s;

        for(const pt of (res.points||[])) {
            telemetry.push({
                dist:      Math.round(totalDist - seg.length_m + pt.dist),
                speed_kph: pt.speed_kph,
                phase:     pt.phase,
                seg:       pt.seg,
                decel_g:   pt.decel_g??null
            });
        }
    }

    const speeds=telemetry.map(p=>p.speed_kph);
    return {
        lapTimeSeconds:  totalTime,
        avgSpeedKph:     Math.round((totalDist/totalTime)*3.6*10)/10,
        maxSpeedKph:     Math.max(...speeds),
        minSpeedKph:     Math.min(...speeds),
        totalDist_m:     Math.round(totalDist),
        sectorTimes:     sectorTimes.map(t=>Math.round(t*1000)/1000),
        telemetry,
        brakeZoneData,
        trackConfig:     track
    };
}

function formatLapTime(s) {
    const m=Math.floor(s/60), rem=s%60;
    const si=Math.floor(rem), ms=Math.round((rem-si)*1000);
    return `${m}:${String(si).padStart(2,'0')}.${String(ms).padStart(3,'0')}`;
}

export { simulateMonacoLap, formatLapTime, TRACK_REGISTRY, MONACO_CONFIG };
