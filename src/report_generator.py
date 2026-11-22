
import csv
import os
from collections import Counter


def write_reports(visits):

    # Priority order
    priority_order = {
        "see_now": 1,
        "today": 2,
        "routine": 3
    }

    # Sort visits by priority and arrival time
    sorted_visits = sorted(
        visits,
        key=lambda visit: (
            priority_order[visit["priority"]],
            visit["arrival_time"]
        )
    )

    # Create reports folder
    os.makedirs("reports", exist_ok=True)

    # Generate nurse_queue.csv
    with open("reports/nurse_queue.csv", "w", newline="", encoding="utf-8") as file:

        fieldnames = [
            "id",
            "arrival_time",
            "note",
            "category",
            "priority",
            "summary"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(sorted_visits)

    # Count priorities and categories
    priority_counts = Counter(
        visit["priority"] for visit in visits
    )

    category_counts = Counter(
        visit["category"] for visit in visits
    )

    # Count visits by arrival hour
    hour_counts = Counter(
        visit["arrival_time"].split(":")[0]
        for visit in visits
    )

    # Generate summary.txt
    with open("reports/summary.txt", "w", encoding="utf-8") as file:

        file.write("CLINIC VISIT SUMMARY\n")
        file.write("====================\n\n")

        file.write("Priority Counts:\n")

        for priority, count in priority_counts.items():
            file.write(f"{priority}: {count}\n")

        file.write("\nCategory Counts:\n")

        for category, count in category_counts.items():
            file.write(f"{category}: {count}\n")

        file.write("\nArrival Hour Counts:\n")

        for hour, count in sorted(hour_counts.items()):
            file.write(f"{hour}:00 - {count}\n")


if __name__ == "__main__":

    test_visits = [
        {
            "id": "1",
            "arrival_time": "09:00",
            "note": "Mild fever",
            "category": "fever_cold",
            "priority": "today",
            "summary": "Mild fever since morning"
        },
        {
            "id": "2",
            "arrival_time": "09:15",
            "note": "Chest pain",
            "category": "pain",
            "priority": "see_now",
            "summary": "Chest pain"
        },
        {
            "id": "3",
            "arrival_time": "10:00",
            "note": "Headache",
            "category": "pain",
            "priority": "routine",
            "summary": "Headache since morning"
        }
    ]

    write_reports(test_visits)

    print("Reports generated successfully!")
