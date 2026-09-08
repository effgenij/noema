"""Tests for the habits data core (the pre-agreed seam: pure Python, no Hermes SDK).

Habits: strict table + per-day check-in log. Streak = consecutive checked days
ending today (or yesterday if today is not yet checked); a missed day resets it.
Sparkline = 0/1 per day for the last N days (rendered as SVG by the UI).
"""

import pytest

from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from habits_core import (  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
    check_in,
    connect,
    create_habit,
    current_streak,
    delete_habit,
    list_habits,
    sparkline,
    uncheck,
)


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "habits.db")
    yield c
    c.close()


def test_create_habit_returns_row(conn):
    h = create_habit(conn, "Read")
    assert h["name"] == "Read"
    assert h["id"]
    assert len(list_habits(conn)) == 1


def test_create_habit_requires_name(conn):
    with pytest.raises(ValueError):
        create_habit(conn, "   ")


def test_check_in_records_day(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-01")
    assert sparkline(conn, h["id"], days=3, today="2026-09-01") == [0, 0, 1]


def test_check_in_idempotent(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-01")
    check_in(conn, h["id"], day="2026-09-01")
    assert sparkline(conn, h["id"], days=3, today="2026-09-01").count(1) == 1


def test_uncheck_removes_day(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-01")
    assert uncheck(conn, h["id"], day="2026-09-01") is True
    assert sparkline(conn, h["id"], days=3, today="2026-09-01").count(1) == 0


def test_streak_counts_consecutive_days(conn):
    h = create_habit(conn, "Read")
    for day in ("2026-09-01", "2026-09-02", "2026-09-03"):
        check_in(conn, h["id"], day=day)
    assert current_streak(conn, h["id"], today="2026-09-03") == 3


def test_streak_resets_on_missed_day(conn):
    h = create_habit(conn, "Read")
    for day in ("2026-09-01", "2026-09-02", "2026-09-04"):
        check_in(conn, h["id"], day=day)
    # gap on 09-03: streak from 09-04 is just 1
    assert current_streak(conn, h["id"], today="2026-09-04") == 1


def test_streak_counts_from_yesterday_if_today_unchecked(conn):
    h = create_habit(conn, "Read")
    for day in ("2026-09-01", "2026-09-02"):
        check_in(conn, h["id"], day=day)
    # today (09-03) not checked yet: streak still alive from yesterday
    assert current_streak(conn, h["id"], today="2026-09-03") == 2


def test_streak_zero_when_no_recent_check(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-01")
    assert current_streak(conn, h["id"], today="2026-09-05") == 0


def test_sparkline_returns_last_n_days(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-03")
    check_in(conn, h["id"], day="2026-09-05")
    assert sparkline(conn, h["id"], days=5, today="2026-09-05") == [0, 0, 1, 0, 1]


def test_list_habits_includes_streak_and_sparkline(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-05")
    rows = list_habits(conn, today="2026-09-05")
    assert rows[0]["streak"] == 1
    assert rows[0]["sparkline"] == [0] * 13 + [1]  # 14 days by default, checked today


def test_delete_habit(conn):
    h = create_habit(conn, "Read")
    check_in(conn, h["id"], day="2026-09-01")
    assert delete_habit(conn, h["id"]) is True
    assert list_habits(conn) == []
    assert delete_habit(conn, h["id"]) is False


def test_persistence_across_reconnect(tmp_path):
    db = tmp_path / "p.db"
    c1 = connect(db)
    h = create_habit(c1, "Read")
    check_in(c1, h["id"], day="2026-09-01")
    c1.close()
    c2 = connect(db)
    assert len(list_habits(c2)) == 1
    c2.close()
