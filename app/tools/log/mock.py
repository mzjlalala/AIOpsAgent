"""日志 Mock 工具：返回确定性内存假数据。"""

from __future__ import annotations

from pydantic import BaseModel

from app.tools.context import ToolContext
from app.tools.exceptions import ToolError
from app.tools.log.base import BaseLogTool, LogSearchQuery
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolOutput


class MockLogTool(BaseLogTool):
    """Mock 日志工具（不访问真实 SLS/ELK/Loki）。"""

    name = "mock.log"
    description = "返回确定性假日志事件，用于本地联调与测试。"
    timeout_seconds = 5.0

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        """按服务名与关键词返回固定日志行。"""
        _ = runtime
        if not isinstance(request, LogSearchQuery):
            raise ToolError(f"不支持的日志请求类型: {type(request).__name__}")

        keyword = request.keyword or "error"
        events = [
            {
                "ts": request.start.isoformat(),
                "level": "ERROR",
                "message": f"[{request.service}] mock {keyword} event #1",
                "fields": {"service": request.service, **dict(request.filters)},
            },
            {
                "ts": request.end.isoformat(),
                "level": "WARN",
                "message": f"[{request.service}] mock {keyword} event #2",
                "fields": {"service": request.service, **dict(request.filters)},
            },
        ]
        limited = events[: request.limit]
        return {
            "service": request.service,
            "total": len(limited),
            "events": limited,
            "trace_id": context.trace_id,
            "mock": True,
        }
