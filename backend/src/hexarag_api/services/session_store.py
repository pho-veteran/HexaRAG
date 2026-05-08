from collections.abc import Sequence

import boto3

from hexarag_api.config import Settings


class InMemorySessionTable:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, list[str]]] = {}

    def get_item(self, Key: dict[str, str]) -> dict[str, dict[str, list[str]]]:
        item = self.items.get(Key['session_id'])
        return {'Item': item} if item else {}

    def put_item(self, Item: dict[str, list[str] | str]) -> None:
        session_id = Item['session_id']
        turns = Item['turns']
        self.items[session_id] = {'session_id': session_id, 'turns': turns}


class DynamoSessionTable:
    def __init__(self, table) -> None:
        self.table = table

    def get_item(self, Key: dict[str, str]) -> dict:
        return self.table.get_item(Key=Key)

    def put_item(self, Item: dict[str, list[str] | str]) -> None:
        self.table.put_item(Item=Item)


IN_MEMORY_SESSION_TABLE = InMemorySessionTable()


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


def build_session_table(settings: Settings):
    if settings.runtime_mode == 'aws':
        table = boto3.resource('dynamodb', region_name=settings.aws_region).Table(settings.session_table_name)
        return DynamoSessionTable(table)
    return IN_MEMORY_SESSION_TABLE
