
import time
import sys
import os

# Allow Python to find modules inside the src folder
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "src")
)

from data_loader import load_visits
from classifier import classify, GeminiQuotaExhausted
from validator import is_valid
from safety import apply_safety
from report_generator import write_reports
from terminal_ui import display_waitlist


def main():

    visits = load_visits()

    print("================================")
    print("      CLINIC VISIT SORTER")
    print("================================")

    print("Total visits loaded:", len(visits))

    gemini_available = True

    for index, visit in enumerate(visits):

        note = visit["note"]

        print("\nProcessing visit:", visit["id"])
        print("Note:", note)

        result = None

        # Try Gemini classification
        if gemini_available:

            try:
                result = classify(note)

            except GeminiQuotaExhausted:

                print("Gemini quota exhausted.")
                print("Using fallback for the remaining visits.")

                gemini_available = False

        # Use fallback if Gemini is unavailable or result is invalid
        if result is None or not is_valid(result):

            print("Using fallback classification.")

            result = {
                "category": "other",
                "priority": "today",
                "summary": "Classification unavailable"
            }

        else:

            print("Category:", result["category"])
            print("Priority:", result["priority"])
            print("Summary:", result["summary"])

        # Add classification to the visit
        visit.update(result)

        # Unknown cases must not be routine
        if (
            result["category"] == "other"
            and result["priority"] == "routine"
        ):
            result["priority"] = "today"

        # Apply red-flag safety checks
        final_priority = apply_safety(
            note,
            result["priority"]
        )

        visit["priority"] = final_priority

        print("Final Priority:", final_priority)

        # Wait only while Gemini is available
        if (
            gemini_available
            and index < len(visits) - 1
        ):
            print("Waiting 13 seconds before the next visit...")
            time.sleep(13)

    # Display the final priority waitlist
    display_waitlist(visits)

    # Generate CSV and summary reports
    write_reports(visits)

    print("\n================================")
    print("REPORTS GENERATED SUCCESSFULLY!")
    print("================================")
    print("Check the reports folder.")


if __name__ == "__main__":
    main()
