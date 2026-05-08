import os
from pathlib import Path


def test_frontend_build_does_not_inherit_dev_only_api_base_url() -> None:
    repo_root = Path(os.environ.get('HEXARAG_REPO_ROOT', '/workspace/repo'))
    compose_text = (repo_root / 'docker-compose.yml').read_text()
    frontend_block = compose_text.split('frontend:\n', 1)[1].split('\n  backend:\n', 1)[0]

    assert 'environment:' not in frontend_block
    assert "command: sh -lc 'VITE_API_BASE_URL=http://backend:8000 npm run dev -- --host 0.0.0.0'" in frontend_block
    assert 'VITE_API_BASE_URL: http://backend:8000' not in frontend_block
    assert 'VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://backend:8000}' not in frontend_block
