"""MediaPipe pose processing and exercise-specific repetition state machines."""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass


def calculate_angle(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Return the smaller ABC angle in degrees."""
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(math.degrees(radians))
    return 360 - angle if angle > 180 else angle


@dataclass
class RepCounter:
    """Hysteresis-based counter that avoids double counts around a threshold."""

    mode: str
    reps: int = 0
    stage: str = "ready"

    def update(self, angle: float) -> tuple[int, str]:
        if self.mode in {"squat", "pushup"}:
            down, up = (95, 155) if self.mode == "squat" else (90, 150)
            if angle < down:
                self.stage = "down"
            elif angle > up and self.stage == "down":
                self.reps += 1
                self.stage = "up"
        elif self.mode == "curl":
            if angle > 145:
                self.stage = "down"
            elif angle < 60 and self.stage == "down":
                self.reps += 1
                self.stage = "up"
        return self.reps, self.stage


class PoseProcessor:
    """streamlit-webrtc processor. Heavy dependencies load only when camera starts."""

    def __init__(self, mode: str = "squat") -> None:
        import mediapipe as mp

        if not hasattr(mp, "solutions"):
            raise RuntimeError(
                "This camera coach requires MediaPipe <0.10.30 because it uses the "
                "legacy Solutions Pose API. Reinstall the versions in requirements.txt."
            )
        self.mode = mode
        self.counter = RepCounter(mode)
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.55, min_tracking_confidence=0.55,
            model_complexity=1, smooth_landmarks=True,
        )
        self.drawer = mp.solutions.drawing_utils
        self.connections = mp.solutions.pose.POSE_CONNECTIONS
        self.landmark = mp.solutions.pose.PoseLandmark
        self.lock = threading.Lock()
        self.angle = 0.0
        self.feedback = "Step back until your full body is visible."

    def recv(self, frame):
        import av
        import cv2
        import mediapipe as mp

        image = cv2.flip(frame.to_ndarray(format="bgr24"), 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        feedback = "Keep your full body in frame."
        angle = 0.0
        if result.pose_landmarks:
            points = result.pose_landmarks.landmark
            side = "LEFT" if points[self.landmark.LEFT_SHOULDER].visibility >= points[self.landmark.RIGHT_SHOULDER].visibility else "RIGHT"
            if self.mode == "squat":
                hip = points[getattr(self.landmark, f"{side}_HIP")]
                knee = points[getattr(self.landmark, f"{side}_KNEE")]
                ankle = points[getattr(self.landmark, f"{side}_ANKLE")]
                angle = calculate_angle((hip.x, hip.y), (knee.x, knee.y), (ankle.x, ankle.y))
                feedback = "Good depth — drive through your whole foot." if angle < 100 else "Sit hips back; keep knees tracking over toes."
            elif self.mode == "pushup":
                shoulder = points[getattr(self.landmark, f"{side}_SHOULDER")]
                elbow = points[getattr(self.landmark, f"{side}_ELBOW")]
                wrist = points[getattr(self.landmark, f"{side}_WRIST")]
                hip = points[getattr(self.landmark, f"{side}_HIP")]
                ankle = points[getattr(self.landmark, f"{side}_ANKLE")]
                angle = calculate_angle((shoulder.x, shoulder.y), (elbow.x, elbow.y), (wrist.x, wrist.y))
                body = calculate_angle((shoulder.x, shoulder.y), (hip.x, hip.y), (ankle.x, ankle.y))
                feedback = "Brace and keep shoulders, hips, and heels aligned." if body < 160 else "Strong plank — lower with elbows angled back."
            else:
                shoulder = points[getattr(self.landmark, f"{side}_SHOULDER")]
                elbow = points[getattr(self.landmark, f"{side}_ELBOW")]
                wrist = points[getattr(self.landmark, f"{side}_WRIST")]
                angle = calculate_angle((shoulder.x, shoulder.y), (elbow.x, elbow.y), (wrist.x, wrist.y))
                feedback = "Keep the elbow close to your side; avoid swinging." 
            reps, stage = self.counter.update(angle)
            self.drawer.draw_landmarks(
                image, result.pose_landmarks, self.connections,
                self.drawer.DrawingSpec(color=(100, 243, 217), thickness=2, circle_radius=2),
                self.drawer.DrawingSpec(color=(102, 128, 255), thickness=2),
            )
            with self.lock:
                self.angle, self.feedback = angle, feedback
            cv2.rectangle(image, (15, 15), (245, 105), (20, 51, 43), -1)
            cv2.putText(image, f"REPS  {reps}", (30, 55), cv2.FONT_HERSHEY_SIMPLEX, .8, (106, 243, 217), 2)
            cv2.putText(image, f"ANGLE {angle:.0f}  {stage.upper()}", (30, 88), cv2.FONT_HERSHEY_SIMPLEX, .55, (255, 255, 255), 1)
            cue = feedback[:72]
            cv2.rectangle(image, (12, image.shape[0] - 52), (image.shape[1] - 12, image.shape[0] - 12), (20, 51, 43), -1)
            cv2.putText(image, cue, (24, image.shape[0] - 27), cv2.FONT_HERSHEY_SIMPLEX, .52, (255, 255, 255), 1)
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def metrics(self) -> dict:
        with self.lock:
            return {"reps": self.counter.reps, "stage": self.counter.stage,
                    "angle": round(self.angle), "feedback": self.feedback}
