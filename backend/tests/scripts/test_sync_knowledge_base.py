import importlib.util
from pathlib import Path


MODULE_PATH = Path('/app/scripts/sync_knowledge_base.py')
spec = importlib.util.spec_from_file_location('sync_knowledge_base', MODULE_PATH)
assert spec and spec.loader
sync_knowledge_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_knowledge_base)


def test_handler_starts_an_ingestion_job(monkeypatch) -> None:
    calls: dict[str, str] = {}

    class FakeClient:
        def start_ingestion_job(self, knowledgeBaseId: str, dataSourceId: str) -> None:
            calls['knowledge_base_id'] = knowledgeBaseId
            calls['data_source_id'] = dataSourceId

    class FakeBoto3:
        @staticmethod
        def client(service_name: str, region_name: str):
            assert service_name == 'bedrock-agent'
            assert region_name == 'us-east-1'
            return FakeClient()

    class FakeSettings:
        aws_region = 'us-east-1'
        knowledge_base_id = 'KB12345678'
        knowledge_base_data_source_id = 'DS12345678'

    monkeypatch.setattr(sync_knowledge_base, 'boto3', FakeBoto3)
    monkeypatch.setattr(sync_knowledge_base, 'Settings', FakeSettings)

    result = sync_knowledge_base.handler({}, None)

    assert result == {
        'status': 'started',
        'knowledge_base_id': 'KB12345678',
        'data_source_id': 'DS12345678',
    }
    assert calls == {
        'knowledge_base_id': 'KB12345678',
        'data_source_id': 'DS12345678',
    }
