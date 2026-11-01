
import cv2
import numpy as np

from ai_engine.config import TARGET_IMAGE_SIZE


def preprocess_image(image_bytes: bytes) -> dict:
    """
    Decode, resize and normalize an image
    for future machine-learning models.
    """

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError("Unable to decode image.")

    # Convert BGR to RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # Resize image
    image = cv2.resize(
        image,
        TARGET_IMAGE_SIZE,
        interpolation=cv2.INTER_AREA
    )

    # Normalize pixel values between 0 and 1
    normalized_image = image.astype(
        np.float32
    ) / 255.0

    return {
        "image": normalized_image,
        "shape": normalized_image.shape,
        "dtype": str(normalized_image.dtype),
        "normalized": True
    }
