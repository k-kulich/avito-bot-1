# Avito Monitor Bot — Telegram Ad Monitoring Service

A Telegram bot that continuously monitors **Avito** for new listings matching user‑defined search queries and delivers real‑time notifications. Built with `python-telegram-bot` v20, asynchronous SQLAlchemy over PostgreSQL, and an async Avito scraper with rotating headers and proxy support.

The project is designed as a **multi‑user, long‑running service**: each user maintains their own set of search queries, can pause or resume them independently, and only receives each listing once. The bot runs a continuous background monitoring loop alongside the Telegram update loop.

## Overview

Users interact with the bot entirely through an inline keyboard interface:

1. Add a search query by choosing a city and typing a query string (e.g. `квартиры студии`).
2. The bot periodically re‑runs every active query, parses new listings, and pushes notifications.
3. Each listing is tracked per user in a `sent_ads` table, so no duplicate notifications are ever sent.
4. Queries can be toggled on/off without deleting them.

Under the hood, a `MonitorManager` orchestrates monitoring cycles, dispatches parsed ads to registered callbacks, and persists state through an async SQLAlchemy session factory shared with the bot handlers.

## Architecture at a Glance

```mermaid
flowchart LR
    subgraph Telegram
        U[User]
    end

    subgraph Bot["Telegram Bot"]
        H[Handlers<br/>commands · callbacks · messages]
        KB[Keyboards]
    end

    subgraph Core["Service Layer"]
        US[user_service]
        CS[city_service]
        QS[query_service]
        AS[ad_service]
    end

    subgraph Monitor["Monitoring Engine"]
        MM[MonitorManager<br/>continuous loop]
        AV[AvitoMonitor<br/>async scraper]
    end

    subgraph Storage
        DB[(PostgreSQL<br/>async SQLAlchemy)]
    end

    AVITO[(Avito)]
    TGAPI[(Telegram Bot API)]

    U -->|inline buttons / text| H
    H --> KB
    H --> US
    H --> CS
    H --> QS
    US --> DB
    CS --> DB
    QS --> DB

    MM -->|fetch active queries| DB
    MM -->|search ads| AV
    AV -->|HTTP + proxy rotation| AVITO
    MM -->|is_ad_sent / mark_ad_sent| AS
    AS --> DB

    MM -->|dispatch new ads| TGAPI
    TGAPI --> U
```

## Key Features

### Telegram Bot
- **`/start`** — registers the user and shows the main menu.
- **`/stop`** — deactivates the user’s subscription without deleting their queries.
- **`/status`** — reports current subscription status.
- **Inline keyboard UI** — add queries, list queries, toggle them, and view help without typing commands.
- **Guided query creation flow** — city search with disambiguation via `city_choice_keyboard`, followed by a free‑text query step.
- **Formatted notifications** — Markdown‑rendered ad messages including title, price, URL, and metadata.

### Avito Scraper (`AvitoMonitor`)
- **Asynchronous HTTP** via `aiohttp` with connection reuse through a shared `ClientSession`.
- **Rotating header pools** — multiple realistic `User-Agent` / `Accept-Language` combinations to reduce fingerprinting.
- **Proxy support** — optional per‑request proxy selection.
- **Retry logic** — up to 4 attempts per request with exponential backoff and IP rotation through `rest-app.net` on failure.
- **HTML parsing** with `BeautifulSoup`:
  - Title, URL, price, description, address, seller name.
  - Image extraction from `img[data-marker="item-photo"]`.
  - Timestamp parsing for `сегодня`, `вчера`, and absolute dates via `dateutil`.
  - Ad ID extraction with regex fallback to a content hash.
- **Detail enrichment** (`get_ad_details`) — fetches phone, total views, and geo coordinates from a listing page when needed.
- **Region and city bootstrap** — helper to download reference data from `rest-app.net` into JSON files.

### Data Model (SQLAlchemy 2.0, async)
- **`User`** — `chat_id`, `username`, `first_name`, `is_active`, `is_admin`, `created_at`, `last_notified`.
- **`City`** — slug, title, region, with a unique index on slug.
- **`SearchQuery`** — per‑user query with `city_id`, `query_string`, `is_active`, and a generated short hash ID.
- **`SentAd`** — per‑user `(user_id, ad_id)` pair preventing duplicate notifications, with `ad_url` and `sent_at`.
- Relationships use cascading deletes so removing a user cleans up their queries and history.

