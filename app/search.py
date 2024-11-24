from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.analysis import StandardAnalyzer
import os
from threading import Lock

schema = Schema(
    id=ID(stored=True), title=TEXT(stored=True, analyzer=StandardAnalyzer())
)

# Add at top level
index_lock = Lock()


def init_search_index(app):
    index_dir = os.path.join(app.instance_path, "whoosh_index")
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
        ix = create_in(index_dir, schema)
    else:
        ix = open_dir(index_dir)
    return ix


def add_to_index(ix, todo_id, title):
    with index_lock:
        writer = ix.writer()
        writer.add_document(id=str(todo_id), title=title)
        writer.commit()


def remove_from_index(ix, todo_id):
    with index_lock:
        writer = ix.writer()
        writer.delete_by_term("id", str(todo_id))
        writer.commit()


def search_todos(ix, query_string, sort_by="title", sort_order="asc"):
    query_string = query_string.strip()
    if not query_string:
        return {"items": [], "total": 0}

    with ix.searcher() as searcher:
        parser = QueryParser("title", ix.schema)

        terms = []
        for term in query_string.split():
            terms.append(f"*{term}*")

        query_string = " OR ".join(terms)
        query = parser.parse(query_string)

        results = searcher.search(query, limit=None)
        total = len(results)

        items = [{"id": hit["id"], "title": hit["title"]} for hit in results]
        return {"items": items, "total": total}
