// ==========================================
// CIRCUITS-RT.JS — Real-Time Simulation Engine
// Car animates along GeoJSON track, physics-accurate
// Weather, multi-lap, car customization
// ==========================================

'use strict';

import { formatLapTime } from './lapSimulator.js';

// ==========================================
// VEHICLE SPECS
// ==========================================
const VEHICLE_SPECS = {
    koenigsegg_jesko:          { power_kw:1195, weight_kg:1420, drag_coefficient:0.278, top_speed_kmh:531, cornering_grip:1.30, downforce_factor:1.05, transmission_efficiency:0.94 },
    koenigsegg_jesko_attack:   { power_kw:1195, weight_kg:1420, drag_coefficient:0.315, top_speed_kmh:480, cornering_grip:1.45, downforce_factor:1.25, transmission_efficiency:0.94 },
    koenigsegg_regera:         { power_kw:1100, weight_kg:1590, drag_coefficient:0.278, top_speed_kmh:410, cornering_grip:1.22, downforce_factor:1.00, transmission_efficiency:0.95 },
    koenigsegg_agera_rs:       { power_kw:1014, weight_kg:1395, drag_coefficient:0.330, top_speed_kmh:447, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.94 },
    bugatti_chiron_ss:         { power_kw:1177, weight_kg:1978, drag_coefficient:0.350, top_speed_kmh:490, cornering_grip:1.10, downforce_factor:0.90, transmission_efficiency:0.93 },
    bugatti_bolide:            { power_kw:1361, weight_kg:1240, drag_coefficient:0.670, top_speed_kmh:500, cornering_grip:1.50, downforce_factor:1.40, transmission_efficiency:0.93 },
    bugatti_veyron_ss:         { power_kw: 882, weight_kg:1888, drag_coefficient:0.360, top_speed_kmh:431, cornering_grip:1.08, downforce_factor:0.88, transmission_efficiency:0.92 },
    hennessey_venom_f5:        { power_kw:1355, weight_kg:1360, drag_coefficient:0.330, top_speed_kmh:484, cornering_grip:1.18, downforce_factor:0.95, transmission_efficiency:0.93 },
    ssc_tuatara:               { power_kw:1305, weight_kg:1247, drag_coefficient:0.279, top_speed_kmh:455, cornering_grip:1.15, downforce_factor:0.92, transmission_efficiency:0.93 },
    pagani_huayra_r:           { power_kw: 620, weight_kg:1050, drag_coefficient:0.300, top_speed_kmh:370, cornering_grip:1.55, downforce_factor:1.35, transmission_efficiency:0.94 },
    pagani_zonda_r:            { power_kw: 559, weight_kg:1070, drag_coefficient:0.360, top_speed_kmh:350, cornering_grip:1.48, downforce_factor:1.30, transmission_efficiency:0.94 },
    mclaren_speedtail:         { power_kw: 782, weight_kg:1430, drag_coefficient:0.278, top_speed_kmh:403, cornering_grip:1.18, downforce_factor:0.95, transmission_efficiency:0.93 },
    mclaren_p1:                { power_kw: 673, weight_kg:1450, drag_coefficient:0.340, top_speed_kmh:350, cornering_grip:1.42, downforce_factor:1.20, transmission_efficiency:0.93 },
    mclaren_senna:             { power_kw: 588, weight_kg:1198, drag_coefficient:0.820, top_speed_kmh:340, cornering_grip:1.60, downforce_factor:1.45, transmission_efficiency:0.93 },
    mclaren_765lt:             { power_kw: 563, weight_kg:1229, drag_coefficient:0.350, top_speed_kmh:330, cornering_grip:1.40, downforce_factor:1.18, transmission_efficiency:0.93 },
    mclaren_720s:              { power_kw: 530, weight_kg:1283, drag_coefficient:0.320, top_speed_kmh:341, cornering_grip:1.32, downforce_factor:1.10, transmission_efficiency:0.93 },
    aston_valkyrie:            { power_kw: 865, weight_kg:1030, drag_coefficient:0.650, top_speed_kmh:402, cornering_grip:1.65, downforce_factor:1.50, transmission_efficiency:0.94 },
    rimac_nevera:              { power_kw:1408, weight_kg:2150, drag_coefficient:0.300, top_speed_kmh:412, cornering_grip:1.25, downforce_factor:1.05, transmission_efficiency:0.97 },
    lotus_evija:               { power_kw:1470, weight_kg:1680, drag_coefficient:0.380, top_speed_kmh:320, cornering_grip:1.28, downforce_factor:1.08, transmission_efficiency:0.97 },
    aspark_owl:                { power_kw:1480, weight_kg:1900, drag_coefficient:0.320, top_speed_kmh:400, cornering_grip:1.20, downforce_factor:1.00, transmission_efficiency:0.97 },
    pininfarina_battista:      { power_kw:1400, weight_kg:2100, drag_coefficient:0.290, top_speed_kmh:350, cornering_grip:1.18, downforce_factor:0.98, transmission_efficiency:0.97 },
    ferrari_sf90:              { power_kw: 735, weight_kg:1570, drag_coefficient:0.340, top_speed_kmh:340, cornering_grip:1.35, downforce_factor:1.12, transmission_efficiency:0.93 },
    ferrari_laferrari:         { power_kw: 588, weight_kg:1255, drag_coefficient:0.330, top_speed_kmh:352, cornering_grip:1.45, downforce_factor:1.22, transmission_efficiency:0.93 },
    ferrari_f8:                { power_kw: 530, weight_kg:1330, drag_coefficient:0.320, top_speed_kmh:340, cornering_grip:1.30, downforce_factor:1.08, transmission_efficiency:0.93 },
    ferrari_812:               { power_kw: 588, weight_kg:1525, drag_coefficient:0.330, top_speed_kmh:340, cornering_grip:1.22, downforce_factor:1.02, transmission_efficiency:0.93 },
    lamborghini_revuelto:      { power_kw: 825, weight_kg:1772, drag_coefficient:0.320, top_speed_kmh:350, cornering_grip:1.32, downforce_factor:1.12, transmission_efficiency:0.93 },
    lamborghini_aventador_svj: { power_kw: 566, weight_kg:1525, drag_coefficient:0.350, top_speed_kmh:352, cornering_grip:1.40, downforce_factor:1.20, transmission_efficiency:0.93 },
    lamborghini_sian:          { power_kw: 602, weight_kg:1595, drag_coefficient:0.350, top_speed_kmh:350, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.94 },
    lamborghini_huracan_sto:   { power_kw: 470, weight_kg:1339, drag_coefficient:0.370, top_speed_kmh:310, cornering_grip:1.42, downforce_factor:1.22, transmission_efficiency:0.93 },
    porsche_918:               { power_kw: 652, weight_kg:1640, drag_coefficient:0.320, top_speed_kmh:345, cornering_grip:1.38, downforce_factor:1.15, transmission_efficiency:0.94 },
    porsche_911_gt2_rs:        { power_kw: 515, weight_kg:1470, drag_coefficient:0.380, top_speed_kmh:340, cornering_grip:1.44, downforce_factor:1.20, transmission_efficiency:0.93 },
    porsche_911_turbo_s:       { power_kw: 478, weight_kg:1640, drag_coefficient:0.330, top_speed_kmh:330, cornering_grip:1.28, downforce_factor:1.05, transmission_efficiency:0.93 },
    mercedes_amg_one:          { power_kw: 782, weight_kg:1695, drag_coefficient:0.320, top_speed_kmh:352, cornering_grip:1.48, downforce_factor:1.28, transmission_efficiency:0.94 },
    gordon_murray_t50:         { power_kw: 485, weight_kg: 986, drag_coefficient:0.320, top_speed_kmh:370, cornering_grip:1.52, downforce_factor:1.32, transmission_efficiency:0.94 },
    czinger_21c:               { power_kw: 930, weight_kg:1250, drag_coefficient:0.320, top_speed_kmh:437, cornering_grip:1.40, downforce_factor:1.18, transmission_efficiency:0.94 },
    ford_gt:                   { power_kw: 485, weight_kg:1385, drag_coefficient:0.340, top_speed_kmh:348, cornering_grip:1.30, downforce_factor:1.10, transmission_efficiency:0.93 },
    corvette_z06:              { power_kw: 500, weight_kg:1560, drag_coefficient:0.340, top_speed_kmh:312, cornering_grip:1.35, downforce_factor:1.15, transmission_efficiency:0.93 },
    dodge_viper_acr:           { power_kw: 477, weight_kg:1521, drag_coefficient:0.420, top_speed_kmh:330, cornering_grip:1.38, downforce_factor:1.18, transmission_efficiency:0.92 },
    acura_nsx_type_s:          { power_kw: 447, weight_kg:1725, drag_coefficient:0.330, top_speed_kmh:307, cornering_grip:1.20, downforce_factor:1.00, transmission_efficiency:0.94 },
    nissan_gtr_nismo:          { power_kw: 441, weight_kg:1720, drag_coefficient:0.350, top_speed_kmh:315, cornering_grip:1.22, downforce_factor:1.02, transmission_efficiency:0.93 },

    // ---- Formula 1 2020 ----
    // F1 cars have exceptional cornering grip (slick tyres + massive downforce)
    // and moderate top speed limited by high-downforce aero configuration
    f1_mercedes_w11:     { power_kw:950, weight_kg:746, drag_coefficient:1.20, top_speed_kmh:372, cornering_grip:2.85, downforce_factor:3.50, transmission_efficiency:0.98 },
    f1_redbull_rb16:     { power_kw:940, weight_kg:744, drag_coefficient:1.22, top_speed_kmh:368, cornering_grip:2.80, downforce_factor:3.45, transmission_efficiency:0.98 },
    f1_ferrari_sf1000:   { power_kw:920, weight_kg:746, drag_coefficient:1.25, top_speed_kmh:360, cornering_grip:2.72, downforce_factor:3.38, transmission_efficiency:0.98 },
    f1_mclaren_mcl35:    { power_kw:915, weight_kg:748, drag_coefficient:1.24, top_speed_kmh:358, cornering_grip:2.70, downforce_factor:3.35, transmission_efficiency:0.98 },
    f1_renault_rs20:     { power_kw:910, weight_kg:746, drag_coefficient:1.25, top_speed_kmh:356, cornering_grip:2.68, downforce_factor:3.32, transmission_efficiency:0.98 },
    f1_alphatauri_at01:  { power_kw:938, weight_kg:745, drag_coefficient:1.23, top_speed_kmh:365, cornering_grip:2.78, downforce_factor:3.42, transmission_efficiency:0.98 },
    f1_racingpoint_rp20: { power_kw:945, weight_kg:743, drag_coefficient:1.21, top_speed_kmh:369, cornering_grip:2.82, downforce_factor:3.48, transmission_efficiency:0.98 },
    f1_alfaromeo_c39:    { power_kw:918, weight_kg:747, drag_coefficient:1.26, top_speed_kmh:357, cornering_grip:2.65, downforce_factor:3.30, transmission_efficiency:0.98 },
    f1_haas_vf20:        { power_kw:916, weight_kg:748, drag_coefficient:1.27, top_speed_kmh:355, cornering_grip:2.62, downforce_factor:3.28, transmission_efficiency:0.98 },
    f1_williams_fw43:    { power_kw:943, weight_kg:745, drag_coefficient:1.24, top_speed_kmh:363, cornering_grip:2.68, downforce_factor:3.35, transmission_efficiency:0.98 },
};

