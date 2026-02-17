# 🏎️ Hypercar Performance Simulator v2.0 - FULLY CUSTOMIZABLE EDITION

![License](https://img.shields.io/badge/license-MIT-red.svg)
![Python](https://img.shields.io/badge/python-3.8+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![Physics](https://img.shields.io/badge/Physics-Fully_Customizable-00ff9d.svg)

A physics-based hypercar drag race simulator featuring 50+ vehicles, **advanced customizable physics engine**, comprehensive tuning system, and real-time telemetry visualization. Experience the raw power of the world's most extreme hypercars through accurate simulation with **complete control over every physics parameter**.

![Hypercar Simulator](https://via.placeholder.com/1200x400/0D0D0D/00ff9d?text=Hypercar+Performance+Simulator+v2.0)

## 🎉 NEW in v2.0: Complete Physics Customization

### ⚙️ Advanced Physics Panel
**NOW WITH FULL UI CONTROL** - No more editing code files!

- **5 Quick Presets**: Arcade, Realistic, Maximum, Endurance Race, Wet Race
- **50+ Parameters**: Complete control over every aspect of simulation physics
- **Real-time Adjustment**: Sliders, toggles, and dropdowns with instant feedback
- **Professional Interface**: Dark-themed UI matching the simulator aesthetic
- **Visual Status**: Button shows "Physics: CUSTOM" when custom physics active

### 🎯 Customizable Physics Categories

1. **🔥 Tire Physics** - Temperature modeling, grip coefficient, wear rate
2. **⚖️ Weight Transfer** - Distribution, coefficients, CG height
3. **🚀 Launch Control** - RPM targeting, clutch slip, traction limits
4. **💨 Turbo/Boost** - Boost pressure, spool rates, power multipliers
5. **🪂 DRS / Active Aero** - Drag reduction, downforce trade-offs
6. **⚙️ Gearbox** - Shift duration, power loss, per-gear settings
7. **⛽ Fuel System** - Consumption rates, tank capacity, weight effects
8. **🛑 Brake System** - Thermal modeling, fade coefficients
9. **⚡ Hybrid System** - Battery SOC, discharge rates, regen efficiency
10. **🎯 Traction Control** - Intervention levels, aggression modes
11. **🌦️ Weather Conditions** - Track conditions, rain, temperature, wind

## ✨ Core Features

### 🏁 8 Race Modes
- **Quarter Mile (402m)** - Classic drag race
- **Half Mile (805m)** - Extended acceleration test
- **1 Mile (1609m)** - Top speed challenge
- **Custom Distance** - Set your own distance
- **Lap Race** - Circuit racing with multiple laps
- **Acceleration Zone** - 0-100, 100-200 km/h tests
- **Roll Race** - Rolling start (60-200 km/h)
- **Top Speed** - Maximum velocity runs

### 🚗 50+ Hypercars
- **Koenigsegg**: Jesko, Agera RS, Regera, One:1, Gemera
- **Bugatti**: Chiron SS 300+, Bolide, Veyron SS, Divo
- **McLaren**: Speedtail, P1, 720S, Senna, Elva
- **Ferrari**: SF90, LaFerrari, F8 Tributo, 812 Superfast
- **Lamborghini**: Aventador SVJ, Huracán, Revuelto
- **Porsche**: 918 Spyder, 911 Turbo S, Taycan Turbo S
- **Electric**: Rimac Nevera, Lotus Evija, Aspark Owl, Pininfarina Battista
- **American**: Hennessey Venom F5, SSC Tuatara, Tesla Model S Plaid
- And many more!

### 🔧 Advanced Tuning System
- **Engine**: Stock → Extreme (+75% power)
- **Tires**: Street → Drag Radials (+70% grip)
- **Aero**: Multiple drag configurations
- **Weight**: Up to -300kg reduction
- **Transmission**: Stock → Instant shifts
- **Boost Pressure**: 0.5x - 2.0x
- **Launch RPM**: 2000-8000 RPM
- **Nitrous**: 50-200 HP injection

### 📊 Real Physics Simulation
- Aerodynamic drag with altitude/temp effects
- Rolling resistance with tire compounds
- Engine torque curve interpolation
- Intelligent gear ratio optimization
- Hybrid system modeling
- Environmental factors
- Traction limits and launch control
- Weight transfer dynamics
- **Tire thermal modeling**
- **Fuel consumption**
- **Brake fade**
- **Weather effects**

### 📈 Live Telemetry
- Real-time speedometers with animated needles
- Distance tracking with progress bars
- RPM monitoring with redline indicators
- Current gear display
- Power output visualization
- Comprehensive metrics (0-60, 0-100, 0-200, quarter-mile)
- Split times at speed milestones

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (3.10+ recommended)
- Modern web browser

### Installation

1. **Download and extract**
```bash
unzip Hypercar_Sim.zip
cd Hypercar_Sim
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start backend**
```bash
uvicorn app.main:app --reload --port 8000
```
API runs at `http://localhost:8000`

4. **Open frontend**
```bash
# Open frontend/simulator.html directly
# OR use local server:
cd frontend
python -m http.server 8080
```
Visit `http://localhost:8080/simulator.html`

## 🎮 Usage Guide

### 🏎️ Basic Racing
1. Select vehicles from dropdown
2. Choose race mode (top tabs)
3. Set environment (temp, altitude)
4. Click "Start Race" or press Space

### 🔧 Vehicle Tuning
1. Select vehicle → Click 🔧 button
2. Adjust engine, tires, aero, weight
3. Apply changes

### ⚙️ Physics Customization ⭐ NEW!
1. Click **"⚙️ Open Physics Settings"**
2. Choose preset OR customize sliders
3. Click **"Apply Physics Settings"**
4. Button shows **"Physics: CUSTOM"**
5. Run race to see dramatic effects!

### Quick Preset Guide
- **Arcade**: Max grip, simplified (beginners)
- **Realistic**: Balanced simulation (comparisons)
- **Maximum**: All features (enthusiasts)
- **Endurance**: Fuel/tire management
- **Wet Race**: Rain conditions

### ⌨️ Keyboard Shortcuts
- `1-8`: Switch race modes
- `Space`: Start race
- `R`: Reset

## 🔬 Physics Engines

### Three Engines Available
1. **Basic** - Simple calculations
2. **Improved** - Default, enhanced physics
3. **Configurable** ⭐ - 50+ parameters, used when custom physics active

### Core Equations
```
Drag = 0.5 × ρ × Cd × A × v²
Rolling = Crr × m × g × friction
Drive = (Torque × Gear × Final × η) / Radius
Net Force = Drive - Drag - Rolling
Acceleration = Net Force / Mass
```

## 🎯 Example Scenarios

### Maximum Performance
```
Tuning: Stage 3, Racing Slicks, Top Speed aero
Physics: Arcade preset (max grip)
Result: ~6.5s quarter mile
```

### Endurance Race
```
Physics: Endurance preset
Mode: 10 laps
Result: Fuel/tire strategy required
```

### Wet Weather
```
Physics: Wet Race preset
Result: ~2s slower, careful throttle
```

### Custom Extreme
```
Physics: Tire grip 2.0, Launch 2.0g, Boost 4.0 bar
Result: Insane power!
```

## 📊 API Endpoints

### `GET /api/vehicles`
List all vehicles

### `POST /api/simulate/drag`
Run simulation with custom physics
```json
{
  "vehicle_ids": ["koenigsegg_jesko"],
  "physics_config": {...},
  "preset_config": "arcade",
  "tuning_mods": {...}
}
```

### `GET /api/health`
Health check

Docs: `http://localhost:8000/docs`

## 🧪 Testing Physics

### Verify It Works

**Backend logs:**
```
⚙️ Using ConfigurablePhysicsEngine
   📋 Applying preset: arcade
```

**Browser console:**
```
✅ Custom physics detected:
  - Tire grip: 1.5
  - Turbo: true
```

### Quick Tests
1. **Stock vs Arcade**: ~1s faster
2. **Dry vs Wet**: ~2s slower
3. **Max Grip**: Insane acceleration

## 🛠️ Customization

### Add Vehicles
Edit `hypercar_data.csv`

### Create Presets
Edit `app/physics_config.py`

### Modify Tuning
Edit `app/tuning.py`

## 📁 Project Structure

```
Hypercar_Sim/
├── app/                           # Backend
│   ├── main.py                   # API (UPDATED)
│   ├── physics_customizable.py   # Custom engine (NEW)
│   ├── physics_config.py         # Config classes (NEW)
│   └── ...
├── frontend/                      # Frontend
│   ├── simulator.html            # Main page (UPDATED)
│   ├── sim.js                    # Logic (UPDATED)
│   ├── physics-customization-ui.js   # UI (NEW)
│   ├── physics-customization-ui.css  # Styles (NEW)
│   └── ...
└── [documentation files]
```

## 📚 Documentation

- **README.md** - This file
- **QUICK_START.md** - 5-min setup
- **CUSTOMIZATION_GUIDE.md** - All parameters
- **PHYSICS_CONFIG_FIXED.md** - Technical details
- **CHANGELOG.md** - Version history

## 🤝 Contributing

1. Fork repo
2. Create branch
3. Commit changes
4. Push and PR

## 📝 Version History

### v2.0 - Physics Customization
- ✅ Complete UI control
- ✅ 5 presets + 50+ parameters
- ✅ Visual indicators
- ✅ Enhanced logging

### v1.0 - Initial Release
- Basic physics
- 30+ vehicles
- Tuning system

## 📋 Roadmap

- [ ] Save/load configs
- [ ] Share configs via URL
- [ ] More presets
- [ ] Track selection
- [ ] Championship mode
- [ ] Multiplayer
- [ ] 3D visualization
- [ ] Mobile app

## 🐛 Known Issues

- Some specs are estimated
- Hybrid modeling simplified
- Extreme parameters may be unrealistic

## 📜 License

MIT License

## 📞 Contact

- **GitHub**: [@jude-pinkman](https://github.com/jude-pinkman)
- **Email**: judesahai0@gmail.com
- **Issues**: [GitHub Issues](https://github.com/jude-pinkman/Hypercar_Sim/issues)

---

## 🎯 v2.0 Key Improvements

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Physics Control | ❌ Code | ✅ Full UI |
| Presets | ❌ None | ✅ 5 presets |
| Parameters | ❌ Fixed | ✅ 50+ adjustable |
| Weather | ❌ None | ✅ 5 conditions |
| Fuel System | ❌ None | ✅ Full sim |
| Tire Thermal | ❌ Basic | ✅ Advanced |
| Brake Fade | ❌ None | ✅ Modeled |
| Battery SOC | ❌ Simple | ✅ Management |

---

**Made with ❤️ for automotive enthusiasts**

⭐ **Star if useful!**

🏁 **NOW with ACTUAL physics customization!**