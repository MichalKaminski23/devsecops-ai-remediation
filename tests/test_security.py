import pytest

from app.app import app, init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Provide a Flask test client with an isolated demo database."""
    monkeypatch.chdir(tmp_path)
    init_db()
    app.config.update(TESTING=False)

    with app.test_client() as test_client:
        yield test_client


def test_user_endpoint_does_not_allow_sql_injection(client):
    """Treat SQL injection payloads as plain usernames."""
    response = client.get("/user", query_string={"username": "' OR '1'='1"})

    assert response.status_code == 404
    assert response.json == {"error": "User not found"}


def test_ping_endpoint_does_not_execute_shell_commands(client):
    """Do not execute shell syntax supplied as the host value."""
    response = client.get(
        "/ping",
        query_string={"host": "127.0.0.1; echo INJECTED"},
    )

    assert b"INJECTED" not in response.data
