"""
Koneksi database Supabase PostgreSQL (online).
Fitur 1 materi: Open Connection + cek koneksi.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Pemrogaman-web@db.ldtnlgtuizihzpspitin.supabase.co:5432/postgres",
)

LAST_DB_ERROR = None


def get_connection():
    """Membuka koneksi baru ke Supabase PostgreSQL (timeout & keepalive anti-stuck)."""
    db_url = DATABASE_URL
    if ("supabase.co" in db_url or "supabase.com" in db_url) and "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"

    conn = psycopg2.connect(
        db_url,
        connect_timeout=15,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
        options="-c statement_timeout=20000",  # max 20s per query
    )
    conn.autocommit = False
    return conn


def is_connected() -> bool:
    """Cek apakah server database online dan bisa diakses."""
    global LAST_DB_ERROR
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        LAST_DB_ERROR = None
        return True
    except Exception as e:
        err_msg = str(e)
        if "Cannot assign requested address" in err_msg or "2406:" in err_msg:
            err_msg += " (SOLUSI: Vercel tidak mendukung koneksi IPv6 langsung port 5432. Gunakan Supabase Pooler URL / port 6543 pada Vercel Environment Variables)."
        LAST_DB_ERROR = err_msg
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@contextmanager
def get_db() -> Generator[Any, None, None]:
    """Context manager: otomatis commit/rollback & tutup koneksi (anti connection leak)."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_cursor(conn, dict_cursor: bool = True):
    """Cursor RealDictCursor agar hasil SELECT seperti dict (row['kolom'])."""
    if dict_cursor:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


def init_db() -> None:
    """Buat tabel jika belum ada + seed admin default + migrasi ringan."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(schema_sql)

        # Pastikan 1 NPM hanya 1 suara di ledger (anti double-vote di level DB)
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'blockchain_ledger_voter_npm_key'
                ) THEN
                    ALTER TABLE blockchain_ledger
                    ADD CONSTRAINT blockchain_ledger_voter_npm_key UNIQUE (voter_npm);
                END IF;
            END $$;
            """
        )

        # Seed admin default jika belum ada
        cur.execute("SELECT id FROM users WHERE npm = %s", ("admin",))
        if cur.fetchone() is None:
            from werkzeug.security import generate_password_hash

            cur.execute(
                """
                INSERT INTO users (npm, nama, password, role, has_voted)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "admin",
                    "Administrator",
                    generate_password_hash("admin123"),
                    "admin",
                    False,
                ),
            )

        cur.close()
