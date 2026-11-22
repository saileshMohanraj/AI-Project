
def raise_priority(current_priority, required_priority):

    priorities = {
        "see_now": 1,
        "today": 2,
        "routine": 3
    }

    if current_priority not in priorities:
        raise ValueError("Invalid current priority")

    if required_priority not in priorities:
        raise ValueError("Invalid required priority")

    if priorities[required_priority] < priorities[current_priority]:
        return required_priority

    return current_priority


if __name__ == "__main__":

    print(raise_priority("routine", "today"))
    print(raise_priority("routine", "see_now"))
    print(raise_priority("see_now", "routine"))
