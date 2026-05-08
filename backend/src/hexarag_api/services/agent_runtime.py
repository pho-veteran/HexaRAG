import json
from pathlib import PurePosixPath
from typing import Any, Protocol
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

FAILURE_TRIGGER_MESSAGE = 'trigger failure'
_STREAM_FAILURE_KEYS = (
    'accessDeniedException',
    'badGatewayException',
    'conflictException',
    'dependencyFailedException',
    'internalServerException',
    'modelNotReadyException',
    'resourceNotFoundException',
    'serviceQuotaExceededException',
    'throttlingException',
    'validationException',
)


class ChatRuntime(Protocol):
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
        ...


class StubAgentRuntime:
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
        if message in {FAILURE_TRIGGER_MESSAGE, 'What is NotificationSvc status?'}:
            raise RuntimeError('live tool unavailable')

        answer = f'Stub answer for: {message}'
        return {
            'answer': answer,
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-architecture',
                        'title': 'architecture.md',
                        'excerpt': 'Current p95 latency sits below the alert threshold.',
                        'recency_note': 'Stubbed knowledge base note.',
                    }
                ],
                'inline_citations': [
                    {
                        'start': 0,
                        'end': len(answer),
                        'source_ids': ['doc-architecture'],
                    }
                ],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'success',
                        'summary': 'Prepared stub observability data',
                        'input': {'question': message},
                        'output': {'mode': 'stub', 'latency_p95_ms': 185},
                    }
                ],
                'grounding_notes': ['This is a deterministic stub response for the deploy-readiness slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        }


class AgentRuntimeService:
    def __init__(self, agent_id: str, agent_alias_id: str, region: str) -> None:
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.client = boto3.client('bedrock-agent-runtime', region_name=region)

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
        try:
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=_build_input_text(message, memory_window),
                enableTrace=True,
            )
            return _normalize_agent_response(response)
        except (BotoCoreError, ClientError, KeyError, TypeError, ValueError, RuntimeError) as exc:
            raise RuntimeError('Bedrock agent invocation failed.') from exc


def _build_input_text(message: str, memory_window: list[str]) -> str:
    if not memory_window:
        return message

    recent_turns = '\n'.join(f'- {turn}' for turn in memory_window)
    return (
        'Use the recent conversation context only when it helps answer the latest user question.\n\n'
        f'Recent conversation:\n{recent_turns}\n\n'
        f'Latest user question:\n{message}'
    )


