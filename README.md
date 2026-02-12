# 🏎️ Hypercar Performance Simulator v2.0

![License](https://img.shields.io/badge/license-MIT-red.svg)
![Python](https://img.shields.io/badge/python-3.8+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)

A physics-based hypercar drag race simulator featuring 30+ vehicles, advanced tuning system, and real-time telemetry visualization. Experience the raw power of the world's most extreme hypercars through accurate simulation.

![Hypercar Simulator](https://via.placeholder.com/1200x400/0D0D0D/FF3B30?text=Hypercar+Performance+Simulator)

## ✨ Features

### 🏁 8 Race Modes
- **Quarter Mile (402m)** - Classic drag race
- **Half Mile (805m)** - Extended acceleration test
- **1 Mile (1609m)** - Top speed challenge
- **Custom Distance** - Set your own distance
- **Lap Race** - Circuit racing simulation
- **Acceleration Zone** - 0-100, 100-200 km/h tests
- **Roll Race** - Rolling start competitions
- **Top Speed** - Maximum velocity runs

### 🚗 30+ Hypercars
Premium vehicle collection including:
- **Koenigsegg**: Jesko Absolut, Agera RS, Regera, One:1
- **Bugatti**: Chiron Super Sport 300+, Bolide, Veyron Super Sport
- **McLaren**: Speedtail, P1, 720S, Senna
- **Ferrari**: SF90 Stradale, LaFerrari, F8 Tributo
- **Lamborghini**: Aventador SVJ, Huracán Performante, Revuelto
- **Porsche**: 918 Spyder, 911 Turbo S, Taycan Turbo S
- **Electric Hypercars**: Rimac Nevera, Lotus Evija, Aspark Owl, Pininfarina Battista
- And many more!

### 🔧 Advanced Tuning System
- **Engine Tuning**: Stock, Stage 1, Stage 2, Stage 3
- **Tire Compounds**: Street, Sport, Slick
- **Aerodynamics**: Stock, Sport, Race packages
- **Weight Reduction**: Stock, Lightweight, Race
- **Transmission**: Stock, Sport, Race efficiency
- **Boost Pressure**: Adjustable turbo/supercharger boost (0.5x - 2.0x)
- **Nitrous Oxide**: NOS injection system

### 📊 Real Physics Simulation
- Accurate aerodynamic drag calculation
- Rolling resistance modeling
- Engine torque curve interpolation
- Gear ratio optimization
- Hybrid system modeling (electric motor contribution)
- Environmental factors (temperature, altitude)
- Traction limits and launch control

### 📈 Live Telemetry
- Real-time speedometers for each vehicle
- Distance tracking
- RPM monitoring
- Gear indicator
- Power output visualization
- Performance metrics (0-100 km/h, 0-200 km/h, quarter-mile time/speed)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js (optional, for development)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/hypercar-simulator.git
cd hypercar-simulator
```

2. **Install Python dependencies**
```bash
pip install fastapi uvicorn pandas pydantic
```

3. **Start the backend server**
```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

4. **Open the frontend**
```bash
# Simply open frontend/home.html in your browser
# Or use a local server:
cd frontend
python -m http.server 8080
```

Visit `http://localhost:8080/home.html`

## 📁 Project Structure

```
hypercar-simulator/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic data models
│   │   ├── physics.py           # Physics simulation engine
│   │   ├── database.py          # CSV database management
│   │   ├── tuning.py            # Tuning system
│   │   └── vehicles.py          # Vehicle specifications
│   │
│   └── data/
│       └── hypercar_data.csv    # Vehicle database
│
├── frontend/
│   ├── home.html                # Landing page
│   ├── index.html               # Main simulator
│   ├── about.html               # About page
│   ├── style.css                # Main styles
│   ├── home-style.css           # Landing page styles
│   ├── tuning-style.css         # Tuning panel styles
│   ├── vehicle-selector.css     # Vehicle selection styles
│   ├── sim.js                   # Main simulation logic
│   ├── render.js                # Canvas rendering
│   ├── tuning.js                # Tuning system UI
│   ├── tuning-integration.js    # Tuning integration
│   ├── vehicle-selector.js      # Vehicle selection UI
│   └── home-script.js           # Landing page interactions
│
└── README.md
```

## 🎮 Usage

### Selecting Vehicles
1. Choose the number of vehicles to race (1-3)
2. Use the searchable dropdown to find vehicles by name or brand
3. Vehicles are grouped by manufacturer for easy browsing
4. Click the 🔧 icon to open the tuning panel for each vehicle

### Tuning Your Vehicle
1. Click the tuning button on any selected vehicle
2. Navigate through tuning categories:
   - **Engine**: Increase power and torque
   - **Tires**: Improve grip and reduce rolling resistance
   - **Aero**: Adjust drag coefficient
   - **Weight**: Reduce vehicle mass
   - **Transmission**: Improve efficiency
   - **Advanced**: Boost pressure and NOS
3. Apply or reset changes

### Running a Race
1. Select your race mode from the top navigation
2. Configure environment settings (temperature, altitude)
3. Adjust mode-specific parameters (distance, laps, etc.)
4. Click "Start Race" or press `Space`
5. Watch the real-time visualization and telemetry
6. Review performance metrics after completion

### Keyboard Shortcuts
- `1-8`: Switch between race modes
- `Space`: Start simulation
- `R`: Reset simulation
- `S`: Go to simulator (from home page)
- `A`: Go to about page (from home page)

## 🔬 Physics Engine

The simulator uses real-world physics equations:

### Force Calculations
```
Drag Force = 0.5 × ρ × Cd × A × v²
Rolling Resistance = Crr × m × g
Drive Force = (Engine Torque × Gear Ratio × Final Drive × η) / Tire Radius
Net Force = Drive Force - Drag Force - Rolling Resistance
Acceleration = Net Force / Mass
```

### Air Density
```
Air Density (ρ) = P / (R × T)
Pressure adjusted for altitude: P × e^(-h/8400)
```

### Gear Shifting
- Intelligent shift points based on RPM and velocity
- Prevents engine bogging
- Optimized for maximum acceleration

## 🛠️ Customization

### Adding New Vehicles
Edit `backend/data/hypercar_data.csv` with vehicle specifications:
- Basic specs (mass, power, torque, drag coefficient)
- Gear ratios and shift points
- Torque curve data
- Hybrid/electric parameters (optional)

### Modifying Tuning Options
Edit `backend/app/tuning.py` to adjust:
- Tuning multipliers
- Available tuning stages
- Custom modifications

### Changing Environment
Adjust default conditions in the UI:
- Temperature (-20°C to 50°C)
- Altitude (0m to 3000m)

## 📊 API Documentation

### Endpoints

#### `GET /api/vehicles`
Returns list of available vehicles
```json
{
  "koenigsegg_jesko": "Koenigsegg Jesko Absolut",
  "bugatti_chiron_ss": "Bugatti Chiron Super Sport 300+"
}
```

#### `POST /api/simulate/drag`
Run drag race simulation
```json
{
  "vehicle_ids": ["koenigsegg_jesko", "bugatti_chiron_ss"],
  "environment": {
    "temperature_celsius": 20,
    "altitude_meters": 0
  },
  "timestep": 0.01,
  "max_time": 30.0,
  "target_distance": 402.336,
  "tuning_mods": {
    "koenigsegg_jesko": {
      "engine": "stage2",
      "tires": "slick"
    }
  }
}
```

#### `POST /api/reload`
Reload vehicle database from CSV

#### `GET /api/health`
Health check endpoint

Full API documentation available at `http://localhost:8000/docs`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex physics calculations
- Test with multiple vehicles before submitting

## 📝 To-Do List

- [ ] Add more vehicle brands (Audi, BMW, Mercedes)
- [ ] Implement weather conditions (rain, wind)
- [ ] Add track surface types
- [ ] Export race data to CSV
- [ ] Multiplayer race comparison
- [ ] 3D visualization option
- [ ] Mobile app version
- [ ] Real-world track layouts
- [ ] Tire wear simulation
- [ ] Fuel consumption modeling

## 🐛 Known Issues

- Some vehicles may have estimated specifications
- Hybrid system modeling is simplified
- Traction limits are approximations
- Database requires manual CSV updates

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Vehicle specifications sourced from manufacturer data
- Physics equations based on automotive engineering principles
- Inspired by real-world drag racing and automotive simulation
- Community feedback and testing

## 📞 Contact

- **GitHub**: [@jude-pinkman](https://github.com/jude-pinkman)
- **Email**: judesahai0@gmail.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/Hypercar_Sim/issues)

---

**Made with ❤️ for automotive enthusiasts and racing fans**

⭐ Star this repo if you find it useful!