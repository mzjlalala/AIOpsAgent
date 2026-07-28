"""执行类 Mock 工具：永远不修改真实环境。"""

from __future__ import annotations

from loguru import logger
from pydantic import BaseModel

from app.tools.context import ToolContext
from app.tools.exceptions import ToolError
from app.tools.executor.base import BaseExecutorTool, ExecuteRequest
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolOutput


class MockExecutorTool(BaseExecutorTool):
    """Mock 执行工具。

    - ``simulated`` 恒为 True
    - ``applied`` 恒为 False（永不落真实操作）
    """

    name = "mock.executor"
    description = "模拟执行运维动作，禁止修改真实环境。"
    timeout_seconds = 5.0

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        """仅返回模拟计划与结果，绝不调用 K8s/SSH/Docker。"""
        _ = runtime
        if not isinstance(request, ExecuteRequest):
            raise ToolError(f"不支持的执行请求类型: {type(request).__name__}")

        if not request.dry_run:
            logger.warning(
                "mock.executor 收到 dry_run=False，仍只做模拟，不修改真实环境 | "
                "action={} target={} trace_id={}",
                request.action,
                request.target,
                context.trace_id,
            )

        plan = (
            f"simulate {request.action} on {request.target} "
            f"with params={dict(request.params)}"
        )
        return {
            "action": request.action,
            "target": request.target,
            "params": dict(request.params),
            "dry_run": request.dry_run,
            "simulated": True,
            "applied": False,
            "plan": plan,
            "trace_id": context.trace_id,
            "mock": True,
        }
