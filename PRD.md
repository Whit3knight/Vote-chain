# PRD — VoteChain  
**Product Requirements Document & Technical Flow Specification**

| Field | Value |
|--------|--------|
| **Product** | VoteChain — E-Voting Mahasiswa Terverifikasi Hash-Chain |
| **Version** | 1.0 |
| **Stack** | Flask 3 · Jinja2 · Bootstrap 5 · Supabase PostgreSQL · SHA-256 (`hashlib`) |
| **Repo path** | `/home/whit3knight/UAS/web` |
| **Audience** | Developer, dosen penguji, anggota kelompok |
| **Related docs** | `README.md`, `fitur_proyek_flask_crud.txt`, `ide_web.pdf` |

---

## 1. Ringkasan produk

### 1.1 Masalah
Pemungutan suara digital di kampus rentan dimanipulasi di level database (admin atau pihak luar mengubah jumlah suara lewat SQL). User butuh sistem yang:

1. Mudah digunakan (web Flask-CRUD sesuai materi kuliah).
2. Menyimpan data online (bukan hanya localhost).
3. Bisa **membuktikan** bahwa suara yang sudah masuk tidak diubah — lewat rantai hash yang bisa diverifikasi ulang.

### 1.2 Solusi
**VoteChain** adalah aplikasi e-voting berbasis web di mana:

- Pemilih mendaftar/login, lalu mencoblos **satu kali**.
- Setiap suara menjadi **satu blok** di ledger:  
  `current_hash = SHA256(index + prev_hash + candidate_id + voter_npm + timestamp)`.
- Admin mengelola kandidat (CRUD).
- Publik/admin bisa **mengecek hash** secara real: server menghitung ulang SHA-256 dari data di DB, bukan mockup di frontend.

### 1.3 Argumentasi utama (untuk presentasi UAS)
> Meskipun admin memiliki akses ke database, mengubah baris suara secara paksa akan membuat `current_hash` tidak cocok dengan hasil perhitungan ulang, atau memutus tautan `prev_hash` antarblok. Halaman **Cek hash** akan menandai rantai **invalid**.

### 1.4 Bukan blockchain publik
Ini **hash-chain sederhana** di aplikasi (Python + tabel PostgreSQL), bukan jaringan multi-node. Cocok untuk demonstrasi konsep integritas data di mata kuliah Pemrograman Web.

---

## 2. Tujuan & non-tujuan

### 2.1 Tujuan (in scope)
| # | Tujuan | Metrik sukses |
|---|--------|----------------|
| G1 | Auth pemilih & admin | Register, login, logout, session |
| G2 | CRUD kandidat (admin) | Tambah, lihat, ubah, hapus + JS confirm |
| G3 | Voting 1 akun = 1 suara | `has_voted` + unique `voter_npm` di ledger |
| G4 | Suara langsung ke DB online | Insert atomik ke Supabase |
| G5 | Hash-chain SHA-256 | Setiap vote = 1 blok terhubung |
| G6 | Verifikasi hash real | Recompute di server, tampil expected vs stored |
| G7 | Copy & cek hash manual | Tombol salin + form cek + API JSON |
| G8 | 10 fitur Flask-CRUD materi | Lihat §12 |
| G9 | UI bersih, template inheritance | `base.html` + Bootstrap |

### 2.2 Non-tujuan (out of scope v1)
- Wallet crypto / smart contract on-chain (Solana, Ethereum, dll.)
- Voting anonim zero-knowledge
- Multi-node consensus / mining
- Mobile native app
- Real-time WebSocket push (hasil di-refresh lewat page load)
- Email OTP / SSO kampus

---

## 3. Persona & peran

| Role | Siapa | Boleh | Tidak boleh |
|------|--------|-------|-------------|
| **Guest** | Pengunjung tanpa login | Lihat hasil, cek hash, daftar, login | Coblos, CRUD kandidat |
| **Pemilih** | Mahasiswa terdaftar | Coblos 1×, lihat hasil, cek hash | CRUD kandidat, lihat ledger admin |
| **Admin** | Panitia / dosen | CRUD kandidat, ledger, cek hash | Coblos (sengaja diblok) |

**Akun default seed**

| Role | NPM / user | Password |
|------|------------|----------|
| Admin | `admin` | `admin123` |

