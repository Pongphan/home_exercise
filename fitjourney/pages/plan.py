"""Personalized workout-plan page."""

from __future__ import annotations

import streamlit as st

from .. import db
from ..exercises import get_exercise
from ..planner import generate_plan
from ..styles import hero
from .common import profile_or_prompt, user_id


def _show_plan(plan: dict) -> None:
    st.markdown(f"## {plan['title']}")
    st.caption(f"{plan['difficulty']} · {plan.get('minutes', 30)} minutes · {len(plan['days'])} days/week")
    if plan.get("adaptation"):
        adjustment = plan["adaptation"]
        st.info(f"Adaptive mode: **{adjustment['label']}** — {adjustment['reason']}")
    tabs = st.tabs([f"Day {i}" for i in range(1, len(plan["days"]) + 1)])
    for tab, day in zip(tabs, plan["days"]):
        with tab:
            for position, item in enumerate(day, 1):
                exercise = get_exercise(item["exercise_id"])
                if not exercise:
                    continue
                prescription = (f"{item['sets']} sets × {item['reps']} reps" if item.get("reps")
                                else f"{item['sets']} rounds × {item.get('duration_sec', 30)} sec")
                st.markdown(f"**{position:02d}  {exercise['name']}**  ·  {prescription}  ·  rest {item['rest_sec']} sec")
                st.caption(" · ".join(exercise["muscles"]))


def render() -> None:
    hero("A plan that meets you here.", "Generated around your time, equipment, goals, recent completion, and perceived effort.", "SMART PLANNER")
    profile = profile_or_prompt()
    if not profile:
        return
    current = db.get_active_plan(user_id())
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write(f"**Goal:** {', '.join(profile['goals'])}  ·  **Equipment:** {', '.join(profile['equipment'])}")
        st.caption(f"{profile['weekly_days']} days/week · {profile['session_minutes']} minutes · {profile['fitness_level']}")
    with c2:
        generate = st.button("Generate a fresh plan", type="primary", use_container_width=True)
    if generate:
        plan = generate_plan(profile, db.recent_adherence(user_id()))
        db.save_plan(user_id(), plan)
        st.session_state["new_plan"] = plan
        st.success("Your new plan is active.")
        current = db.get_active_plan(user_id())
    if current:
        _show_plan(current)
    else:
        st.info("No active plan yet. Generate one to begin.")
