
from collections import defaultdict


def calculate_zone_scores(victims, teams):
    """
    Calculate a Zone Criticality Score (ZCS) from 0 to 100.
    Only pending victims contribute to zone scores.
    """

    pending_by_zone = defaultdict(list)

    for victim in victims:
        if victim.status == "pending":
            pending_by_zone[victim.zone_id].append(victim)

    scores = {}

    for zone_id, zone_victims in pending_by_zone.items():
        total = len(zone_victims)

        if total == 0:
            continue

        # Critical-victim burden: severity 5 counts as critical.
        critical_count = sum(
            1 for v in zone_victims if v.severity == 5
        )

        critical_burden = min(critical_count / 5.0, 1.0)

        # Normalize severity and vulnerability to [0, 1].
        avg_severity = sum(
            (v.severity - 1) / 4.0 for v in zone_victims
        ) / total

        avg_vulnerability = sum(
            (v.vulnerability - 1) / 4.0
            for v in zone_victims
        ) / total

        # Count available teams that can serve at least
        # one pending victim in this zone.
        suitable_teams = []

        for team in teams:
            if not team.available:
                continue

            can_serve = any(
                set(v.required_resources).issubset(
                    set(team.resources)
                )
                for v in zone_victims
            )

            if can_serve:
                suitable_teams.append(team)

        available_count = len(suitable_teams)

        # Higher demand per available team means more pressure.
        demand_pressure = min(
            total / (max(available_count, 1) * 3.0),
            1.0
        )

        score = 100 * (
            0.35 * critical_burden
            + 0.30 * avg_severity
            + 0.20 * avg_vulnerability
            + 0.15 * demand_pressure
        )

        scores[zone_id] = round(score, 2)

    return scores