// ==========================================
// WEATHER CONFIG
// ==========================================
const WEATHER_CONFIG = {
    dry:   { grip:1.00, brakingMult:1.00, label:'Track: Dry · Grip: 100% · Visibility: Clear',    color:'#00FF9D', rain:false },
    damp:  { grip:0.78, brakingMult:0.80, label:'Track: Damp · Grip: 78% · Visibility: Mist',     color:'#88CCFF', rain:true,  intensity:0.3 },
    wet:   { grip:0.58, brakingMult:0.62, label:'Track: Wet · Grip: 58% · Visibility: Reduced',   color:'#4499FF', rain:true,  intensity:0.7 },
    storm: { grip:0.40, brakingMult:0.42, label:'Track: Storm · Grip: 40% · Visibility: Poor',    color:'#FF4466', rain:true,  intensity:1.0 },
};

// Tire compound grip modifiers
const TIRE_GRIP = { soft:1.12, medium:1.0, hard:0.90, wet:1.05 };  // wet compound good in rain
const TIRE_TEMP_OPT = { soft:55, medium:70, hard:85, wet:30 };       // optimal temps °C

// ==========================================
// PHYSICS CONSTANTS
// ==========================================
const G           = 9.81;
const AIR_RHO     = 1.225;
const DT          = 0.010;  // 10ms integration step
const TIRE_MU_BASE= 1.55;

// ==========================================
// MONACO TRACK
// ==========================================
const MONACO_CONFIG = {
    id:'monaco', name:'Circuit de Monaco', length_m:3337, referenceGrip:1.80, tarmacGrip:0.97,
    segments:[
        { id:'s0',  type:'straight', name:'Start / Pit Straight',        length_m:170, sector:0 },
        { id:'b1',  type:'braking',  name:'BZ T1 – Sainte-Dévote',       length_m:62,  brakingG_ref:3.8, sector:0, isBrakeZone:true, cornerRef:'T1 Sainte-Dévote' },
        { id:'c1',  type:'corner',   name:'T1 – Sainte-Dévote',          length_m:55,  apexSpeed_kph:73, sector:0 },
        { id:'a1',  type:'accel',    name:'Exit T1',                      length_m:35,  sector:0 },
        { id:'s1',  type:'straight', name:'Beau Rivage Climb',            length_m:175, sector:0 },
        { id:'b3',  type:'braking',  name:'BZ T3 – Massenet',            length_m:40,  brakingG_ref:3.2, sector:0, isBrakeZone:true, cornerRef:'T3 Massenet' },
        { id:'c3',  type:'corner',   name:'T3 – Massenet',               length_m:50,  apexSpeed_kph:92, sector:0 },
        { id:'a3',  type:'accel',    name:'Exit T3',                      length_m:25,  sector:0 },
        { id:'b4',  type:'braking',  name:'BZ T4 – Casino',              length_m:30,  brakingG_ref:3.0, sector:0, isBrakeZone:true, cornerRef:'T4 Casino' },
        { id:'c4',  type:'corner',   name:'T4 – Casino',                 length_m:48,  apexSpeed_kph:82, sector:0 },
        { id:'a4',  type:'accel',    name:'Exit T4',                      length_m:20,  sector:0 },
        { id:'b5',  type:'braking',  name:'BZ T5 – Mirabeau Haute',      length_m:35,  brakingG_ref:3.4, sector:1, isBrakeZone:true, cornerRef:'T5 Mirabeau Haute' },
        { id:'c5',  type:'corner',   name:'T5 – Mirabeau Haute',         length_m:42,  apexSpeed_kph:63, sector:1 },
        { id:'a5',  type:'accel',    name:'Exit T5',                      length_m:15,  sector:1 },
        { id:'b6',  type:'braking',  name:"BZ T6 – Grand Hôtel Hairpin", length_m:42,  brakingG_ref:4.2, sector:1, isBrakeZone:true, cornerRef:"T6 Grand Hôtel Hairpin" },
        { id:'c6',  type:'corner',   name:"T6 – Grand Hôtel Hairpin",    length_m:55,  apexSpeed_kph:44, sector:1 },
        { id:'a6',  type:'accel',    name:'Exit T6',                      length_m:20,  sector:1 },
        { id:'b7',  type:'braking',  name:'BZ T7 – Mirabeau Bas',        length_m:22,  brakingG_ref:2.8, sector:1, isBrakeZone:true, cornerRef:'T7 Mirabeau Bas' },
        { id:'c7',  type:'corner',   name:'T7 – Mirabeau Bas',           length_m:38,  apexSpeed_kph:60, sector:1 },
        { id:'a7',  type:'accel',    name:'Exit T7',                      length_m:18,  sector:1 },
        { id:'b8',  type:'braking',  name:'BZ T8 – Portier',             length_m:28,  brakingG_ref:2.6, sector:1, isBrakeZone:true, cornerRef:'T8 Portier' },
        { id:'c8',  type:'corner',   name:'T8 – Portier',                length_m:52,  apexSpeed_kph:88, sector:1 },
        { id:'a8',  type:'accel',    name:'Exit T8',                      length_m:22,  sector:1 },
        { id:'s2',  type:'straight', name:'Tunnel Approach',              length_m:135, sector:1 },
        { id:'b9',  type:'braking',  name:'BZ T9 – Tunnel Exit',         length_m:50,  brakingG_ref:3.8, sector:1, isBrakeZone:true, cornerRef:'T9 Tunnel Exit' },
        { id:'c9',  type:'corner',   name:'T9 – Tunnel Exit',            length_m:58,  apexSpeed_kph:128, sector:1 },
        { id:'a9',  type:'accel',    name:'Exit T9',                      length_m:28,  sector:1 },
        { id:'s3',  type:'straight', name:'Harbour Straight',             length_m:168, sector:2 },
        { id:'b10', type:'braking',  name:'BZ T10/11 – Nouvelle Chicane',length_m:55,  brakingG_ref:4.0, sector:2, isBrakeZone:true, cornerRef:'T10/11 Nouvelle Chicane' },
        { id:'c10', type:'corner',   name:'T10/11 – Nouvelle Chicane',   length_m:72,  apexSpeed_kph:65, sector:2 },
        { id:'a10', type:'accel',    name:'Exit Chicane',                 length_m:30,  sector:2 },
        { id:'b12', type:'braking',  name:'BZ T12 – Tabac',              length_m:25,  brakingG_ref:2.5, sector:2, isBrakeZone:true, cornerRef:'T12 Tabac' },
        { id:'c12', type:'corner',   name:'T12 – Tabac',                 length_m:58,  apexSpeed_kph:105, sector:2 },
        { id:'a12', type:'accel',    name:'Exit T12',                     length_m:25,  sector:2 },
        { id:'b13', type:'braking',  name:'BZ T13 – Louis',              length_m:22,  brakingG_ref:2.4, sector:2, isBrakeZone:true, cornerRef:'T13 Louis' },
        { id:'c13', type:'corner',   name:'T13 – Louis / Chiron',        length_m:75,  apexSpeed_kph:90, sector:2 },
        { id:'a13', type:'accel',    name:'Exit T13/14',                  length_m:25,  sector:2 },
        { id:'b15', type:'braking',  name:'BZ T15/16 – Piscine',         length_m:30,  brakingG_ref:2.8, sector:2, isBrakeZone:true, cornerRef:'T15/16 Piscine' },
        { id:'c15', type:'corner',   name:'T15/16 – Piscine',            length_m:62,  apexSpeed_kph:70, sector:2 },
        { id:'a15', type:'accel',    name:'Exit Piscine',                 length_m:20,  sector:2 },
        { id:'s4',  type:'straight', name:'Pre-Rascasse',                 length_m:52,  sector:2 },
        { id:'b18', type:'braking',  name:'BZ T18 – La Rascasse',        length_m:38,  brakingG_ref:3.6, sector:2, isBrakeZone:true, cornerRef:'T18 La Rascasse' },
        { id:'c18', type:'corner',   name:'T18 – La Rascasse',           length_m:48,  apexSpeed_kph:43, sector:2 },
        { id:'a18', type:'accel',    name:'Exit Rascasse',                length_m:18,  sector:2 },
        { id:'b19', type:'braking',  name:"BZ T19 – Anthony Noghès",     length_m:22,  brakingG_ref:2.8, sector:2, isBrakeZone:true, cornerRef:"T19 Anthony Noghès" },
        { id:'c19', type:'corner',   name:"T19 – Anthony Noghès",        length_m:40,  apexSpeed_kph:58, sector:2 },
        { id:'a19', type:'accel',    name:'Exit T19 to Grid',             length_m:95,  sector:2 },
    ]
};

