
import pytest

from os_module.models import Victim, RescueTeam
from os_module.scheduler import dispatch_next


def create_victim(
    victim_id,
    severity=3,
    vulnerability=50,
    arrival_time=0,
    life_threatening=False
):
    return Victim(
        victim_id=victim_id,
        zone_id="Zone-A",
        severity=severity,
        vulnerability=vulnerability,
        arrival_time=arrival_time,
        latitude=30.0,
        longitude=78.0,
        required_resources=[],
        life_threatening=life_threatening
    )


def create_team(team_id="Team-1"):
    return RescueTeam(
        team_id=team_id,
        resources=[],
        latitude=30.0,
        longitude=78.0
    )


def test_emergency_victim_gets_priority():
    """Emergency victims should be dispatched first."""

    victims = [
        create_victim("V1", severity=2),
        create_victim(
            "V2",
            severity=5,
            life_threatening=True
        )
    ]

    teams = [create_team()]

    result = dispatch_next(victims, teams, current_time=20)

    assert result["victim_id"] == "V2"


def test_starvation_prevention():
    """Victims waiting for 600 seconds should not starve."""

    victims = [
        create_victim("NEW", arrival_time=650),
        create_victim("OLD", arrival_time=0)
    ]

    teams = [create_team()]

    result = dispatch_next(victims, teams, current_time=700)

    assert result["victim_id"] == "OLD"


def test_rescue_team_assignment():
    """A rescue team should be assigned to a victim."""

    victims = [
        create_victim("V1")
    ]

    teams = [create_team("Team-1")]

    result = dispatch_next(victims, teams, current_time=20)

    assert result["victim_id"] == "V1"
    assert result["team_id"] == "Team-1"
    assert teams[0].available is False


def test_dispatch_result_structure():
    """Dispatch should return the required information."""

    victims = [create_victim("V1")]
    teams = [create_team()]

    result = dispatch_next(victims, teams, current_time=20)

    assert "message" in result
    assert "victim_id" in result
    assert "zone_id" in result
    assert "team_id" in result
    assert "priority_type" in result
    assert "zone_scores" in result
