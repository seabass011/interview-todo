import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest
from app.server import app, init_db, get_db_connection
from app.search import init_search_index


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def search_index():
    return init_search_index(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db_conn = get_db_connection()
    db_conn.execute("DELETE FROM todo")
    db_conn.commit()


def add_todo_item(client, title):
    return client.post("/add", data={"title": title}, follow_redirects=True)


def test_exact_match_search(client):
    # Add test todos
    add_todo_item(client, "Buy apples")
    add_todo_item(client, "Buy oranges")

    # Test exact match
    response = client.get("/?q=apples")
    assert b"Buy apples" in response.data
    assert b"Buy oranges" not in response.data


def test_partial_word_search(client):
    add_todo_item(client, "Programming task")
    add_todo_item(client, "Buy groceries")

    # Test partial word
    response = client.get("/?q=prog")
    assert b"Programming task" in response.data
    assert b"Buy groceries" not in response.data


def test_case_insensitive_search(client):
    add_todo_item(client, "Buy APPLES")

    # Test lower case search
    response = client.get("/?q=apples")
    assert b"Buy APPLES" in response.data


def test_no_false_positives(client):
    add_todo_item(client, "Buy apples")

    # Test unrelated search term
    response = client.get("/?q=qb")
    assert b"Buy apples" not in response.data


def test_multiple_word_search(client):
    add_todo_item(client, "Buy red apples")
    add_todo_item(client, "Buy green bananas")

    # Test multiple words
    response = client.get("/?q=red apples")
    assert b"Buy red apples" in response.data
    assert b"Buy green bananas" not in response.data


def test_empty_search_query(client):
    add_todo_item(client, "Test Todo")
    response = client.get("/?q=")
    assert b"Test Todo" in response.data
    assert response.status_code == 200


def test_search_with_numbers(client):
    add_todo_item(client, "Task 123")
    response = client.get("/?q=123")
    assert b"Task 123" in response.data


def test_search_with_unicode(client):
    add_todo_item(client, "Café Task")
    response = client.get("/?q=café")
    assert b"Caf\xc3\xa9 Task" in response.data


def test_search_with_long_query(client):
    add_todo_item(client, "Short task")
    # Test with a very long search query (e.g., 100 characters)
    long_query = "a" * 100
    response = client.get(f"/?q={long_query}")
    assert response.status_code == 200


def test_search_with_multiple_spaces(client):
    add_todo_item(client, "Multiple     Spaces")
    response = client.get("/?q=Multiple     Spaces")
    assert b"Multiple     Spaces" in response.data
