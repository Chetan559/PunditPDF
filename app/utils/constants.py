# FILE: app/utils/constants.py
from enum import Enum

class QuizStatus(str, Enum):
    ACTIVE = "active"
    EVALUATED = "evaluated"

def calculate_grade(percentage: float) -> str:
    """Returns a letter grade based on the percentage score."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"