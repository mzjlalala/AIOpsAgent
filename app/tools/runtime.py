"""工具运行期依赖注入容器。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RuntimeDependencies:
    """运行期依赖容器（非 Pydantic，不进入 Trace 序列化）。

    后续阶段可在此扩展 db_session、http_client、settings 等。
    本阶段提供 ``extensions`` 作为扩展槽，禁止把依赖塞进 ToolContext。
    """

    extensions: dict[str, object] = field(default_factory=dict)

    def get(self, key: str, default: object | None = None) -> object | None:
        """读取扩展依赖。"""
        return self.extensions.get(key, default)

    def require(self, key: str) -> object:
        """读取必需扩展依赖；缺失时抛 KeyError。"""
        if key not in self.extensions:
            raise KeyError(f"缺少运行时依赖: {key}")
        return self.extensions[key]
