"""Wearable/manual biometric inputs and account controls."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import db
from ..styles import hero
from .common import user_id


def render() -> None:
    hero("Signals & preferences", "Add optional heart-rate context and manage this local account.", "SETTINGS")
    st.subheader("Heart rate")
    st.write("Manual entry works with any wearable. It is optional and does not alter medical or safety guidance.")
    with st.form("heart_rate"):
        c1, c2 = st.columns(2)
        bpm = c1.number_input("Heart rate (bpm)", 30, 240, 70)
        context = c2.selectbox("Context", ["Resting", "Pre-workout", "During workout", "Post-workout", "Manual"])
        save = st.form_submit_button("Save reading", type="primary")
    if save:
        db.save_heart_rate(user_id(), bpm, context)
        st.success("Heart-rate reading saved.")
    readings = db.get_heart_rates(user_id())
    if readings:
        frame = pd.DataFrame(readings)
        frame["measured_at"] = pd.to_datetime(frame["measured_at"], utc=True).dt.tz_convert(None)
        st.line_chart(frame.set_index("measured_at")["bpm"], color="#ff8066")
        st.dataframe(frame[["measured_at", "bpm", "context"]], hide_index=True, use_container_width=True)
    with st.expander("Google Fit integration"):
        st.info("Connector-ready extension point: configure OAuth and replace manual imports with the Google Fit REST API. No health data is sent anywhere in this local build.")
