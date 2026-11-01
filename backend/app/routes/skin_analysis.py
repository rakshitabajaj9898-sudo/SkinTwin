
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.consent_purpose import ConsentPurpose
from backend.app.models.consent_record import ConsentRecord
from backend.app.security.dependencies import get_current_user

from ai_engine.config import MAX_IMAGE_SIZE_BYTES
from ai_engine.image_validator import validate_and_analyze_image
from ai_engine.preprocessing.image_preprocessor import preprocess_image


router = APIRouter(
    prefix="/skin-analysis",
    tags=["Skin Analysis"]
)


@router.post("/validate-image")
async def validate_skin_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Check whether skin image analysis is an active purpose
    purpose = (
        db.query(ConsentPurpose)
        .filter(
            ConsentPurpose.code == "SKIN_IMAGE_ANALYSIS",
            ConsentPurpose.is_active.is_(True),
        )
        .first()
    )

    if not purpose:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Skin image analysis is currently unavailable.",
        )

    # 2. Check the user's latest consent decision
    latest_consent = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose_id == purpose.id,
        )
        .order_by(
            ConsentRecord.created_at.desc(),
            ConsentRecord.id.desc(),
        )
        .first()
    )

    if not latest_consent or latest_consent.status != "granted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please grant skin image analysis consent before uploading an image.",
        )

    # 3. Read a bounded amount of image data
    try:
        image_bytes = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
    finally:
        await file.close()

    # 4. Validate format, size, dimensions and image quality
    result = validate_and_analyze_image(
        image_bytes,
        file.filename or "",
    )

    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    # 5. Preprocess the image in memory
    try:
        processed_image = preprocess_image(image_bytes)
    except (ValueError, cv2.error):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to preprocess the uploaded image.",
        )

    # 6. Return metadata only; do not store or return the selfie
    return {
        "message": "Image validation and preprocessing completed successfully.",
        "image_quality": result,
        "preprocessing": {
            "shape": list(processed_image["shape"]),
            "dtype": processed_image["dtype"],
            "normalized": processed_image["normalized"],
        },
    }
