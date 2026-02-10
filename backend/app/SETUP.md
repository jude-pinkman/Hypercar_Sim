# Setup Instructions - Your CSV Format

## 📋 What You Have

Your CSV format:
```
Car,Gear,Ratio,Redline_RPM,Top_Speed_Redline_mph,Shift_Point_mph,Speed_Range
Koenigsegg Jesko Absolut,1,3.85,8500,61,61,0-61 mph
```

## 🚀 Setup Steps

### 1. Place your CSV file

Put your `hypercar_data.csv` in:
```
backend/data/hypercar_data.csv
```

### 2. File structure should be:

```
backend/
├── app/
│   ├── __init__.py          ← Copy this
│   ├── main.py              ← Copy this  
│   ├── models.py            ← Copy this
│   ├── database.py          ← Copy this (reads your CSV!)
│   └── physics.py           ← Copy this
└── data/
    └── hypercar_data.csv    ← YOUR CSV FILE HERE
```

### 3. Run the server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. You should see:

```
============================================================
🚗 Hypercar Simulation API Starting...
============================================================
Loading vehicle database from: /path/to/backend/data/hypercar_data.csv
  ✓ Loaded: Koenigsegg Jesko Absolut (9 gears)
  ✓ Loaded: Bugatti Chiron Super Sport 300+ (7 gears)
  ✓ Loaded: Hennessey Venom F5 (3 gears)
Database loaded: 3 vehicles
============================================================
```

## ✏️ Update Shift Points

### Option 1: Edit CSV and reload

1. Open `data/hypercar_data.csv`
2. Change `Shift_Point_mph` value
3. Save file
4. Call: `http://localhost:8000/api/reload`

### Option 2: Directly in CSV

Your CSV line:
```csv
Koenigsegg Jesko Absolut,1,3.85,8500,61,61,0-61 mph
                                           ↑
                                    Change this!
```

Change to:
```csv
Koenigsegg Jesko Absolut,1,3.85,8500,61,65,0-65 mph
```

Then reload: POST to `/api/reload`

## 🎯 Vehicle IDs

The code automatically creates vehicle IDs from car names:
- `Koenigsegg Jesko Absolut` → `koenigsegg_jesko`
- `Bugatti Chiron Super Sport 300+` → `bugatti_chiron_ss`
- `Hennessey Venom F5` → `hennessey_venom_f5`

## 📊 What Gets Generated

Since your CSV doesn't have all specs, the code includes hardcoded values for:
- Mass
- Power
- Drag coefficient
- Tire radius
- etc.

To customize these, edit the `_get_vehicle_specs()` function in `database.py`

## 🔍 Testing

1. Check loaded vehicles:
```bash
curl http://localhost:8000/api/vehicles
```

2. Run simulation:
```bash
curl -X POST http://localhost:8000/api/simulate/drag \
  -H "Content-Type: application/json" \
  -d '{"vehicle_ids": ["koenigsegg_jesko"]}'
```

## ⚠️ Important Notes

- **CSV must have header row** with exact column names
- **Speeds in CSV are in MPH** (code converts to km/h)
- **Shift points = top speed** in your data (car shifts at redline)
- To shift earlier, edit the `Shift_Point_mph` column

## 🆕 Adding New Cars

Just add rows to your CSV:
```csv
Car,Gear,Ratio,Redline_RPM,Top_Speed_Redline_mph,Shift_Point_mph,Speed_Range
New Car Name,1,4.0,7000,50,50,0-50 mph
New Car Name,2,2.8,7000,75,75,50-75 mph
```

Then add specs in `database.py` → `_get_vehicle_specs()`

Reload: `POST /api/reload`

Done! ✅
