"""
VoteChain — modul blockchain sederhana (hash-chain SHA-256).
Setiap suara = 1 blok yang terhubung ke blok sebelumnya.

Validasi bersifat REAL (bukan mock):
hash dihitung ulang dengan hashlib.sha256 dari field blok,
lalu dibandingkan dengan current_hash yang tersimpan di database.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


GENESIS_HASH = "0" * 64


def build_payload(
    block_index: int,
    prev_hash: str,
    candidate_id: int,
    voter_npm: str,
    timestamp: str,
) -> str:
    """String yang di-hash (urutan & format harus konsisten saat create & verify)."""
    return f"{block_index}{prev_hash}{candidate_id}{voter_npm}{timestamp}"


def compute_hash(
    block_index: int,
    prev_hash: str,
    candidate_id: int,
    voter_npm: str,
    timestamp: str,
) -> str:
    """Hash_blok = SHA256(Index + PrevHash + CandidateID + VoterNPM + Timestamp)."""
    payload = build_payload(
        block_index, prev_hash, int(candidate_id), str(voter_npm), str(timestamp)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_block(
    block_index: int,
    prev_hash: str,
    candidate_id: int,
    voter_npm: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Membuat blok transaksi suara baru."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    current_hash = compute_hash(
        block_index, prev_hash, candidate_id, voter_npm, timestamp
    )
    return {
        "block_index": block_index,
        "prev_hash": prev_hash,
        "candidate_id": candidate_id,
        "voter_npm": voter_npm,
        "timestamp": timestamp,
        "current_hash": current_hash,
    }


def inspect_block(
    block: dict[str, Any],
    prev_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Periksa SATU blok secara detail (recompute hash + cek tautan rantai).
    Dipakai UI verifikasi agar user bisa lihat expected vs stored.
    """
    expected = compute_hash(
        int(block["block_index"]),
        str(block["prev_hash"]),
        int(block["candidate_id"]),
        str(block["voter_npm"]),
        str(block["timestamp"]),
    )
    stored = str(block.get("current_hash") or "")
    hash_ok = stored == expected

    link_ok = True
    link_note = "Blok genesis (prev_hash = 64 nol)."
    if prev_block is None:
        if block["prev_hash"] != GENESIS_HASH:
            link_ok = False
            link_note = "Prev hash genesis tidak valid."
        if int(block["block_index"]) != 0:
            link_ok = False
            link_note = "Index blok pertama harus 0."
    else:
        if block["prev_hash"] != prev_block["current_hash"]:
            link_ok = False
            link_note = "Prev hash tidak cocok dengan hash blok sebelumnya (rantai putus)."
        elif int(block["block_index"]) != int(prev_block["block_index"]) + 1:
            link_ok = False
            link_note = "Index blok tidak berurutan."
        else:
            link_note = "Tautan ke blok sebelumnya utuh."

    payload = build_payload(
        int(block["block_index"]),
        str(block["prev_hash"]),
        int(block["candidate_id"]),
        str(block["voter_npm"]),
        str(block["timestamp"]),
    )

    return {
        "block_index": int(block["block_index"]),
        "hash_ok": hash_ok,
        "link_ok": link_ok,
        "ok": hash_ok and link_ok,
        "stored_hash": stored,
        "expected_hash": expected,
        "payload": payload,
        "link_note": link_note,
        "candidate_id": block.get("candidate_id"),
        "nama_paslon": block.get("nama_paslon"),
        "voter_npm": block.get("voter_npm"),
        "timestamp": block.get("timestamp"),
        "prev_hash": block.get("prev_hash"),
    }


def validate_chain(blocks: list[dict[str, Any]]) -> tuple[bool, str, list[dict[str, Any]]]:
    """
    Validasi integritas seluruh rantai blok.
    Returns (is_valid, message, detail_per_block).
    """
    if not blocks:
        return True, "Belum ada suara di ledger. Tidak ada blok yang perlu dicek.", []

    details: list[dict[str, Any]] = []
    for i, block in enumerate(blocks):
        prev = blocks[i - 1] if i > 0 else None
        detail = inspect_block(block, prev)
        details.append(detail)
        if not detail["ok"]:
            if not detail["hash_ok"]:
                msg = (
                    f"Blok #{detail['block_index']} TIDAK VALID: "
                    f"hash tersimpan tidak cocok dengan perhitungan ulang SHA-256."
                )
            else:
                msg = f"Blok #{detail['block_index']} TIDAK VALID: {detail['link_note']}"
            return False, msg, details

    return True, f"Semua {len(blocks)} blok valid. Hash & rantai utuh.", details


def find_block_by_hash(
    blocks: list[dict[str, Any]], query_hash: str
) -> dict[str, Any] | None:
    """Cari blok berdasarkan current_hash (case-insensitive, strip spasi)."""
    q = (query_hash or "").strip().lower()
    if not q:
        return None
    for i, block in enumerate(blocks):
        if str(block.get("current_hash", "")).lower() == q:
            prev = blocks[i - 1] if i > 0 else None
            return inspect_block(block, prev)
    return None
