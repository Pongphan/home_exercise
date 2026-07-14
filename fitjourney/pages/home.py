"""Overview page."""

from __future__ import annotations

import streamlit as st

from .. import db
from ..analytics import calculate_streak
from ..styles import hero, metric_card
from .common import safety_note, user_id


def render() -> None:
    user = st.session_state["user"]
    profile = db.get_profile(user_id())
    sessions = db.get_sessions(user_id())
    hero(
        f"Move well, {user['display_name'].split()[0]}.",
        "A thoughtful workout for today, clear form cues, and progress that compounds.",
        "YOUR TRAINING SPACE",
    )

    cols = st.columns(4)
    values = [
        ("Current streak", f"{calculate_streak(sessions)} days", "Keep the rhythm"),
        ("Sessions", str(len(sessions)), "All time"),
        ("Active minutes", f"{sum(s['duration_minutes'] for s in sessions):.0f}", "All time"),
        ("Est. energy", f"{sum(s['calories'] for s in sessions):.0f} kcal", "All time"),
    ]
    for column, item in zip(cols, values):
        with column:
            metric_card(*item)

    st.subheader("Your next move")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 01 · Personalize")
        st.write("Tell FitJourney what you want, what you have, and what needs extra care.")
        st.caption("Complete" if profile else "Needs attention")
    with c2:
        st.markdown("### 02 · Build")
        st.write("Generate a balanced plan that fits your week and adapts to your effort.")
        plan = db.get_active_plan(user_id())
        st.caption(plan["title"] if plan else "No active plan")
    with c3:
        st.markdown("### 03 · Train")
        st.write("Track sets, reps, timed intervals, effort, and recovery in one place.")
        st.caption("Ready when you are")

    st.divider()
    safety_note()
