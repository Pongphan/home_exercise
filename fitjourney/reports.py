"""CSV and compact PDF report generation."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def sessions_csv(sessions: list[dict]) -> bytes:
    columns = ["completed_at", "duration_minutes", "completion_rate", "rpe", "calories", "notes"]
    frame = pd.DataFrame(sessions)
    if frame.empty:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = frame[[c for c in columns if c in frame.columns]]
        if "completion_rate" in frame:
            frame["completion_rate"] = (frame["completion_rate"] * 100).round(0).astype(str) + "%"
    return frame.to_csv(index=False).encode("utf-8")


def progress_pdf(display_name: str, sessions: list[dict], streak: int) -> bytes:
    """Return a simple branded PDF; ReportLab is imported lazily."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("FitJourney Progress Report", styles["Title"]),
             Paragraph(f"Athlete: {display_name}", styles["Heading2"]), Spacer(1, 8)]
    total_minutes = sum(float(s["duration_minutes"]) for s in sessions)
    calories = sum(float(s["calories"]) for s in sessions)
    story.append(Paragraph(
        f"{len(sessions)} sessions · {total_minutes:.0f} active minutes · "
        f"{calories:.0f} estimated kcal · {streak}-day current streak", styles["BodyText"]
    ))
    story.append(Spacer(1, 14))
    data = [["Date", "Minutes", "Complete", "RPE", "Est. kcal"]]
    for item in sessions[:30]:
        data.append([item["completed_at"][:10], f'{item["duration_minutes"]:.0f}',
                     f'{item["completion_rate"] * 100:.0f}%', str(item["rpe"]), f'{item["calories"]:.0f}'])
    if len(data) == 1:
        data.append(["No workouts logged yet", "—", "—", "—", "—"])
    table = Table(data, repeatRows=1, colWidths=[42 * mm, 27 * mm, 32 * mm, 22 * mm, 28 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14332B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CED9D4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F2")]),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([table, Spacer(1, 16), Paragraph(
        "Calorie values are estimates. Stop exercise and seek qualified care for concerning symptoms.",
        styles["Italic"],
    )])
    doc.build(story)
    return output.getvalue()
