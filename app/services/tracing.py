from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
logging.getLogger("langfuse").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)


def _get_langfuse():
    settings = get_settings()

    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        logger.info("Langfuse keys not found. Tracing is disabled.")
        return None

    try:
        from langfuse import Langfuse
        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse client initialized successfully.")
        return client

    except Exception as e:
        logger.warning("Langfuse client initialization failed: %s", e)
        return None


def get_callbacks() -> list[Any]:
    return []


def trace_chat(tenant_id: str, query: str, answer: str, latency_ms: int) -> None:
    client = _get_langfuse()
    if client is None:
        return

    try:
        trace = client.trace(
            name="chat",
            user_id=tenant_id,
            input=query,
            output=answer,
            metadata={"latency_ms": latency_ms},
            tags=["chat", "production"],
        )
        print(f"Trace object: {trace.id}")
        client.flush()
        # print(f"Task manager stats: {client.task_manager._queue.qsize()}")
        # print(f"Consumer running: {client.task_manager.consumer_thread.is_alive()}")
        # print("Flush complete")
        logger.info("Langfuse trace created: %s", trace.id)
    except Exception as e:
        logger.exception("Langfuse tracing failed")
        print(f"FULL ERROR: {type(e).__name__}: {e}")