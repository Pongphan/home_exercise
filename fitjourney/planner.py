"""Personalized workout generation and adaptive progression rules."""

from __future__ import annotations

from itertools import cycle

from .exercises import get_exercises


LEVEL_RANK = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}


def adaptation(adherence: dict[str, float]) -> dict:
    """Translate completion and perceived effort into a conservative adjustment."""
    completion = adherence.get("completion_rate", 1.0)
    rpe = adherence.get("rpe", 6.0)
    if completion >= 0.9 and rpe <= 7:
        return {"label": "Progressing", "set_delta": 1, "rep_delta": 1, "rest_delta": -5,
                "reason": "Recent sessions were completed comfortably."}
    if completion < 0.7 or rpe >= 9:
        return {"label": "Deload", "set_delta": -1, "rep_delta": -2, "rest_delta": 15,
                "reason": "Recent completion or effort suggests more recovery."}
    return {"label": "Maintaining", "set_delta": 0, "rep_delta": 0, "rest_delta": 0,
            "reason": "Current workload matches recent performance."}


def _allowed(exercise: dict, profile: dict) -> bool:
    equipment = set(profile.get("equipment", [])) | {"None"}
    if exercise["equipment"] not in equipment:
        return False
    level = LEVEL_RANK.get(profile.get("fitness_level", "Beginner"), 0)
    if LEVEL_RANK.get(exercise["level"], 0) > level + (1 if level else 0):
        return False
    limitations = profile.get("limitations", "").lower()
    # Conservative keyword filters; never presented as medical screening.
    if "knee" in limitations and exercise["id"] in {"reverse_lunge", "jumping_jack", "hiit_skater"}:
        return False
    if ("wrist" in limitations or "shoulder" in limitations) and exercise["id"] in {"pushup", "mountain_climber"}:
        return False
    if "back" in limitations and exercise["id"] in {"dumbbell_row", "mountain_climber"}:
        return False
    return True


def generate_plan(profile: dict, adherence: dict | None = None) -> dict:
    """Build a balanced, equipment-aware routine sized to the available time."""
    catalog = [x for x in get_exercises() if _allowed(x, profile)]
    goals = set(profile.get("goals", []))
    minutes = int(profile.get("session_minutes", 30))
    days = int(profile.get("weekly_days", 3))
    adjust = adaptation(adherence or {"completion_rate": 1.0, "rpe": 6.0})

    if "Mobility" in goals:
        category_pattern = ["Strength", "Flexibility", "Flexibility", "Cardio"]
    elif "Weight loss" in goals:
        category_pattern = ["Strength", "Cardio", "HIIT", "Flexibility"]
    else:
        category_pattern = ["Strength", "Strength", "Cardio", "Flexibility"]

    target_count = max(3, min(8, minutes // 6))
    pools = {category: [x for x in catalog if x["category"] == category]
             for category in {x["category"] for x in catalog}}
    offsets = {category: 0 for category in pools}
    planned_days: list[list[dict]] = []

    for day_index in range(days):
        items: list[dict] = []
        used: set[str] = set()
        pattern = cycle(category_pattern[day_index:] + category_pattern[:day_index])
        attempts = 0
        while len(items) < target_count and attempts < target_count * 8:
            attempts += 1
            category = next(pattern)
            pool = pools.get(category) or pools.get("Strength", [])
            if not pool:
                continue
            exercise = pool[offsets.get(category, 0) % len(pool)]
            offsets[category] = offsets.get(category, 0) + 1
            if exercise["id"] in used:
                continue
            used.add(exercise["id"])
            timed = exercise["category"] in {"Cardio", "HIIT", "Flexibility"}
            base_sets = 2 if profile.get("fitness_level") == "Beginner" else 3
            items.append({
                "exercise_id": exercise["id"],
                "sets": max(1, min(4, base_sets + adjust["set_delta"])),
                "reps": 0 if timed else max(6, 10 + adjust["rep_delta"]),
                "duration_sec": (30 if exercise["category"] == "HIIT" else 45) if timed else 0,
                "rest_sec": max(20, 45 + adjust["rest_delta"]),
            })
        planned_days.append(items)

    primary_goal = next(iter(profile.get("goals") or ["Wellness"]))
    return {
        "title": f"{primary_goal} · {days}-day plan",
        "difficulty": profile.get("fitness_level", "Beginner"),
        "minutes": minutes,
        "days": planned_days,
        "adaptation": adjust,
    }
