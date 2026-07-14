"""Workout statistics and chart-ready transformations."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd


def session_frame(sessions: list[dict]) -> pd.DataFrame:
    if not sessions:
        return pd.DataFrame(columns=["date", "duration_minutes", "completion_rate", "rpe", "calories"])
    frame = pd.DataFrame(sessions)
    frame["date"] = pd.to_datetime(frame["completed_at"], utc=True).dt.tz_convert(None)
    return frame.sort_values("date")


def volume_frame(logs: list[dict]) -> pd.DataFrame:
    if not logs:
        return pd.DataFrame(columns=["date", "volume"])
    frame = pd.DataFrame(logs)
    frame["date"] = pd.to_datetime(frame["completed_at"], utc=True).dt.tz_convert(None).dt.date
    return frame.groupby("date", as_index=False)["volume"].sum()


def calculate_streak(sessions: list[dict], today: date | None = None) -> int:
    """Count consecutive calendar days, allowing today or yesterday as the last day."""
    if not sessions:
        return 0
    today = today or date.today()
    completed = sorted({datetime.fromisoformat(s["completed_at"].replace("Z", "+00:00")).date() for s in sessions}, reverse=True)
    if completed[0] not in {today, today - timedelta(days=1)}:
        return 0
    streak = 1
    for previous, current in zip(completed, completed[1:]):
        if previous - current == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def estimate_calories(weight_kg: float, minutes: float, mets: list[float]) -> float:
    """Estimate energy using MET × 3.5 × kg / 200 × minutes."""
    met = sum(mets) / len(mets) if mets else 4.0
    return round(met * 3.5 * max(weight_kg, 35) / 200 * minutes, 1)
