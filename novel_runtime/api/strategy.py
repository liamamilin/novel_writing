from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.strategy_service import StrategyService

router = APIRouter(prefix="/api/projects/{project_id}/strategy", tags=["strategy"])


def get_service(request: Request) -> StrategyService:
    settings = request.app.state.settings
    from pathlib import Path
    return StrategyService(ProjectService(request.app.state.db, Path(settings.storage_base_path)))


@router.get("")
async def get_strategy(
    project_id: str,
    svc: StrategyService = Depends(get_service),
):
    return svc.get_strategy(project_id)


@router.put("")
async def update_strategy(
    project_id: str, body: dict,
    svc: StrategyService = Depends(get_service),
):
    return svc.update_strategy(project_id, body)


@router.post("/reset")
async def reset_strategy(
    project_id: str,
    svc: StrategyService = Depends(get_service),
):
    return svc.reset_strategy(project_id)
