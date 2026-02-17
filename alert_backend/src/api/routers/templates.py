from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Template, User
from src.api.schemas import TemplateCreate, TemplateOut, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post(
    "",
    response_model=TemplateOut,
    summary="Create template",
    description="Create a reusable message template.",
)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TemplateOut:
    t = Template(
        name=payload.name,
        description=payload.description,
        subject=payload.subject,
        body=payload.body,
        metadata_json=payload.metadata_json,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get(
    "",
    response_model=list[TemplateOut],
    summary="List templates",
    description="List all templates.",
)
def list_templates(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[TemplateOut]:
    return db.query(Template).order_by(Template.created_at.desc()).all()


@router.get(
    "/{template_id}",
    response_model=TemplateOut,
    summary="Get template",
    description="Get a template by id.",
)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TemplateOut:
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return t


@router.patch(
    "/{template_id}",
    response_model=TemplateOut,
    summary="Update template",
    description="Update a template by id.",
)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TemplateOut:
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, field, value)

    db.commit()
    db.refresh(t)
    return t


@router.delete(
    "/{template_id}",
    status_code=204,
    summary="Delete template",
    description="Delete a template by id.",
)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    db.delete(t)
    db.commit()
    return None
