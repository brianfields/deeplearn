from __future__ import annotations

from typing import Any

from llm_flow_engine.core.llm.config import LLMConfig, create_llm_config_from_env
from llm_flow_engine.database.connection import DatabaseManager
from pydantic import BaseModel, Field

from .repo import FlowEngineRepo


class StartFlowRequest(BaseModel):
    flow_name: str = Field(..., description="Registered flow identifier")
    method_name: str = Field(..., description="Public method on flow to invoke")
    inputs: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = Field(default=None)
    estimated_steps: int | None = Field(default=None)


class StartFlowResponse(BaseModel):
    flow_id: str


class FlowProgress(BaseModel):
    step_progress: int | None = None
    total_steps: int | None = None
    percentage: float = 0.0


class FlowTiming(BaseModel):
    started_at: str | None = None
    completed_at: str | None = None
    last_heartbeat: str | None = None
    execution_time_seconds: int | None = None


class FlowMetrics(BaseModel):
    total_tokens: int = 0
    total_cost: float = 0.0
    execution_time_ms: int | None = None


class FlowStatusDTO(BaseModel):
    flow_id: str
    flow_name: str
    status: str
    execution_mode: str
    current_step: str | None = None
    progress: FlowProgress
    timing: FlowTiming
    metrics: FlowMetrics
    outputs: dict[str, Any] | None = None
    error_message: str | None = None
    is_running: bool = False
    steps: list[FlowStepStatusDTO] = []


class FlowListItemDTO(BaseModel):
    flow_id: str
    flow_name: str
    status: str
    progress_percentage: float
    started_at: str | None = None
    completed_at: str | None = None
    execution_time_seconds: int | None = None


class FlowListResponseDTO(BaseModel):
    items: list[FlowListItemDTO]


class UserFlowsResponseDTO(BaseModel):
    flows: list[FlowListItemDTO]
    pagination: dict[str, Any]
    filters_applied: dict[str, Any]


class SystemMetricsDTO(BaseModel):
    system_health: dict[str, Any]
    usage_metrics_24h: dict[str, Any]
    usage_metrics_7d: dict[str, Any]
    timestamp: str


class FlowStepStatusDTO(BaseModel):
    step_id: str
    step_name: str
    step_order: int
    status: str
    tokens_used: int | None = None
    cost_estimate: float | None = None
    execution_time_seconds: int | None = None
    created_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class FlowMetricsDetailDTO(BaseModel):
    flow_id: str
    flow_name: str
    overall_metrics: dict[str, Any]
    step_metrics: list[dict[str, Any]]
    llm_metrics: dict[str, Any]
    performance_insights: list[str]


class BackgroundStatsDTO(BaseModel):
    running_flows: int
    active_flow_ids: list[str]
    is_shutdown: bool


