"""
VoteChain — Sistem E-Voting Mahasiswa Terverifikasi Blockchain
Proyek Akhir Pemrograman Web (Flask-CRUD + Supabase PostgreSQL)
"""

from __future__ import annotations

import os
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from blockchain import (
    GENESIS_HASH,
    create_block,
    find_block_by_hash,
    validate_chain,
)
from db import LAST_DB_ERROR, get_cursor, get_db, init_db, is_connected

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "votechain-dev-secret")
if os.getenv("VERCEL"):
    app.config["UPLOAD_FOLDER"] = "/tmp"
else:
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(__file__), "static", "img"
    )

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
except OSError:
    pass

# Lock ID khusus transaksi voting (serialisasi penomoran blok)
VOTE_ADVISORY_LOCK = 880_042

# Otomatis buat tabel & admin default saat startup (termasuk Vercel serverless)
try:
    if is_connected():
        init_db()
except Exception:
    pass


# ── Session sync (status vote selalu akurat dari DB) ─────────────────────────

@app.before_request
def sync_vote_status():
    """
    Sinkronkan has_voted dari DB hanya di halaman yang butuh status akurat.
    Tidak dijalankan di static/status agar tidak menambah latency di setiap request.
    """
    if "user_id" not in session:
        return
    # Hanya endpoint yang menampilkan status vote / form coblos
    if request.endpoint not in ("index", "vote_page", "vote_submit", "verifikasi"):
        return
    try:
        with get_db() as conn:
            cur = get_cursor(conn)
            cur.execute(
                "SELECT has_voted, role, nama FROM users WHERE id = %s",
                (session["user_id"],),
            )
            row = cur.fetchone()
            cur.close()
        if not row:
            session.clear()
            return
        session["has_voted"] = bool(row["has_voted"])
        session["role"] = row["role"]
        session["nama"] = row["nama"]
    except Exception:
        # Jangan blokir request jika DB sebentar gagal
        pass


# ── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Akses ditolak. Hanya admin yang diizinkan.", "danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped


def fetch_candidates(conn, search: str | None = None):
    cur = get_cursor(conn)
    if search:
        cur.execute(
            """
            SELECT c.*,
                   (SELECT COUNT(*) FROM blockchain_ledger b
                    WHERE b.candidate_id = c.id) AS jumlah_suara
            FROM candidates c
            WHERE c.nama_paslon ILIKE %s OR c.visi_misi ILIKE %s
            ORDER BY c.id ASC
            """,
            (f"%{search}%", f"%{search}%"),
        )
    else:
        cur.execute(
            """
            SELECT c.*,
                   (SELECT COUNT(*) FROM blockchain_ledger b
                    WHERE b.candidate_id = c.id) AS jumlah_suara
            FROM candidates c
            ORDER BY c.id ASC
            """
        )
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_ledger(conn):
    cur = get_cursor(conn)
    cur.execute(
        """
        SELECT b.*, c.nama_paslon
        FROM blockchain_ledger b
        LEFT JOIN candidates c ON c.id = b.candidate_id
        ORDER BY b.block_index ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    return rows


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        npm = request.form.get("npm", "").strip()
        nama = request.form.get("nama", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not npm or not nama or not password:
            flash("Semua field wajib diisi.", "danger")
            return render_template("register.html")
        if password != password2:
            flash("Konfirmasi password tidak cocok.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password minimal 6 karakter.", "danger")
            return render_template("register.html")

        try:
            with get_db() as conn:
                cur = get_cursor(conn)
                cur.execute("SELECT id FROM users WHERE npm = %s", (npm,))
                if cur.fetchone():
                    flash("NPM sudah terdaftar.", "danger")
                    return render_template("register.html")

                cur.execute(
                    """
                    INSERT INTO users (npm, nama, password, role, has_voted)
                    VALUES (%s, %s, %s, 'pemilih', FALSE)
                    """,
                    (npm, nama, generate_password_hash(password)),
                )
                cur.close()
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Gagal registrasi: {e}", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        npm = request.form.get("npm", "").strip()
        password = request.form.get("password", "")

        try:
            with get_db() as conn:
                cur = get_cursor(conn)
                cur.execute("SELECT * FROM users WHERE npm = %s", (npm,))
                user = cur.fetchone()
                cur.close()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["npm"] = user["npm"]
                session["nama"] = user["nama"]
                session["role"] = user["role"]
                session["has_voted"] = user["has_voted"]
                flash(f"Selamat datang, {user['nama']}!", "success")
                return redirect(url_for("index"))

            flash("NPM atau password salah.", "danger")
        except Exception as e:
            flash(f"Gagal login: {e}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("login"))


# ── Halaman utama / Quick Count ──────────────────────────────────────────────

@app.route("/")
def index():
    search = request.args.get("q", "").strip() or None
    db_ok = is_connected()
    candidates = []
    total_votes = 0

    if db_ok:
        try:
            with get_db() as conn:
                candidates = fetch_candidates(conn, search)
                total_votes = sum(c["jumlah_suara"] for c in candidates)
        except Exception as e:
            flash(f"Gagal memuat data: {e}", "danger")

    return render_template(
        "index.html",
        candidates=candidates,
        total_votes=total_votes,
        search=search or "",
        db_ok=db_ok,
    )


# ── CRUD Kandidat (Admin) ────────────────────────────────────────────────────

@app.route("/kandidat")
@admin_required
def kandidat_list():
    with get_db() as conn:
        candidates = fetch_candidates(conn)
    return render_template("kandidat_list.html", candidates=candidates)


@app.route("/kandidat/tambah", methods=["GET", "POST"])
@admin_required
def kandidat_tambah():
    if request.method == "POST":
        nama = request.form.get("nama_paslon", "").strip()
        visi = request.form.get("visi_misi", "").strip()
        foto_name = "default.png"

        if not nama:
            flash("Nama paslon wajib diisi.", "danger")
            return render_template("kandidat_form.html", kandidat=None, mode="tambah")

        file = request.files.get("foto")
        if file and file.filename and allowed_file(file.filename):
            foto_name = secure_filename(file.filename)
            import time

            foto_name = f"{int(time.time())}_{foto_name}"
            try:
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_name))
            except Exception:
                foto_name = "default.png"

        with get_db() as conn:
            cur = get_cursor(conn, dict_cursor=False)
            cur.execute(
                """
                INSERT INTO candidates (nama_paslon, visi_misi, foto)
                VALUES (%s, %s, %s)
                """,
                (nama, visi, foto_name),
            )
            cur.close()

        flash("Kandidat berhasil ditambahkan.", "success")
        return redirect(url_for("kandidat_list"))

    return render_template("kandidat_form.html", kandidat=None, mode="tambah")


@app.route("/kandidat/ubah/<int:id>", methods=["GET", "POST"])
@admin_required
def kandidat_ubah(id: int):
    with get_db() as conn:
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM candidates WHERE id = %s", (id,))
        kandidat = cur.fetchone()
        cur.close()

    if not kandidat:
        flash("Kandidat tidak ditemukan.", "danger")
        return redirect(url_for("kandidat_list"))

    if request.method == "POST":
        nama = request.form.get("nama_paslon", "").strip()
        visi = request.form.get("visi_misi", "").strip()
        foto_name = kandidat["foto"] or "default.png"

        if not nama:
            flash("Nama paslon wajib diisi.", "danger")
            return render_template(
                "kandidat_form.html", kandidat=kandidat, mode="ubah"
            )

        file = request.files.get("foto")
        if file and file.filename and allowed_file(file.filename):
            import time

            new_foto_name = f"{int(time.time())}_{secure_filename(file.filename)}"
            try:
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], new_foto_name))
                foto_name = new_foto_name
            except Exception:
                pass

        with get_db() as conn:
            cur = get_cursor(conn, dict_cursor=False)
            cur.execute(
                """
                UPDATE candidates
                SET nama_paslon = %s, visi_misi = %s, foto = %s
                WHERE id = %s
                """,
                (nama, visi, foto_name, id),
            )
            cur.close()

        flash("Data kandidat berhasil diperbarui.", "success")
        return redirect(url_for("kandidat_list"))

    return render_template("kandidat_form.html", kandidat=kandidat, mode="ubah")


@app.route("/kandidat/hapus/<int:id>")
@admin_required
def kandidat_hapus(id: int):
    try:
        with get_db() as conn:
            cur = get_cursor(conn, dict_cursor=False)
            # Cegah hapus jika sudah ada suara di ledger
            cur.execute(
                "SELECT COUNT(*) FROM blockchain_ledger WHERE candidate_id = %s",
                (id,),
            )
            count = cur.fetchone()[0]
            if count > 0:
                flash(
                    "Tidak bisa menghapus kandidat yang sudah memiliki suara di blockchain.",
                    "danger",
                )
                return redirect(url_for("kandidat_list"))

            cur.execute("DELETE FROM candidates WHERE id = %s", (id,))
            cur.close()
        flash("Kandidat berhasil dihapus.", "success")
    except Exception as e:
        flash(f"Gagal menghapus: {e}", "danger")

    return redirect(url_for("kandidat_list"))


# ── Voting ───────────────────────────────────────────────────────────────────

def cast_vote(user_id: int, candidate_id: int) -> dict:
    """
    Transaksi voting atomik ke Supabase:
    1) lock advisory (serialisasi blok)
    2) lock baris user (anti double-vote)
    3) insert blockchain_ledger
    4) update users.has_voted = TRUE
    Commit hanya jika semua sukses — gagal = rollback total.
    """
    with get_db() as conn:
        cur = get_cursor(conn)

        # Serialisasi penomoran blok agar concurrent vote tidak bentrok
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (VOTE_ADVISORY_LOCK,))

        # Kunci baris pemilih
        cur.execute(
            """
            SELECT id, npm, role, has_voted
            FROM users
            WHERE id = %s
            FOR UPDATE
            """,
            (user_id,),
        )
        user = cur.fetchone()
        if not user:
            return {"ok": False, "code": "no_user", "message": "User tidak ditemukan."}
        if user["role"] != "pemilih":
            return {
                "ok": False,
                "code": "not_voter",
                "message": "Hanya akun pemilih yang boleh mencoblos.",
            }
        if user["has_voted"]:
            return {
                "ok": False,
                "code": "already_voted",
                "message": "Anda sudah memberikan suara. Satu akun = satu suara.",
            }

        # Cek juga di ledger (sumber kebenaran blockchain)
        cur.execute(
            "SELECT block_index FROM blockchain_ledger WHERE voter_npm = %s LIMIT 1",
            (user["npm"],),
        )
        if cur.fetchone():
            cur.execute(
                "UPDATE users SET has_voted = TRUE WHERE id = %s",
                (user_id,),
            )
            return {
                "ok": False,
                "code": "already_voted",
                "message": "Suara Anda sudah tercatat di blockchain.",
            }

        # Validasi kandidat
        cur.execute(
            "SELECT id, nama_paslon FROM candidates WHERE id = %s",
            (candidate_id,),
        )
        kandidat = cur.fetchone()
        if not kandidat:
            return {
                "ok": False,
                "code": "bad_candidate",
                "message": "Kandidat tidak valid atau sudah dihapus.",
            }

        # Blok berikutnya
        cur.execute(
            """
            SELECT block_index, current_hash
            FROM blockchain_ledger
            ORDER BY block_index DESC
            LIMIT 1
            FOR UPDATE
            """
        )
        last = cur.fetchone()
        if last:
            next_index = int(last["block_index"]) + 1
            prev_hash = last["current_hash"]
        else:
            next_index = 0
            prev_hash = GENESIS_HASH

        block = create_block(
            block_index=next_index,
            prev_hash=prev_hash,
            candidate_id=int(candidate_id),
            voter_npm=user["npm"],
        )

        cur.execute(
            """
            INSERT INTO blockchain_ledger
                (block_index, prev_hash, candidate_id, voter_npm, timestamp, current_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                block["block_index"],
                block["prev_hash"],
                block["candidate_id"],
                block["voter_npm"],
                block["timestamp"],
                block["current_hash"],
            ),
        )
        cur.execute(
            "UPDATE users SET has_voted = TRUE WHERE id = %s AND has_voted = FALSE",
            (user_id,),
        )
        if cur.rowcount != 1:
            # Race condition: user sudah ditandai voted di proses lain
            raise RuntimeError("Status vote berubah saat transaksi. Coba lagi.")

        cur.close()
        # commit otomatis di get_db()

        return {
            "ok": True,
            "code": "success",
            "message": (
                f"Suara untuk “{kandidat['nama_paslon']}” berhasil dicatat ke database "
                f"& blockchain (blok #{block['block_index']})."
            ),
            "block": block,
            "kandidat": dict(kandidat),
        }