Pemilih baru dibuat lewat `/register` atau seed demo.

---

## 4. Arsitektur sistem

### 4.1 Diagram komponen

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER (Client)                         │
│  HTML (Jinja2) · CSS · JS (confirm, copy hash, anti double-click)│
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP GET/POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK APP (app.py)                          │
│  Routing · Session · Flash · Auth guards · cast_vote()           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  blockchain  │  │    db.py     │  │  templates/ + static/  │  │
│  │  .py SHA-256 │  │  psycopg2    │  │  Jinja2 render         │  │
│  └──────────────┘  └──────┬───────┘  └────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────┘
                              │ PostgreSQL wire protocol (TLS)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              SUPABASE PostgreSQL (online database)               │
│   users  ·  candidates  ·  blockchain_ledger                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Struktur direktori

```
web/
├── app.py                 # Entry point: routes, auth, voting, verifikasi
├── blockchain.py          # Hash-chain SHA-256 + validasi rantai
├── db.py                  # Koneksi Supabase, get_db(), init_db()
├── schema.sql             # DDL tabel
├── requirements.txt       # Flask, psycopg2-binary, python-dotenv, Werkzeug
├── .env                   # DATABASE_URL, SECRET_KEY (jangan di-commit)
├── .gitignore
├── README.md
├── PRD.md                 # Dokumen ini
├── fitur_proyek_flask_crud.txt
├── ide_web.pdf
├── templates/
│   ├── base.html          # Layout master (nav, flash, footer)
│   ├── index.html         # Hasil / quick count
│   ├── login.html
│   ├── register.html
│   ├── vote.html          # Halaman coblos
│   ├── verifikasi.html    # Cek rantai + cek 1 hash
│   ├── ledger.html        # Ledger admin
│   ├── kandidat_list.html
│   └── kandidat_form.html # Tambah / ubah kandidat
└── static/
    ├── css/style.css
    ├── js/app.js          # confirm, copy clipboard, disable tombol vote
    └── img/               # Foto paslon (upload)
```

### 4.3 Dependency runtime

| Package | Fungsi |
|---------|--------|
| Flask | Web framework, routing, session, templates |
| psycopg2-binary | Driver PostgreSQL → Supabase |
| python-dotenv | Load `.env` |
| Werkzeug | `generate_password_hash` / `check_password_hash`, `secure_filename` |

Konfigurasi env:

```env
DATABASE_URL=postgresql://postgres:...@db.xxx.supabase.co:5432/postgres
SECRET_KEY=...
FLASK_DEBUG=1
```

---

## 5. Model data

### 5.1 ER (konseptual)

```
users 1────0..1  (via voter_npm)  blockchain_ledger N────1 candidates
  │                                      │
  │ has_voted                            │ block_index berantai
  │ role: admin|pemilih                  │ prev_hash → current_hash prev
```

### 5.2 Tabel `users`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | SERIAL PK | ID internal |
| `npm` | VARCHAR(20) UNIQUE | Username login (NPM atau `admin`) |
| `nama` | VARCHAR(100) | Nama tampilan |
| `password` | VARCHAR(255) | Hash Werkzeug (bukan plain text) |
| `role` | VARCHAR(20) | `admin` \| `pemilih` |
| `has_voted` | BOOLEAN | Flag anti double-vote di aplikasi |
| `created_at` | TIMESTAMP | Waktu daftar |

### 5.3 Tabel `candidates`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | SERIAL PK | Dipakai di form vote & ledger |
| `nama_paslon` | VARCHAR(150) | Nama pasangan calon |
| `visi_misi` | TEXT | Deskripsi |
| `foto` | VARCHAR(255) | Nama file di `static/img/` |
| `created_at` | TIMESTAMP | |

### 5.4 Tabel `blockchain_ledger`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `block_index` | INTEGER PK | 0, 1, 2, … berurutan |
| `prev_hash` | VARCHAR(64) | Hash blok sebelumnya; genesis = 64 digit `0` |
| `candidate_id` | INTEGER FK → candidates | Siapa yang dipilih |
| `voter_npm` | VARCHAR(20) **UNIQUE** | 1 NPM = max 1 baris (anti double-vote DB) |
| `timestamp` | VARCHAR(50) | ISO UTC saat blok dibuat |
| `current_hash` | VARCHAR(64) **UNIQUE** | SHA-256 hasil perhitungan |

