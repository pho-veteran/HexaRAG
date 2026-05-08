from hexarag_api.config import Settings
from hexarag_api.services.agent_runtime import AgentRuntimeService
from hexarag_api.services.chat_service import ChatService
from hexarag_api.services.session_store import InMemorySessionTable, SessionStore, build_session_table


class FakeRuntime:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, str, list[str]]] = []

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        self.calls.append((session_id, message, memory_window))
        if self.should_fail:
            raise RuntimeError('live tool unavailable')

        return {
            'answer': f'AWS-mode answer for: {message}',
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-ops',
                        'title': 'ops.md',
                        'excerpt': 'Operational ownership details.',
                    }
                ],
                'tool_calls': [],
                'grounding_notes': ['Returned from the fake runtime.'],
                'uncertainty': None,
            },
        }


class FakeDynamoResource:
    def __init__(self) -> None:
        self.requested_tables: list[str] = []

    def Table(self, table_name: str):
        self.requested_tables.append(table_name)
        return object()


class FakeAgentClient:
    def __init__(self, events: list[dict]) -> None:
        self.events = events
        self.calls: list[dict] = []

    def invoke_agent(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {'completion': iter(self.events)}


def test_chat_service_persists_turns_and_passes_memory_window() -> None:
    table = InMemorySessionTable()
    session_store = SessionStore(table)
    session_store.append_turns('memory-session', 'Who owns Notifications?', 'Team Mercury owns Notifications.')
    runtime = FakeRuntime()
    service = ChatService(
        session_store=session_store,
        runtime=runtime,
        recent_turn_limit=6,
        failure_message='fallback',
    )

    response = service.answer('memory-session', 'What is PaymentGW latency?')

    assert response.message.content == 'AWS-mode answer for: What is PaymentGW latency?'
    assert runtime.calls == [
        (
            'memory-session',
            'What is PaymentGW latency?',
            ['Who owns Notifications?', 'Team Mercury owns Notifications.'],
        )
    ]
    assert session_store.load_recent_turns('memory-session', limit=4) == [
        'Who owns Notifications?',
        'Team Mercury owns Notifications.',
        'What is PaymentGW latency?',
        'AWS-mode answer for: What is PaymentGW latency?',
    ]


def test_chat_service_returns_grounded_fallback_when_runtime_raises() -> None:
    service = ChatService(
        session_store=SessionStore(InMemorySessionTable()),
        runtime=FakeRuntime(should_fail=True),
        recent_turn_limit=6,
        failure_message='Could not complete the live tool step. Here is the best grounded fallback available right now.',
    )

    response = service.answer('fallback-session', 'What is NotificationSvc status?')

    assert 'could not complete the live tool step' in response.message.content.lower()
    assert response.message.trace.citations == []
    assert response.message.trace.tool_calls[0].status == 'error'
    assert response.message.trace.uncertainty == 'Live monitoring data is temporarily unavailable.'


def test_build_session_table_uses_dynamodb_in_aws_mode(monkeypatch) -> None:
    fake_resource = FakeDynamoResource()

    class FakeBoto3:
        @staticmethod
        def resource(service_name: str, region_name: str):
            assert service_name == 'dynamodb'
            assert region_name == 'us-east-1'
            return fake_resource

    monkeypatch.setattr('hexarag_api.services.session_store.boto3', FakeBoto3)

    table = build_session_table(
        Settings(runtime_mode='aws', aws_region='us-east-1', session_table_name='hexarag-sessions')
    )

    assert table.__class__.__name__ == 'DynamoSessionTable'
    assert fake_resource.requested_tables == ['hexarag-sessions']


def test_agent_runtime_service_normalizes_bedrock_agent_response(monkeypatch) -> None:
    answer_text = 'PaymentGW is healthy.[1]'
    events = [
        {
            'trace': {
                'trace': {
                    'orchestrationTrace': {
                        'rationale': {'text': 'I checked the monitoring action before answering.'},
                        'invocationInput': {
                            'traceId': 'action-1',
                            'actionGroupInvocationInput': {
                                'actionGroupName': 'MonitoringTools',
                                'function': 'get_service_metrics',
                                'apiPath': '/metrics/PaymentGW',
                                'verb': 'GET',
                                'parameters': [{'name': 'service_name', 'value': 'PaymentGW'}],
                            },
                        },
                    }
                }
            }
        },
        {
            'trace': {
                'trace': {
                    'orchestrationTrace': {
                        'observation': {
                            'traceId': 'action-1',
                            'type': 'ACTION_GROUP',
                            'actionGroupInvocationOutput': {
                                'text': '{"latency_p95_ms": 182, "error_rate": 0.002}'
                            },
                        }
                    }
                }
            }
        },
        {
            'chunk': {
                'bytes': answer_text.encode('utf-8'),
                'attribution': {
                    'citations': [
                        {
                            'generatedResponsePart': {
                                'textResponsePart': {
                                    'span': {'start': 0, 'end': len(answer_text)},
                                    'text': answer_text,
                                }
                            },
                            'retrievedReferences': [
                                {
                                    'content': {'text': 'PaymentGW p95 is below the alert threshold.'},
                                    'location': {'s3Location': {'uri': 's3://hexarag-kb/runbooks/paymentgw.md'}},
                                    'metadata': {
                                        'title': 'paymentgw.md',
                                        'source_id': 'doc-paymentgw',
                                        'version': 'v3',
                                        'recency_note': 'Updated 2026-05-01',
                                    },
                                }
                            ],
                        }
                    ]
                },
            }
        },
        {
            'trace': {
                'trace': {
                    'orchestrationTrace': {
                        'observation': {
                            'type': 'KNOWLEDGE_BASE',
                            'traceId': 'kb-1',
                            'knowledgeBaseLookupOutput': {
                                'retrievedReferences': [
                                    {
                                        'content': {'text': 'PaymentGW owner is Team Mercury.'},
                                        'location': {'s3Location': {'uri': 's3://hexarag-kb/runbooks/paymentgw.md'}},
                                    }
                                ]
                            },
                        },
                        'invocationInput': {
                            'traceId': 'kb-1',
                            'knowledgeBaseLookupInput': {
                                'knowledgeBaseId': 'KB12345678',
                                'text': 'PaymentGW status and ownership',
                            },
                        },
                    }
                }
            }
        },
    ]
    fake_client = FakeAgentClient(events)

    class FakeBoto3:
        @staticmethod
        def client(service_name: str, region_name: str):
            assert service_name == 'bedrock-agent-runtime'
            assert region_name == 'us-east-1'
            return fake_client

    monkeypatch.setattr('hexarag_api.services.agent_runtime.boto3', FakeBoto3)

    runtime = AgentRuntimeService('AGENT123456', 'ALIAS12345', 'us-east-1')
    response = runtime.answer('session-1', 'How is PaymentGW doing?', ['Prior question', 'Prior answer'])

    assert response['answer'] == answer_text
    assert response['trace']['citations'] == [
        {
            'source_id': 'doc-paymentgw',
            'title': 'paymentgw.md',
            'excerpt': 'PaymentGW p95 is below the alert threshold.',
            'version': 'v3',
            'recency_note': 'Updated 2026-05-01',
        }
    ]
    assert response['trace']['inline_citations'] == [
        {'start': 0, 'end': len(answer_text), 'source_ids': ['doc-paymentgw']}
    ]
    assert response['trace']['tool_calls'] == [
        {
            'name': 'get_service_metrics',
            'status': 'success',
            'summary': 'get_service_metrics returned data.',
            'input': {
                'action_group_name': 'MonitoringTools',
                'function': 'get_service_metrics',
                'api_path': '/metrics/PaymentGW',
                'verb': 'GET',
                'parameters': [{'name': 'service_name', 'value': 'PaymentGW'}],
            },
            'output': {'latency_p95_ms': 182, 'error_rate': 0.002},
        }
    ]
    assert response['trace']['grounding_notes'] == [
        'I checked the monitoring action before answering.',
        'Retrieved 1 references from KB12345678.',
        'Knowledge base query: PaymentGW status and ownership',
    ]
    assert response['trace']['uncertainty'] is None
    assert fake_client.calls == [
        {
            'agentId': 'AGENT123456',
            'agentAliasId': 'ALIAS12345',
            'sessionId': 'session-1',
            'inputText': 'Use the recent conversation context only when it helps answer the latest user question.\n\nRecent conversation:\n- Prior question\n- Prior answer\n\nLatest user question:\nHow is PaymentGW doing?',
            'enableTrace': True,
        }
    ]


def test_agent_runtime_service_raises_on_stream_error(monkeypatch) -> None:
    fake_client = FakeAgentClient([
        {'dependencyFailedException': {'message': 'Monitoring action failed.'}},
    ])

    class FakeBoto3:
        @staticmethod
        def client(service_name: str, region_name: str):
            assert service_name == 'bedrock-agent-runtime'
            assert region_name == 'us-east-1'
            return fake_client

    monkeypatch.setattr('hexarag_api.services.agent_runtime.boto3', FakeBoto3)

    runtime = AgentRuntimeService('AGENT123456', 'ALIAS12345', 'us-east-1')

    try:
        runtime.answer('session-1', 'How is PaymentGW doing?', [])
    except RuntimeError as exc:
        assert str(exc) == 'Bedrock agent invocation failed.'
    else:
        raise AssertionError('Expected Bedrock runtime failure to raise RuntimeError.')
