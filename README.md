# FitJourney

FitJourney is a deployment-ready, multi-user Streamlit app for guided home training. It combines personalized workout planning, set/rep and interval tracking, adaptive difficulty, persistent progress analytics, exports, manual wearable context, and an optional MediaPipe camera coach.

> FitJourney provides general exercise guidance, not diagnosis or medical treatment. Users should work in a pain-free range and consult a qualified professional about health conditions or injuries.

## What is included

- Secure local accounts using salted PBKDF2-SHA256 hashes (no plaintext passwords)
- Onboarding for level, goals, equipment, time, weight, and physical limitations
- Cached illustrated library spanning strength, cardio, flexibility, and HIIT
- Equipment-aware plan generator with simple injury keyword exclusions
- Adaptation from the last five sessions' completion rate and RPE
- Guided workout log with a stopwatch, rep/set fields, rest countdown, and alert
- SQLite persistence with per-user plans, sessions, exercise logs, and heart rate
- Plotly history, volume, effort, calorie, and streak dashboard
- CSV history and a branded PDF report
- Browser webcam pose tracking for squats, push-ups, and curls
- Hysteresis-based rep counting from knee/elbow angles
- Responsive theme, Docker image, Streamlit Cloud configuration, and tests

## Architecture

```text
home_exercise/
├── app.py                         # authentication + st.navigation shell
├── fitjourney/
│   ├── auth.py                    # PBKDF2 password hashing
│   ├── db.py                      # SQLite schema and repositories
│   ├── exercises.py               # cached built-in catalog
│   ├── planner.py                 # generation + adaptive workload rules
│   ├── analytics.py               # streak, MET, and chart transforms
│   ├── reports.py                 # CSV/PDF exports
│   ├── cv_engine.py               # pose processor + rep state machine
│   ├── styles.py                  # responsive design system
│   └── pages/                     # callable Streamlit page modules
├── assets/                        # local SVG instruction-category artwork
├── data/                          # runtime SQLite database (git-ignored)
├── tests/                         # core, database, planning, and CV tests
├── .streamlit/config.toml
├── requirements.txt               # full build, including camera coach
├── requirements-core.txt          # lighter camera-free build
└── Dockerfile
```

## Local run

Python 3.11 is recommended because it has broad MediaPipe/OpenCV wheel support.

```bash
cd home_exercise
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` is the camera-free core build used by Streamlit Community Cloud. To enable the webcam coach locally, install `pip install -r requirements-camera.txt` instead. The Docker image also uses the full camera build.

The database is created at `data/fitjourney.db`. Set `FITJOURNEY_DB=/persistent/path/app.db` to place it on a mounted volume. SQLite is suitable for a small single-instance deployment. For horizontally scaled production, replace `fitjourney/db.py` with a Supabase/Postgres repository while preserving its function interface.

## Docker

```bash
cd home_exercise
docker build -t fitjourney .
docker run --rm -p 8501:8501 -v fitjourney-data:/app/data fitjourney
```

Open <http://localhost:8501>. Camera access requires a secure context in production (HTTPS; localhost is allowed by browsers).

## Streamlit Community Cloud

1. Push this folder to a repository.
2. Create an app with `home_exercise/app.py` as the entry point.
3. Community Cloud discovers the lightweight `home_exercise/requirements.txt` beside the entrypoint. It intentionally omits native camera packages so the core tracker can install reliably.
4. Python 3.12 is recommended, though the core build does not depend on the legacy MediaPipe wheel.
5. Remember that Community Cloud's local filesystem is ephemeral. Attach an external database for durable history across app reboots.
6. The camera coach remains available in the Docker/local full build. WebRTC deployments may additionally require a TURN server; configure credentials as secrets rather than source code.

## Tests

```bash
pip install pytest
pytest -q
```

Tests cover authentication, personalization constraints, adaptive difficulty, streak/MET calculations, CV joint angles and rep cycles, plus SQLite round trips.

## Camera-coach limitations

The live coach processes frames in memory and does not save video. It is a fitness cueing aid, not a medical or biomechanical assessment. Counts depend on camera position, visibility, lighting, clothing, and range of motion. The side-on setup described in the UI gives the most reliable joint angles.

The camera engine currently uses MediaPipe's legacy `mp.solutions.pose` API. `requirements.txt` intentionally constrains MediaPipe below `0.10.30`, the release line that removed that API. Keep this constraint unless `cv_engine.py` is migrated to the Tasks Pose Landmarker API and supplied with a compatible model bundle.

## Optional Google Fit extension

The settings page intentionally begins with portable manual heart-rate entry. A production Google Fit adapter should use OAuth, server-side token storage, minimal scopes, explicit consent, and deletion/export controls. Keep provider code behind the same `save_heart_rate` interface so the dashboard remains unchanged.
