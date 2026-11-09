
from os_module.zone_analyzer import calculate_zone_scores
from os_module.priority_scheduler import (
    calculate_victim_score,
    select_priority_victim,
)
from os_module.resource_manager import find_best_rescue_team
from os_module.synchronization import (
    dispatch_lock,
    reserve_team,
    complete_rescue,
)


STARVATION_WAIT_SECONDS = 600


def dispatch_next(victims, teams, current_time):
    """
    Dispatch one victim using zone-aware priority scheduling.

    Priority order:
    1. Life-threatening / severity-5 emergency
    2. Overdue pending victim with a suitable team
    3. Highest-scoring zone, then highest-scoring victim

    Active rescue missions are not interrupted automatically.
    """

    with dispatch_lock:
        pending = [
            v for v in victims
            if v.status == "pending"
        ]

        if not pending:
            return {
                "message": "No pending requests"
            }

        zone_scores = calculate_zone_scores(
            victims, teams
        )

        # ---------------------------------------------
        # 1. Emergency override across all zones
        # ---------------------------------------------
        emergencies = [
            v for v in pending
            if v.life_threatening or v.severity == 5
        ]

        emergencies.sort(
            key=lambda v: (
                v.severity,
                v.vulnerability,
                -v.arrival_time
            ),
            reverse=True
        )

        for candidate in emergencies:
            team = find_best_rescue_team(
                candidate, teams
            )

            if team is not None:
                if reserve_team(team, candidate):
                    candidate.dispatch_time = current_time

                    return {
                        "message": "Rescue team dispatched",
                        "victim_id": candidate.victim_id,
                        "zone_id": candidate.zone_id,
                        "team_id": team.team_id,
                        "priority_type": "emergency",
                        "zone_scores": zone_scores,
                    }

        # ---------------------------------------------
        # 2. Starvation prevention using waiting time
        # ---------------------------------------------
        overdue = [
            v for v in pending
            if current_time - v.arrival_time
            >= STARVATION_WAIT_SECONDS
        ]

        overdue.sort(
            key=lambda v: (
                current_time - v.arrival_time,
                calculate_victim_score(v, current_time)
            ),
            reverse=True
        )

        for candidate in overdue:
            team = find_best_rescue_team(
                candidate, teams
            )

            if team is not None:
                if reserve_team(team, candidate):
                    candidate.dispatch_time = current_time

                    return {
                        "message": "Rescue team dispatched",
                        "victim_id": candidate.victim_id,
                        "zone_id": candidate.zone_id,
                        "team_id": team.team_id,
                        "priority_type": "overdue",
                        "zone_scores": zone_scores,
                    }

        # ---------------------------------------------
        # 3. Zone-wise priority scheduling
        # ---------------------------------------------
        ranked_zones = sorted(
            zone_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )

        for zone_id, zone_score in ranked_zones:
            candidate = select_priority_victim(
                zone_id,
                victims,
                current_time
            )

            if candidate is None:
                continue

            team = find_best_rescue_team(
                candidate, teams
            )

            if team is None:
                # Try another zone if no suitable team exists.
                continue

            if reserve_team(team, candidate):
                candidate.dispatch_time = current_time

                return {
                    "message": "Rescue team dispatched",
                    "victim_id": candidate.victim_id,
                    "zone_id": candidate.zone_id,
                    "team_id": team.team_id,
                    "priority_type": "zone_priority",
                    "selected_zone_score": zone_score,
                    "zone_scores": zone_scores,
                }

        # ---------------------------------------------
        # 4. No compatible team available
        # ---------------------------------------------
        return {
            "message": "No suitable team available",
            "zone_scores": zone_scores,
            "pending_victims": [
                v.victim_id for v in pending
            ],
        }


def finish_rescue(
    victim_id,
    victims,
    teams,
    completion_time
):
    """
    Complete a simulated rescue and release the team.
    """

    with dispatch_lock:
        victim = next(
            (
                v for v in victims
                if v.victim_id == victim_id
            ),
            None
        )

        if victim is None:
            return {
                "message": "Victim not found"
            }

        if victim.status != "assigned":
            return {
                "message": "Victim is not currently assigned"
            }

        team = next(
            (
                t for t in teams
                if t.team_id == victim.assigned_team
            ),
            None
        )

        if team is None:
            return {
                "message": "Assigned team not found"
            }

        success = complete_rescue(
            team, victim, completion_time
        )

        if not success:
            return {
                "message": "Could not complete rescue"
            }

        return {
            "message": "Rescue completed",
            "victim_id": victim.victim_id,
            "team_id": team.team_id,
            "completion_time": victim.completion_time,
        }
