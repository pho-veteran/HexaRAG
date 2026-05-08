from pathlib import Path

from hexarag_api.services.lambda_packaging import COMMON_WEB_DEPENDENCIES, build_artifact_specs


def test_build_artifact_specs_cover_all_three_lambda_zips() -> None:
    specs = build_artifact_specs(Path('/workspace/repo'))

    assert sorted(specs.keys()) == ['backend', 'kb_sync', 'monitoring']
    assert specs['backend'].output_path == Path('/workspace/repo/infra/terraform/backend.zip')
    assert specs['monitoring'].handler == 'monitoring_api.main.handler'
    assert specs['kb_sync'].handler == 'sync_knowledge_base.handler'


def test_common_web_dependencies_include_fastapi_runtime_transitive_imports() -> None:
    assert 'annotated_doc*' in COMMON_WEB_DEPENDENCIES
    assert 'dotenv*' in COMMON_WEB_DEPENDENCIES
