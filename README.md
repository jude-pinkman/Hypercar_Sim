# 🏎️ Hypercar Performance Simulator v3.0

![License](https://img.shields.io/badge/license-MIT-red.svg)
![Python](https://img.shields.io/badge/python-3.8+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![Physics](https://img.shields.io/badge/Physics-Fully_Customizable-00ff9d.svg)
![F1](https://img.shields.io/badge/Formula_1-2020_Season-e10600.svg)

A physics-based vehicle performance simulator featuring hypercars, Formula 1 cars, customizable physics, tuning, telemetry, and real-world circuit simulation.

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/home.html`. API documentation is available at `/docs`.

## Security configuration

The API uses an explicit CORS allowlist. For a separate frontend, set `CORS_ORIGINS` to a comma-separated list of trusted origins:

```bash
CORS_ORIGINS=https://your-frontend.example,https://www.your-frontend.example
```

The database reload endpoint is disabled unless an admin token is configured. To enable it for controlled administration, set `RELOAD_TOKEN` and send it as `X-Admin-Token`:

```bash
RELOAD_TOKEN=use-a-long-random-secret
curl -X POST http://localhost:8000/api/reload \
  -H 'X-Admin-Token: use-a-long-random-secret'
```

Do not commit either value to the repository. The default frontend configuration uses the current origin, avoiding a hardcoded production API URL. For a separately hosted API, define `window.__HYPERCAR_API_BASE_URL__` before loading `config.js`.

## API limits

Simulation requests are bounded to three vehicles, 120 seconds, 0.1-second maximum timestep, 100 km of target distance, and a 150 m/s starting velocity. Invalid or conflicting physics options are rejected before simulation begins.

## Main features

- Drag simulation with multiple race modes
- F1 and hypercar catalogues
- Circuit and lap simulation
- Tuning and configurable physics presets
- Weather, tyre, hybrid, and telemetry systems
- Offline-capable frontend fallback

## Project structure

- `app/`: FastAPI backend, physics engines, race simulation, and ML prediction
- `frontend/`: static HTML, CSS, and JavaScript client
- `hypercar_data.csv`: hypercar gear/specification data
- `requirements.txt`: Python dependencies

## License

MIT License.
