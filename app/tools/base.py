"""Tool 基类：公开 ainvoke，子类实现 _execute。"""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable

from loguru import logger
from pydantic import BaseModel

from app.tools.context import ToolContext
from app.tools.exceptions import ToolError, ToolRetryExhaustedError, ToolTimeoutError
from app.tools.immutability import freeze_str_tags
from app.tools.results import ToolMetadata, ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory, ToolOutput


class BaseTool(ABC):
    """工具抽象基类。

    公开入口统一为 ``ainvoke``；子类实现 ``_execute``（可为 sync 或 async）。
    基类负责日志、耗时、超时、重试、异常包装与 Hook 调度。
    """

    name: str
    description: str
    category: ToolCategory
    timeout_seconds: float = 30.0
    max_retries: int = 0
    retry_interval_seconds: float = 0.1

    async def before(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> None:
        """调用前 Hook（默认为空，子类可覆盖）。"""
        return None

    async def on_result(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        result: ToolResult,
    ) -> None:
        """结果 Hook：已组装 ToolResult 后触发（成功或失败均触发）。"""
        return None

    async def after(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        result: ToolResult,
    ) -> None:
        """收尾 Hook：在 on_result 之后调用，用于清理/审计收口。"""
        return None

    async def on_error(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        exc: Exception,
    ) -> None:
        """异常 Hook：捕获到异常后、组装失败结果前调用。"""
        return None

    async def ainvoke(
        self,
        request: BaseModel,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """框架统一公开入口：Hook + 日志 + 耗时 + 超时 + 重试 + 异常包装。"""
        ctx = context or ToolContext(trace_id=str(uuid.uuid4()))
        rt = runtime or RuntimeDependencies()
        started = time.perf_counter()
        attempt = 0
        last_exc: Exception | None = None

        logger.info(
            "tool.start name={} category={} trace_id={}",
            self.name,
            self.category.value,
            ctx.trace_id,
        )

        try:
            await self.before(request, ctx, rt)
        except Exception as exc:
            logger.exception(
                "tool.before_failed name={} trace_id={} err={}",
                self.name,
                ctx.trace_id,
                exc,
            )
            result = self._failure_result(
                context=ctx,
                attempt=1,
                error=f"before hook failed: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            await self._emit_result_hooks(request, ctx, rt, result)
            return result

        max_attempts = self.max_retries + 1
        while attempt < max_attempts:
            attempt += 1
            try:
                data = await asyncio.wait_for(
                    self._run_execute(request, ctx, rt),
                    timeout=self.timeout_seconds,
                )
                latency_ms = (time.perf_counter() - started) * 1000
                result = ToolResult(
                    success=True,
                    trace_id=ctx.trace_id,
                    data=data,
                    latency_ms=latency_ms,
                    metadata=self._build_metadata(ctx, attempt),
                )
                logger.info(
                    "tool.success name={} trace_id={} attempt={} latency_ms={:.2f}",
                    self.name,
                    ctx.trace_id,
                    attempt,
                    latency_ms,
                )
                await self._emit_result_hooks(request, ctx, rt, result)
                return result
            except TimeoutError as exc:
                last_exc = ToolTimeoutError(
                    f"工具 {self.name} 超时（{self.timeout_seconds}s）"
                )
                last_exc.__cause__ = exc
                logger.warning(
                    "tool.timeout name={} trace_id={} attempt={}",
                    self.name,
                    ctx.trace_id,
                    attempt,
                )
                await self.on_error(request, ctx, rt, last_exc)
            except Exception as exc:
                last_exc = exc if isinstance(exc, ToolError) else ToolError(str(exc))
                if last_exc is not exc:
                    last_exc.__cause__ = exc
                logger.warning(
                    "tool.error name={} trace_id={} attempt={} err={}",
                    self.name,
                    ctx.trace_id,
                    attempt,
                    exc,
                )
                await self.on_error(request, ctx, rt, last_exc)

            if attempt < max_attempts:
                await asyncio.sleep(self.retry_interval_seconds)

        latency_ms = (time.perf_counter() - started) * 1000
        error_msg = str(last_exc) if last_exc else "unknown error"
        if self.max_retries > 0 and last_exc is not None:
            error_msg = f"重试耗尽: {error_msg}"
            last_exc = ToolRetryExhaustedError(error_msg)

        result = self._failure_result(
            context=ctx,
            attempt=attempt,
            error=error_msg,
            latency_ms=latency_ms,
        )
        logger.error(
            "tool.failed name={} trace_id={} attempts={} latency_ms={:.2f} err={}",
            self.name,
            ctx.trace_id,
            attempt,
            latency_ms,
            error_msg,
        )
        await self._emit_result_hooks(request, ctx, rt, result)
        return result

    async def _emit_result_hooks(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        result: ToolResult,
    ) -> None:
        """依次触发 on_result 与 after。"""
        try:
            await self.on_result(request, context, runtime, result)
        except Exception as exc:
            logger.exception(
                "tool.on_result_failed name={} trace_id={} err={}",
                self.name,
                context.trace_id,
                exc,
            )
        try:
            await self.after(request, context, runtime, result)
        except Exception as exc:
            logger.exception(
                "tool.after_failed name={} trace_id={} err={}",
                self.name,
                context.trace_id,
                exc,
            )

    async def _run_execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        """调度 _execute：协程直接 await，同步函数放入线程池。"""
        execute_fn = self._execute
        if inspect.iscoroutinefunction(execute_fn):
            output = await execute_fn(request, context, runtime)
        else:
            output = await asyncio.to_thread(execute_fn, request, context, runtime)

        # 兼容：同步函数误返回 Awaitable 时再 await 一次
        if inspect.isawaitable(output):
            output = await output
        return output

    def _build_metadata(self, context: ToolContext, attempt: int) -> ToolMetadata:
        """组装不可变的结果元数据。"""
        return ToolMetadata(
            tool_name=self.name,
            category=self.category,
            attempt=attempt,
            tags=freeze_str_tags(context.tags),
        )

    def _failure_result(
        self,
        *,
        context: ToolContext,
        attempt: int,
        error: str,
        latency_ms: float,
    ) -> ToolResult:
        """组装失败结果。"""
        return ToolResult(
            success=False,
            trace_id=context.trace_id,
            data=None,
            error=error,
            latency_ms=latency_ms,
            metadata=self._build_metadata(context, attempt),
        )

    @abstractmethod
    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput | Awaitable[ToolOutput]:
        """子类实现业务逻辑：可为 sync 或 async，返回 ToolOutput。"""
