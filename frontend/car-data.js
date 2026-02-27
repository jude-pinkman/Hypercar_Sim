// ==========================================
// CAR DATA — Structured catalogue
// carCategory: 'hypercars' | 'f1'
// Add future seasons by pushing new objects
// ==========================================

export const CAR_CATALOGUE = [
    // ---- HYPERCARS ----
    { carCategory:'hypercars', id:'koenigsegg_jesko',          team:'Koenigsegg', model:'Jesko',                    year:2020, engine:'5.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'koenigsegg_jesko_attack',   team:'Koenigsegg', model:'Jesko Attack',             year:2020, engine:'5.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'koenigsegg_regera',         team:'Koenigsegg', model:'Regera',                   year:2016, engine:'5.0L twin-turbo V8 + 3 e-motors' },
    { carCategory:'hypercars', id:'koenigsegg_agera_rs',       team:'Koenigsegg', model:'Agera RS',                 year:2015, engine:'5.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'bugatti_chiron_ss',         team:'Bugatti',    model:'Chiron Super Sport 300+',  year:2021, engine:'8.0L quad-turbo W16' },
    { carCategory:'hypercars', id:'bugatti_bolide',            team:'Bugatti',    model:'Bolide',                   year:2024, engine:'8.0L quad-turbo W16' },
    { carCategory:'hypercars', id:'bugatti_veyron_ss',         team:'Bugatti',    model:'Veyron Super Sport',       year:2010, engine:'8.0L quad-turbo W16' },
    { carCategory:'hypercars', id:'hennessey_venom_f5',        team:'Hennessey',  model:'Venom F5',                 year:2020, engine:'6.6L twin-turbo V8' },
    { carCategory:'hypercars', id:'ssc_tuatara',               team:'SSC',        model:'Tuatara',                  year:2020, engine:'5.9L twin-turbo V8' },
    { carCategory:'hypercars', id:'pagani_huayra_r',           team:'Pagani',     model:'Huayra R',                 year:2021, engine:'6.0L NA V12' },
    { carCategory:'hypercars', id:'pagani_zonda_r',            team:'Pagani',     model:'Zonda R',                  year:2009, engine:'6.0L NA V12' },
    { carCategory:'hypercars', id:'mclaren_speedtail',         team:'McLaren',    model:'Speedtail',                year:2019, engine:'4.0L twin-turbo V8 hybrid' },
    { carCategory:'hypercars', id:'mclaren_p1',                team:'McLaren',    model:'P1',                       year:2013, engine:'3.8L twin-turbo V8 hybrid' },
    { carCategory:'hypercars', id:'mclaren_senna',             team:'McLaren',    model:'Senna',                    year:2018, engine:'4.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'mclaren_765lt',             team:'McLaren',    model:'765LT',                    year:2020, engine:'4.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'mclaren_720s',              team:'McLaren',    model:'720S',                     year:2017, engine:'4.0L twin-turbo V8' },
    { carCategory:'hypercars', id:'aston_valkyrie',            team:'Aston Martin',model:'Valkyrie',                year:2021, engine:'6.5L NA V12 hybrid' },
    { carCategory:'hypercars', id:'rimac_nevera',              team:'Rimac',      model:'Nevera',                   year:2021, engine:'4× electric motors' },
    { carCategory:'hypercars', id:'lotus_evija',               team:'Lotus',      model:'Evija',                    year:2020, engine:'4× electric motors' },
    { carCategory:'hypercars', id:'aspark_owl',                team:'Aspark',     model:'Owl',                      year:2020, engine:'4× electric motors' },
    { carCategory:'hypercars', id:'pininfarina_battista',      team:'Pininfarina',model:'Battista',                 year:2020, engine:'4× electric motors' },
    { carCategory:'hypercars', id:'ferrari_sf90',              team:'Ferrari',    model:'SF90 Stradale',            year:2019, engine:'4.0L twin-turbo V8 hybrid' },
    { carCategory:'hypercars', id:'ferrari_laferrari',         team:'Ferrari',    model:'LaFerrari',                year:2013, engine:'6.3L NA V12 hybrid' },
    { carCategory:'hypercars', id:'ferrari_f8',                team:'Ferrari',    model:'F8 Tributo',               year:2019, engine:'3.9L twin-turbo V8' },
    { carCategory:'hypercars', id:'ferrari_812',               team:'Ferrari',    model:'812 Superfast',            year:2017, engine:'6.5L NA V12' },
    { carCategory:'hypercars', id:'lamborghini_revuelto',      team:'Lamborghini',model:'Revuelto',                 year:2023, engine:'6.5L NA V12 hybrid' },
    { carCategory:'hypercars', id:'lamborghini_aventador_svj', team:'Lamborghini',model:'Aventador SVJ',            year:2018, engine:'6.5L NA V12' },
    { carCategory:'hypercars', id:'lamborghini_sian',          team:'Lamborghini',model:'Sian FKP 37',              year:2019, engine:'6.5L NA V12 hybrid' },
    { carCategory:'hypercars', id:'lamborghini_huracan_sto',   team:'Lamborghini',model:'Huracán STO',              year:2020, engine:'5.2L NA V10' },
    { carCategory:'hypercars', id:'porsche_918',               team:'Porsche',    model:'918 Spyder',               year:2013, engine:'4.6L NA V8 hybrid' },
    { carCategory:'hypercars', id:'porsche_911_gt2_rs',        team:'Porsche',    model:'911 GT2 RS',               year:2017, engine:'3.8L twin-turbo H6' },
    { carCategory:'hypercars', id:'porsche_911_turbo_s',       team:'Porsche',    model:'911 Turbo S',              year:2020, engine:'3.8L twin-turbo H6' },
    { carCategory:'hypercars', id:'mercedes_amg_one',          team:'Mercedes-AMG',model:'AMG ONE',                 year:2022, engine:'1.6L turbo V6 hybrid (F1-derived)' },
    { carCategory:'hypercars', id:'gordon_murray_t50',         team:'Gordon Murray',model:'T.50',                   year:2022, engine:'4.0L NA V12' },
    { carCategory:'hypercars', id:'czinger_21c',               team:'Czinger',    model:'21C',                      year:2020, engine:'2.88L twin-turbo V8 hybrid' },
    { carCategory:'hypercars', id:'ford_gt',                   team:'Ford',       model:'GT',                       year:2017, engine:'3.5L twin-turbo EcoBoost V6' },
    { carCategory:'hypercars', id:'corvette_z06',              team:'Chevrolet',  model:'Corvette Z06',             year:2022, engine:'5.5L NA flat-plane V8' },
    { carCategory:'hypercars', id:'dodge_viper_acr',           team:'Dodge',      model:'Viper ACR',                year:2016, engine:'8.4L NA V10' },
    { carCategory:'hypercars', id:'acura_nsx_type_s',          team:'Acura',      model:'NSX Type S',               year:2021, engine:'3.5L twin-turbo V6 hybrid' },
    { carCategory:'hypercars', id:'nissan_gtr_nismo',          team:'Nissan',     model:'GT-R NISMO',               year:2022, engine:'3.8L twin-turbo V6' },

    // ---- FORMULA 1 — 2020 Season ----
    { carCategory:'f1', id:'f1_mercedes_w11',         team:'Mercedes',        model:'W11',     year:2020, engine:'Mercedes M11 EQ Power+ 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_redbull_rb16',         team:'Red Bull Racing', model:'RB16',    year:2020, engine:'Honda RA620H 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_ferrari_sf1000',       team:'Ferrari',         model:'SF1000',  year:2020, engine:'Ferrari 065 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_mclaren_mcl35',        team:'McLaren',         model:'MCL35',   year:2020, engine:'Renault E-Tech 20 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_renault_rs20',         team:'Renault',         model:'R.S.20',  year:2020, engine:'Renault E-Tech 20 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_alphatauri_at01',      team:'AlphaTauri',      model:'AT01',    year:2020, engine:'Honda RA620H 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_racingpoint_rp20',     team:'Racing Point',    model:'RP20',    year:2020, engine:'Mercedes M10 EQ Power+ 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_alfaromeo_c39',        team:'Alfa Romeo',      model:'C39',     year:2020, engine:'Ferrari 065 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_haas_vf20',            team:'Haas',            model:'VF-20',   year:2020, engine:'Ferrari 065 1.6L V6 Hybrid' },
    { carCategory:'f1', id:'f1_williams_fw43',        team:'Williams',        model:'FW43',    year:2020, engine:'Mercedes M10 EQ Power+ 1.6L V6 Hybrid' },
];

// ---- F1 car physics specs (same schema as VEHICLE_SPECS) ----
// All 2020 F1 cars share ~950kW, ~740kg. Individual differences tuned per team.
export const F1_VEHICLE_SPECS = {
    f1_mercedes_w11:     { power_kw:950, weight_kg:746, drag_coefficient:0.720, top_speed_kmh:372, cornering_grip:3.20, downforce_factor:3.50, transmission_efficiency:0.98 },
    f1_redbull_rb16:     { power_kw:940, weight_kg:744, drag_coefficient:0.730, top_speed_kmh:368, cornering_grip:3.15, downforce_factor:3.45, transmission_efficiency:0.98 },
    f1_ferrari_sf1000:   { power_kw:920, weight_kg:746, drag_coefficient:0.740, top_speed_kmh:360, cornering_grip:3.05, downforce_factor:3.30, transmission_efficiency:0.98 },
    f1_mclaren_mcl35:    { power_kw:915, weight_kg:748, drag_coefficient:0.735, top_speed_kmh:358, cornering_grip:3.00, downforce_factor:3.25, transmission_efficiency:0.98 },
    f1_renault_rs20:     { power_kw:910, weight_kg:746, drag_coefficient:0.738, top_speed_kmh:356, cornering_grip:2.95, downforce_factor:3.20, transmission_efficiency:0.98 },
    f1_alphatauri_at01:  { power_kw:938, weight_kg:745, drag_coefficient:0.733, top_speed_kmh:365, cornering_grip:3.05, downforce_factor:3.35, transmission_efficiency:0.98 },
    f1_racingpoint_rp20: { power_kw:945, weight_kg:743, drag_coefficient:0.722, top_speed_kmh:369, cornering_grip:3.10, downforce_factor:3.40, transmission_efficiency:0.98 },
    f1_alfaromeo_c39:    { power_kw:918, weight_kg:747, drag_coefficient:0.742, top_speed_kmh:357, cornering_grip:2.98, downforce_factor:3.22, transmission_efficiency:0.98 },
    f1_haas_vf20:        { power_kw:916, weight_kg:748, drag_coefficient:0.745, top_speed_kmh:355, cornering_grip:2.92, downforce_factor:3.18, transmission_efficiency:0.98 },
    f1_williams_fw43:    { power_kw:943, weight_kg:745, drag_coefficient:0.726, top_speed_kmh:363, cornering_grip:2.88, downforce_factor:3.15, transmission_efficiency:0.98 },
};

// ---- Team colours (used for category toggle accent + tooltip badge) ----
export const F1_TEAM_COLORS = {
    'Mercedes':        '#00D2BE',
    'Red Bull Racing': '#1E41FF',
    'Ferrari':         '#DC0000',
    'McLaren':         '#FF8000',
    'Renault':         '#FFF500',
    'AlphaTauri':      '#2B4562',
    'Racing Point':    '#F596C8',
    'Alfa Romeo':      '#9B0000',
    'Haas':            '#B6BABD',
    'Williams':        '#005AFF',
};

// ---- Helper: get cars filtered by category ----
export function getCarsByCategory(category) {
    return CAR_CATALOGUE.filter(c => c.carCategory === category);
}

// ---- Helper: group cars by team within a category ----
export function groupByTeam(cars) {
    const grouped = {};
    cars.forEach(car => {
        if (!grouped[car.team]) grouped[car.team] = [];
        grouped[car.team].push(car);
    });
    // Sort teams alphabetically, cars within team alphabetically by model
    const sorted = {};
    Object.keys(grouped).sort().forEach(team => {
        sorted[team] = grouped[team].sort((a,b) => a.model.localeCompare(b.model));
    });
    return sorted;
}
