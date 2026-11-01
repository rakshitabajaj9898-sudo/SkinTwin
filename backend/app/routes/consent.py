
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.consent_purpose import ConsentPurpose
from backend.app.models.consent_notice import ConsentNotice
from backend.app.models.consent_record import ConsentRecord
from backend.app.models.consent_audit_log import ConsentAuditLog

from backend.app.schemas.consent import (
    ConsentDecisionRequest,
    ConsentWithdrawalRequest,
    ConsentPurposeResponse,
    ConsentNoticeResponse,
    ConsentAuditResponse,
)

from backend.app.security.dependencies import get_current_user


router = APIRouter(prefix="/consents", tags=["Consent Management"])


# 1. Get all active consent purposes
@router.get("/purposes", response_model=list[ConsentPurposeResponse])
def get_consent_purposes(db: Session = Depends(get_db)):
    return (
        db.query(ConsentPurpose)
        .filter(ConsentPurpose.is_active.is_(True))
        .order_by(ConsentPurpose.id.asc())
        .all()
    )


# 2. Get all currently published consent notices
@router.get("/notices", response_model=list[ConsentNoticeResponse])
def get_consent_notices(db: Session = Depends(get_db)):
    return (
        db.query(ConsentNotice)
        .join(
            ConsentPurpose,
            ConsentNotice.purpose_id == ConsentPurpose.id
        )
        .filter(
            ConsentNotice.is_active.is_(True),
            ConsentNotice.published_at.isnot(None),
            ConsentPurpose.is_active.is_(True)
        )
        .order_by(ConsentNotice.id.asc())
        .all()
    )


# 3. Submit a consent decision
@router.post(
    "/decisions",
    status_code=status.HTTP_201_CREATED
)
def submit_consent(
    decision: ConsentDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        notice = (
            db.query(ConsentNotice)
            .filter(
                ConsentNotice.id == decision.notice_id,
                ConsentNotice.is_active.is_(True),
                ConsentNotice.published_at.isnot(None)
            )
            .with_for_update()
            .first()
        )

        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active consent notice not found."
            )

        purpose = (
            db.query(ConsentPurpose)
            .filter(
                ConsentPurpose.id == notice.purpose_id,
                ConsentPurpose.is_active.is_(True)
            )
            .with_for_update()
            .first()
        )

        if not purpose:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This consent purpose is inactive."
            )

        now = datetime.now(timezone.utc)

        consent_record = ConsentRecord(
            user_id=current_user.id,
            purpose_id=purpose.id,
            notice_id=notice.id,
            status=decision.status,
            collection_method=decision.collection_method,
            consented_at=now if decision.status == "granted" else None
        )

        db.add(consent_record)
        db.flush()

        audit_log = ConsentAuditLog(
            user_id=current_user.id,
            consent_record_id=consent_record.id,
            action=(
                "consent_granted"
                if decision.status == "granted"
                else "consent_denied"
            ),
            previous_status=None,
            new_status=decision.status,
            collection_method=decision.collection_method
        )

        db.add(audit_log)
        db.commit()
        db.refresh(consent_record)

        return {
            "message": "Consent decision recorded successfully.",
            "consent_record_id": consent_record.id,
            "purpose_id": purpose.id,
            "status": consent_record.status,
            "notice_version": notice.version,
            "recorded_at": now
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save consent decision."
        )


# 4. Withdraw previously granted consent
@router.post("/withdraw")
def withdraw_consent(
    request: ConsentWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        purpose = (
            db.query(ConsentPurpose)
            .filter(ConsentPurpose.id == request.purpose_id)
            .with_for_update()
            .first()
        )

        if not purpose:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent purpose not found."
            )

        latest_record = (
            db.query(ConsentRecord)
            .filter(
                ConsentRecord.user_id == current_user.id,
                ConsentRecord.purpose_id == request.purpose_id
            )
            .order_by(
                ConsentRecord.created_at.desc(),
                ConsentRecord.id.desc()
            )
            .first()
        )

        if not latest_record or latest_record.status != "granted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active consent is available to withdraw."
            )

        now = datetime.now(timezone.utc)

        withdrawal_record = ConsentRecord(
            user_id=current_user.id,
            purpose_id=latest_record.purpose_id,
            notice_id=latest_record.notice_id,
            status="withdrawn",
            collection_method=request.collection_method,
            withdrawn_at=now
        )

        db.add(withdrawal_record)
        db.flush()

        audit_log = ConsentAuditLog(
            user_id=current_user.id,
            consent_record_id=withdrawal_record.id,
            action="consent_withdrawn",
            previous_status="granted",
            new_status="withdrawn",
            collection_method=request.collection_method
        )

        db.add(audit_log)
        db.commit()
        db.refresh(withdrawal_record)

        return {
            "message": "Consent withdrawal recorded successfully.",
            "consent_record_id": withdrawal_record.id,
            "purpose_id": withdrawal_record.purpose_id,
            "status": withdrawal_record.status,
            "recorded_at": now
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to record consent withdrawal."
        )


# 5. Get the latest consent decision for each purpose
@router.get("/my-consents")
def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(ConsentRecord, ConsentNotice.version)
        .join(
            ConsentNotice,
            ConsentRecord.notice_id == ConsentNotice.id
        )
        .filter(ConsentRecord.user_id == current_user.id)
        .order_by(
            ConsentRecord.created_at.desc(),
            ConsentRecord.id.desc()
        )
        .all()
    )

    latest_by_purpose = {}

    for record, notice_version in records:
        if record.purpose_id not in latest_by_purpose:
            latest_by_purpose[record.purpose_id] = {
                "id": record.id,
                "purpose_id": record.purpose_id,
                "notice_id": record.notice_id,
                "notice_version": notice_version,
                "status": record.status,
                "collection_method": record.collection_method,
                "consented_at": record.consented_at,
                "withdrawn_at": record.withdrawn_at,
                "created_at": record.created_at
            }

    return list(latest_by_purpose.values())


# 6. Get the authenticated user's consent audit history
@router.get(
    "/audit-history",
    response_model=list[ConsentAuditResponse]
)
def get_consent_audit_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(ConsentAuditLog)
        .filter(ConsentAuditLog.user_id == current_user.id)
        .order_by(
            ConsentAuditLog.created_at.desc(),
            ConsentAuditLog.id.desc()
        )
        .all()
    )
