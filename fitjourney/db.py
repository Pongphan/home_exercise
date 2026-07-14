"""SQLite persistence layer for profiles, plans, and workout history."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = APP_DIR / "data" / "fitjourney.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path() -> Path:
    path = Path(os.environ.get("FITJOURNEY_DB", DEFAULT_DB))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path(), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create or migrate the local database idempotently."""
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                fitness_level TEXT NOT NULL,
                goals_json TEXT NOT NULL,
                equipment_json TEXT NOT NULL,
                limitations TEXT NOT NULL DEFAULT '',
                age INTEGER,
                weight_kg REAL,
                weekly_days INTEGER NOT NULL DEFAULT 3,
                session_minutes INTEGER NOT NULL DEFAULT 30,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                days_per_week INTEGER NOT NULL,
                minutes INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS plan_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
                day_no INTEGER NOT NULL,
                position INTEGER NOT NULL,
                exercise_id TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                duration_sec INTEGER NOT NULL DEFAULT 0,
                rest_sec INTEGER NOT NULL DEFAULT 45
            );
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                plan_id INTEGER REFERENCES plans(id) ON DELETE SET NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                duration_minutes REAL NOT NULL,
                completion_rate REAL NOT NULL,
                rpe INTEGER NOT NULL,
                calories REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
                exercise_id TEXT NOT NULL,
                sets_completed INTEGER NOT NULL,
                reps_completed INTEGER NOT NULL,
                weight_kg REAL NOT NULL DEFAULT 0,
                duration_sec INTEGER NOT NULL DEFAULT 0,
                volume REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS heart_rate_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                measured_at TEXT NOT NULL,
                bpm INTEGER NOT NULL,
                context TEXT NOT NULL DEFAULT 'Manual'
            );
            """
        )


def row_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def create_user(username: str, display_name: str, password_hash: str) -> int:
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username.strip(), display_name.strip(), password_hash, utc_now()),
        )
        return int(cur.lastrowid)


def get_user(username: str) -> dict | None:
    with connection() as conn:
        return row_dict(conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone())


def get_profile(user_id: int) -> dict | None:
    with connection() as conn:
        profile = row_dict(conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone())
    if profile:
        profile["goals"] = json.loads(profile.pop("goals_json"))
        profile["equipment"] = json.loads(profile.pop("equipment_json"))
    return profile


def save_profile(user_id: int, profile: dict[str, Any]) -> None:
    values = (
        user_id, profile["fitness_level"], json.dumps(profile["goals"]),
        json.dumps(profile["equipment"]), profile.get("limitations", ""),
        profile.get("age"), profile.get("weight_kg"), profile.get("weekly_days", 3),
        profile.get("session_minutes", 30), utc_now(),
    )
    with connection() as conn:
        conn.execute(
            """INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              fitness_level=excluded.fitness_level, goals_json=excluded.goals_json,
              equipment_json=excluded.equipment_json, limitations=excluded.limitations,
              age=excluded.age, weight_kg=excluded.weight_kg,
              weekly_days=excluded.weekly_days, session_minutes=excluded.session_minutes,
              updated_at=excluded.updated_at""",
            values,
        )


def save_plan(user_id: int, plan: dict[str, Any]) -> int:
    with connection() as conn:
        conn.execute("UPDATE plans SET active = 0 WHERE user_id = ?", (user_id,))
        cur = conn.execute(
            "INSERT INTO plans(user_id,title,difficulty,days_per_week,minutes,active,created_at) VALUES (?,?,?,?,?,1,?)",
            (user_id, plan["title"], plan["difficulty"], len(plan["days"]), plan["minutes"], utc_now()),
        )
        plan_id = int(cur.lastrowid)
        for day_no, items in enumerate(plan["days"], start=1):
            conn.executemany(
                """INSERT INTO plan_items(plan_id,day_no,position,exercise_id,sets,reps,duration_sec,rest_sec)
                VALUES (?,?,?,?,?,?,?,?)""",
                [
                    (plan_id, day_no, pos, item["exercise_id"], item["sets"], item["reps"],
                     item.get("duration_sec", 0), item["rest_sec"])
                    for pos, item in enumerate(items, start=1)
                ],
            )
    return plan_id


def get_active_plan(user_id: int) -> dict | None:
    with connection() as conn:
        plan = row_dict(conn.execute(
            "SELECT * FROM plans WHERE user_id=? AND active=1 ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone())
        if not plan:
            return None
        rows = conn.execute("SELECT * FROM plan_items WHERE plan_id=? ORDER BY day_no,position", (plan["id"],)).fetchall()
    plan["days"] = []
    for row in rows:
        while len(plan["days"]) < row["day_no"]:
            plan["days"].append([])
        plan["days"][row["day_no"] - 1].append(dict(row))
    return plan


def save_session(user_id: int, session: dict[str, Any], logs: list[dict[str, Any]]) -> int:
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO workout_sessions
            (user_id,plan_id,started_at,completed_at,duration_minutes,completion_rate,rpe,calories,notes)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, session.get("plan_id"), session.get("started_at", utc_now()), utc_now(),
             session["duration_minutes"], session["completion_rate"], session["rpe"],
             session["calories"], session.get("notes", "")),
        )
        session_id = int(cur.lastrowid)
        conn.executemany(
            """INSERT INTO exercise_logs
            (session_id,exercise_id,sets_completed,reps_completed,weight_kg,duration_sec,volume)
            VALUES (?,?,?,?,?,?,?)""",
            [(session_id, x["exercise_id"], x["sets_completed"], x["reps_completed"],
              x.get("weight_kg", 0), x.get("duration_sec", 0), x.get("volume", 0)) for x in logs],
        )
    return session_id


def get_sessions(user_id: int, limit: int | None = None) -> list[dict]:
    sql = "SELECT * FROM workout_sessions WHERE user_id=? ORDER BY completed_at DESC"
    params: list[Any] = [user_id]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    with connection() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def get_session_logs(user_id: int) -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            """SELECT l.*, s.completed_at FROM exercise_logs l
            JOIN workout_sessions s ON s.id=l.session_id
            WHERE s.user_id=? ORDER BY s.completed_at""", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def recent_adherence(user_id: int, limit: int = 5) -> dict[str, float]:
    sessions = get_sessions(user_id, limit)
    if not sessions:
        return {"completion_rate": 1.0, "rpe": 6.0}
    return {
        "completion_rate": sum(s["completion_rate"] for s in sessions) / len(sessions),
        "rpe": sum(s["rpe"] for s in sessions) / len(sessions),
    }


def save_heart_rate(user_id: int, bpm: int, context: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO heart_rate_logs(user_id,measured_at,bpm,context) VALUES (?,?,?,?)",
            (user_id, utc_now(), bpm, context),
        )


def get_heart_rates(user_id: int, limit: int = 100) -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM heart_rate_logs WHERE user_id=? ORDER BY measured_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
