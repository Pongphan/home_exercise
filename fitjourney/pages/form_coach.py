"""Live webcam form feedback page."""

from __future__ import annotations

import streamlit as st

from ..cv_engine import PoseProcessor
from ..styles import hero
from .common import safety_note


LABELS = {"squat": "Bodyweight squat", "pushup": "Push-up", "curl": "Biceps curl"}


def render() -> None:
    hero("A form coach in your browser.", "Private, real-time joint tracking with rep counting and simple movement cues.", "CAMERA COACH · BETA")
    safety_note()
    st.caption("Video is processed in the live app session and is not saved by FitJourney.")
    mode = st.segmented_control("Movement", list(LABELS), format_func=lambda x: LABELS[x], default="squat")
    try:
        from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer
    except ImportError:
        st.error("Camera dependencies are not installed. Install the full requirements file and restart the app.")
        return
    left, right = st.columns([2, 1])
    with left:
        ctx = webrtc_streamer(
            key=f"pose-{mode}", mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
            video_processor_factory=lambda: PoseProcessor(mode), async_processing=True,
        )
    with right:
        st.markdown("### Camera setup")
        st.write("Place the camera side-on, 2–3 m away. Keep your full body visible in even light.")
        st.write("Move smoothly through a clear range. The counter uses joint-angle thresholds and can miss partial or obscured reps.")
        if ctx.state.playing:
            st.success("Pose tracking is active.")
        else:
            st.info("Press START and allow camera access.")
        st.markdown("### Counting logic")
        if mode == "squat":
            st.write("Counts after the knee closes below ~95° and returns above ~155°.")
        elif mode == "pushup":
            st.write("Counts after the elbow closes below ~90° and returns above ~150°.")
        else:
            st.write("Counts after the elbow extends past ~145° and curls below ~60°.")
