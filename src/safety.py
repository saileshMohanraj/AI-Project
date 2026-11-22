
from priority import raise_priority


def check_red_flags(note):

    note = note.lower()

    red_flags = [
        "chest pain",
        "pain in chest",
        "nenju vali",

        "difficulty breathing",
        "difficult to breathe",
        "cannot breathe",
        "can't breathe",
        "moochu vida kashtam",
        "moochu vida kashtama",

        "fainted",
        "fainting",
        "faint",
        "feeling faint",
        "dizzy and faint",
        "mayakkam pottu",

        "heavy bleeding",
        "bleeding heavily",
        "blood won't stop",
        "niraya ratham",

        "lips are swelling",
        "lip swelling",
        "face is swelling",
        "face swelling",

        "cannot stand",
        "can't stand",
        "unable to stand",
        "nikka mudiyala"
    ]

    for flag in red_flags:
        if flag in note:
            return True

    return False


def apply_safety(note, current_priority):

    if check_red_flags(note):
        return raise_priority(current_priority, "see_now")

    return current_priority
