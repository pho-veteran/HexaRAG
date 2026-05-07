from hexarag_api.tools.analytics import summarize_q1_costs


def test_summarize_q1_costs_returns_expected_total(fake_db_connection):
    result = summarize_q1_costs(fake_db_connection)
    assert result['total_cost'] == 56350
