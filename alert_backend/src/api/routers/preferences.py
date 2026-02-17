from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import User, UserPreference
from src.api.schemas import PreferenceOut, PreferenceUpsert

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get(
    "",
    response_model=list[PreferenceOut],
    summary="List preferences",
    description="List current user's notification channel preferences.",
)
def list_preferences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[PreferenceOut]:
    return db.query(UserPreference).filter(UserPreference.user_id == current_user.id).all()


@router.put(
    "",
    response_model=PreferenceOut,
    summary="Upsert preference",
    description="Create or update a preference record for a channel.",
)
def upsert_preference(
    payload: PreferenceUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreferenceOut:
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id, UserPreference.channel == payload.channel)
        .first()
    )
    if pref:
        pref.enabled = payload.enabled
        pref.config = payload.config
    else:
        pref = UserPreference(user_id=current_user.id, channel=payload.channel, enabled=payload.enabled, config=payload.config)
        db.add(pref)

    db.commit()
    db.refresh(pref)
    return pref
