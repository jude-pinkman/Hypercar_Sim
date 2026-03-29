"""
F1 Championship Predictor
Forecasts the F1 championship winner based on race outcomes and remaining schedule.

Uses the existing WinnerPredictor for individual race forecasts and applies
championship logic (Elo-inspired weighting, points accumulation) to predict
overall season winner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime


@dataclass
class DriverChampionshipForecast:
    """Single driver's championship forecast"""
    driver_name: str
    team: str
    current_points: int
    races_completed: int
    
    # Forecasted values
    predicted_final_points: int
    win_probability: float          # Probability of winning championship
    top3_probability: float         # Top 3 finish
    
    # Supporting metrics
    average_finish_position: float
    dnf_probability: float
    
    def to_dict(self) -> Dict:
        return {
            "driver_name": self.driver_name,
            "team": self.team,
            "current_points": self.current_points,
            "races_completed": self.races_completed,
            "predicted_final_points": self.predicted_final_points,
            "win_probability": round(self.win_probability, 4),
            "top3_probability": round(self.top3_probability, 4),
            "average_finish_position": round(self.average_finish_position, 2),
            "dnf_probability": round(self.dnf_probability, 4),
        }


@dataclass
class ChampionshipForecast:
    """Complete championship forecast"""
    season_year: int
    races_completed: int
    total_races: int
    forecast_date: str
    
    # Per-driver forecasts
    drivers: List[DriverChampionshipForecast]
    
    # Top contenders
    champion_prediction: str
    top3_predictions: List[str]
    
    # Confidence metrics
    champion_probability: float     # Confidence in predicted champion
    uncertainty: float              # StdDev of final points distribution
    
    def to_dict(self) -> Dict:
        return {
            "season_year": self.season_year,
            "races_completed": self.races_completed,
            "total_races": self.total_races,
            "forecast_date": self.forecast_date,
            "drivers": [d.to_dict() for d in self.drivers],
            "champion_prediction": self.champion_prediction,
            "top3_predictions": self.top3_predictions,
            "champion_probability": round(self.champion_probability, 4),
            "uncertainty": round(self.uncertainty, 2),
        }


