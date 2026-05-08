from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LambdaArtifactSpec:
    name: str
    handler: str
    output_path: Path
    package_dirs: tuple[Path, ...]
    root_files: tuple[Path, ...]
    dependency_globs: tuple[str, ...]


COMMON_WEB_DEPENDENCIES = (
    'annotated_doc*',
    'annotated_types*',
    'anyio*',
    'boto3*',
    'botocore*',
    'certifi*',
    'dateutil*',
    'dotenv*',
    'fastapi*',
    'h11*',
    'httpcore*',
    'httpx*',
    'idna*',
    'jmespath*',
    'mangum*',
    'psycopg*',
    'pydantic*',
    'pydantic_core*',
    'pydantic_settings*',
    'python_dotenv*',
    's3transfer*',
    'sniffio*',
    'starlette*',
    'typing_extensions*',
    'typing_inspection*',
    'urllib3*',
    'six*',
)

SYNC_ONLY_DEPENDENCIES = (
    'boto3*',
    'botocore*',
    'dateutil*',
    'jmespath*',
    'pydantic*',
    'pydantic_core*',
    'pydantic_settings*',
    'python_dotenv*',
    's3transfer*',
    'typing_extensions*',
    'typing_inspection*',
    'urllib3*',
    'six*',
)


def build_artifact_specs(repo_root: Path) -> dict[str, LambdaArtifactSpec]:
    backend_root = repo_root / 'backend'
    terraform_root = repo_root / 'infra' / 'terraform'

    return {
        'backend': LambdaArtifactSpec(
            name='backend',
            handler='hexarag_api.handler.handler',
            output_path=terraform_root / 'backend.zip',
            package_dirs=(backend_root / 'src' / 'hexarag_api',),
            root_files=(),
            dependency_globs=COMMON_WEB_DEPENDENCIES,
        ),
        'monitoring': LambdaArtifactSpec(
            name='monitoring',
            handler='monitoring_api.main.handler',
            output_path=terraform_root / 'monitoring.zip',
            package_dirs=(backend_root / 'src' / 'monitoring_api',),
            root_files=(),
            dependency_globs=COMMON_WEB_DEPENDENCIES,
        ),
        'kb_sync': LambdaArtifactSpec(
            name='kb_sync',
            handler='sync_knowledge_base.handler',
            output_path=terraform_root / 'kb-sync.zip',
            package_dirs=(backend_root / 'src' / 'hexarag_api',),
            root_files=(backend_root / 'scripts' / 'sync_knowledge_base.py',),
            dependency_globs=SYNC_ONLY_DEPENDENCIES,
        ),
    }
