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
            # KOENIGSEGG
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
            "Koenigsegg Jesko Attack": {
                "vehicle_id": "koenigsegg_jesko_attack",
                "mass": 1420,
                "power_kw": 1195,
                "torque_nm": 1500,
                "drag_coefficient": 0.315,
                "frontal_area": 1.88,
                "final_drive": 2.85,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1200,
                "tire_radius": 0.370,
                "rolling_resistance_coef": 0.009,
            },
            "Koenigsegg Regera": {
                "vehicle_id": "koenigsegg_regera",
                "mass": 1590,
                "power_kw": 1100,
                "torque_nm": 2000,
                "drag_coefficient": 0.278,
                "frontal_area": 1.88,
                "final_drive": 2.73,
                "transmission_efficiency": 0.95,
                "idle_rpm": 1200,
                "tire_radius": 0.370,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 515,
                "electric_torque_nm": 900,
                "electric_max_speed_kmh": 160,
            },
            "Koenigsegg Agera RS": {
                "vehicle_id": "koenigsegg_agera_rs",
                "mass": 1395,
                "power_kw": 1014,
                "torque_nm": 1371,
                "drag_coefficient": 0.33,
                "frontal_area": 1.87,
                "final_drive": 2.85,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.368,
                "rolling_resistance_coef": 0.009,
            },
            
            # BUGATTI
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
            "Bugatti Bolide": {
                "vehicle_id": "bugatti_bolide",
                "mass": 1240,
                "power_kw": 1361,
                "torque_nm": 1600,
                "drag_coefficient": 0.67,
                "frontal_area": 1.95,
                "final_drive": 2.73,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1200,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.008,
            },
            "Bugatti Veyron Super Sport": {
                "vehicle_id": "bugatti_veyron_ss",
                "mass": 1888,
                "power_kw": 882,
                "torque_nm": 1500,
                "drag_coefficient": 0.36,
                "frontal_area": 2.07,
                "final_drive": 2.73,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.010,
            },
            
            # HENNESSEY & SSC
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
            },
            "SSC Tuatara": {
                "vehicle_id": "ssc_tuatara",
                "mass": 1247,
                "power_kw": 1305,
                "torque_nm": 1735,
                "drag_coefficient": 0.279,
                "frontal_area": 1.92,
                "final_drive": 3.00,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
            },
            
            # PAGANI
            "Pagani Huayra R": {
                "vehicle_id": "pagani_huayra_r",
                "mass": 1050,
                "power_kw": 620,
                "torque_nm": 750,
                "drag_coefficient": 0.30,
                "frontal_area": 1.82,
                "final_drive": 3.27,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1200,
                "tire_radius": 0.355,
                "rolling_resistance_coef": 0.008,
            },
            "Pagani Zonda R": {
                "vehicle_id": "pagani_zonda_r",
                "mass": 1070,
                "power_kw": 559,
                "torque_nm": 710,
                "drag_coefficient": 0.36,
                "frontal_area": 1.80,
                "final_drive": 3.42,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.355,
                "rolling_resistance_coef": 0.008,
            },
            
            # MCLAREN
            "McLaren Speedtail": {
                "vehicle_id": "mclaren_speedtail",
                "mass": 1430,
                "power_kw": 782,
                "torque_nm": 1150,
                "drag_coefficient": 0.278,
                "frontal_area": 1.85,
                "final_drive": 3.15,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 230,
                "electric_torque_nm": 400,
                "electric_max_speed_kmh": 140,
            },
            "McLaren P1": {
                "vehicle_id": "mclaren_p1",
                "mass": 1450,
                "power_kw": 673,
                "torque_nm": 900,
                "drag_coefficient": 0.34,
                "frontal_area": 1.98,
                "final_drive": 3.23,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 130,
                "electric_torque_nm": 260,
                "electric_max_speed_kmh": 130,
            },
            "McLaren Senna": {
                "vehicle_id": "mclaren_senna",
                "mass": 1198,
                "power_kw": 588,
                "torque_nm": 800,
                "drag_coefficient": 0.82,
                "frontal_area": 1.95,
                "final_drive": 3.41,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.008,
            },
            "McLaren 765LT": {
                "vehicle_id": "mclaren_765lt",
                "mass": 1229,
                "power_kw": 563,
                "torque_nm": 800,
                "drag_coefficient": 0.35,
                "frontal_area": 1.95,
                "final_drive": 3.41,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            "McLaren 720S": {
                "vehicle_id": "mclaren_720s",
                "mass": 1283,
                "power_kw": 530,
                "torque_nm": 770,
                "drag_coefficient": 0.32,
                "frontal_area": 1.95,
                "final_drive": 3.41,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            
            # ASTON MARTIN
            "Aston Martin Valkyrie": {
                "vehicle_id": "aston_valkyrie",
                "mass": 1030,
                "power_kw": 865,
                "torque_nm": 900,
                "drag_coefficient": 0.65,
                "frontal_area": 1.75,
                "final_drive": 3.56,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1500,
                "tire_radius": 0.350,
                "rolling_resistance_coef": 0.007,
                "electric_power_kw": 120,
                "electric_torque_nm": 280,
                "electric_max_speed_kmh": 120,
            },
            
            # ELECTRIC HYPERCARS
            "Rimac Nevera": {
                "vehicle_id": "rimac_nevera",
                "mass": 2150,
                "power_kw": 1408,
                "torque_nm": 2360,
                "drag_coefficient": 0.30,
                "frontal_area": 2.10,
                "final_drive": 9.73,
                "transmission_efficiency": 0.96,
                "idle_rpm": 0,
                "tire_radius": 0.368,
                "rolling_resistance_coef": 0.009,
            },
            "Lotus Evija": {
                "vehicle_id": "lotus_evija",
                "mass": 1680,
                "power_kw": 1470,
                "torque_nm": 1700,
                "drag_coefficient": 0.38,
                "frontal_area": 1.90,
                "final_drive": 10.5,
                "transmission_efficiency": 0.96,
                "idle_rpm": 0,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.008,
            },
            "Aspark Owl": {
                "vehicle_id": "aspark_owl",
                "mass": 1900,
                "power_kw": 1480,
                "torque_nm": 2000,
                "drag_coefficient": 0.32,
                "frontal_area": 1.95,
                "final_drive": 11.0,
                "transmission_efficiency": 0.96,
                "idle_rpm": 0,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
            },
            "Pininfarina Battista": {
                "vehicle_id": "pininfarina_battista",
                "mass": 2100,
                "power_kw": 1400,
                "torque_nm": 2300,
                "drag_coefficient": 0.29,
                "frontal_area": 2.08,
                "final_drive": 9.73,
                "transmission_efficiency": 0.96,
                "idle_rpm": 0,
                "tire_radius": 0.368,
                "rolling_resistance_coef": 0.009,
            },
            
            # FERRARI
            "Ferrari SF90 Stradale": {
                "vehicle_id": "ferrari_sf90",
                "mass": 1570,
                "power_kw": 735,
                "torque_nm": 900,
                "drag_coefficient": 0.34,
                "frontal_area": 2.00,
                "final_drive": 3.25,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 162,
                "electric_torque_nm": 315,
                "electric_max_speed_kmh": 135,
            },
            "Ferrari LaFerrari": {
                "vehicle_id": "ferrari_laferrari",
                "mass": 1255,
                "power_kw": 588,
                "torque_nm": 900,
                "drag_coefficient": 0.33,
                "frontal_area": 2.00,
                "final_drive": 3.27,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.008,
                "electric_power_kw": 120,
                "electric_torque_nm": 270,
                "electric_max_speed_kmh": 130,
            },
            "Ferrari F8 Tributo": {
                "vehicle_id": "ferrari_f8",
                "mass": 1330,
                "power_kw": 530,
                "torque_nm": 770,
                "drag_coefficient": 0.32,
                "frontal_area": 2.00,
                "final_drive": 3.27,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            "Ferrari 812 Superfast": {
                "vehicle_id": "ferrari_812",
                "mass": 1525,
                "power_kw": 588,
                "torque_nm": 718,
                "drag_coefficient": 0.33,
                "frontal_area": 2.02,
                "final_drive": 3.08,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
            },
            
            # LAMBORGHINI
            "Lamborghini Revuelto": {
                "vehicle_id": "lamborghini_revuelto",
                "mass": 1772,
                "power_kw": 825,
                "torque_nm": 1000,
                "drag_coefficient": 0.32,
                "frontal_area": 2.05,
                "final_drive": 3.12,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 140,
                "electric_torque_nm": 350,
                "electric_max_speed_kmh": 140,
            },
            "Lamborghini Aventador SVJ": {
                "vehicle_id": "lamborghini_aventador_svj",
                "mass": 1525,
                "power_kw": 566,
                "torque_nm": 720,
                "drag_coefficient": 0.35,
                "frontal_area": 2.08,
                "final_drive": 3.42,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
            },
            "Lamborghini Sian FKP 37": {
                "vehicle_id": "lamborghini_sian",
                "mass": 1595,
                "power_kw": 602,
                "torque_nm": 720,
                "drag_coefficient": 0.35,
                "frontal_area": 2.08,
                "final_drive": 3.42,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 25,
                "electric_torque_nm": 38,
                "electric_max_speed_kmh": 130,
            },
            "Lamborghini Huracan STO": {
                "vehicle_id": "lamborghini_huracan_sto",
                "mass": 1339,
                "power_kw": 470,
                "torque_nm": 565,
                "drag_coefficient": 0.37,
                "frontal_area": 1.98,
                "final_drive": 3.76,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.350,
                "rolling_resistance_coef": 0.008,
            },
            
            # PORSCHE
            "Porsche 918 Spyder": {
                "vehicle_id": "porsche_918",
                "mass": 1640,
                "power_kw": 652,
                "torque_nm": 1280,
                "drag_coefficient": 0.32,
                "frontal_area": 1.98,
                "final_drive": 3.44,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 210,
                "electric_torque_nm": 500,
                "electric_max_speed_kmh": 150,
            },
            "Porsche 911 GT2 RS": {
                "vehicle_id": "porsche_911_gt2_rs",
                "mass": 1470,
                "power_kw": 515,
                "torque_nm": 750,
                "drag_coefficient": 0.38,
                "frontal_area": 1.92,
                "final_drive": 3.88,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            "Porsche 911 Turbo S": {
                "vehicle_id": "porsche_911_turbo_s",
                "mass": 1640,
                "power_kw": 478,
                "torque_nm": 800,
                "drag_coefficient": 0.33,
                "frontal_area": 1.92,
                "final_drive": 3.44,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.009,
            },
            
            # MERCEDES & GORDON MURRAY
            "Mercedes-AMG ONE": {
                "vehicle_id": "mercedes_amg_one",
                "mass": 1695,
                "power_kw": 782,
                "torque_nm": 1020,
                "drag_coefficient": 0.32,
                "frontal_area": 1.95,
                "final_drive": 3.12,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1500,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.008,
                "electric_power_kw": 120,
                "electric_torque_nm": 320,
                "electric_max_speed_kmh": 140,
            },
            "Gordon Murray T.50": {
                "vehicle_id": "gordon_murray_t50",
                "mass": 986,
                "power_kw": 485,
                "torque_nm": 467,
                "drag_coefficient": 0.32,
                "frontal_area": 1.85,
                "final_drive": 3.72,
                "transmission_efficiency": 0.94,
                "idle_rpm": 1500,
                "tire_radius": 0.345,
                "rolling_resistance_coef": 0.008,
            },
            
            # CZINGER
            "Czinger 21C": {
                "vehicle_id": "czinger_21c",
                "mass": 1250,
                "power_kw": 930,
                "torque_nm": 1250,
                "drag_coefficient": 0.32,
                "frontal_area": 1.82,
                "final_drive": 3.25,
                "transmission_efficiency": 0.93,
                "idle_rpm": 1200,
                "tire_radius": 0.355,
                "rolling_resistance_coef": 0.008,
                "electric_power_kw": 200,
                "electric_torque_nm": 500,
                "electric_max_speed_kmh": 150,
            },
            
            # AMERICAN MUSCLE & SUPERCARS
            "Ford GT": {
                "vehicle_id": "ford_gt",
                "mass": 1385,
                "power_kw": 485,
                "torque_nm": 746,
                "drag_coefficient": 0.34,
                "frontal_area": 1.95,
                "final_drive": 3.43,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            "Chevrolet Corvette Z06": {
                "vehicle_id": "corvette_z06",
                "mass": 1560,
                "power_kw": 500,
                "torque_nm": 623,
                "drag_coefficient": 0.34,
                "frontal_area": 2.00,
                "final_drive": 3.15,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1000,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.009,
            },
            "Dodge Viper ACR": {
                "vehicle_id": "dodge_viper_acr",
                "mass": 1521,
                "power_kw": 477,
                "torque_nm": 814,
                "drag_coefficient": 0.42,
                "frontal_area": 2.10,
                "final_drive": 3.55,
                "transmission_efficiency": 0.90,
                "idle_rpm": 800,
                "tire_radius": 0.365,
                "rolling_resistance_coef": 0.009,
            },
            
            # JAPANESE SUPERCARS
            "Acura NSX Type S": {
                "vehicle_id": "acura_nsx_type_s",
                "mass": 1725,
                "power_kw": 447,
                "torque_nm": 667,
                "drag_coefficient": 0.33,
                "frontal_area": 1.98,
                "final_drive": 3.58,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.355,
                "rolling_resistance_coef": 0.009,
                "electric_power_kw": 35,
                "electric_torque_nm": 148,
                "electric_max_speed_kmh": 120,
            },
            "Nissan GT-R Nismo": {
                "vehicle_id": "nissan_gtr_nismo",
                "mass": 1720,
                "power_kw": 441,
                "torque_nm": 652,
                "drag_coefficient": 0.35,
                "frontal_area": 2.05,
                "final_drive": 3.70,
                "transmission_efficiency": 0.90,
                "idle_rpm": 1000,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.009,
            },
            "Lexus LFA": {
                "vehicle_id": "lexus_lfa",
                "mass": 1480,
                "power_kw": 412,
                "torque_nm": 480,
                "drag_coefficient": 0.31,
                "frontal_area": 1.95,
                "final_drive": 3.73,
                "transmission_efficiency": 0.92,
                "idle_rpm": 1200,
                "tire_radius": 0.358,
                "rolling_resistance_coef": 0.008,
            },
            
            # AUDI
            "Audi R8 V10 Performance": {
                "vehicle_id": "audi_r8_v10",
                "mass": 1595,
                "power_kw": 456,
                "torque_nm": 580,
                "drag_coefficient": 0.34,
                "frontal_area": 2.02,
                "final_drive": 3.46,
                "transmission_efficiency": 0.91,
                "idle_rpm": 1200,
                "tire_radius": 0.360,
                "rolling_resistance_coef": 0.009,
            },
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
                torque_curve=self._generate_torque_curve(redline_rpm, specs["torque_nm"]),
                electric_power_kw=specs.get("electric_power_kw"),
                electric_torque_nm=specs.get("electric_torque_nm"),
                electric_max_speed_kmh=specs.get("electric_max_speed_kmh"),
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