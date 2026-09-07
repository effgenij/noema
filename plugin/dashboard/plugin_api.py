"""Cortex backend routes. Mounted by the Hermes gateway at /api/plugins/cortex/."""

from fastapi import APIRouter  # type: ignore[reportMissingImports]  # runtime: Hermes venv (~/.hermes/hermes-agent/venv)

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "plugin": "cortex"}
