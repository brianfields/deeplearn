"""Async repository layer for the object_store module."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AudioModel, ImageModel


class ImageRepo:
    """Data access helpers for image records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int | None,
        s3_key: str,
        s3_bucket: str,
        filename: str,
        content_type: str,
        file_size: int,
        width: int | None,
        height: int | None,
        alt_text: str | None,
        description: str | None,
    ) -> ImageModel:
        image = ImageModel(
            user_id=user_id,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            width=width,
            height=height,
            alt_text=alt_text,
            description=description,
        )
        self.session.add(image)
        await self.session.flush()
        await self.session.refresh(image)
        return image

    async def by_id(self, image_id: uuid.UUID) -> ImageModel | None:
        return await self.session.get(ImageModel, image_id)

    async def by_user_id(self, user_id: int | None) -> list[ImageModel]:
        stmt = select(ImageModel).where(ImageModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int | None, *, limit: int, offset: int) -> list[ImageModel]:
        stmt = (
            select(ImageModel)
            .where(ImageModel.user_id == user_id)
            .order_by(ImageModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_global(self, *, limit: int, offset: int) -> list[ImageModel]:
        stmt = (
            select(ImageModel)
            .where(ImageModel.user_id.is_(None))
            .order_by(ImageModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, image: ImageModel) -> None:
        await self.session.delete(image)
        await self.session.flush()

    async def exists(self, image_id: uuid.UUID) -> bool:
        stmt = select(ImageModel.id).where(ImageModel.id == image_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_by_user(self, user_id: int | None) -> int:
        stmt = select(ImageModel.id).where(ImageModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())


class AudioRepo:
    """Data access helpers for audio records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int | None,
        s3_key: str,
        s3_bucket: str,
        filename: str,
        content_type: str,
        file_size: int,
        duration_seconds: float | None,
        bitrate_kbps: int | None,
        sample_rate_hz: int | None,
        transcript: str | None,
    ) -> AudioModel:
        audio = AudioModel(
            user_id=user_id,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            duration_seconds=duration_seconds,
            bitrate_kbps=bitrate_kbps,
            sample_rate_hz=sample_rate_hz,
            transcript=transcript,
        )
        self.session.add(audio)
        await self.session.flush()
        await self.session.refresh(audio)
        return audio

    async def by_id(self, audio_id: uuid.UUID) -> AudioModel | None:
        return await self.session.get(AudioModel, audio_id)

    async def by_user_id(self, user_id: int | None) -> list[AudioModel]:
        stmt = select(AudioModel).where(AudioModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int | None, *, limit: int, offset: int) -> list[AudioModel]:
        stmt = (
            select(AudioModel)
            .where(AudioModel.user_id == user_id)
            .order_by(AudioModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_global(self, *, limit: int, offset: int) -> list[AudioModel]:
        stmt = (
            select(AudioModel)
            .where(AudioModel.user_id.is_(None))
            .order_by(AudioModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, audio: AudioModel) -> None:
        await self.session.delete(audio)
        await self.session.flush()

    async def exists(self, audio_id: uuid.UUID) -> bool:
        stmt = select(AudioModel.id).where(AudioModel.id == audio_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_by_user(self, user_id: int | None) -> int:
        stmt = select(AudioModel.id).where(AudioModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
