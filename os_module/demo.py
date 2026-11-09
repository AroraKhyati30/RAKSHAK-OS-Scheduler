
from os_module.models import Victim, RescueTeam
from os_module.scheduler import dispatch_next, finish_rescue
from os_module.zone_analyzer import calculate_zone_scores
from os_module.metrics import calculate_metrics


def main():
    # 1. Create sample distress requests.
    victims = [
        Victim(
            victim_id="V1",
            zone_id="Zone-A",
            severity=5,
            vulnerability=5,
            arrival_time=0,
            latitude=30.32,
            longitude=78.03,
            required_resources=["boat"],
            life_threatening=True,
        ),
        Victim(
            victim_id="V2",
            zone_id="Zone-A",
            severity=4,
            vulnerability=4,
            arrival_time=10,
            latitude=30.33,
            longitude=78.04,
            required_resources=["boat"],
        ),
        Victim(
            victim_id="V3",
            zone_id="Zone-B",
            severity=3,
            vulnerability=3,
            arrival_time=20,
            latitude=30.30,
            longitude=78.01,
            required_resources=["ambulance"],
        ),
        Victim(
            victim_id="V4",
            zone_id="Zone-C",
            severity=2,
            vulnerability=5,
            arrival_time=30,
            latitude=30.29,
            longitude=78.00,
            required_resources=["medical_kit"],
        ),
    ]

    # 2. Create rescue teams.
    teams = [
        RescueTeam(
            team_id="T1",
            resources=["boat", "medical_kit"],
            latitude=30.31,
            longitude=78.02,
        ),
        RescueTeam(
            team_id="T2",
            resources=["ambulance", "medical_kit"],
            latitude=30.30,
            longitude=78.02,
        ),
    ]

    # 3. Display the initial zone scores.
    print("\n--- INITIAL ZONE SCORES ---")

    scores = calculate_zone_scores(victims, teams)

    for zone_id, score in sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"{zone_id}: {score}/100")

    # 4. Start after all sample requests have arrived.
    simulation_start = 30.0
    current_time = simulation_start
    simulated_rescue_duration = 60.0

    print("\n--- RESCUE DISPATCH LOG ---")

    # 5. Dispatch and complete requests.
    while any(v.status == "pending" for v in victims):
        result = dispatch_next(
            victims,
            teams,
            current_time,
        )

        print("\nDispatch:", result)

        if result.get("message") != "Rescue team dispatched":
            print("Unable to dispatch remaining requests.")
            break

        # Simulate 60 seconds for one rescue.
        current_time += simulated_rescue_duration

        completion = finish_rescue(
            result["victim_id"],
            victims,
            teams,
            completion_time=current_time,
        )

        print("Completion:", completion)

    # 6. Display final victim statuses.
    print("\n--- FINAL VICTIM STATUS ---")

    for victim in victims:
        print(
            f"Victim={victim.victim_id}, "
            f"Zone={victim.zone_id}, "
            f"Status={victim.status}, "
            f"Team={victim.assigned_team}"
        )

    # 7. Calculate elapsed simulation time.
    elapsed_time = current_time - simulation_start

    # 8. Display OS performance metrics.
    print("\n--- PERFORMANCE METRICS ---")

    metrics = calculate_metrics(
        victims,
        teams,
        elapsed_time,
    )

    for name, value in metrics.items():
        print(f"{name}: {value}")

    # 9. Display final team availability.
    print("\n--- RESCUE TEAM STATUS ---")

    for team in teams:
        print(
            f"{team.team_id}: "
            f"available={team.available}, "
            f"busy_seconds={team.busy_seconds}"
        )


if __name__ == "__main__":
    main()
