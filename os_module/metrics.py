
def calculate_metrics(victims, teams, simulation_time):
    """
    Calculate basic scheduling performance metrics.

    simulation_time must be elapsed simulation time,
    not an absolute timestamp.
    """

    total_requests = len(victims)

    dispatched = [
        v for v in victims
        if v.dispatch_time is not None
    ]

    rescued = [
        v for v in victims
        if v.status == "rescued"
    ]

    waiting_times = [
        max(0.0, v.dispatch_time - v.arrival_time)
        for v in dispatched
    ]

    average_wait = (
        sum(waiting_times) / len(waiting_times)
        if waiting_times else 0.0
    )

    maximum_wait = max(waiting_times, default=0.0)

    dispatch_rate = (
        len(dispatched) / total_requests * 100
        if total_requests else 0.0
    )

    completion_rate = (
        len(rescued) / total_requests * 100
        if total_requests else 0.0
    )

    total_busy = sum(
        team.busy_seconds for team in teams
    )

    total_team_time = (
        len(teams) * max(simulation_time, 0.0)
    )

    utilization = (
        min(total_busy / total_team_time * 100, 100.0)
        if total_team_time > 0 else 0.0
    )

    return {
        "total_requests": total_requests,
        "dispatched_requests": len(dispatched),
        "completed_rescues": len(rescued),
        "pending_requests": sum(
            1 for v in victims if v.status == "pending"
        ),
        "average_waiting_time_seconds": round(
            average_wait, 2
        ),
        "maximum_waiting_time_seconds": round(
            maximum_wait, 2
        ),
        "dispatch_rate_percent": round(
            dispatch_rate, 2
        ),
        "completion_rate_percent": round(
            completion_rate, 2
        ),
        "team_utilization_percent": round(
            utilization, 2
        ),
    }
