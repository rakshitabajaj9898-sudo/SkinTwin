# SkinTwin AI Engine Configuration

# Supported image formats
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Image size limits
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Image dimensions
MIN_IMAGE_WIDTH = 256
MIN_IMAGE_HEIGHT = 256
MAX_IMAGE_WIDTH = 4096
MAX_IMAGE_HEIGHT = 4096

# Image preprocessing
TARGET_IMAGE_SIZE = (224, 224)

# Image quality
MIN_BRIGHTNESS = 30
MAX_BRIGHTNESS = 225

# Privacy
STORE_UPLOADED_IMAGES = False
USE_IMAGES_FOR_TRAINING = False