"""
F1 Race Event System
Real-time event streaming for live race tracking via WebSocket.

Event types:
  - RaceStarted: Lights out, race begins
  - LapCompleted: Driver completes a lap
  - PositionChange: Driver moves up/down in standings
  - PitStop: Driver enters/exits pit lane
  - WeatherChange: Track condition changes
  - Incident: Crash, collision, DNF
  - RaceFinished: Chequered flag
  - Safety Car: Safety car deployment

Events are broadcast to connected WebSocket clients with JSON serialization.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from enum import Enum
import json
import asyncio


class EventType(Enum):
    """All possible race events"""
    RACE_STARTED = "race_started"
    RACE_FINISHED = "race_finished"
    LAP_COMPLETED = "lap_completed"
    POSITION_CHANGE = "position_change"
    PIT_STOP_ENTER = "pit_stop_enter"
    PIT_STOP_EXIT = "pit_stop_exit"
    WEATHER_CHANGE = "weather_change"
    INCIDENT = "incident"
    SAFETY_CAR = "safety_car"
    DRS_ENABLED = "drs_enabled"
    FASTEST_LAP = "fastest_lap"


@dataclass
class RaceEvent:
    """Base race event"""
    event_type: EventType
    timestamp: float           # Race time in seconds
    race_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dict"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "race_id": self.race_id,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        """Serialize event to JSON"""
        return json.dumps(self.to_dict())


# ============================================================================
# SPECIFIC EVENT TYPES (subclasses for clarity)
# ============================================================================

@dataclass
class RaceStartedEvent(RaceEvent):
    """Race begins"""
    def __init__(self, race_id: str, circuit_name: str, grid_positions: List[Dict], laps: int):
        super().__init__(
            event_type=EventType.RACE_STARTED,
            timestamp=0.0,
            race_id=race_id,
            data={
                "circuit": circuit_name,
                "grid_positions": grid_positions,
                "total_laps": laps,
            }
        )


@dataclass
class LapCompletedEvent(RaceEvent):
    """Driver completes a lap"""
    def __init__(self, race_id: str, timestamp: float, driver_name: str, lap: int,
                 lap_time: float, sector_times: List[float], position: int,
                 gap_to_leader: float):
        super().__init__(
            event_type=EventType.LAP_COMPLETED,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "driver": driver_name,
                "lap": lap,
                "lap_time": round(lap_time, 3),
                "sector_times": [round(st, 3) for st in sector_times],
                "position": position,
                "gap_to_leader": round(gap_to_leader, 3),
            }
        )


@dataclass
class PositionChangeEvent(RaceEvent):
    """Driver changes position"""
    def __init__(self, race_id: str, timestamp: float, driver_name: str,
                 old_position: int, new_position: int, lap: int):
        super().__init__(
            event_type=EventType.POSITION_CHANGE,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "driver": driver_name,
                "old_position": old_position,
                "new_position": new_position,
                "lap": lap,
            }
        )


@dataclass
class PitStopEvent(RaceEvent):
    """Driver enters/exits pit stop"""
    def __init__(self, race_id: str, timestamp: float, driver_name: str,
                 entering: bool, lap: int, pit_duration: Optional[float] = None,
                 tyre_from: Optional[str] = None, tyre_to: Optional[str] = None):
        super().__init__(
            event_type=EventType.PIT_STOP_ENTER if entering else EventType.PIT_STOP_EXIT,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "driver": driver_name,
                "lap": lap,
                "pit_duration": round(pit_duration, 2) if pit_duration else None,
                "tyre_from": tyre_from,
                "tyre_to": tyre_to,
            }
        )


@dataclass
class WeatherChangeEvent(RaceEvent):
    """Weather condition changes"""
    def __init__(self, race_id: str, timestamp: float, lap: int,
                 condition: str, grip_level: float, visibility: str):
        super().__init__(
            event_type=EventType.WEATHER_CHANGE,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "lap": lap,
                "condition": condition,
                "grip_level": round(grip_level, 2),
                "visibility": visibility,
            }
        )


@dataclass
class IncidentEvent(RaceEvent):
    """Incident (crash, collision, DNF)"""
    def __init__(self, race_id: str, timestamp: float, lap: int,
                 incident_type: str, drivers_involved: List[str],
                 location: str, dnf_drivers: Optional[List[str]] = None):
        super().__init__(
            event_type=EventType.INCIDENT,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "lap": lap,
                "incident_type": incident_type,  # "crash", "collision", "mechanical_failure"
                "drivers_involved": drivers_involved,
                "location": location,
                "dnf_drivers": dnf_drivers or [],
            }
        )


@dataclass
class SafetyCarEvent(RaceEvent):
    """Safety car deployed"""
    def __init__(self, race_id: str, timestamp: float, lap: int,
                 reason: str, restart_lap: Optional[int] = None):
        super().__init__(
            event_type=EventType.SAFETY_CAR,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "lap": lap,
                "reason": reason,
                "restart_lap": restart_lap,
            }
        )


@dataclass
class RaceFinishedEvent(RaceEvent):
    """Race ends"""
    def __init__(self, race_id: str, timestamp: float, results: List[Dict]):
        super().__init__(
            event_type=EventType.RACE_FINISHED,
            timestamp=timestamp,
            race_id=race_id,
            data={
                "results": results,
                "total_race_time": round(timestamp, 2),
            }
        )


# ============================================================================
# EVENT BROADCASTER
# ============================================================================

class RaceEventBroadcaster:
    """
    Manages live event broadcasting to multiple WebSocket clients.
    
    Usage:
      broadcaster = RaceEventBroadcaster()
      broadcaster.subscribe(race_id, websocket)
      
      # Emit event to all subscribers
      event = LapCompletedEvent(...)
      await broadcaster.broadcast(event)
    """
    
    def __init__(self):
        # Map: race_id -> list of callbacks (async functions)
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, race_id: str, callback: Callable) -> None:
        """
        Subscribe to race events.
        
        Args:
            race_id: Race ID to subscribe to
            callback: Async callback function(event) called when event is emitted
        """
        async with self._lock:
            if race_id not in self._subscribers:
                self._subscribers[race_id] = []
            self._subscribers[race_id].append(callback)
    
    async def unsubscribe(self, race_id: str, callback: Callable) -> None:
        """Unsubscribe from race events"""
        async with self._lock:
            if race_id in self._subscribers:
                self._subscribers[race_id].remove(callback)
                if not self._subscribers[race_id]:
                    del self._subscribers[race_id]
    
    async def broadcast(self, event: RaceEvent) -> None:
        """
        Broadcast event to all subscribers of this race.
        
        Args:
            event: RaceEvent to broadcast
        """
        async with self._lock:
            subscribers = self._subscribers.get(event.race_id, [])
        
        # Send to all subscribers in parallel
        tasks = []
        for callback in subscribers:
            tasks.append(callback(event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscriber_count(self, race_id: str) -> int:
        """Get number of active subscribers for this race"""
        return len(self._subscribers.get(race_id, []))


# ============================================================================
# GLOBAL BROADCASTER INSTANCE
# ============================================================================

_global_broadcaster: Optional[RaceEventBroadcaster] = None


def get_broadcaster() -> RaceEventBroadcaster:
    """Get or create global event broadcaster"""
    global _global_broadcaster
    if _global_broadcaster is None:
        _global_broadcaster = RaceEventBroadcaster()
    return _global_broadcaster


# ============================================================================
# RACE EVENT LOG
# ============================================================================

class RaceEventLog:
    """
    Stores historical events for a race.
    Useful for replays, debugging, and post-race analysis.
    """
    
    def __init__(self, race_id: str):
        self.race_id = race_id
        self.events: List[RaceEvent] = []
    
    def add_event(self, event: RaceEvent) -> None:
        """Record an event"""
        self.events.append(event)
    
    def get_events(self, event_type: Optional[EventType] = None) -> List[RaceEvent]:
        """Get all events, optionally filtered by type"""
        if event_type is None:
            return self.events
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_for_driver(self, driver_name: str) -> List[RaceEvent]:
        """Get all events involving a specific driver"""
        result = []
        for event in self.events:
            if event.data.get("driver") == driver_name:
                result.append(event)
        return result
    
    def to_json(self) -> str:
        """Serialize entire log to JSON"""
        return json.dumps({
            "race_id": self.race_id,
            "events": [e.to_dict() for e in self.events],
        }, indent=2)


# Global event logs (race_id -> RaceEventLog)
_event_logs: Dict[str, RaceEventLog] = {}


def get_event_log(race_id: str) -> RaceEventLog:
    """Get or create event log for a race"""
    if race_id not in _event_logs:
        _event_logs[race_id] = RaceEventLog(race_id)
    return _event_logs[race_id]
