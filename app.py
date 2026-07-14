"""FitJourney Streamlit entry point."""

from __future__ import annotations

import sqlite3

import streamlit as st

from fitjourney import db
from fitjourney.auth import hash_password, verify_password
from fitjourney.pages import form_coach, home, library, onboarding, plan, progress, session, settings
from fitjourney.styles import inject_styles


st.set_page_config(
    page_title="FitJourney · Home training",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource(show_spinner=False)
def bootstrap_database(database_path: str) -> str:
    """Run idempotent migrations once per app process."""
    db.init_db()
    return database_path


bootstrap_database(str(db.db_path()))
inject_styles()


def auth_screen() -> None:
    st.markdown(
        '<section class="hero"><div class="eyebrow">FITJOURNEY</div><h1>Your strongest habit starts at home.</h1>'
        '<p>Personal plans, guided sessions, clear progress, and private camera-based form feedback.</p></section>',
        unsafe_allow_html=True,
    )
    login_tab, register_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            user = db.get_user(username)
            if user and verify_password(password, user["password_hash"]):
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Username or password is incorrect.")
    with register_tab:
        with st.form("register_form"):
            display = st.text_input("Display name")
            username_new = st.text_input("Choose a username", autocomplete="username")
            password_new = st.text_input("Choose a password", type="password", autocomplete="new-password",
                                         help="Use at least 8 characters.")
            confirm = st.text_input("Confirm password", type="password", autocomplete="new-password")
            create = st.form_submit_button("Create local account", type="primary", use_container_width=True)
        if create:
            if len(username_new.strip()) < 3 or not username_new.replace("_", "").isalnum():
                st.error("Use at least 3 letters/numbers; underscores are allowed.")
            elif not display.strip():
                st.error("Enter a display name.")
            elif len(password_new) < 8:
                st.error("Password must contain at least 8 characters.")
            elif password_new != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    uid = db.create_user(username_new, display, hash_password(password_new))
                    st.session_state["user"] = db.get_user(username_new) | {"id": uid}
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That username is already in use.")


if "user" not in st.session_state:
    auth_screen()
    st.stop()

with st.sidebar:
    st.markdown("## FITJOURNEY")
    st.caption(f"Signed in as {st.session_state['user']['display_name']}")
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

navigation = st.navigation({
    "TODAY": [st.Page(home.render, title="Overview", url_path="overview", default=True)],
    "TRAIN": [
        st.Page(plan.render, title="My plan", url_path="plan"),
        st.Page(session.render, title="Guided session", url_path="session"),
        st.Page(form_coach.render, title="Camera coach", url_path="camera-coach"),
    ],
    "DISCOVER": [
        st.Page(library.render, title="Exercise library", url_path="exercise-library"),
        st.Page(progress.render, title="Progress", url_path="progress"),
    ],
    "YOU": [
        st.Page(onboarding.render, title="Training profile", url_path="profile"),
        st.Page(settings.render, title="Settings & heart rate", url_path="settings"),
    ],
})
navigation.run()
