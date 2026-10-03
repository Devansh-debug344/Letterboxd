# BingeSaga

A full-stack film diary application for discovering films, tracking watch status, and publishing rated reviews.

## Overview

BingeSaga is a React single-page application backed by an asynchronous FastAPI API. It gives users a place to search and browse movie data, keep a watchlist, record watched films with an optional rating and date, and create one review per film. Public profile statistics, movie statistics, person pages, and movie reviews are also exposed by the API.

The implementation combines a PostgreSQL source of record with Redis for short-lived response caching and rate limiting. Movie metadata is retrieved from TMDB and normalized into the application's movie shape; optional background work moves movie artwork to Cloudinary. Celery keeps artwork processing and authentication audit persistence off the request path.

## Features

### Accounts and profiles

- Username/email registration and form-based login
- JWT access tokens and rotating, database-backed refresh tokens
- Logout of the current session or all sessions
- Optional phone OTP sign-in through Twilio
- Profile editing, avatar upload, public user statistics, and paginated user reviews

### Movie discovery and library

- TMDB-backed title search, trending and popular collections, movie details, and person filmographies
- Local persistence of movie metadata when a movie is added to a library feature or viewed by ID
- Personal watchlist with duplicate prevention
- Watched list with optional rating and watched-at timestamp; marking a film watched removes it from the watchlist
- Per-movie statistics for reviews, ratings, watched entries, and watchlist entries

### Reviews and media

- Create, update, list, and delete reviews with a 0.5–5 rating and spoiler flag
- One review, watchlist entry, and watched entry per user/movie pair
- Authenticated image uploads and signed direct-upload parameters when Cloudinary is configured
- Background poster/backdrop import to Cloudinary, with retryable Celery tasks

### Operational behavior

- Redis-backed fixed-window rate limits on authentication, read, discovery, and write routes
- Redis response caching with cache invalidation/versioning around library and review changes
- Best-effort, batched authentication audit events dispatched to Celery

## Tech Stack

### Frontend

- React 19, TypeScript, React Router, and Vite
- TanStack Query for server-state queries and Zustand for persisted authentication tokens
- Axios for API requests and token-refresh interception
- Tailwind CSS/PostCSS, Framer Motion, and Lucide React

### Backend

- Python 3.11 (the Docker image) and FastAPI
- SQLAlchemy 2 asynchronous sessions with `asyncpg`; SQLite support is used by the test suite
- Pydantic 2 schemas and Alembic migrations
- `python-jose` JWTs, OAuth2 bearer-token dependency, and Argon2 password hashing via Passlib
- HTTPX for TMDB and artwork requests; Celery for background tasks

### Database and infrastructure

- PostgreSQL for application data
- Redis for caching, rate limits, OTP state, and—by default—Celery broker/result storage
- Docker and Docker Compose for the backend, Celery worker, and Nginx reverse proxy
- Nginx TLS proxy configuration for the deployed backend

### External services

