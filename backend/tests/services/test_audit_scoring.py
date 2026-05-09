import json

from hexarag_api.services.audit_scoring import AUDIT_TAXONOMY, build_unscored_result, score_single_turn_result
from hexarag_api.services.evaluator import run_evaluation


class _StubResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class _StubClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, json: dict[str, object]) -> _StubResponse:
        self.calls.append({'url': url, 'json': json})
        return _StubResponse(self._payload)


def test_audit_taxonomy_exposes_unscored_baseline() -> None:
    assert AUDIT_TAXONOMY['version'] == 'w4-live-audit-v1'
    assert AUDIT_TAXONOMY['score_values'] == ['pass', 'partial', 'fail', 'unscored']
    assert AUDIT_TAXONOMY['retest_priorities'] == ['untriaged']
    assert 'backend_runtime_or_trace_shaping' in AUDIT_TAXONOMY['failure_layers']


def test_build_unscored_result_returns_task_1_shape() -> None:
    result = build_unscored_result()

    assert result == {
        'grading_fit': 'unscored',
        'product_quality': 'unscored',
        'overall_readiness': 'unscored',
        'primary_failure_layer': None,
        'secondary_failure_layers': [],
        'evidence_summary': '',
        'improvement_insight': '',
        'retest_priority': 'untriaged',
    }


def test_score_single_turn_result_flags_missing_citations_for_l1() -> None:
    result = score_single_turn_result(
        level='l1',
        answer='The policy says deploy on Tuesdays.',
        trace={'citations': [], 'tool_calls': [], 'memory_window': []},
        expected_answer='Deployments happen on Tuesdays.',
    )

    assert result['grading_fit'] == 'partial'
    assert result['product_quality'] == 'fail'
    assert result['overall_readiness'] == 'fail'
    assert result['primary_failure_layer'] == 'backend_runtime_or_trace_shaping'


def test_score_single_turn_result_passes_l1_with_citations() -> None:
    result = score_single_turn_result(
        level='l1',
        answer='Deployments happen on Tuesdays.',
        trace={
            'citations': [
                {
                    'source_id': 'doc-1',
                    'title': 'Deployment Policy',
                    'excerpt': 'Deployments happen on Tuesdays.',
                }
            ],
            'tool_calls': [],
            'memory_window': [],
        },
        expected_answer='Deployments happen on Tuesdays.',
    )

    assert result['grading_fit'] == 'pass'
    assert result['product_quality'] == 'pass'
    assert result['overall_readiness'] == 'pass'
    assert result['primary_failure_layer'] is None


def test_run_evaluation_attaches_scored_l1_results(tmp_path) -> None:
    questions_root = tmp_path
    questions_root.joinpath('L1_questions.json').write_text(
        json.dumps(
            {
                'description': 'Single-turn audit sample',
                'questions': [
                    {
                        'id': 'L1-01',
                        'question': 'When do deployments happen?',
                        'expected_answer': 'Deployments happen on Tuesdays.',
                    }
                ],
            }
        ),
        encoding='utf-8',
    )
    client = _StubClient(
        {
            'message': {
                'content': 'The policy says deploy on Tuesdays.',
                'trace': {'citations': [], 'tool_calls': [], 'memory_window': []},
            }
        }
    )

    report = run_evaluation(
        api_base_url='https://example.invalid',
        level='l1',
        questions_root=questions_root,
        limit=1,
        client=client,
    )

    assert report['results'][0]['grading_fit'] == 'partial'
    assert report['results'][0]['product_quality'] == 'fail'
    assert report['results'][0]['overall_readiness'] == 'fail'
    assert report['results'][0]['primary_failure_layer'] == 'backend_runtime_or_trace_shaping'
    assert client.calls[0]['json'] == {
        'session_id': 'eval-l1-l1-01',
        'message': 'When do deployments happen?',
    }
