"""Searchable exercise library."""

from __future__ import annotations

import streamlit as st

from ..exercises import exercise_image, get_exercises
from ..styles import hero


def render() -> None:
    hero("Movement, made clear.", "Filter by training style, equipment, or muscle. Open any card for precise setup and cues.", "EXERCISE LIBRARY")
    exercises = get_exercises()
    f1, f2, f3 = st.columns([1, 1, 1.2])
    with f1:
        category = st.selectbox("Category", ["All", "Strength", "Cardio", "Flexibility", "HIIT"])
    with f2:
        equipment = st.selectbox("Equipment", ["All"] + sorted({x["equipment"] for x in exercises}))
    with f3:
        search = st.text_input("Search exercise or muscle", placeholder="Try glutes, core, push-up…")

    filtered = []
    for item in exercises:
        haystack = " ".join([item["name"], *item["muscles"]]).lower()
        if category != "All" and item["category"] != category:
            continue
        if equipment != "All" and item["equipment"] != equipment:
            continue
        if search and search.lower() not in haystack:
            continue
        filtered.append(item)
    st.caption(f"{len(filtered)} movements")

    for index in range(0, len(filtered), 2):
        columns = st.columns(2)
        for column, item in zip(columns, filtered[index:index + 2]):
            with column:
                st.image(exercise_image(item["category"]), use_container_width=True)
                st.markdown(f"### {item['name']}")
                st.caption(f"{item['category']} · {item['level']} · {item['equipment']}")
                st.markdown(" ".join(f'<span class="pill">{m}</span>' for m in item["muscles"]), unsafe_allow_html=True)
                with st.expander("How to perform"):
                    for step, instruction in enumerate(item["instructions"], 1):
                        st.markdown(f"**{step}.** {instruction}")
                    st.info(item["tips"], icon="💡")
