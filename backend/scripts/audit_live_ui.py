import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_OUTPUT = 'artifacts/audits/2026-05-09-l1-l5-live-ui-results.json'


def repo_root() -> Path:
    return Path(os.environ.get('HEXARAG_REPO_ROOT', '/workspace/repo')).resolve()


def output_path() -> Path:
    configured = os.environ.get('HEXARAG_UI_AUDIT_OUTPUT', DEFAULT_OUTPUT)
    return repo_root() / configured


def main() -> None:
    output = output_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    frontend_url = os.environ.get('HEXARAG_LIVE_FRONTEND_URL', 'http://localhost:5173')
    command = ['docker', 'compose', 'run', '--rm', 'frontend', 'npm', 'run', 'audit:ui']
    env = os.environ.copy()
    env['HEXARAG_LIVE_FRONTEND_URL'] = frontend_url

    completed = subprocess.run(command, check=False, env=env)

    report = {
        'status': 'passed' if completed.returncode == 0 else 'failed',
        'frontend_url': frontend_url,
        'command': command,
        'returncode': completed.returncode,
        'generated_at': datetime.now(UTC).isoformat(),
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')

    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
