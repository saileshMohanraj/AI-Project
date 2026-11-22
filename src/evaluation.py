
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from classifier import classify, GeminiQuotaExhausted
from safety import apply_safety

test_cases = [
    {
        "note": "I have a mild fever since morning",
        "category": "fever_cold",
        "priority": "today"
    },
    {
        "note": "My stomach hurts after breakfast",
        "category": "stomach",
        "priority": "today"
    },
    {
        "note": "I slipped and hurt my ankle",
        "category": "injury",
        "priority": "today"
    },
    {
        "note": "My skin is itchy after eating peanuts",
        "category": "allergy",
        "priority": "today"
    },
    {
        "note": "Enakku nenju vali irukku",
        "category": "pain",
        "priority": "see_now"
    }
]

correct = 0

for test in test_cases:
    print("\nTesting:", test["note"])

    try:
        result = classify(test["note"])

        if result is None:
            print("Classification unavailable")
            continue

        final_priority = apply_safety(
            test["note"], result["priority"]
        )

        category_ok = result["category"] == test["category"]
        priority_ok = final_priority == test["priority"]

        if category_ok and priority_ok:
            correct += 1
            print("Result: CORRECT")
        else:
            print("Result: INCORRECT")

        print("Expected:", test["category"], test["priority"])
        print("Actual:", result["category"], final_priority)

    except GeminiQuotaExhausted:
        print("Gemini quota exhausted. Evaluation stopped.")
        break

print("\nEvaluation complete.")
print("Correct:", correct, "out of", len(test_cases))
