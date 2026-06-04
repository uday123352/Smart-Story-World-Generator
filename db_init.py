"""
Database Initialization
=======================
Creates all SQLite tables if they don't already exist.
Follows secure SQL practices — no raw string interpolation.
"""

import sqlite3
import os


def get_db(app):
    """Return a fresh SQLite connection using the app's DATABASE config."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # enforce FK constraints
    return conn


def init_db(app):
    """Create all tables on first run (idempotent)."""
    db_path = app.config['DATABASE']
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ── Users ────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password_hash TEXT  NOT NULL,
            avatar      TEXT    DEFAULT 'default',
            bio         TEXT    DEFAULT '',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Worlds ───────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS worlds (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            world_name  TEXT    NOT NULL,
            genre       TEXT    NOT NULL,
            theme       TEXT,
            world_type  TEXT,
            magic_level TEXT,
            story_tone  TEXT,
            lore        TEXT,
            plot        TEXT,
            history     TEXT,
            magic_system TEXT,
            political_system TEXT,
            economy     TEXT,
            religion    TEXT,
            world_rules TEXT,
            timeline    TEXT,
            map_svg     TEXT,
            map_image   TEXT,
            is_public   INTEGER DEFAULT 0,
            likes       INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Characters ───────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            role        TEXT,
            archetype   TEXT,
            powers      TEXT,
            backstory   TEXT,
            relationships TEXT,
            appearance  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Kingdoms ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kingdoms (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id      INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            kingdom_name  TEXT    NOT NULL,
            ruler         TEXT,
            capital_city  TEXT,
            army_power    INTEGER DEFAULT 0,
            economy_type  TEXT,
            flag_colors   TEXT,
            politics      TEXT,
            description   TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Stories / Chapters ───────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id      INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            chapter_title TEXT    NOT NULL,
            chapter_num   INTEGER DEFAULT 1,
            content       TEXT,
            dialogues     TEXT,
            quests        TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Creatures ────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS creatures (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            species     TEXT,
            powers      TEXT,
            habitat     TEXT,
            lore        TEXT,
            danger_level INTEGER DEFAULT 5,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Weapons ──────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weapons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            weapon_type TEXT,
            power_level INTEGER DEFAULT 5,
            lore        TEXT,
            owner       TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── AI Generation History ────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            prompt      TEXT,
            result_type TEXT,
            world_id    INTEGER REFERENCES worlds(id),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Comments / Community ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id    INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content     TEXT    NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")
