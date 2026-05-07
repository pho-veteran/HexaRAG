from collections.abc import Sequence


def trim_recent_turns(turns: Sequence[str], limit: int = 6) -> list[str]:
    return list(turns[-limit:])


class SessionStore:
    def __init__(self, table) -> None:
        self.table = table

    def load_recent_turns(self, session_id: str, limit: int = 6) -> list[str]:
        response = self.table.get_item(Key={'session_id': session_id})
        turns = response.get('Item', {}).get('turns', [])
        return trim_recent_turns(turns, limit=limit)

    def append_turns(self, session_id: str, user_message: str, assistant_message: str) -> None:
        existing = self.load_recent_turns(session_id, limit=100)
        self.table.put_item(Item={'session_id': session_id, 'turns': [*existing, user_message, assistant_message]})