- [TMDB](https://www.themoviedb.org/) for movie and person data
- [Cloudinary](https://cloudinary.com/) for optional avatars, user media, and imported movie artwork
- [Twilio](https://www.twilio.com/) for optional SMS OTP delivery

## Architecture

The active client is a Vite React SPA. Its API modules call the FastAPI routes under `/api`; Axios attaches a bearer access token and uses a single shared refresh request after a `401`. The backend organizes code by route handlers (`app/api`), Pydantic request/response schemas, CRUD functions, SQLAlchemy models, and focused services for caching, external data, authentication, and background dispatch.

```mermaid
flowchart TD
    U[Browser] --> F[React + Vite frontend]
    F -->|/api| A[FastAPI]
    A --> P[(PostgreSQL)]
    A --> R[(Redis)]
    A --> T[TMDB API]
    A --> D[Background dispatcher]
    D --> C[Celery worker]
    C --> P
    C --> CL[Cloudinary]
    A --> CL
    A --> TW[Twilio]
    N[Nginx in Docker deployment] --> A
```

- Routes use dependencies to open an async database session and, where needed, require the current bearer-token user.
- CRUD modules contain SQLAlchemy queries and writes. PostgreSQL/SQLite-specific `INSERT ... ON CONFLICT DO NOTHING` statements make duplicate list and review creation idempotent.
- The lifespan hook initializes Redis, starts the bounded Celery-publisher queue and audit batcher, then closes the HTTP client, Redis pool, and database engine on shutdown.
- Celery tasks create their own database sessions. Movie artwork processing downloads TMDB artwork, uploads it to Cloudinary, updates the movie record, and retries transient failures; audit events are persisted in batches.

## Caching

Two independent caches are present.

**Application response cache.** Redis JSON values are prefixed `bingesaga:db:v1:`. For five minutes, the API caches movie details (`movie:{id}`), movie stats (`movie:{id}:stats`), user stats (`user:{id}:stats`), a user's watchlist and watched list, and paginated review lists. Review-list keys include a version segment, such as `user:{id}:reviews:v{n}:all:{page}:{limit}` and `movie:{id}:reviews:v{n}:{page}:{limit}`. Creating, updating, or deleting reviews bumps the matching version; list, review, watched, and profile mutations invalidate related keys.

**TMDB adapter cache.** External movie, search, person, and collection responses use keys under `bingesaga:cache:v1:` and a 15-minute TTL. The adapter follows cache-aside behavior: read Redis first, fetch on a miss, then populate the cache. Its per-process `_in_flight` task map coalesces concurrent requests for the same external key. If Redis is absent or an external-cache operation fails, it uses a process-local TTL cache instead. The response cache simply behaves as a cache miss when Redis is unavailable.

Redis connection pooling uses health checks, bounded connect/command timeouts, TCP keepalive, and one retry for idempotent cache reads, writes, and deletes. The fixed-window limiter and OTP storage require Redis; the rate limiter deliberately becomes a no-op if Redis is unavailable. TMDB requests use a Redis-backed process-wide limit of 30 requests per 60 seconds when Redis is available.

## Database

PostgreSQL is accessed through asynchronous SQLAlchemy sessions. The core tables are `users`, `movies`, `watchlist`, `watched`, `reviews`, `refresh_tokens`, and `auth_events`.

- `watchlist`, `watched`, and `reviews` join users to movies. Each has a unique user/movie constraint, preventing duplicate entries; reviews are additionally indexed by user and movie.
- User, movie, and refresh-token relationships use foreign keys with cascade deletion. Movies have a unique, indexed external identifier (`imdb_id`—despite the name, the current TMDB adapter stores TMDB IDs in this field).
- Refresh tokens are stored as SHA-256 hashes, indexed uniquely, and track revocation, rotation, and expiry. Authentication events are indexed by event type and creation time.
- Alembic migration history creates the schema and evolves watched/review constraints, timezone-aware timestamps, avatars, and Cloudinary artwork fields. Run migrations from `backend/` with `alembic upgrade head`.

## Authentication & Security

The API signs HS256 JWT access tokens containing the user ID; access tokens expire after 50 minutes. Passwords are hashed with Argon2. The OAuth2 bearer dependency protects profile, watchlist, watched, review, media, and logout operations.

Login and OTP verification issue an opaque refresh token as well as an access token. Only a SHA-256 hash of the refresh token is persisted. Refresh rotation marks the old token as used; reusing a rotated token revokes all of that user's refresh tokens. The default refresh-token lifetime is seven days and can be changed with `REFRESH_TOKEN_EXPIRE_DAYS`.

Redis rate limiting is applied to authentication and most API operations. Avatar and media uploads require authentication, validate content type, and cap files at 5 MB. Cloudinary credentials, the JWT signing secret, database URL, and external API credentials are supplied through environment variables and should never be committed.

The current FastAPI CORS configuration allows all origins while enabling credentials. Treat that as an implementation detail to review before exposing the service beyond its intended deployment.

## API

All routes below are mounted beneath `/api`. Protected endpoints require `Authorization: Bearer <access-token>`.

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/login` | Form-encoded username/password login; returns access and refresh tokens. |
| POST | `/refresh` | Rotate a refresh token and return a new token pair. |
| POST | `/logout` | Revoke the user's active refresh tokens. |
| POST | `/logout-all` | Revoke all of the user's refresh tokens. |
| POST | `/otp/send` | Send an OTP to a phone number. |
| POST | `/otp/verify` | Verify an OTP; creates an OTP-backed user if necessary and returns tokens. |
| POST | `/user/` | Register a user. |

### Users and media

| Method | Endpoint | Description |
| --- | --- | --- |
| GET / PATCH | `/user/profile` | Read or update the authenticated user's profile. |
| POST | `/user/avatar` | Upload the authenticated user's avatar to Cloudinary. |
| GET | `/user/{user_id}/stats` | Get public watched/review/watchlist counts and average review rating. |
| GET | `/user/{user_id}/reviews` | Get paginated reviews for a user. |
| POST | `/media/upload` | Upload an authenticated user's image to Cloudinary. |
| GET | `/media/upload-signature` | Get signed Cloudinary parameters for a direct upload. |

### Movies

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/movies/search?search=` | Search a saved exact-title match or TMDB. |
| GET | `/movies/discover/{collection}?page=` | Get `trending` or `popular` TMDB movies. |
| GET | `/movies/person/{person_id}` | Get a TMDB person's profile and filmography. |
| GET | `/movies/{omdb_id}` | Get or import a movie by its stored external ID. |
| GET | `/movies/{omdb_id}/stats` | Get aggregate application statistics for a movie. |

### Watchlist, watched films, and reviews

| Method | Endpoint | Description |
| --- | --- | --- |
| GET / POST / DELETE | `/watchlist/` | List, add, or remove an authenticated user's watchlist movie. |
| GET / POST | `/watched/` | List watched entries or record a watched movie. |
| DELETE | `/watched/{omdb_id}` | Remove a watched entry. |
| GET / POST / PATCH / DELETE | `/review/` | List the current user's reviews, or create, edit, or delete one. |
| GET | `/review/movie/{omdb_id}` | Get paginated reviews for a movie. |

The route parameter and request field are named `omdb_id` for compatibility with the existing API shape; the current TMDB adapter supplies TMDB IDs.

## Project Structure

```text
.
├── backend/
│   ├── alembic/                 # Migration environment and revisions
│   ├── app/
│   │   ├── api/                 # FastAPI routers
│   │   ├── auth/                # JWT dependency and token creation
│   │   ├── crud/                # SQLAlchemy data-access functions
│   │   ├── db/                  # Async sessions, Redis, upsert helper
│   │   ├── models/              # ORM models
│   │   ├── schemas/             # Pydantic models
│   │   ├── services/            # Cache, TMDB, OTP, media, rate limiting
│   │   ├── tasks/               # Celery task definitions
│   │   ├── celery_app.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── run.py                   # ASGI entry point
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios API modules
│   │   ├── components/
│   │   ├── pages/
│   │   └── stores/
│   ├── package.json
│   └── vite.config.js
├── nginx/nginx.conf
├── Dockerfile
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.11 (matches the Docker image)
- Node.js and npm
- PostgreSQL and Redis reachable from the machine running the backend
- A TMDB API key
- Docker and Docker Compose only if using the supplied backend/worker/Nginx deployment configuration

The supplied Compose file starts **Nginx, the FastAPI backend, and a Celery worker**. It does not define PostgreSQL or Redis containers, so provide reachable instances yourself. It also mounts host Let's Encrypt certificates and is configured for `devansh.online`; it is not a self-contained local-development stack.

### 1. Clone and configure

```bash
git clone <repository-url> BingeSaga
cd BingeSaga
```

Create a root-level `.env` file with the variables in the next section. The repository does not include an `.env.example`. Do not copy real credentials into documentation or source control.

### 2. Start dependencies

Start PostgreSQL and Redis using your local installation or managed services, then point `DB_URL` and `REDIS_URL` in the root `.env` file at them. The application accepts `postgresql://...` or `postgres://...` and converts it to SQLAlchemy's async `postgresql+asyncpg://...` URL at runtime. Redis is required for the project's OTP flow, cache/rate-limit behavior, and default Celery broker/backend.

### 3. Install backend dependencies and migrate

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 4. Run the backend and worker

In one terminal from `backend/`:

```bash
source .venv/bin/activate
uvicorn run:app --reload --host 0.0.0.0 --port 8000
```

In another terminal from `backend/`, start the worker if you want background audit persistence and Cloudinary movie-artwork imports:

```bash
source .venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=info --concurrency=2
```

FastAPI exposes its generated OpenAPI UI at `http://localhost:8000/docs` when run locally.

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The current Axios client has a fixed API base URL of `https://devansh.online` in `frontend/src/api/client.ts`; it does not read a Vite API-base environment variable. The Vite server will start locally, but API calls from the checked-in SPA target that URL unless the client source is changed for a local backend.

### Docker deployment configuration

After creating the root `.env` and making PostgreSQL/Redis reachable to the containers, the supplied configuration can be built with:

```bash
docker compose up --build
```

This starts the services declared in `docker-compose.yml`; migration execution remains a separate step.

### Tests

From `backend/`, with the environment configured and Redis running:

```bash
pytest
```

The test suite uses SQLite through `aiosqlite` for database fixtures, but its fixtures flush the Redis URL configured in `REDIS_URL`.

## Environment Variables

Create `.env` at the repository root. Required values are marked accordingly; empty values for optional integrations leave the relevant functionality unavailable or skipped.

```env
# Required for the backend
TMDB_API_KEY=
DB_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
JWT_SECRET_TOKEN=
REDIS_URL=redis://HOST:6379/0

# Optional: defaults to 7
REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional: required for SMS OTP
TWILIO_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_API_SECRET=
TWILIO_PHONE_NUMBER=

# Optional: required for Cloudinary uploads and artwork import
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=bingesaga

# Optional: fall back to REDIS_URL when unset
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

# Optional Redis connection tuning
REDIS_SOCKET_CONNECT_TIMEOUT=2
REDIS_SOCKET_TIMEOUT=2
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_MAX_CONNECTIONS=50

# Optional best-effort Celery/audit dispatch tuning
BACKGROUND_DISPATCH_QUEUE_SIZE=1000
BACKGROUND_DISPATCH_PUBLISHERS=2
AUDIT_EVENT_QUEUE_SIZE=1000
AUDIT_EVENT_BATCH_SIZE=50
AUDIT_EVENT_BATCH_WAIT_MS=50
```

Some older, currently unmounted frontend components read `VITE_MOVIE_API_KEY` for direct TMDB calls. The active SPA routes use the backend API modules instead; no frontend API-base environment variable is implemented in the current client.
