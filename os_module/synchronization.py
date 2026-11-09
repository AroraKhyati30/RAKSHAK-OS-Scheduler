
from threading import Lock


# Protect shared in-memory scheduling state.
dispatch_lock = Lock()


def reserve_team(team, victim):
    """
    Reserve a team and mark a victim as assigned.

    Caller must already hold dispatch_lock.
    """

    if not team.available:
        return False

    if victim.status != "pending":
        return False

    team.available = False
    team.current_victim = victim.victim_id

    victim.status = "assigned"
    victim.assigned_team = team.team_id

    return True


def complete_rescue(
    team,
    victim,
    completion_time
):
    """
    Complete a simulated rescue and release its team.

    Caller must already hold dispatch_lock.
    """

    if victim.status != "assigned":
        return False

    if team.current_victim != victim.victim_id:
        return False

    if victim.dispatch_time is None:
        return False

    completion_time = max(
        completion_time, victim.dispatch_time
    )

    team.busy_seconds += (
        completion_time - victim.dispatch_time
    )

    victim.completion_time = completion_time
    victim.status = "rescued"

    team.available = True
    team.current_victim = None

    return True
