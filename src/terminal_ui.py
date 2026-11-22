
from textwrap import shorten

PRIORITY_RANK = {
    "see_now": 1,
    "today": 2,
    "routine": 3
}

def display_waitlist(visits):

    sorted_visits = sorted(
        visits,
        key=lambda visit: (
            PRIORITY_RANK.get(visit["priority"], 2),
            visit["arrival_time"]
        )
    )

    print("\n")
    print("=" * 90)
    print("             CLINIC VISIT PRIORITY WAITLIST")
    print("=" * 90)

    print("Total visits:", len(sorted_visits))
    print("-" * 90)

    print(
        f"{'ID':<8}"
        f"{'ARRIVAL':<12}"
        f"{'PRIORITY':<15}"
        f"{'CATEGORY':<15}"
        f"SUMMARY"
    )

    print("-" * 90)

    for visit in sorted_visits:

        priority = visit["priority"].upper()

        summary = shorten(
            visit.get("summary", visit["note"]),
            width=35
        )

        print(
            f"{visit['id']:<8}"
            f"{visit['arrival_time']:<12}"
            f"[{priority:<12}]"
            f"{visit['category']:<15}"
            f"{summary}"
        )

    print("-" * 90)
    print("Priority order: SEE_NOW -> TODAY -> ROUTINE")
    print("=" * 90)
