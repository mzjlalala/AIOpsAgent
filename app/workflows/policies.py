"""Execute 内挂载的 Retry / Timeout / Fallback 策略。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """最多尝试 max_attempts 次（含首次）。"""

    max_attempts: int = Field(default=2, ge=1)


class TimeoutPolicy(BaseModel):
    """单次尝试超时（秒）；超时视为可 retry 的失败。"""

    seconds: float = Field(default=30.0, gt=0)


class FallbackPolicy(BaseModel):
    """重试耗尽后的行为：continue 继续后续步骤；abort 终止全流程。"""

    on_exhausted: Literal["continue", "abort"] = "continue"


class AttemptFailed(Exception):
    """单次尝试失败（含超时），供 retry 循环捕获。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def run_with_retry[T](
    fn: Callable[[], Awaitable[T]],
    *,
    retry: RetryPolicy,
    timeout: TimeoutPolicy,
) -> T:
    """带超时与重试执行；全部失败则抛出最后一次 AttemptFailed。"""
    last_error = "unknown"
    for _attempt in range(1, retry.max_attempts + 1):
        try:
            return await asyncio.wait_for(fn(), timeout=timeout.seconds)
        except TimeoutError:
            last_error = f"timeout after {timeout.seconds}s"
        except AttemptFailed as exc:
            last_error = exc.message
        except Exception as exc:  # noqa: BLE001 — 策略层统一捕获后重试
            last_error = str(exc) or exc.__class__.__name__
    raise AttemptFailed(last_error)
