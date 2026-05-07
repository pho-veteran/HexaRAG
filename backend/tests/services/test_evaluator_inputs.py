from pathlib import Path

from hexarag_api.services.evaluator import apply_limit, load_level_questions, resolve_question_file


def test_resolve_question_file_points_to_l1_fixture() -> None:
    path = resolve_question_file('l1')

    assert path == Path('/workspace/W4/questions/student/L1_questions.json')


def test_load_level_questions_reads_l1_fixture() -> None:
    payload = load_level_questions(resolve_question_file('l1'))

    assert payload['level'] == 1
    assert len(payload['questions']) >= 1
    assert payload['questions'][0]['id'].startswith('L1-')


def test_resolve_question_file_points_to_l4_fixture() -> None:
    path = resolve_question_file('l4')

    assert path == Path('/workspace/W4/questions/student/L4_conversation_scripts.json')


def test_apply_limit_keeps_requested_prefix() -> None:
    items = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]

    assert apply_limit(items, limit=2) == [{'id': 'a'}, {'id': 'b'}]
    assert apply_limit(items, limit=None) == items
