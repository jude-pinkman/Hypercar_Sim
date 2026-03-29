"""
F1 2026 Season Data Module
Realistic driver, team, and circuit definitions for the 2026 F1 season.
Includes real driver lineups, performance profiles, and championship standings.

Status: March 19, 2026 (After Australian GP - Race 1)

2026 Grid (11 Teams, 22 Drivers):
  McLaren            - Lando Norris (#4), Oscar Piastri (#81)
  Red Bull Racing    - Max Verstappen (#1), Isack Hadjar (#6)
  Mercedes           - George Russell (#63), Andrea Kimi Antonelli (#12)
  Ferrari            - Lewis Hamilton (#44), Charles Leclerc (#16)
  Aston Martin       - Fernando Alonso (#14), Lance Stroll (#18)
  Alpine             - Pierre Gasly (#10), Franco Colapinto (#43)
  Williams           - Alexander Albon (#23), Carlos Sainz Jr. (#55)
  Haas F1 Team       - Esteban Ocon (#31), Oliver Bearman (#87)
  Audi               - Nico Hülkenberg (#27), Gabriel Bortoleto (#5)
  Racing Bulls       - Liam Lawson (#30), Arvid Lindblad (#7)
  Cadillac F1 Team   - Valtteri Bottas (#77), Sergio Pérez (#11)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class CircuitType(Enum):
    """Circuit characteristics for performance tuning"""
    STREET   = "street"    # Tight corners, low speeds (Monaco, Baku)
    BALANCED = "balanced"  # Mixed fast & slow sections (Silverstone)
    POWER    = "power"     # High-speed, long straights (Monza, Spa)


@dataclass
class Driver:
    """F1 Driver profile"""
    driver_id: str
    name: str
    number: int
    team: str
    nationality: str

    # Performance profile (0.0 - 1.0)
    speed: float        # Raw pace capability
    consistency: float  # Lap-to-lap stability
    wet_weather: float  # Rain performance
    racecraft: float    # Overtaking, defensive driving, strategy execution

    # Season data (updated after each race)
    points: int = 0
    races_completed: int = 0
    wins: int = 0
    poles: int = 0
    dnf_count: int = 0

    def get_skill_rating(self) -> float:
        """Composite skill score"""
        return (self.speed + self.consistency + self.wet_weather + self.racecraft) / 4


@dataclass
class Team:
    """F1 Team / constructor profile"""
    team_id: str
    name: str
    country: str

    # Car characteristics
    power: float          # Engine performance (0.0 - 1.0)
    handling: float       # Chassis balance & grip
    reliability: float    # DNF resistance
    pit_efficiency: float # Pit crew quality

    # Season data
    points: int = 0
    races_completed: int = 0


@dataclass
class Circuit:
    """F1 Circuit definition"""
    circuit_id: str
    name: str
    country: str
    lap_length_km: float
    corners: int
    drs_zones: int
    circuit_type: CircuitType
    lap_record: str
    lap_record_seconds: float
    typical_race_laps: int
    average_race_time_mins: float


# ============================================================================
# 2026 DRIVER LINEUP — 22 Drivers / 11 Teams (CORRECTED FOR 2026 SEASON)
# ============================================================================

F1_DRIVERS_2026: List[Driver] = [

    # McLaren
    Driver("NOR", "Lando Norris",         4,  "McLaren",          "GBR",
           speed=0.95, consistency=0.94, wet_weather=0.89, racecraft=0.93),
    Driver("PIA", "Oscar Piastri",        81, "McLaren",          "AUS",
           speed=0.93, consistency=0.93, wet_weather=0.87, racecraft=0.90),

    # Red Bull Racing
    Driver("VER", "Max Verstappen",       1,  "Red Bull Racing",  "NED",
           speed=0.99, consistency=0.96, wet_weather=0.95, racecraft=0.97),
    Driver("HAD", "Isack Hadjar",         6,  "Red Bull Racing",  "FRA",
           speed=0.83, consistency=0.82, wet_weather=0.80, racecraft=0.81),

    # Mercedes
    Driver("RUS", "George Russell",       63, "Mercedes",         "GBR",
           speed=0.94, consistency=0.95, wet_weather=0.88, racecraft=0.91),
    Driver("ANT", "Andrea Kimi Antonelli",12, "Mercedes",         "ITA",
           speed=0.84, consistency=0.80, wet_weather=0.82, racecraft=0.82),

    # Ferrari
    Driver("HAM", "Lewis Hamilton",       44, "Ferrari",          "GBR",
           speed=0.95, consistency=0.97, wet_weather=0.96, racecraft=0.97),
    Driver("LEC", "Charles Leclerc",      16, "Ferrari",          "MCO",
           speed=0.96, consistency=0.91, wet_weather=0.89, racecraft=0.92),

    # Aston Martin
    Driver("ALO", "Fernando Alonso",      14, "Aston Martin",     "ESP",
           speed=0.92, consistency=0.97, wet_weather=0.91, racecraft=0.96),
    Driver("STR", "Lance Stroll",         18, "Aston Martin",     "CAN",
           speed=0.83, consistency=0.84, wet_weather=0.79, racecraft=0.81),

    # Alpine
    Driver("GAS", "Pierre Gasly",         10, "Alpine",           "FRA",
           speed=0.88, consistency=0.90, wet_weather=0.87, racecraft=0.88),
    Driver("COL", "Franco Colapinto",     43, "Alpine",           "ARG",
           speed=0.85, consistency=0.83, wet_weather=0.84, racecraft=0.84),

    # Williams
    Driver("ALB", "Alexander Albon",      23, "Williams",         "THA",
           speed=0.88, consistency=0.91, wet_weather=0.86, racecraft=0.87),
    Driver("SAI", "Carlos Sainz Jr.",     55, "Williams",         "ESP",
           speed=0.93, consistency=0.93, wet_weather=0.86, racecraft=0.93),

    # Haas F1 Team
    Driver("OCO", "Esteban Ocon",         31, "Haas F1 Team",     "FRA",
           speed=0.87, consistency=0.90, wet_weather=0.86, racecraft=0.86),
    Driver("BEA", "Oliver Bearman",       87, "Haas F1 Team",     "GBR",
           speed=0.84, consistency=0.82, wet_weather=0.81, racecraft=0.83),

    # Audi (rebranded from Kick Sauber for 2026)
    Driver("HUL", "Nico Hülkenberg",      27, "Audi",             "GER",
           speed=0.87, consistency=0.88, wet_weather=0.85, racecraft=0.86),
    Driver("BOR", "Gabriel Bortoleto",    5,  "Audi",             "BRA",
           speed=0.83, consistency=0.80, wet_weather=0.79, racecraft=0.81),

    # Racing Bulls (VCARB / RB)
    Driver("LAW", "Liam Lawson",          30, "Racing Bulls",     "NZL",
           speed=0.85, consistency=0.85, wet_weather=0.83, racecraft=0.84),
    Driver("LIN", "Arvid Lindblad",       7,  "Racing Bulls",     "SWE",
           speed=0.80, consistency=0.78, wet_weather=0.77, racecraft=0.79),

    # Cadillac F1 Team (new entry for 2026)
    Driver("BOT", "Valtteri Bottas",      77, "Cadillac F1 Team", "FIN",
           speed=0.87, consistency=0.90, wet_weather=0.88, racecraft=0.83),
    Driver("PER", "Sergio Pérez",         11, "Cadillac F1 Team", "MEX",
           speed=0.86, consistency=0.87, wet_weather=0.84, racecraft=0.85),
]


# ============================================================================
# 2026 TEAM ROSTER — 11 Teams (CORRECTED)
# ============================================================================

F1_TEAMS_2026: List[Team] = [
    Team("McLaren",    "McLaren",          "GBR", power=0.95, handling=0.96, reliability=0.93, pit_efficiency=0.94),
    Team("RedBull",    "Red Bull Racing",  "AUT", power=0.97, handling=0.95, reliability=0.94, pit_efficiency=0.95),
    Team("Mercedes",   "Mercedes",         "GER", power=0.96, handling=0.95, reliability=0.95, pit_efficiency=0.96),
    Team("Ferrari",    "Ferrari",          "ITA", power=0.94, handling=0.93, reliability=0.91, pit_efficiency=0.93),
    Team("AstonMartin","Aston Martin",     "GBR", power=0.88, handling=0.87, reliability=0.86, pit_efficiency=0.88),
    Team("Alpine",     "Alpine",           "FRA", power=0.82, handling=0.84, reliability=0.83, pit_efficiency=0.84),
    Team("Williams",   "Williams",         "GBR", power=0.80, handling=0.82, reliability=0.81, pit_efficiency=0.82),
    Team("Haas",       "Haas F1 Team",     "USA", power=0.78, handling=0.79, reliability=0.78, pit_efficiency=0.80),
    Team("Audi",       "Audi",             "GER", power=0.76, handling=0.77, reliability=0.75, pit_efficiency=0.78),
    Team("RacingBulls","Racing Bulls",     "ITA", power=0.77, handling=0.78, reliability=0.76, pit_efficiency=0.79),
    Team("Cadillac",   "Cadillac F1 Team", "USA", power=0.74, handling=0.74, reliability=0.73, pit_efficiency=0.75),
]


# ============================================================================
# 2026 F1 CIRCUITS — 21 Races
# ============================================================================

F1_CIRCUITS_2026: List[Circuit] = [
    Circuit("AUS","Albert Park Circuit",                "AUS",5.278,16,2,CircuitType.BALANCED, "1:17.657 (Leclerc, 2024)",    77.657, 58, 96.0),
    Circuit("CHN","Shanghai International Circuit",     "CHN",5.451,16,2,CircuitType.BALANCED, "1:31.897 (Bottas, 2018)",     91.897, 56,105.0),
    Circuit("JPN","Suzuka International Racing Course", "JPN",5.807,16,1,CircuitType.POWER,    "1:27.064 (Hamilton, 2019)",   87.064, 53, 99.0),
    Circuit("MIA","Miami International Autodrome",      "USA",5.410,19,2,CircuitType.STREET,   "1:29.708 (Russell, 2023)",    89.708, 57,105.0),
    Circuit("MON","Circuit de Monaco",                  "MCO",3.337,19,0,CircuitType.STREET,   "1:10.166 (Leclerc, 2023)",    70.166, 78,105.0),
    Circuit("CAN","Circuit Gilles Villeneuve",          "CAN",4.361,13,1,CircuitType.STREET,   "1:21.459 (Bottas, 2018)",     81.459, 70,111.0),
    Circuit("BAR","Circuit de Barcelona-Catalunya",     "ESP",4.657,16,2,CircuitType.BALANCED, "1:18.149 (Bottas, 2018)",     78.149, 66,102.0),
    Circuit("AUT","Red Bull Ring",                      "AUT",4.318,10,1,CircuitType.BALANCED, "1:05.619 (Bottas, 2020)",     65.619, 71,108.0),
    Circuit("GBR","Silverstone Circuit",                "GBR",5.891,18,2,CircuitType.BALANCED, "1:27.097 (Hamilton, 2020)",   87.097, 52, 97.8),
    Circuit("BEL","Circuit de Spa-Francorchamps",       "BEL",6.996,19,2,CircuitType.POWER,    "1:41.252 (Verstappen, 2023)",101.252, 44, 90.0),
    Circuit("HUN","Hungaroring",                        "HUN",4.381,14,0,CircuitType.BALANCED, "1:16.627 (Hamilton, 2020)",   76.627, 70,111.0),
    Circuit("NED","Circuit Park Zandvoort",             "NED",4.259,14,2,CircuitType.BALANCED, "1:11.097 (Bottas, 2021)",     71.097, 72,108.0),
    Circuit("ITA","Autodromo Nazionale di Monza",       "ITA",5.793,11,2,CircuitType.POWER,    "1:19.119 (Verstappen, 2023)", 79.119, 53, 81.0),
    Circuit("AZE","Baku City Circuit",                  "AZE",6.003,18,2,CircuitType.STREET,   "1:43.009 (Leclerc, 2019)",   103.009, 51, 96.0),
    Circuit("SIN","Marina Bay Street Circuit",          "SGP",5.063,23,2,CircuitType.STREET,   "1:41.905 (Hamilton, 2019)",  101.905, 61, 96.0),
    Circuit("USA","Circuit of The Americas",            "USA",5.513,20,2,CircuitType.BALANCED, "1:32.910 (Hamilton, 2017)",   92.910, 56,106.2),
    Circuit("MEX","Autódromo Hermanos Rodríguez",       "MEX",4.304,17,2,CircuitType.BALANCED, "1:18.741 (Hamilton, 2018)",   78.741, 71,105.0),
    Circuit("BRA","Autódromo José Carlos Pace",         "BRA",4.309,15,1,CircuitType.BALANCED, "1:10.540 (Bottas, 2016)",     70.540, 71,108.0),
    Circuit("LVG","Las Vegas Strip Circuit",            "USA",6.120,17,2,CircuitType.STREET,   "1:35.490 (Sainz, 2023)",      95.490, 50, 99.0),
    Circuit("QAT","Lusail International Circuit",       "QAT",5.419,16,2,CircuitType.BALANCED, "1:24.535 (Leclerc, 2021)",    84.535, 57,105.0),
    Circuit("ABU","Yas Marina Circuit",                 "UAE",5.281,16,2,CircuitType.BALANCED, "1:26.103 (Leclerc, 2019)",    86.103, 58,102.0),
]


# ============================================================================
# 2026 CHAMPIONSHIP STANDINGS — After Round 1 (Australian GP)
# Points: 25-18-15-12-10-8-6-4-2-1
# ============================================================================

def get_championship_standings() -> Dict[str, int]:
    return {
        "VER": 25, "LEC": 18, "RUS": 15, "NOR": 12, "HAM": 10,
        "PIA":  8, "SAI":  6, "ALO":  4, "GAS":  2, "ALB":  1,
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_driver_by_id(driver_id: str) -> Optional[Driver]:
    for d in F1_DRIVERS_2026:
        if d.driver_id == driver_id:
            return d
    return None


def get_team_by_name(team_name: str) -> Optional[Team]:
    for t in F1_TEAMS_2026:
        if t.name == team_name:
            return t
    return None


def get_circuit_by_id(circuit_id: str) -> Optional[Circuit]:
    for c in F1_CIRCUITS_2026:
        if c.circuit_id == circuit_id:
            return c
    return None


def get_driver_grid_spec(driver: Driver, championship_points: Dict[str, int]) -> Dict:
    """
    Convert a driver + team profile into car physics parameters
    for the race simulator.  Driver skill modulates team car baseline by ±10%.
    """
    team = get_team_by_name(driver.team)
    if not team:
        raise ValueError(f"Team '{driver.team}' not found for driver {driver.name}")

    base_max_speed = 90.0 + (team.power    * 8.0)   # 90–98 m/s
    base_accel     = 10.8 + (team.power    * 2.0)   # 10.8–12.8 m/s²
    base_grip      = 0.80 + (team.handling * 0.18)  # 0.80–0.98
    base_drag      = 0.72 - (team.power    * 0.08)  # 0.64–0.72

    return {
        "driver_id":        driver.driver_id,
        "driver_name":      driver.name,
        "team":             driver.team,
        "number":           driver.number,
        "nationality":      driver.nationality,
        "max_speed":        base_max_speed * (0.95 + driver.speed     * 0.10),
        "acceleration":     base_accel     * (0.95 + driver.speed     * 0.10),
        "tyre_grip":        base_grip      * (0.95 + driver.racecraft * 0.10),
        "drag_coefficient": base_drag,
        "cornering_ability":0.85 + (driver.racecraft * 0.15),
        "wet_weather":      driver.wet_weather,
        "consistency":      driver.consistency,
        "reliability":      team.reliability,
        "pit_efficiency":   team.pit_efficiency,
        "skill_rating":     driver.get_skill_rating(),
    }


def create_f1_2026_grid() -> List[Dict]:
    """
    Build the complete 22-car starting grid.
    Returns list of dicts ready for RaceSimulator.add_car()
    """
    standings = get_championship_standings()
    return [get_driver_grid_spec(d, standings) for d in F1_DRIVERS_2026]


# ============================================================================
# 2026 SEASON CALENDAR — 21 Races
# ============================================================================

SEASON_2026_CALENDAR = [
    {"round":  1, "name": "Australian Grand Prix",                  "circuit": "AUS", "date": "2026-03-15", "status": "completed"},
    {"round":  2, "name": "Chinese Grand Prix",                     "circuit": "CHN", "date": "2026-03-22", "status": "upcoming"},
    {"round":  3, "name": "Japanese Grand Prix",                    "circuit": "JPN", "date": "2026-04-05", "status": "upcoming"},
    {"round":  4, "name": "Miami Grand Prix",                       "circuit": "MIA", "date": "2026-05-03", "status": "upcoming"},
    {"round":  5, "name": "Grand Prix de Monaco",                   "circuit": "MON", "date": "2026-05-24", "status": "upcoming"},
    {"round":  6, "name": "Canadian Grand Prix",                    "circuit": "CAN", "date": "2026-06-14", "status": "upcoming"},
    {"round":  7, "name": "Gran Premio de Barcelona-Catalunya",     "circuit": "BAR", "date": "2026-06-28", "status": "upcoming"},
    {"round":  8, "name": "Austrian Grand Prix",                    "circuit": "AUT", "date": "2026-07-05", "status": "upcoming"},
    {"round":  9, "name": "British Grand Prix",                     "circuit": "GBR", "date": "2026-07-19", "status": "upcoming"},
    {"round": 10, "name": "Belgian Grand Prix",                     "circuit": "BEL", "date": "2026-07-26", "status": "upcoming"},
    {"round": 11, "name": "Hungarian Grand Prix",                   "circuit": "HUN", "date": "2026-08-02", "status": "upcoming"},
    {"round": 12, "name": "Dutch Grand Prix",                       "circuit": "NED", "date": "2026-08-30", "status": "upcoming"},
    {"round": 13, "name": "Gran Premio d'Italia",                   "circuit": "ITA", "date": "2026-09-06", "status": "upcoming"},
    {"round": 14, "name": "Azerbaijan Grand Prix",                  "circuit": "AZE", "date": "2026-09-20", "status": "upcoming"},
    {"round": 15, "name": "Singapore Grand Prix",                   "circuit": "SIN", "date": "2026-10-04", "status": "upcoming"},
    {"round": 16, "name": "United States Grand Prix",               "circuit": "USA", "date": "2026-10-18", "status": "upcoming"},
    {"round": 17, "name": "Gran Premio de la Ciudad de México",     "circuit": "MEX", "date": "2026-10-25", "status": "upcoming"},
    {"round": 18, "name": "Grande Prêmio de São Paulo",             "circuit": "BRA", "date": "2026-11-08", "status": "upcoming"},
    {"round": 19, "name": "Las Vegas Grand Prix",                   "circuit": "LVG", "date": "2026-11-21", "status": "upcoming"},
    {"round": 20, "name": "Qatar Airways Qatar Grand Prix",         "circuit": "QAT", "date": "2026-11-29", "status": "upcoming"},
    {"round": 21, "name": "Abu Dhabi Grand Prix",                   "circuit": "ABU", "date": "2026-12-06", "status": "upcoming"},
]
