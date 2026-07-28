"""从环境变量加载的应用配置。"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    """支持的部署环境。"""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class Settings(BaseSettings):
    """OpsAgent 统一配置入口。

    从环境变量与可选 ``.env`` 读取。业务代码应依赖本对象，
    禁止直接读取 ``os.environ``。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="OpsAgent", description="服务显示名称。")
    app_env: AppEnv = Field(default=AppEnv.DEV, description="运行环境。")
    log_level: str = Field(default="INFO", description="Loguru 日志级别。")
    api_host: str = Field(default="0.0.0.0", description="Uvicorn 监听地址。")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Uvicorn 端口。")
    api_debug: bool = Field(
        default=False,
        description="是否开启 FastAPI debug（仅建议开发环境）。",
    )

    database_url: str = Field(
        default="mysql+asyncmy://opsagent:opsagent@127.0.0.1:3306/opsagent",
        description="异步 SQLAlchemy 数据库连接串。",
    )
    database_url_sync: str | None = Field(
        default=None,
        description="Alembic 同步连接串；为空时由 database_url 推导。",
    )
    database_echo: bool = Field(
        default=False,
        description="是否将 SQL 语句输出到日志。",
    )

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def _empty_sync_url_to_none(cls, value: object) -> object:
        """空字符串视为未配置。"""
        if value == "":
            return None
        return value

    @property
    def is_dev(self) -> bool:
        """是否为开发环境。"""
        return self.app_env == AppEnv.DEV

    @property
    def is_prod(self) -> bool:
        """是否为生产环境。"""
        return self.app_env == AppEnv.PROD

    def resolved_database_url_sync(self) -> str:
        """解析 Alembic 使用的同步数据库 URL。"""
        if self.database_url_sync:
            return self.database_url_sync
        return self.database_url.replace(
            "mysql+asyncmy://", "mysql+pymysql://", 1
        ).replace("sqlite+aiosqlite://", "sqlite://", 1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回进程级缓存的 Settings 实例。"""
    return Settings()
