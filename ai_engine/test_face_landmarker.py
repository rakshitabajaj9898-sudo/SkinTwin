
from pathlib import Path
import cv2

from ai_engine.face_landmarker import SkinTwinFaceLandmarker
from ai_engine.region_mapper import SkinTwinRegionMapper

BASE_DIR = Path(__file__).parent

image_path = BASE_DIR / "datasets/test_images/portrait.jpg"
output_path = BASE_DIR / "datasets/test_images/portrait_regions.jpg"

image = cv2.imread(str(image_path))

if image is None:
    raise ValueError("Could not load test image.")

rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

detector = SkinTwinFaceLandmarker()
mapper = SkinTwinRegionMapper()

try:
    result = detector.detect(rgb_image)

    if not result["face_detected"]:
        raise ValueError("No face detected.")

    regions = mapper.map_regions(image, result["landmarks"])
    output = mapper.draw_regions(image, regions)

    cv2.imwrite(str(output_path), output)

    print("Face detected:", result["face_detected"])
    print("Landmarks:", result["landmark_count"])
    print("Regions mapped:", len(regions))

    for name in regions:
        print("-", name)

    print("Visualization saved:", output_path)

finally:
    detector.close()
