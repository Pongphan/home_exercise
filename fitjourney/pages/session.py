"""Guided workout logging with browser-side timers."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

from .. import db
from ..analytics import estimate_calories
from ..exercises import get_exercise
from ..styles import hero
from .common import profile_or_prompt, user_id


def timer_widget(rest_seconds: int) -> None:
    """Self-contained JavaScript stopwatch and audible rest countdown."""
    components.html(
        f"""
        <style>
        body{{font-family:Arial,sans-serif;margin:0;color:#14332b}} .timer{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;
        background:#fff;border:1px solid #dce7e1;border-radius:16px;padding:14px}} #clock{{font-size:30px;font-weight:800;min-width:108px}}
        button{{border:0;border-radius:9px;padding:9px 14px;background:#14332b;color:white;font-weight:700;cursor:pointer}}
        button.alt{{background:#edf3ef;color:#14332b}}
        </style><div class="timer"><div><small>SESSION TIMER</small><div id="clock">00:00</div></div>
        <button onclick="toggle()" id="start">Start</button><button class="alt" onclick="resetClock()">Reset</button>
        <div><small>REST</small><div id="rest">{rest_seconds}s</div></div>
        <button onclick="startRest()">Start rest</button></div>
        <script>
        let elapsed=0,running=false,tick=null,remaining={rest_seconds},restTick=null;
        const fmt=s=>String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
        function toggle(){{running=!running;document.getElementById('start').innerText=running?'Pause':'Start';
          if(running)tick=setInterval(()=>{{elapsed++;document.getElementById('clock').innerText=fmt(elapsed)}},1000);else clearInterval(tick)}}
        function resetClock(){{running=false;clearInterval(tick);elapsed=0;document.getElementById('clock').innerText='00:00';document.getElementById('start').innerText='Start'}}
        function startRest(){{clearInterval(restTick);remaining={rest_seconds};document.getElementById('rest').innerText=remaining+'s';
          restTick=setInterval(()=>{{remaining--;document.getElementById('rest').innerText=remaining+'s';if(remaining<=0){{clearInterval(restTick);
          document.getElementById('rest').innerText='GO!';try{{new AudioContext().createOscillator()}}catch(e){{}};alert('Rest complete — ready for the next set!')}}}},1000)}}
        </script>""", height=115,
    )


def render() -> None:
    hero("Today’s work, one set at a time.", "Use the timer, log honest reps, and finish with an effort score so tomorrow can adapt.", "GUIDED SESSION")
    profile = profile_or_prompt()
    if not profile:
        return
    plan = db.get_active_plan(user_id())
    if not plan:
        st.warning("Generate a workout plan before starting a guided session.")
        return
    day_index = st.selectbox("Workout day", range(len(plan["days"])), format_func=lambda x: f"Day {x + 1}")
    items = plan["days"][day_index]
    if "session_started_at" not in st.session_state:
        st.session_state["session_started_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    timer_widget(max((item["rest_sec"] for item in items), default=45))

    with st.form(f"workout_{plan['id']}_{day_index}"):
        logs = []
        for index, item in enumerate(items):
            exercise = get_exercise(item["exercise_id"])
            if not exercise:
                continue
            st.markdown(f"### {index + 1:02d} · {exercise['name']}")
            target = (f"{item['sets']} × {item['reps']} reps" if item["reps"]
                      else f"{item['sets']} × {item['duration_sec']} sec")
            st.caption(f"Target: {target} · Rest {item['rest_sec']} sec · {', '.join(exercise['muscles'])}")
            a, b, c, d = st.columns([1, 1, 1, .8])
            sets = a.number_input("Sets done", 0, 10, item["sets"], key=f"sets_{item['id']}")
            reps = b.number_input("Reps / set", 0, 100, item["reps"], key=f"reps_{item['id']}",
                                  disabled=not bool(item["reps"]))
            weight = c.number_input("Load (kg)", 0.0, 250.0, 0.0, .5, key=f"weight_{item['id']}")
            complete = d.checkbox("Done", value=False, key=f"done_{item['id']}")
            logs.append({"exercise_id": item["exercise_id"], "sets_completed": sets if complete else 0,
                         "reps_completed": reps if complete else 0, "weight_kg": weight,
                         "duration_sec": item["duration_sec"] * sets if complete else 0,
                         "volume": sets * reps * max(weight, 1) if complete else 0,
                         "met": exercise["met"], "complete": complete})
        st.divider()
        duration = st.number_input("Total active minutes", 1, 240, plan["minutes"])
        rpe = st.slider("Session effort (RPE)", 1, 10, 6, help="1 = very easy; 10 = maximal effort")
        notes = st.text_area("Session notes", placeholder="What felt strong? What should change next time?")
        save = st.form_submit_button("Finish and save workout", type="primary", use_container_width=True)
    if save:
        done = sum(x["complete"] for x in logs)
        completion = done / len(logs) if logs else 0
        calories = estimate_calories(float(profile.get("weight_kg") or 70), duration,
                                     [x["met"] for x in logs if x["complete"]])
        db.save_session(user_id(), {
            "plan_id": plan["id"], "started_at": st.session_state.pop("session_started_at", None),
            "duration_minutes": duration, "completion_rate": completion, "rpe": rpe,
            "calories": calories, "notes": notes.strip(),
        }, logs)
        st.success(f"Workout saved — {completion:.0%} complete and about {calories:.0f} kcal.")
        st.balloons()
