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
