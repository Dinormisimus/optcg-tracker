# One Piece TCG Locals Stats Tracker

Aplikacija za praćenje statistike mečeva i vođenje lokalnih turnira u One Piece Trading Card Gameu (OP TCG). Omogućuje igračima praćenje postotka pobjeda (Win Rate) po Leaderima i protivnicima, bilježenje ishoda mečeva (bacanje kockice, tko ide prvi/drugi) te organizaciju lokalnih turnira.

Referentni backend projekt iz kolegija **Programiranje za web** na SIT UNIZD.

---

## 📁 Struktura projekta

```text
optcg-tracker/
├── api/                     # Backend (FastAPI)
│   ├── alembic/             # Skripte za baze i migracije
│   ├── app/
│   │   ├── core/            # Postavke, baza, JWT autorizacija i ovisnosti
│   │   ├── models/          # SQLAlchemy ORM modeli (User, Leader, Match, Tournament)
│   │   ├── repositories/    # SQL upiti i agregacije statistika
│   │   ├── routers/         # API endpoints (rute)
│   │   ├── schemas/         # Pydantic ulazne i izlazne sheme
│   │   ├── services/        # Poslovna logika i autorizacija
│   │   ├── __init__.py
│   │   └── main.py          # Glavna FastAPI aplikacija
│   ├── tests/               # Automatski testovi (pytest)
│   ├── alembic.ini
│   └── requirements.txt     # Python zavisnosti
├── docker-compose.yml       # PostgreSQL 17 kontejner
├── .env.example             # Predložak varijabli okoline
└── README.md

# Preduvjeti
Prije pokretanja projekta provjerite imate li instalirano:

Git
Python 3.11+
uv (brzi upravitelj Python paketima)
Docker Desktop (s alatom Docker Compose)

🚀 Pokretanje projekta (Korak po korak)

1. Konfiguracija okoline
Stvorite .env datoteku iz predloška u korijenu projekta:

```PowerShell
# PowerShell (Windows)
Copy-Item .env.example .env

# Bash / Linux / macOS
cp .env.example .env
```

2. Pokretanje baze podataka (PostgreSQL)
U korijenu projekta pokrenite bazu u Docker kontejneru:

```bash
docker compose up -d db
```

Status kontejnera provjerite naredbom 
```bash
docker compose ps
```

3. Priprema backenda i virtualnog okruženja
Ulazak u mapu api/, izrada okruženja alatom uv i instalacija zavisnosti:
```PowerShell
cd api

# Izrada virtualnog okruženja
uv venv

# Aktivacija okruženja (PowerShell na Windowsima)
.venv\Scripts\Activate.ps1

# Aktivacija okruženja (Git Bash / Linux / macOS)
# source .venv/Scripts/activate  (Git Bash)
# source .venv/bin/activate       (Linux/macOS)

# Instalacija paketa
uv pip install -r requirements.txt
```

4. Primjena migracija i punjenje baze
Stvaranje tablica u bazi i dodavanje inicijalnih podataka (Admin korisnik i službeni Leaderi):
```bash
alembic upgrade head
python -m app.seed
```

5. Pokretanje FastAPI poslužitelja
```bash
uvicorn app.main:app --reload
```

🔗 Linkovi za provjeru rada
Nakon pokretanja poslužitelja otvorite u pregledniku:

Health Check status: http://127.0.0.1:8000/health
(Očekivani odziv: {"status": "ok", "database": "PostgreSQL 17..."})

Swagger UI dokumentacija: http://127.0.0.1:8000/docs

📡 Trenutno dostupne backend rute
- `POST /auth/login` prima JSON: `{"username": "...", "password": "..."}`.
- `POST /auth/refresh` prima refresh token i vraća novi par tokena.
- `GET /auth/me` vraća prijavljenog korisnika.
- `GET /leaders` podržava `limit`, `offset` i opcionalni filter `color`.
- `GET /matches` vraća samo mečeve prijavljenog korisnika i podržava `limit` i
  `offset`.
- `GET`, `POST`, `PATCH` i `DELETE /matches/{match_id}` omogućuju upravljanje
  vlastitim mečevima. Meč vezan uz turnir mora imati broj kola.

🧪 Pokretanje testova
Testovi koriste zasebnu PostgreSQL bazu kako razvojni podaci ne bi bili dirani.
Po zadanim postavkama baza se naziva `optcg_db_test`; naziv se može promijeniti
varijablom `TEST_DATABASE_URL`.

```PowerShell
docker compose up -d db
cd api
pytest
```

Testna se baza priprema automatski pri prvom pokretanju testova, a tablice se
čiste prije svakog testa.

Rad s bazom i Alembic migracijama
Sve promjene u SQL strukturi izvode se kroz Alembic migracije:

```bash
cd api

# Stvaranje nove migracije nakon izmjene u models/
alembic revision --autogenerate -m "opis promjene"

# Primjena migracija na bazu
alembic upgrade head

# Poništavanje zadnje migracije
alembic downgrade -1

# Prikaz trenutne verzije baze
alembic current
```

Potpuno resetiranje baze
U slučaju pojave neusklađenosti ili rušenja testnih podataka:
```bash
# U korijenu projekta obrišite Docker kontejner i volumen
docker compose down -v

# Ponovno pokrenite bazu i napravite migracije
docker compose up -d db
cd api
alembic upgrade head
python -m app.seed
```

👥 Početni testni računi (app.seed)
Nakon pokretanja python -m app.seed, u bazi su dostupni sljedeći računi za testiranje:

| Uloga | Korisničko ime | Email | Lozinka |
|---|---|---|---|
| super_admin | superadmin | admin@example.com | Admin123! |
| admin | organizer | organizer@example.com | Organizer123! |
| user | player1 | player1@example.com | Player123! |

Prijava se obavlja korisničkim imenom i lozinkom.
