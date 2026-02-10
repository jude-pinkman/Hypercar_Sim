"""
CSV Database Loader for Vehicle Data
Reads from hypercar_data.csv with format:
Car,Gear,Ratio,Redline_RPM,Top_Speed_Redline_mph,Shift_Point_mph,Speed_Range
"""

import csv
from pathlib import Path
from typing import Dict, List
from app.models import Vehicle, GearInfo, TorquePoint


# =========================
# SAFE PARSING HELPERS
# =========================
def safe_float(value, default=0.0) -> float:
    if value is None:
        return default
    value = str(value).strip()
    if value.lower() in ("n/a", "na", "", "null", "none"):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except Exception:
        return default


class VehicleDatabase:
    """Loads and manages vehicle data from CSV file"""

    def __init__(self, csv_path: str = None):
        if csv_path is None:
            base_path = Path(__file__).parent.parent
            csv_path = base_path / "data" / "hypercar_data.csv"

        self.csv_path = Path(csv_path)
        self.vehicles: Dict[str, Vehicle] = {}

        self.vehicle_specs = self._get_vehicle_specs()
        self.load_database()

    # =========================
    # HARD-CODED VEHICLE SPECS
    # =========================
    def _get_vehicle_specs(self) -> Dict[str, dict]:
        return {
            "Koenigsegg Jesko Absolut": {
                "vehicle_id": "koenigsegg_jesko",
                "mass": 1420,
                "power_kw": 1195,
                "torque_nm": 1500,
                "drag_coefficient": 0.278,
                "frontal_area": 1.88,
                "final_drive": 2.85,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1200,
                "tire_radius": 0.370,
                "rolling_resistance_coef": 0.009,
            },
            "Bugatti Chiron Super Sport 300+": {
                "vehicle_id": "bugatti_chiron_ss",
                "mass": 1978,
                "power_kw": 1177,
                "torque_nm": 1600,
                "drag_coefficient": 0.35,
                "frontal_area": 2.07,
                "final_drive": 2.73,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.010,
            },
            "Hennessey Venom F5": {
                "vehicle_id": "hennessey_venom_f5",
                "mass": 1360,
                "power_kw": 1355,
                "torque_nm": 1617,
                "drag_coefficient": 0.33,
                "frontal_area": 1.95,
                "final_drive": 3.08,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.368,
                "rolling_resistance_coef": 0.009,
            }
        }

    # =========================
    # TORQUE CURVE
    # =========================
    def _generate_torque_curve(self, redline_rpm: float, peak_torque: float) -> List[TorquePoint]:
        points = [
            (0.14, 0.60),
            (0.25, 0.75),
            (0.35, 0.88),
            (0.45, 0.97),
            (0.55, 1.00),
            (0.65, 0.98),
            (0.75, 0.94),
            (0.85, 0.88),
            (0.95, 0.80),
            (1.00, 0.75),
        ]

        curve = []
        for rpm_ratio, torque_ratio in points:
            curve.append(
                TorquePoint(
                    rpm=redline_rpm * rpm_ratio,
                    torque=peak_torque * torque_ratio
                )
            )
        return curve

    # =========================
    # LOAD DATABASE
    # =========================
    def load_database(self):
        print(f"Loading vehicle database from: {self.csv_path}")

        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found at {self.csv_path}")

        gears_by_car = self._parse_csv()

        for car_name, gears_data in gears_by_car.items():
            if car_name not in self.vehicle_specs:
                print(f"  ✗ Skipping {car_name}: specs not defined")
                continue

            specs = self.vehicle_specs[car_name]
            redline_rpm = gears_data[0]["redline_rpm"]

            gears = [
                GearInfo(
                    gear_number=g["gear"],
                    ratio=g["ratio"],
                    top_speed_kmh=g["top_speed_kmh"],
                    shift_speed_kmh=g["shift_speed_kmh"]
                )
                for g in gears_data
            ]

            vehicle = Vehicle(
                vehicle_id=specs["vehicle_id"],
                name=car_name,
                mass=specs["mass"],
                power_kw=specs["power_kw"],
                torque_nm=specs["torque_nm"],
                drag_coefficient=specs["drag_coefficient"],
                frontal_area=specs["frontal_area"],
                final_drive=specs["final_drive"],
                transmission_efficiency=specs["transmission_efficiency"],
                idle_rpm=specs["idle_rpm"],
                redline_rpm=redline_rpm,
                tire_radius=specs["tire_radius"],
                rolling_resistance_coef=specs["rolling_resistance_coef"],
                gears=gears,
                torque_curve=self._generate_torque_curve(redline_rpm, specs["torque_nm"])
            )

            self.vehicles[vehicle.vehicle_id] = vehicle
            print(f"  ✓ Loaded: {car_name} ({len(gears)} gears)")

        print(f"Database loaded: {len(self.vehicles)} vehicles\n")

    # =========================
    # CSV PARSER (FIXED)
    # =========================
    def _parse_csv(self) -> Dict[str, List[dict]]:
        gears_by_car: Dict[str, List[dict]] = {}

        with open(self.csv_path, newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                car_name = row.get("Car", "").strip()
                if not car_name:
                    continue

                gear_data = {
                    "gear": safe_int(row.get("Gear")),
                    "ratio": safe_float(row.get("Ratio")),
                    "redline_rpm": safe_float(row.get("Redline_RPM"), 8000),
                    "top_speed_kmh": safe_float(row.get("Top_Speed_Redline_mph")) * 1.60934,
                    "shift_speed_kmh": safe_float(row.get("Shift_Point_mph")) * 1.60934,
                }

                gears_by_car.setdefault(car_name, []).append(gear_data)

        for car in gears_by_car:
            gears_by_car[car].sort(key=lambda g: g["gear"])

        return gears_by_car

    # =========================
    # PUBLIC API
    # =========================
    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        if vehicle_id not in self.vehicles:
            raise ValueError(f"Vehicle '{vehicle_id}' not found")
        return self.vehicles[vehicle_id]

    def list_vehicles(self) -> Dict[str, str]:
        return {vid: v.name for vid, v in self.vehicles.items()}


# =========================
# SINGLETON ACCESS
# =========================
_db_instance = None


def get_database(csv_path: str = None) -> VehicleDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = VehicleDatabase(csv_path)
    return _db_instance


def reload_database():
    global _db_instance
    if _db_instance:
        _db_instance.vehicles.clear()
        _db_instance.load_database()
