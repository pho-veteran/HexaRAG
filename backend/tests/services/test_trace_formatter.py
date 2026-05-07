from hexarag_api.services.trace_formatter import build_trace_payload


def test_build_trace_payload_surfaces_conflict_resolution():
    raw = {
        'citations': [{'sourceId': 'api_reference_v2.md', 'title': 'api_reference_v2.md', 'excerpt': '1000 rpm'}],
        'conflict_resolution': {
            'chosen_source': 'api_reference_v2.md',
            'rationale': 'v2 supersedes archived v1',
            'competing_sources': ['api_reference_v1_archived.md'],
        },
    }

    trace = build_trace_payload(raw, memory_window=['What is the PaymentGW rate limit?'])
    assert trace.conflict_resolution.chosen_source == 'api_reference_v2.md'
    assert trace.memory_window == ['What is the PaymentGW rate limit?']


def test_build_trace_payload_orders_citations_by_first_inline_appearance() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
            {'sourceId': 'doc-escalation', 'title': 'escalation.md', 'excerpt': 'Escalation excerpt'},
        ],
        'inline_citations': [
            {'start': 32, 'end': 61, 'source_ids': ['doc-escalation']},
            {'start': 0, 'end': 31, 'source_ids': ['doc-ownership']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership', 'doc-escalation']
    assert trace.inline_citations[0].source_ids == ['doc-ownership']
    assert trace.inline_citations[1].source_ids == ['doc-escalation']


def test_build_trace_payload_reuses_sources_and_keeps_multi_source_order() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
            {'sourceId': 'doc-escalation', 'title': 'escalation.md', 'excerpt': 'Escalation excerpt'},
        ],
        'inline_citations': [
            {'start': 0, 'end': 24, 'source_ids': ['doc-ownership']},
            {'start': 25, 'end': 56, 'source_ids': ['doc-ownership', 'doc-escalation']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership', 'doc-escalation']
    assert trace.inline_citations[1].source_ids == ['doc-ownership', 'doc-escalation']


def test_build_trace_payload_drops_inline_anchors_for_unknown_sources() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
        ],
        'inline_citations': [
            {'start': 0, 'end': 24, 'source_ids': ['doc-unknown']},
            {'start': 25, 'end': 56, 'source_ids': ['doc-ownership']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership']
    assert len(trace.inline_citations) == 1
    assert trace.inline_citations[0].source_ids == ['doc-ownership']
