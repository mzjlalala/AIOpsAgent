"""Tool 层异常定义。"""

from __future__ import annotations


class ToolError(Exception):
    """工具执行相关的基础异常。"""


class ToolTimeoutError(ToolError):
    """工具执行超时。"""


class ToolRetryExhaustedError(ToolError):
    """重试次数耗尽。"""


class ToolAlreadyRegisteredError(ToolError):
    """工具名称重复注册。"""


class ToolNotFoundError(ToolError):
    """Registry 中未找到指定工具。"""
