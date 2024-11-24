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
    db_conn.close()


# Basic CRUD Operations
def test_add_todo(client):
    response = client.post("/add", data={"title": "Test Todo"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Todo" in response.data


def test_add_empty_todo(client):
    response = client.post("/add", data={"title": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Todo" not in response.data


def test_delete_todo(client):
    # Add a todo first
    response = client.post("/add", data={"title": "Delete Me"}, follow_redirects=True)
    assert b"Delete Me" in response.data

    # Get the todo ID (you'll need to modify this based on your HTML structure)
    conn = get_db_connection()
    todo = conn.execute(
        "SELECT id FROM todo WHERE title = ?", ("Delete Me",)
    ).fetchone()
    conn.close()

    # Delete the todo
    response = client.get(f"/delete/{todo['id']}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Delete Me" not in response.data


def test_delete_nonexistent_todo(client):
    response = client.get("/delete/999", follow_redirects=True)
    assert response.status_code == 200


# Sorting Tests
def test_sort_by_title(client):
    titles = ["C Todo", "A Todo", "B Todo"]
    for title in titles:
        client.post("/add", data={"title": title}, follow_redirects=True)

    # Test ascending sort
    response = client.get("/?sort_by=title&sort_order=asc")
    response_text = response.data.decode("utf-8")
    assert response_text.index("A Todo") < response_text.index("B Todo")
    assert response_text.index("B Todo") < response_text.index("C Todo")

    # Test descending sort
    response = client.get("/?sort_by=title&sort_order=desc")
    response_text = response.data.decode("utf-8")
    assert response_text.index("C Todo") < response_text.index("B Todo")
    assert response_text.index("B Todo") < response_text.index("A Todo")


# Search Functionality Tests
def test_search_with_special_characters(client):
    client.post("/add", data={"title": "Test & Search"}, follow_redirects=True)
    response = client.get("/?q=Test%20%26%20Search")
    assert b"Test &amp; Search" in response.data


def test_sql_injection_prevention(client):
    malicious_input = "'; DROP TABLE todo; --"
    client.post("/add", data={"title": malicious_input}, follow_redirects=True)

    # Verify table still exists and can be queried
    conn = get_db_connection()
    result = conn.execute("SELECT COUNT(*) FROM todo").fetchone()
    conn.close()
    assert result is not None


def test_concurrent_operations(client):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    def add_and_delete():
        with app.app_context():
            # Create a new test client for each thread
            test_client = app.test_client()
            title = f"Concurrent Test {threading.get_ident()}"

            # Add todo
            response = test_client.post(
                "/add", data={"title": title}, follow_redirects=True
            )

            if response.status_code == 200:
                # Delete todo if it was added
                conn = get_db_connection()
                todo = conn.execute(
                    "SELECT id FROM todo WHERE title = ?", (title,)
                ).fetchone()
                conn.close()

                if todo:
                    test_client.get(f"/delete/{todo['id']}")

            return response.status_code

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: add_and_delete(), range(5)))

    assert all(status in [200, 302] for status in results)
