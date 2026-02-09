from __future__ import annotations

from typing import Any

import aiosqlite

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE IF NOT EXISTS spellings (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id  INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    spelling TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS definitions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id     INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    description TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS definition_tags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    definition_id INTEGER NOT NULL REFERENCES definitions(id) ON DELETE CASCADE,
    tag           TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL UNIQUE,
    token TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    action    TEXT    NOT NULL,
    detail    TEXT    NOT NULL DEFAULT '',
    timestamp TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_spellings_word    ON spellings(word_id);
CREATE INDEX IF NOT EXISTS idx_spellings_text    ON spellings(spelling);
CREATE INDEX IF NOT EXISTS idx_definitions_word  ON definitions(word_id);
CREATE INDEX IF NOT EXISTS idx_def_tags_def      ON definition_tags(definition_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp    ON logs(timestamp);
"""

type Word = dict[str, Any]


async def init_db(path: str = "skibidict.db") -> aiosqlite.Connection:
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.executescript(_SCHEMA)
    await db.commit()
    return db


# ── helpers ──────────────────────────────────────────────────────────


async def _row_to_word(db: aiosqlite.Connection, word_id: int) -> Word | None:
    cur = await db.execute("SELECT id FROM words WHERE id = ?", (word_id,))
    row = await cur.fetchone()
    if row is None:
        return None

    cur = await db.execute(
        "SELECT spelling FROM spellings WHERE word_id = ? ORDER BY id", (word_id,)
    )
    spellings: list[Any] = [r["spelling"] for r in await cur.fetchall()]

    cur = await db.execute(
        "SELECT id, description FROM definitions WHERE word_id = ? ORDER BY id",
        (word_id,),
    )
    defs: list[dict[str, Any]] = []
    for d in await cur.fetchall():
        tag_cur = await db.execute(
            "SELECT tag FROM definition_tags WHERE definition_id = ? ORDER BY id",
            (d["id"],),
        )
        tags: list[Any] = [t["tag"] for t in await tag_cur.fetchall()]
        defs.append({"description": d["description"], "tags": tags})

    return {"id": word_id, "spellings": spellings, "definitions": defs}


async def _insert_spellings_and_defs(
    db: aiosqlite.Connection, word_id: int, data: Word
) -> None:
    for sp in data.get("spellings", []):
        await db.execute(
            "INSERT INTO spellings (word_id, spelling) VALUES (?, ?)", (word_id, sp)
        )
    for defn in data.get("definitions", []):
        cur = await db.execute(
            "INSERT INTO definitions (word_id, description) VALUES (?, ?)",
            (word_id, defn["description"]),
        )
        def_id = cur.lastrowid
        for tag in defn.get("tags", []):
            await db.execute(
                "INSERT INTO definition_tags (definition_id, tag) VALUES (?, ?)",
                (def_id, tag),
            )


# ── CRUD ─────────────────────────────────────────────────────────────


async def insert_word(db: aiosqlite.Connection, data: Word) -> Word:
    cur = await db.execute("INSERT INTO words DEFAULT VALUES")
    word_id = cur.lastrowid
    assert word_id is not None
    await _insert_spellings_and_defs(db, word_id, data)
    await db.commit()
    result = await _row_to_word(db, word_id)
    assert result is not None
    return result


async def get_word(db: aiosqlite.Connection, word_id: int) -> Word | None:
    return await _row_to_word(db, word_id)


async def get_words(
    db: aiosqlite.Connection, query: str | None = None
) -> list[Word]:
    if query:
        cur = await db.execute(
            "SELECT DISTINCT word_id FROM spellings WHERE spelling LIKE ?",
            (f"%{query}%",),
        )
        word_ids: list[Any] = [r["word_id"] for r in await cur.fetchall()]
    else:
        cur = await db.execute("SELECT id FROM words ORDER BY id")
        word_ids = [r["id"] for r in await cur.fetchall()]

    words: list[Word] = []
    for wid in word_ids:
        w = await _row_to_word(db, wid)
        if w:
            words.append(w)
    return words


async def update_word(
    db: aiosqlite.Connection, word_id: int, data: Word
) -> Word | None:
    cur = await db.execute("SELECT id FROM words WHERE id = ?", (word_id,))
    if await cur.fetchone() is None:
        return None

    # delete old children (cascade would handle this, but be explicit)
    await db.execute("DELETE FROM spellings WHERE word_id = ?", (word_id,))
    await db.execute(
        """DELETE FROM definition_tags WHERE definition_id IN
           (SELECT id FROM definitions WHERE word_id = ?)""",
        (word_id,),
    )
    await db.execute("DELETE FROM definitions WHERE word_id = ?", (word_id,))

    await _insert_spellings_and_defs(db, word_id, data)
    await db.commit()
    return await _row_to_word(db, word_id)


async def delete_word(db: aiosqlite.Connection, word_id: int) -> bool:
    cur = await db.execute("SELECT id FROM words WHERE id = ?", (word_id,))
    if await cur.fetchone() is None:
        return False
    await db.execute("DELETE FROM words WHERE id = ?", (word_id,))
    await db.commit()
    return True


# ── users ────────────────────────────────────────────────────────────


async def get_user_by_token(
    db: aiosqlite.Connection, token: str
) -> dict[str, Any] | None:
    cur = await db.execute(
        "SELECT id, name, token FROM users WHERE token = ?", (token,)
    )
    row = await cur.fetchone()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "token": row["token"]}


async def create_user(db: aiosqlite.Connection, name: str, token: str) -> None:
    await db.execute(
        "INSERT INTO users (name, token) VALUES (?, ?)", (name, token)
    )
    await db.commit()


# ── logs ─────────────────────────────────────────────────────────────


async def add_log(
    db: aiosqlite.Connection, user_id: int, action: str, detail: str = ""
) -> None:
    await db.execute(
        "INSERT INTO logs (user_id, action, detail) VALUES (?, ?, ?)",
        (user_id, action, detail),
    )
    await db.commit()


async def get_logs(
    db: aiosqlite.Connection, *, limit: int = 100, offset: int = 0
) -> list[dict[str, Any]]:
    limit = min(limit, 300)
    cur = await db.execute(
        """SELECT l.id, u.name AS user, l.action, l.detail, l.timestamp
           FROM logs l JOIN users u ON l.user_id = u.id
           ORDER BY l.id DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    )
    return [dict(r) for r in await cur.fetchall()]
