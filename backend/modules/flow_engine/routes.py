from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from .public import FlowEngineProvider, flow_engine_provider
from .service import (
    BackgroundStatsDTO,
    FlowListResponseDTO,
    FlowMetricsDetailDTO,
    FlowStatusDTO,
    StartFlowRequest,
    StartFlowResponse,
    SystemMetricsDTO,
    UserFlowsResponseDTO,
)

router = APIRouter(prefix="/api/v1/flow", tags=["flow"])


def service_provider() -> FlowEngineProvider:
    return flow_engine_provider()


@router.post("/start", response_model=StartFlowResponse)
async def start_flow(body: StartFlowRequest, svc: FlowEngineProvider = Depends(service_provider)) -> StartFlowResponse:
    try:
        await svc.initialize()
        return await svc.start(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{flow_id}", response_model=FlowStatusDTO)
async def get_status(flow_id: str, svc: FlowEngineProvider = Depends(service_provider)) -> FlowStatusDTO:
    try:
        await svc.initialize()
        return await svc.status(flow_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/running", response_model=FlowListResponseDTO)
async def list_running(
    user_id: str | None = Query(default=None),
    svc: FlowEngineProvider = Depends(service_provider),
) -> FlowListResponseDTO:
    await svc.initialize()
    return await svc.list_running(user_id)


@router.get("/user/{user_id}", response_model=UserFlowsResponseDTO)
async def list_user_flows(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    svc: FlowEngineProvider = Depends(service_provider),
) -> UserFlowsResponseDTO:
    await svc.initialize()

    # Create a concrete service instance to call list_user which returns UserFlowsResponseDTO
    # The provider protocol does not expose this method, so use the concrete service.
    concrete = service_provider()  # type: ignore[assignment]
    await concrete.initialize()
    return await concrete.list_user(user_id=user_id, limit=limit, offset=offset)  # type: ignore[attr-defined]


@router.get("/metrics/system", response_model=SystemMetricsDTO)
async def system_metrics(svc: FlowEngineProvider = Depends(service_provider)) -> SystemMetricsDTO:
    await svc.initialize()
    return await svc.metrics()


@router.post("/{flow_id}/cancel")
async def cancel(flow_id: str, svc: FlowEngineProvider = Depends(service_provider)) -> dict[str, bool]:
    await svc.initialize()
    ok = await svc.cancel(flow_id)
    return {"success": ok}


@router.get("/{flow_id}/metrics", response_model=FlowMetricsDetailDTO)
async def flow_metrics(flow_id: str, svc: FlowEngineProvider = Depends(service_provider)) -> FlowMetricsDetailDTO:
    await svc.initialize()
    # use concrete service for extra methods
    from .service import create_flow_engine_service

    s = create_flow_engine_service()
    await s.initialize()
    return await s.flow_metrics(flow_id)


@router.get("/background/stats", response_model=BackgroundStatsDTO)
async def background_stats() -> BackgroundStatsDTO:
    from .service import create_flow_engine_service

    s = create_flow_engine_service()
    await s.initialize()
    return await s.background_stats()
