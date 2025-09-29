# Object Store Module — Agents Guide

This module is the single place to store and retrieve large binary objects (especially images and audio). It abstracts provider-specific details (e.g., Amazon S3) behind a stable public interface so callers do not handle storage SDKs directly.

- **Use this module for all large objects**: images, audio, and any sizeable binary files should be stored and fetched via this module.
- **Provider abstraction**: the implementation currently targets S3, but the design hides provider particulars so we can swap or extend providers without changing callers.
- **Public interface only**: other modules should import from `modules.object_store.public` and rely on the `ObjectStoreProvider` protocol.

## How to use (cross-module)

- Import the provider factory and DTOs from the public surface:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from modules.object_store.public import (
    object_store_provider,
    ImageCreate,
    AudioCreate,
)

async def upload_example(session: AsyncSession) -> None:
    store = object_store_provider(session)
    # Upload image
    img_result = await store.upload_image(
        ImageCreate(
            user_id=123,
            filename="cover.png",
            content_type="image/png",
            data=b"...",
        ),
        generate_presigned_url=True,
    )
    # Upload audio
    audio_result = await store.upload_audio(
        AudioCreate(
            user_id=123,
            filename="clip.mp3",
            content_type="audio/mpeg",
            data=b"...",
        ),
        generate_presigned_url=True,
    )
```

- Prefer presigned URLs for client downloads; the service can generate expiring links.
- Do not use storage SDKs (e.g., boto3) outside this module.

## Capabilities

- Upload, retrieve, list, and delete images and audio with per-user scoping.
- Optional presigned URL generation with configurable TTL.
- Storage metadata persisted via repos; binary persisted via the provider (e.g., S3).

## Extensibility

- Providers are encapsulated (`s3_provider.py`); adding a new backend requires implementing the same interface and wiring in the factory.
- Callers keep using `ObjectStoreProvider` methods—no changes needed when providers change.