// ==========================================
// SPA-FRANCORCHAMPS TRACK
// ==========================================
const SPA_CONFIG = {
    id:'spa', name:'Circuit de Spa-Francorchamps', length_m:6996, referenceGrip:1.75, tarmacGrip:0.96,
    segments:[
        // SECTOR 1 — La Source to top of Raidillon
        { id:'s0',   type:'straight', name:'Start / Kemmel Straight Approach', length_m:210, sector:0 },
        { id:'b1',   type:'braking',  name:'BZ T1 – La Source',               length_m:80,  brakingG_ref:4.5, sector:0, isBrakeZone:true, cornerRef:'T1 La Source' },
        { id:'c1',   type:'corner',   name:'T1 – La Source',                   length_m:90,  apexSpeed_kph:70, sector:0 },
        { id:'a1',   type:'accel',    name:'Exit La Source',                   length_m:60,  sector:0 },
        { id:'s1',   type:'straight', name:'Eau Rouge Descent',                length_m:120, sector:0 },
        { id:'b2',   type:'braking',  name:'BZ T2 – Eau Rouge',               length_m:25,  brakingG_ref:2.5, sector:0, isBrakeZone:true, cornerRef:'T2 Eau Rouge' },
        { id:'c2',   type:'corner',   name:'T2 – Eau Rouge',                  length_m:80,  apexSpeed_kph:260, sector:0 },
        { id:'a2',   type:'accel',    name:'Raidillon Climb',                  length_m:110, sector:0 },
        { id:'b4',   type:'braking',  name:'BZ T4 – Raidillon',               length_m:20,  brakingG_ref:2.2, sector:0, isBrakeZone:true, cornerRef:'T4 Raidillon' },
        { id:'c4',   type:'corner',   name:'T4 – Raidillon',                  length_m:60,  apexSpeed_kph:230, sector:0 },
        { id:'a4',   type:'accel',    name:'Top of Raidillon',                 length_m:40,  sector:0 },
        // SECTOR 2 — Kemmel Straight to Bus Stop
        { id:'s2',   type:'straight', name:'Kemmel Straight',                  length_m:760, sector:1 },
        { id:'b5',   type:'braking',  name:'BZ T5 – Les Combes',              length_m:100, brakingG_ref:4.8, sector:1, isBrakeZone:true, cornerRef:'T5 Les Combes' },
        { id:'c5',   type:'corner',   name:'T5 – Les Combes',                 length_m:80,  apexSpeed_kph:100, sector:1 },
        { id:'a5',   type:'accel',    name:'Exit Les Combes',                  length_m:30,  sector:1 },
        { id:'b6',   type:'braking',  name:'BZ T6 – Les Combes 2',            length_m:35,  brakingG_ref:3.2, sector:1, isBrakeZone:true, cornerRef:'T6 Les Combes 2' },
        { id:'c6',   type:'corner',   name:'T6 – Les Combes 2',               length_m:55,  apexSpeed_kph:145, sector:1 },
        { id:'a6',   type:'accel',    name:'Exit Les Combes 2',                length_m:25,  sector:1 },
        { id:'b7',   type:'braking',  name:'BZ T7 – Malmedy',                 length_m:45,  brakingG_ref:3.6, sector:1, isBrakeZone:true, cornerRef:'T7 Malmedy' },
        { id:'c7',   type:'corner',   name:'T7 – Malmedy',                    length_m:65,  apexSpeed_kph:120, sector:1 },
        { id:'a7',   type:'accel',    name:'Exit Malmedy',                     length_m:55,  sector:1 },
        { id:'b8',   type:'braking',  name:'BZ T8 – Rivage',                  length_m:75,  brakingG_ref:4.2, sector:1, isBrakeZone:true, cornerRef:'T8 Rivage' },
        { id:'c8',   type:'corner',   name:'T8 – Rivage',                     length_m:70,  apexSpeed_kph:85, sector:1 },
        { id:'a8',   type:'accel',    name:'Exit Rivage',                      length_m:45,  sector:1 },
        { id:'b9',   type:'braking',  name:"BZ T9 – Speaker's Corner",        length_m:40,  brakingG_ref:3.0, sector:1, isBrakeZone:true, cornerRef:"T9 Speaker's Corner" },
        { id:'c9',   type:'corner',   name:"T9 – Speaker's Corner",           length_m:60,  apexSpeed_kph:110, sector:1 },
        { id:'a9',   type:'accel',    name:"Exit Speaker's Corner",            length_m:35,  sector:1 },
        { id:'s3',   type:'straight', name:'Pouhon Approach',                  length_m:300, sector:1 },
        { id:'b10',  type:'braking',  name:'BZ T10 – Pouhon',                 length_m:55,  brakingG_ref:3.8, sector:1, isBrakeZone:true, cornerRef:'T10 Pouhon' },
        { id:'c10',  type:'corner',   name:'T10 – Pouhon',                    length_m:110, apexSpeed_kph:165, sector:1 },
        { id:'a10',  type:'accel',    name:'Exit Pouhon',                      length_m:30,  sector:1 },
        { id:'b11',  type:'braking',  name:'BZ T11 – Double Gauche',          length_m:40,  brakingG_ref:3.0, sector:1, isBrakeZone:true, cornerRef:'T11 Double Gauche' },
        { id:'c11',  type:'corner',   name:'T11 – Double Gauche',             length_m:75,  apexSpeed_kph:130, sector:1 },
        { id:'a11',  type:'accel',    name:'Exit Double Gauche',               length_m:25,  sector:1 },
        // SECTOR 3 — Fagnes to finish
        { id:'s4',   type:'straight', name:'Fagnes Straight',                  length_m:250, sector:2 },
        { id:'b12',  type:'braking',  name:'BZ T12 – Fagnes',                 length_m:50,  brakingG_ref:3.8, sector:2, isBrakeZone:true, cornerRef:'T12 Fagnes' },
        { id:'c12',  type:'corner',   name:'T12 – Fagnes',                    length_m:65,  apexSpeed_kph:95, sector:2 },
        { id:'a12',  type:'accel',    name:'Exit Fagnes',                      length_m:30,  sector:2 },
        { id:'b13',  type:'braking',  name:'BZ T13 – Fagnes 2',               length_m:35,  brakingG_ref:3.2, sector:2, isBrakeZone:true, cornerRef:'T13 Fagnes 2' },
        { id:'c13',  type:'corner',   name:'T13 – Fagnes 2',                  length_m:55,  apexSpeed_kph:115, sector:2 },
        { id:'a13',  type:'accel',    name:'Exit Fagnes 2',                    length_m:35,  sector:2 },
        { id:'b14',  type:'braking',  name:'BZ T14 – Campus',                 length_m:65,  brakingG_ref:4.0, sector:2, isBrakeZone:true, cornerRef:'T14 Campus' },
        { id:'c14',  type:'corner',   name:'T14 – Campus',                    length_m:70,  apexSpeed_kph:90, sector:2 },
        { id:'a14',  type:'accel',    name:'Exit Campus',                      length_m:40,  sector:2 },
        { id:'b15',  type:'braking',  name:'BZ T15 – Curve Paul Frere',       length_m:55,  brakingG_ref:3.5, sector:2, isBrakeZone:true, cornerRef:'T15 Curve Paul Frere' },
        { id:'c15',  type:'corner',   name:'T15 – Curve Paul Frere',          length_m:90,  apexSpeed_kph:200, sector:2 },
        { id:'a15',  type:'accel',    name:'Exit Paul Frere',                  length_m:55,  sector:2 },
        { id:'s5',   type:'straight', name:'Blanchimont Straight',             length_m:380, sector:2 },
        { id:'b16',  type:'braking',  name:'BZ T16 – Blanchimont',            length_m:30,  brakingG_ref:2.8, sector:2, isBrakeZone:true, cornerRef:'T16 Blanchimont' },
        { id:'c16',  type:'corner',   name:'T16 – Blanchimont',               length_m:95,  apexSpeed_kph:270, sector:2 },
        { id:'a16',  type:'accel',    name:'Exit Blanchimont',                 length_m:40,  sector:2 },
        { id:'b17',  type:'braking',  name:'BZ T17 – Blanchimont 2',          length_m:25,  brakingG_ref:2.5, sector:2, isBrakeZone:true, cornerRef:'T17 Blanchimont 2' },
        { id:'c17',  type:'corner',   name:'T17 – Blanchimont 2',             length_m:70,  apexSpeed_kph:255, sector:2 },
        { id:'a17',  type:'accel',    name:'Exit Blanchimont 2',               length_m:45,  sector:2 },
        { id:'b18',  type:'braking',  name:'BZ T18 – Bus Stop Chicane',       length_m:110, brakingG_ref:5.0, sector:2, isBrakeZone:true, cornerRef:'T18 Bus Stop Chicane' },
        { id:'c18',  type:'corner',   name:'T18 – Bus Stop Chicane (In)',      length_m:55,  apexSpeed_kph:75, sector:2 },
        { id:'a18',  type:'accel',    name:'Bus Stop mid',                     length_m:30,  sector:2 },
        { id:'b19',  type:'braking',  name:'BZ T19 – Bus Stop Exit',          length_m:25,  brakingG_ref:3.0, sector:2, isBrakeZone:true, cornerRef:'T19 Bus Stop Exit' },
        { id:'c19',  type:'corner',   name:'T19 – Bus Stop Chicane (Out)',     length_m:50,  apexSpeed_kph:95, sector:2 },
        { id:'a19',  type:'accel',    name:'Exit Bus Stop to Finish',          length_m:185, sector:2 },
    ]
};

