import os
import sys
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from .search import init_search_index, add_to_index, remove_from_index, search_todos

app = Flask(__name__)
search_index = init_search_index(app)


def get_db_connection():
    if "pytest" in sys.modules:
        db_name = "test.db"
    else:
        db_name = "prod.db"
    conn = sqlite3.connect(os.path.join(app.instance_path, db_name))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Create instance directory if it doesn't exist
    os.makedirs(app.instance_path, exist_ok=True)

    conn = get_db_connection()
    with app.open_resource("schema.sql") as f:
        conn.executescript(f.read().decode("utf8"))
    conn.close()


@app.route("/")
def index():
    search_query = request.args.get("q", "")
    sort_by = request.args.get("sort_by", "title")
    sort_order = request.args.get("sort_order", "asc")

    conn = get_db_connection()

    if search_query:
        search_results = search_todos(
            search_index,
            search_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        todos = search_results["items"]
        total_results = search_results["total"]
    else:
        query = """
            SELECT id, title 
            FROM todo 
            ORDER BY title COLLATE NOCASE {}
        """.format("DESC" if sort_order == "desc" else "ASC")

        todos = conn.execute(query).fetchall()
        total_results = len(todos)

    conn.close()
    return render_template(
        "index.html",
        todos=todos,
        search_query=search_query,
        total_results=total_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.route("/add", methods=("GET", "POST"))
def add():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            return redirect(url_for("index"))

        # HTML escape the title
        title = (
            title.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

        conn = get_db_connection()
        cursor = conn.execute("INSERT INTO todo (title) VALUES (?)", (title,))
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()

        add_to_index(search_index, todo_id, title)
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    todo = conn.execute("SELECT id FROM todo WHERE id = ?", (id,)).fetchone()
    if not todo:
        conn.close()
        return redirect(url_for("index"))

    conn.execute("DELETE FROM todo WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    remove_from_index(search_index, id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()  # Initialize the in-memory database
    app.run(debug=True)