@app.route("/vote")
@login_required
def vote_page():
    if session.get("role") == "admin":
        flash("Admin tidak ikut mencoblos. Gunakan akun pemilih.", "info")
        return redirect(url_for("index"))

    try:
        with get_db() as conn:
            cur = get_cursor(conn)
            cur.execute(
                "SELECT has_voted FROM users WHERE id = %s",
                (session["user_id"],),
            )
            user = cur.fetchone()
            candidates = fetch_candidates(conn)
            cur.close()
    except Exception as e:
        flash(f"Gagal memuat halaman coblos: {e}", "danger")
        return redirect(url_for("index"))

    if user and user["has_voted"]:
        session["has_voted"] = True
        flash("Anda sudah memberikan suara. Satu akun = satu suara.", "warning")
        return redirect(url_for("index"))

    if not candidates:
        flash("Belum ada kandidat. Hubungi admin.", "warning")
        return redirect(url_for("index"))

    return render_template("vote.html", candidates=candidates)


@app.route("/vote/<int:candidate_id>", methods=["POST"])
@login_required
def vote_submit(candidate_id: int):
    """Terima coblos → catat atomik ke Supabase → redirect + flash."""
    if session.get("role") == "admin":
        flash("Admin tidak boleh voting.", "danger")
        return redirect(url_for("index"))

    if session.get("has_voted"):
        flash("Anda sudah memberikan suara.", "warning")
        return redirect(url_for("index"))

    try:
        result = cast_vote(session["user_id"], candidate_id)
    except Exception as e:
        # Unique violation / lock / timeout → pesan ramah, tidak stuck
        err = str(e)
        if "blockchain_ledger_voter_npm_key" in err or "unique" in err.lower():
            session["has_voted"] = True
            flash("Suara Anda sudah tercatat sebelumnya (anti double-vote).", "warning")
        elif "statement timeout" in err.lower() or "timeout" in err.lower():
            flash("Koneksi database timeout. Silakan coba coblos lagi.", "danger")
        else:
            flash(f"Gagal mencatat suara: {e}", "danger")
        return redirect(url_for("index"))

    if result["ok"]:
        session["has_voted"] = True
        block = result["block"]
        flash(
            f"{result['message']} Hash: {block['current_hash'][:16]}…",
            "success",
        )
        return redirect(url_for("index"))

    # Gagal validasi bisnis
    if result["code"] == "already_voted":
        session["has_voted"] = True
        flash(result["message"], "warning")
        return redirect(url_for("index"))
    if result["code"] == "no_user":
        session.clear()
        flash(result["message"], "danger")
        return redirect(url_for("login"))
    if result["code"] == "bad_candidate":
        flash(result["message"], "danger")
        return redirect(url_for("vote_page"))

    flash(result["message"], "danger")
    return redirect(url_for("index"))


