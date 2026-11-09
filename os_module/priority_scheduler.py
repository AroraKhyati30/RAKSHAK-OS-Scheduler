
def calculate_victim_score(
    victim,
    current_time,
    target_wait=600
):
    """
    Calculate Victim Priority Score (VPS) from 0 to 100.

    target_wait is a configurable waiting-time target
    in simulation seconds.
    """

    severity_score = (victim.severity - 1) / 4.0
    vulnerability_score = (victim.vulnerability - 1) / 4.0

    waiting_time = max(
        0.0, current_time - victim.arrival_time
    )

    waiting_score = min(
        waiting_time / max(target_wait, 1),
        1.0
    )

    score = 100 * (
        0.50 * severity_score
        + 0.30 * vulnerability_score
        + 0.20 * waiting_score
    )

    return round(score, 2)


def select_priority_victim(
    zone_id,
    victims,
    current_time,
    target_wait=600
):
    """
    Select the highest-priority pending victim within a zone.
    """

    candidates = [
        v for v in victims
        if v.zone_id == zone_id and v.status == "pending"
    ]

    if not candidates:
        return None

    # Within the selected zone, life-threatening requests
    # and severity-5 requests receive emergency precedence.
    emergencies = [
        v for v in candidates
        if v.life_threatening or v.severity == 5
    ]

    if emergencies:
        candidates = emergencies

    return max(
        candidates,
        key=lambda v: (
            calculate_victim_score(
                v, current_time, target_wait
            ),
            -v.arrival_time
        )
    )