### 5.5 Rumus hash (kontrak data)

```
payload      = str(block_index) + prev_hash + str(candidate_id) + voter_npm + timestamp
current_hash = SHA256(payload).hexdigest()   # 64 karakter hex
```

Implementasi: `blockchain.compute_hash()` / `create_block()` / `validate_chain()`.

---

## 6. Peta rute (API & halaman)

| Method | Path | Auth | Handler | Response |
|--------|------|------|---------|----------|
| GET | `/` | Public | `index` | HTML hasil suara |
| GET/POST | `/register` | Guest | `register` | Form / redirect login |
| GET/POST | `/login` | Guest | `login` | Form / set session |
| GET | `/logout` | Session | `logout` | Clear session |
| GET | `/vote` | Pemilih | `vote_page` | Form coblos |
| POST | `/vote/<candidate_id>` | Pemilih | `vote_submit` | Redirect + flash |
| GET | `/kandidat` | Admin | `kandidat_list` | Tabel kandidat |
| GET/POST | `/kandidat/tambah` | Admin | `kandidat_tambah` | Form create |
| GET/POST | `/kandidat/ubah/<id>` | Admin | `kandidat_ubah` | Form update |
| GET | `/kandidat/hapus/<id>` | Admin | `kandidat_hapus` | Redirect list |
| GET/POST | `/verifikasi` | Public | `verifikasi` | Validasi rantai + cek hash |
| GET/POST | `/api/cek-hash` | Public | `api_cek_hash` | JSON hasil cek |
| GET | `/ledger` | Admin | `ledger` | Tabel ledger + status |
| GET | `/status` | Public | `status` | JSON health DB |

---

## 7. Session & guard

### 7.1 Isi session setelah login
```
user_id, npm, nama, role, has_voted
```

### 7.2 Decorators
- `login_required` — wajib `user_id` di session; else flash + redirect `/login`.
- `admin_required` — wajib login **dan** `role == 'admin'`.

### 7.3 `before_request: sync_vote_status`
Pada endpoint `index`, `vote_page`, `vote_submit`, `verifikasi`:

1. Jika ada `user_id`, query ulang `has_voted`, `role`, `nama` dari DB.
2. Update session agar status coblos tidak stale (mis. tab lain / admin ubah data).
3. Jika user hilang dari DB → `session.clear()`.
4. Gagal DB → **tidak** memblokir request (fail-open untuk UX).

---

## 8. Flow frontend → backend (detail per fitur)

### 8.1 Boot aplikasi

```
python app.py
        │
        ├─ load_dotenv() → DATABASE_URL, SECRET_KEY
        ├─ is_connected() → SELECT 1 ke Supabase
        ├─ init_db()
        │     ├─ jalankan schema.sql (CREATE TABLE IF NOT EXISTS)
        │     ├─ pastikan UNIQUE voter_npm di ledger
        │     └─ seed admin jika belum ada
        └─ app.run(host=0.0.0.0, port=5000)
```

**Frontend:** belum ada; ini proses server saja.

---

### 8.2 Registrasi pemilih

```
[UI] GET /register → templates/register.html (extends base.html)
        │ user isi: npm, nama, password, password2
        │ submit POST
        ▼
[BE] register()
        │ validasi field kosong / password mismatch / min 6 char
        │ SELECT users WHERE npm = ?
        │   ada → flash error, render form lagi
        │   belum → INSERT users (password = generate_password_hash(...), role=pemilih)
        │ commit via get_db()
        ▼
[UI] redirect /login + flash "Registrasi berhasil"
```

---

### 8.3 Login

```
[UI] GET /login → login.html
        │ POST npm + password
        ▼
[BE] login()
        │ SELECT * FROM users WHERE npm = ?
        │ check_password_hash(stored, input)
        │ gagal → flash error
        │ sukses → isi session → redirect /
        ▼
[UI] base.html menampilkan nama + role; menu Coblos jika pemilih & !has_voted
```

---

### 8.4 Logout

```
[UI] klik Keluar → GET /logout
[BE] session.clear() → redirect /login
```

---

### 8.5 Halaman hasil (Quick Count) — Read

