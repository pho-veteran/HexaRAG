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
                    'INSERT INTO monthly_costs (service, month, total_cost) VALUES (%s, %s, %s)',
                    (row['service'], row['month'], row['total_cost']),
                )
        connection.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description='Load HexaRAG structured data into PostgreSQL.')
    parser.add_argument('--data-root', type=Path, help='Override the root path that contains structured_data/.')
    args = parser.parse_args()

    settings = Settings()
    data_root = args.data_root or Path(settings.w4_data_root)

    with psycopg.connect(settings.database_url) as connection:
        load_monthly_costs(data_root, connection)


if __name__ == '__main__':
    main()
