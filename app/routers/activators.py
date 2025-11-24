from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.activator import Activator
from app.models.activator_composition import ActivatorComposition
from app.models.substance import Substance
from app.schemas.activator import (
    ActivatorCreate,
    ActivatorUpdate,
    ActivatorCompositionItem,
    ActivatorResponse,
    ActivatorCompositionResponse,
)
from app.auth import get_current_user
from app.schemas.user import UserResponse


router = APIRouter(prefix="/activators", tags=["activators"])


def build_activator_response(activator: Activator) -> ActivatorResponse:
    """
    Monta resposta de ativador com suas composições
    """
    return ActivatorResponse(
        id=activator.id,
        name=activator.name,
        created_at=activator.created_at,
        compositions=[
            ActivatorCompositionResponse(
                substance_id=composition.substance_id,
                volume_ml=composition.volume_ml,
                substance_name=composition.substance.name if composition.substance else "",
            )
            for composition in activator.compositions
        ],
    )


@router.post("", response_model=ActivatorResponse, status_code=status.HTTP_201_CREATED)
async def create_activator(
    activator_data: ActivatorCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Criar novo ativador metabólico com suas composições
    """
    # Validar substâncias
    substance_ids = {item.substance_id for item in activator_data.compositions}
    existing_substances = (
        db.query(Substance)
        .filter(Substance.id.in_(list(substance_ids)))
        .all()
    )
    if len(existing_substances) != len(substance_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more substances not found",
        )

    new_activator = Activator(name=activator_data.name)
    db.add(new_activator)
    db.flush()

    for item in activator_data.compositions:
        composition = ActivatorComposition(
            activator_id=new_activator.id,
            substance_id=item.substance_id,
            volume_ml=item.volume_ml,
        )
        db.add(composition)

    db.commit()
    db.refresh(new_activator)
    # Recarregar composições com substâncias
    new_activator = db.query(Activator).filter(Activator.id == new_activator.id).first()
    return build_activator_response(new_activator)


@router.get("", response_model=List[ActivatorResponse])
async def list_activators(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Listar todos os ativadores metabólicos
    """
    activators = db.query(Activator).order_by(Activator.name).all()
    return [build_activator_response(activator) for activator in activators]


@router.get("/{activator_id}", response_model=ActivatorResponse)
async def get_activator(
    activator_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Buscar ativador metabólico por ID
    """
    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    if not activator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activator not found",
        )
    return build_activator_response(activator)


@router.put("/{activator_id}", response_model=ActivatorResponse)
async def update_activator(
    activator_id: UUID,
    activator_data: ActivatorUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Atualizar ativador metabólico e, opcionalmente, suas composições
    """
    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    if not activator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activator not found",
        )

    update_data = activator_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        activator.name = update_data["name"]

    # Atualizar composições se fornecidas
    if "compositions" in update_data and update_data["compositions"] is not None:
        new_items = update_data["compositions"]

        substance_ids = {item["substance_id"] for item in new_items}
        existing_substances = (
            db.query(Substance)
            .filter(Substance.id.in_(list(substance_ids)))
            .all()
        )
        if len(existing_substances) != len(substance_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more substances not found",
            )

        # Remover composições antigas
        for composition in list(activator.compositions):
            db.delete(composition)

        # Adicionar novas composições
        for item in new_items:
            composition = ActivatorComposition(
                activator_id=activator.id,
                substance_id=item["substance_id"],
                volume_ml=item["volume_ml"],
            )
            db.add(composition)

    db.commit()
    db.refresh(activator)
    activator = db.query(Activator).filter(Activator.id == activator.id).first()
    return build_activator_response(activator)


@router.post(
    "/{activator_id}/compositions",
    response_model=ActivatorResponse,
    status_code=status.HTTP_200_OK,
)
async def add_substance_to_activator(
    activator_id: UUID,
    composition_data: ActivatorCompositionItem,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Adicionar nova substância (com volume) a um ativador existente
    """
    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    if not activator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activator not found",
        )

    substance = (
        db.query(Substance)
        .filter(Substance.id == composition_data.substance_id)
        .first()
    )
    if not substance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Substance not found",
        )

    existing_composition = (
        db.query(ActivatorComposition)
        .filter(
            ActivatorComposition.activator_id == activator_id,
            ActivatorComposition.substance_id == composition_data.substance_id,
        )
        .first()
    )
    if existing_composition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Substance already linked to this activator",
        )

    new_composition = ActivatorComposition(
        activator_id=activator_id,
        substance_id=composition_data.substance_id,
        volume_ml=composition_data.volume_ml,
    )
    db.add(new_composition)
    db.commit()

    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    return build_activator_response(activator)


@router.delete("/{activator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activator(
    activator_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Deletar ativador metabólico
    """
    activator = db.query(Activator).filter(Activator.id == activator_id).first()
    if not activator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activator not found",
        )

    db.delete(activator)
    db.commit()
    return None


