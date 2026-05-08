import os
from pathlib import Path

from fastapi.testclient import TestClient

from hexarag_api.config import Settings
from hexarag_api.main import create_app


def test_preflight_accepts_cloudfront_origin(monkeypatch) -> None:
    from hexarag_api import main as main_module

    monkeypatch.setattr(
        main_module,
        'get_settings',
        lambda: Settings(allowed_origins='http://localhost:5173,https://d111111abcdef8.cloudfront.net'),
    )
    client = TestClient(create_app())

    response = client.options(
        '/chat',
        headers={
            'Origin': 'https://d111111abcdef8.cloudfront.net',
            'Access-Control-Request-Method': 'POST',
        },
    )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://d111111abcdef8.cloudfront.net'


def test_backend_http_api_declares_cors_for_cloudfront_preflight() -> None:
    repo_root = Path(os.environ.get('HEXARAG_REPO_ROOT', '/workspace/repo'))
    compute_tf = (repo_root / 'infra' / 'terraform' / 'compute.tf').read_text()
    backend_api_block = compute_tf.split('resource "aws_apigatewayv2_api" "backend" {', 1)[1].split(
        'resource "aws_apigatewayv2_integration" "backend" {',
        1,
    )[0]

    assert 'cors_configuration {' in backend_api_block
    assert 'allow_credentials = true' in backend_api_block
    assert 'allow_headers' in backend_api_block
    assert 'content-type' in backend_api_block.lower()
    assert 'allow_methods' in backend_api_block
    assert '"OPTIONS"' in backend_api_block
    assert '"POST"' in backend_api_block
    assert 'allow_origins' in backend_api_block
    assert 'https://${aws_cloudfront_distribution.frontend.domain_name}' in backend_api_block
