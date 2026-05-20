"""Stats admin — SQL brut via sqlite3."""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from .. import auth, models
from ..database import DATABASE_URL

_PILLAR_TABLES = ("culture", "lieux", "activites", "cuisine")
_DONE_COLUMN = {
    "culture": "seen_at",
    "lieux": "visited_at",
    "activites": "done_at",
    "cuisine": "cooked_at",
}


def get_admin_user(
    current_user: models.User = Depends(auth.get_current_user),
) -> models.User:
    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip()
    if not admin_email or current_user.email != admin_email:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return current_user


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],
)


def _sqlite_path() -> str:
    if not DATABASE_URL.startswith("sqlite:///"):
        raise HTTPException(
            status_code=500,
            detail="Les stats admin nécessitent une base SQLite",
        )
    return DATABASE_URL.removeprefix("sqlite:///")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_sqlite_path())
    conn.row_factory = sqlite3.Row
    return conn


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _pillars_have_created_by(conn: sqlite3.Connection) -> bool:
    return all(_table_has_column(conn, t, "created_by") for t in _PILLAR_TABLES)


def _fetch_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Row:
    return conn.execute(sql, params).fetchone()


def _fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def _pillar_counts(conn: sqlite3.Connection, table: str) -> dict[str, int]:
    done_col = _DONE_COLUMN[table]
    row = _fetch_one(
        conn,
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN {done_col} IS NOT NULL THEN 1 ELSE 0 END) AS done
        FROM {table}
        """,
    )
    return {"total": row["total"] or 0, "done": row["done"] or 0}


def _recent_additions(conn: sqlite3.Connection, days: int) -> int:
    row = _fetch_one(
        conn,
        f"""
        SELECT COUNT(*) AS n FROM (
            SELECT created_at FROM culture
            WHERE substr(created_at, 1, 10) >= date('now', '-{days} days')
            UNION ALL
            SELECT created_at FROM lieux
            WHERE substr(created_at, 1, 10) >= date('now', '-{days} days')
            UNION ALL
            SELECT created_at FROM activites
            WHERE substr(created_at, 1, 10) >= date('now', '-{days} days')
            UNION ALL
            SELECT created_at FROM cuisine
            WHERE substr(created_at, 1, 10) >= date('now', '-{days} days')
        )
        """,
    )
    return row["n"] or 0


@router.get("/stats/overview")
def stats_overview() -> dict[str, Any]:
    with _connect() as conn:
        pillars = {
            "culture": _pillar_counts(conn, "culture"),
            "lieux": _pillar_counts(conn, "lieux"),
            "activites": _pillar_counts(conn, "activites"),
            "cuisine": _pillar_counts(conn, "cuisine"),
        }
        total_items = sum(p["total"] for p in pillars.values())
        done_items = sum(p["done"] for p in pillars.values())
        completion_rate = round((done_items / total_items) * 100, 1) if total_items else 0.0

        return {
            "pillars": pillars,
            "total_items": total_items,
            "done_items": done_items,
            "completion_rate": completion_rate,
            "ajouts_30j": _recent_additions(conn, 30),
            "ajouts_7j": _recent_additions(conn, 7),
        }


@router.get("/stats/contributions")
def stats_contributions() -> dict[str, Any]:
    with _connect() as conn:
        if _pillars_have_created_by(conn):
            return {"mode": "by_user", "contributions": _contributions_by_user(conn)}
        return {"mode": "by_user", "contributions": _contributions_by_membership(conn)}


def _contributions_by_user(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = _fetch_all(
        conn,
        """
        SELECT
            u.id,
            u.display_name,
            u.email,
            COALESCE(cu.cnt, 0) AS culture,
            COALESCE(li.cnt, 0) AS lieux,
            COALESCE(ac.cnt, 0) AS activites,
            COALESCE(cu2.cnt, 0) AS cuisine,
            COALESCE(cu.cnt, 0) + COALESCE(li.cnt, 0)
                + COALESCE(ac.cnt, 0) + COALESCE(cu2.cnt, 0) AS total,
            la.last_activity
        FROM users u
        LEFT JOIN (
            SELECT created_by, COUNT(*) AS cnt FROM culture GROUP BY created_by
        ) cu ON cu.created_by = u.id
        LEFT JOIN (
            SELECT created_by, COUNT(*) AS cnt FROM lieux GROUP BY created_by
        ) li ON li.created_by = u.id
        LEFT JOIN (
            SELECT created_by, COUNT(*) AS cnt FROM activites GROUP BY created_by
        ) ac ON ac.created_by = u.id
        LEFT JOIN (
            SELECT created_by, COUNT(*) AS cnt FROM cuisine GROUP BY created_by
        ) cu2 ON cu2.created_by = u.id
        LEFT JOIN (
            SELECT created_by, MAX(created_at) AS last_activity FROM (
                SELECT created_by, created_at FROM culture
                UNION ALL
                SELECT created_by, created_at FROM lieux
                UNION ALL
                SELECT created_by, created_at FROM activites
                UNION ALL
                SELECT created_by, created_at FROM cuisine
            ) GROUP BY created_by
        ) la ON la.created_by = u.id
        WHERE COALESCE(cu.cnt, 0) + COALESCE(li.cnt, 0)
            + COALESCE(ac.cnt, 0) + COALESCE(cu2.cnt, 0) > 0
        ORDER BY total DESC
        """,
    )
    return [
        {
            "display_name": r["display_name"],
            "email": r["email"],
            "culture": r["culture"],
            "lieux": r["lieux"],
            "activites": r["activites"],
            "cuisine": r["cuisine"],
            "total": r["total"],
            "last_activity": r["last_activity"],
        }
        for r in rows
    ]


def _contributions_by_membership(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Totaux par user via les cocons dont il est membre (sans created_by sur les piliers)."""
    rows = _fetch_all(
        conn,
        """
        SELECT
            u.display_name,
            u.email,
            (SELECT COUNT(*) FROM culture
             WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)) AS culture,
            (SELECT COUNT(*) FROM lieux
             WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)) AS lieux,
            (SELECT COUNT(*) FROM activites
             WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)) AS activites,
            (SELECT COUNT(*) FROM cuisine
             WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)) AS cuisine,
            (SELECT COUNT(*) FROM culture
             WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id))
            + (SELECT COUNT(*) FROM lieux
               WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id))
            + (SELECT COUNT(*) FROM activites
               WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id))
            + (SELECT COUNT(*) FROM cuisine
               WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)) AS total,
            (SELECT MAX(created_at) FROM (
                SELECT created_at FROM culture
                WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)
                UNION ALL
                SELECT created_at FROM lieux
                WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)
                UNION ALL
                SELECT created_at FROM activites
                WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)
                UNION ALL
                SELECT created_at FROM cuisine
                WHERE cocon_id IN (SELECT cocon_id FROM cocon_members WHERE user_id = u.id)
            )) AS last_activity
        FROM users u
        WHERE EXISTS (SELECT 1 FROM cocon_members WHERE user_id = u.id)
        ORDER BY total DESC
        """,
    )
    return [
        {
            "display_name": r["display_name"],
            "email": r["email"],
            "culture": r["culture"],
            "lieux": r["lieux"],
            "activites": r["activites"],
            "cuisine": r["cuisine"],
            "total": r["total"],
            "last_activity": r["last_activity"],
        }
        for r in rows
    ]


