"""Streamlit startup and callable-page smoke tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from fitjourney import db
from fitjourney.auth import hash_password
from fitjourney.planner import generate_plan


PAGE_MODULES = [
    "fitjourney.pages.home",
    "fitjourney.pages.onboarding",
    "fitjourney.pages.library",
    "fitjourney.pages.plan",
    "fitjourney.pages.session",
    "fitjourney.pages.progress",
    "fitjourney.pages.form_coach",
    "fitjourney.pages.settings",
]


@pytest.fixture()
def test_user(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setenv("FITJOURNEY_DB", str(tmp_path / "streamlit.db"))
    db.init_db()
    user_id = db.create_user("smoke_user", "Smoke User", hash_password("strong-pass-123"))
    profile = {
        "fitness_level": "Beginner", "goals": ["Strength"],
        "equipment": ["None", "Mat", "Chair"], "limitations": "",
        "age": 30, "weight_kg": 70, "weekly_days": 3, "session_minutes": 30,
    }
    db.save_profile(user_id, profile)
    db.save_plan(user_id, generate_plan(profile))
    return {"id": user_id, "username": "smoke_user", "display_name": "Smoke User"}


def test_entrypoint_has_no_duplicate_page_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FITJOURNEY_DB", str(tmp_path / "entrypoint.db"))
    app = AppTest.from_file("app.py", default_timeout=20).run()
    assert not app.exception
    assert [button.label for button in app.button] == ["Sign in", "Create local account"]


def test_registration_reaches_authenticated_overview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FITJOURNEY_DB", str(tmp_path / "registration.db"))
    app = AppTest.from_file("app.py", default_timeout=20).run()
    values = {
        "Display name": "New Athlete", "Choose a username": "new_athlete",
        "Choose a password": "strong-pass-123", "Confirm password": "strong-pass-123",
    }
    for widget in app.text_input:
        if widget.label in values:
            widget.set_value(values[widget.label])
    next(button for button in app.button if button.label == "Create local account").click()
    app.run()
    assert not app.exception
    assert app.session_state["user"]["username"] == "new_athlete"
    assert [button.label for button in app.button] == ["Sign out"]


@pytest.mark.parametrize("module_name", PAGE_MODULES)
def test_authenticated_page_renders(
    module_name: str, test_user: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FITJOURNEY_TEST_PAGE", module_name)
    if module_name == "fitjourney.pages.form_coach":
        # streamlit-webrtc requires a live browser session manager, which
        # Streamlit's AppTest mock runtime intentionally does not provide.
        import streamlit_webrtc

        monkeypatch.setattr(
            streamlit_webrtc,
            "webrtc_streamer",
            lambda **_kwargs: SimpleNamespace(state=SimpleNamespace(playing=False)),
        )
    page = AppTest.from_file("tests/page_harness.py", default_timeout=20)
    page.session_state["user"] = test_user
    page.run()
    assert not page.exception


def test_plan_session_progress_workflow(test_user: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FITJOURNEY_TEST_PAGE", "fitjourney.pages.plan")
    planner = AppTest.from_file("tests/page_harness.py", default_timeout=20)
    planner.session_state["user"] = test_user
    planner.run()
    next(button for button in planner.button if button.label == "Generate a fresh plan").click()
    planner.run()
    assert not planner.exception

    monkeypatch.setenv("FITJOURNEY_TEST_PAGE", "fitjourney.pages.session")
    workout = AppTest.from_file("tests/page_harness.py", default_timeout=20)
    workout.session_state["user"] = test_user
    workout.run()
    for checkbox in workout.checkbox:
        checkbox.set_value(True)
    next(button for button in workout.button if button.label == "Finish and save workout").click()
    workout.run()
    assert not workout.exception
    assert len(db.get_sessions(test_user["id"])) == 1

    monkeypatch.setenv("FITJOURNEY_TEST_PAGE", "fitjourney.pages.progress")
    dashboard = AppTest.from_file("tests/page_harness.py", default_timeout=20)
    dashboard.session_state["user"] = test_user
    dashboard.run()
    assert not dashboard.exception
    assert len(dashboard.get("plotly_chart")) == 3
