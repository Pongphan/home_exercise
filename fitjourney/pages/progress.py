"""Progress dashboard and report downloads."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from .. import db
from ..analytics import calculate_streak, session_frame, volume_frame
from ..reports import progress_pdf, sessions_csv
from ..styles import hero, metric_card
from .common import user_id


def render() -> None:
    hero("Proof of consistency.", "See the work accumulate: sessions, volume, effort, energy, and the streak you are building.", "PROGRESS")
    sessions = db.get_sessions(user_id())
    logs = db.get_session_logs(user_id())
    streak = calculate_streak(sessions)
    cols = st.columns(4)
    metrics = [
        ("Sessions", str(len(sessions)), "all time"),
        ("Current streak", f"{streak} days", "today or yesterday"),
        ("Training volume", f"{sum(x['volume'] for x in logs):,.0f}", "kg-reps / bodyweight reps"),
        ("Estimated burn", f"{sum(x['calories'] for x in sessions):,.0f}", "kcal"),
    ]
    for col, metric in zip(cols, metrics):
        with col:
            metric_card(*metric)
    if not sessions:
        st.info("Finish your first guided session to unlock trends and reports.")
        return

    session_df = session_frame(sessions)
    volume_df = volume_frame(logs)
    left, right = st.columns(2)
    with left:
        fig = px.bar(session_df, x="date", y="duration_minutes", color="rpe",
                     color_continuous_scale=["#d9f36a", "#ff8066"], title="Active minutes & effort")
        fig.update_layout(coloraxis_colorbar_title="RPE", margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.line(volume_df, x="date", y="volume", markers=True, title="Training volume trend")
        fig.update_traces(line_color="#14332b", marker_color="#ff8066", line_width=3)
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    fig = px.area(session_df, x="date", y="calories", title="Estimated calorie burn")
    fig.update_traces(line_color="#2d8068", fillcolor="rgba(217,243,106,.35)")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Export your history")
    c1, c2 = st.columns(2)
    c1.download_button("Download CSV", sessions_csv(sessions), "fitjourney_history.csv", "text/csv",
                       use_container_width=True)
    try:
        pdf = progress_pdf(st.session_state["user"]["display_name"], sessions, streak)
        c2.download_button("Download PDF report", pdf, "fitjourney_progress.pdf", "application/pdf",
                           use_container_width=True)
    except ImportError:
        c2.info("Install ReportLab to enable PDF export.")
