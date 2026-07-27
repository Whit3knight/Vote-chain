# VoteChain — E-Voting Mahasiswa + Blockchain

Sistem e-voting kampus berbasis **Flask + Supabase PostgreSQL** dengan pencatatan suara ke **hash-chain SHA-256**.

> Meskipun admin punya akses database, suara yang sudah masuk **tidak bisa dimanipulasi** tanpa merusak rantai blockchain (terdeteksi di halaman Verifikasi).

## Fitur (memenuhi 10 fitur UAS Flask-CRUD)

| # | Fitur materi | Implementasi VoteChain |
|---|--------------|------------------------|
| 1 | Koneksi DB | Supabase PostgreSQL (`psycopg2`) + cek `is_connected()` |
| 2 | Read data | Quick count, daftar kandidat, ledger |
| 3 | Create data | Registrasi, tambah kandidat, cast vote → blok baru |
| 4 | Update data | Ubah data kandidat |
| 5 | Delete data | Hapus kandidat (dengan proteksi jika sudah ada suara) |
| 6 | JS Confirm | Konfirmasi hapus & coblos |
| 7 | Template inheritance | `base.html` + `{% extends %}` / `{% block %}` |
| 8 | Jinja2 logic | `{% for %}`, `{% if %}`, filter pencarian |
| 9 | Static assets | `static/css`, `static/js`, `static/img` + `url_for` |
| 10 | Routing & redirect | `@app.route`, flash message, `redirect(url_for(...))` |

### Fitur domain VoteChain
- Auth pemilih & admin (password di-hash `werkzeug.security`)
- Anti double voting (`has_voted`)
- Blockchain engine: `Hash = SHA256(index + prev_hash + candidate_id + npm + timestamp)`
- Halaman verifikasi integritas ledger (publik)
- Quick count real-time

## Stack
- **Backend:** Flask 3
- **Database online:** Supabase (PostgreSQL)
- **Frontend:** Bootstrap 5 + Jinja2
- **Blockchain:** modul Python murni (`hashlib`)

## Setup lokal

```bash
cd web
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Buat file `.env` (sudah disediakan, jangan di-commit):

```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres
SECRET_KEY=ganti-dengan-rahasia-anda
FLASK_DEBUG=1
```

Jalankan:

```bash
python app.py
```

Buka http://127.0.0.1:5000

### Akun default
| Role  | NPM / user | Password  |
|-------|------------|-----------|
| Admin | `admin`    | `admin123`|

Registrasi pemilih lewat menu **Daftar**.

## Struktur

```
web/
├── app.py              # Routing & logic Flask
├── blockchain.py       # Engine hash-chain SHA-256
├── db.py               # Koneksi Supabase + init schema
├── schema.sql          # DDL tabel
├── requirements.txt
├── .env                # rahasia (di-gitignore)
├── templates/          # Jinja2 (extends base.html)
└── static/
    ├── css/style.css
    ├── js/app.js
    └── img/            # foto paslon
```

## Skema database (Supabase)

1. `users` — id, npm, nama, password, role, has_voted  
2. `candidates` — id, nama_paslon, visi_misi, foto  
3. `blockchain_ledger` — block_index, prev_hash, candidate_id, voter_npm, timestamp, current_hash  

Tabel dibuat otomatis saat `python app.py` pertama kali.

## Deploy (Render / PythonAnywhere)

1. Push ke GitHub (**tanpa** file `.env`)
2. Set environment variable `DATABASE_URL` dan `SECRET_KEY` di dashboard host
3. Start command: `gunicorn app:app` (tambahkan `gunicorn` ke requirements jika perlu)

## Keamanan

- Jangan commit `.env` / password database
- Ganti password admin setelah demo
- Password user di-hash (bukan di-enkripsi dua arah)
- Blockchain dipakai untuk **integritas suara**, bukan penyimpanan password
