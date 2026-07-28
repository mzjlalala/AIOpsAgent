"""Loguru 日志配置。"""

from __future__ import annotations

import sys

from loguru import logger

from app.config.settings import AppEnv, Settings


def setup_logging(settings: Settings) -> None:
    """按环境配置 Loguru 输出。

    开发环境使用可读彩色格式；测试/生产使用便于采集的紧凑格式。
    """
    logger.remove()

    if settings.app_env == AppEnv.DEV:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    else:
        log_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )

    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=log_format,
        enqueue=True,
        backtrace=settings.is_dev,
        diagnose=settings.is_dev,
    )
    logger.info(
        "Logging initialized | env={} level={}",
        settings.app_env.value,
        settings.log_level.upper(),
    )
