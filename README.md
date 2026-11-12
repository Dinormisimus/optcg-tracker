# One Piece TCG Locals Stats Tracker

Backend aplikacija za bilježenje OP TCG mečeva, pregled Leader karata i
organizaciju lokalnih turnira. Igrači mogu pratiti svoje rezultate; organizator
može upravljati turnirima.

## Struktura

```text
api/
  alembic/       # migracije baze
  app/
    core/        # konfiguracija, baza, autentifikacija i greške
    models/      # SQLAlchemy modeli
    repositories/# upiti prema bazi
    routers/     # FastAPI rute
    schemas/     # Pydantic ulazne i izlazne sheme
    services/    # poslovna logika
  tests/         # pytest testovi
docker-compose.yml
.env.example
```

## Preduvjeti

- Windows 10/11 i PowerShell
- Git
- Python 3.11 ili noviji
- Docker Desktop s uključenim Docker Composeom

Provjeri instalacije iz PowerShella:

```powershell
py --version
docker --version
docker compose version
```

## Prvo pokretanje

Sve naredbe u ovom odjeljku izvršavaju se iz korijenske mape projekta
`optcg-tracker`.

### 1. Konfiguriraj varijable okoline

Napravi lokalnu `.env` datoteku iz predloška:

```powershell
Copy-Item .env.example .env
```

`.env` sadrži vezu prema bazi i JWT postavke. Datoteku nemoj commitati; Git je
ignorira. Za lokalni razvoj predložak već sadrži potrebne postavke.

### 2. Pokreni PostgreSQL u Dockeru

Pokreni Docker Desktop, zatim u PowerShellu:

```powershell
docker compose up -d db
docker compose ps
```

Pričekaj da servis `db` ima status `Up`. Ako se ne pokrene, pogledaj zapisnik:

```powershell
docker compose logs db
```

Projekt koristi PostgreSQL 17 na `localhost:5432`. Compose konfiguracija
stvara bazu `optcg_db`, korisnika `optcg_user` i razvojni volumen `pgdata`.

### 3. Napravi Python virtualno okruženje i instaliraj pakete

```powershell
Set-Location api
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Uspješna aktivacija obično se vidi po prefiksu `(.venv)` u retku PowerShella.
Ako PowerShell blokira aktivaciju skripte, jednokratno pokreni:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Zatvori i ponovno otvori terminal pa ponovi aktivaciju iz `api` mape. Alternativno,
možeš preskočiti aktivaciju i pozivati interpreter izravno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Napravi tablice i početne podatke

Dok si u mapi `api` i virtualno okruženje je aktivno:

```powershell
alembic upgrade head
python -m app.seed
```

Prva naredba primjenjuje sve Alembic migracije. Druga dodaje početne korisnike i
OP TCG Leadere. Seed se može pokrenuti više puta; postojeće korisnike i Leadere
ne dodaje ponovno.

### 5. Pokreni API

I dalje iz mape `api`:

```powershell
python -m uvicorn app.main:app --reload
```

Ostavi ovaj prozor terminala otvoren dok koristiš aplikaciju. Zaustavi server s
`Ctrl+C`.

### Brzi demo sučelja

Dok API radi, otvori novi PowerShell u korijenskoj mapi projekta i pokreni:

```powershell
py -m http.server 8765
```

Otvori `http://localhost:8765/web/login.html`. Za probu prijave koristi
`organizer` / `Organizer123!` (izradu turnira i mečeva) ili
`player1` / `Player123!` (mečeve). Demo stranice pozivaju lokalni API na portu
8000 i koriste razvojni CORS pristup koji je omogućen samo u `ENV="dev"`.

Otvori:

- Swagger UI: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

Health check vraća status API-ja i verziju PostgreSQL-a. Ako baza nije dostupna,
odgovor je HTTP `503`.

## Svakodnevno pokretanje

