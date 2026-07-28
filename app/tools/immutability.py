"""不可变辅助函数。"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


def freeze_str_tags(value: object | None = None) -> Mapping[str, str]:
    """将标签深拷贝为不可变 Mapping。

    - 对入参 ``dict`` 先 ``dict(...)`` 拷贝，再包 ``MappingProxyType``，
      避免外部继续修改原 dict 影响已构造对象。
    - ``MappingProxyType`` 自身禁止 ``__setitem__``。
    """
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise TypeError("tags 必须是 Mapping[str, str]")
    copied: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise TypeError("tags 仅允许 str -> str")
        copied[key] = item
    return MappingProxyType(copied)
