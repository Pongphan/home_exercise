"""Built-in exercise catalog and cached lookup helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # Allows pure unit tests without Streamlit installed.
    st = None


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


EXERCISES = [
    {
        "id": "bodyweight_squat", "name": "Bodyweight Squat", "category": "Strength",
        "level": "Beginner", "equipment": "None", "muscles": ["Quadriceps", "Glutes", "Core"],
        "instructions": ["Stand with feet just wider than hips.", "Sit hips back while keeping the chest tall.", "Drive through the whole foot to stand."],
        "tips": "Track knees over toes and use a pain-free depth.", "met": 5.0, "rep_mode": "squat",
    },
    {
        "id": "reverse_lunge", "name": "Reverse Lunge", "category": "Strength",
        "level": "Beginner", "equipment": "None", "muscles": ["Glutes", "Quadriceps", "Hamstrings"],
        "instructions": ["Step one foot back onto the ball of the foot.", "Lower both knees with an upright torso.", "Push through the front foot and alternate."],
        "tips": "Shorten the range or hold a chair if balance is limited.", "met": 4.5,
    },
    {
        "id": "incline_pushup", "name": "Incline Push-up", "category": "Strength",
        "level": "Beginner", "equipment": "Chair", "muscles": ["Chest", "Triceps", "Shoulders"],
        "instructions": ["Place hands on a stable raised surface.", "Brace into a straight head-to-heel line.", "Lower the chest, then press the surface away."],
        "tips": "Choose a higher surface to reduce difficulty.", "met": 4.0, "rep_mode": "pushup",
    },
    {
        "id": "pushup", "name": "Push-up", "category": "Strength",
        "level": "Intermediate", "equipment": "None", "muscles": ["Chest", "Triceps", "Core"],
        "instructions": ["Set hands below shoulders and brace the body.", "Lower with elbows angled back about 45 degrees.", "Press up without letting hips sag."],
        "tips": "Use knees or an incline when form begins to change.", "met": 6.0, "rep_mode": "pushup",
    },
    {
        "id": "glute_bridge", "name": "Glute Bridge", "category": "Strength",
        "level": "Beginner", "equipment": "Mat", "muscles": ["Glutes", "Hamstrings", "Core"],
        "instructions": ["Lie down with knees bent and feet planted.", "Tuck the pelvis gently and squeeze the glutes.", "Lift hips, pause, then lower with control."],
        "tips": "Stop before the lower back arches.", "met": 3.5,
    },
    {
        "id": "dumbbell_row", "name": "One-arm Dumbbell Row", "category": "Strength",
        "level": "Intermediate", "equipment": "Dumbbells", "muscles": ["Upper back", "Lats", "Biceps"],
        "instructions": ["Hinge at the hips with a long neutral spine.", "Pull the weight toward the back pocket.", "Lower until the arm is long without rotating."],
        "tips": "Brace the free hand on a chair if needed.", "met": 5.0,
    },
    {
        "id": "bicep_curl", "name": "Dumbbell Biceps Curl", "category": "Strength",
        "level": "Beginner", "equipment": "Dumbbells", "muscles": ["Biceps", "Forearms"],
        "instructions": ["Stand tall with arms at the sides.", "Curl without letting elbows drift forward.", "Squeeze briefly and lower fully."],
        "tips": "Use a load that allows a slow, controlled lowering.", "met": 3.5, "rep_mode": "curl",
    },
    {
        "id": "band_pull_apart", "name": "Band Pull-apart", "category": "Strength",
        "level": "Beginner", "equipment": "Resistance band", "muscles": ["Upper back", "Rear shoulders"],
        "instructions": ["Hold the band at shoulder height.", "Pull hands apart while keeping ribs down.", "Return slowly without losing tension."],
        "tips": "Use a lighter band if the shoulders shrug.", "met": 3.0,
    },
    {
        "id": "march", "name": "Low-impact Power March", "category": "Cardio",
        "level": "Beginner", "equipment": "None", "muscles": ["Hip flexors", "Calves", "Core"],
        "instructions": ["Stand tall and march with purposeful arm drive.", "Land softly under the hips.", "Increase pace while maintaining posture."],
        "tips": "Keep one foot on the floor for a joint-friendly option.", "met": 4.0,
    },
    {
        "id": "jumping_jack", "name": "Jumping Jack", "category": "Cardio",
        "level": "Intermediate", "equipment": "None", "muscles": ["Full body", "Calves", "Shoulders"],
        "instructions": ["Start tall with arms by the sides.", "Jump feet wide as hands travel overhead.", "Land softly and return with rhythm."],
        "tips": "Step side to side instead of jumping for low impact.", "met": 8.0,
    },
    {
        "id": "mountain_climber", "name": "Mountain Climber", "category": "Cardio",
        "level": "Intermediate", "equipment": "Mat", "muscles": ["Core", "Shoulders", "Hip flexors"],
        "instructions": ["Begin in a strong high plank.", "Drive one knee forward without lifting hips.", "Alternate smoothly at a sustainable pace."],
        "tips": "Elevate hands to reduce wrist and shoulder load.", "met": 8.0,
    },
    {
        "id": "shadow_box", "name": "Shadow Boxing", "category": "Cardio",
        "level": "Beginner", "equipment": "None", "muscles": ["Shoulders", "Core", "Calves"],
        "instructions": ["Take a staggered athletic stance.", "Punch forward while rotating through the torso.", "Retract each hand to guard position."],
        "tips": "Keep punches relaxed and never lock the elbow.", "met": 6.0,
    },
    {
        "id": "dead_bug", "name": "Dead Bug", "category": "Strength",
        "level": "Beginner", "equipment": "Mat", "muscles": ["Core", "Hip flexors"],
        "instructions": ["Lie on the back with hips and knees at 90 degrees.", "Brace gently and extend opposite arm and leg.", "Return without the lower back lifting."],
        "tips": "Shorten the lever if the back begins to arch.", "met": 3.0,
    },
    {
        "id": "hip_flexor_stretch", "name": "Half-kneeling Hip Stretch", "category": "Flexibility",
        "level": "Beginner", "equipment": "Mat", "muscles": ["Hip flexors", "Quadriceps"],
        "instructions": ["Kneel with the opposite foot forward.", "Tuck the pelvis without arching the back.", "Shift forward gently and breathe."],
        "tips": "Place padding under the kneeling knee.", "met": 2.0,
    },
    {
        "id": "thoracic_rotation", "name": "Open-book Rotation", "category": "Flexibility",
        "level": "Beginner", "equipment": "Mat", "muscles": ["Upper back", "Chest", "Shoulders"],
        "instructions": ["Lie on one side with knees stacked.", "Reach the top arm across and open toward the floor.", "Follow the hand with the eyes, then return."],
        "tips": "Keep the knees together to focus motion in the upper back.", "met": 2.0,
    },
    {
        "id": "hamstring_sweep", "name": "Standing Hamstring Sweep", "category": "Flexibility",
        "level": "Beginner", "equipment": "None", "muscles": ["Hamstrings", "Calves"],
        "instructions": ["Extend one heel with toes lifted.", "Hinge slightly and sweep hands toward the toes.", "Stand and switch sides fluidly."],
        "tips": "Keep a soft bend in the supporting knee.", "met": 2.5,
    },
    {
        "id": "hiit_squat_reach", "name": "Squat to Reach", "category": "HIIT",
        "level": "Intermediate", "equipment": "None", "muscles": ["Full body", "Glutes", "Shoulders"],
        "instructions": ["Sit into a controlled squat.", "Stand quickly and reach both hands overhead.", "Repeat with quiet, balanced feet."],
        "tips": "Remove the jump and limit depth for low impact.", "met": 7.5, "rep_mode": "squat",
    },
    {
        "id": "hiit_skater", "name": "Lateral Skater", "category": "HIIT",
        "level": "Advanced", "equipment": "None", "muscles": ["Glutes", "Quadriceps", "Calves"],
        "instructions": ["Push laterally from one leg to the other.", "Land softly with hip and knee aligned.", "Use the arms for balance and rhythm."],
        "tips": "Step side to side rather than jumping.", "met": 9.0,
    },
]


def _catalog() -> list[dict]:
    return deepcopy(EXERCISES)


if st is not None:
    get_exercises = st.cache_data(show_spinner=False)(_catalog)
else:
    get_exercises = _catalog


def get_exercise(exercise_id: str) -> dict | None:
    """Return one exercise by stable identifier."""
    return next((item for item in get_exercises() if item["id"] == exercise_id), None)


def exercise_image(category: str) -> str:
    """Return a local category illustration path."""
    return str(ASSET_DIR / f"{category.lower()}.svg")