```
[UI] GET /
        ▼
[BE] index()
        │ is_connected()
        │ fetch_candidates(conn, search=q)
        │   SELECT candidates + subquery COUNT(blockchain_ledger) AS jumlah_suara
        │   optional ILIKE filter nama/visi
        │ total_votes = sum(jumlah_suara)
        ▼
[UI] index.html
        │ kartu statistik + progress bar %
        │ CTA coblos jika pemilih belum vote
        │ tombol "Pilih paslon ini" (POST vote) jika eligible
        │ loop Jinja {% for c in candidates %}
```

**Fitur materi:** Read/Fetch, Jinja for/if, static CSS, routing.

---

### 8.6 CRUD kandidat (admin)

#### List
```
GET /kandidat  → admin_required → fetch_candidates → kandidat_list.html
```

#### Create
```
GET  /kandidat/tambah → form kosong
POST /kandidat/tambah
        │ ambil nama_paslon, visi_misi, optional file foto
        │ secure_filename + simpan static/img/
        │ INSERT candidates
        │ redirect /kandidat + flash
```

#### Update
```
GET  /kandidat/ubah/<id> → SELECT satu baris → populate form
POST /kandidat/ubah/<id> → UPDATE ... WHERE id
```

#### Delete
```
[UI] klik Hapus → JS confirmDelete(nama)  (static/js/app.js)
        │ user cancel → stop
        │ user OK → GET /kandidat/hapus/<id>
        ▼
[BE] SELECT COUNT(*) ledger WHERE candidate_id
        │ > 0 → tolak (sudah ada suara di chain)
        │ 0   → DELETE candidates WHERE id
```

---

### 8.7 Flow voting (inti produk) — **end-to-end**

Ini alur paling penting: frontend coblos → backend atomik → Supabase + hash.

```
┌────────────── FRONTEND ──────────────┐
│ 1. Pemilih buka /vote atau tombol    │
│    di index.html                     │
│ 2. vote.html / kartu kandidat        │
│ 3. form.vote-form POST               │
│    action=/vote/<candidate_id>       │
│ 4. JS: confirmVote(nama)             │
│ 5. JS: disable semua .vote-btn       │
│    label "Menyimpan…" (anti double)  │
└──────────────────┬───────────────────┘
                   │ POST + session cookie
                   ▼
┌────────────── BACKEND app.py ────────┐
│ vote_submit(candidate_id)            │
│  · login_required                    │
│  · tolak jika role=admin             │
│  · tolak jika session.has_voted      │
│  · cast_vote(user_id, candidate_id)  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌────────────── cast_vote() ───────────┐
│ with get_db() as conn:  # 1 transaksi│
│                                      │
│ 1. pg_advisory_xact_lock(VOTE_LOCK)  │  serialisasi nomor blok
│ 2. SELECT users ... FOR UPDATE       │  kunci baris pemilih
│      · tidak ada / bukan pemilih     │
│      · has_voted true → reject       │
│ 3. SELECT ledger WHERE voter_npm     │  double-check di chain
│      · sudah ada → sync has_voted    │
│ 4. SELECT candidates WHERE id        │  validasi paslon
│ 5. SELECT last block FOR UPDATE      │  prev_hash + next_index
│      · kosong → index=0, prev=0×64   │
│ 6. create_block(...)  # blockchain.py│
│      · timestamp UTC ISO             │
│      · current_hash = SHA256(...)    │
│ 7. INSERT blockchain_ledger (...)    │  ★ data online
│ 8. UPDATE users SET has_voted=TRUE   │  ★ flag online
│      · rowcount harus 1              │
│ commit otomatis di get_db finally    │
└──────────────────┬───────────────────┘
                   │ result dict
                   ▼
┌────────────── RESPONSE ──────────────┐
│ session['has_voted'] = True          │
│ flash success + cuplikan hash        │
│ redirect /                           │
│                                      │
│ error path:                          │
│  · unique violation → already voted  │
│  · timeout DB → pesan coba lagi      │
│  · never leave open transaction      │
└──────────────────────────────────────┘
```

**Jaminan anti-stuck / anti-race**

| Mekanisme | Efek |
|-----------|------|
| `statement_timeout=20000` | Query max 20 detik |
| `get_db()` finally close | Tidak bocor koneksi |
| Advisory lock + FOR UPDATE | Dua vote bersamaan tidak bentrok index |
| UNIQUE `voter_npm` | DB menolak double vote |
| Disable tombol JS | User tidak spam POST |
| Transaksi tunggal | Insert ledger + update user commit bersama / rollback bersama |

