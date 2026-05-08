import argparse

import boto3

from hexarag_api.config import Settings


def run_sync() -> dict[str, str]:
    settings = Settings()
    client = boto3.client('bedrock-agent', region_name=settings.aws_region)
    client.start_ingestion_job(
        knowledgeBaseId=settings.knowledge_base_id,
        dataSourceId=settings.knowledge_base_data_source_id,
    )
    return {
        'status': 'started',
        'knowledge_base_id': settings.knowledge_base_id,
        'data_source_id': settings.knowledge_base_data_source_id,
    }


def handler(event, context):
    return run_sync()


def main() -> None:
    parser = argparse.ArgumentParser(description='Trigger a Bedrock knowledge base ingestion job.')
    parser.parse_args()
    run_sync()


if __name__ == '__main__':
    main()