class FlowEngineService:
    """Use-cases around running and monitoring flows. Returns DTOs only."""

    def __init__(self, repo: FlowEngineRepo, llm_config: LLMConfig | None = None) -> None:
        self.repo = repo
        self.llm_config = llm_config or create_llm_config_from_env()

    async def initialize(self) -> None:
        await self.repo.initialize()

    async def start(self, req: StartFlowRequest) -> StartFlowResponse:
        from .public import flow_registry

        flow_class = flow_registry.get(req.flow_name)
        if not flow_class:
            raise ValueError(f"Unknown flow: {req.flow_name}")

        flow_id = await self.repo.start_background_flow(
            flow_class=flow_class,
            method_name=req.method_name,
            inputs=req.inputs,
            user_id=req.user_id,
            estimated_steps=req.estimated_steps,
            llm_config=self.llm_config,
        )
        return StartFlowResponse(flow_id=str(flow_id))

    async def status(self, flow_id: str) -> FlowStatusDTO:
        raw = await self.repo.get_flow_status(flow_id)
        dto = FlowStatusDTO(
            flow_id=raw.flow_id if hasattr(raw, "flow_id") else raw.get("flow_id"),
            flow_name=raw.flow_name if hasattr(raw, "flow_name") else raw.get("flow_name"),
            status=raw.status if hasattr(raw, "status") else raw.get("status"),
            execution_mode=(raw.execution_mode if hasattr(raw, "execution_mode") else raw.get("execution_mode")),
            current_step=(raw.current_step if hasattr(raw, "current_step") else raw.get("current_step")),
            progress=FlowProgress(
                step_progress=(raw.step_progress if hasattr(raw, "step_progress") else raw.get("progress", {}).get("step_progress")),
                total_steps=(raw.total_steps if hasattr(raw, "total_steps") else raw.get("progress", {}).get("total_steps")),
                percentage=(raw.progress_percentage if hasattr(raw, "progress_percentage") else raw.get("progress", {}).get("percentage", 0.0)),
            ),
            timing=FlowTiming(
                started_at=(raw.started_at if hasattr(raw, "started_at") else raw.get("timing", {}).get("started_at")),
                completed_at=(raw.completed_at if hasattr(raw, "completed_at") else raw.get("timing", {}).get("completed_at")),
                last_heartbeat=(raw.last_heartbeat if hasattr(raw, "last_heartbeat") else raw.get("timing", {}).get("last_heartbeat")),
                execution_time_seconds=(raw.execution_time_seconds if hasattr(raw, "execution_time_seconds") else raw.get("timing", {}).get("execution_time_seconds")),
            ),
            metrics=FlowMetrics(
                total_tokens=(raw.total_tokens if hasattr(raw, "total_tokens") else raw.get("metrics", {}).get("total_tokens", 0)),
                total_cost=(raw.total_cost if hasattr(raw, "total_cost") else float(raw.get("metrics", {}).get("total_cost", 0.0))),
                execution_time_ms=(raw.execution_time_ms if hasattr(raw, "execution_time_ms") else raw.get("metrics", {}).get("execution_time_ms")),
            ),
            outputs=(raw.outputs if hasattr(raw, "outputs") else raw.get("outputs")),
            error_message=(raw.error_message if hasattr(raw, "error_message") else raw.get("error_message")),
            is_running=(raw.is_running if hasattr(raw, "is_running") else raw.get("is_running", False)),
        )
        # Steps (only present for FlowStatusAPI result)
        if hasattr(raw, "steps") and isinstance(raw.steps, list):
            dto.steps = [
                FlowStepStatusDTO(
                    step_id=getattr(s, "step_id", None) or s.get("step_id"),
                    step_name=getattr(s, "step_name", None) or s.get("step_name"),
                    step_order=getattr(s, "step_order", None) or s.get("step_order"),
                    status=getattr(s, "status", None) or s.get("status"),
                    tokens_used=getattr(s, "tokens_used", None) or s.get("tokens_used"),
                    cost_estimate=(getattr(s, "cost_estimate", None) or s.get("cost_estimate")),
                    execution_time_seconds=(getattr(s, "execution_time_seconds", None) or s.get("execution_time_seconds")),
                    created_at=(getattr(s, "created_at", None) or s.get("created_at")),
                    completed_at=(getattr(s, "completed_at", None) or s.get("completed_at")),
                    error_message=(getattr(s, "error_message", None) or s.get("error_message")),
                )
                for s in raw.steps
            ]
        return dto

    async def list_running(self, user_id: str | None) -> FlowListResponseDTO:
        items_raw = await self.repo.list_running_flows(user_id=user_id)
        items = [
            FlowListItemDTO(
                flow_id=i["flow_id"],
                flow_name=i["flow_name"],
                status=i["status"],
                progress_percentage=i.get("progress_percentage", 0.0),
                started_at=i.get("started_at"),
                completed_at=i.get("completed_at"),
                execution_time_seconds=i.get("execution_time_seconds"),
            )
            for i in items_raw
        ]
        return FlowListResponseDTO(items=items)

    async def list_user(self, user_id: str, limit: int = 50, offset: int = 0) -> UserFlowsResponseDTO:
        raw = await self.repo.list_user_flows(user_id=user_id, limit=limit, offset=offset)
        data = raw.model_dump() if isinstance(raw, BaseModel) else raw
        items = [
            FlowListItemDTO(
                flow_id=i["flow_id"],
                flow_name=i["flow_name"],
                status=i["status"],
                progress_percentage=i.get("progress_percentage", 0.0),
                started_at=i.get("created_at"),
                completed_at=i.get("completed_at"),
                execution_time_seconds=i.get("execution_time_seconds"),
            )
            for i in data.get("flows", [])
        ]
        return UserFlowsResponseDTO(
            flows=items,
            pagination=data.get("pagination", {}),
            filters_applied=data.get("filters_applied", {}),
        )

    async def metrics(self) -> SystemMetricsDTO:
        raw = await self.repo.get_system_metrics()
        return SystemMetricsDTO(**(raw.model_dump() if isinstance(raw, BaseModel) else raw))

    async def cancel(self, flow_id: str) -> bool:
        return await self.repo.cancel_flow(flow_id)

    async def flow_metrics(self, flow_id: str) -> FlowMetricsDetailDTO:
        raw = await self.repo.get_flow_metrics(flow_id)
        data = raw.model_dump() if isinstance(raw, BaseModel) else raw
        return FlowMetricsDetailDTO(**data)

    async def background_stats(self) -> BackgroundStatsDTO:
        data = await self.repo.get_background_stats()
        return BackgroundStatsDTO(**data)


def create_flow_engine_service(database_url: str | None = None, llm_config: LLMConfig | None = None) -> FlowEngineService:
    db_url = database_url
    if db_url is None:
        import os

        db_url = os.getenv("DATABASE_URL")
    db_manager = DatabaseManager(db_url)  # type: ignore[arg-type]
    repo = FlowEngineRepo(db_manager)
    return FlowEngineService(repo=repo, llm_config=llm_config)
