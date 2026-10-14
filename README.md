# SATRA (Tortoise Management System)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

SATRA is an offline-first wildlife conservation platform designed for tortoise tracking, rescue, rehabilitation, clinical health inspections, reproductive/breeding management, and computer-vision biometric shell pattern recognition.

---

## Architecture Overview

- **Backend API (`backend/`)**: FastAPI, Python 3.11, Pydantic v2, SQLAlchemy, Uvicorn.
- **Database**: PostgreSQL (PostGIS enabled for geospatial queries).
- **Hosting / PaaS**: [Render.com](https://render.com) using Infrastructure-as-Code Blueprint (`render.yaml`).
- **Specification**: Complete technical requirements and data models in [SPECIFICATION.md](SPECIFICATION.md).

---

## Deploying to Render.com

SATRA includes a native `render.yaml` Blueprint that automatically provisions:
1. **`satra-api`**: FastAPI Web Service with automated health checking (`/healthz`).
2. **`satra-db`**: Managed PostgreSQL Database linked directly via `DATABASE_URL`.

### One-Time Setup in Render:

1. Log into your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect your GitHub repository: `faustzar/satra`.
4. Render will detect `render.yaml` and display the blueprint resources (`satra-api` and `satra-db`).
5. Click **Apply**.
6. Render will automatically build the service, start PostgreSQL, run the health check, and assign you a live HTTPS URL (e.g. `https://satra-api.onrender.com`).

---

## Local Development

### 1. Set up Virtual Environment
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/healthz](http://localhost:8000/healthz)

---

## Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/healthz` | Health check probe for Render |
| `GET` | `/api/v1/specimens` | List registered tortoises |
| `POST` | `/api/v1/specimens` | Register a new tortoise profile |
| `POST` | `/api/v1/sightings` | Log GPS location and micro-habitat sighting |
| `POST` | `/api/v1/health-inspections` | Record weight, SCL, BCS & Jackson's ratio |
| `POST` | `/api/v1/breeding/pairings` | Record mating, courtship and nesting |
| `POST` | `/api/v1/recognition/match-shell`| Biometric shell pattern matching |