const TRACK_REGISTRY = {
    monaco: MONACO_CONFIG,
    spa:    SPA_CONFIG,
};

// ==========================================
// PHYSICS FUNCTIONS
// ==========================================
function dragForce(v, Cd, A)    { return 0.5*AIR_RHO*Cd*A*v*v; }
function downforceN(v, car)     { const Cl=(car.downforce_factor??1.0)*1.4; return 0.5*AIR_RHO*Cl*1.85*v*v; }
function normalLoad(v, car)     { return car.weight_kg*G + downforceN(v,car); }
function engineForce(v, car)    { if(v<0.5)v=0.5; return (car.power_kw*1000*(car.transmission_efficiency??0.92))/v; }
function maxTraction(v, car)    { const mu=TIRE_MU_BASE*(car.cornering_grip??1.0)/1.55; return mu*normalLoad(v,car); }
function tractiveForce(v, car)  { return Math.min(engineForce(v,car), maxTraction(v,car), car.weight_kg*G*1.65); }
function apexSpeedForCar(aKph, car, track) {
    const gr=(car.cornering_grip??1.2)*(car.downforce_factor??1.0)/track.referenceGrip;
    return Math.min(aKph*Math.sqrt(gr), aKph*1.35);
}
function brakingGForCar(refG, car) {
    const mu=(car.cornering_grip??1.2)*0.92;
    return Math.min(refG*(mu/4.2), 1.55);
}
function estimateGear(v_kph) {
    if(v_kph<30)  return 1;
    if(v_kph<60)  return 2;
    if(v_kph<95)  return 3;
    if(v_kph<135) return 4;
    if(v_kph<185) return 5;
    if(v_kph<240) return 6;
    return 7;
}

// ==========================================
// FULL LAP PHYSICS SIMULATION
// Returns array of telemetry points with cumulative distance
// ==========================================
function simulateLap(car, track, weatherKey, tireKey, customDownforce, brakeBias, fuelLoad, tempC) {
    const wx       = WEATHER_CONFIG[weatherKey] || WEATHER_CONFIG.dry;
    const tireGrip = TIRE_GRIP[tireKey] || 1.0;

    // Temperature affects tire grip slightly (colder = less grip)
    const tempGripFactor = Math.max(0.80, Math.min(1.08, 1.0 + (tempC - 22) * 0.003));

    // In storm/wet, wet tires are much better
    const wetBonus = (weatherKey === 'wet' || weatherKey === 'storm') && tireKey === 'wet' ? 1.20 : 1.0;

    // Total grip multiplier
    const totalGrip = wx.grip * tireGrip * tempGripFactor * wetBonus * (customDownforce??1.0)*0.15 + wx.grip*0.85;

    // Fuel mass adds to weight (1L ≈ 0.74 kg for petrol)
    const effectiveCar = Object.assign({}, car, {
        weight_kg: car.weight_kg + fuelLoad * 0.74,
        cornering_grip: car.cornering_grip * totalGrip,
        downforce_factor: (car.downforce_factor??1.0) * (customDownforce??1.0),
    });

    const topV = car.top_speed_kmh / 3.6 * Math.sqrt(wx.grip); // top speed reduced in wet

    const telemetry = [], brakeZoneData = [], sectorTimes = [0,0,0];
    let totalTime = 0, totalDist = 0;
    let v = 80/3.6;

    // Pre-compute apex speeds
    const apexSpeeds = {};
    for(const seg of track.segments) {
        if(seg.type === 'corner') {
            apexSpeeds[seg.id] = apexSpeedForCar(seg.apexSpeed_kph, effectiveCar, track) / 3.6;
        }
    }
    function targetForBrake(bSeg) {
        const cid = bSeg.id.replace('b','c');
        return apexSpeeds[cid] ?? (50/3.6);
    }

    for(const seg of track.segments) {
        let res;
        const Cd = effectiveCar.drag_coefficient ?? 0.35, A = 1.85, m = effectiveCar.weight_kg;

        if(seg.type === 'straight' || seg.type === 'accel') {
            // Straight integration
            let sv=v, dist=0, t=0; const pts=[];let ns=0;
            while(dist < seg.length_m) {
                const Fd = dragForce(sv,Cd,A);
                const Ft = tractiveForce(sv, effectiveCar);
                const a  = (Ft-Fd)/m;
                sv = Math.min(sv+a*DT, topV);
                dist = Math.min(dist+sv*DT, seg.length_m);
                t += DT;
                if(dist>=ns){ pts.push({dist:Math.round(dist), speed_kph:Math.round(sv*3.6), phase:'accel', seg:seg.name, throttle:1, brake:0, decel_g:0}); ns+=8; }
                if(sv>=topV && a<=0.01) break;
            }
            if(dist<seg.length_m) t+=(seg.length_m-dist)/Math.max(sv,1);
            res={time_s:t, v_exit_ms:sv, points:pts};

        } else if(seg.type === 'braking') {
            const brakingG = brakingGForCar(seg.brakingG_ref, effectiveCar) * wx.brakingMult * (brakeBias?brakeBias/0.60:1.0);
            const vt = targetForBrake(seg);
            let sv=v, dist=0, t=0, peakDecel=0; const pts=[];let ns=0;
            while(sv>vt && dist<seg.length_m*1.8) {
                const Fd = dragForce(sv,Cd,A);
                const Fn = m*G + downforceN(sv,effectiveCar);
                const Fbr= Math.min(brakingG*G*m, TIRE_MU_BASE*(effectiveCar.cornering_grip??1.2)*Fn*0.92);
                const a  = -(Fbr+Fd)/m;
                const gv = Math.abs(a)/G;
                if(gv>peakDecel) peakDecel=gv;
                sv = Math.max(sv+a*DT, vt);
                dist += sv*DT; t+=DT;
                const brakeRatio = Math.min(1, (v-sv)/(v-vt+0.001));
                if(dist>=ns){ pts.push({dist:Math.round(dist), speed_kph:Math.round(sv*3.6), phase:'braking', seg:seg.name, decel_g:Math.round(gv*10)/10, throttle:0, brake:brakeRatio}); ns+=4; }
            }
            brakeZoneData.push({
                corner: seg.cornerRef||seg.name,
                brakingDist_m: Math.round(dist),
                brakingTime_ms: Math.round(t*1000),
                peakDecel_g: Math.round(peakDecel*10)/10,
                entry_kph: Math.round(v*3.6),
                apex_kph: Math.round(vt*3.6),
                speedLoss_kph: Math.round((v-vt)*3.6)
            });
            res={time_s:t, v_exit_ms:sv, points:pts, braking_dist_m:Math.round(dist), braking_time_ms:Math.round(t*1000), peak_decel_g:Math.round(peakDecel*10)/10};

        } else if(seg.type === 'corner') {
            const va = apexSpeeds[seg.id] ?? (50/3.6);
            const t  = seg.length_m / Math.max(va,1);
            res = {time_s:t, v_exit_ms:va, points:[
                {dist:0, speed_kph:Math.round(va*3.6), phase:'corner', seg:seg.name, decel_g:0, throttle:0.3, brake:0},
                {dist:Math.round(seg.length_m), speed_kph:Math.round(va*3.6), phase:'corner', seg:seg.name, decel_g:0, throttle:0.5, brake:0}
            ]};
        } else { continue; }

        totalTime += res.time_s;
        totalDist += seg.length_m;
        v = res.v_exit_ms;
        sectorTimes[seg.sector ?? 0] += res.time_s;

        for(const pt of (res.points||[])) {
            telemetry.push({
                dist:      Math.round(totalDist - seg.length_m + pt.dist),
                speed_kph: pt.speed_kph,
                phase:     pt.phase,
                seg:       pt.seg,
                decel_g:   pt.decel_g??0,
                throttle:  pt.throttle??0,
                brake:     pt.brake??0,
            });
        }
    }

    const speeds = telemetry.map(p=>p.speed_kph);
    return {
        lapTimeSeconds: totalTime,
        avgSpeedKph:    Math.round((totalDist/totalTime)*3.6*10)/10,
        maxSpeedKph:    Math.max(...speeds),
        minSpeedKph:    Math.min(...speeds),
        totalDist_m:    Math.round(totalDist),
        sectorTimes:    sectorTimes.map(t=>Math.round(t*1000)/1000),
        telemetry,
        brakeZoneData,
    };
}

