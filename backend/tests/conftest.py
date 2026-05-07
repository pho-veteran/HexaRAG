import pytest


class FakeCursor:
    def __init__(self, total_cost: int) -> None:
        self.total_cost = total_cost
        self.executed: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str) -> None:
        self.executed.append(query)

    def fetchone(self) -> tuple[int]:
        return (self.total_cost,)


class FakeConnection:
    def __init__(self, total_cost: int) -> None:
        self.cursor_instance = FakeCursor(total_cost)

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


@pytest.fixture
def fake_db_connection() -> FakeConnection:
    return FakeConnection(total_cost=56350)
