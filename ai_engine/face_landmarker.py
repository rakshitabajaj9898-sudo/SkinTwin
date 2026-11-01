
from pathlib import Path

import mediapipe as mp
import numpy as np


MODEL_PATH = (
    Path(__file__).parent
    / "model_assets"
    / "face_landmarker.task"
)


class SkinTwinFaceLandmarker:

    def __init__(self):
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}"
            )

        base_options = mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        )

        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5
        )

        self.detector = (
            mp.tasks.vision.FaceLandmarker.create_from_options(
                options
            )
        )

    def detect(self, image: np.ndarray) -> dict:

        if image is None or image.size == 0:
            raise ValueError("Invalid image.")

        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Expected an RGB image.")

        rgb_image = np.ascontiguousarray(
            image, dtype=np.uint8
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_image
        )

        result = self.detector.detect(mp_image)

        if not result.face_landmarks:
            return {
                "face_detected": False,
                "landmark_count": 0,
                "landmarks": []
            }

        landmarks = [
            {
                "x": float(point.x),
                "y": float(point.y),
                "z": float(point.z)
            }
            for point in result.face_landmarks[0]
        ]

        return {
            "face_detected": True,
            "landmark_count": len(landmarks),
            "landmarks": landmarks
        }

    def close(self):
        self.detector.close()
