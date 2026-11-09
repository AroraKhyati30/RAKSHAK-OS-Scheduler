
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Victim:
    victim_id: str
    zone_id: str
    severity: int
    vulnerability: int
    arrival_time: float

    latitude: float = 0.0
    longitude: float = 0.0

    required_resources: list[str] = field(default_factory=list)
    life_threatening: bool = False

    status: str = "pending"
    assigned_team: Optional[str] = None

    dispatch_time: Optional[float] = None
    completion_time: Optional[float] = None


@dataclass
class RescueTeam:
    team_id: str
    resources: list[str] = field(default_factory=list)

    latitude: float = 0.0
    longitude: float = 0.0

    available: bool = True
    current_victim: Optional[str] = None

    busy_seconds: float = 0.0


@dataclass
class Zone:
    zone_id: str
    name: str