// ==========================================
// STATE
// ==========================================
const state = {
    activeTrack: 'monaco',
    vehicles: [],
    selectedVehicle: null,
    simResult: null,
    map: null,
    telemetryChart: null,
    isRunning: false,
    animRaf: null,
    // Car setup
    downforceMult: 1.0,
    tireCompound: 'medium',
    brakeBias: 0.60,
    fuelLoad: 60,
    // Weather
    weather: 'dry',
    tempC: 22,
    // Sim params
    lapCount: 1,
    simSpeed: 1,
    // Markers
    carMarker: null,
    trailPolyline: null,
    trackCoords: null,   // [lng, lat] from GeoJSON
    // Runtime
    lapResults: [],
    rainEl: null,
};

// ==========================================
// BOOT
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    await initVehicleDropdown();
    await bootMap();
    bindUI();
});

// Track asset registry
const TRACK_ASSETS = {
    monaco: {
        trackGeoJson: 'data/Monaco_Track.geojson',
        turnsGeoJson: 'data/Monaco_Turns.geojson',
        defaultCenter: [43.7374, 7.4265],
        defaultZoom: 15,
        info: { length:'3.337 km', corners:'19', record:'1:10.166' },
        loName: 'CIRCUIT DE MONACO',
        resultTag: 'Circuit de Monaco',
    },
    spa: {
        trackGeoJson: 'data/Spa_Francorchamps_Track.geojson',
        turnsGeoJson: 'data/Spa_Francorchamps_Turns.geojson',
        defaultCenter: [50.4347, 5.9691],
        defaultZoom: 14,
        info: { length:'6.996 km', corners:'19', record:'1:41.252' },
        loName: 'CIRCUIT DE SPA-FRANCORCHAMPS',
        resultTag: 'Spa-Francorchamps',
    },
};

// Layer groups for clearing on track switch
let trackLayerGroup = null;

// ==========================================
// MAP INIT
// ==========================================
async function bootMap() {
    state.map = L.map('circuit-map', {
        center: [43.7374, 7.4265],
        zoom: 15,
        zoomControl: true,
        attributionControl: false,
        scrollWheelZoom: true,
        doubleClickZoom: false,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution:'© OpenStreetMap, © CARTO', subdomains:'abcd', maxZoom:19
    }).addTo(state.map);

    trackLayerGroup = L.layerGroup().addTo(state.map);
    await loadTrackOnMap('monaco');
    document.getElementById('map-loading')?.classList.add('hidden');
}

async function loadTrackOnMap(trackId) {
    const assets = TRACK_ASSETS[trackId];
    if(!assets) return;

    // Show loading
    const loadEl = document.getElementById('map-loading');
    if(loadEl) loadEl.classList.remove('hidden');

    // Clear existing layers
    trackLayerGroup.clearLayers();
    if(state.carMarker)  { state.map.removeLayer(state.carMarker); state.carMarker = null; }

    const [trackData, turnsData] = await Promise.all([
        fetch(assets.trackGeoJson).then(r=>r.json()),
        fetch(assets.turnsGeoJson).then(r=>r.json()),
    ]);

    // Store track coords for animation
    state.trackCoords = trackData.features[0].geometry.coordinates; // [[lng,lat], ...]

    // Track glow + line
    const glowLayer = L.geoJSON(trackData, { style:{ color:'#00FF9D', weight:10, opacity:0.15, lineCap:'round', lineJoin:'round' } });
    const lineLayer = L.geoJSON(trackData, { style:{ color:'#00FF9D', weight:3,  opacity:0.90, lineCap:'round', lineJoin:'round' } });
    trackLayerGroup.addLayer(glowLayer);
    trackLayerGroup.addLayer(lineLayer);

    // Turn markers
    turnsData.features.forEach(feat => {
        const { Turn_No, Turn_Name } = feat.properties;
        const [lng, lat] = feat.geometry.coordinates;
        const isPit = Turn_Name === 'PIT IN' || Turn_Name === 'PIT_OUT' || Turn_Name === 'PIT_STOP';
        const label  = Turn_No != null ? `T${Turn_No}` : (isPit ? '⏷' : '·');
        const col    = isPit ? '#FF6600' : '#00FF9D';
        const bg     = isPit ? 'rgba(255,102,0,0.18)' : 'rgba(0,255,157,0.12)';
        const icon   = L.divIcon({ className:'', html:`<div class="turn-marker" style="border-color:${col};background:${bg};color:${col};">${label}</div>`, iconSize:[28,28], iconAnchor:[14,14] });
        const marker = L.marker([lat,lng], {icon});
        const displayName = Turn_Name || '—';
        const popup  = `<div class="turn-popup"><div class="turn-popup-num">${Turn_No!=null?`T${Turn_No}`:'—'}</div><div class="turn-popup-name">${displayName}</div></div>`;
        marker.bindPopup(popup, {className:'circuit-popup', closeButton:false, maxWidth:200});
        marker.on('click', () => {
            const info = document.getElementById('turn-info-bar');
            if(info) { info.innerHTML=`<span class="turn-tag">${Turn_No!=null?`T${Turn_No}`:'—'}</span><span class="turn-tag-name">${displayName}</span>`; info.classList.add('visible'); }
        });
        trackLayerGroup.addLayer(marker);
    });

    // Fit and zoom
    const bounds = L.geoJSON(trackData).getBounds();
    if(bounds.isValid()) state.map.fitBounds(bounds, {padding:[30,30]});

    // Update circuit info badge
    updateCircuitBadge(assets.info);

    if(loadEl) loadEl.classList.add('hidden');
}

// ==========================================
// VEHICLE DROPDOWN
// ==========================================

// F1 display names for the circuits dropdown
const F1_DISPLAY_NAMES = {
    f1_mercedes_w11:     'Mercedes W11 (2020)',
    f1_redbull_rb16:     'Red Bull RB16 (2020)',
    f1_ferrari_sf1000:   'Ferrari SF1000 (2020)',
    f1_mclaren_mcl35:    'McLaren MCL35 (2020)',
    f1_renault_rs20:     'Renault R.S.20 (2020)',
    f1_alphatauri_at01:  'AlphaTauri AT01 (2020)',
    f1_racingpoint_rp20: 'Racing Point RP20 (2020)',
    f1_alfaromeo_c39:    'Alfa Romeo C39 (2020)',
    f1_haas_vf20:        'Haas VF-20 (2020)',
    f1_williams_fw43:    'Williams FW43 (2020)',
};

let _activeCarCategory = 'hypercars'; // 'hypercars' | 'f1'

