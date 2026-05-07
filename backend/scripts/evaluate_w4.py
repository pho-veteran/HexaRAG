import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == '':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hexarag_api.services.evaluator import LEVEL_FILENAMES, print_summary, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description='Replay W4 student questions against the HexaRAG /chat API.')
    parser.add_argument('--api-base-url', required=True, help='Base URL for the HexaRAG API, for example http://backend:8000.')
    parser.add_argument('--level', required=True, choices=sorted(LEVEL_FILENAMES), help='W4 level to replay.')
    parser.add_argument('--limit', type=int, help='Optional limit on the number of questions or conversations to run.')
    parser.add_argument('--output', type=Path, help='Optional file path for saving JSON results.')
    parser.add_argument('--questions-root', type=Path, help='Override the directory containing W4 student question files.')
    args = parser.parse_args()

    report = run_evaluation(
        api_base_url=args.api_base_url,
        level=args.level,
        questions_root=args.questions_root,
        limit=args.limit,
    )
    print_summary(report)

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
