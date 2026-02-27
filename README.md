# 🏎️ Hypercar Performance Simulator v3.0

![License](https://img.shields.io/badge/license-MIT-red.svg)
![Python](https://img.shields.io/badge/python-3.8+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![Physics](https://img.shields.io/badge/Physics-Fully_Customizable-00ff9d.svg)
![F1](https://img.shields.io/badge/Formula_1-2020_Season-e10600.svg)

A physics-based vehicle performance simulator featuring **50+ hypercars and all 10 Formula 1 teams from the 2020 season**, an advanced customizable physics engine, comprehensive tuning system, real-time telemetry, and real-world circuit lap simulation. Runs fully offline — no backend required for F1 cars or drag simulation.

---

## 🎉 What's New in v3.0: Formula 1 + Offline Physics

### 🏁 Formula 1 2020 Season
All 10 constructor teams fully modelled with accurate physics:

| Team | Car | Engine |
|------|-----|--------|
| Mercedes | W11 | Mercedes M11 EQ Power+ Hybrid |
| Red Bull Racing | RB16 | Honda RA620H Hybrid |
| Ferrari | SF1000 | Ferrari 065 Hybrid |
| McLaren | MCL35 | Renault E-Tech 20 Hybrid |
| Renault | R.S.20 | Renault E-Tech 20 Hybrid |
| AlphaTauri | AT01 | Honda RA620H Hybrid |
| Racing Point | RP20 | Mercedes M10 EQ Power+ Hybrid |
| Alfa Romeo | C39 | Ferrari 065 Hybrid |
| Haas | VF-20 | Ferrari 065 Hybrid |
| Williams | FW43 | Mercedes M10 EQ Power+ Hybrid |

F1 physics are calibrated against real 2020 benchmarks:
- Mercedes W11: **0–100 km/h in ~2.6s**, quarter mile in ~8.8s
- F1-specific gear ratios derived from actual shift speeds (G1 @82 km/h → G8 @340 km/h)
- Pirelli slick tyre warm-up model (cold μ = 0.78 → warm μ = 1.65)
- Downforce contribution to traction (~640 kg at 300 km/h)
- Seamless 50ms gear changes

### ⚡ Offline-First Architecture
The simulator no longer requires the backend to be running for most operations:
- **Drag simulation**: Frontend physics engine handles all vehicle categories when the backend is unavailable or returns a 404 for unknown IDs
- **Vehicle selection**: F1 cars and hypercars load from an embedded catalogue — no API call needed
- **Circuits page**: F1 car specs are built into `circuits-rt.js` — works offline

### 🗂️ Category Toggle
Both the **Simulator** and **Circuits** pages now have a **🏎 Hypercars / 🏁 Formula 1** toggle above the car selector. Switching categories repopulates the dropdown instantly without a page reload.

---

## ✨ Full Feature List

### 🏁 8 Race Modes (Simulator)
- **Quarter Mile (402m)** — classic drag race
- **Half Mile (805m)** — extended acceleration test
- **1 Mile (1609m)** — top speed challenge
- **Custom Distance** — set your own distance
- **Lap Race** — multi-lap circuit racing
- **Acceleration Zone** — speed-range tests (e.g. 0–100, 100–200 km/h)
- **Roll Race** — rolling start (60–200 km/h)
- **Top Speed** — maximum velocity run

### 🗺️ Real-World Circuits (Circuits Page)
- **Circuit de Monaco** — 3.337 km, 19 corners, lap record 1:10.166
- **Spa-Francorchamps** — 6.996 km, 19 corners
- **Autodromo di Monza** — 5.793 km, 11 corners
- Physics-accurate braking zones, sector times, full telemetry
- Weather conditions: Dry / Damp / Wet / Storm
- Car setup: downforce, tyre compound, brake bias

### 🚗 Vehicle Roster

**Hypercars (40+)**
- Koenigsegg: Jesko, Jesko Attack, Regera, Agera RS
- Bugatti: Chiron Super Sport 300+, Bolide, Veyron SS
- McLaren: Speedtail, P1, Senna, 765LT, 720S
- Ferrari: SF90, LaFerrari, F8 Tributo, 812 Superfast
- Lamborghini: Revuelto, Aventador SVJ, Sián, Huracán STO
- Porsche: 918 Spyder, 911 GT2 RS, 911 Turbo S
- Electric: Rimac Nevera, Lotus Evija, Aspark Owl, Pininfarina Battista
- American: Hennessey Venom F5, SSC Tuatara, Ford GT, Corvette Z06, Dodge Viper ACR
- Others: Aston Martin Valkyrie, Mercedes-AMG ONE, Gordon Murray T.50, Czinger 21C, Pagani Huayra R, Acura NSX Type S, Nissan GT-R Nismo

**Formula 1 (10 teams — 2020 season)**
All 10 constructors listed above.

### 🔧 Tuning System
- **Engine**: Stock → Extreme (+75% power)
- **Tyres**: Street → Drag Radials (+70% grip)
- **Aero**: Multiple drag configurations
- **Weight**: Up to −300 kg reduction
- **Transmission**: Stock → Instant shifts
- **Boost Pressure**: 0.5× – 2.0×
- **Launch RPM**: 2,000–8,000 RPM
- **Nitrous**: 50–200 HP injection

### ⚙️ Physics Customization (5 Presets + 50+ Parameters)
1. 🔥 Tire Physics — temperature, grip, wear
2. ⚖️ Weight Transfer — distribution, CG height
3. 🚀 Launch Control — RPM targeting, clutch slip
4. 💨 Turbo/Boost — pressure, spool rate
5. 🪂 DRS / Active Aero — drag reduction, downforce
6. ⚙️ Gearbox — shift duration, power loss
7. ⛽ Fuel System — consumption, tank capacity
8. 🛑 Brake System — thermal fade, bias
9. ⚡ Hybrid — battery SOC, regen
10. 🎯 Traction Control — intervention levels
11. 🌦️ Weather — track condition, rain, wind

**Quick Presets**: Arcade · Realistic · Maximum · Endurance Race · Wet Race

### 📈 Live Telemetry
- Animated speedometers with RPM and gear display
- Distance progress tracking
- Power output visualization
- 0–60, 0–100, 0–200 km/h split times
- Quarter-mile time and trap speed

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (3.10+ recommended)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Installation

```bash
# 1. Extract the project
unzip Hypercar_Sim.zip
cd Hypercar_Sim

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the backend
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### Opening the Frontend

The frontend is served directly by the backend:

| Page | URL |
|------|-----|
| Home | `http://localhost:8000/home.html` |
| Simulator | `http://localhost:8000/simulator.html` |
| Circuits | `http://localhost:8000/circuits.html` |
| About | `http://localhost:8000/about.html` |

> **No backend? No problem.** The simulator and circuits pages work fully offline — vehicles load from the embedded catalogue and drag simulation runs in the browser using the built-in physics engine.

---

## 🎮 Usage Guide

### Drag Racing (Simulator Page)
1. Select a category: **🏎 Hypercars** or **🏁 Formula 1**
2. Pick up to 3 vehicles from the dropdowns
3. Choose a race mode using the top tabs
4. Set environment conditions (temperature, altitude)
5. Click **Start Race** or press `Space`

### Lap Simulation (Circuits Page)
1. Select a circuit from the track list
2. Choose a category and car
3. Adjust car setup (downforce, tyre compound, brake bias)
4. Click **Simulate Lap**

### Vehicle Tuning
1. Select a vehicle in the Simulator page
2. Click the 🔧 button next to the vehicle
3. Adjust engine, tyres, aero, and weight
4. Click **Apply**

### Physics Customization
1. Click **⚙️ Open Physics Settings**
2. Choose a preset or adjust individual sliders
3. Click **Apply Physics Settings** — the button turns green showing **Physics: CUSTOM**
4. Run a race to see the effects

### Keyboard Shortcuts
- `1`–`8` — switch race modes
- `Space` — start race
- `R` — reset

---

## 🔬 Physics Engines

### How Simulation Works

**Hypercars** use the backend Python physics engine (three tiers):
- **Basic** — simple force calculation
- **Improved** *(default)* — tyre thermals, launch control, turbo lag, DRS, weight transfer
- **Configurable** — all of the above plus 50+ user-adjustable parameters

**F1 cars and offline fallback** use the frontend JavaScript physics engine (`sim-physics.js`):
- Identical mathematical model ported to JS
- F1-specific gear ratios, tyre model, and downforce
- Activates automatically when the backend is unavailable or the selected vehicle is an F1 car

### Core Physics Equations

```
Aerodynamic drag:   F_drag = 0.5 × ρ × Cd × A × v²
Rolling resistance: F_roll = Crr × m × g
Downforce:          F_df   = 0.5 × ρ × CL × A × v²
Max traction:       F_max  = μ × (m × g + F_df)
Drive force:        F_d    = (τ × G_ratio × G_final × η) / r_tyre
Net force:          F_net  = min(F_d, F_max) − F_drag − F_roll
Acceleration:       a      = F_net / m
```

---

## 📊 API Reference

### `GET /api/vehicles`
Returns all hypercar IDs and display names.

### `POST /api/simulate/drag`
Runs a drag race simulation.

```json
{
  "vehicle_ids": ["koenigsegg_jesko", "f1_mercedes_w11"],
  "environment": {
    "temperature_celsius": 20,
    "altitude_meters": 0
  },
  "max_time": 30,
  "target_distance": 402.336,
  "tuning_mods": {},
  "physics_config": {},
  "preset_config": "realistic"
}
```

> **Note:** F1 vehicle IDs (`f1_*`) are not in the backend database and will return a 404. The frontend automatically falls back to the JS physics engine for these IDs.

### `GET /api/health`
Returns backend status and number of vehicles loaded.

---

## 📁 Project Structure

```
Hypercar_Sim/
├── app/                              # Python backend (FastAPI)
│   ├── main.py                       # API routes
│   ├── database.py                   # Vehicle database (CSV loader)
│   ├── models.py                     # Pydantic data models
│   ├── physics.py                    # Basic physics engine
│   ├── physics_improved.py           # Improved physics engine
│   ├── physics_customizable.py       # Configurable physics engine
│   ├── physics_config.py             # Physics config + presets
│   └── tuning.py                     # Tuning system
├── frontend/                         # Static web frontend
│   ├── simulator.html                # Drag race simulator
│   ├── circuits.html                 # Real-world circuit lap sim
│   ├── home.html                     # Landing page
│   ├── about.html                    # About page
│   ├── sim.js                        # Simulator logic + race engine
│   ├── sim-physics.js                # Frontend JS physics engine (F1 + offline)
│   ├── car-data.js                   # Unified vehicle catalogue (hypercars + F1)
│   ├── vehicle-selector.js           # Vehicle picker with category toggle
│   ├── circuits-rt.js                # Circuit simulation engine
│   ├── render.js                     # Canvas race renderer
│   ├── tuning.js                     # Tuning panel UI
│   ├── physics-customization-ui.js   # Physics settings UI
│   └── config.js                     # API base URL config
├── hypercar_data.csv                 # Hypercar gear/spec database
├── requirements.txt
└── README.md
```

---

## 🛠️ Extending the Simulator

### Add a New Hypercar
1. Add a row to `hypercar_data.csv` with the car's gear ratios
2. Add its specs to the `_get_vehicle_specs()` dict in `app/database.py`
3. Add physics specs to `HYPERCAR_SPECS` in `frontend/sim-physics.js`
4. Add circuit specs to `VEHICLE_SPECS` in `frontend/circuits-rt.js`
5. Add a catalogue entry in `frontend/car-data.js`

### Add a New F1 Season
In `frontend/car-data.js`, add 10 new entries with `carCategory: 'f1'` and the new `year`. The physics engine will pick them up automatically if matching specs exist in `sim-physics.js`.

### Add a New Circuit
Add a GeoJSON track file to `frontend/data/` and register it in the `TRACKS` array in `circuits-rt.js`.

### Create a Custom Physics Preset
Add a new entry to `PRESET_CONFIGS` in `app/physics_config.py`.

---

## 📝 Changelog

### v3.0 — Formula 1 + Offline Engine
- ✅ All 10 Formula 1 2020 constructor teams added
- ✅ F1 physics calibrated to real 2020 benchmarks
- ✅ Category toggle (Hypercars / Formula 1) on Simulator and Circuits pages
- ✅ Frontend JS physics engine — simulation works fully offline
- ✅ Backend routing fixed for `simulator.html` and `circuits.html`
- ✅ Vehicle catalogue (`car-data.js`) as single source of truth

### v2.0 — Physics Customization
- ✅ 50+ physics parameters with full UI control
- ✅ 5 quick presets (Arcade, Realistic, Maximum, Endurance, Wet Race)
- ✅ Weather system (Dry / Damp / Wet / Storm)
- ✅ Fuel, brake thermal, and hybrid modelling

### v1.0 — Initial Release
- ✅ 30+ hypercars, basic physics, tuning system

---

## 📋 Roadmap

- [ ] Additional F1 seasons (2021, 2022, 2023)
- [ ] Save and share physics configs via URL
- [ ] Additional circuits (Silverstone, Suzuka, Nürburgring)
- [ ] Championship / points mode
- [ ] Side-by-side telemetry comparison view
- [ ] Mobile-responsive layout

---

## 🐛 Known Limitations

- F1 drag simulation uses the frontend engine; backend presets (Wet Race, Endurance) do not apply to F1 cars
- Some hypercar specs are manufacturer estimates rather than independently verified figures
- Hybrid system modelling is simplified (no battery depletion during a drag run)

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 📞 Contact

- **GitHub**: [@jude-pinkman](https://github.com/jude-pinkman)
- **Email**: judesahai0@gmail.com
- **Issues**: [GitHub Issues](https://github.com/jude-pinkman/Hypercar_Sim/issues)

---

*Made with ❤️ for motorsport enthusiasts. Star the repo if you find it useful!*
