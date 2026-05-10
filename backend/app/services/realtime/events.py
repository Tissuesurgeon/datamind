"""Realtime event payloads broadcast over Redis pubsub + WebSocket."""

from __future__ import annotations

import enum
import time
from dataclasses import asdict, dataclass, field
from typing import Any


class EventType(str, enum.Enum):
    UPLOAD_STARTED = "upload.started"
    UPLOAD_PROGRESS = "upload.progress"
    UPLOAD_COMPLETED = "upload.completed"
    UPLOAD_FAILED = "upload.failed"

    EMBED_STARTED = "embed.started"
    EMBED_PROGRESS = "embed.progress"
    EMBED_COMPLETED = "embed.completed"

    ANALYZE_STARTED = "analyze.started"
    ANALYZE_COMPLETED = "analyze.completed"

    STORAGE_PUSHING = "storage.pushing"
    STORAGE_ANCHORED = "storage.anchored"

    TRAIN_STARTED = "train.started"
    TRAIN_PROGRESS = "train.progress"
    TRAIN_LOG = "train.log"
    TRAIN_COMPLETED = "train.completed"
    TRAIN_FAILED = "train.failed"


@dataclass
class RealtimeEvent:
    type: EventType
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_json(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d
