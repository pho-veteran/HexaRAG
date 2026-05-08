from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'HexaRAG API'
    allowed_origins: str = 'http://localhost:5173'
    runtime_mode: Literal['stub', 'aws'] = 'stub'
    aws_region: str = 'us-east-1'
    database_url: str = 'postgresql://hexarag:hexarag@postgres:5432/hexarag'
    session_table_name: str = 'hexarag-sessions'
    monitoring_base_url: str = 'http://backend:8001'
    w4_data_root: str = '/workspace/W4/data_package'
    knowledge_base_id: str = ''
    knowledge_base_data_source_id: str = ''
    agent_id: str = ''
    agent_alias_id: str = ''
    failure_message: str = 'Could not complete the live tool step. Here is the best grounded fallback available right now.'
    recent_turn_limit: int = 6

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
