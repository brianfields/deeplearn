from __future__ import annotations

from typing import Any
import uuid

from llm_flow_engine.core.llm.config import LLMConfig
from llm_flow_engine.database.connection import DatabaseManager
from llm_flow_engine.flows.background_manager import BackgroundFlowManager
from llm_flow_engine.flows.base import BaseFlow
from llm_flow_engine.flows.status_api import FlowStatusAPI


class FlowEngineRepo:
    """Database/engine access layer for flow execution and monitoring."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.background = BackgroundFlowManager(db_manager)
        self.status_api = FlowStatusAPI(db_manager)

    async def initialize(self) -> None:
        await self.db_manager.initialize()

    async def start_background_flow(
        self,
        flow_class: type[BaseFlow],
        method_name: str,
        inputs: dict[str, Any],
        user_id: str | None,
        estimated_steps: int | None,
        llm_config: LLMConfig | None,
    ) -> uuid.UUID:
        return await self.background.start_background_flow(
            flow_class=flow_class,
            method_name=method_name,
            inputs=inputs,
            user_id=user_id,
            estimated_steps=estimated_steps,
            llm_config=llm_config,
        )

    async def get_flow_status(self, flow_id: str) -> Any:
        return await self.status_api.get_flow_status(flow_id)

    async def list_running_flows(self, user_id: str | None = None) -> list[dict[str, Any]]:
        return await self.background.list_running_flows(user_id=user_id)

    async def list_user_flows(self, user_id: str, limit: int = 50, offset: int = 0) -> Any:
        return await self.status_api.list_user_flows(user_id=user_id, limit=limit, offset=offset)

    async def get_system_metrics(self) -> Any:
        return await self.status_api.get_system_metrics()

    async def cancel_flow(self, flow_id: str) -> bool:
        return await self.background.cancel_flow(flow_id)

    async def get_flow_metrics(self, flow_id: str) -> Any:
        return await self.status_api.get_flow_metrics(flow_id)

    async def get_background_stats(self) -> dict[str, Any]:
        return self.background.get_system_stats()
