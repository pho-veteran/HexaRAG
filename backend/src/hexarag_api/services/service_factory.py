from functools import lru_cache

from hexarag_api.config import get_settings
from hexarag_api.services.agent_runtime import AgentRuntimeService, StubAgentRuntime
from hexarag_api.services.chat_service import ChatService
from hexarag_api.services.session_store import SessionStore, build_session_table


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    runtime = (
        AgentRuntimeService(settings.agent_id, settings.agent_alias_id, settings.aws_region)
        if settings.runtime_mode == 'aws'
        else StubAgentRuntime()
    )
    session_store = SessionStore(build_session_table(settings))
    return ChatService(
        session_store=session_store,
        runtime=runtime,
        recent_turn_limit=settings.recent_turn_limit,
        failure_message=settings.failure_message,
    )
