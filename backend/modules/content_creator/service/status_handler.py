"""Status polling and lifecycle helpers for the content creator service."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from modules.content.public import ContentProvider, UnitStatus
from modules.task_queue.public import task_queue_provider

from .dtos import MobileUnitCreationResult

logger = logging.getLogger(__name__)


class StatusHandler:
    """Encapsulate task submission and unit status lifecycle operations."""

    def __init__(
        self,
        content: ContentProvider,
        task_queue_factory: Callable[[], Any] = task_queue_provider,
    ) -> None:
        self._content = content
        self._task_queue_factory = task_queue_factory

    async def enqueue_unit_creation(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        learner_level: str,
    ) -> str:
        """Submit the ARQ flow responsible for background unit creation."""

        task_queue_service = self._task_queue_factory()
        task_result = await task_queue_service.submit_flow_task(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(unit_id),
            inputs={
                "unit_id": unit_id,
                "topic": topic,
                "unit_source_material": source_material,
                "target_lesson_count": target_lesson_count,
                "learner_level": learner_level,
            },
        )
        await self._content.set_unit_task(unit_id, task_result.task_id)
        return str(task_result.task_id)

    async def retry_unit_creation(self, unit_id: str) -> MobileUnitCreationResult | None:
        """Retry a failed unit creation by resubmitting its task."""

        unit = await self._content.get_unit(unit_id)
        if not unit:
            return None
        if unit.status != UnitStatus.FAILED.value:
            raise ValueError(f"Unit {unit_id} is not in failed state (current: {unit.status})")
        if not unit.generated_from_topic:
            raise ValueError(f"Unit {unit_id} was not generated from a topic and cannot be retried")

        await self._content.update_unit_status(
            unit_id=unit_id,
            status=UnitStatus.IN_PROGRESS.value,
            error_message=None,
            creation_progress={"stage": "retrying", "message": "Retrying unit creation..."},
        )

        task_queue_service = self._task_queue_factory()
        task_result = await task_queue_service.submit_flow_task(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(unit_id),
            inputs={
                "unit_id": unit_id,
                "topic": unit.title,
                "source_material": unit.source_material,
                "target_lesson_count": unit.target_lesson_count,
                "learner_level": unit.learner_level,
            },
        )
        await self._content.set_unit_task(unit_id, task_result.task_id)
        logger.info("✅ Unit retry initiated: unit_id=%s", unit_id)
        return MobileUnitCreationResult(unit_id=unit_id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

    async def dismiss_unit(self, unit_id: str) -> bool:
        """Dismiss (delete) a unit or mark it as dismissed when deletion is unavailable."""

        unit = await self._content.get_unit(unit_id)
        if not unit:
            return False

        try:
            success = await self._content.delete_unit(unit_id)
            logger.info("✅ Unit dismissed: unit_id=%s", unit_id)
            return bool(success)
        except AttributeError:
            logger.warning(
                "Delete method not available, marking unit as dismissed: unit_id=%s",
                unit_id,
            )
            result = await self._content.update_unit_status(
                unit_id=unit_id,
                status="dismissed",
                error_message=None,
                creation_progress={"stage": "dismissed", "message": "Unit dismissed by user"},
            )
            return result is not None

    async def check_and_timeout_stale_units(self, timeout_seconds: int = 3600) -> int:
        """Check for units stuck in progress and mark them as failed once timed out."""

        logger.info("🔍 Checking for stale in_progress units (timeout: %s seconds)", timeout_seconds)
        in_progress_units = await self._content.get_units_by_status(UnitStatus.IN_PROGRESS.value, limit=1000)
        if not in_progress_units:
            logger.debug("No in_progress units found")
            return 0

        timeout_threshold = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        timed_out_count = 0
        task_queue_service = self._task_queue_factory()

        for unit in in_progress_units:
            try:
                unit_age = datetime.now(UTC) - unit.updated_at.replace(tzinfo=UTC)
                task_failed = False
                if unit.arq_task_id:
                    task_status = await task_queue_service.get_task_status(unit.arq_task_id)
                    if task_status:
                        if task_status.status == "failed":
                            task_failed = True
                            logger.warning("Unit %s has failed task %s", unit.id, unit.arq_task_id)
                    else:
                        logger.warning("Unit %s has non-existent task %s", unit.id, unit.arq_task_id)
                        if unit_age.total_seconds() > 300:
                            task_failed = True

                should_timeout = task_failed or (unit.updated_at.replace(tzinfo=UTC) < timeout_threshold)
                if should_timeout:
                    error_reason = "Associated task failed" if task_failed else (
                        f"Unit creation exceeded timeout ({timeout_seconds} seconds)"
                    )
                    logger.warning(
                        "⏰ Timing out unit %s: %s (age: %s seconds)",
                        unit.id,
                        error_reason,
                        unit_age.total_seconds(),
                    )
                    await self._content.update_unit_status(
                        unit_id=unit.id,
                        status=UnitStatus.FAILED.value,
                        error_message=f"Creation timed out: {error_reason}",
                        creation_progress={"stage": "failed", "message": "Creation timed out"},
                    )
                    timed_out_count += 1
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error checking unit %s: %s", unit.id, str(exc), exc_info=True)
                continue

        if timed_out_count > 0:
            logger.info("✅ Marked %s stale unit(s) as failed", timed_out_count)
        else:
            logger.debug("No stale units found")
        return timed_out_count