def _contributions_by_cocon(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = _fetch_all(
        conn,
        """
        SELECT
            c.id AS cocon_id,
            c.name AS cocon_name,
            COALESCE(cu.cnt, 0) AS culture,
            COALESCE(li.cnt, 0) AS lieux,
            COALESCE(ac.cnt, 0) AS activites,
            COALESCE(cu2.cnt, 0) AS cuisine,
            COALESCE(cu.cnt, 0) + COALESCE(li.cnt, 0)
                + COALESCE(ac.cnt, 0) + COALESCE(cu2.cnt, 0) AS total,
            la.last_activity
        FROM cocons c
        LEFT JOIN (
            SELECT cocon_id, COUNT(*) AS cnt FROM culture GROUP BY cocon_id
        ) cu ON cu.cocon_id = c.id
        LEFT JOIN (
            SELECT cocon_id, COUNT(*) AS cnt FROM lieux GROUP BY cocon_id
        ) li ON li.cocon_id = c.id
        LEFT JOIN (
            SELECT cocon_id, COUNT(*) AS cnt FROM activites GROUP BY cocon_id
        ) ac ON ac.cocon_id = c.id
        LEFT JOIN (
            SELECT cocon_id, COUNT(*) AS cnt FROM cuisine GROUP BY cocon_id
        ) cu2 ON cu2.cocon_id = c.id
        LEFT JOIN (
            SELECT cocon_id, MAX(created_at) AS last_activity FROM (
                SELECT cocon_id, created_at FROM culture
                UNION ALL
                SELECT cocon_id, created_at FROM lieux
                UNION ALL
                SELECT cocon_id, created_at FROM activites
                UNION ALL
                SELECT cocon_id, created_at FROM cuisine
            ) GROUP BY cocon_id
        ) la ON la.cocon_id = c.id
        ORDER BY total DESC
        """,
    )
    return [
        {
            "cocon_id": r["cocon_id"],
            "cocon_name": r["cocon_name"],
            "culture": r["culture"],
            "lieux": r["lieux"],
            "activites": r["activites"],
            "cuisine": r["cuisine"],
            "total": r["total"],
            "last_activity": r["last_activity"],
        }
        for r in rows
    ]


@router.get("/stats/culture")
def stats_culture() -> dict[str, Any]:
    with _connect() as conn:
        by_type_rows = _fetch_all(
            conn,
            "SELECT type, COUNT(*) AS cnt FROM culture GROUP BY type",
        )
        par_type = {r["type"]: r["cnt"] for r in by_type_rows}

        genre_rows = _fetch_all(
            conn,
            """
            SELECT value AS genre, COUNT(*) AS count
            FROM culture, json_each(culture.genres)
            WHERE genres IS NOT NULL
            GROUP BY value
            ORDER BY count DESC
            """,
        )
        par_genre = [{"genre": r["genre"], "count": r["count"]} for r in genre_rows]

        status_row = _fetch_one(
            conn,
            """
            SELECT
                SUM(CASE WHEN seen_at IS NULL THEN 1 ELSE 0 END) AS a_voir,
                SUM(CASE WHEN seen_at IS NOT NULL THEN 1 ELSE 0 END) AS vu_ensemble
            FROM culture
            """,
        )

        return {
            "par_type": par_type,
            "par_genre": par_genre,
            "par_statut": {
                "a_voir": status_row["a_voir"] or 0,
                "vu_ensemble": status_row["vu_ensemble"] or 0,
            },
        }


@router.get("/stats/lieux")
def stats_lieux() -> dict[str, Any]:
    with _connect() as conn:
        section_rows = _fetch_all(
            conn,
            "SELECT section, COUNT(*) AS cnt FROM lieux GROUP BY section",
        )
        par_section = {r["section"]: r["cnt"] for r in section_rows}

        category_rows = _fetch_all(
            conn,
            """
            SELECT category, COUNT(*) AS count
            FROM lieux
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            """,
        )
        par_category = [
            {"category": r["category"], "count": r["count"]} for r in category_rows
        ]

        status_row = _fetch_one(
            conn,
            """
            SELECT
                SUM(CASE WHEN visited_at IS NULL THEN 1 ELSE 0 END) AS a_visiter,
                SUM(CASE WHEN visited_at IS NOT NULL THEN 1 ELSE 0 END) AS visite
            FROM lieux
            """,
        )

        return {
            "par_section": par_section,
            "par_category": par_category,
            "par_statut": {
                "a_visiter": status_row["a_visiter"] or 0,
                "visité": status_row["visite"] or 0,
            },
        }


@router.get("/stats/activity")
def stats_activity() -> dict[str, Any]:
    with _connect() as conn:
        rows = _fetch_all(
            conn,
            """
            SELECT pilier, titre, created_at FROM (
                SELECT 'culture' AS pilier, title AS titre, created_at FROM culture
                UNION ALL
                SELECT 'lieux', name, created_at FROM lieux
                UNION ALL
                SELECT 'activites', title, created_at FROM activites
                UNION ALL
                SELECT 'cuisine', title, created_at FROM cuisine
            )
            ORDER BY created_at DESC
            LIMIT 20
            """,
        )
        return {
            "items": [
                {
                    "pilier": r["pilier"],
                    "titre": r["titre"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        }
