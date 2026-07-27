-- VoteChain schema for Supabase PostgreSQL
-- Run automatically by app.py on startup

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    npm VARCHAR(20) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL DEFAULT '',
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'pemilih'
        CHECK (role IN ('admin', 'pemilih')),
    has_voted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    nama_paslon VARCHAR(150) NOT NULL,
    visi_misi TEXT NOT NULL DEFAULT '',
    foto VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blockchain_ledger (
    block_index INTEGER PRIMARY KEY,
    prev_hash VARCHAR(64) NOT NULL,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    voter_npm VARCHAR(20) NOT NULL UNIQUE,
    timestamp VARCHAR(50) NOT NULL,
    current_hash VARCHAR(64) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_ledger_candidate ON blockchain_ledger(candidate_id);
CREATE INDEX IF NOT EXISTS idx_users_npm ON users(npm);
