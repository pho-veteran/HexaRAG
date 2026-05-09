from pathlib import Path
from typing import Any

from hexarag_api.services.evaluator import default_questions_root, load_level_questions

LEVEL_FILENAMES = {
    'l1': 'L1_questions.json',
    'l2': 'L2_questions.json',
    'l3': 'L3_questions.json',
    'l4': 'L4_conversation_scripts.json',
    'l5': 'L5_investigation_prompts.json',
}

UI_CASE_IDS = {
    'l1': {'L1-01', 'L1-03'},
    'l2': {'L2-01', 'L2-05'},
    'l3': {'L3-04', 'L3-06', 'L3-09'},
    'l4': {'L4-01', 'L4-03'},
    'l5': {'L5-01', 'L5-03'},
}

_PAYLOAD_KEYS = {
    'l1': 'questions',
    'l2': 'questions',
    'l3': 'questions',
    'l4': 'conversations',
    'l5': 'investigations',
}


def resolve_ui_fixture(level: str) -> Path:
    return default_questions_root() / LEVEL_FILENAMES[level]


def select_ui_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for level in LEVEL_FILENAMES:
        payload = load_level_questions(resolve_ui_fixture(level))
        selected_ids = UI_CASE_IDS.get(level, set())
        items = payload[_PAYLOAD_KEYS[level]]
        cases.extend({'level': level, **item} for item in items if item['id'] in selected_ids)

    return cases