**Setelah sukses, data di Supabase**

```sql
-- contoh
blockchain_ledger: (3, prev_hash, 1, '22.99.4106', '2026-...', '9ea3562b...')
users.has_voted = true WHERE npm = '22.99.4106'
```

Quick count di `/` naik karena `COUNT(*)` dari ledger.

---

### 8.8 Verifikasi rantai & cek hash — **real validation**

#### A. Validasi seluruh rantai (otomatis saat buka halaman)

```
[UI] GET /verifikasi
        ▼
[BE] verifikasi()
        │ fetch_ledger()  -- JOIN candidates untuk nama
        │ validate_chain(blocks)  -- blockchain.py
        │
        │ untuk setiap blok i:
        │   expected = compute_hash(index, prev_hash, candidate_id, npm, ts)
        │   jika expected != stored current_hash → INVALID (hash)
        │   jika i==0: prev harus GENESIS (0×64), index==0
        │   jika i>0: prev_hash == blocks[i-1].current_hash
        │            index == prev.index + 1
        │
        │ return is_valid, message, details[]
        ▼
[UI] verifikasi.html
        │ banner "Rantai valid / bermasalah"
        │ tabel tiap blok: status, hash short, tombol Salin, tombol Cek
        │ <details> expected hash, payload, link_note
```

#### B. Cek satu hash (paste / dari tombol Cek)

```
[UI] form POST /verifikasi  field hash=...
  atau GET /verifikasi?hash=...
        ▼
[BE] find_block_by_hash(blocks, query)
        │ strip + lower compare current_hash
        │ tidak ketemu → found=false
        │ ketemu → inspect_block (recompute + cek tautan)
        ▼
[UI] panel hasil: valid / invalid, stored vs expected, payload, Salin
```

#### C. API JSON

```
GET/POST /api/cek-hash?hash=<64hex>
        ▼
JSON {
  ok, found, block_index, hash_ok, link_ok,
  stored_hash, expected_hash, voter_npm, candidate_id,
  nama_paslon, timestamp, payload, message
}
```

#### D. Copy hash di frontend

```
[UI] klik [data-copy="..."]
[JS] navigator.clipboard.writeText / fallback textarea
     toast "Hash disalin" + label tombol "Tersalin"
```

**Penting:** perhitungan SHA-256 **hanya di server** (`hashlib`). JS tidak “mengarang” validitas.

---

### 8.9 Ledger admin

```
GET /ledger → admin_required
        │ fetch_ledger + validate_chain
        ▼
ledger.html: tabel blok, Salin hash, link Cek ke /verifikasi?hash=
```

---

### 8.10 Health check

```
GET /status → { database: online|offline, provider, connected }
```

Dipakai debugging / monitoring sederhana.

---

## 9. Template & static flow

### 9.1 Inheritance

```
base.html
  ├── block title
  ├── nav (menu dinamis role/session)
  ├── flash messages
  ├── block content   ← diisi child
  ├── footer (tanpa info DB)
  └── static/js/app.js + toast host
```

Child: `index`, `login`, `register`, `vote`, `verifikasi`, `ledger`, `kandidat_*`.

### 9.2 Static assets

| File | Peran di flow |
|------|----------------|
| `static/css/style.css` | Layout netral, panel, hash cell, status banner |
| `static/js/app.js` | confirm vote/delete, anti double-submit, copy hash |
| `static/img/*` | Foto paslon; dilayani `url_for('static', ...)` |

### 9.3 Jinja logic (contoh)

- `{% if session.get('has_voted') %}` — status coblos / sembunyikan menu.
- `{% for c in candidates %}` — list & progress %.
- `{% for d in details %}` — status valid per blok.
- Filter search di server; empty state di template.

---

## 10. Layer database (`db.py`)

| Fungsi | Perilaku |
|--------|----------|
| `get_connection()` | `psycopg2.connect` + connect_timeout 15s, keepalive, `statement_timeout=20s` |
| `is_connected()` | SELECT 1; selalu close |
| `get_db()` | Context manager: yield → commit; except → rollback; finally → close |
| `get_cursor(dict)` | `RealDictCursor` → `row['kolom']` |
| `init_db()` | schema.sql + constraint unique + seed admin |