async function initVehicleDropdown() {
    const select = document.getElementById('car-select');
    let hypercars = [];

    // Try backend for hypercar names
    try {
        const apiBase = window.CONFIG ? window.CONFIG.API_BASE_URL : 'http://localhost:8000';
        const resp = await fetch(`${apiBase}/api/vehicles`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (data && typeof data === 'object' && !Array.isArray(data)) {
            hypercars = Object.entries(data).map(([id, name]) => ({ id, name, ...(VEHICLE_SPECS[id] || {}) }));
        }
    } catch {
        // Backend unavailable — build from VEHICLE_SPECS (hypercars only)
        hypercars = Object.entries(VEHICLE_SPECS)
            .filter(([id]) => !id.startsWith('f1_'))
            .map(([id, specs]) => ({
                id, name: id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), ...specs
            }));
    }
    hypercars.sort((a, b) => a.name.localeCompare(b.name));

    const f1cars = Object.entries(F1_DISPLAY_NAMES).map(([id, name]) => ({
        id, name, ...VEHICLE_SPECS[id]
    }));

    // Store both lists on state
    state._hypercars = hypercars;
    state._f1cars = f1cars;
    state.vehicles = hypercars; // default to hypercars

    // Inject category toggle buttons above the select
    const wrap = select.closest('.car-select-wrap') || select.parentElement;
    if (!document.getElementById('circuits-cat-toggle')) {
        const toggle = document.createElement('div');
        toggle.id = 'circuits-cat-toggle';
        toggle.className = 'circuits-cat-toggle';
        toggle.innerHTML = `
            <button class="circuits-cat-btn active" data-cat="hypercars">&#127950; Hypercars</button>
            <button class="circuits-cat-btn"        data-cat="f1">&#127937; Formula 1</button>
        `;
        wrap.insertBefore(toggle, select);

        toggle.querySelectorAll('.circuits-cat-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                toggle.querySelectorAll('.circuits-cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                _activeCarCategory = btn.dataset.cat;

                // Reset selection
                state.selectedVehicle = null;
                document.getElementById('car-preview').innerHTML = '';
                document.getElementById('car-preview').classList.remove('visible');
                document.getElementById('customization-panel').style.display = 'none';

                _populateCarSelect();
            });
        });
    }

    // Update panel title
    _updateCarPanelTitle();
    _populateCarSelect();
}

function _updateCarPanelTitle() {
    const titleEl = document.querySelector('.panel-card .panel-title');
    if (titleEl && (titleEl.textContent === 'Hypercar' || titleEl.textContent === 'Formula 1')) {
        titleEl.textContent = _activeCarCategory === 'f1' ? 'Formula 1' : 'Hypercar';
    }
}

function _populateCarSelect() {
    const select = document.getElementById('car-select');
    const vehicles = _activeCarCategory === 'f1' ? state._f1cars : state._hypercars;
    state.vehicles = vehicles;

    select.innerHTML = `<option value="">— Select ${_activeCarCategory === 'f1' ? 'F1 Car' : 'Hypercar'} —</option>`;
    vehicles.forEach((v, i) => {
        const o = document.createElement('option');
        o.value = i;
        o.textContent = v.name;
        select.appendChild(o);
    });

    _updateCarPanelTitle();
}

// ==========================================
// UI BINDINGS
// ==========================================
function bindUI() {
    document.getElementById('car-select')?.addEventListener('change', e => {
        const idx = parseInt(e.target.value);
        state.selectedVehicle = !isNaN(idx) && state.vehicles[idx] ? state.vehicles[idx] : null;
        if(state.selectedVehicle) {
            updateCarPreview(state.selectedVehicle);
            document.getElementById('customization-panel').style.display = 'block';
        } else {
            document.getElementById('car-preview').innerHTML = '';
            document.getElementById('car-preview').classList.remove('visible');
            document.getElementById('customization-panel').style.display = 'none';
        }
    });

    document.getElementById('simulate-btn')?.addEventListener('click', runRealtimeSim);
    document.getElementById('stop-btn')?.addEventListener('click', stopSim);

    // Track cards
    document.querySelectorAll('.track-card').forEach(c => {
        c.addEventListener('click', () => {
            if(c.classList.contains('coming-soon')) return;
            if(state.isRunning) return; // don't switch mid-sim
            document.querySelectorAll('.track-card').forEach(x=>x.classList.remove('active'));
            c.classList.add('active');
            state.activeTrack = c.dataset.track;
            loadTrackOnMap(state.activeTrack);
            // Update result track tag
            const tag = document.getElementById('res-track-tag') || document.querySelector('.result-track-tag');
            if(tag) tag.textContent = TRACK_ASSETS[state.activeTrack]?.resultTag || state.activeTrack;
        });
    });

    // Car customization sliders
    const sliders = [
        { id:'custom-downforce', valId:'custom-downforce-val', format:v=>`${parseFloat(v).toFixed(2)}×`, key:'downforceMult' },
        { id:'custom-brake-bias', valId:'custom-brake-bias-val', format:v=>`${Math.round(parseFloat(v)*100)}% F`, key:'brakeBias', parse:parseFloat },
        { id:'custom-fuel', valId:'custom-fuel-val', format:v=>`${v} L`, key:'fuelLoad', parse:parseInt },
        { id:'custom-temp', valId:'custom-temp-val', format:v=>`${v}°C`, key:'tempC', parse:parseInt },
    ];
    sliders.forEach(({id, valId, format, key, parse}) => {
        const el = document.getElementById(id);
        if(!el) return;
        el.addEventListener('input', () => {
            const v = el.value;
            document.getElementById(valId).textContent = format(v);
            state[key] = (parse||parseFloat)(v);
        });
    });

    // Tire buttons
    document.querySelectorAll('.tire-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tire-btn').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            state.tireCompound = btn.dataset.tire;
        });
    });

    // Weather
    document.querySelectorAll('.weather-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.weather-btn').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            state.weather = btn.dataset.weather;
            document.getElementById('weather-info').textContent = WEATHER_CONFIG[state.weather]?.label || '';
            updateRainEffect();
        });
    });

    // Lap counter
    document.getElementById('lap-minus')?.addEventListener('click', () => {
        state.lapCount = Math.max(1, state.lapCount - 1);
        document.getElementById('lap-count-display').textContent = state.lapCount;
    });
    document.getElementById('lap-plus')?.addEventListener('click', () => {
        state.lapCount = Math.min(20, state.lapCount + 1);
        document.getElementById('lap-count-display').textContent = state.lapCount;
    });

    // Sim speed
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.speed-btn').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            state.simSpeed = parseInt(btn.dataset.speed);
        });
    });
}

function updateCarPreview(car) {
    const p = document.getElementById('car-preview');
    if(!p) return;
    p.innerHTML = `<div class="preview-grid">
        <div class="preview-stat"><span class="pstat-label">POWER</span><span class="pstat-val">${car.power_kw??'—'} <span class="pstat-unit">kW</span></span></div>
        <div class="preview-stat"><span class="pstat-label">WEIGHT</span><span class="pstat-val">${car.weight_kg??'—'} <span class="pstat-unit">kg</span></span></div>
        <div class="preview-stat"><span class="pstat-label">TOP SPEED</span><span class="pstat-val">${car.top_speed_kmh??'—'} <span class="pstat-unit">km/h</span></span></div>
        <div class="preview-stat"><span class="pstat-label">DRAG Cd</span><span class="pstat-val">${car.drag_coefficient?car.drag_coefficient.toFixed(3):'—'}</span></div>
    </div>`;
    p.classList.add('visible');
}

// ==========================================
// RAIN OVERLAY
// ==========================================
function updateRainEffect() {
    const mapEl = document.getElementById('circuit-map');
    if(!mapEl) return;
    // Remove old
    document.querySelectorAll('.rain-overlay').forEach(e=>e.remove());

    const wx = WEATHER_CONFIG[state.weather];
    if(!wx?.rain) return;

    const overlay = document.createElement('div');
    overlay.className = 'rain-overlay';
    const count = Math.floor(wx.intensity * 80);
    for(let i=0;i<count;i++){
        const drop = document.createElement('div');
        drop.className = 'raindrop';
        const left = Math.random()*100;
        const dur  = 0.4 + Math.random()*0.5;
        const h    = 8 + Math.random()*12;
        const delay= Math.random()*0.8;
        drop.style.cssText = `left:${left}%;height:${h}px;animation-duration:${dur}s;animation-delay:-${delay}s;opacity:${0.3+wx.intensity*0.4}`;
        overlay.appendChild(drop);
    }
    mapEl.parentElement.appendChild(overlay);
}

