import argparse
from pathlib import Path

import boto3

from hexarag_api.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description='Upload W4 knowledge base markdown files to S3.')
    parser.add_argument('--bucket', required=True, help='Knowledge base S3 bucket name.')
    args = parser.parse_args()

    settings = Settings()
    knowledge_base_root = Path(settings.w4_data_root) / 'knowledge_base'
    client = boto3.client('s3', region_name=settings.aws_region)

    for path in sorted(knowledge_base_root.glob('*.md')):
        client.upload_file(str(path), args.bucket, path.name)


if __name__ == '__main__':
    main()
