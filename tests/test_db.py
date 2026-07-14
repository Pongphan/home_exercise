from fitjourney import db
from fitjourney.auth import hash_password


def test_profile_plan_and_session_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("FITJOURNEY_DB", str(tmp_path / "test.db"))
    db.init_db()
    user_id = db.create_user("alex", "Alex", hash_password("very-secret"))
    db.save_profile(user_id, {
        "fitness_level": "Beginner", "goals": ["Strength"], "equipment": ["None"],
        "limitations": "", "age": 30, "weight_kg": 70, "weekly_days": 2, "session_minutes": 20,
    })
    assert db.get_profile(user_id)["goals"] == ["Strength"]
    plan_id = db.save_plan(user_id, {
        "title": "Test plan", "difficulty": "Beginner", "minutes": 20,
        "days": [[{"exercise_id": "bodyweight_squat", "sets": 2, "reps": 10,
                   "duration_sec": 0, "rest_sec": 45}]],
    })
    assert db.get_active_plan(user_id)["id"] == plan_id
    db.save_session(user_id, {
        "plan_id": plan_id, "duration_minutes": 20, "completion_rate": 1.0,
        "rpe": 6, "calories": 100, "notes": "Good",
    }, [{"exercise_id": "bodyweight_squat", "sets_completed": 2, "reps_completed": 10,
         "weight_kg": 0, "duration_sec": 0, "volume": 20}])
    assert len(db.get_sessions(user_id)) == 1
    assert db.get_session_logs(user_id)[0]["volume"] == 20
