"""Profile onboarding and editing."""

from __future__ import annotations

import streamlit as st

from .. import db
from ..styles import hero
from .common import user_id


GOALS = ["Weight loss", "Strength", "Mobility", "General fitness"]
EQUIPMENT = ["None", "Mat", "Chair", "Dumbbells", "Resistance band"]


def render() -> None:
    hero("Build your training profile", "A few details make every routine safer, more realistic, and more personal.", "ONBOARDING")
    old = db.get_profile(user_id()) or {}
    with st.form("profile_form"):
        st.subheader("Training context")
        c1, c2 = st.columns(2)
        with c1:
            level = st.select_slider(
                "Current fitness level", ["Beginner", "Intermediate", "Advanced"],
                value=old.get("fitness_level", "Beginner"),
            )
            goals = st.multiselect("Primary goals", GOALS, default=old.get("goals", ["General fitness"]))
            equipment = st.multiselect(
                "Equipment available", EQUIPMENT,
                default=old.get("equipment", ["None", "Mat"]),
                help="Choose None as well as any simple home equipment you have.",
            )
        with c2:
            age = st.number_input("Age (optional)", 13, 100, old.get("age") or 30)
            weight = st.number_input("Body weight in kg (for calorie estimates)", 35.0, 250.0,
                                     float(old.get("weight_kg") or 70), step=0.5)
            days = st.slider("Training days each week", 2, 6, int(old.get("weekly_days", 3)))
            minutes = st.select_slider("Minutes per session", [15, 20, 30, 40, 45, 60],
                                       value=int(old.get("session_minutes", 30)))
        limitations = st.text_area(
            "Physical limitations, injuries, or movements to avoid",
            value=old.get("limitations", ""),
            placeholder="Example: recovering right knee; avoid jumping. Share only what is useful for exercise selection.",
        )
        consent = st.checkbox("I understand this is general exercise guidance and will work within a pain-free range.")
        submitted = st.form_submit_button("Save training profile", type="primary", use_container_width=True)
    if submitted:
        if not goals or not equipment:
            st.error("Choose at least one goal and one equipment option.")
        elif not consent:
            st.error("Please acknowledge the safety note before saving.")
        else:
            db.save_profile(user_id(), {
                "fitness_level": level, "goals": goals, "equipment": equipment,
                "limitations": limitations.strip(), "age": age, "weight_kg": weight,
                "weekly_days": days, "session_minutes": minutes,
            })
            st.success("Profile saved. Your next generated plan will use these preferences.")
            st.balloons()
