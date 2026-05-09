AUDIT_TAXONOMY = {
    'version': 'w4-live-audit-v1',
    'score_values': ['pass', 'partial', 'fail', 'unscored'],
    'retest_priorities': ['untriaged'],
    'failure_layers': [
        'agent_instruction_or_behavior',
        'knowledge_base_content_or_ingestion',
        'structured_data_coverage',
        'monitoring_or_tool_coverage',
        'backend_runtime_or_trace_shaping',
        'session_memory_behavior',
        'frontend_rendering_or_interaction',
        'aws_runtime_or_configuration',
        'evaluation_or_scoring_gap',
    ],
}


def build_unscored_result() -> dict[str, object]:
    return {
        'grading_fit': 'unscored',
        'product_quality': 'unscored',
        'overall_readiness': 'unscored',
        'primary_failure_layer': None,
        'secondary_failure_layers': [],
        'evidence_summary': '',
        'improvement_insight': '',
        'retest_priority': 'untriaged',
    }


def score_single_turn_result(
    level: str,
    answer: str,
    trace: dict[str, object],
    expected_answer: str,
) -> dict[str, object]:
    scored = build_unscored_result()
    normalized_level = level.lower()
    has_citations = bool(trace.get('citations'))

    if normalized_level == 'l1' and has_citations:
        scored['grading_fit'] = 'pass'
        scored['product_quality'] = 'pass'
        scored['overall_readiness'] = 'pass'
        scored['evidence_summary'] = 'L1 answer included at least one citation.'
        scored['improvement_insight'] = 'Maintain citation coverage for single-document retrieval answers.'
    elif normalized_level == 'l1':
        scored['grading_fit'] = 'partial'
        scored['product_quality'] = 'fail'
        scored['overall_readiness'] = 'fail'
        scored['primary_failure_layer'] = 'backend_runtime_or_trace_shaping'
        scored['evidence_summary'] = 'L1 answer was returned without citations.'
        scored['improvement_insight'] = 'Ensure L1 retrieval answers surface citations in the trace.'

    return scored
