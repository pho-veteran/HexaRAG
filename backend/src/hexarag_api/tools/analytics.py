from collections.abc import Mapping


Q1_DATE_START = '2026-01-01'
Q1_DATE_END = '2026-03-31'
SEVERITY_BY_RANK = {1: 'P1', 2: 'P2', 3: 'P3'}


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


def fetch_sla_target(connection, service: str) -> Mapping[str, float | str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                MAX(CASE WHEN metric = 'latency_p99_ms' THEN target END),
                MAX(CASE WHEN metric = 'error_rate_percent' THEN target END)
            FROM sla_targets
            WHERE service = %s
            """,
            (service,),
        )
        latency_p99_ms, error_rate_percent = cursor.fetchone()

    return {
        'service': service,
        'latency_p99_ms': latency_p99_ms,
        'error_rate_percent': error_rate_percent,
    }


def fetch_q1_average_latency(connection, service: str) -> Mapping[str, float | str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(AVG(latency_p99_ms), 0)
            FROM daily_metrics
            WHERE service = %s AND date BETWEEN %s AND %s
            """,
            (service, Q1_DATE_START, Q1_DATE_END),
        )
        average_latency_p99_ms = cursor.fetchone()[0]

    return {
        'service': service,
        'average_latency_p99_ms': average_latency_p99_ms,
    }


def fetch_q1_incident_summary(connection, service: str | None = None) -> Mapping[str, int | str | None]:
    query = """
        SELECT
            COUNT(*),
            COALESCE(SUM(duration_minutes), 0),
            MIN(
                CASE severity
                    WHEN 'P1' THEN 1
                    WHEN 'P2' THEN 2
                    WHEN 'P3' THEN 3
                    ELSE NULL
                END
            )
        FROM incidents
        WHERE date BETWEEN %s AND %s
    """
    params: tuple[str, ...] | tuple[str, str, str]
    if service is None:
        params = (Q1_DATE_START, Q1_DATE_END)
    else:
        query += ' AND service = %s'
        params = (Q1_DATE_START, Q1_DATE_END, service)

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        incident_count, total_duration_minutes, highest_severity_rank = cursor.fetchone()

    return {
        'service': service or 'all',
        'incident_count': incident_count,
        'total_duration_minutes': total_duration_minutes,
        'highest_severity': SEVERITY_BY_RANK.get(highest_severity_rank),
    }