# ── Verifikasi Blockchain (REAL: recompute SHA-256 di server) ────────────────

@app.route("/verifikasi", methods=["GET", "POST"])
def verifikasi():
    """
    Validasi hash sungguhan di backend:
    - Ambil semua blok dari Supabase
    - Hitung ulang SHA-256 tiap blok (hashlib)
    - Bandingkan dengan current_hash di DB
    - Cek prev_hash mengunci rantai
    Opsional: POST/GET ?hash=... untuk cek satu hash yang di-paste.
    """
    blocks: list[dict] = []
    details: list[dict] = []
    is_valid = True
    message = ""
    lookup = None
    query_hash = ""

    if request.method == "POST":
        query_hash = (request.form.get("hash") or "").strip()
    else:
        query_hash = (request.args.get("hash") or "").strip()

    try:
        with get_db() as conn:
            rows = fetch_ledger(conn)
            blocks = [dict(r) for r in rows]
            is_valid, message, details = validate_chain(blocks)

            if query_hash:
                lookup = find_block_by_hash(blocks, query_hash)
                if lookup is None:
                    # Hash tidak ada di ledger
                    lookup = {
                        "found": False,
                        "query": query_hash,
                        "ok": False,
                        "message": (
                            "Hash tidak ditemukan di ledger. "
                            "Pastikan Anda menyalin current_hash lengkap (64 karakter hex)."
                        ),
                    }
                else:
                    lookup["found"] = True
                    lookup["query"] = query_hash
                    if lookup["ok"]:
                        lookup["message"] = (
                            f"Hash valid. Cocok dengan blok #{lookup['block_index']} "
                            f"dan lolos perhitungan ulang SHA-256."
                        )
                    else:
                        lookup["message"] = (
                            f"Hash ditemukan di blok #{lookup['block_index']}, "
                            f"tetapi data blok TIDAK lolos validasi (mungkin dimanipulasi)."
                        )
    except Exception as e:
        is_valid = False
        message = f"Gagal membaca / memvalidasi ledger: {e}"

    return render_template(
        "verifikasi.html",
        blocks=blocks,
        details=details,
        is_valid=is_valid,
        message=message,
        lookup=lookup,
        query_hash=query_hash,
    )


