
from math import radians, sin, cos, sqrt, atan2


def calculate_distance(team, victim):
    """
    Approximate straight-line distance in kilometres
    using the Haversine formula.
    """

    earth_radius_km = 6371.0

    lat1 = radians(team.latitude)
    lat2 = radians(victim.latitude)

    dlat = radians(victim.latitude - team.latitude)
    dlon = radians(victim.longitude - team.longitude)

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def find_best_rescue_team(victim, teams):
    """
    Return the nearest available compatible rescue team.
    Return None if no suitable team is available.
    """

    candidates = []

    for team in teams:
        if not team.available:
            continue

        required = set(victim.required_resources)
        available = set(team.resources)

        if not required.issubset(available):
            continue

        distance = calculate_distance(team, victim)

        candidates.append((distance, team))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])

    return candidates[0][1]
