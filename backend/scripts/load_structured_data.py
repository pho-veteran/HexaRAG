import argparse
import csv
from pathlib import Path

import psycopg

from hexarag_api.config import Settings


def load_monthly_costs(data_root: Path, connection) -> None:
    csv_path = data_root / 'structured_data' / 'monthly_costs.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        with connection.cursor() as cursor:
            for row in reader:
                cursor.execute(
                    'INSERT INTO monthly_costs (service, month, compute_cost, storage_cost, network_cost, third_party_cost, total_cost) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (service, month) DO UPDATE SET compute_cost = EXCLUDED.compute_cost, storage_cost = EXCLUDED.storage_cost, network_cost = EXCLUDED.network_cost, third_party_cost = EXCLUDED.third_party_cost, total_cost = EXCLUDED.total_cost',
                    (
                        row['service'],
                        row['month'],
                        row['compute_cost'],
                        row['storage_cost'],
                        row['network_cost'],
                        row['third_party_cost'],
                        row['total_cost'],
                    ),
                )


def load_incidents(data_root: Path, connection) -> None:
    csv_path = data_root / 'structured_data' / 'incidents.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        with connection.cursor() as cursor:
            for row in reader:
                cursor.execute(
                    'INSERT INTO incidents (incident_id, service, date, severity, duration_minutes, root_cause, resolution, team_responsible, reported_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (incident_id) DO UPDATE SET service = EXCLUDED.service, date = EXCLUDED.date, severity = EXCLUDED.severity, duration_minutes = EXCLUDED.duration_minutes, root_cause = EXCLUDED.root_cause, resolution = EXCLUDED.resolution, team_responsible = EXCLUDED.team_responsible, reported_by = EXCLUDED.reported_by',
                    (
                        row['incident_id'],
                        row['service'],
                        row['date'],
                        row['severity'],
                        row['duration_minutes'],
                        row['root_cause'],
                        row['resolution'],
                        row['team_responsible'],
                        row['reported_by'],
                    ),
                )


def load_sla_targets(data_root: Path, connection) -> None:
    csv_path = data_root / 'structured_data' / 'sla_targets.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        with connection.cursor() as cursor:
            for row in reader:
                cursor.execute(
                    'INSERT INTO sla_targets (service, metric, target, measurement_window) VALUES (%s, %s, %s, %s) ON CONFLICT (service, metric) DO UPDATE SET target = EXCLUDED.target, measurement_window = EXCLUDED.measurement_window',
                    (row['service'], row['metric'], row['target'], row['measurement_window']),
                )


def load_daily_metrics(data_root: Path, connection) -> None:
    csv_path = data_root / 'structured_data' / 'daily_metrics.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        with connection.cursor() as cursor:
            for row in reader:
                cursor.execute(
                    'INSERT INTO daily_metrics (date, service, latency_p99_ms, error_rate_percent, requests_per_minute, availability_percent) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (date, service) DO UPDATE SET latency_p99_ms = EXCLUDED.latency_p99_ms, error_rate_percent = EXCLUDED.error_rate_percent, requests_per_minute = EXCLUDED.requests_per_minute, availability_percent = EXCLUDED.availability_percent',
                    (
                        row['date'],
                        row['service'],
                        row['latency_p99_ms'],
                        row['error_rate_percent'],
                        row['requests_per_minute'],
                        row['availability_percent'],
                    ),
                )


LOADERS = (
    load_monthly_costs,
    load_incidents,
    load_sla_targets,
    load_daily_metrics,
)


def main() -> None:
    parser = argparse.ArgumentParser(description='Load HexaRAG structured data into PostgreSQL.')
    parser.add_argument('--data-root', type=Path, help='Override the root path that contains structured_data/.')
    args = parser.parse_args()

    settings = Settings()
    data_root = args.data_root or Path(settings.w4_data_root)

    with psycopg.connect(settings.database_url) as connection:
        for loader in LOADERS:
            loader(data_root, connection)
        connection.commit()


if __name__ == '__main__':
    main()