Semua write path bisnis (vote, CRUD, register) memakai `with get_db()`.

---

## 11. Layer blockchain (`blockchain.py`)

| Fungsi | Input → Output |
|--------|----------------|
| `build_payload` | field blok → string mentah |
| `compute_hash` | field → hex SHA-256 64 char |
| `create_block` | index, prev, candidate, npm → dict blok lengkap |
| `inspect_block` | 1 blok (+ prev) → detail hash_ok, link_ok, expected, payload |
| `validate_chain` | list blok → `(valid, message, details[])` |
| `find_block_by_hash` | list + query → detail blok atau None |
| `GENESIS_HASH` | `"0" * 64` |

---

## 12. Mapping fitur UAS Flask-CRUD

| # | Fitur materi | Di mana di VoteChain |
|---|--------------|----------------------|
| 1 | Open connection MySQL/DB | `db.py` → Supabase PostgreSQL (`psycopg2`), `is_connected()`, `/status` |
| 2 | Read / fetch | `fetch_candidates`, `fetch_ledger`, index, list kandidat, verifikasi |
| 3 | Create / insert | Register, tambah kandidat, `INSERT blockchain_ledger` saat vote |
| 4 | Update | `kandidat_ubah`, `UPDATE users.has_voted` |
| 5 | Delete | `kandidat_hapus` (ditolak jika sudah ada suara) |
| 6 | JS confirm | `confirmDelete`, `confirmVote` di `app.js` |
| 7 | Template inheritance | `base.html` + `{% extends %}` / `{% block %}` |
| 8 | Jinja for/if | List kandidat, status vote, detail validasi |
| 9 | Static assets | `static/css`, `static/js`, `static/img`, `url_for` |
| 10 | Routing & redirect | Seluruh `@app.route`, `redirect(url_for)`, flash |

**Fitur domain tambahan:** hash-chain, cek hash, copy hash, advisory lock, anti double-vote.

---

## 13. Diagram alur aktor (ringkas)

### 13.1 Pemilih

```
Daftar → Login → Lihat hasil → Coblos (confirm) → Suara ke DB+hash
       → (opsional) Cek hash bukti → Logout
```

### 13.2 Admin

```
Login → CRUD kandidat → Pantau hasil → Ledger → Jalankan cek hash
     → (tidak coblos)
```

### 13.3 Publik / dosen penguji

```
Buka / → lihat quick count
Buka /verifikasi → lihat rantai valid
Salin hash → cek ulang /api/cek-hash atau form
```

---

## 14. Sequence: coblos sukses (teknis)

```
Browser          Flask              blockchain.py         Supabase
   │               │                      │                   │
   │ POST /vote/2  │                      │                   │
   │──────────────>│                      │                   │
   │               │ BEGIN + advisory lock│                   │
   │               │─────────────────────────────────────────>│
   │               │ FOR UPDATE user      │                   │
   │               │ SELECT last block    │                   │
   │               │ create_block()       │                   │
   │               │─────────────────────>│                   │
   │               │     hash, timestamp  │                   │
   │               │<─────────────────────│                   │
   │               │ INSERT ledger        │                   │
   │               │ UPDATE has_voted     │                   │
   │               │ COMMIT               │                   │
   │               │─────────────────────────────────────────>│
   │ 302 / + flash │                      │                   │
   │<──────────────│                      │                   │
   │ GET /         │ SELECT counts        │                   │
   │──────────────>│─────────────────────────────────────────>│
   │ HTML hasil↑   │                      │                   │
   │<──────────────│                      │                   │
```

---

## 15. Sequence: verifikasi hash

```
Browser                    Flask                         blockchain.py
   │ GET /verifikasi          │                                │
   │─────────────────────────>│ SELECT * ledger                │
   │                          │ validate_chain(blocks)         │
   │                          │───────────────────────────────>│
   │                          │  recompute tiap blok (hashlib) │
   │                          │  bandingkan stored vs expected │
   │                          │  cek prev_hash chain           │
   │                          │ details[]                      │
   │ HTML + status valid      │<───────────────────────────────│
   │<─────────────────────────│                                │
   │ klik Salin               │ (client clipboard only)        │
   │ POST hash=...            │ find_block_by_hash + inspect   │
   │─────────────────────────>│───────────────────────────────>│
   │ panel hasil valid/invalid│                                │
   │<─────────────────────────│                                │
```

