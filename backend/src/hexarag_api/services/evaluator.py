import json
from pathlib import Path
from typing import Any

import httpx

from hexarag_api.config import Settings

LEVEL_FILENAMES = {
    'l1': 'L1_questions.json',
    'l2': 'L2_questions.json',
    'l3': 'L3_questions.json',
    'l4': 'L4_conversation_scripts.json',
}


def default_questions_root() -> Path:
    return Path(Settings().w4_data_root).parent / 'questions' / 'student'


def resolve_question_file(level: str, questions_root: Path | None = None) -> Path:
    normalized_level = level.lower()
    if normalized_level not in LEVEL_FILENAMES:
        raise ValueError(f'Unsupported level: {level}')

    root = questions_root or default_questions_root()
    return root / LEVEL_FILENAMES[normalized_level]


def load_level_questions(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def apply_limit(items: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    if limit is None:
        return items
    return items[:limit]


def evaluate_prompt(client: httpx.Client, api_base_url: str, session_id: str, prompt: str) -> dict[str, Any]:
    response = client.post(
        f'{api_base_url}/chat',
        json={'session_id': session_id, 'message': prompt},
    )
    response.raise_for_status()
    return response.json()


def evaluate_single_turn_level(
    client: httpx.Client,
    api_base_url: str,
    level: str,
    payload: dict[str, Any],
    limit: int | None,
) -> list[dict[str, Any]]:
    results = []
    for item in apply_limit(payload['questions'], limit):
        session_id = f'eval-{level}-{item["id"].lower()}'
        response = evaluate_prompt(client, api_base_url, session_id, item['question'])
        results.append(
            {
                'id': item['id'],
                'question': item['question'],
                'expected_answer': item['expected_answer'],
                'session_id': session_id,
                'assistant_answer': response['message']['content'],
                'trace': response['message']['trace'],
            }
        )
    return results


def evaluate_conversation_level(
    client: httpx.Client,
    api_base_url: str,
    level: str,
    payload: dict[str, Any],
    limit: int | None,
) -> list[dict[str, Any]]:
    results = []
    for conversation in apply_limit(payload['conversations'], limit):
        session_id = f'eval-{level}-{conversation["id"].lower()}'
        turn_results = []
        for turn in conversation['turns']:
            response = evaluate_prompt(client, api_base_url, session_id, turn['user'])
            turn_results.append(
                {
                    'turn': turn['turn'],
                    'user': turn['user'],
                    'expected_answer': turn['expected_answer'],
                    'assistant_answer': response['message']['content'],
                    'trace': response['message']['trace'],
                }
            )
        results.append(
            {
                'id': conversation['id'],
                'title': conversation['title'],
                'session_id': session_id,
                'turns': turn_results,
            }
        )
    return results


def run_evaluation(
    api_base_url: str,
    level: str,
    questions_root: Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    question_file = resolve_question_file(level, questions_root)
    payload = load_level_questions(question_file)

    with httpx.Client(timeout=30.0) as client:
        if level == 'l4':
            results = evaluate_conversation_level(client, api_base_url, level, payload, limit)
        else:
            results = evaluate_single_turn_level(client, api_base_url, level, payload, limit)

    return {
        'level': level,
        'description': payload.get('description'),
        'question_file': str(question_file),
        'result_count': len(results),
        'results': results,
    }


def print_summary(report: dict[str, Any]) -> None:
    print(f"Level {report['level']} - {report['result_count']} item(s)")
    for result in report['results']:
        if 'turns' in result:
            print(f"- {result['id']}: {result['title']} ({len(result['turns'])} turn(s))")
            for turn in result['turns']:
                print(f"  turn {turn['turn']}: {turn['assistant_answer']}")
        else:
            print(f"- {result['id']}: {result['assistant_answer']}")
