import importlib.util
from pathlib import Path

import pytest

from hexarag_api.services.evaluator import apply_limit, load_level_questions, resolve_question_file, run_evaluation


def load_evaluate_w4_module():
    module_path = Path(__file__).resolve().parents[2] / 'scripts' / 'evaluate_w4.py'
    spec = importlib.util.spec_from_file_location('evaluate_w4_script', module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_parser():
    return load_evaluate_w4_module().build_parser()


class StubResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class StubHttpClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def post(self, url: str, json: dict) -> StubResponse:
        self.calls.append({'url': url, 'json': json})
        return StubResponse(self.payload)

    def close(self) -> None:
        return None

    @property
    def is_closed(self) -> bool:
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def __bool__(self) -> bool:
        return True


class StubClientFactory:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.instances: list[StubHttpClient] = []

    def build(self) -> StubHttpClient:
        client = StubHttpClient(self.payload)
        self.instances.append(client)
        return client

    def __call__(self) -> StubHttpClient:
        return self.build()


_FAKE_CHAT_PAYLOAD = {
    'message': {
        'content': 'Investigation summary',
        'trace': {
            'citations': [],
            'inline_citations': [],
            'tool_calls': [],
            'memory_window': [],
            'grounding_notes': [],
            'uncertainty': None,
            'conflict_resolution': None,
            'runtime': {
                'mode': 'stub',
                'provider': 'test',
                'region': None,
                'agent_id': None,
                'agent_alias_id': None,
                'model': 'stub-model',
            },
            'reasoning': {
                'evidence_types': [],
                'selected_sources': [],
                'tool_basis': [],
                'memory_applied': False,
                'memory_summary': None,
                'uncertainty_reason': None,
                'answer_strategy': 'grounded-answer',
                'runtime_label': 'stub runtime',
                'caveat': None,
                'source_summary': None,
                'tool_summary': None,
                'explanation_summary': None,
                'narrative_focus': 'evidence-synthesis',
                'next_step': None,
                'conflict_summary': None,
            },
        },
    }
}


def test_resolve_question_file_points_to_l1_fixture() -> None:
    path = resolve_question_file('l1')

    assert path == Path('/workspace/W4/questions/student/L1_questions.json')


def test_load_level_questions_reads_l1_fixture() -> None:
    payload = load_level_questions(resolve_question_file('l1'))

    assert payload['level'] == 1
    assert len(payload['questions']) >= 1
    assert payload['questions'][0]['id'].startswith('L1-')


def test_resolve_question_file_points_to_l4_fixture() -> None:
    path = resolve_question_file('l4')

    assert path == Path('/workspace/W4/questions/student/L4_conversation_scripts.json')


def test_resolve_question_file_points_to_l5_fixture() -> None:
    path = resolve_question_file('l5')

    assert path == Path('/workspace/W4/questions/student/L5_investigation_prompts.json')


def test_apply_limit_keeps_requested_prefix() -> None:
    items = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]

    assert apply_limit(items, limit=2) == [{'id': 'a'}, {'id': 'b'}]
    assert apply_limit(items, limit=None) == items


def test_run_evaluation_includes_investigation_results() -> None:
    factory = StubClientFactory(_FAKE_CHAT_PAYLOAD)
    client = factory.build()

    report = run_evaluation(
        api_base_url='https://example.invalid',
        level='l5',
        limit=1,
        client=client,
    )

    assert report['level'] == 'l5'
    assert report['result_count'] == 1
    assert report['results'][0]['id'].startswith('L5-')
    assert report['results'][0]['grading_fit'] == 'unscored'
    assert report['results'][0]['product_quality'] == 'unscored'
    assert report['results'][0]['overall_readiness'] == 'unscored'
    assert report['results'][0]['primary_failure_layer'] is None
    assert report['results'][0]['secondary_failure_layers'] == []
    assert report['results'][0]['evidence_summary'] == ''
    assert report['results'][0]['improvement_insight'] == ''
    assert report['results'][0]['retest_priority'] == 'untriaged'
    assert report['results'][0]['expected_steps']
    assert 'expected_findings' in report['results'][0]
    assert 'data_sources_needed' in report['results'][0]
    assert report['results'][0]['assistant_answer'] == 'Investigation summary'
    assert report['results'][0]['trace'] == _FAKE_CHAT_PAYLOAD['message']['trace']
    assert factory.instances[0].calls[0]['json']['session_id'] == 'eval-l5-l5-01'


def test_cli_parser_requires_output_and_accepts_audit_mode() -> None:
    parser = build_parser()

    args = parser.parse_args([
        '--api-base-url',
        'https://example.invalid',
        '--level',
        'l5',
        '--output',
        'artifacts/audits/report.json',
    ])

    assert args.mode == 'audit'
    assert args.output == Path('artifacts/audits/report.json')

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([
            '--api-base-url',
            'https://example.invalid',
            '--level',
            'l1',
        ])

    assert exc_info.value.code == 2


def test_cli_parser_accepts_replay_mode() -> None:
    parser = build_parser()

    args = parser.parse_args([
        '--api-base-url',
        'https://example.invalid',
        '--level',
        'l3',
        '--mode',
        'replay',
        '--output',
        'artifacts/audits/report.json',
    ])

    assert args.mode == 'replay'
    assert args.level == 'l3'