// ==========================================
// REALTIME SIMULATION
// ==========================================
async function runRealtimeSim() {
    if(!state.selectedVehicle) { showError('Select a car first.'); return; }
    if(state.isRunning) return;

    const car = state.selectedVehicle;

    // Simulate all laps at once (compute phase)
    const trackConfig = TRACK_REGISTRY[state.activeTrack] || MONACO_CONFIG;
    state.lapResults = [];
    for(let lap=0; lap<state.lapCount; lap++) {
        const result = simulateLap(
            car, trackConfig,
            state.weather, state.tireCompound,
            state.downforceMult, state.brakeBias,
            state.fuelLoad, state.tempC
        );
        // slight variation per lap (tire wear, throttle evolution)
        const variation = 1 + (Math.random()-0.5)*0.008 + lap*0.003; // tires degrade
        result.lapTimeSeconds *= variation;
        result.sectorTimes = result.sectorTimes.map(t => t*variation);
        state.lapResults.push(result);
    }
    state.simResult = state.lapResults[0];

    // === LIGHTS OUT ===
    await lightsOutSequence(car.name || car.id);

    // Show HUD
    const hud = document.getElementById('live-hud');
    hud.style.display = 'block';

    // Clear old trail
    if(state.trailPolyline) { state.map.removeLayer(state.trailPolyline); state.trailPolyline=null; }
    if(state.carMarker)     { state.map.removeLayer(state.carMarker); state.carMarker=null; }

    // Rain visual
    updateRainEffect();

    // Set buttons
    document.getElementById('simulate-btn').style.display = 'none';
    document.getElementById('stop-btn').style.display = 'block';
    state.isRunning = true;

    // Clear old results
    const panel = document.getElementById('result-panel');
    panel.style.display = 'none'; panel.classList.remove('visible');
    const strip = document.getElementById('lap-summary-strip');
    strip.style.display = 'flex'; strip.innerHTML = '';

    // Run laps
    for(let lap=0; lap<state.lapResults.length && state.isRunning; lap++) {
        await animateLap(lap, state.lapResults[lap], car);
        if(!state.isRunning) break;
        // Show lap chip
        addLapChip(lap, state.lapResults[lap], state.lapResults);
        await delay(300 / state.simSpeed);
    }

    // Done
    if(state.isRunning) {
        finishSimulation(car);
    }
    cleanupRun();
}

// ==========================================
// ANIMATE SINGLE LAP
// ==========================================
async function animateLap(lapIdx, result, car) {
    const coords = state.trackCoords; // [[lng,lat], ...]
    const tele   = result.telemetry;

    // Map track coords to cumulative distance
    const trackDists = buildTrackDistances(coords);
    const totalTrackLen = trackDists[trackDists.length-1];

    // Create car marker
    if(!state.carMarker) {
        const icon = L.divIcon({ className:'', html:`<div class="car-marker-div">🚗</div>`, iconSize:[24,24], iconAnchor:[12,12] });
        state.carMarker = L.marker([coords[0][1], coords[0][0]], {icon, zIndexOffset:1000}).addTo(state.map);
    }

    // Trail
    const trailCoords = [];
    const trailLayer = L.polyline([], { color:'#FF0066', weight:2.5, opacity:0.7, dashArray:'4,3' }).addTo(state.map);

    // Animate along telemetry
    const lapStartTime = performance.now();
    const realDurationMs = result.lapTimeSeconds * 1000 / state.simSpeed;

    return new Promise(resolve => {
        let lastTeleIdx = 0;

        function tick() {
            if(!state.isRunning) { trailLayer.remove(); resolve(); return; }

            const elapsed = (performance.now() - lapStartTime);
            const simProgress = Math.min(elapsed / realDurationMs, 1);

            // Find telemetry point by progress
            const simDist = simProgress * result.totalDist_m;
            while(lastTeleIdx < tele.length-1 && tele[lastTeleIdx+1].dist <= simDist) lastTeleIdx++;
            const pt = tele[Math.min(lastTeleIdx, tele.length-1)];

            // Map sim dist → track coord
            const normDist = (simDist / result.totalDist_m) * totalTrackLen;
            const [lat, lng] = interpolateTrackPos(coords, trackDists, normDist);
            state.carMarker.setLatLng([lat, lng]);

            // Trail
            trailCoords.push([lat,lng]);
            if(trailCoords.length > 120) trailCoords.shift();
            trailLayer.setLatLngs(trailCoords);

            // HUD update
            updateHUD(pt, lapIdx+1, state.lapResults.length, simProgress, result.lapTimeSeconds);

            // Phase-based car icon
            let icon;
            if(pt.phase === 'braking')      icon = '🔴';
            else if(pt.phase === 'corner')  icon = '🟡';
            else                             icon = '🚗';
            state.carMarker.setIcon(L.divIcon({ className:'', html:`<div class="car-marker-div" style="font-size:${pt.phase==='braking'?'16px':'14px'}">${icon}</div>`, iconSize:[24,24], iconAnchor:[12,12] }));

            if(simProgress >= 1) {
                trailLayer.remove();
                resolve();
                return;
            }
            state.animRaf = requestAnimationFrame(tick);
        }
        state.animRaf = requestAnimationFrame(tick);
    });
}

// ==========================================
// BUILD CUMULATIVE DISTANCES ALONG TRACK
// ==========================================
function buildTrackDistances(coords) {
    const dists = [0];
    for(let i=1;i<coords.length;i++){
        const [lng1,lat1] = coords[i-1];
        const [lng2,lat2] = coords[i];
        const d = haversine(lat1,lng1,lat2,lng2);
        dists.push(dists[i-1]+d);
    }
    return dists;
}

function haversine(lat1,lng1,lat2,lng2) {
    const R=6371000, dLat=(lat2-lat1)*Math.PI/180, dLng=(lng2-lng1)*Math.PI/180;
    const a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)**2;
    return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}

function interpolateTrackPos(coords, dists, targetDist) {
    const total = dists[dists.length-1];
    const d = ((targetDist % total) + total) % total;
    let lo=0, hi=dists.length-1;
    while(lo<hi-1){ const mid=Math.floor((lo+hi)/2); if(dists[mid]<=d) lo=mid; else hi=mid; }
    const t=(d-dists[lo])/(dists[hi]-dists[lo]||1);
    const [lng1,lat1]=coords[lo], [lng2,lat2]=coords[hi];
    return [lat1+(lat2-lat1)*t, lng1+(lng2-lng1)*t];
}

// ==========================================
// HUD UPDATE
// ==========================================
function updateHUD(pt, lapNum, totalLaps, progress, lapTotalSecs) {
    document.getElementById('hud-speed').textContent = pt.speed_kph;
    document.getElementById('hud-lap').textContent   = `${lapNum}/${totalLaps}`;
    document.getElementById('hud-time').textContent  = formatLapTime(progress * lapTotalSecs);
    document.getElementById('hud-gear').textContent  = estimateGear(pt.speed_kph);
    document.getElementById('hud-gforce').textContent= (pt.decel_g||0).toFixed(1);
    document.getElementById('hud-throttle-bar').style.width = `${(pt.throttle||0)*100}%`;
    document.getElementById('hud-brake-bar').style.width    = `${(pt.brake||0)*100}%`;
}

// ==========================================
// LAP CHIP
// ==========================================
function addLapChip(lapIdx, result, allResults) {
    const best = Math.min(...allResults.map(r=>r.lapTimeSeconds));
    const strip = document.getElementById('lap-summary-strip');
    const isBest = result.lapTimeSeconds <= best + 0.001;
    const chip = document.createElement('div');
    chip.className = `lap-chip${isBest?' best-lap':''}`;
    chip.innerHTML = `<div class="chip-lap">LAP ${lapIdx+1}${isBest?' 🏆':''}</div><div>${formatLapTime(result.lapTimeSeconds)}</div>`;
    strip.appendChild(chip);
}

// ==========================================
// FINISH SIMULATION
// ==========================================
function finishSimulation(car) {
    const results = state.lapResults;
    const best = results.reduce((b,r)=>r.lapTimeSeconds<b.lapTimeSeconds?r:b, results[0]);

    // Show results panel
    const panel = document.getElementById('result-panel');
    panel.style.display = 'block';
    setTimeout(()=>panel.classList.add('visible'), 50);

    document.getElementById('res-car-name').textContent = car.name || car.id;
    document.getElementById('res-weather-tag').textContent = state.weather.charAt(0).toUpperCase()+state.weather.slice(1);
    const trackTag = document.querySelector('.result-track-tag');
    if(trackTag) trackTag.textContent = TRACK_ASSETS[state.activeTrack]?.resultTag || state.activeTrack;

    animateValue('res-laptime', 0, best.lapTimeSeconds, 2200, v=>formatLapTime(v));
    setTimeout(()=>{ animateValue('res-avgspeed', 0, best.avgSpeedKph, 900, v=>v.toFixed(1)+' km/h'); }, 200);
    setTimeout(()=>{ animateValue('res-topspeed', 0, best.maxSpeedKph, 900, v=>Math.round(v)+' km/h'); }, 400);

    renderSectorTimes(best.sectorTimes);
    renderTelemetryChart(best.telemetry);
    renderBrakeZoneTable(best.brakeZoneData);

    // Multi-lap table
    if(results.length > 1) {
        renderLapTimesTable(results, best.lapTimeSeconds);
    }

    panel.scrollIntoView({ behavior:'smooth', block:'start' });
}

// ==========================================
// STOP
// ==========================================
function stopSim() {
    state.isRunning = false;
    if(state.animRaf) { cancelAnimationFrame(state.animRaf); state.animRaf=null; }
}

function cleanupRun() {
    state.isRunning = false;
    document.getElementById('simulate-btn').style.display = 'block';
    document.getElementById('stop-btn').style.display = 'none';
    document.getElementById('live-hud').style.display = 'none';
}

// ==========================================
// SECTOR TIMES RENDER
// ==========================================
function renderSectorTimes(sectorTimes) {
    const el = document.getElementById('sector-times');
    if(!el) return;
    el.innerHTML = sectorTimes.map((t,i)=>`<div class="sector-card"><div class="sector-label">S${i+1}</div><div class="sector-time">${formatLapTime(t)}</div></div>`).join('');
    el.classList.add('visible');
}

