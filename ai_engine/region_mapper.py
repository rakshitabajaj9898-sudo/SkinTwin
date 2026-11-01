
import cv2
import numpy as np


class SkinTwinRegionMapper:
    """Create approximate polygon-based facial skin regions."""

    # MediaPipe Face Mesh landmark indices
    LEFT_EYE = [33, 133, 159, 145]
    RIGHT_EYE = [362, 263, 386, 374]

    LEFT_EYEBROW = [70, 63, 105, 66, 107]
    RIGHT_EYEBROW = [336, 296, 334, 293, 300]

    NOSE = [1, 2, 98, 327, 168, 197, 5, 4]
    MOUTH = [61, 291, 0, 17, 13, 14]

    def _point(self, landmarks, index, width, height):
        point = landmarks[index]
        return (
            int(point["x"] * width),
            int(point["y"] * height)
        )

    def _polygon(self, points, shape):
        height, width = shape[:2]
        polygon = np.array(points, dtype=np.int32)

        polygon[:, 0] = np.clip(polygon[:, 0], 0, width - 1)
        polygon[:, 1] = np.clip(polygon[:, 1], 0, height - 1)

        return polygon

    def map_regions(self, image, landmarks):
        if image is None or image.size == 0:
            raise ValueError("Invalid image.")

        if len(landmarks) < 478:
            raise ValueError("Expected 478 facial landmarks.")

        height, width = image.shape[:2]

        def p(index):
            return self._point(landmarks, index, width, height)

        # Facial reference points
        left_face = p(234)
        right_face = p(454)
        forehead_center = p(10)
        chin_center = p(152)

        left_eye_outer = p(33)
        right_eye_outer = p(263)

        left_brow = p(70)
        right_brow = p(300)

        nose_top = p(168)
        nose_bottom = p(2)
        left_nose = p(98)
        right_nose = p(327)

        mouth_left = p(61)
        mouth_right = p(291)
        mouth_bottom = p(17)

        # Approximate forehead boundary
        forehead = [
            (left_brow[0], left_brow[1]),
            (right_brow[0], right_brow[1]),
            (right_face[0] - 15, forehead_center[1]),
            (forehead_center[0], forehead_center[1] - 15),
            (left_face[0] + 15, forehead_center[1])
        ]

        # Cheek polygons
        left_cheek = [
            left_face,
            left_eye_outer,
            left_brow,
            left_nose,
            mouth_left,
            (mouth_left[0], mouth_bottom[1]),
            (left_face[0] + 10, mouth_bottom[1] + 25)
        ]

        right_cheek = [
            right_eye_outer,
            right_face,
            (right_face[0] - 10, mouth_bottom[1] + 25),
            (mouth_right[0], mouth_bottom[1]),
            mouth_right,
            right_nose,
            right_brow
        ]

        # Nose polygon
        nose = [
            nose_top,
            right_nose,
            p(5),
            nose_bottom,
            left_nose
        ]

        # Chin polygon
        chin = [
            mouth_left,
            mouth_right,
            (chin_center[0], chin_center[1]),
            (left_face[0] + 15, mouth_bottom[1] + 20),
            (right_face[0] - 15, mouth_bottom[1] + 20)
        ]

        raw_regions = {
            "forehead": forehead,
            "left_cheek": left_cheek,
            "right_cheek": right_cheek,
            "nose": nose,
            "chin": chin
        }

        regions = {}

        for name, points in raw_regions.items():
            regions[name] = self._polygon(points, image.shape)

        return regions

    def draw_regions(self, image, regions):
        output = image.copy()

        for name, polygon in regions.items():
            cv2.polylines(
                output,
                [polygon],
                isClosed=True,
                color=(0, 255, 0),
                thickness=2
            )

            center = polygon.mean(axis=0).astype(int)

            cv2.putText(
                output,
                name.replace("_", " ").title(),
                tuple(center),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 255, 0),
                1
            )

        return output