Nakon što su `.env`, virtualno okruženje, paketi, migracije i seed već postavljeni,
za svaki novi radni dan dovoljno je:

**PowerShell prozor 1 — baza, iz korijenske mape projekta:**

```powershell
docker compose up -d db
```

**PowerShell prozor 2 — API:**

```powershell
Set-Location "C:\putanja\do\optcg-tracker\api"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Zatim otvori <http://127.0.0.1:8000/docs>. Ako je terminal već otvoren u
korijenskoj mapi projekta, dovoljno je `Set-Location api` umjesto pune putanje.

## Početni korisnički računi

Nakon `python -m app.seed` dostupni su:

| Uloga | Korisničko ime | Email | Lozinka |
|---|---|---|---|
| super_admin | `superadmin` | `admin@example.com` | `Admin123!` |
| admin | `organizer` | `organizer@example.com` | `Organizer123!` |
| user | `player1` | `player1@example.com` | `Player123!` |

Prijava se obavlja korisničkim imenom i lozinkom. Lokalni testni računi služe
samo za razvoj — nemoj koristiti te lozinke u produkciji.

## Trenutačne API rute

Zaštićene rute traže JWT access token. Swaggeru ga možeš dati preko **Authorize**
gumba nakon poziva `POST /auth/login`.

| Metoda | Ruta | Namjena |
|---|---|---|
| `GET` | `/health` | Provjera API-ja i baze |
| `POST` | `/auth/login` | Prijava i dobivanje tokena |
| `POST` | `/auth/refresh` | Obnova tokena |
| `GET` | `/auth/me` | Podaci prijavljenog korisnika |
| `GET` | `/leaders` | Popis Leadera; filter `color`, `limit`, `offset` |
| `POST` | `/leaders` | Dodavanje Leadera (admin) |
| `GET` | `/matches` | Vlastiti mečevi; `limit`, `offset` |
| `POST` | `/matches` | Bilježenje meča |
| `GET` | `/matches/{match_id}` | Dohvat vlastitog meča |
| `PATCH` | `/matches/{match_id}` | Izmjena vlastitog meča |
| `DELETE` | `/matches/{match_id}` | Brisanje vlastitog meča |
| `GET` | `/tournaments` | Popis turnira; `limit`, `offset` |
| `GET` | `/tournaments/mine` | Turniri na kojima sudjeluje prijavljeni korisnik |
| `POST` | `/tournaments` | Stvaranje turnira (admin) |
| `GET` | `/tournaments/{tournament_id}` | Dohvat turnira |
| `GET` | `/tournaments/{tournament_id}/participants` | Prijavljeni igrači i njihovi Leaderi |
| `POST` | `/tournaments/{tournament_id}/participants/me` | Prijava na turnir uz odabir Leadera |
| `GET` | `/tournaments/{tournament_id}/participants/me` | Pregled vlastite prijave i Leadera |
| `PATCH` | `/tournaments/{tournament_id}/participants/me` | Promjena Leadera prije prvog meča |
| `DELETE` | `/tournaments/{tournament_id}/participants/me` | Odjava prije prvog meča |
| `PATCH` | `/tournaments/{tournament_id}` | Izmjena turnira (organizator ili superadmin) |
| `DELETE` | `/tournaments/{tournament_id}` | Brisanje praznog turnira |
| `GET` | `/stats/overall` | Ukupna statistika prijavljenog korisnika |
| `GET` | `/stats/leaders` | Statistika s vlastitim Leaderima |
| `GET` | `/stats/opponents` | Statistika po imenu protivnika |
| `GET` | `/stats/opponent-leaders` | Statistika protiv protivničkih Leadera |
| `GET` | `/stats/matchups` | Statistika po protivniku i njegovu Leaderu |

Igrač može pregledavati turnire, ali samo organizator turnira ili
superadministrator može ga izmijeniti ili obrisati. Turnir s povezanim mečevima
ne može se obrisati. Mečevi su vidljivi i izmjenjivi samo korisniku koji ih je
zabilježio. Prijavljeni igrač bira Leadera za svaki turnir zasebno. Taj odabir
može promijeniti do svojeg prvog meča na turniru; nakon toga ne može promijeniti
Leadera ni odjaviti se s turnira. Turnir služi za grupiranje mečeva i pregled
statistike. Za unos turnirskog meča prijavljen mora biti samo korisnik koji
bilježi meč; protivnik ne mora imati korisnički račun niti biti prijavljen na
turnir. Protivničko ime i Leader unose se radi statistike.

Statistika se računa iz mečeva koje je prijavljeni korisnik zabilježio. Winrate
je postotak pobjeda među odlučenim mečevima (`pobjede / (pobjede + porazi)`),
tako da se neodlučeni mečevi prikazuju u ukupnom broju, ali ne ulaze u izračun
winratea. Statistika protivnika grupira imena bez obzira na velika/mala slova i
razmake na početku ili kraju. Liste po Leaderu i protivniku podržavaju
`limit` i `offset`.

## Testovi

Testovi koriste zasebnu PostgreSQL bazu `optcg_db_test`, tako da ne brišu
razvojne podatke iz `optcg_db`. Docker baza mora biti pokrenuta. Iz mape `api`,
uz aktivno virtualno okruženje, pokreni:

```powershell
pytest
```

Testna se baza priprema automatski, a tablice se prazne prije svakog testa.
Vlastitu testnu vezu možeš zadati varijablom okoline `TEST_DATABASE_URL`.
**Nemoj je postaviti na razvojnu bazu** jer testovi brišu tablice u testnoj bazi.

## Alembic migracije

Sve promjene sheme baze moraju biti zapisane migracijama. Iz mape `api`:

```powershell
# Napravi migraciju nakon promjene SQLAlchemy modela
alembic revision --autogenerate -m "opis promjene"

