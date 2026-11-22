def is_valid(result):
    categories = [
        "injury",
        "fever_cold",
        "stomach",
        "pain",
        "allergy",
        "other"
    ]
    priorities = [
        "see_now",
        "today",
        "routine"
    ]
    if not isinstance(result, dict):
        return False
    if"category" not in result:
        return False
    if"priority" not in result:
        return False
    if"summary" not in result:
        return False
    if result["category"] not in categories:
        return False
    if result["priority"] not in priorities:
        return False
    if not isinstance(result["summary"], str):
        return False
    if len(result["summary"].split()) >12:
        return False
    return True
test_result = {
    "category": "fever_cold",
    "priority": "today",
    "summary": "Mild fever since morning"
}