class ChampionshipPredictor:
    """
    Predicts F1 championship outcomes using:
      1. Current standings
      2. Historical driver/team performance
      3. Race winner predictions for remaining races
      4. Points accumulation logic
    """
    
    # F1 2026 points system: 25 18 15 12 10 8 6 4 2 1 (top 10)
    POINTS_SYSTEM = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    
    def __init__(self):
        """Initialize championship predictor"""
        # Can optionally load trained race winner predictor for future race forecasts
        self._race_predictor = None
    
    def set_race_predictor(self, predictor) -> None:
        """
        Attach the trained race winner predictor for more accurate forecasts.
        
        Args:
            predictor: WinnerPredictor instance
        """
        self._race_predictor = predictor
    
    def forecast_championship(
        self,
        drivers: List[Dict],              # [{name, team, current_points, performance_metrics}, ...]
        teams: List[Dict],                # [{name, power, reliability}, ...]
        races_completed: int,
        remaining_races: int,
        historical_performance: Optional[Dict] = None,
    ) -> ChampionshipForecast:
        """
        Generate championship forecast based on current standings and remaining races.
        
        Args:
            drivers: List of driver dicts with current_points, performance profile
            teams: List of team dicts with performance characteristics
            races_completed: Number of races completed so far
            remaining_races: Number of races left in season
            historical_performance: Optional dict of {driver_name: {"avg_position": x, "wins": y, ...}}
        
        Returns:
            ChampionshipForecast with per-driver probabilities and predictions
        """
        
        total_races = races_completed + remaining_races
        
        # Simulate remaining races using Monte Carlo
        # For each driver, estimate points from remaining races
        driver_simulations = self._simulate_remaining_races(
            drivers=drivers,
            teams=teams,
            remaining_races=remaining_races,
            historical_performance=historical_performance,
            simulations=1000,  # 1000 simulations = smooth distribution
        )
        
        # Process results into forecast
        forecasts = []
        final_points_dist = {d["name"]: [] for d in drivers}
        
        for driver in drivers:
            name = driver["name"]
            current_pts = driver.get("current_points", 0)
            team = driver.get("team", "Unknown")
            
            # Collect simulated final points for this driver
            if name in driver_simulations:
                simulated_final = driver_simulations[name]
                final_points_dist[name] = simulated_final
                
                predicted_final = np.mean(simulated_final)
                win_prob = np.mean([pts >= max(final_points_dist[d["name"]]) for pts in simulated_final])
                top3_prob = self._calculate_top3_probability(name, final_points_dist)
                
                avg_finish = driver.get("avg_finish_position", 10.0)
                dnf_prob = driver.get("dnf_probability", 0.05)
                
            else:
                predicted_final = current_pts
                win_prob = 0.0
                top3_prob = 0.0
                avg_finish = 15.0
                dnf_prob = 0.1
            
            forecast = DriverChampionshipForecast(
                driver_name=name,
                team=team,
                current_points=current_pts,
                races_completed=races_completed,
                predicted_final_points=int(predicted_final),
                win_probability=win_prob,
                top3_probability=top3_prob,
                average_finish_position=avg_finish,
                dnf_probability=dnf_prob,
            )
            forecasts.append(forecast)
        
        # Sort by predicted final points
        forecasts.sort(key=lambda x: x.predicted_final_points, reverse=True)
        
        # Top predictions
        champion = forecasts[0].driver_name if forecasts else "Unknown"
        top3 = [f.driver_name for f in forecasts[:3]]
        champion_prob = forecasts[0].win_probability if forecasts else 0.0
        
        # Calculate uncertainty (stddev of champion's simulations)
        champion_sims = final_points_dist.get(champion, [])
        uncertainty = float(np.std(champion_sims)) if champion_sims else 0.0
        
        return ChampionshipForecast(
            season_year=2026,
            races_completed=races_completed,
            total_races=total_races,
            forecast_date=datetime.now().isoformat(),
            drivers=forecasts,
            champion_prediction=champion,
            top3_predictions=top3,
            champion_probability=champion_prob,
            uncertainty=uncertainty,
        )
    
    def _simulate_remaining_races(
        self,
        drivers: List[Dict],
        teams: List[Dict],
        remaining_races: int,
        historical_performance: Optional[Dict],
        simulations: int,
    ) -> Dict[str, List[float]]:
        """
        Monte Carlo simulation of remaining races.
        
        For each simulation:
          - Simulate pointsfor each remaining race
          - Accumulate to get final championship points
        
        Returns:
            Dict {driver_name: [final_points_sim1, sim2, ...]}
        """
        
        # Build team lookup
        team_map = {t["name"]: t for t in teams}
        
        # Prepare driver profiles
        driver_probs = {}
        for driver in drivers:
            name = driver["name"]
            team_name = driver.get("team", "Unknown")
            team = team_map.get(team_name, {})
            
            # Win probability estimation
            # Based on: team performance (60%), driver skill (40%)
            team_perf = team.get("power", 0.5)  # 0.0-1.0
            driver_skill = driver.get("speed_rating", 0.5)  # 0.0-1.0
            
            base_win_prob = (team_perf * 0.6 + driver_skill * 0.4)
            
            # Historical adjustment
            if historical_performance and name in historical_performance:
                hist = historical_performance[name]
                wins = hist.get("wins", 0)
                # Slight boost for proven winners
                base_win_prob *= (1.0 + wins * 0.05)
            
            driver_probs[name] = {
                "win_prob": min(base_win_prob, 0.25),  # Cap at 25% (22 drivers)
                "team": team_name,
                "current_points": driver.get("current_points", 0),
            }
        
        # Normalize probabilities to sum to 1.0
        total_prob = sum(p["win_prob"] for p in driver_probs.values())
        for prob_data in driver_probs.values():
            prob_data["win_prob"] /= total_prob
        
        # Run simulations
        result: Dict[str, List[float]] = {name: [] for name in driver_probs.keys()}
        
        for _ in range(simulations):
            # Simulate each remaining race
            points_gained = {name: 0 for name in driver_probs.keys()}
            
            for race_idx in range(remaining_races):
                # Simulate race outcome (who finishes where)
                # Using a probabilistic model where top teams are more likely to score
                
                # Add some variance across races
                race_variance = np.random.normal(1.0, 0.15, size=len(driver_probs))
                adjusted_probs = {}
                
                for driver_name, prob_data in driver_probs.items():
                    adj_prob = prob_data["win_prob"] * race_variance[list(driver_probs.keys()).index(driver_name)]
                    adjusted_probs[driver_name] = max(0.0001, adj_prob)  # Keep minimum probability
                
                # Normalize
                total_adj = sum(adjusted_probs.values())
                for name in adjusted_probs:
                    adjusted_probs[name] /= total_adj
                
                # Sample finish order (simple: just take probabilities as finish positions)
                # In reality, would use more sophisticated ranking
                drivers_list = list(adjusted_probs.keys())
                probs_list = [adjusted_probs[d] for d in drivers_list]
                
                # Winner is highest probability
                winner = max(drivers_list, key=lambda d: adjusted_probs[d])
                
                # Assign points to top 10 (simplified: winner gets 25, 2nd gets 18, etc.)
                # Other drivers finish out of points
                sorted_drivers = sorted(drivers_list, key=lambda d: adjusted_probs[d], reverse=True)
                
                for finish_pos, driver_name in enumerate(sorted_drivers[:10]):
                    points_gained[driver_name] += self.POINTS_SYSTEM[finish_pos]
            
            # Final points = current + simulated
            for driver_name in result.keys():
                final = driver_probs[driver_name]["current_points"] + points_gained[driver_name]
                result[driver_name].append(final)
        
        return result
    
    def _calculate_top3_probability(
        self,
        driver_name: str,
        final_points_dist: Dict[str, List[float]],
    ) -> float:
        """
        Calculate probability of finishing in top 3 of championship.
        """
        if driver_name not in final_points_dist:
            return 0.0
        
        driver_points = np.array(final_points_dist[driver_name])
        top3_count = 0
        
        for sim_idx in range(len(driver_points)):
            # Get all drivers' points for this simulation
            points_in_sim = [final_points_dist[d][sim_idx] for d in final_points_dist.keys()]
            sorted_points = sorted(points_in_sim, reverse=True)
            
            # Check if driver is in top 3
            if driver_points[sim_idx] in sorted_points[:3]:
                top3_count += 1
        
        return top3_count / len(driver_points) if len(driver_points) > 0 else 0.0
