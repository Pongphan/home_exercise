"""Common page helpers."""

from __future__ import annotations

import streamlit as st

from .. import db


def user_id() -> int:
    return int(st.session_state["user"]["id"])


def profile_or_prompt() -> dict | None:
    profile = db.get_profile(user_id())
    if not profile:
        st.warning("Complete onboarding first so recommendations match your goals and equipment.")
        st.caption("Open Training profile from the sidebar to continue.")
    return profile


def safety_note() -> None:
    st.markdown(
        '<div class="safety"><strong>Train safely.</strong> This app provides general fitness guidance, not medical care. '
        'Use pain-free movement, stop for dizziness, chest pain, or unusual shortness of breath, and consult a qualified '
        'professional about injuries or health conditions.</div>', unsafe_allow_html=True,
    )