```mermaid
erDiagram
    USER ||--o{ SEARCH_QUERY : "owns"
    USER ||--o{ SENT_AD : "received"
    CITY ||--o{ SEARCH_QUERY : "targets"

    USER {
        int chat_id PK
        string username
        string first_name
        bool is_active
        bool is_admin
        datetime created_at
        datetime last_notified
    }

    CITY {
        int id PK
        string slug UK
        string title
        string region
    }

    SEARCH_QUERY {
        string id PK
        int user_id FK
        int city_id FK
        string query_string
        bool is_active
    }

    SENT_AD {
        int id PK
        int user_id FK
        string ad_id
        string ad_url
        datetime sent_at
    }
```

### Service Layer
The project follows a thin‑service pattern, with each domain isolated in its own module:
- `user_service` — get, create, update, and fetch active users.
- `city_service` — one‑time seeding from JSON, transliteration‑based slug generation, fuzzy search, and lookup by slug or ID.
- `query_service` — create, toggle, delete, and list user queries.
- `ad_service` — idempotent “has this ad already been sent to this user” checks and marking.

### Monitoring Engine (`MonitorManager`)
- **Query aggregation** — joins `SearchQuery` with `User` to fetch only active queries of active users.
- **Dataclass bridging** — converts ORM models to `SearchQueryDC` so the parser has no DB dependency.
- **Observer pattern** — callbacks are registered once (`add_callback`) and invoked for each new ad per user, which decouples the bot from the monitoring engine.
- **Continuous loop** — `start_continuous_monitoring(interval=300)` respects a target interval regardless of processing time and backs off on errors.
- **Graceful shutdown** — handles `asyncio.CancelledError` and logs the stop.

### Configuration & Startup
- Environment‑driven via `python-dotenv` and `lib/core/config.py` (`TELEGRAM_TOKEN`, `DATABASE_URL`, `CHANGE_IP`).
- `run.py` bootstraps everything in one place:
  1. Creates tables from declarative metadata.
  2. Seeds the city reference table.
  3. Instantiates and runs the bot.
- Async engine uses `asyncpg` with `expire_on_commit=False` for safe post‑commit attribute access.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Language** | Python 3.10+ |
| **Bot** | `python-telegram-bot` 20.7 |
| **HTTP / Parsing** | `aiohttp`, `BeautifulSoup4`, `lxml` |
| **Persistence** | PostgreSQL, SQLAlchemy 2.0 (async), `asyncpg` |
| **Data Modeling** | `dataclasses`, `dataclasses-json` |
| **Utilities** | `python-dateutil`, `python-dotenv`, `hashlib`, `re` |

## Architecture

```
avito-monitor-bot/
├── run.py                      # Entry point: DB init, city seeding, bot launch
├── requirements.txt
├── lib/
│   ├── core/
│   │   ├── config.py           # Env vars: TELEGRAM_TOKEN, DATABASE_URL, CHANGE_IP
│   │   └── database.py         # Async engine, session factory, Base
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── city.py
│   │   ├── search_query.py
│   │   └── sent_ad.py
│   ├── services/               # Domain logic
│   │   ├── user_service.py
│   │   ├── city_service.py
│   │   ├── query_service.py
│   │   └── ad_service.py
│   ├── parser/
│   │   └── avito_parser.py     # AvitoMonitor (async scraper)
│   ├── monitor/
│   │   └── monitor_manager.py  # Monitoring loop + callback dispatch
│   ├── bot/
│   │   ├── bot.py              # AvitoBot, Application wiring
│   │   ├── commands.py         # /start, /stop, /status
│   │   ├── callbacks.py        # Inline button handlers
│   │   ├── handlers.py         # Handler registration
│   │   ├── keyboards.py        # Reply / inline keyboards
│   │   └── messages.py         # Text templates and message handler
│   └── data_classes.py         # SearchQueryDC, AdItemDC
└── data/                       # Seeded JSON reference files
    ├── all_regions.json
    └── all_cities.json
```

## How It Works

**Startup (`run.py`)**

