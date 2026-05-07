from collections.abc import Mapping


def summarize_q1_costs(connection) -> Mapping[str, int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(SUM(total_cost), 0)
            FROM monthly_costs
            WHERE month IN ('2026-01', '2026-02', '2026-03')
            """
        )
        total_cost = cursor.fetchone()[0]

    return {'total_cost': total_cost}
