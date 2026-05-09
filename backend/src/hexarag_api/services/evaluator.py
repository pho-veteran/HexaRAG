import json
from pathlib import Path
from typing import Any

import httpx

from hexarag_api.config import Settings
from hexarag_api.services.audit_scoring import build_unscored_result, score_single_turn_result

LEVEL_FILENAMES = {
    'l1': 'L1_questions.json',
    'l2': 'L2_questions.json',
    'l3': 'L3_questions.json',
    'l4': 'L4_conversation_scripts.json',
    'l5': 'L5_investigation_prompts.json',
}

_SINGLE_TURN_LEVELS = {'l1', 'l2', 'l3'}
_CONVERSATION_LEVELS = {'l4'}
_INVESTIGATION_LEVELS = {'l5'}


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


def _score_single_turn(level: str, response: dict[str, Any], expected_answer: str) -> dict[str, object]:
    if level.lower() == 'l1':
        return score_single_turn_result(
            level=level,
            answer=response['message']['content'],
            trace=response['message']['trace'],
            expected_answer=expected_answer,
        )
    return build_unscored_result()


def _score_conversation_turn(level: str, response: dict[str, Any], expected_answer: str) -> dict[str, object]:
    return _score_single_turn(level, response, expected_answer)


def _score_conversation_result() -> dict[str, object]:
    return build_unscored_result()


def _score_investigation_result() -> dict[str, object]:
    return build_unscored_result()


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
                **_score_single_turn(level, response, item['expected_answer']),
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
                    **_score_conversation_turn(level, response, turn['expected_answer']),
                }
            )
        results.append(
            {
                'id': conversation['id'],
                'title': conversation['title'],
                'session_id': session_id,
                'turns': turn_results,
                **_score_conversation_result(),
            }
        )
    return results


def evaluate_investigation_level(
    client: httpx.Client,
    api_base_url: str,
    level: str,
    payload: dict[str, Any],
    limit: int | None,
) -> list[dict[str, Any]]:
    results = []
    for item in apply_limit(payload['investigations'], limit):
        session_id = f'eval-{level}-{item["id"].lower()}'
        response = evaluate_prompt(client, api_base_url, session_id, item['prompt'])
        results.append(
            {
                'id': item['id'],
                'prompt': item['prompt'],
                'expected_steps': item.get('expected_steps', []),
                'expected_findings': item.get('expected_findings'),
                'data_sources_needed': item.get('data_sources_needed', []),
                'session_id': session_id,
                'assistant_answer': response['message']['content'],
                'trace': response['message']['trace'],
                **_score_investigation_result(),
            }
        )
    return results


def run_evaluation(
    api_base_url: str,
    level: str,
    questions_root: Path | None = None,
    limit: int | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    normalized_level = level.lower()
    question_file = resolve_question_file(normalized_level, questions_root)
    payload = load_level_questions(question_file)

    if client is not None:
        if normalized_level in _CONVERSATION_LEVELS:
            results = evaluate_conversation_level(client, api_base_url, normalized_level, payload, limit)
        elif normalized_level in _INVESTIGATION_LEVELS:
            results = evaluate_investigation_level(client, api_base_url, normalized_level, payload, limit)
        else:
            results = evaluate_single_turn_level(client, api_base_url, normalized_level, payload, limit)
    else:
        with httpx.Client(timeout=30.0) as managed_client:
            if normalized_level in _CONVERSATION_LEVELS:
                results = evaluate_conversation_level(managed_client, api_base_url, normalized_level, payload, limit)
            elif normalized_level in _INVESTIGATION_LEVELS:
                results = evaluate_investigation_level(managed_client, api_base_url, normalized_level, payload, limit)
            else:
                results = evaluate_single_turn_level(managed_client, api_base_url, normalized_level, payload, limit)

    return {
        'level': normalized_level,
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