// ==========================================
// TELEMETRY CHART
// ==========================================
function renderTelemetryChart(telemetry) {
    const canvas = document.getElementById('telemetry-chart');
    if(!canvas || typeof Chart==='undefined') return;
    if(state.telemetryChart) { state.telemetryChart.destroy(); state.telemetryChart=null; }

    const step = Math.max(1, Math.floor(telemetry.length/200));
    const sampled = telemetry.filter((_,i)=>i%step===0);
    const labels = sampled.map(p=>p.dist+'m');
    const speeds = sampled.map(p=>p.speed_kph);
    const ptColors = sampled.map(p=> p.phase==='braking'?'rgba(255,0,102,0.9)':p.phase==='corner'?'rgba(255,165,0,0.9)':'rgba(0,255,157,0.7)');

    state.telemetryChart = new Chart(canvas, {
        type:'line',
        data:{ labels, datasets:[{ label:'Speed (km/h)', data:speeds, borderColor:'#00FF9D', borderWidth:2.5, pointBackgroundColor:ptColors, pointBorderColor:'transparent', pointRadius:sampled.map(p=>(p.phase==='braking'||p.phase==='corner')?4:0), pointHoverRadius:6, fill:true, backgroundColor:ctx=>{ const g=ctx.chart.ctx.createLinearGradient(0,0,0,280); g.addColorStop(0,'rgba(0,255,157,0.22)'); g.addColorStop(1,'rgba(0,255,157,0.00)'); return g; }, tension:0.35 }] },
        options:{ animation:{duration:1600,easing:'easeInOutQuart'}, responsive:true, maintainAspectRatio:false, interaction:{intersect:false,mode:'index'}, plugins:{ legend:{display:false}, tooltip:{ backgroundColor:'#0A120E', borderColor:'#00FF9D', borderWidth:1, titleColor:'#00FF9D', bodyColor:'#FFFFFF', padding:10, callbacks:{ title:items=>sampled[items[0].dataIndex]?.seg||'', label:item=>{ const pt=sampled[item.dataIndex]; let s=` Speed: ${item.raw} km/h`; if(pt?.decel_g) s+=`  |  Braking: ${pt.decel_g}g`; return s; }, labelColor:item=>{ const c=ptColors[item.dataIndex]; return{backgroundColor:c,borderColor:c}; } } } }, scales:{ x:{ ticks:{color:'rgba(255,255,255,0.35)',maxTicksLimit:14,font:{size:9}}, grid:{color:'rgba(255,255,255,0.04)'} }, y:{ min:0, ticks:{color:'rgba(255,255,255,0.55)',font:{family:'Orbitron',size:9}}, grid:{color:'rgba(0,255,157,0.06)'}, title:{display:true,text:'km/h',color:'#00FF9D',font:{size:10}} } } }
    });
}

// ==========================================
// BRAKING ZONE TABLE (FIXED STYLING)
// ==========================================
function renderBrakeZoneTable(brakeZones) {
    const container = document.getElementById('brake-zone-section');
    const tbody     = document.getElementById('brake-zone-body');
    if(!container || !tbody) return;

    tbody.innerHTML = '';
    brakeZones.forEach((bz,i)=>{
        const barPct  = Math.min(100, (bz.brakingDist_m/80)*100);
        const barColor= bz.peakDecel_g>=1.2?'#FF0066':bz.peakDecel_g>=0.9?'#FF8C00':'#00FF9D';
        const row = document.createElement('tr');
        row.className='bz-row';
        row.style.animationDelay=`${i*60}ms`;
        row.innerHTML=`
            <td class="bz-corner">${bz.corner}</td>
            <td class="bz-entry">${bz.entry_kph}</td>
            <td class="bz-apex">${bz.apex_kph}</td>
            <td class="bz-loss">−${bz.speedLoss_kph}</td>
            <td class="bz-dist">
                <div class="bz-bar-wrap">
                    <div class="bz-bar" style="width:${barPct}%;background:${barColor};"></div>
                    <span>${bz.brakingDist_m}m</span>
                </div>
            </td>
            <td class="bz-time">${bz.brakingTime_ms}ms</td>
            <td class="bz-g" style="color:${barColor}">${bz.peakDecel_g}g</td>`;
        tbody.appendChild(row);
    });
    container.classList.add('visible');
}

// ==========================================
// MULTI-LAP TABLE
// ==========================================
function renderLapTimesTable(results, bestTime) {
    const section = document.getElementById('lap-times-section');
    const tbody   = document.getElementById('lap-times-body');
    if(!section || !tbody) return;

    tbody.innerHTML = '';
    results.forEach((r,i)=>{
        const delta = r.lapTimeSeconds - bestTime;
        const deltaStr = delta<0.001 ? '—' : `+${delta.toFixed(3)}`;
        const isBest   = delta < 0.001;
        const row = document.createElement('tr');
        row.className = 'bz-row' + (isBest?' best-lap-row':'');
        if(isBest) row.style.cssText='background:rgba(0,255,157,0.06);';
        row.innerHTML=`
            <td style="color:rgba(255,255,255,0.5);font-size:0.75rem">L${i+1}${isBest?' 🏆':''}</td>
            <td class="bz-entry" style="font-family:'Orbitron',sans-serif;font-size:0.8rem">${formatLapTime(r.lapTimeSeconds)}</td>
            <td style="color:rgba(255,255,255,0.6);font-size:0.72rem">${formatLapTime(r.sectorTimes[0])}</td>
            <td style="color:rgba(255,255,255,0.6);font-size:0.72rem">${formatLapTime(r.sectorTimes[1])}</td>
            <td style="color:rgba(255,255,255,0.6);font-size:0.72rem">${formatLapTime(r.sectorTimes[2])}</td>
            <td style="color:${isBest?'#00FF9D':'rgba(255,100,100,0.8)'};font-size:0.72rem;font-family:'Orbitron',sans-serif">${deltaStr}</td>`;
        tbody.appendChild(row);
    });
    section.style.display = 'block';
}

// ==========================================
// F1 LIGHTS-OUT
// ==========================================
async function lightsOutSequence(carName) {
    const trackName = TRACK_ASSETS[state.activeTrack]?.loName || 'CIRCUIT DE MONACO';
    let overlay = document.getElementById('lights-overlay');
    if(!overlay) {
        overlay = document.createElement('div');
        overlay.id='lights-overlay';
        overlay.innerHTML=`
            <div class="lo-track">${trackName}</div>
            <div class="lo-car">${carName}</div>
            <div class="lo-lights">
                <div class="lo-light" id="ll1"></div><div class="lo-light" id="ll2"></div>
                <div class="lo-light" id="ll3"></div><div class="lo-light" id="ll4"></div>
                <div class="lo-light" id="ll5"></div>
            </div>
            <div class="lo-status" id="lo-status">FORMATION LAP COMPLETE</div>`;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.lo-track').textContent = trackName;
        overlay.querySelector('.lo-car').textContent=carName;
        overlay.querySelectorAll('.lo-light').forEach(l=>l.classList.remove('on'));
        overlay.querySelector('#lo-status').textContent='FORMATION LAP COMPLETE';
        overlay.querySelector('#lo-status').className='lo-status';
    }
    overlay.classList.remove('fade-out');
    overlay.style.display='flex';
    void overlay.offsetWidth;
    overlay.classList.add('visible');
    await delay(900);
    for(let i=1;i<=5;i++) { document.getElementById(`ll${i}`)?.classList.add('on'); await delay(700); }
    await delay(1200);
    document.querySelectorAll('.lo-light').forEach(l=>l.classList.remove('on'));
    const status=document.getElementById('lo-status');
    status.textContent="IT'S LIGHTS OUT AND AWAY WE GO!";
    status.classList.add('go');
    await delay(1000);
    overlay.classList.add('fade-out');
    await delay(550);
    overlay.style.display='none';
    overlay.classList.remove('visible','fade-out');
}

function updateCircuitBadge(info) {
    const badge = document.querySelector('.circuit-info-badge');
    if(!badge) return;
    const rows = badge.querySelectorAll('.cib-val');
    if(rows[0]) rows[0].textContent = info.length;
    if(rows[1]) rows[1].textContent = info.corners;
    if(rows[2]) rows[2].textContent = info.record;
}

// ==========================================
// ANIMATED VALUE
// ==========================================
function animateValue(id, from, to, durationMs, formatter) {
    const el=document.getElementById(id);
    if(!el) return;
    const start=performance.now();
    function tick(now) {
        const p=Math.min((now-start)/durationMs,1), e=1-Math.pow(1-p,3);
        el.textContent=formatter(from+(to-from)*e);
        if(p<1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function delay(ms) { return new Promise(r=>setTimeout(r,ms)); }
function showError(msg) {
    const e=document.getElementById('sim-error');
    if(e){ e.textContent=msg; e.classList.add('visible'); setTimeout(()=>e.classList.remove('visible'),4000); }
}