@app.route("/api/cek-hash", methods=["GET", "POST"])
def api_cek_hash():
    """API JSON: cek satu hash (untuk tombol 'Cek' di baris ledger)."""
    if request.method == "POST":
        query_hash = (
            (request.get_json(silent=True) or {}).get("hash")
            or request.form.get("hash")
            or ""
        ).strip()
    else:
        query_hash = (request.args.get("hash") or "").strip()

    if not query_hash:
        return {"ok": False, "found": False, "message": "Parameter hash wajib diisi."}, 400

    try:
        with get_db() as conn:
            blocks = [dict(r) for r in fetch_ledger(conn)]
        result = find_block_by_hash(blocks, query_hash)
        if result is None:
            return {
                "ok": False,
                "found": False,
                "query": query_hash,
                "message": "Hash tidak ada di ledger.",
            }
        return {
            "ok": result["ok"],
            "found": True,
            "query": query_hash,
            "block_index": result["block_index"],
            "hash_ok": result["hash_ok"],
            "link_ok": result["link_ok"],
            "stored_hash": result["stored_hash"],
            "expected_hash": result["expected_hash"],
            "voter_npm": result["voter_npm"],
            "candidate_id": result["candidate_id"],
            "nama_paslon": result.get("nama_paslon"),
            "timestamp": result["timestamp"],
            "payload": result["payload"],
            "message": (
                "Hash valid."
                if result["ok"]
                else "Hash ditemukan tetapi isi blok tidak valid."
            ),
        }
    except Exception as e:
        return {"ok": False, "found": False, "message": str(e)}, 500


@app.route("/ledger")
@admin_required
def ledger():
    with get_db() as conn:
        blocks = fetch_ledger(conn)
        is_valid, message, details = validate_chain([dict(b) for b in blocks])
    return render_template(
        "ledger.html",
        blocks=blocks,
        details=details,
        is_valid=is_valid,
        message=message,
    )


# ── Status DB ────────────────────────────────────────────────────────────────

@app.route("/status")
def status():
    from db import LAST_DB_ERROR
    ok = is_connected()
    res = {
        "database": "online" if ok else "offline",
        "provider": "Supabase PostgreSQL",
        "connected": ok,
    }
    if not ok and LAST_DB_ERROR:
        res["error_detail"] = LAST_DB_ERROR
    return res


@app.route("/init-db")
def route_init_db():
    try:
        init_db()
        return {
            "status": "success",
            "message": "Skema database & tabel (users, candidates, blockchain_ledger) berhasil dibuat!",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ── Boot ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Menginisialisasi database Supabase…")
    if not is_connected():
        print("ERROR: Tidak bisa terhubung ke Supabase. Cek DATABASE_URL.")
    else:
        init_db()
        print("Database siap. Admin default: npm=admin / password=admin123")
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug, use_reloader=False)