def _normalize_agent_response(response: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {
        'answer_parts': [],
        'answer_fallback': None,
        'citations': [],
        'citations_by_source_id': {},
        'inline_citations': [],
        'tool_calls': [],
        'grounding_notes': [],
        'uncertainty': None,
        'conflict_resolution': None,
        'action_inputs_by_trace_id': {},
        'knowledge_base_inputs_by_trace_id': {},
    }

    for event in response['completion']:
        _raise_for_stream_error(event)

        chunk = event.get('chunk')
        if chunk:
            text = _decode_chunk_bytes(chunk.get('bytes'))
            if text:
                state['answer_parts'].append(text)
            _collect_chunk_attribution(chunk.get('attribution') or {}, state)

        trace_part = event.get('trace')
        if trace_part:
            _collect_trace_part(trace_part, state)

    answer = ''.join(state['answer_parts']).strip()
    if not answer:
        answer = (state['answer_fallback'] or '').strip()
    if not answer:
        raise RuntimeError('Bedrock agent returned an empty response.')

    return {
        'answer': answer,
        'trace': {
            'citations': state['citations'],
            'inline_citations': state['inline_citations'],
            'tool_calls': state['tool_calls'],
            'grounding_notes': state['grounding_notes'],
            'uncertainty': state['uncertainty'],
            'conflict_resolution': state['conflict_resolution'],
        },
    }


def _raise_for_stream_error(event: dict[str, Any]) -> None:
    for key in _STREAM_FAILURE_KEYS:
        details = event.get(key)
        if details:
            raise RuntimeError(details.get('message') or f'Bedrock agent stream returned {key}.')


def _collect_chunk_attribution(attribution: dict[str, Any], state: dict[str, Any]) -> None:
    for citation in attribution.get('citations', []):
        generated_part = citation.get('generatedResponsePart', {}).get('textResponsePart', {})
        span = generated_part.get('span') or {}
        source_ids: list[str] = []

        for reference in citation.get('retrievedReferences', []):
            normalized = _normalize_reference(reference)
            source_id = normalized['source_id']
            source_ids.append(source_id)
            if source_id not in state['citations_by_source_id']:
                citation_item = {
                    'source_id': source_id,
                    'title': normalized['title'],
                    'excerpt': normalized['excerpt'],
                    'version': normalized.get('version'),
                    'recency_note': normalized.get('recency_note'),
                }
                state['citations_by_source_id'][source_id] = citation_item
                state['citations'].append(citation_item)

        if source_ids and span.get('start') is not None and span.get('end') is not None:
            state['inline_citations'].append(
                {
                    'start': span['start'],
                    'end': span['end'],
                    'source_ids': source_ids,
                }
            )


def _normalize_reference(reference: dict[str, Any]) -> dict[str, Any]:
    metadata = reference.get('metadata') or {}
    location = reference.get('location') or {}
    excerpt = _extract_excerpt(reference.get('content') or {})
    title = _coerce_string(metadata.get('title')) or _title_from_location(location)
    source_id = (
        _coerce_string(metadata.get('source_id'))
        or _coerce_string(metadata.get('sourceId'))
        or _coerce_string(metadata.get('id'))
        or _location_identifier(location)
        or title
        or excerpt[:80]
        or 'bedrock-reference'
    )

    return {
        'source_id': source_id,
        'title': title or source_id,
        'excerpt': excerpt,
        'version': _coerce_string(metadata.get('version'))
        or _coerce_string(metadata.get('document_version'))
        or _coerce_string(metadata.get('documentVersion')),
        'recency_note': _coerce_string(metadata.get('recency_note'))
        or _coerce_string(metadata.get('recencyNote'))
        or _coerce_string(metadata.get('last_updated'))
        or _coerce_string(metadata.get('lastUpdated'))
        or _coerce_string(metadata.get('published_at')),
    }


def _collect_trace_part(trace_part: dict[str, Any], state: dict[str, Any]) -> None:
    trace = trace_part.get('trace') or {}

    failure_trace = trace.get('failureTrace')
    if failure_trace:
        state['uncertainty'] = failure_trace.get('failureReason') or state['uncertainty']

    guardrail_trace = trace.get('guardrailTrace')
    if guardrail_trace and guardrail_trace.get('action'):
        _append_unique(state['grounding_notes'], f"Guardrail action: {guardrail_trace['action']}")

    for key in ('orchestrationTrace', 'customOrchestrationTrace'):
        trace_value = trace.get(key)
        if trace_value:
            _collect_execution_trace(trace_value, state)


def _collect_execution_trace(trace_value: dict[str, Any], state: dict[str, Any]) -> None:
    rationale = trace_value.get('rationale') or {}
    rationale_text = _coerce_string(rationale.get('text'))
    if rationale_text:
        _append_unique(state['grounding_notes'], rationale_text)

    invocation_input = trace_value.get('invocationInput') or {}
    trace_id = _coerce_string(invocation_input.get('traceId'))
    action_input = invocation_input.get('actionGroupInvocationInput') or {}
    knowledge_base_input = invocation_input.get('knowledgeBaseLookupInput') or {}

    if trace_id and action_input:
        state['action_inputs_by_trace_id'][trace_id] = _normalize_action_input(action_input)
    if trace_id and knowledge_base_input:
        state['knowledge_base_inputs_by_trace_id'][trace_id] = {
            'knowledge_base_id': knowledge_base_input.get('knowledgeBaseId'),
            'query': knowledge_base_input.get('text'),
        }

    observation = trace_value.get('observation') or {}
    observation_type = observation.get('type')
    observation_trace_id = _coerce_string(observation.get('traceId'))

    final_response = observation.get('finalResponse') or {}
    final_text = _coerce_string(final_response.get('text'))
    if final_text:
        state['answer_fallback'] = final_text

    action_output = observation.get('actionGroupInvocationOutput') or {}
    if action_output:
        normalized_input = state['action_inputs_by_trace_id'].get(observation_trace_id or '', {})
        tool_name = (
            normalized_input.get('function')
            or normalized_input.get('api_path')
            or normalized_input.get('action_group_name')
            or 'action_group'
        )
        state['tool_calls'].append(
            {
                'name': tool_name,
                'status': 'success',
                'summary': f'{tool_name} returned data.',
                'input': normalized_input,
                'output': _parse_tool_output(action_output.get('text')),
            }
        )

    knowledge_base_output = observation.get('knowledgeBaseLookupOutput') or {}
    if knowledge_base_output:
        refs = knowledge_base_output.get('retrievedReferences', [])
        kb_input = state['knowledge_base_inputs_by_trace_id'].get(observation_trace_id or '', {})
        kb_id = kb_input.get('knowledge_base_id') or 'the knowledge base'
        _append_unique(state['grounding_notes'], f'Retrieved {len(refs)} references from {kb_id}.')
        query = _coerce_string(kb_input.get('query'))
        if query:
            _append_unique(state['grounding_notes'], f'Knowledge base query: {query}')

    if observation_type == 'ASK_USER':
        state['uncertainty'] = state['uncertainty'] or 'The agent needs more information to answer confidently.'
    if observation_type == 'REPROMPT':
        state['uncertainty'] = state['uncertainty'] or 'The agent had to reprompt because the available context was incomplete.'


def _normalize_action_input(action_input: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    if action_input.get('actionGroupName'):
        normalized['action_group_name'] = action_input['actionGroupName']
    if action_input.get('function'):
        normalized['function'] = action_input['function']
    if action_input.get('apiPath'):
        normalized['api_path'] = action_input['apiPath']
    if action_input.get('verb'):
        normalized['verb'] = action_input['verb']
    if action_input.get('parameters'):
        normalized['parameters'] = action_input['parameters']
    if action_input.get('requestBody'):
        normalized['request_body'] = action_input['requestBody']
    if action_input.get('executionType'):
        normalized['execution_type'] = action_input['executionType']
    return normalized


def _parse_tool_output(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {'text': value}
        return parsed if isinstance(parsed, dict) else {'value': parsed}
    return {'value': value}


def _extract_excerpt(content: dict[str, Any]) -> str:
    text = _coerce_string(content.get('text'))
    if text:
        return text
    row = content.get('row')
    if row is not None:
        return json.dumps(row, ensure_ascii=False)
    byte_content = _coerce_string(content.get('byteContent'))
    if byte_content:
        return byte_content
    return ''


def _location_identifier(location: dict[str, Any]) -> str | None:
    location_value = _first_location_value(location)
    if location_value:
        return location_value
    return _coerce_string(location.get('type'))


def _title_from_location(location: dict[str, Any]) -> str | None:
    location_value = _first_location_value(location)
    if not location_value:
        return None
    parsed = urlparse(location_value)
    path = parsed.path or location_value
    name = PurePosixPath(path.rstrip('/')).name
    return name or location_value


def _first_location_value(location: dict[str, Any]) -> str | None:
    for key in (
        's3Location',
        'webLocation',
        'confluenceLocation',
        'salesforceLocation',
        'sharePointLocation',
        'customDocumentLocation',
        'kendraDocumentLocation',
        'sqlLocation',
    ):
        value = location.get(key)
        if isinstance(value, dict):
            for nested_key in ('uri', 'url', 'id', 'documentId', 'query'):
                nested_value = _coerce_string(value.get(nested_key))
                if nested_value:
                    return nested_value
    return None


def _decode_chunk_bytes(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        return value.decode('utf-8')
    if isinstance(value, str):
        return value
    return ''


def _coerce_string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
