from hexarag_api.services.ui_audit_matrix import select_ui_cases


def test_select_ui_cases_keeps_high_risk_cases_per_level() -> None:
    cases = select_ui_cases()

    ids = {case['id'] for case in cases}

    assert 'L1-01' in ids
    assert 'L2-01' in ids
    assert 'L3-04' in ids
    assert 'L4-01' in ids
    assert 'L5-01' in ids
