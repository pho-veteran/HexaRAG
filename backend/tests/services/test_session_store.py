from hexarag_api.services.session_store import trim_recent_turns


def test_trim_recent_turns_keeps_last_four_entries():
    turns = ['u1', 'a1', 'u2', 'a2', 'u3', 'a3']
    assert trim_recent_turns(turns, limit=4) == ['u2', 'a2', 'u3', 'a3']
