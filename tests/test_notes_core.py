"""Tests for the notes data core (the pre-agreed seam: pure Python, no Hermes SDK).

Notes are JSON documents (hybrid model): the content column stores a JSON object
with a ``text`` body; folders group notes for the tree (folders inside bases).
"""

import json

import pytest

from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from notes_core import (  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
    append_note,
    connect,
    create_note,
    delete_note,
    folders,
    get_note,
    list_notes,
    update_note,
)


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "notes.db")
    yield c
    c.close()


def test_create_note_returns_row(conn):
    n = create_note(conn, "Meeting notes", folder="work", text="discussed roadmap")
    assert n["title"] == "Meeting notes"
    assert n["folder"] == "work"
    assert json.loads(n["content"])["text"] == "discussed roadmap"
    assert n["id"]
    assert len(list_notes(conn)) == 1


def test_create_note_requires_title(conn):
    with pytest.raises(ValueError):
        create_note(conn, "   ")


def test_list_notes_filters_by_folder(conn):
    create_note(conn, "a", folder="work")
    create_note(conn, "b", folder="home")
    create_note(conn, "c", folder="")
    assert len(list_notes(conn, folder="work")) == 1
    assert len(list_notes(conn)) == 3


def test_folders_returns_distinct(conn):
    create_note(conn, "a", folder="work")
    create_note(conn, "b", folder="work")
    create_note(conn, "c", folder="home")
    assert sorted(folders(conn)) == ["home", "work"]


def test_get_note(conn):
    n = create_note(conn, "x")
    assert get_note(conn, n["id"])["title"] == "x"
    assert get_note(conn, "nope") is None


def test_update_note_changes_fields(conn):
    n = create_note(conn, "x", text="old")
    updated = update_note(conn, n["id"], title="X!", text="new", folder="work")
    assert updated["title"] == "X!"
    assert json.loads(updated["content"])["text"] == "new"
    assert updated["folder"] == "work"
    assert updated["updated_at"] >= n["updated_at"]


def test_update_note_missing_returns_none(conn):
    assert update_note(conn, "nope", title="x") is None


def test_update_note_noop_keeps_updated_at(conn):
    n = create_note(conn, "x")
    updated = update_note(conn, n["id"])
    assert updated["updated_at"] == n["updated_at"]


def test_update_note_partial_preserves_other_fields(conn):
    n = create_note(conn, "x", folder="work", text="body")
    updated = update_note(conn, n["id"], title="X")
    assert json.loads(updated["content"])["text"] == "body"
    assert updated["folder"] == "work"


def test_append_note_adds_text(conn):
    n = create_note(conn, "x", text="first")
    appended = append_note(conn, n["id"], "agent summary")
    body = json.loads(appended["content"])["text"]
    assert "first" in body
    assert "agent summary" in body


def test_append_note_missing_returns_none(conn):
    assert append_note(conn, "nope", "x") is None


def test_delete_note(conn):
    n = create_note(conn, "a")
    assert delete_note(conn, n["id"]) is True
    assert list_notes(conn) == []
    assert delete_note(conn, n["id"]) is False


def test_persistence_across_reconnect(tmp_path):
    db = tmp_path / "p.db"
    c1 = connect(db)
    create_note(c1, "persist me")
    c1.close()
    c2 = connect(db)
    assert len(list_notes(c2)) == 1
    c2.close()
