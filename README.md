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