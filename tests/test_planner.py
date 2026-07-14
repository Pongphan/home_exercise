from fitjourney.planner import adaptation, generate_plan


PROFILE = {
    "fitness_level": "Beginner",
    "goals": ["Strength"],
    "equipment": ["None", "Mat", "Chair"],
    "limitations": "",
    "weekly_days": 3,
    "session_minutes": 30,
}


def test_plan_matches_time_days_and_equipment():
    plan = generate_plan(PROFILE)
    assert len(plan["days"]) == 3
    assert all(3 <= len(day) <= 5 for day in plan["days"])
    allowed = {"None", "Mat", "Chair"}
    from fitjourney.exercises import get_exercise
    assert all(get_exercise(item["exercise_id"])["equipment"] in allowed for day in plan["days"] for item in day)


def test_adaptation_progress_and_deload():
    assert adaptation({"completion_rate": .95, "rpe": 6})["label"] == "Progressing"
    assert adaptation({"completion_rate": .5, "rpe": 9})["label"] == "Deload"


def test_knee_limit_filters_high_impact_lunges():
    profile = PROFILE | {"limitations": "right knee pain", "fitness_level": "Advanced"}
    ids = {x["exercise_id"] for day in generate_plan(profile)["days"] for x in day}
    assert "reverse_lunge" not in ids
    assert "hiit_skater" not in ids