# Prije primjene pročitaj i pregledaj generiranu migraciju
alembic upgrade head

# Provjeri trenutačnu verziju baze
alembic current

# Vrati jednu migraciju
alembic downgrade -1
```

Autogeneriranu migraciju uvijek pregledaj prije primjene, posebno promjene koje
uključuju preimenovanje stupaca ili brisanje podataka.

## Česti problemi

**`/docs` se ne otvara**

- Provjeri da Uvicorn još radi i da terminal nije zatvoren.
- Provjeri adresu <http://127.0.0.1:8000/docs>.
- Ako je port zauzet, pokreni na drugom portu:
  `python -m uvicorn app.main:app --reload --port 8001`.

**API javlja da se ne može spojiti na bazu**

- Provjeri da Docker Desktop radi.
- Iz korijenske mape pokreni `docker compose ps`.
- Po potrebi pogledaj `docker compose logs db`.
- Provjeri da `.env` sadrži ispravnu `DATABASE_URL` za lokalni PostgreSQL servis.

**Naredba `alembic` ili `uvicorn` nije pronađena**

- Provjeri da si u mapi `api` i da je virtualno okruženje aktivirano.
- Ili pokreni naredbu kroz interpreter virtualnog okruženja, npr.
  `.\.venv\Scripts\python.exe -m alembic upgrade head`.

**Import ili paket nedostaje**

```powershell
Set-Location api
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Potpuni reset lokalne baze

Ovo briše Docker volumen i **sve podatke u lokalnoj razvojnoj bazi**. Koristi
samo ako želiš krenuti od prazne baze:

```powershell
# Iz korijenske mape projekta; zaustavi API s Ctrl+C prije toga
docker compose down -v
docker compose up -d db

# Zatim iz api mape, s aktivnim .venv
Set-Location api
alembic upgrade head
python -m app.seed
```

## Kvaliteta koda

Iz mape `api`:

```powershell
ruff check .
ruff format --check .
pytest
```
