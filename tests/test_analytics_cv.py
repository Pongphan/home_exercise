from datetime import date

from fitjourney.analytics import calculate_streak, estimate_calories
from fitjourney.cv_engine import RepCounter, calculate_angle


def test_joint_angle():
    assert round(calculate_angle((1, 0), (0, 0), (0, 1))) == 90


def test_squat_rep_uses_full_cycle():
    counter = RepCounter("squat")
    for angle in [170, 120, 90, 80, 110, 160, 170]:
        counter.update(angle)
    assert counter.reps == 1


def test_curl_rep_uses_full_cycle():
    counter = RepCounter("curl")
    for angle in [160, 120, 55, 45, 90, 160, 55]:
        counter.update(angle)
    assert counter.reps == 2


def test_streak_and_calories():
    sessions = [
        {"completed_at": "2026-07-14T08:00:00+00:00"},
        {"completed_at": "2026-07-13T08:00:00+00:00"},
        {"completed_at": "2026-07-12T08:00:00+00:00"},
    ]
    assert calculate_streak(sessions, date(2026, 7, 14)) == 3
    assert estimate_calories(70, 30, [5]) == 183.8