---

## 16. Error handling & edge cases

| Kasus | Perilaku sistem |
|-------|-----------------|
| Belum login coblos | Redirect `/login` |
| Admin coblos | Ditolak, flash info |
| Sudah coblos, buka `/vote` | Redirect `/`, flash warning |
| Double POST vote | UNIQUE / has_voted / lock → 1 suara saja |
| Kandidat dihapus tapi sudah ada suara | Hapus ditolak |
| Hapus kandidat tanpa suara | OK |
| DB timeout | Flash "coba lagi", koneksi ditutup |
| Hash tidak di ledger | `found: false` |
| Data ledger ditamper | `hash_ok: false` / rantai invalid |
| Ledger kosong | Rantai dianggap valid (belum ada data) |
| Password salah | Flash error, tidak bocorkan detail hash |

---

## 17. Keamanan

| Area | Implementasi |
|------|----------------|
| Password | Hash satu arah Werkzeug (bukan enkripsi dua arah; **bukan** blockchain untuk password) |
| Session | Cookie HttpOnly Flask signed `SECRET_KEY` |
| SQL | Parameterized query `%s` (hindari injection) |
| Upload | `secure_filename`, allowlist ekstensi, max 2MB |
| Secret | `.env` + `.gitignore` |
| Integrity suara | Hash-chain + unique voter + validasi recompute |
| Admin vote | Diblok di UI & backend |

**Catatan produksi:** ganti password admin & DB setelah demo; jangan commit `.env`; pertimbangkan HTTPS & CSRF token untuk hardening lanjutan.

---

## 18. UX / UI requirements (terpenuhi di v1)

- Navigasi sederhana: Hasil · Cek hash · Coblos (kondisional) · Kandidat/Ledger (admin).
- Footer bersih tanpa teks infrastruktur DB.
- Tombol **Salin** pada setiap hash di daftar.
- Form **Cek satu hash** di `/verifikasi`.
- Feedback flash setelah aksi (success / warning / danger).
- Anti double-click pada coblos.
- Tampilan netral (bukan “template AI” berlebihan).

---

## 19. Kriteria penerimaan (acceptance criteria)

| ID | Kriteria | Cara verifikasi |
|----|----------|-----------------|
| AC1 | User bisa daftar & login | Flow register → login → session |
| AC2 | Admin CRUD kandidat | Tambah/ubah/hapus di UI |
| AC3 | Pemilih coblos 1× | Insert ledger + has_voted true |
| AC4 | Double vote gagal | Percobaan kedua ditolak; count ledger = 1 |
| AC5 | Hasil naik real-time (setelah reload) | COUNT dari ledger di index |
| AC6 | Validasi hash real | Ubah `candidate_id` di DB → /verifikasi invalid |
| AC7 | Copy hash | Tombol Salin → clipboard berisi 64 hex |
| AC8 | Cek hash paste | Form/API return found + hash_ok |
| AC9 | DB online | `/status` → connected true |
| AC10 | Template inheritance | Semua page extends base |

---

## 20. Menjalankan proyek

```bash
cd web
pip install -r requirements.txt
# pastikan .env berisi DATABASE_URL Supabase
python app.py
# buka http://127.0.0.1:5000
```

---

## 21. Glosarium

| Istilah | Arti di proyek ini |
|---------|-------------------|
| **Blok** | Satu baris `blockchain_ledger` = satu suara |
| **Ledger** | Seluruh rantai blok suara |
| **Genesis** | Blok pertama; `prev_hash` = 64 nol |
| **Current hash** | Hasil SHA-256 blok ini |
| **Prev hash** | Current hash blok sebelumnya (mengunci urutan) |
| **Recompute** | Hitung ulang hash dari field DB untuk validasi |
| **Advisory lock** | Kunci PostgreSQL agar penomoran blok tidak race |

---

## 22. Riwayat dokumen

| Versi | Tanggal | Catatan |
|-------|---------|---------|
| 1.0 | 2026-07-27 | PRD awal: arsitektur, skema, seluruh flow FE→BE, validasi hash real, mapping fitur UAS |

---

*Dokumen ini merefleksikan implementasi aktual di codebase VoteChain (`app.py`, `blockchain.py`, `db.py`, templates, static).*