1. `Base.metadata.create_all` runs through the async engine.
2. `init_cities` checks whether the `cities` table is empty; if so, loads `data/all_cities.json`, generates missing slugs via transliteration, and commits.
3. `AvitoBot` is constructed: it builds the `Application`, wires handlers, and instantiates a `MonitorManager`.
4. `bot.run()`:
   - Registers `send_ad_notification` as a monitor callback.
   - Launches `start_continuous_monitoring()` as a background task.
   - Initializes and starts the bot’s polling loop.
   - Keeps the process alive while both loops run.

**Monitoring cycle**

1. Fetch all `SearchQuery` records joined with active `User`s.
2. For each query, convert to `SearchQueryDC` and call `AvitoMonitor.search_ads`.
3. For every returned `AdItemDC`, check `is_ad_sent(user_id, ad_id)`.
4. If new, call every registered callback (currently the Telegram notifier) and mark the ad as sent.
5. Sleep for the remainder of the target interval, with error backoff.

```mermaid
sequenceDiagram
    autonumber
    participant MM as MonitorManager
    participant DB as PostgreSQL
    participant AV as AvitoMonitor
    participant AVITO as Avito
    participant CB as Callbacks (Telegram)

    loop every interval
        MM->>DB: SELECT active SearchQuery JOIN active User
        DB-->>MM: list of queries

        loop each query
            MM->>AV: search_ads(SearchQueryDC)
            AV->>AVITO: GET /{city}?q={query}
            AVITO-->>AV: HTML
            AV-->>MM: list[AdItemDC]

            loop each ad
                MM->>DB: is_ad_sent(user_id, ad_id)?
                DB-->>MM: true / false
                alt new ad
                    MM->>CB: callback(user_id, ad)
                    CB-->>CB: send Telegram message
                    MM->>DB: mark_ad_sent(user_id, ad_id)
                else already sent
                    MM-->>MM: skip
                end
            end
        end

        MM->>MM: sleep(remaining interval)
    end
```

**Notification**

`AvitoBot.send_ad_notification` sends a Markdown‑formatted message to the user’s `chat_id` via `application.bot.send_message`.

## Usage

### Prerequisites
- Python 3.10+
- PostgreSQL instance
- Telegram bot token from [@BotFather](https://t.me/BotFather)

### Install

```bash
pip install -r requirements.txt
```

### Configure

Create a `.env` file:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
CHANGE_IP=https://rest-app.net/api/change-ip
```

### Run

```bash
python run.py
```

The script creates tables, seeds cities (on first run), and starts the bot. Open the bot in Telegram and press **Start**.

### Optional: refresh reference data

`AvitoMonitor._get_regions_and_cities()` can be called once to regenerate `data/all_regions.json` and `data/all_cities.json` from the `rest-app.net` API.

## What This Project Demonstrates

- **End‑to‑end service architecture** — the bot is not a script; it’s a long‑running service with persistent state, a background worker, and a clean service layer.
- **Asynchronous design** — `aiohttp`, async SQLAlchemy, and coordinated tasks (`asyncio.create_task`) running alongside `python-telegram-bot`’s polling loop.
- **Multi‑user correctness** — per‑user deduplication of ads, independent query toggling, and cascade deletes.
- **Resilient scraping** — header rotation, proxy support, retry with backoff, and IP rotation on failure.
- **Domain modeling** — ORM models mirror the business flow (users → queries → sent ads), and dataclasses decouple the parser from persistence.
- **Separation of concerns** — bot handlers, services, parser, and monitoring loop live in distinct modules with narrow interfaces.
- **Environment‑driven configuration** — tokens, DB URL, and IP rotation endpoint are all injectable via `.env`, suitable for deployment.
- **Observer pattern for notifications** — the monitor engine emits ads to any registered callback, so the Telegram layer can be swapped without touching the monitoring logic.

## Possible Improvements

- Add rate limiting and per‑user cooldowns to avoid Telegram flood limits.
- Introduce a job queue (e.g. Redis + `arq`) instead of in‑process `asyncio` tasks for horizontal scaling.
- Add structured logging with request/response correlation IDs.
- Add unit tests for `_parse_search_page` and `rewrite`‑style timestamp parsing.
- Support paginated Avito result pages and price/room filters via the UI.
- Containerize with Docker Compose (`bot + postgres`) for one‑command deployment.
- Add metrics (Prometheus) for parsed ads, requests, and failures.
